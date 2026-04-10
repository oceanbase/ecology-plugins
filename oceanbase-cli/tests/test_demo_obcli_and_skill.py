"""Tests: encrypted DSN, read-only sql only, optional policy.json; skill doc checklist.

Run: cd oceanbase-cli && pip install -e ".[dev]" && pytest tests/test_demo_obcli_and_skill.py -v
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from oceanbase_cli import credentials_store
from oceanbase_cli.main import cli

_WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
_SKILL_MD = _WORKSPACE_ROOT / "skills" / "oceanbase-cli" / "SKILL.md"


def _json_line(s: str) -> dict:
    s = s.strip()
    if not s:
        return {}
    return json.loads(s)


@pytest.fixture
def isolated_obcli_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    cfg = tmp_path / "config"
    cache = tmp_path / "cache"
    cfg.mkdir()
    cache.mkdir()
    db = cfg / "demo.db"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache))

    key = Fernet.generate_key()
    credentials_store.set_test_encryption_key(key)
    try:
        credentials_store.store_encrypted_dsn(f"embedded:{db}")
        policy = {
            "block_rules": [
                {
                    "id": "PLAT-MOCK-GRANT",
                    "match": {"sql_pattern": r"(?i)^\s*GRANT\b"},
                    "action": "deny",
                    "message": "GRANT blocked in mock policy",
                }
            ],
        }
        (cfg / "obcli" / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
        yield os.environ.copy()
    finally:
        credentials_store.set_test_encryption_key(None)


def test_skill_md_exists_and_covers_agent_requirements() -> None:
    assert _SKILL_MD.is_file(), f"Expected skill at {_SKILL_MD}"
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert "name: oceanbase-cli" in text
    required = [
        "obcli",
        "shell",
        "--format",
        "config",
        "set-dsn",
        "rules show",
        "OBCLI-NO-WRITE",
        "encrypted",
        "must not modify",
        "Forbidden (agent)",
        "sql_writes_supported",
    ]
    missing = [k for k in required if k not in text]
    assert not missing, f"SKILL.md missing keywords: {missing}"


def test_rules_metadata_and_show(isolated_obcli_env: dict[str, str]) -> None:
    runner = CliRunner()
    r = runner.invoke(cli, ["--format", "json", "rules", "metadata"], env=isolated_obcli_env)
    assert r.exit_code == 0, r.output
    data = _json_line(r.output)
    d0 = data.get("data") or {}
    assert d0.get("entry") == "obcli"
    assert d0.get("sql_writes_supported") is False
    assert d0.get("sql_writes_opt_in_flag") is None
    assert d0.get("policy_governs_writes") is True

    r = runner.invoke(cli, ["--format", "json", "rules", "show"], env=isolated_obcli_env)
    assert r.exit_code == 0, r.output
    data = _json_line(r.output)
    d = data.get("data") or {}
    assert d.get("encrypted_dsn_present") is True
    assert d.get("sql_writes_supported") is False
    assert d.get("sql_writes_opt_in_flag") is None
    assert d.get("policy_governs_writes") is True
    assert d.get("policy") is not None


def test_config_status(isolated_obcli_env: dict[str, str]) -> None:
    runner = CliRunner()
    r = runner.invoke(cli, ["--format", "json", "config", "status"], env=isolated_obcli_env)
    assert r.exit_code == 0, r.output
    data = _json_line(r.output)
    assert (data.get("data") or {}).get("encrypted_dsn_present") is True


def test_sql_select_embedded(isolated_obcli_env: dict[str, str]) -> None:
    runner = CliRunner()
    r = runner.invoke(cli, ["--format", "json", "sql", "SELECT 1 AS n"], env=isolated_obcli_env)
    assert r.exit_code == 0, r.output
    data = _json_line(r.output)
    assert data.get("ok") is True
    rows = data.get("rows") or []
    assert rows and (rows[0].get("n") == 1 or rows[0].get("1") == 1)


def test_policy_blocks_grant(isolated_obcli_env: dict[str, str]) -> None:
    runner = CliRunner()
    r = runner.invoke(
        cli,
        ["--format", "json", "sql", "GRANT SELECT ON *.* TO x"],
        env=isolated_obcli_env,
    )
    assert r.exit_code == 2, r.output
    assert "PLAT-MOCK-GRANT" in r.output or "POLICY_DENIED" in r.output


def test_write_sql_always_denied(isolated_obcli_env: dict[str, str]) -> None:
    """Without policy.json, INSERT is rejected; config.json cannot enable writes."""
    cfg_home = Path(isolated_obcli_env["XDG_CONFIG_HOME"])
    (cfg_home / "obcli" / "policy.json").unlink(missing_ok=True)
    (cfg_home / "obcli" / "config.json").write_text(
        json.dumps({"allow_write_sql": True, "disable_write_sql": False}),
        encoding="utf-8",
    )
    runner = CliRunner()
    r = runner.invoke(
        cli,
        ["--format", "json", "sql", "INSERT INTO t_obcli_demo (c) VALUES (1)"],
        env=isolated_obcli_env,
    )
    assert r.exit_code == 2, r.output
    assert "OBCLI-NO-WRITE" in r.output


def test_write_sql_without_writer_when_policy_governs(isolated_obcli_env: dict[str, str]) -> None:
    """With enforced policy.json, DML is allowed if block_rules do not match."""
    runner = CliRunner()
    env = {**isolated_obcli_env, "OBCLI_AUDIT_DISABLED": "1"}
    r = runner.invoke(
        cli,
        ["--format", "json", "sql", "CREATE TABLE IF NOT EXISTS t_gov (id INTEGER PRIMARY KEY)"],
        env=env,
    )
    assert r.exit_code == 0, r.output
    r2 = runner.invoke(
        cli,
        ["--format", "json", "sql", "INSERT INTO t_gov (id) VALUES (42)"],
        env=env,
    )
    assert r2.exit_code == 0, r2.output


def test_write_sql_denied_when_policy_blocks_insert(isolated_obcli_env: dict[str, str]) -> None:
    cfg = Path(isolated_obcli_env["XDG_CONFIG_HOME"]) / "obcli"
    policy = {
        "block_rules": [
            {
                "id": "NO-INSERT",
                "match": {"sql_pattern": r"(?i)^\s*INSERT\b"},
                "action": "deny",
                "message": "INSERT blocked by policy",
            }
        ],
    }
    (cfg / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
    runner = CliRunner()
    r = runner.invoke(
        cli,
        ["--format", "json", "sql", "INSERT INTO any_table (c) VALUES (1)"],
        env=isolated_obcli_env,
    )
    assert r.exit_code == 2, r.output
    assert "NO-INSERT" in r.output or "POLICY_DENIED" in r.output


def test_max_result_rows_truncates(isolated_obcli_env: dict[str, str]) -> None:
    cfg = Path(isolated_obcli_env["XDG_CONFIG_HOME"]) / "obcli"
    pol = {
        "block_rules": [],
        "limits": {"max_result_rows": 2},
    }
    (cfg / "policy.json").write_text(json.dumps(pol), encoding="utf-8")
    runner = CliRunner()
    env = {**isolated_obcli_env, "OBCLI_AUDIT_DISABLED": "1"}
    assert runner.invoke(
        cli,
        ["--format", "json", "sql", "CREATE TABLE IF NOT EXISTS rtrunc (x INTEGER)"],
        env=env,
    ).exit_code == 0
    assert runner.invoke(
        cli,
        ["--format", "json", "sql", "INSERT INTO rtrunc (x) VALUES (1),(2),(3)"],
        env=env,
    ).exit_code == 0
    r = runner.invoke(
        cli,
        ["--format", "json", "sql", "SELECT x FROM rtrunc ORDER BY x"],
        env=env,
    )
    assert r.exit_code == 0, r.output
    data = _json_line(r.output)
    assert len(data.get("rows") or []) == 2
    assert data.get("truncated") is True
    assert data.get("max_result_rows") == 2


def test_set_dsn_from_stdin(isolated_obcli_env: dict[str, str], tmp_path: Path) -> None:
    """Overwrite encrypted DSN via stdin; verify with a follow-up invoke (same isolated env)."""
    runner = CliRunner()
    new_db = tmp_path / "via_stdin.db"
    dsn = f"embedded:{new_db}"
    r = runner.invoke(
        cli,
        ["--format", "json", "config", "set-dsn"],
        input=dsn,
        env=isolated_obcli_env,
    )
    assert r.exit_code == 0, r.output
    r2 = runner.invoke(
        cli,
        ["--format", "json", "sql", "SELECT 2 AS n"],
        env=isolated_obcli_env,
    )
    assert r2.exit_code == 0, r2.output
    row = (_json_line(r2.output).get("rows") or [{}])[0]
    assert row.get("n") == 2 or row.get("2") == 2
