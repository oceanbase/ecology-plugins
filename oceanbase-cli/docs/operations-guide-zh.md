# OceanBase CLI（`obcli`）操作手册

面向安装、配置与日常使用。策略示例：[examples/policy.example.json](../examples/policy.example.json)；源码说明：[developer-guide-zh.md](./developer-guide-zh.md)。

---

## 1. 概述

`obcli` 通过 **pymysql** 连接 **OceanBase / MySQL 协议**（`oceanbase://`、`mysql://`）：

- DSN **加密**保存在本机配置目录（不必把连接串放环境变量）。
- **`obcli sql`**：**无有效 `policy.json` 时仅允许只读类 SQL**；有效策略下由 **`block_rules`** 拦截写类语句（见第 6、7 节）。**不能**用 CLI 开关或环境变量跳过 `policy.json`。
- 策略路径、当前是否托管写权限：用 **`obcli rules show`** 或 **`obcli rules metadata`**（字段 **`policy_governs_writes`** 等）。

**限制：** **`policy.json` 仅作用于 `obcli sql`。** `status`、`schema tables` 不读策略。

---

## 2. 安装

```bash
cd /path/to/repo
pip install -e ./oceanbase-cli
obcli --version
```

---

## 3. 配置目录

| 条件 | obcli 配置目录 |
|------|----------------|
| 未设置 `XDG_CONFIG_HOME` | `~/.config/obcli/` |
| 已设置 | `$XDG_CONFIG_HOME/obcli/` |

常用文件：**`dsn.enc`**（加密 DSN）、**`.obcli-key`**（密钥）、**`policy.json`**（可选）。

持久化修改 `XDG_CONFIG_HOME` 可写入 `~/.zshrc` / `~/.bashrc`：

```bash
export XDG_CONFIG_HOME="$HOME/my-config"
mkdir -p "$XDG_CONFIG_HOME/obcli"
```

查看路径与文件是否存在：

```bash
obcli --format json config status
```

---

## 4. DSN

**格式示例：** `oceanbase://user:password@host:2881/database_name`  
URL 里未写端口时默认为 **3306**；OceanBase 常见为 **2881**，建议在 DSN 里写清。

**OceanBase 账号（二段式 / 三段式，未编码写法）：**  
- **二段式**（`用户@租户` + 密码）：`oceanbase://mysqluser@mytenant:你的密码@主机:端口/库名`  
- **三段式**（`用户@租户#集群` + 密码）：`oceanbase://mysqluser@mytenant#mycluster:你的密码@主机:端口/库名`  

用户名与密码之间用**第一个** `:` 分隔。二段 / 三段**可直接写未转义**的 `@`、`#`，由 **`obcli` 内部编码**；触发条件：`oceanbase://` 且（含 **`#`**，或 `//` 后 **`@` 不少于 2 个**），再按「最后一个 `@主机:端口/库`」拆分。密码里若含**未编码的 `:`**，须写成 `%3A`。若整条 DSN 已用手工 **`%40` / `%23`** 写好，则走标准 URL 解析，**不会**二次编码。

**写入加密 DSN（推荐，避免出现在 `ps` 参数里）：**

```bash
printf '%s' 'oceanbase://user:pass@10.0.0.1:2881/mydb' | obcli config set-dsn
```

**注意：** DSN 里若含 **`%40`、`%23`** 等百分号编码，必须用 **`printf '%s' '整段URL'`**（先写 **`%s`**，URL 放在引号里）。不要写成 **`printf 'oceanbase://...%40...'`**，否则 shell 会把 **`%40`** 当成 `printf` 的格式指令，报错 **`invalid directive`**，且管道里可能只传了半截错误内容。

**本次进程临时覆盖：**

```bash
obcli --dsn 'oceanbase://...' --format json sql "SELECT 1"
```

**清除：**

```bash
obcli config clear-dsn
```

---

## 5. 全局选项

| 选项 | 说明 |
|------|------|
| `--format json\|table\|csv\|jsonl` | 输出格式，默认 `json` |
| `--dsn '...'` | 覆盖本次使用的 DSN |

---

## 6. `obcli sql`

1. 校验 DSN 与 SQL 非空。  
2. 若磁盘上存在且能解析为 **非空 JSON 对象**的 **`policy.json`**：先做 **`block_rules`**，命中 **`deny`** 则拒绝（**`POLICY_DENIED`**）。  
3. **「可托管写」**即上一步策略已加载：此时写类 SQL 才可能执行（仍受 **`block_rules`** 约束）。若**无文件**、**解析失败**，或文件解析结果是 **空对象 `{}`**：写类 SQL 一律 **`OBCLI-NO-WRITE`**。  
4. 执行 SQL；在已加载策略且配置了 **`limits.max_result_rows`** 时，结果行可能被截断（JSON 可出现 `truncated`、`max_result_rows`、`row_count_returned`）。

