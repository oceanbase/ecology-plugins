"""obcli — default read-only SQL, encrypted local DSN, MySQL protocol via pymysql."""

from __future__ import annotations

import click

from oceanbase_cli import __version__
from oceanbase_cli.config_commands import config_group
from oceanbase_cli.credentials_store import load_encrypted_dsn
from oceanbase_cli.rules_commands import rules_group
from oceanbase_cli.schema_cmd import schema_group
from oceanbase_cli.sql_cmd import sql_cmd
from oceanbase_cli.status_cmd import status_cmd


@click.group(invoke_without_command=True)
@click.option(
    "--dsn",
    default=None,
    help="Override DSN for this process only (visible in ps — avoid in agent workflows). "
    "Default: decrypt ~/.config/obcli/dsn.enc (use `obcli config set-dsn` from stdin).",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "table", "csv", "jsonl"]),
    default="json",
    help="Output format.",
)
@click.version_option(__version__, prog_name="obcli")
@click.pass_context
def cli(ctx: click.Context, dsn: str | None, fmt: str) -> None:
    """OceanBase CLI — encrypted local DSN, default read-only; data plane uses pymysql."""
    ctx.ensure_object(dict)
    ctx.obj["dsn"] = (dsn.strip() if dsn else None) or load_encrypted_dsn()
    ctx.obj["format"] = fmt

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(config_group, name="config")
cli.add_command(rules_group, name="rules")
cli.add_command(sql_cmd, name="sql")
cli.add_command(status_cmd, name="status")
cli.add_command(schema_group, name="schema")
