"""Content-addressable manifest for incremental pipeline operations.

Generates MD5-based manifests of Parquet files in staging/curated directories,
compares manifests to detect added/modified/removed files, and provides
load/save helpers for JSON persistence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

__all__ = [
    "ChangedFiles",
    "compare_manifests",
    "generate_manifest",
    "load_manifest",
    "save_manifest",
]

MANIFEST_FILENAME = ".manifest.json"
LAST_LOADED_MANIFEST_FILENAME = ".last_loaded_manifest.json"


def md5_file(path: Path, chunk_size: int = 8192) -> str:
    """Compute MD5 hex digest of a file."""
    h = hashlib.md5()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest(data_dir: Path) -> dict[str, dict[str, Any]]:
    """Walk staging/ and curated/ under *data_dir*, returning a manifest dict.

    Keys are relative paths like ``staging/hadiths_bukhari.parquet``.
    Values contain ``md5``, ``rows``, ``size_bytes``, and ``last_modified``.
    """
    manifest: dict[str, dict[str, Any]] = {}
    for subdir in ("staging", "curated"):
        d = data_dir / subdir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.parquet")):
            key = f"{subdir}/{p.name}"
            rows = pq.read_metadata(p).num_rows
            manifest[key] = {
                "md5": md5_file(p),
                "rows": rows,
                "size_bytes": p.stat().st_size,
                "last_modified": datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat(),
            }
    return manifest


@dataclass(frozen=True)
class ChangedFiles:
    """Result of comparing two manifests."""

    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.removed)

    @property
    def changed_files(self) -> list[str]:
        """All files that were added or modified."""
        return self.added + self.modified


def compare_manifests(
    current: dict[str, dict[str, Any]],
    previous: dict[str, dict[str, Any]],
) -> ChangedFiles:
    """Compare *current* manifest against *previous*, returning change sets."""
    added: list[str] = []
    modified: list[str] = []
    unchanged: list[str] = []
    removed: list[str] = []

    current_keys = set(current)
    previous_keys = set(previous)

    for key in sorted(current_keys - previous_keys):
        added.append(key)

    for key in sorted(current_keys & previous_keys):
        if current[key]["md5"] != previous[key]["md5"]:
            modified.append(key)
        else:
            unchanged.append(key)

    for key in sorted(previous_keys - current_keys):
        removed.append(key)

    return ChangedFiles(added=added, modified=modified, unchanged=unchanged, removed=removed)


def save_manifest(manifest: dict[str, dict[str, Any]], path: Path) -> None:
    """Write manifest dict to *path* as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    """Load a manifest from *path*. Returns empty dict if file does not exist."""
    if not path.exists():
        return {}
    result: dict[str, dict[str, Any]] = json.loads(path.read_text())
    return result
