"""Optional ``pool.json`` dataclass for connection-pool defaults.

Not used by core ``obcli`` commands (``sql`` / ``status`` use ``executor`` per
invoke). Intended for experiments or tools that call ``connection_pool`` directly.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class PoolConfig:
    """Serializable pool-related defaults (separate from ``PoolConfig`` in ``connection_pool``)."""

    # Target database
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    database: str = "oceanbase"

    # Pool sizing / timeouts (mirrors high-level knobs only)
    max_connections: int = 20
    min_connections: int = 5
    max_lifetime: int = 3600  # seconds (informational; pool may not enforce yet)
    idle_timeout: int = 300  # seconds
    acquire_timeout: int = 30  # seconds

    # Health / cache toggles (informational for downstream tools)
    enable_health_check: bool = True
    health_check_interval: int = 300  # seconds
    enable_query_cache: bool = False

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "PoolConfig":
        """Load from ``pool.json`` or return defaults."""
        if config_path:
            path = Path(config_path)
        else:
            home_dir = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            path = Path(home_dir) / "obcli" / "pool.json"

        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Warning: failed to load pool config, using defaults: {e}")

        return cls()

    def save(self, config_path: Optional[str] = None):
        """Write dataclass fields as JSON to ``pool.json``."""
        if config_path:
            path = Path(config_path)
        else:
            home_dir = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            path = Path(home_dir) / "obcli" / "pool.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

        print(f"Pool config saved to {path}")
