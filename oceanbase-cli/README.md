# oceanbase-cli (`obcli`)

**OceanBase / MySQL protocol** CLI (**pymysql**):

- **Encrypted DSN** under `~/.config/obcli/` (or `$XDG_CONFIG_HOME/obcli/`).
- **`obcli sql`** — read-only without **`policy.json`**; with a valid **`policy.json`**, DML/DDL follow **`block_rules`** (no CLI flag or env to skip policy).
- **Chinese ops guide:** [docs/operations-guide-zh.md](./docs/operations-guide-zh.md) · **Policy sample:** [examples/policy.example.json](./examples/policy.example.json)

Design note (historical): [docs/cloud-platform-token-cli-skills-design.md](../docs/cloud-platform-token-cli-skills-design.md)

**Agent skill:** [skills/oceanbase-cli/SKILL.md](../skills/oceanbase-cli/SKILL.md) · **Architecture (中文):** [docs/architecture-components-zh.md](./docs/architecture-components-zh.md)

## Install

```bash
pip install -e ./oceanbase-cli
```

Dependencies: `click`, `cryptography`, `pymysql`. Optional **`oceanbase_cli.connection_pool`** for other tools; **`obcli`** uses one connection per command via `executor`.

## Store DSN (stdin)

```bash
printf '%s' 'oceanbase://user:pass@host:2881/db' | obcli config set-dsn
obcli config status
```

Avoid `obcli --dsn '...'` where argv is visible in `ps`.

## Commands

| Command | Purpose |
|---------|---------|
| `obcli config set-dsn` / `clear-dsn` / `status` | Encrypted DSN + paths |
| `obcli rules show` / `metadata` / `explain` | `policy.json` + **`policy_governs_writes`** 等 |
| `obcli sql`, `status`, `schema tables` | Data plane |

## Publishing to PyPI (maintainers)

Releases are automated from [ecology-plugins](https://github.com/oceanbase/ecology-plugins): workflow **[`publish-oceanbase-cli-pypi.yml`](../.github/workflows/publish-oceanbase-cli-pypi.yml)** (same Twine + token pattern as [publish-pyobsql-pypi.yml](../.github/workflows/publish-pyobsql-pypi.yml)).

- **Manual run**: Actions → *Publish OceanBase CLI to PyPI* → *Run workflow* (optional version override, Test PyPI toggle).
- **Tag push**: push a tag matching `release_oceanbase_cli_*` after bumping `version` in [`pyproject.toml`](./pyproject.toml).

Configure repository secrets **`PYPI_API_TOKEN`** / **`TEST_PYPI_API_TOKEN`** as in the monorepo [root README](../README.md#-pypi-release-workflows).

## Tests

```bash
cd oceanbase-cli && pip install -e ".[dev]" && pytest tests/ -v
```

## Debug

`OBCLI_AUDIT_LOG` / `OBCLI_AUDIT_DISABLED` — audit JSONL.
