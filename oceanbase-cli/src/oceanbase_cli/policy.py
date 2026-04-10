from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import click

from oceanbase_cli import audit, output
from oceanbase_cli.clickutil import root_context
from oceanbase_cli.dsn import database_from_dsn
from oceanbase_cli.paths import local_policy_path


def _load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_local_policy() -> dict[str, Any] | None:
    """Optional ~/.config/obcli/policy.json: root must be a JSON object (dict)."""
    data = _load_json_file(local_policy_path())
    return data if isinstance(data, dict) else None


def local_policy_governs_writes() -> bool:
    """True when policy.json exists, parses, and is non-empty; writes allowed unless a block_rule matches."""
    pol = load_local_policy()
    return bool(pol)


def get_policy_row_limit() -> int | None:
    """Top-level limits.max_result_rows in policy.json, or None."""
    pol = load_local_policy()
    if not pol:
        return None
    limits = pol.get("limits")
    if not isinstance(limits, dict):
        return None
    raw = limits.get("max_result_rows")
    if raw is None:
        return None
    try:
        n = int(raw)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def evaluate_local_block_rules(sql_text: str, policy: dict[str, Any]) -> tuple[str, str] | None:
    for rule in policy.get("block_rules") or []:
        if not isinstance(rule, dict):
            continue
        if rule.get("action") != "deny":
            continue
        pat = (rule.get("match") or {}).get("sql_pattern")
        if not pat:
            continue
        try:
            if re.search(pat, sql_text):
                rid = rule.get("id") or "PLAT-RULE"
                msg = rule.get("message") or "blocked by local policy"
                return (str(rid), str(msg))
        except re.error:
            continue
    return None


def apply_pre_sql_policy(sql_text: str, ctx: click.Context) -> None:
    """Evaluate policy.json block_rules when the file exists and parses."""
    root = root_context(ctx)
    fmt = str(root.obj.get("format") or "json")
    dsn = root.obj.get("dsn")

    pol = load_local_policy()
    if not pol:
        return
    reason = evaluate_local_block_rules(sql_text, pol)
    if not reason:
        return
    rid, msg = reason
    audit.emit(
        {
            "action": "sql.execute",
            "outcome": "denied",
            "deny_reason": rid,
            "message": msg,
            "database": database_from_dsn(dsn),
        }
    )
    output.error(
        "POLICY_DENIED",
        msg,
        fmt=fmt,
        extra={"rule_id": rid},
        exit_code=output.EXIT_USAGE_ERROR,
    )
