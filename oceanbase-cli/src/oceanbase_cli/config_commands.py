"""`obcli config` — encrypted DSN on disk (no env vars for connection strings)."""

from __future__ import annotations

import sys

import click

from oceanbase_cli import output
from oceanbase_cli.clickutil import output_fmt
from oceanbase_cli.credentials_store import clear_encrypted_dsn, store_encrypted_dsn
from oceanbase_cli.paths import config_dir, encrypted_dsn_path, local_policy_path


@click.group("config")
def config_group() -> None:
    """Local encrypted DSN and paths (no cloud platform)."""


@config_group.command("set-dsn")
@click.pass_context
def config_set_dsn(ctx: click.Context) -> None:
    """Read DSN from stdin (one connection string). Do not pass the DSN on the command line (visible in ps)."""
    fmt = output_fmt(ctx)
    raw = sys.stdin.read()
    try:
        store_encrypted_dsn(raw)
    except ValueError as e:
        output.error("INVALID_DSN", str(e), fmt=fmt, exit_code=output.EXIT_USAGE_ERROR)
    p = encrypted_dsn_path()
    output.success(
        {
            "stored": True,
            "path": str(p),
            "hint": "Run obcli without --dsn to use this encrypted DSN.",
        },
        fmt=fmt,
    )


@config_group.command("clear-dsn")
@click.pass_context
def config_clear_dsn(ctx: click.Context) -> None:
    fmt = output_fmt(ctx)
    clear_encrypted_dsn()
    output.success({"cleared": True}, fmt=fmt)


@config_group.command("status")
@click.pass_context
def config_status(ctx: click.Context) -> None:
    fmt = output_fmt(ctx)
    dsn_file = encrypted_dsn_path()
    key_file = config_dir() / ".obcli-key"
    output.success(
        {
            "config_dir": str(config_dir()),
            "sql_writes_supported": False,
            "encrypted_dsn_present": dsn_file.is_file(),
            "encrypted_dsn_path": str(dsn_file),
            "key_present": key_file.is_file(),
            "policy_file": str(local_policy_path()),
            "policy_present": local_policy_path().is_file(),
        },
        fmt=fmt,
    )
