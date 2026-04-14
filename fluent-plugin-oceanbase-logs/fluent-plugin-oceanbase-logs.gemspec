lib = File.expand_path('../lib', __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'fluent/plugin/oceanbase/logs/version'

Gem::Specification.new do |spec|
  spec.name          = "fluent-plugin-oceanbase-logs"
  spec.version       = Fluent::Plugin::OceanBase::Logs::VERSION
  spec.authors       = ["OceanBase Integrations"]
  spec.email         = ["integrations@example.com"]
  spec.summary       = "Fluentd input plugin for OceanBase Cloud Logs"
  spec.description   = "Fetches Slow SQL and Top SQL per-execution samples from OceanBase Cloud " \
                        "and emits them as Fluentd events (one record per trace, dedup by traceId)."
  spec.homepage      = "https://github.com/oceanbase/ecology-plugins/tree/main/fluent-plugin-oceanbase-logs"
  spec.license       = "Apache-2.0"

  spec.files         = Dir['lib/**/*', 'README.md', 'LICENSE']
  spec.require_paths = ["lib"]
  spec.required_ruby_version = '>= 2.4'

  spec.add_dependency 'fluentd', '>= 1.8.0'

  spec.add_development_dependency "bundler"
  spec.add_development_dependency "rake"
  spec.add_development_dependency "test-unit", "~> 3.0"
  spec.add_development_dependency "webmock", "~> 3.0"
end
