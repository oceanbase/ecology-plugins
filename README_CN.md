# OceanBase 生态插件合集

本仓库包含多个插件，旨在解决 **OceanBase** 与不同框架/工具（如 Flyway、Trino、WordPress、Fluentd 等）之间的兼容性问题。每个插件针对特定场景优化，确保数据库操作的稳定性与高效性。

---

## 🧩 项目概述

OceanBase 是一款兼容 MySQL 和 Oracle 协议的高性能数据库。本仓库提供以下插件，帮助开发者在实际应用中解决常见兼容性问题：

全屏复制

| 插件名称                                                                                 | 适用场景                     | 主要功能                                                                  |
| ---------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------- |
| [Flyway OceanBase 插件](./flyway-oceanbase-plugin/README_CN.md)                             | 数据库迁移                   | 解决 Flyway 在 OceanBase MySQL 模式下的兼容性问题                         |
| [Trino OceanBase 插件](https://github.com/oceanbase/trino-oceanbase)                        | 数据分析                     | 支持 Trino 连接 OceanBase（MySQL/Oracle 模式）                            |
| [WordPress OceanBase 插件](./wordpress-oceanbase-plugin/README_CN.md)                       | 内容管理                     | 修复 WordPress 与 OceanBase MySQL 租户的兼容性问题                        |
| [OceanBase SQL 助手插件](./oceanbase-sql-helper-plugin/README_CN.md)                        | 开发工具                     | VSCode 插件，快速访问 OceanBase SQL 关键词文档                            |
| [Metabase OceanBase 插件](./metabase-oceanbase-plugin/README_CN.md)                         | 数据可视化                   | 支持 Metabase 连接 OceanBase（MySQL/Oracle 模式）                         |
| [OceanBase SQLAlchemy 插件](./oceanbase-sqlalchemy-plugin/README.md)                        | Python ORM                   | SQLAlchemy 方言，支持 OceanBase Oracle 模式，兼容 SQLAlchemy 1.3+ 和 2.0+ |
| [LangGraph Checkpoint OceanBase 插件](./langgraph-checkpoint-oceanbase-plugin/README.md)    | 保存 LangGraph 的 checkpoint | 使用 OceanBase MySQL 模式实现了 LangGraph CheckpointSaver                 |
| [Fluent Plugin OceanBase Logs](./fluent-plugin-oceanbase-logs/README.md)                  | 日志采集（Fluentd）        | Fluentd 输入插件，从 OceanBase 云拉取慢 SQL、Top SQL 等诊断数据           |
| [PyObsql OceanBase 插件](./pyobsql-oceanbase-plugin/README.md)                                 | Python SDK                   | 支持 JSON Table、SQLAlchemy 方言扩展和高级数据类型的 OceanBase Python SDK |

---

## 📁 插件详情

### ✅ Flyway OceanBase MySQL 插件

- **功能**：解决 Flyway 在 OceanBase MySQL 模式下的迁移问题（如 `version` 字段冲突、驱动兼容性等）。
- **适用场景**：使用 Flyway 管理 OceanBase MySQL 模式的数据库迁移。
- **详细文档**：[Flyway OceanBase 插件](./flyway-oceanbase-plugin/README_CN.md)

---

### ✅ Trino OceanBase 插件

- **功能**：支持 Trino 连接 OceanBase（MySQL/Oracle 模式），优化 SQL 查询与事务处理。此项目已迁移到新仓库。
- **适用场景**：通过 Trino 查询 OceanBase 数据库（支持多模式）。
- **详细文档**：[Trino OceanBase 插件](https://github.com/oceanbase/trino-oceanbase)
- **仓库地址**：https://github.com/oceanbase/trino-oceanbase

---

### ✅ WordPress OceanBase 插件

- **功能**：修复 WordPress 与 OceanBase MySQL 租户的兼容性问题（如表别名限制）。
- **适用场景**：WordPress 部署在 OceanBase MySQL 租户时的兼容性适配。
- **详细文档**：[WordPress OceanBase 插件](./wordpress-oceanbase-plugin/README_CN.md)

---

### ✅ OceanBase SQL 助手插件

- **功能**：VSCode 插件，提供 OceanBase SQL 关键词文档的快速访问，支持悬停提示和直接导航。
- **适用场景**：增强开发者在编写 OceanBase 数据库 SQL 查询时的开发体验。
- **详细文档**：[OceanBase SQL 助手插件](./oceanbase-sql-helper-plugin/README_CN.md)

---

### ✅ Metabase OceanBase 插件

- **功能**：支持 Metabase 连接 OceanBase（MySQL/Oracle 模式），自动检测兼容模式并适配相应 SQL 语法。
- **适用场景**：使用 Metabase 进行数据分析和可视化，连接 OceanBase 数据库。
- **详细文档**：[Metabase OceanBase 插件](./metabase-oceanbase-plugin/README_CN.md)

---

### ✅ OceanBase SQLAlchemy 插件

- **功能**：SQLAlchemy 方言，支持 OceanBase Oracle 模式，完全兼容 SQLAlchemy 1.3.x 和 2.0+，提供优化的 SQL 查询和约束反射。
- **适用场景**：使用 Python SQLAlchemy ORM 框架连接和操作 OceanBase Oracle 模式数据库。
- **详细文档**：[OceanBase SQLAlchemy 插件](./oceanbase-sqlalchemy-plugin/README.md)

---

### ✅ LangGraph Checkpoint OceanBase 插件

- **功能**：使用 OceanBase MySQL 模式实现了 LangGraph CheckpointSaver。
- **适用场景**：使用 OceanBase 作为 LangGraph 的 Checkpointer。
- **详细文档**：[LangGraph Checkpoint OceanBase 插件](./langgraph-checkpoint-oceanbase-plugin/README.md)

---

### ✅ PyObsql OceanBase 插件

- **功能**：OceanBase SQL 的 Python SDK，提供扩展的 SQLAlchemy 方言支持、JSON Table 操作和高级数据类型（VECTOR、SPARSE_VECTOR、ARRAY、POINT）。
- **适用场景**：需要使用 SQLAlchemy 与 OceanBase 数据库交互并利用 OceanBase 特定功能的 Python 应用程序。
- **详细文档**：[PyObsql OceanBase 插件](./pyobsql-oceanbase-plugin/README.md)

---

### ✅ Fluent Plugin OceanBase Logs

- **功能**：Fluentd **输入**插件，通过 OceanBase 云 API 周期性拉取 SQL 诊断数据（慢 SQL、Top SQL 等）；每条事件为一次执行采样，可选附带实例、租户与时间窗口等元数据。
- **适用场景**：将 OceanBase 云上的 SQL 诊断接入 Fluentd 流水线（例如输出为 JSON 文件，或通过 [fluent-plugin-grafana-loki](https://github.com/grafana/fluent-plugin-grafana-loki) 写入 Grafana Loki）。
- **详细文档**：[Fluent Plugin OceanBase Logs](./fluent-plugin-oceanbase-logs/README.md)

---

## 📚 完整文档链接

| 插件名称                            | 文档链接                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------- |
| Flyway OceanBase MySQL 插件         | [Flyway OceanBase 插件](./flyway-oceanbase-plugin/README_CN.md)                             |
| Trino OceanBase 插件                | [Trino OceanBase 插件](https://github.com/oceanbase/trino-oceanbase)                        |
| WordPress OceanBase 插件            | [WordPress OceanBase 插件](./wordpress-oceanbase-plugin/README_CN.md)                       |
| OceanBase SQL 助手插件              | [OceanBase SQL 助手插件](./oceanbase-sql-helper-plugin/README_CN.md)                        |
| Metabase OceanBase 插件             | [Metabase OceanBase 插件](./metabase-oceanbase-plugin/README_CN.md)                         |
| OceanBase SQLAlchemy 插件           | [OceanBase SQLAlchemy 插件](./oceanbase-sqlalchemy-plugin/README.md)                        |
| LangGraph Checkpoint OceanBase 插件 | [LangGraph Checkpoint OceanBase 插件](./langgraph-checkpoint-oceanbase-plugin/README.md)    |
| Fluent Plugin OceanBase Logs        | [Fluent Plugin OceanBase Logs](./fluent-plugin-oceanbase-logs/README.md)                   |
| PyObsql OceanBase 插件              | [PyObsql OceanBase 插件](./pyobsql-oceanbase-plugin/README.md)                             |

---

## 🛠️ 贡献与反馈

欢迎提交 Issues 或 Pull Request，帮助完善插件功能。

- [GitHub Issues](https://github.com/oceanbase/ecology-plugins/issues)

---

## 📄 授权协议

本项目采用 [Apache License 2.0](./LICENSE) 协议开源。

---

## 📌 注意事项

- 每个插件的详细配置与使用方法，请参考对应文档。
- 确保 OceanBase 版本与插件兼容（建议 ≥ 3.1.0）。
- 插件适用于 MySQL/Oracle 模式，需根据实际环境选择适配版本。
