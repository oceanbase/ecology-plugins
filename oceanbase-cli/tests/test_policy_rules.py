"""Unit tests for policy.json evaluation (no real database)."""

from __future__ import annotations

from unittest.mock import patch

from oceanbase_cli.policy import evaluate_local_block_rules, get_policy_row_limit


def test_block_rules_match_grant() -> None:
    pol = {
        "block_rules": [
            {
                "id": "DENY-GRANT",
                "match": {"sql_pattern": r"(?i)^\s*GRANT\b"},
                "action": "deny",
                "message": "no grant",
            }
        ],
    }
    hit = evaluate_local_block_rules("GRANT SELECT ON t TO u", pol)
    assert hit is not None
    assert hit[0] == "DENY-GRANT"


def test_block_rules_no_match() -> None:
    pol = {
        "block_rules": [
            {
                "id": "DENY-GRANT",
                "match": {"sql_pattern": r"(?i)^\s*GRANT\b"},
                "action": "deny",
                "message": "no grant",
            }
        ],
    }
    assert evaluate_local_block_rules("SELECT 1", pol) is None


def test_non_deny_action_skipped() -> None:
    pol = {
        "block_rules": [
            {
                "id": "X",
                "match": {"sql_pattern": ".*"},
                "action": "allow",
                "message": "ignored",
            }
        ],
    }
    assert evaluate_local_block_rules("DROP TABLE x", pol) is None


def test_get_policy_row_limit_top_level() -> None:
    pol = {"limits": {"max_result_rows": 5}}
    with patch("oceanbase_cli.policy.load_local_policy", return_value=pol):
        assert get_policy_row_limit() == 5
