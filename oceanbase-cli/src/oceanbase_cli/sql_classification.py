"""Classify SQL statements for policy (write vs read)."""

from __future__ import annotations

import re

_WRITE_RE = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|REPLACE|ALTER|CREATE|DROP|TRUNCATE|RENAME)\b",
    re.I,
)
_SELECT_RE = re.compile(r"^\s*(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN)\b", re.I)


def is_write_sql(sql: str) -> bool:
    return bool(_WRITE_RE.match(sql))


def is_select_sql(sql: str) -> bool:
    return bool(_SELECT_RE.match(sql))
