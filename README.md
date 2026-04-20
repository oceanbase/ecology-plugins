# OceanBase Ecosystem Plugins Collection

This repository includes multiple plugins designed to resolve compatibility issues between **OceanBase** and various frameworks/tools (such as Flyway, Trino, WordPress, Fluentd, [Haystack](https://haystack.deepset.ai/) for RAG, and more). Each plugin is optimized for specific scenarios to ensure stable and efficient database operations.

---

## 🧩 Project Overview

OceanBase is a high-performance database compatible with both MySQL and Oracle protocols. This repository provides the following plugins to help developers address common compatibility issues in real-world applications:

| Plugin Name                                                                             | Use Case                  | Key Features                                                                           |
| --------------------------------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------- |
| [Flyway OceanBase Plugin](./flyway-oceanbase-plugin/README.md)                             | Database Migration        | This plugin enables Flyway to support OceanBase in both MySQL and Oracle compatibility modes. |
| [Trino OceanBase Plugin](https://github.com/oceanbase/trino-oceanbase)                      | Data Analysis             | Enables Trino to connect to OceanBase (MySQL/Oracle mode)                              |
| [WordPress OceanBase Plugin](./wordpress-oceanbase-plugin/README.md)                       | Content Management        | This plugin enables WordPress to support OceanBase in both MySQL modes.              |
| [OceanBase SQL Helper Plugin](./oceanbase-sql-helper-plugin/README.md)                     | Development Tools         | A VSCode extension that helps developers quickly find OceanBase SQL keywords documentation. |
| [Metabase OceanBase Plugin](./metabase-oceanbase-plugin/README.md)                         | Data Visualization        | Enables Metabase to connect to OceanBase (MySQL/Oracle mode)                           |
| [OceanBase SQLAlchemy Plugin](./oceanbase-sqlalchemy-plugin/README.md)                     | Python ORM                | SQLAlchemy ORM for OceanBase Oracle mode, compatible with SQLAlchemy 1.3+ and 2.0+ |
| [OceanBase Dify Plugin](https://github.com/oceanbase/dify-plugin-oceanbase)               | AI Applications           | Enables secure SQL query execution on OceanBase databases through Dify applications    |
| [LangGraph Checkpoint OceanBase Plugin](./langgraph-checkpoint-oceanbase-plugin/README.md) | LangGraph CheckpointSaver | Implementation of LangGraph CheckpointSaver in OceanBase MySQL mode             |
| [Fluent Plugin OceanBase Logs](./fluent-plugin-oceanbase-logs/README.md)                   | Log collection (Fluentd)  | Fluentd input plugin that pulls slow SQL and top SQL diagnostics from OceanBase Cloud |
| [PyObsql OceanBase Plugin](./pyobsql-oceanbase-plugin/README.md)                             | Python SDK                | A Python SDK for OceanBase SQL with JSON Table support and SQLAlchemy dialect extensions |
| [OceanBase CLI](./oceanbase-cli/README.md)                                                   | CLI & Agent Skill         | `obcli` for MySQL protocol (encrypted local DSN, optional `policy.json`); includes [Agent Skill](./skills/oceanbase-cli/SKILL.md) for Cursor / Claude Code |
| [OceanBase Haystack](./oceanbase-haystack/README.md)                                         | Haystack / RAG            | Haystack 2.x document store and embedding retriever for OceanBase vector search via [pyobvector](https://github.com/oceanbase/pyobvector) |

---

## 📁 Plugin Details

### ✅ Flyway OceanBase MySQL Plugin

- **Function**: Resolves compatibility issues when using Flyway with OceanBase in MySQL mode (e.g., `version` column conflicts, driver compatibility).
- **Use Case**: Managing database migrations for OceanBase MySQL mode using Flyway.
- **Documentation**: [Flyway OceanBase Plugin](./flyway-oceanbase-plugin/README.md)

---

### ✅ Trino OceanBase Plugin

- **Function**: Enables Trino to connect to OceanBase (MySQL/Oracle mode), optimizing SQL queries and transaction handling. This project has been migrated to a new repository.
- **Use Case**: Querying OceanBase databases via Trino (supports both modes).
- **Documentation**: [Trino OceanBase Plugin](https://github.com/oceanbase/trino-oceanbase)
- **Repository**: https://github.com/oceanbase/trino-oceanbase

---

### ✅ WordPress OceanBase Plugin

- **Function**: Fixes compatibility issues between WordPress and OceanBase MySQL tenants (e.g., table alias restrictions).
- **Use Case**: Ensuring WordPress compatibility when deployed on OceanBase MySQL tenants.
- **Documentation**: [WordPress OceanBase Plugin](./wordpress-oceanbase-plugin/README.md)

---

### ✅ OceanBase SQL Helper Plugin

- **Function**: VSCode extension that provides quick access to OceanBase SQL keywords documentation with hover tooltips and direct navigation.
- **Use Case**: Enhancing developer experience when writing SQL queries for OceanBase databases.
- **Documentation**: [OceanBase SQL Helper Plugin](./oceanbase-sql-helper-plugin/README.md)

---

### ✅ Metabase OceanBase Plugin

- **Function**: Enables Metabase to connect to OceanBase (MySQL/Oracle mode) with automatic compatibility mode detection and SQL syntax adaptation.
- **Use Case**: Data analysis and visualization using Metabase connected to OceanBase databases.
- **Documentation**: [Metabase OceanBase Plugin](./metabase-oceanbase-plugin/README.md)

---

### ✅ OceanBase SQLAlchemy Plugin

- **Function**: SQLAlchemy dialect for OceanBase Oracle mode, fully compatible with SQLAlchemy 1.3.x and 2.0+, providing optimized SQL queries and constraint reflection.
- **Use Case**: Using Python SQLAlchemy ORM framework to connect and operate OceanBase Oracle mode databases.
- **Documentation**: [OceanBase SQLAlchemy Plugin](./oceanbase-sqlalchemy-plugin/README.md)

---

### ✅ OceanBase Dify Plugin

- **Function**: A Dify plugin for connecting to and querying OceanBase databases. This project has been migrated to a new repository.
- **Use Case**: AI applications that need to interact with OceanBase databases through Dify platform for data querying and manipulation.
- **Documentation**: [OceanBase Dify Plugin](./dify-plugin-oceanbase/README.md)
- **Repository**: https://github.com/oceanbase/dify-plugin-oceanbase

---

### ✅ LangGraph Checkpoint OceanBase Plugin

- **Function**: OceanBase MySQL mode can be used as LangGraph's CheckpointSaver to preserve both short-term and long-term memory.
- **Use Case**: Using OceanBase as LangGraph's Checkpointer.
- **Documentation**: [LangGraph Checkpoint OceanBase Plugin](./langgraph-checkpoint-oceanbase-plugin/README.md)

---

### ✅ PyObsql OceanBase Plugin

- **Function**: A Python SDK for OceanBase SQL, providing extended SQLAlchemy dialect support, JSON Table operations, and advanced data types (VECTOR, SPARSE_VECTOR, ARRAY, POINT).
- **Use Case**: Python applications that need to interact with OceanBase databases using SQLAlchemy with OceanBase-specific features.
- **Documentation**: [PyObsql OceanBase Plugin](./pyobsql-oceanbase-plugin/README.md)

---

### ✅ Fluent Plugin OceanBase Logs

- **Function**: Fluentd **input** plugin that periodically pulls SQL diagnostics (slow SQL and top SQL samples) from OceanBase Cloud via API; each event is one execution sample, with optional metadata (instance, tenant, time window).
- **Use Case**: Shipping OceanBase Cloud SQL diagnostics to Fluentd pipelines (for example JSON files, or Grafana Loki via [fluent-plugin-grafana-loki](https://github.com/grafana/fluent-plugin-grafana-loki)).
- **Documentation**: [Fluent Plugin OceanBase Logs](./fluent-plugin-oceanbase-logs/README.md)

---

### ✅ OceanBase CLI (`obcli`)

- **Function**: Command-line tool for OceanBase over the **MySQL protocol** (via **pymysql**): encrypted DSN under `~/.config/obcli/`, read-oriented `obcli sql` by default, optional local **`policy.json`** with **`block_rules`** for write-class SQL when enabled.
- **Use Case**: Local or scripted access to OceanBase tenants; pair with the **[Agent Skill](./skills/oceanbase-cli/SKILL.md)** so assistants invoke `obcli` only through the shell and do not modify on-disk config.
- **Documentation**: [OceanBase CLI](./oceanbase-cli/README.md) · **Skill contract**: [skills/oceanbase-cli/SKILL.md](./skills/oceanbase-cli/SKILL.md)

---

### ✅ OceanBase Haystack

- **Function**: [Haystack](https://haystack.deepset.ai/) 2.x integration for OceanBase **vector** search: `OceanBaseDocumentStore`, dense/sparse/hybrid retrievers, and JSON `meta` filters, backed by [pyobvector](https://github.com/oceanbase/pyobvector) (`ObVecClient`). The API is modeled after [milvus-haystack](https://github.com/milvus-io/milvus-haystack) where practical.
- **Use Case**: Building RAG pipelines, semantic search, and hybrid dense+sparse retrieval on OceanBase tenants that expose `VECTOR` indexes and compatible SQL.
- **Documentation**: [OceanBase Haystack](./oceanbase-haystack/README.md)
- **Location in this repo**: [`./oceanbase-haystack/`](./oceanbase-haystack/)
- **CI**: The [main workflow](./.github/workflows/workflow.yml) runs Ruff, mocked unit tests (`pytest -m "not oceanbase"`), and a package build on pushes and PRs to `main`. An [extended workflow](./.github/workflows/oceanbase-haystack-ci.yml) runs a multi-version Python matrix and optional **OceanBase CE** live integration tests when files under `oceanbase-haystack/` change.
- **Requirements**: Python 3.9+, Haystack 2.x, and an OceanBase deployment with vector features enabled (see the component README for connection and index options).

---

## 📚 Full Documentation Links

| Plugin Name                           | Documentation Link                                                                      |
| ------------------------------------- | --------------------------------------------------------------------------------------- |
| Flyway OceanBase Plugin               | [Flyway OceanBase Plugin](./flyway-oceanbase-plugin/README.md)                             |
| Trino OceanBase Plugin                | [Trino OceanBase Plugin](https://github.com/oceanbase/trino-oceanbase)                      |
| WordPress OceanBase Plugin            | [WordPress OceanBase Plugin](./wordpress-oceanbase-plugin/README.md)                       |
| OceanBase SQL Helper Plugin           | [OceanBase SQL Helper Plugin](./oceanbase-sql-helper-plugin/README.md)                     |
| Metabase OceanBase Plugin             | [Metabase OceanBase Plugin](./metabase-oceanbase-plugin/README.md)                         |
| OceanBase SQLAlchemy Plugin           | [OceanBase SQLAlchemy Plugin](./oceanbase-sqlalchemy-plugin/README.md)                     |
| OceanBase Dify Plugin                 | [OceanBase Dify Plugin](./dify-plugin-oceanbase/README.md)                                 |
| LangGraph Checkpoint OceanBase Plugin | [LangGraph Checkpoint OceanBase Plugin](./langgraph-checkpoint-oceanbase-plugin/README.md) |
| Fluent Plugin OceanBase Logs          | [Fluent Plugin OceanBase Logs](./fluent-plugin-oceanbase-logs/README.md)                   |
| PyObsql OceanBase Plugin              | [PyObsql OceanBase Plugin](./pyobsql-oceanbase-plugin/README.md)                             |
| OceanBase CLI                         | [OceanBase CLI](./oceanbase-cli/README.md) · [Agent Skill](./skills/oceanbase-cli/SKILL.md)   |
| OceanBase Haystack                    | [OceanBase Haystack](./oceanbase-haystack/README.md)                                       |

---

## 📦 PyPI release workflows

Manual and tag-driven publishes use **`PYPI_API_TOKEN`** / **`TEST_PYPI_API_TOKEN`** repository secrets (same pattern as [Publish PyObsql to PyPI](./.github/workflows/publish-pyobsql-pypi.yml)). Use an **entire-account** or **project-scoped** token that is allowed to upload the target package.

| Workflow | Trigger | Package |
|----------|---------|---------|
| [publish-pyobsql-pypi.yml](./.github/workflows/publish-pyobsql-pypi.yml) | `workflow_dispatch` | `pyobsql` |
| [publish-oceanbase-cli-pypi.yml](./.github/workflows/publish-oceanbase-cli-pypi.yml) | `workflow_dispatch` or tag `release_oceanbase_cli_*` | `oceanbase-cli` |
| [publish-oceanbase-haystack-pypi.yml](./.github/workflows/publish-oceanbase-haystack-pypi.yml) | `workflow_dispatch` or tag `release_oceanbase_haystack_*` | `oceanbase-haystack` |

---

## 🛠️ Contributing & Feedback

We welcome contributions via **Issues** or **Pull Requests**.
For questions or suggestions, visit [GitHub Issues](https://github.com/oceanbase/ecology-plugins/issues).

---

## 📄 License

This project is licensed under the [Apache License 2.0](./LICENSE).

---

## 📌 Notes

- For detailed configuration and usage instructions, refer to the respective plugin documentation.
- Ensure OceanBase version compatibility (recommended ≥ 3.1.0 for general plugins).
- Plugins support MySQL/Oracle modes where applicable; select the appropriate version based on your environment.
- **Vector / Haystack**: [OceanBase Haystack](./oceanbase-haystack/README.md) depends on OceanBase **vector** capabilities and [pyobvector](https://github.com/oceanbase/pyobvector); verify your cluster version and vector-related parameters against that component’s documentation.
