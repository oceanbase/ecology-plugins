# fluent-plugin-oceanbase-logs

Fluentd **input** plugin: periodically pulls SQL diagnostics from [OceanBase Cloud](https://www.oceanbase.com/) . Each event is **one execution sample**

| `log_type` | API | Meaning |
| --- | --- | --- |
| `slow_sql` (default) | `…/slowSql` + per-`sqlId` samples | Slow SQL |
| `top_sql` | `…/topSql` + samples | Top SQL |

Every record includes **`ob_log_type`** (`slow_sql` or `top_sql`). With `include_metadata true` (default), records also get `ob_instance_id`, `ob_tenant_id`, and the query time window.

## Requirements

| Gem | Fluentd | Ruby |
| --- | --- | --- |
| >= 0.1.5 | >= 1.8.0 | >= 2.4 |

For **Grafana Loki** output you additionally need [fluent-plugin-grafana-loki](https://github.com/grafana/fluent-plugin-grafana-loki).

## Installation

```bash
gem install fluent-plugin-oceanbase-logs
```

## Preparation

1. Create an AccessKey in [OceanBase Cloud — AccessKey](https://console-cn.oceanbase.com/account/accessKey).
2. In the console, copy **Instance ID** and **Tenant ID** 


## Configuration

### Environment variables

Typical pattern in Fluentd:

```text
access_key_id     "#{ENV['OCEANBASE_ACCESS_KEY_ID']}"
access_key_secret "#{ENV['OCEANBASE_ACCESS_KEY_SECRET']}"
instance_id       "#{ENV['OCEANBASE_INSTANCE_ID']}"
tenant_id         "#{ENV['OCEANBASE_TENANT_ID']}"
```

Optional: `OCEANBASE_ENDPOINT`, `OCEANBASE_FETCH_INTERVAL`, `OCEANBASE_LOOKBACK_SECONDS`, `OCEANBASE_DB_NAME`, `OCEANBASE_SEARCH_KEYWORD`, `OCEANBASE_PROJECT_ID` — see `.env.example` and the Docker table below.

### Multiple instances, tenants, and databases

Use one or more `<target>` blocks. Each block sets **`instance_id`** and **`tenant_id`** (required). Optional **`db_name`** applies the same `dbName` filter as the top-level parameter, for that scope only.

When any `<target>` is present, the plugin **only** uses those scopes; top-level `instance_id` / `tenant_id` / `db_name` are ignored (you may leave them empty). Global options such as `access_key_id`, `log_type`, `search_keyword`, `endpoint`, and `fetch_interval` still apply to every target.

Example: two clusters, one tenant each, and a second scope that filters one database on another tenant:

```conf
<source>
  @type oceanbase_logs
  tag  oceanbase.slow_sql
  log_type slow_sql
  access_key_id     "#{ENV['OCEANBASE_ACCESS_KEY_ID']}"
  access_key_secret "#{ENV['OCEANBASE_ACCESS_KEY_SECRET']}"
  endpoint     "#{ENV['OCEANBASE_ACCESS_KEY_SECRET']}"
  fetch_interval   60
  lookback_seconds 600
  deduplicate      true
  include_metadata true
  <target>
    instance_id "OCEANBASE_INSTANCE_1"
    tenant_id   "OCEANBASE_TENANT_A"
  </target>
  <target>
    instance_id "OCEANBASE_INSTANCE_2"
    tenant_id   "OCEANBASE_TENANT_B"
  </target>
  <storage>
    @type local
    persistent true
    path /var/log/fluentd/slow_sql_seen
  </storage>
</source>
```

### Example: Slow SQL → JSON file

Full sample: [`example/fluentd.conf`](example/fluentd.conf).

```conf
<source>
  @type oceanbase_logs
  tag  oceanbase.slow_sql
  log_type slow_sql
  access_key_id     "#{ENV['OCEANBASE_ACCESS_KEY_ID']}"
  access_key_secret "#{ENV['OCEANBASE_ACCESS_KEY_SECRET']}"
  instance_id       "#{ENV['OCEANBASE_INSTANCE_ID']}"
  tenant_id         "#{ENV['OCEANBASE_TENANT_ID']}"
  endpoint          api-cloud-cn.oceanbase.com
  fetch_interval    60
  lookback_seconds  600
  deduplicate       true
  include_metadata  true
  <storage>
    @type local
    persistent true
    path /var/log/fluentd/slow_sql_seen
  </storage>
</source>

<match oceanbase.slow_sql>
  @type file
  path /var/log/fluentd/slow_sql
  append true
  <format>
    @type json
  </format>
</match>
```

### Example: Loki + Docker Compose

Ready-made stack (Loki, Fluentd, Grafana) and a **slow_sql + top_sql**：

```bash
cp .env.example .env   # fill in secrets
cd example/oceanbase2loki-docker && docker compose up -d
```

**Compose-related environment** (host `.env` or exports):

| Variable | Required | Default |
| --- | --- | --- |
| `LOKI_URL` | no | `http://loki:3100` |
| `OCEANBASE_ACCESS_KEY_ID` | **yes** | — |
| `OCEANBASE_ACCESS_KEY_SECRET` | **yes** | — |
| `OCEANBASE_INSTANCE_ID` | **yes** | — |
| `OCEANBASE_TENANT_ID` | **yes** | — |
| `OCEANBASE_ENDPOINT` | no | `api-cloud-cn.oceanbase.com` |
| `OCEANBASE_FETCH_INTERVAL` | no | `60` |
| `OCEANBASE_LOOKBACK_SECONDS` | no | `600` |
| `OCEANBASE_DB_NAME` | no | `test` |
| `OCEANBASE_SEARCH_KEYWORD` | no | `SELECT` |
| `OCEANBASE_PROJECT_ID` | no | *(unset)* |

> The bundled `fluentd-to-loki.conf` uses `record.dig` and avoids `";` / `]` patterns that break Fluentd’s config parser and `record_transformer` — keep that style if you edit it.