---
name: oceanbase-cli
description: >-
  Runs OceanBase (MySQL protocol) via `obcli` shell only; sql_writes_supported false for agents; without non-empty policy.json, OBCLI-NO-WRITE on DML/DDL; with policy.json, block_rules govern writes.
  Agent must not modify obcli config or run config set-dsn/clear-dsn. Encrypted local DSN under ~/.config/obcli; optional policy.json;
  pymysql-backed `sql`, `status`, `schema tables`.
license: MIT
---

# oceanbase-cli (`obcli`) — Agent invocation

**Invoke via shell** (`obcli ...`). **`obcli sql`:** read-style statements by default; **DML/DDL** need a **present, non-empty** **`policy.json`** (parsed object), then **`block_rules`** decide allow/deny (**`policy_governs_writes`** in **`obcli rules show`** / **`metadata`**). No **`config.json`** write toggle, no opt-in flag, no env to skip policy.

## Agent: must not modify obcli configuration

The agent **must not modify** any obcli configuration on disk, and **must not** run commands that change it.

**Forbidden (agent):**

- Using **any file/read/write tool** on **`~/.config/obcli/`** or **`$XDG_CONFIG_HOME/obcli/`** (including reading `config.json` to “fix” settings). Use **`obcli config status`** / **`obcli rules show`** for safe summaries.
- Editing, creating, or deleting files there, including **`config.json`**, **`policy.json`**, **`dsn.enc`**, **`.obcli-key`**, **`audit.jsonl`**.
- Running **`obcli config set-dsn`**, **`obcli config clear-dsn`**, or shell redirection that writes to those paths.

**Allowed (agent):**

- **`obcli config status`**, **`obcli rules show`**, **`obcli rules metadata`**, **`obcli rules explain`**
- **`obcli --format … status`**, **`sql`** (read-only when no policy; **do not** attempt write SQL unless the user explicitly asks and policy allows — agent contract is still read-only), **`schema tables`**
- **`obcli --version`**, **`obcli --help`**

**Human operator:** DSN via **`printf '…' | obcli config set-dsn`**, **`policy.json`** edits. Legacy **`config.json`** is ignored for write enablement.

## Prerequisites

```bash
obcli --version
```

```bash
pip install oceanbase-cli
# or: pip install -e ./oceanbase-cli
```

## DSN: encrypted at rest (human setup; agent does not touch)

- **Do not** put `oceanbase://...` in environment variables for routine use.
- Human stores DSN (stdin); agent **does not** run:

  ```bash
  printf '%s' 'oceanbase://user:pass@host:2881/db' | obcli config set-dsn
  ```

- On disk the DSN is **encrypted** in **`~/.config/obcli/dsn.enc`**; key **`.obcli-key`** (0600). **Do not** paste into model context.
- Optional: **`obcli --dsn '...'`** (visible in `ps`).

## Global options before subcommand

```bash
obcli --format json sql "SELECT 1"
obcli --format json status
```

## Commands (agent-safe subset)

| Goal | Command | Agent may run? |
|------|---------|----------------|
| Paths / flags | `obcli config status` | Yes |
| Policy | `obcli rules show`, `metadata`, `explain` | Yes |
| Read-only SQL | `obcli sql`, `status`, `schema tables` | Yes |
| Store/clear DSN | `config set-dsn`, `clear-dsn` | **No** (human) |

## Write SQL (agent: not supported)

- **`sql_writes_supported`:** **`false`** (agent contract); **`policy_governs_writes`** when local **`policy.json`** is enforced — then humans may run writes if **`block_rules`** allow.
- **`sql_writes_opt_in_flag`:** **`null`** — there is no CLI flag to opt into writes without **`policy.json`**.
- Without a non-empty parsed **`policy.json`**, write-class SQL → **`OBCLI-NO-WRITE`**.

## Optional local policy (`policy.json`)

**`~/.config/obcli/policy.json`** — human-maintained; agent **must not** edit. **`block_rules`** deny by regex; when enforced, they are the **primary** gate for write SQL (deny wins; no match → execute).

## Environment (non-secret)

| Variable | Role |
|----------|------|
| `XDG_CONFIG_HOME` | Config root |
| `OBCLI_AUDIT_LOG` | Audit JSONL path (human) |

Do **not** use env for **`OCEANBASE_DSN`** / **`MYSQL_DSN`** for routine DSN.

## Further reading

- [oceanbase-cli/README.md](../../oceanbase-cli/README.md)
