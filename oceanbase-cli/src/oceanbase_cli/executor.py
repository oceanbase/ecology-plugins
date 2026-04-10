"""Execute SQL via pymysql (MySQL / OceanBase protocol) or sqlite3 (embedded: local file)."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from oceanbase_cli.dsn import (
    is_embedded_dsn,
    is_mysql_protocol_dsn,
    parse_embedded_dsn,
    parse_mysql_url,
)


def _jsonable_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = str(v)
        elif isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        elif isinstance(v, (bytes, bytearray)):
            out[k] = v.decode("utf-8", errors="replace")
        else:
            out[k] = v
    return out


def execute_sql(dsn: str, sql: str) -> tuple[list[str], list[dict[str, Any]], int]:
    """Run a single statement; return (columns, rows, rowcount)."""
    sql = sql.strip()
    if not sql:
        return [], [], 0
    if is_embedded_dsn(dsn):
        return _execute_sqlite(dsn, sql)
    if is_mysql_protocol_dsn(dsn):
        return _execute_pymysql(dsn, sql)
    raise ValueError(
        "Unsupported DSN. Use oceanbase:// or mysql:// for remote, or embedded: for local SQLite.",
    )


def _execute_sqlite(dsn: str, sql: str) -> tuple[list[str], list[dict[str, Any]], int]:
    cfg = parse_embedded_dsn(dsn)
    path = Path(cfg.path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        if cur.description:
            columns = [d[0] for d in cur.description]
            rows = [_jsonable_row(dict(r)) for r in cur.fetchall()]
            return columns, rows, cur.rowcount
        conn.commit()
        return [], [], cur.rowcount
    finally:
        conn.close()


def _execute_pymysql(dsn: str, sql: str) -> tuple[list[str], list[dict[str, Any]], int]:
    cfg = parse_mysql_url(dsn)
    conn = pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database or None,
        charset="utf8mb4",
        cursorclass=DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                columns = [d[0] for d in cur.description]
                raw = cur.fetchall()
                rows = [_jsonable_row(dict(r)) for r in raw]
                return columns, rows, cur.rowcount
            conn.commit()
            return [], [], cur.rowcount
    finally:
        conn.close()
