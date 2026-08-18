"""COGNIX memory system.

Live Memory is persistent and stays until explicitly removed.
Time Memory is persistent for a limited amount of time and is removed
automatically after expiration.
"""

import json
import time
from pathlib import Path
from typing import Any

MEMORY_FILE = Path(__file__).resolve().parent / "cognix_memory.json"

DEFAULT_MEMORY: dict[str, dict[str, Any]] = {
    "live": {},
    "time": {},
}


def _load() -> dict[str, dict[str, Any]]:
    data = DEFAULT_MEMORY.copy()

    if not MEMORY_FILE.exists():
        return data

    try:
        loaded = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data["live"] = loaded.get("live", {})
            data["time"] = loaded.get("time", {})
    except (OSError, json.JSONDecodeError):
        pass

    return data


def _save(data: dict[str, dict[str, Any]]) -> bool:
    try:
        MEMORY_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def _cleanup_expired(data: dict[str, dict[str, Any]]) -> None:
    now = time.time()
    expired = []

    for key, item in data["time"].items():
        if not isinstance(item, dict):
            expired.append(key)
            continue

        expires_at = item.get("expires_at")
        if isinstance(expires_at, (int, float)) and expires_at <= now:
            expired.append(key)

    for key in expired:
        data["time"].pop(key, None)


def set_live(key: str, value: Any) -> bool:
    """Store a value permanently until it is explicitly forgotten."""
    data = _load()
    data["live"][key.strip()] = value
    return _save(data)


def get_live(key: str, default: Any = None) -> Any:
    data = _load()
    return data["live"].get(key.strip(), default)


def forget_live(key: str) -> bool:
    data = _load()
    data["live"].pop(key.strip(), None)
    return _save(data)


def set_time(key: str, value: Any, seconds: int) -> bool:
    """Store a value until the requested number of seconds has elapsed."""
    seconds = max(1, int(seconds))
    data = _load()
    data["time"][key.strip()] = {
        "value": value,
        "created_at": time.time(),
        "expires_at": time.time() + seconds,
    }
    return _save(data)


def get_time(key: str, default: Any = None) -> Any:
    data = _load()
    _cleanup_expired(data)
    _save(data)

    item = data["time"].get(key.strip())
    if not isinstance(item, dict):
        return default

    return item.get("value", default)


def forget_time(key: str) -> bool:
    data = _load()
    data["time"].pop(key.strip(), None)
    return _save(data)


def get_all() -> dict[str, dict[str, Any]]:
    data = _load()
    _cleanup_expired(data)
    _save(data)
    return data


def clear_all() -> bool:
    return _save({"live": {}, "time": {}})
