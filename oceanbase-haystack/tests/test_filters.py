"""Unit tests for ``parse_filters_to_sql`` (Haystack filter dict → SQL)."""

import pytest
from haystack.errors import FilterError

from oceanbase_haystack.filters import parse_filters_to_sql


def test_comparison_eq():
    sql = parse_filters_to_sql(
        "meta",
        {"field": "meta.type", "operator": "==", "value": "article"},
    )
    assert "`meta`" in sql
    assert "JSON_EXTRACT" in sql
    assert "$.type" in sql
    assert "CAST(" in sql and "article" in sql


def test_comparison_neq():
    sql = parse_filters_to_sql("meta", {"field": "meta.n", "operator": "!=", "value": 1})
    assert "!=" in sql or "<>" in sql or ("NOT" in sql)


def test_comparison_numeric():
    sql = parse_filters_to_sql("meta", {"field": "meta.score", "operator": ">=", "value": 0.5})
    assert ">=" in sql


def test_field_without_meta_prefix():
    sql = parse_filters_to_sql("meta", {"field": "category", "operator": "==", "value": "x"})
    assert "$.category" in sql


def test_in_operator():
    sql = parse_filters_to_sql(
        "meta",
        {"field": "meta.id", "operator": "in", "value": [1, 2, 3]},
    )
    assert " IN (" in sql


def test_not_in_operator():
    sql = parse_filters_to_sql(
        "meta",
        {"field": "meta.id", "operator": "not in", "value": ["a", "b"]},
    )
    assert " NOT IN (" in sql


def test_in_operator_requires_list():
    with pytest.raises(FilterError, match="list"):
        parse_filters_to_sql("meta", {"field": "meta.x", "operator": "in", "value": "not-a-list"})


def test_logic_and():
    sql = parse_filters_to_sql(
        "meta",
        {
            "operator": "AND",
            "conditions": [
                {"field": "meta.a", "operator": "==", "value": 1},
                {"field": "meta.b", "operator": "==", "value": 2},
            ],
        },
    )
    assert " AND " in sql


def test_logic_or():
    sql = parse_filters_to_sql(
        "meta",
        {
            "operator": "OR",
            "conditions": [
                {"field": "meta.a", "operator": "==", "value": 1},
                {"field": "meta.b", "operator": "==", "value": 2},
            ],
        },
    )
    assert " OR " in sql


def test_logic_not():
    sql = parse_filters_to_sql(
        "meta",
        {
            "operator": "NOT",
            "conditions": [
                {"field": "meta.hidden", "operator": "==", "value": True},
            ],
        },
    )
    assert sql.strip().startswith("(NOT (")


def test_filters_must_be_dict():
    with pytest.raises(FilterError, match="dictionary"):
        parse_filters_to_sql("meta", [])  # type: ignore[arg-type]


def test_unsupported_comparison_operator():
    with pytest.raises(FilterError, match="operator must be one of"):
        parse_filters_to_sql("meta", {"field": "meta.x", "operator": "~~", "value": "x"})


def test_string_escape_single_quote():
    sql = parse_filters_to_sql(
        "meta",
        {"field": "meta.title", "operator": "==", "value": "O'Brien"},
    )
    assert "''" in sql
