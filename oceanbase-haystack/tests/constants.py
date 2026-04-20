"""Shared test constants (no DB)."""

CONNECTION_ARGS = {
    "host": "localhost",
    "port": "2881",
    "user": "root@test",
    "password": "",
    "db_name": "test",
}

DEFAULT_INDEX_PARAMS = {"metric_type": "L2", "index_type": "HNSW", "params": {}}
