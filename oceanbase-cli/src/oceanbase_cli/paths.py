from __future__ import annotations

import os
from pathlib import Path


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "obcli"
    return Path.home() / ".config" / "obcli"


def encrypted_dsn_path() -> Path:
    return config_dir() / "dsn.enc"


def local_policy_path() -> Path:
    """Optional JSON: block_rules + optional limits."""
    return config_dir() / "policy.json"


def user_config_json_path() -> Path:
    """Legacy path; obcli ignores allow_write_sql — kept for human reference only."""
    return config_dir() / "config.json"


def default_audit_log_path() -> Path:
    p = os.environ.get("OBCLI_AUDIT_LOG")
    if p:
        return Path(p)
    return config_dir() / "audit.jsonl"
