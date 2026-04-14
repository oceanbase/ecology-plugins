"""Parse DSN strings: oceanbase:// / mysql:// (MySQL protocol) and embedded: (local SQLite for tests/demos)."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlparse


_EMBEDDED_RE = re.compile(
    r"^embedded:(?P<path>[^?]+?)(?:\?database=(?P<database>[^&]+))?$",
    re.I,
)


@dataclass(frozen=True)
class EmbeddedConfig:
    """Local SQLite file URI (CI / demos only; not OceanBase)."""

    path: str
    database: str | None  # logical name for policy checks only


@dataclass(frozen=True)
class MySQLUrlConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None


def is_embedded_dsn(dsn: str) -> bool:
    return bool(dsn and dsn.lower().startswith("embedded:"))


def parse_embedded_dsn(dsn: str) -> EmbeddedConfig:
    m = _EMBEDDED_RE.match(dsn.strip())
    if not m:
        raise ValueError(
            "Invalid embedded DSN. Expected: embedded:<path>[?database=<name>]",
        )
    path = m.group("path").strip()
    db = m.group("database")
    return EmbeddedConfig(path=path, database=unquote(db) if db else None)


def is_mysql_protocol_dsn(dsn: str) -> bool:
    if not dsn:
        return False
    p = dsn.split("://", 1)[0].lower()
    return p in ("oceanbase", "mysql", "mariadb")


# Match trailing @host:port or @host:port/db (IPv4, hostname, localhost).
_OB_HOST_TAIL = re.compile(
    r"@((?:\d{1,3}\.){3}\d{1,3}|localhost|[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?):(\d+)(/[^?#]*)?$"
)


def _should_try_oceanbase_loose(dsn: str) -> bool:
    """Unencoded two-part (user@tenant:pass@host) or three-part (user@tenant#cluster:...) breaks urlparse."""
    if not dsn.lower().startswith("oceanbase://"):
        return False
    rest = dsn[len("oceanbase://") :]
    if "#" in rest:
        return True
    return rest.count("@") >= 2


def _oceanbase_loose_credentials_url(dsn: str) -> str | None:
    """Split on last @host:port[/db]; credentials use first : for user / password; URL-encode both."""
    s = dsn.strip()
    if not s.lower().startswith("oceanbase://"):
        return None
    rest = s[len("oceanbase://") :]
    m = _OB_HOST_TAIL.search(rest)
    if not m:
        return None
    cred = rest[: m.start()]
    if not cred or ":" not in cred:
        return None
    user, password = cred.split(":", 1)
    if not user:
        return None
    host, port, path = m.group(1), m.group(2), m.group(3) or ""
    return (
        f"oceanbase://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:{port}{path}"
    )


def parse_mysql_url(dsn: str) -> MySQLUrlConfig:
    if not is_mysql_protocol_dsn(dsn):
        raise ValueError("DSN must use oceanbase://, mysql://, or mariadb://")
    dsn = dsn.strip()
    if _should_try_oceanbase_loose(dsn):
        rebuilt = _oceanbase_loose_credentials_url(dsn)
        if rebuilt:
            dsn = rebuilt
    u = urlparse(dsn)
    if u.scheme.lower() not in ("oceanbase", "mysql", "mariadb"):
        raise ValueError("Unsupported scheme")
    host = u.hostname or "127.0.0.1"
    port = u.port or 3306
    user = unquote(u.username or "")
    password = unquote(u.password or "") if u.password else ""
    db = (u.path or "").lstrip("/") or None
    if db:
        db = unquote(db.split("?")[0])
    return MySQLUrlConfig(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=db,
    )


def database_from_dsn(dsn: str | None) -> str | None:
    if not dsn:
        return None
    if is_embedded_dsn(dsn):
        cfg = parse_embedded_dsn(dsn)
        return cfg.database
    try:
        return parse_mysql_url(dsn).database
    except ValueError:
        return None
