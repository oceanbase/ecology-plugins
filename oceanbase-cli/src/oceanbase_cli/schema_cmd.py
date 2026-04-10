"""`obcli schema` — minimal table listing (MySQL / OceanBase or embedded SQLite)."""

from __future__ import annotations

import click

from oceanbase_cli import output
from oceanbase_cli.clickutil import output_fmt, root_context
from oceanbase_cli.dsn import is_embedded_dsn, is_mysql_protocol_dsn
from oceanbase_cli.executor import execute_sql


@click.group("schema")
def schema_group() -> None:
    """Schema introspection."""


@schema_group.command("tables")
@click.pass_context
def schema_tables(ctx: click.Context) -> None:
    root = root_context(ctx)
    fmt = output_fmt(ctx)
    dsn = root.obj.get("dsn")
    if not dsn:
        output.error(
            "NO_DSN",
            "No DSN: use `obcli config set-dsn` (stdin) or --dsn for local override.",
            fmt=fmt,
            exit_code=output.EXIT_USAGE_ERROR,
        )

    if is_embedded_dsn(dsn):
        sql = (
            "SELECT name AS table_name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    elif is_mysql_protocol_dsn(dsn):
        sql = (
            "SELECT TABLE_NAME AS table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() ORDER BY TABLE_NAME"
        )
    else:
        output.error(
            "BAD_DSN",
            "Unsupported DSN for schema tables.",
            fmt=fmt,
            exit_code=output.EXIT_USAGE_ERROR,
        )

    try:
        columns, rows, _ = execute_sql(dsn, sql)
    except Exception as e:
        output.error("SQL_ERROR", str(e), fmt=fmt, exit_code=output.EXIT_BIZ_ERROR)

    output.success_rows(columns, rows, fmt=fmt)
