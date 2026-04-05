"""Audit trail for pipeline operations (sync, load, enrich).

Writes structured JSON audit records to ``data/audit/`` after each
pipeline stage, enabling change tracking and operational visibility.
"""

from __future__ import annotations

import getpass
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = ["AuditEntry", "list_recent_entries", "write_audit_entry"]

AUDIT_DIR_NAME = "audit"


@dataclass(frozen=True)
class AuditEntry:
    """A single audit record for a pipeline stage execution."""

    stage: str
    timestamp: str
    duration_seconds: float
    operator: str
    files_changed: list[dict[str, Any]] = field(default_factory=list)
    rows_affected: int = 0
    summary: dict[str, Any] = field(default_factory=dict)


def write_audit_entry(data_dir: Path, entry: AuditEntry) -> Path:
    """Write an audit entry to ``data/audit/{timestamp}-{stage}.json``.

    Returns the path of the written file.
    """
    audit_dir = data_dir / AUDIT_DIR_NAME
    audit_dir.mkdir(parents=True, exist_ok=True)

    safe_ts = entry.timestamp.replace(":", "-").replace("+", "p")
    filename = f"{safe_ts}-{entry.stage}.json"
    path = audit_dir / filename

    path.write_text(json.dumps(asdict(entry), indent=2) + "\n")
    return path


def create_audit_entry(
    stage: str,
    *,
    duration_seconds: float,
    files_changed: list[dict[str, Any]] | None = None,
    rows_affected: int = 0,
    summary: dict[str, Any] | None = None,
) -> AuditEntry:
    """Build an AuditEntry with auto-populated timestamp and operator."""
    return AuditEntry(
        stage=stage,
        timestamp=datetime.now(tz=UTC).isoformat(),
        duration_seconds=duration_seconds,
        operator=getpass.getuser(),
        files_changed=files_changed or [],
        rows_affected=rows_affected,
        summary=summary or {},
    )


def list_recent_entries(data_dir: Path, last_n: int = 10) -> list[AuditEntry]:
    """Return the *last_n* most recent audit entries, newest first."""
    audit_dir = data_dir / AUDIT_DIR_NAME
    if not audit_dir.exists():
        return []

    files = sorted(audit_dir.glob("*.json"), reverse=True)
    entries: list[AuditEntry] = []
    for fp in files[:last_n]:
        data = json.loads(fp.read_text())
        entries.append(AuditEntry(**data))
    return entries
