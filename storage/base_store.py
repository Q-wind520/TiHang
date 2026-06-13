"""Base class for JSON-backed stores with threading lock."""

import threading
from pathlib import Path
from .json_helpers import read_json, write_json, ensure_file


class BaseStore:
    """Base store with JSON read/write and a reentrant lock for thread safety."""

    def __init__(self, filepath: str | Path, default: dict | list | None = None):
        self._filepath = Path(filepath)
        self._lock = threading.RLock()
        ensure_file(self._filepath, default)

    @property
    def filepath(self) -> Path:
        return self._filepath

    def _read(self) -> dict | list:
        with self._lock:
            return read_json(self._filepath)

    def _write(self, data: dict | list) -> None:
        with self._lock:
            write_json(self._filepath, data)
