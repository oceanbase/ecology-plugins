"""`obcli sql` — read-only when policy.json is absent; DML/DDL only when policy.json is present and enforced."""

from __future__ import annotations

import click

from oceanbase_cli import audit, output
from oceanbase_cli.clickutil import output_fmt, root_context
from oceanbase_cli.dsn import database_from_dsn
from oceanbase_cli.executor import execute_sql
from oceanbase_cli.policy import apply_pre_sql_policy, get_policy_row_limit, local_policy_governs_writes
from oceanbase_cli.sql_classification import is_write_sql


@click.command("sql")
@click.argument("statement", required=False)
@click.pass_context
def sql_cmd(ctx: click.Context, statement: str | None) -> None:
    root = root_context(ctx)
    fmt = output_fmt(ctx)
    dsn = root.obj.get("dsn")
    if not dsn:
        output.error(
            "NO_DSN",
            "No DSN: use `printf '%s' 'oceanbase://...' | obcli config set-dsn` or pass --dsn (not recommended for agents).",
            fmt=fmt,
            exit_code=output.EXIT_USAGE_ERROR,
        )
    if not statement or not statement.strip():
        output.error("USAGE", "Missing SQL statement.", fmt=fmt, exit_code=output.EXIT_USAGE_ERROR)

    sql_text = statement.strip()
    apply_pre_sql_policy(sql_text, ctx)
    policy_governs_writes = local_policy_governs_writes()

    if is_write_sql(sql_text) and not policy_governs_writes:
        audit.emit(
            {
                "action": "sql.execute",
                "outcome": "denied",
                "deny_reason": "OBCLI-NO-WRITE",
                "message": "obcli only executes read-only SQL (SELECT/SHOW/DESC/EXPLAIN/…) without a valid policy.json.",
                "database": database_from_dsn(dsn),
            }
        )
        output.error(
            "POLICY_DENIED",
            "obcli only executes read-only SQL without a valid policy.json. Add policy.json (block_rules) to allow DML/DDL; deny rules still apply.",
            fmt=fmt,
            extra={"rule_id": "OBCLI-NO-WRITE"},
            exit_code=output.EXIT_USAGE_ERROR,
        )

    try:
        with output.Timer() as t:
            columns, rows, affected = execute_sql(dsn, sql_text)
    except Exception as e:
        output.error("SQL_ERROR", str(e), fmt=fmt, exit_code=output.EXIT_BIZ_ERROR)

    row_limit = get_policy_row_limit()
    extra_out: dict[str, object] | None = None
    if row_limit is not None and len(rows) > row_limit:
        rows = rows[:row_limit]
        extra_out = {
            "truncated": True,
            "max_result_rows": row_limit,
            "row_count_returned": len(rows),
        }

    if is_write_sql(sql_text) and policy_governs_writes:
        audit.emit(
            {
                "action": "sql.execute",
                "outcome": "allowed",
                "message": "write SQL executed (policy.json governs)",
                "policy_governs_writes": True,
                "database": database_from_dsn(dsn),
            }
        )

    output.success_rows(
        columns,
        rows,
        affected=max(affected, 0),
        time_ms=t.elapsed_ms,
        fmt=fmt,
        extra=extra_out,
    )
