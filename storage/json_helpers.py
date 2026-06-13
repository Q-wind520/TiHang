"""Atomic JSON file read/write utilities.

Uses tempfile + os.replace for atomic writes to prevent data corruption
if the process crashes mid-write.
"""

import json
import os
import tempfile
import threading
from pathlib import Path


class StorageError(Exception):
    """Raised when a storage operation fails."""


def read_json(filepath: str | Path) -> dict:
    """Read a JSON file and return its contents as a dict.

    Returns an empty dict if the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise StorageError(f"Invalid JSON in {path}: {e}") from e
    except OSError as e:
        raise StorageError(f"Cannot read {path}: {e}") from e


def write_json(filepath: str | Path, data: dict, indent: int = 2) -> None:
    """Atomically write data to a JSON file.

    Writes to a temp file then replaces the target file, so a crash
    mid-write never leaves a corrupted file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            os.replace(tmp_path, path)
        except Exception:
            # Clean up the temp file on error
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except (OSError, json.JSONDecodeError) as e:
        raise StorageError(f"Failed to write {path}: {e}") from e


def ensure_file(filepath: str | Path, default: list | dict | None = None) -> Path:
    """Ensure a JSON file exists; create with default if missing."""
    path = Path(filepath)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, default if default is not None else {})
    return path