**写类 SQL（内置分类）：** 以 `INSERT`、`UPDATE`、`DELETE`、`REPLACE`、`ALTER`、`CREATE`、`DROP`、`TRUNCATE`、`RENAME` 等开头的语句。要允许写，须部署合法 **`policy.json`**；要禁止某一类，在 **`block_rules`** 里写对应正则。

| 场景 | 写类 SQL |
|------|----------|
| 无文件，或 JSON 损坏无法解析 | 不允许（**`OBCLI-NO-WRITE`**） |
| 文件存在但内容为 **空对象 `{}`** | 不允许（**`OBCLI-NO-WRITE`**） |
| 有非空策略对象（例如含 **`block_rules`** / **`limits`**） | 由 **`block_rules`** 决定拦或放行 |

---

## 7. `policy.json`

路径：**`配置目录/policy.json`**。

**说明：** 无「跳过 `policy.json`」开关。文件存在、能解析为 **JSON 对象**（`{...}`，不能是数组等）且对象**非空**时走策略步骤；**`policy_governs_writes`** 在上述条件满足时为 `true`。

### 字段

| 字段 | 说明 |
|------|------|
| **`block_rules`** | 数组；每条含 **`id`**、**`action":"deny"`**、**`message`**、**`match.sql_pattern`**（对**整条 SQL** 做 `re.search`） |
| **`limits`**（可选） | **`max_result_rows`**：正整数时截断查询返回行数 |

（若存在其它键名，当前版本会**忽略**；不要求也不校验 **`version`** 字段。）

**JSON 里写正则：** 需要 `\s`、`\b` 时在字符串里写成 **`\\s`**、**`\\b`**。多写反斜杠会导致规则不命中。

**示例（禁止 DML、禁止 DDL）：**

```json
{
  "block_rules": [
    {
      "id": "DENY-DML",
      "match": { "sql_pattern": "(?i)^\\s*(INSERT|UPDATE|DELETE|REPLACE)\\b" },
      "action": "deny",
      "message": "DML not allowed"
    },
    {
      "id": "DENY-DDL",
      "match": { "sql_pattern": "(?i)^\\s*(ALTER|CREATE|DROP|TRUNCATE|RENAME)\\b" },
      "action": "deny",
      "message": "DDL not allowed"
    }
  ],
  "limits": { "max_result_rows": 5000 }
}
```

完整可复制示例：[policy.example.json](../examples/policy.example.json)。

---

## 8. 其他命令

| 命令 | 作用 |
|------|------|
| `obcli config set-dsn` | 从 stdin 读 DSN → 加密保存 |
| `obcli config clear-dsn` | 删除加密 DSN |
| `obcli config status` | 配置目录、密钥、DSN、策略文件是否存在 |
| `obcli rules show` / `metadata` / `explain` | 策略路径、`cli_version`、`policy_governs_writes` 等 |
| `obcli status` | 探测连接 |
| `obcli schema tables` | 列出当前库表名 |

**`policy_governs_writes`：** `policy.json` 存在、能解析且根对象非空时为 `true`。

---

## 9. 环境变量

| 变量 | 作用 |
|------|------|
| `XDG_CONFIG_HOME` | 配置根目录（见第 3 节） |
| `OBCLI_AUDIT_LOG` | 审计 JSONL 路径；不设则默认 `配置目录/audit.jsonl` |
| `OBCLI_AUDIT_DISABLED` | 为 `1` 时不写审计 |

---

## 10. 排错

| 现象 | 处理 |
|------|------|
| `NO_DSN` | `set-dsn` 或传 `--dsn` |
| `OBCLI-NO-WRITE` | 需要写类 SQL 时：在配置目录放置合法 **`policy.json`**（并由 **`block_rules`** 放行） |
| `POLICY_DENIED` | 命中 **`block_rules`** 的 **`deny`**；若以为该命中却未命中：检查 JSON 中正则 **反斜杠是否多写** |
| 以为 `status`/`schema` 也走策略 | 仅 **`sql`** 走 `policy.json` |

退出码：成功 `0`；用法错误常见 `2`；其它错误见 CLI 输出中的 `exit_code`。

---

## 11. 推荐阅读

- [README.md](../README.md)  
- [skills/oceanbase-cli/SKILL.md](../../skills/oceanbase-cli/SKILL.md)（Agent 约束）
