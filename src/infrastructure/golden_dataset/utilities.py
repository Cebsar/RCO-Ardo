from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def compute_dataset_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def format_dataset_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def versioned_filename(name: str, version: str, extension: str = ".json") -> str:
    return f"{name}.v{version}{extension}"
