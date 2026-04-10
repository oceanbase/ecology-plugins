"""`obcli status` — connection probe (MySQL protocol or local embedded SQLite)."""

from __future__ import annotations

import click

from oceanbase_cli import output
from oceanbase_cli.clickutil import output_fmt, root_context
from oceanbase_cli.dsn import is_embedded_dsn, is_mysql_protocol_dsn, parse_embedded_dsn
from oceanbase_cli.executor import execute_sql


@click.command("status")
@click.pass_context
def status_cmd(ctx: click.Context) -> None:
    root = root_context(ctx)
    fmt = output_fmt(ctx)
    dsn = root.obj.get("dsn")
    if not dsn:
        output.error(
            "NO_DSN",
            "No DSN: use `obcli config set-dsn` (stdin) or pass --dsn for local override only.",
            fmt=fmt,
            exit_code=output.EXIT_USAGE_ERROR,
        )

    if is_embedded_dsn(dsn):
        cfg = parse_embedded_dsn(dsn)
        output.success(
            {
                "mode": "embedded_sqlite",
                "path": cfg.path,
                "logical_database": cfg.database,
                "connected": True,
            },
            fmt=fmt,
        )

    if is_mysql_protocol_dsn(dsn):
        try:
            cols, rows, _ = execute_sql(dsn, "SELECT VERSION() AS version, DATABASE() AS current_db")
        except Exception as e:
            output.error("CONNECT_ERROR", str(e), fmt=fmt, exit_code=output.EXIT_BIZ_ERROR)
        row = rows[0] if rows else {}
        output.success(
            {
                "mode": "mysql_protocol",
                "connected": True,
                "version": row.get("version"),
                "current_db": row.get("current_db"),
            },
            fmt=fmt,
        )

    output.error(
        "BAD_DSN",
        "Unsupported DSN for status. Use oceanbase://, mysql://, or embedded:.",
        fmt=fmt,
        exit_code=output.EXIT_USAGE_ERROR,
    )
