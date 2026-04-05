#!/usr/bin/env python3
"""Pipeline smoke test: acquire, parse, and validate 3 healthy data sources.

Sources tested (no API keys required):
  - open_hadith  (GitHub clone, CSV)
  - lk_corpus    (GitHub clone, CSV)
  - muhaddithat  (GitHub clone, CSV)

Usage:
    uv run python scripts/pipeline_smoke.py
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Schemas for validation
# ---------------------------------------------------------------------------
from src.parse.schemas import (
    COLLECTION_SCHEMA,
    HADITH_SCHEMA,
    NARRATOR_BIO_SCHEMA,
    NARRATOR_MENTION_SCHEMA,
    NETWORK_EDGE_SCHEMA,
)

EXPECTED_SCHEMAS: dict[str, Any] = {
    "hadiths_": HADITH_SCHEMA,
    "narrator_mentions_": NARRATOR_MENTION_SCHEMA,
    "narrators_bio_": NARRATOR_BIO_SCHEMA,
    "collections_": COLLECTION_SCHEMA,
    "network_edges_": NETWORK_EDGE_SCHEMA,
}

SOURCES = ["open_hadith", "lk", "muhaddithat"]

# Mapping from source name to acquire module attribute name
SOURCE_MODULE_MAP = {
    "open_hadith": "open_hadith",
    "lk": "lk_corpus",
    "muhaddithat": "muhaddithat",
}


@dataclass
class StageResult:
    """Result of a single pipeline stage for a single source."""

    source: str
    stage: str
    success: bool
    duration_s: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def _match_schema(filename: str) -> tuple[str, Any] | None:
    for prefix, schema in EXPECTED_SCHEMAS.items():
        if filename.startswith(prefix):
            return prefix, schema
    return None


def _check_schema(table_schema: Any, expected_schema: Any) -> list[str]:
    issues: list[str] = []
    expected_names = {f.name for f in expected_schema}
    actual_names = {f.name for f in table_schema}
    missing = expected_names - actual_names
    extra = actual_names - expected_names
    if missing:
        issues.append(f"Missing columns: {sorted(missing)}")
    if extra:
        issues.append(f"Extra columns: {sorted(extra)}")
    for fld in expected_schema:
        if fld.name in actual_names:
            actual_field = table_schema.field(fld.name)
            if actual_field.type != fld.type:
                issues.append(
                    f"Column '{fld.name}' type mismatch: "
                    f"expected {fld.type}, got {actual_field.type}"
                )
    return issues


# ---------------------------------------------------------------------------
# Acquire stage
# ---------------------------------------------------------------------------
def acquire_source(source: str, raw_dir: Path) -> StageResult:
    """Download a single source into raw_dir."""
    mod_name = SOURCE_MODULE_MAP[source]
    module = __import__(f"src.acquire.{mod_name}", fromlist=[mod_name])

    t0 = time.monotonic()
    try:
        dest = module.run(raw_dir)
        elapsed = time.monotonic() - t0
        file_count = len(list(dest.rglob("*"))) if dest and dest.exists() else 0
        return StageResult(
            source=source,
            stage="acquire",
            success=True,
            duration_s=round(elapsed, 2),
            details={"output_dir": str(dest), "file_count": file_count},
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        return StageResult(
            source=source,
            stage="acquire",
            success=False,
            duration_s=round(elapsed, 2),
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Parse stage
# ---------------------------------------------------------------------------
def parse_source(source: str, raw_dir: Path, staging_dir: Path) -> StageResult:
    """Parse a single source from raw_dir into staging_dir."""
    mod_name = SOURCE_MODULE_MAP[source]
    module = __import__(f"src.parse.{mod_name}", fromlist=[mod_name])

    t0 = time.monotonic()
    try:
        result = module.run(raw_dir, staging_dir)
        elapsed = time.monotonic() - t0

        # Normalize result to list of paths
        if isinstance(result, list | tuple):
            paths = list(result)
        elif isinstance(result, dict):
            paths = list(result.values())
        else:
            paths = [result]

        file_details: list[dict[str, Any]] = []
        for p in paths:
            if p and p.exists():
                meta = pq.read_metadata(p)
                file_details.append({"file": p.name, "rows": meta.num_rows})

        return StageResult(
            source=source,
            stage="parse",
            success=True,
            duration_s=round(elapsed, 2),
            details={"files": file_details, "file_count": len(paths)},
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        return StageResult(
            source=source,
            stage="parse",
            success=False,
            duration_s=round(elapsed, 2),
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Validate stage (schema conformance on produced Parquet files)
# ---------------------------------------------------------------------------
def validate_source(source: str, staging_dir: Path) -> StageResult:
    """Validate Parquet outputs for a source against expected PyArrow schemas."""
    t0 = time.monotonic()
    try:
        # Find parquet files belonging to this source
        suffix = source
        parquet_files = [f for f in sorted(staging_dir.glob("*.parquet")) if suffix in f.name]
        if not parquet_files:
            elapsed = time.monotonic() - t0
            return StageResult(
                source=source,
                stage="validate",
                success=False,
                duration_s=round(elapsed, 2),
                error="No Parquet files found for source",
            )

        all_issues: dict[str, list[str]] = {}
        file_summaries: list[dict[str, Any]] = []

        for pf in parquet_files:
            table = pq.read_table(pf)
            match = _match_schema(pf.name)
            issues: list[str] = []
            if match:
                _, expected = match
                issues = _check_schema(table.schema, expected)
            else:
                issues = ["No matching expected schema"]

            all_issues[pf.name] = issues
            file_summaries.append(
                {
                    "file": pf.name,
                    "rows": table.num_rows,
                    "columns": len(table.column_names),
                    "schema_ok": len(issues) == 0,
                    "issues": issues,
                }
            )

        all_ok = all(len(v) == 0 for v in all_issues.values())
        elapsed = time.monotonic() - t0
        return StageResult(
            source=source,
            stage="validate",
            success=all_ok,
            duration_s=round(elapsed, 2),
            details={"files": file_summaries},
            error=None if all_ok else "Schema validation issues found",
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        return StageResult(
            source=source,
            stage="validate",
            success=False,
            duration_s=round(elapsed, 2),
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    staging_dir = project_root / "data" / "staging"

    # Create dirs
    raw_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    results: list[StageResult] = []
    overall_start = time.monotonic()

    print("=" * 70)
    print("PIPELINE SMOKE TEST")
    print(f"Sources: {', '.join(SOURCES)}")
    print(f"Raw dir: {raw_dir}")
    print(f"Staging dir: {staging_dir}")
    print("=" * 70)

    for source in SOURCES:
        print(f"\n{'---' * 17}")
        print(f"Source: {source}")
        print(f"{'---' * 17}")

        # Acquire
        print(f"  [acquire] downloading {source}...")
        acq = acquire_source(source, raw_dir)
        results.append(acq)
        status = "OK" if acq.success else "FAIL"
        print(f"  [acquire] {status} ({acq.duration_s}s)")
        if not acq.success:
            print(f"  [acquire] Error: {acq.error}")
            continue

        # Parse
        print(f"  [parse]   parsing {source}...")
        par = parse_source(source, raw_dir, staging_dir)
        results.append(par)
        status = "OK" if par.success else "FAIL"
        print(f"  [parse]   {status} ({par.duration_s}s)")
        if par.success and par.details.get("files"):
            for fd in par.details["files"]:
                print(f"            {fd['file']}: {fd['rows']:,} rows")
        if not par.success:
            print(f"  [parse]   Error: {par.error}")
            continue

        # Validate
        print(f"  [validate] checking schemas for {source}...")
        val = validate_source(source, staging_dir)
        results.append(val)
        status = "OK" if val.success else "FAIL"
        print(f"  [validate] {status} ({val.duration_s}s)")
        if val.details.get("files"):
            for fs in val.details["files"]:
                schema_status = "OK" if fs["schema_ok"] else "ISSUES"
                print(
                    f"             {fs['file']}: {fs['rows']:,} rows, "
                    f"{fs['columns']} cols, schema={schema_status}"
                )
                for issue in fs.get("issues", []):
                    print(f"               - {issue}")

    # Summary
    overall_elapsed = round(time.monotonic() - overall_start, 2)
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total time: {overall_elapsed}s\n")

    # Group by source
    for source in SOURCES:
        source_results = [r for r in results if r.source == source]
        statuses = []
        for r in source_results:
            mark = "PASS" if r.success else "FAIL"
            statuses.append(f"{r.stage}={mark}")
        print(f"  {source:15s}  {', '.join(statuses)}")

    failures = [r for r in results if not r.success]
    print()
    if failures:
        print(f"RESULT: {len(failures)} failure(s)")
        return 1
    print("RESULT: All stages passed for all sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
