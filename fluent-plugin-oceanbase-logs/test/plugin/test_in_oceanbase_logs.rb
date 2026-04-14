require 'test/unit'
require 'fluent/test'
require 'fluent/test/driver/input'
require 'fluent/plugin/in_oceanbase_logs'
require 'webmock/test_unit'

class OceanBaseLogsInputTest < Test::Unit::TestCase
  def setup
    Fluent::Test.setup
    WebMock.disable_net_connect!
  end

  def teardown
    WebMock.allow_net_connect!
  end

  BASE_CONFIG = %(
    tag oceanbase.logs
    access_key_id     test_access_key_id
    access_key_secret test_access_key_secret
    instance_id       ob317v4uif0001
    tenant_id         t4louaeei0001
    fetch_interval    60
    lookback_seconds  300
    deduplicate       false
  )

  # List API response (plugin only uses sqlId from each item)
  SLOW_SQL_RESPONSE = {
    'success' => true,
    'data' => {
      'dataList' => [
        { 'sqlId' => '8D6E84ABCD0B8FB1823D199E2CA10001' },
        { 'sqlId' => '8D6E84ABCD0B8FB1823D199E2CA10002' },
      ],
      'total' => 2
    }
  }.freeze

  TOP_SQL_RESPONSE = {
    'success' => true,
    'data' => {
      'dataList' => [
        { 'sqlId' => 'TOP_SQL_001' },
      ],
      'total' => 1
    }
  }.freeze

  # Per-execution sample (used after list API; plugin fetches samples per sqlId)
  SAMPLES_RESPONSE = {
    'success' => true,
    'data' => {
      'dataList' => [
        {
          'sqlId'        => '8D6E84ABCD0B8FB1823D199E2CA10001',
          'traceId'      => 'trace-slow-001',
          'requestTime'  => '2026-03-09T08:00:00Z',
          'fullSqlText'  => 'SELECT * FROM orders WHERE created_at > ?',
          'sqlTextShort' => 'SELECT * FROM orders WHERE created_at > ?',
          'sqlType'      => 'select',
          'dbName'       => 'shop_db',
          'userName'     => 'app_user',
          'elapsedTime'  => 1876.78,
          'cpuTime'      => 1875.34,
          'executeTime'  => 1850.0,
          'returnRows'   => 100,
          'affectedRows' => 0,
        }
      ]
    }
  }.freeze

  SAMPLES_RESPONSE_TOP = {
    'success' => true,
    'data' => {
      'dataList' => [
        {
          'sqlId'        => 'TOP_SQL_001',
          'traceId'      => 'trace-top-001',
          'requestTime'  => '2026-03-09T08:01:00Z',
          'fullSqlText'  => 'SELECT count(*) FROM large_table',
          'sqlTextShort' => 'SELECT count(*) FROM large_table',
          'sqlType'      => 'select',
          'dbName'       => 'analytics_db',
          'userName'     => 'report_user',
          'elapsedTime'  => 903.29,
          'cpuTime'      => 875.34,
        }
      ]
    }
  }.freeze

  def create_driver(conf = BASE_CONFIG)
    Fluent::Test::Driver::Input.new(
      Fluent::Plugin::OceanBaseLogsInput
    ).configure(conf)
  end

  def stub_digest_auth(path_pattern, response_body)
    stub_request(:get, path_pattern)
      .to_return(
        { status: 401, headers: { 'WWW-Authenticate' => 'Digest realm="OceanBase", nonce="abc123", qop="auth"' } },
        { status: 200, body: response_body.to_json, headers: { 'Content-Type' => 'application/json' } }
      )
  end

  # Stub samples API for multiple sqlIds (list returns 2 items => 2 sample calls)
  def stub_samples_auth(samples_response, times: 2)
    responses = times.times.flat_map do
      [
        { status: 401, headers: { 'WWW-Authenticate' => 'Digest realm="OceanBase", nonce="abc123", qop="auth"' } },
        { status: 200, body: samples_response.to_json, headers: { 'Content-Type' => 'application/json' } }
      ]
    end
    stub_request(:get, %r{/sqls/[^/]+/samples})
      .to_return(*responses)
  end

  # -------------------------------------------------------------- configure

  sub_test_case 'configuration' do
    test 'defaults to slow_sql log_type' do
      d = create_driver
      assert_equal :slow_sql, d.instance.log_type
      assert_equal 'oceanbase.logs', d.instance.tag
      assert_equal 'ob317v4uif0001', d.instance.instance_id
      assert_equal 't4louaeei0001',  d.instance.tenant_id
      assert_equal 'api-cloud-cn.oceanbase.com', d.instance.endpoint
      assert_equal 60,    d.instance.fetch_interval
      assert_equal 300,   d.instance.lookback_seconds
      assert_equal 65535, d.instance.sql_text_length
    end

    test 'accepts top_sql log_type' do
      d = create_driver(BASE_CONFIG + "  log_type top_sql\n")
      assert_equal :top_sql, d.instance.log_type
    end

    test 'rejects invalid log_type' do
      assert_raise(Fluent::ConfigError) do
        create_driver(BASE_CONFIG + "  log_type invalid_type\n")
      end
    end

    test 'optional project_id' do
      d = create_driver(BASE_CONFIG + "  project_id proj123\n")
      assert_equal 'proj123', d.instance.project_id
    end

    test 'custom endpoint for intl site' do
      d = create_driver(BASE_CONFIG + "  endpoint api-cloud.oceanbase.com\n")
      assert_equal 'api-cloud.oceanbase.com', d.instance.endpoint
    end

    test 'missing required parameter raises error' do
      assert_raise(Fluent::ConfigError) do
        create_driver(%(
          tag oceanbase.logs
          access_key_id     test_id
          access_key_secret test_secret
          tenant_id         t0001
        ))
      end
    end

    test 'empty instance_id raises error' do
      conf = BASE_CONFIG.sub(/^\s*instance_id\s+.*\n/, "    instance_id \"\"\n")
      assert_raise(Fluent::ConfigError) { create_driver(conf) }
    end

    test 'empty tenant_id raises error' do
      conf = BASE_CONFIG.sub(/^\s*tenant_id\s+.*\n/, "    tenant_id \"\"\n")
      assert_raise(Fluent::ConfigError) { create_driver(conf) }
    end

    test 'multiple targets: top-level instance_id and tenant_id may be empty' do
      conf = %(
    tag oceanbase.logs
    access_key_id     test_access_key_id
    access_key_secret test_access_key_secret
    fetch_interval    60
    lookback_seconds  300
    deduplicate       false
    <target>
      instance_id ob_a
      tenant_id t_a
    </target>
    <target>
      instance_id ob_b
      tenant_id t_b
      db_name analytics_db
    </target>
  )
      d = create_driver(conf)
      assert_equal 2, d.instance.instance_variable_get(:@fetch_scopes).size
      scopes = d.instance.instance_variable_get(:@fetch_scopes)
      assert_equal 'ob_a', scopes[0].instance_id
      assert_equal 't_a',  scopes[0].tenant_id
      assert_nil scopes[0].db_name
      assert_equal 'ob_b', scopes[1].instance_id
      assert_equal 'analytics_db', scopes[1].db_name
    end

    test 'target section missing tenant_id raises error' do
      conf = %(
    tag oceanbase.logs
    access_key_id     test_access_key_id
    access_key_secret test_access_key_secret
    fetch_interval    60
    lookback_seconds  300
    deduplicate       false
    <target>
      instance_id ob_a
      tenant_id ""
    </target>
  )
      assert_raise(Fluent::ConfigError) { create_driver(conf) }
    end

  end

  # ----------------------------------------------------------- fetching

  sub_test_case 'fetching SQL data' do
    test 'slow_sql calls /slowSql then /samples and emits events' do
      stub_digest_auth(
        %r{api-cloud-cn\.oceanbase\.com/api/v2/instances/ob317v4uif0001/tenants/t4louaeei0001/slowSql},
        SLOW_SQL_RESPONSE
      )
      stub_samples_auth(SAMPLES_RESPONSE, times: 2)

      d = create_driver
      d.run(timeout: 3)

      events = d.events
      assert events.length >= 2, "Expected at least 2 events, got #{events.length}"

      first = events[0][2]
      assert_equal '8D6E84ABCD0B8FB1823D199E2CA10001', first['sqlId']
      assert_equal 'trace-slow-001', first['traceId']
      assert_equal 'shop_db',  first['dbName']
      assert_equal 'app_user', first['userName']
      assert_equal 'select',   first['sqlType']
      assert_equal 1876.78,    first['elapsedTime']
      assert_equal 'slow_sql', first['ob_log_type']
      assert_equal 'ob317v4uif0001', first['ob_instance_id']
      assert_equal 't4louaeei0001',  first['ob_tenant_id']
    end

    test 'top_sql calls /topSql then /samples and emits events' do
      stub_digest_auth(
        %r{api-cloud-cn\.oceanbase\.com/api/v2/instances/ob317v4uif0001/tenants/t4louaeei0001/topSql},
        TOP_SQL_RESPONSE
      )
      stub_samples_auth(SAMPLES_RESPONSE_TOP, times: 1)

      d = create_driver(BASE_CONFIG + "  log_type top_sql\n")
      d.run(timeout: 3)

      events = d.events
      assert events.length >= 1, "Expected at least 1 event, got #{events.length}"

      record = events[0][2]
      assert_equal 'TOP_SQL_001',  record['sqlId']
      assert_equal 'trace-top-001', record['traceId']
      assert_equal 'analytics_db', record['dbName']
      assert_equal 903.29,         record['elapsedTime']
      assert_equal 'top_sql',     record['ob_log_type']
    end

    test 'handles empty list (no samples called)' do
      stub_digest_auth(
        %r{api-cloud-cn\.oceanbase\.com/api/v2/instances/ob317v4uif0001/tenants/t4louaeei0001/slowSql},
        { 'success' => true, 'data' => { 'dataList' => [], 'total' => 0 } }
      )

      d = create_driver
      d.run(timeout: 3)
      assert_equal 0, d.events.length
    end

    test 'handles API error gracefully' do
      stub_request(:get, %r{api-cloud-cn\.oceanbase\.com})
        .to_return(status: 500, body: 'Internal Server Error')

      d = create_driver
      d.run(timeout: 3)
      assert_equal 0, d.events.length
    end

    test 'handles malformed JSON response' do
      stub_request(:get, %r{api-cloud-cn\.oceanbase\.com})
        .to_return(
          { status: 401, headers: { 'WWW-Authenticate' => 'Digest realm="OB", nonce="x", qop="auth"' } },
          { status: 200, body: 'not-json' }
        )

      d = create_driver
      d.run(timeout: 3)
      assert_equal 0, d.events.length
    end

    test 'handles API-level error' do
      stub_digest_auth(
        %r{api-cloud-cn\.oceanbase\.com},
        { 'success' => false, 'errorCode' => 'E001R000', 'errorMessage' => 'unknown error' }
      )

      d = create_driver
      d.run(timeout: 3)
      assert_equal 0, d.events.length
    end

    test 'slow_sql with two targets calls both APIs and emits scoped metadata' do
      list_one = {
        'success' => true,
        'data' => { 'dataList' => [{ 'sqlId' => 'SQL_MULTI_A' }], 'total' => 1 },
      }
      list_two = {
        'success' => true,
        'data' => { 'dataList' => [{ 'sqlId' => 'SQL_MULTI_B' }], 'total' => 1 },
      }
      stub_digest_auth(
        %r{instances/ob_a/tenants/t_a/slowSql},
        list_one
      )
      stub_digest_auth(
        %r{instances/ob_b/tenants/t_b/slowSql},
        list_two
      )
      stub_samples_auth(SAMPLES_RESPONSE, times: 2)

      conf = %(
    tag oceanbase.logs
    access_key_id     test_access_key_id
    access_key_secret test_access_key_secret
    fetch_interval    60
    lookback_seconds  300
    deduplicate       false
    <target>
      instance_id ob_a
      tenant_id t_a
    </target>
    <target>
      instance_id ob_b
      tenant_id t_b
    </target>
  )
      d = create_driver(conf)
      d.run(timeout: 3)

      events = d.events
      assert events.length >= 2, "Expected at least 2 events, got #{events.length}"
      insts = events.map { |e| e[2]['ob_instance_id'] }.uniq.sort
      assert_equal %w[ob_a ob_b], insts
    end
  end

  # ---------------------------------------------------------- deduplication

  sub_test_case 'deduplication' do
    test 'skips duplicate traceIds when enabled' do
      conf = BASE_CONFIG.sub('deduplicate       false', 'deduplicate       true')

      stub_digest_auth(
        %r{/slowSql},
        SLOW_SQL_RESPONSE
      )
      # Same traceId in both sample responses => second is deduplicated
      stub_samples_auth(SAMPLES_RESPONSE, times: 2)

      d = create_driver(conf)
      d.run(timeout: 5)

      trace_ids = d.events.map { |e| e[2]['traceId'] }
      assert_equal trace_ids.uniq, trace_ids, "Expected no duplicate traceIds"
    end
  end

  # -------------------------------------------------------- metadata

  sub_test_case 'metadata' do
    test 'does not include metadata when disabled' do
      conf = BASE_CONFIG + "  include_metadata false\n"

      stub_digest_auth(%r{/slowSql}, SLOW_SQL_RESPONSE)
      stub_samples_auth(SAMPLES_RESPONSE, times: 2)

      d = create_driver(conf)
      d.run(timeout: 3)

      record = d.events.first[2]
      assert_nil record['ob_instance_id']
      assert_nil record['ob_tenant_id']
      assert_equal 'slow_sql', record['ob_log_type']
    end
  end
end
