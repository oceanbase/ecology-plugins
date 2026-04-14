"""Optional pymysql connection pool (thread-safe).

The main ``obcli`` commands (``sql``, ``status``, …) open one connection per
invocation via ``executor``; they do **not** use this module. Kept for reuse in
long-running tools or tests.
"""

import threading
import logging
from typing import Any, Optional
from dataclasses import dataclass
import time

import pymysql


logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Connection pool settings (host, credentials, sizing, timeouts)."""
    host: str
    port: int
    user: str
    password: str
    database: str

    # Pool sizing and timeouts
    max_connections: int = 20  # Upper bound on pooled connections
    min_connections: int = 5  # Pre-created connections at init
    max_lifetime: int = 3600  # Max connection age in seconds (reserved for future use)
    idle_timeout: int = 300  # Idle timeout in seconds (reserved for future use)
    acquire_timeout: int = 30  # Max wait when acquiring a connection

    # Client session
    charset: str = "utf8mb4"
    autocommit: bool = True

    # pymysql connect_timeout
    connect_timeout: int = 10


class Connection:
    """Wrapper that returns the underlying connection to the pool on ``close()``."""

    def __init__(self, real_conn, pool):
        self._conn = real_conn
        self._pool = pool
        self._closed = False

    def cursor(self, cursorclass=None):
        return self._conn.cursor(cursorclass)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if not self._closed:
            self._closed = True
            # Return to pool instead of closing the real connection
            self._pool._return_connection(self._conn)

    def ping(self, reconnect=False):
        return self._conn.ping(reconnect)

    @property
    def open(self):
        return not self._closed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SimpleConnectionPool:
    """Minimal thread-safe pool over pymysql connections."""

    def __init__(self, config: PoolConfig):
        self.config = config
        self._connections = []
        self._active_connections = set()
        self._lock = threading.Lock()
        self._stats = {
            "created": 0,
            "acquired": 0,
            "released": 0,
            "failed": 0,
        }
        self._initialized = False
        self._stop = threading.Event()

    def initialize(self):
        """Pre-create ``min_connections`` and mark the pool ready."""
        if self._initialized:
            return True

        try:
            for i in range(self.config.min_connections):
                conn = self._create_connection()
                if conn:
                    self._connections.append(conn)

            self._initialized = True
            logger.info("Connection pool initialized: %s connections", len(self._connections))
            logger.info("Pool size range: %s .. %s", self.config.min_connections, self.config.max_connections)
            return True

        except Exception as e:
            logger.error("Connection pool init failed: %s", e)
            return False

    def _create_connection(self) -> Optional[Any]:
        """Open one pymysql connection and track stats."""
        try:
            conn = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                autocommit=self.config.autocommit,
                connect_timeout=self.config.connect_timeout,
                cursorclass=pymysql.cursors.DictCursor,
            )
            self._stats["created"] += 1
            logger.debug("Created connection id=%s", id(conn))
            return conn
        except Exception as e:
            logger.error("Create connection failed: %s", e)
            self._stats["failed"] += 1
            return None

    def get_connection(self, timeout: int = None) -> Optional[Connection]:
        """Borrow a connection, wrapped for pool-safe ``close()``."""
        timeout = timeout or self.config.acquire_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self._lock:
                # Prefer an idle connection from the pool
                for i, conn in enumerate(self._connections):
                    if conn not in self._active_connections:
                        try:
                            conn.ping(reconnect=False)
                            self._active_connections.add(conn)
                            self._stats["acquired"] += 1
                            return Connection(conn, self)
                        except Exception:
                            # Stale connection: drop and retry outer loop
                            logger.debug("Removing dead connection id=%s", id(conn))
                            try:
                                conn.close()
                            except Exception:
                                pass
                            self._connections.pop(i)
                            break

                if len(self._connections) < self.config.max_connections:
                    conn = self._create_connection()
                    if conn:
                        self._active_connections.add(conn)
                        self._stats["acquired"] += 1
                        return Connection(conn, self)

            time.sleep(0.1)

        logger.error("Acquire connection timed out")
        return None

    def _return_connection(self, conn: Any):
        """Mark a connection idle again (internal)."""
        with self._lock:
            self._active_connections.discard(conn)
            self._stats["released"] += 1
            logger.debug("Returned connection id=%s", id(conn))

    def health_check(self) -> dict:
        """Return pool size and counters for observability."""
        with self._lock:
            return {
                "status": "healthy" if self._initialized else "not_initialized",
                "total": len(self._connections),
                "active": len(self._active_connections),
                "idle": len(self._connections) - len(self._active_connections),
                "max_connections": self.config.max_connections,
                "min_connections": self.config.min_connections,
                "stats": self._stats.copy(),
            }

    def close_all(self):
        """Close every real connection and reset state."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception:
                    pass
            self._connections.clear()
            self._active_connections.clear()
            self._initialized = False
            logger.info("Connection pool closed")


_pool_instance: Optional[SimpleConnectionPool] = None


def get_pool() -> Optional[SimpleConnectionPool]:
    """Return the process-wide pool instance, if any."""
    return _pool_instance


def init_pool(config: PoolConfig) -> bool:
    """Create and initialize the global pool."""
    global _pool_instance
    _pool_instance = SimpleConnectionPool(config)
    return _pool_instance.initialize()


def get_connection() -> Optional[Connection]:
    """Convenience: borrow from the global pool."""
    global _pool_instance
    if _pool_instance is None:
        logger.warning("Pool not initialized; cannot get connection")
        return None
    return _pool_instance.get_connection()


def get_pool_stats() -> dict:
    """Convenience: ``health_check()`` on the global pool."""
    global _pool_instance
    if _pool_instance is None:
        return {"status": "not_initialized"}
    return _pool_instance.health_check()


def shutdown_pool() -> None:
    """Close all connections and drop the global pool (for tests or clean exit)."""
    global _pool_instance
    if _pool_instance is not None:
        _pool_instance.close_all()
    _pool_instance = None
