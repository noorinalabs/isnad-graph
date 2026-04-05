"""Acquire the Open Hadith Data corpus from GitHub.

Shallow-clones mhashim6/Open-Hadith-Data which contains 9+ CSV files
of hadith texts with full Arabic diacritics (tashkeel).
"""

from __future__ import annotations

from pathlib import Path

from src.acquire.base import clone_repo, ensure_dir, write_manifest
from src.utils.logging import get_logger

logger = get_logger(__name__)

REPO_URL = "https://github.com/mhashim6/Open-Hadith-Data.git"
MIN_EXPECTED_CSVS = 9


def run(raw_dir: Path) -> Path:
    """Clone Open Hadith Data and validate CSV files exist.

    Idempotent -- skips if destination already populated.
    """
    dest = ensure_dir(raw_dir / "open_hadith")
    clone_repo(REPO_URL, dest)

    csv_files = list(dest.rglob("*.csv"))
    if len(csv_files) < MIN_EXPECTED_CSVS:
        msg = f"Expected >={MIN_EXPECTED_CSVS} CSVs, found {len(csv_files)}"
        raise AssertionError(msg)

    logger.info("open_hadith_acquired", file_count=len(csv_files))
    write_manifest(dest, csv_files)
    return dest
