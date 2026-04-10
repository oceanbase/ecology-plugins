from __future__ import annotations

import click

from oceanbase_cli import __version__, output
from oceanbase_cli.clickutil import output_fmt
from oceanbase_cli.constants import BUILTIN_RULE_SET_VERSION
from oceanbase_cli.paths import (
    config_dir,
    encrypted_dsn_path,
    local_policy_path,
    user_config_json_path,
)
from oceanbase_cli.policy import load_local_policy, local_policy_governs_writes


def _rules_common_fields() -> dict[str, object]:
    return {
        "builtin_rule_set_version": BUILTIN_RULE_SET_VERSION,
        "sql_writes_supported": False,
        "sql_writes_opt_in_flag": None,
        "policy_governs_writes": local_policy_governs_writes(),
    }


@click.group("rules")
def rules_group() -> None:
    """Inspect optional policy.json and paths (writes require a valid policy.json)."""


@rules_group.command("show")
@click.pass_context
def rules_show(ctx: click.Context) -> None:
    fmt = output_fmt(ctx)
    pol = load_local_policy()
    output.success(
        {
            **_rules_common_fields(),
            "config_dir": str(config_dir()),
            "user_config_json_path": str(user_config_json_path()),
            "user_config_json_present": user_config_json_path().is_file(),
            "encrypted_dsn_path": str(encrypted_dsn_path()),
            "encrypted_dsn_present": encrypted_dsn_path().is_file(),
            "policy_path": str(local_policy_path()),
            "policy": pol,
        },
        fmt=fmt,
    )


@rules_group.command("metadata")
@click.pass_context
def rules_metadata(ctx: click.Context) -> None:
    fmt = output_fmt(ctx)
    output.success(
        {
            "cli_version": __version__,
            "entry": "obcli",
            **_rules_common_fields(),
            "config_dir": str(config_dir()),
            "user_config_json_path": str(user_config_json_path()),
        },
        fmt=fmt,
    )


@rules_group.command("explain")
@click.option("--action", type=click.Choice(["sql"]), default="sql", help="Execution pipeline to describe.")
@click.pass_context
def rules_explain(ctx: click.Context, action: str) -> None:
    fmt = output_fmt(ctx)
    if action == "sql":
        checkpoints = [
            {"step": 1, "id": "DSN", "detail": "Resolve DSN from encrypted store or explicit --dsn (avoid argv for secrets)."},
            {"step": 2, "id": "POLICY.JSON", "detail": "If policy.json exists and parses: block_rules (regex deny) + optional limits.max_result_rows. No flag or env to skip."},
            {"step": 3, "id": "OBCLI-NO-WRITE", "detail": "Without policy.json (missing, empty, or invalid JSON): write-class SQL rejected. With policy: block_rules only; config.json never enables writes."},
            {"step": 4, "id": "EXECUTE", "detail": "pymysql / embedded SQLite; DML/DDL per step 3 and policy."},
            {"step": 5, "id": "AUDIT", "detail": "Denied path may emit JSONL (default: <config-dir>/audit.jsonl; see OBCLI_AUDIT_LOG)."},
        ]
        output.success({"action": "sql", "checkpoints": checkpoints}, fmt=fmt)
