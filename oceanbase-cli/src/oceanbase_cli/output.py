"""Unified JSON / table / CSV / JSONL output for obcli."""

from __future__ import annotations

import csv
import io
import json
import sys
import time
from typing import Any

EXIT_OK = 0
EXIT_BIZ_ERROR = 1
EXIT_USAGE_ERROR = 2


class Timer:
    def __init__(self) -> None:
        self.start: float = 0
        self.elapsed_ms: int = 0

    def __enter__(self) -> Timer:
        self.start = time.monotonic()
        return self

    def __exit__(self, *_: Any) -> None:
        self.elapsed_ms = int((time.monotonic() - self.start) * 1000)


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def success(data: Any, *, time_ms: int = 0, fmt: str = "json") -> None:
    payload: dict[str, Any] = {"ok": True, "data": data}
    if time_ms:
        payload["time_ms"] = time_ms
    _emit(payload, fmt=fmt)
    sys.exit(EXIT_OK)


def success_rows(
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    affected: int = 0,
    time_ms: int = 0,
    fmt: str = "json",
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "ok": True,
        "columns": columns,
        "rows": rows,
        "affected": affected,
        "time_ms": time_ms,
    }
    if extra:
        payload.update(extra)
    _emit(payload, fmt=fmt, columns=columns, rows=rows)
    sys.exit(EXIT_OK)


def error(
    code: str,
    message: str,
    *,
    fmt: str = "json",
    exit_code: int = EXIT_BIZ_ERROR,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "ok": False,
        "error": {"code": code, "message": message},
    }
    if extra:
        payload.update(extra)
    _emit(payload, fmt=fmt)
    sys.exit(exit_code)


def _emit(
    payload: dict[str, Any],
    *,
    fmt: str = "json",
    columns: list[str] | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> None:
    if fmt == "json":
        print(_json_dumps(payload))
    elif fmt == "table":
        _print_table(payload, columns, rows)
    elif fmt == "csv":
        _print_csv(payload, columns, rows)
    elif fmt == "jsonl":
        _print_jsonl(payload, rows)
    else:
        print(_json_dumps(payload))


def _print_table(
    payload: dict[str, Any],
    columns: list[str] | None,
    rows: list[dict[str, Any]] | None,
) -> None:
    if not columns or not rows:
        _print_table_from_data(payload)
        return
    col_widths = {c: len(c) for c in columns}
    str_rows: list[dict[str, str]] = []
    for row in rows:
        sr: dict[str, str] = {}
        for c in columns:
            val = str(row.get(c, ""))
            sr[c] = val
            col_widths[c] = max(col_widths[c], len(val))
        str_rows.append(sr)
    header = " | ".join(c.ljust(col_widths[c]) for c in columns)
    sep = "-+-".join("-" * col_widths[c] for c in columns)
    print(header)
    print(sep)
    for sr in str_rows:
        print(" | ".join(sr[c].ljust(col_widths[c]) for c in columns))


def _print_table_from_data(payload: dict[str, Any]) -> None:
    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        cols = list(data[0].keys())
        _print_table(payload, cols, data)
        return
    print(_json_dumps(payload))


def _print_csv(
    payload: dict[str, Any],
    columns: list[str] | None,
    rows: list[dict[str, Any]] | None,
) -> None:
    if columns and rows:
        _write_csv(columns, rows)
        return
    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        cols = list(data[0].keys())
        _write_csv(cols, data)
        return
    print(_json_dumps(payload))


def _write_csv(columns: list[str], rows: list[dict[str, Any]]) -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        flat: dict[str, str] = {}
        for c in columns:
            val = row.get(c)
            flat[c] = (
                json.dumps(val, ensure_ascii=False, default=str)
                if isinstance(val, (dict, list))
                else str(val)
                if val is not None
                else ""
            )
        writer.writerow(flat)
    sys.stdout.write(buf.getvalue())


def _print_jsonl(payload: dict[str, Any], rows: list[dict[str, Any]] | None) -> None:
    if rows:
        for row in rows:
            print(_json_dumps(row))
        return
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            print(_json_dumps(item))
        return
    print(_json_dumps(payload))
