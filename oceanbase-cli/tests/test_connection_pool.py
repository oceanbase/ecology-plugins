"""Unit tests for optional connection_pool (mocked pymysql; no network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oceanbase_cli.connection_pool import (
    PoolConfig,
    get_connection,
    get_pool_stats,
    init_pool,
    shutdown_pool,
)


@pytest.fixture(autouse=True)
def _reset_pool() -> None:
    yield
    shutdown_pool()


def _mock_mysql_conn() -> MagicMock:
    c = MagicMock()
    c.ping = MagicMock()
    c.close = MagicMock()
    cur = MagicMock()
    cur.__enter__ = MagicMock(return_value=cur)
    cur.__exit__ = MagicMock(return_value=False)
    c.cursor = MagicMock(return_value=cur)
    return c


@patch("oceanbase_cli.connection_pool.pymysql.connect")
def test_init_pool_and_stats(mock_connect: MagicMock) -> None:
    mock_connect.side_effect = lambda **kw: _mock_mysql_conn()
    cfg = PoolConfig(
        host="127.0.0.1",
        port=3306,
        user="u",
        password="p",
        database="d",
        min_connections=2,
        max_connections=3,
    )
    assert init_pool(cfg) is True
    stats = get_pool_stats()
    assert stats["status"] == "healthy"
    assert stats["min_connections"] == 2
    assert stats["max_connections"] == 3
    assert mock_connect.call_count >= 2


@patch("oceanbase_cli.connection_pool.pymysql.connect")
def test_get_connection_acquire_release(mock_connect: MagicMock) -> None:
    mock_connect.side_effect = lambda **kw: _mock_mysql_conn()
    cfg = PoolConfig(
        host="127.0.0.1",
        port=3306,
        user="u",
        password="p",
        database="d",
        min_connections=1,
        max_connections=2,
    )
    assert init_pool(cfg) is True
    conn = get_connection()
    assert conn is not None
    conn.close()
    stats = get_pool_stats()
    assert stats["stats"]["released"] >= 1


def test_get_pool_stats_before_init() -> None:
    shutdown_pool()
    s = get_pool_stats()
    assert s.get("status") == "not_initialized"


def test_get_connection_before_init() -> None:
    shutdown_pool()
    assert get_connection() is None


@patch("oceanbase_cli.connection_pool.pymysql.connect")
def test_pool_config_defaults(mock_connect: MagicMock) -> None:
    mock_connect.side_effect = lambda **kw: _mock_mysql_conn()
    cfg = PoolConfig(
        host="h",
        port=3306,
        user="u",
        password="p",
        database="d",
    )
    assert cfg.charset == "utf8mb4"
    assert cfg.autocommit is True
    assert cfg.max_connections == 20
    assert cfg.min_connections == 5
