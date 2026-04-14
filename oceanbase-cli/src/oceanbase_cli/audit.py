from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

from oceanbase_cli.paths import default_audit_log_path


def emit(event: dict[str, Any]) -> None:
    if os.environ.get("OBCLI_AUDIT_DISABLED") == "1":
        return
    line = dict(event)
    line.setdefault("ts", datetime.now(UTC).isoformat().replace("+00:00", "Z"))
    path = default_audit_log_path()
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
