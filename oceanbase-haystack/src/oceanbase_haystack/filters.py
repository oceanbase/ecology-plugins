# SPDX-FileCopyrightText: 2023-present deepset GmbH <info@deepset.ai>
# SPDX-License-Identifier: Apache-2.0
"""Translate Haystack filter dicts into SQL predicates for a JSON ``meta`` column (same shape as milvus-haystack)."""

import json
from typing import Any, Dict, Union

from haystack.errors import FilterError

LOGIC_OPERATORS = ["AND", "OR", "NOT"]

COMPARISON_OPERATORS = ["==", "!=", ">", ">=", "<", "<=", "in", "not in"]


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _json_path_from_field(field: str) -> str:
    if field.startswith("meta."):
        field = field[5:]
    return "$." + field if field else "$"


def _json_extract_sql(meta_column: str, field: str) -> str:
    path = _json_path_from_field(field)
    return f"JSON_EXTRACT(`{meta_column}`, '{path}')"


def _value_to_json_cast(value: Union[int, float, str, bool, None]) -> str:
    """Render a Python value as ``CAST(... AS JSON)`` for comparison with ``JSON_EXTRACT``."""
    dumped = json.dumps(value)
    return f"CAST('{_escape_sql_string(dumped)}' AS JSON)"


def _value_to_sql(value: Union[int, float, str, list, bool, None]) -> str:
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.append(_value_to_json_cast(item))
        return "(" + ", ".join(parts) + ")"
    return _value_to_json_cast(value)


def parse_filters_to_sql(meta_column: str, filters: Dict[str, Any]) -> str:
    """
    Turn a Haystack filter dict into a SQL expression for use in a ``WHERE`` clause (without the ``WHERE`` keyword).

    Metadata lives in a JSON column (typically ``meta``); field names like ``meta.xxx`` map to
    ``JSON_EXTRACT(meta, '$.xxx')``.
    """
    if not isinstance(filters, dict):
        msg = "Filters must be a dictionary"
        raise FilterError(msg)
    if "field" in filters:
        return _parse_comparison(meta_column, filters)
    return _parse_logic(meta_column, filters)


def _parse_comparison(meta_column: str, filters: Dict[str, Any]) -> str:
    try:
        _assert_comparison_filter(filters)
    except AssertionError as assert_e:
        raise FilterError(str(assert_e)) from assert_e
    operator = filters["operator"]
    field = filters["field"]
    value = filters["value"]
    lhs = _json_extract_sql(meta_column, field)
    if operator in ("==", "!=", ">", ">=", "<", "<="):
        op_sql = "=" if operator == "==" else operator
        rhs = _value_to_json_cast(value)
        return f"({lhs} {op_sql} {rhs})"
    if operator == "in":
        if not isinstance(value, list):
            msg = "Value for 'in' operator must be a list"
            raise FilterError(msg)
        return f"({lhs} IN ({', '.join(_value_to_sql(v) for v in value)}))"
    if operator == "not in":
        if not isinstance(value, list):
            msg = "Value for 'not in' operator must be a list"
            raise FilterError(msg)
        return f"({lhs} NOT IN ({', '.join(_value_to_sql(v) for v in value)}))"
    msg = f"Unsupported operator: {operator}"
    raise FilterError(msg)


def _assert_comparison_filter(filters: Dict[str, Any]) -> None:
    assert "operator" in filters, "operator must be specified in filters"  # noqa: S101
    assert "field" in filters, "field must be specified in filters"  # noqa: S101
    assert "value" in filters, "value must be specified in filters"  # noqa: S101
    assert filters["operator"] in COMPARISON_OPERATORS, f"operator must be one of: {COMPARISON_OPERATORS}"  # noqa: S101


def _parse_logic(meta_column: str, filters: Dict[str, Any]) -> str:
    try:
        _assert_logic_filter(filters)
    except AssertionError as assert_e:
        raise FilterError(str(assert_e)) from assert_e
    if filters["operator"] == "NOT":
        clause_filter = {"operator": "AND", "conditions": filters["conditions"]}
        clause = parse_filters_to_sql(meta_column, clause_filter)
        return f"(NOT ({clause}))"
    operator = f" {filters['operator']} "
    parts = [parse_filters_to_sql(meta_column, condition) for condition in filters["conditions"]]
    return "(" + operator.join(parts) + ")"


def _assert_logic_filter(filters: Dict[str, Any]) -> None:
    assert "operator" in filters, "operator must be specified in filters"  # noqa: S101
    assert "conditions" in filters, "conditions must be specified in filters"  # noqa: S101
    assert filters["operator"] in LOGIC_OPERATORS, f"operator must be one of: {LOGIC_OPERATORS}"  # noqa: S101
    assert isinstance(filters["conditions"], list), "conditions must be a list"  # noqa: S101
