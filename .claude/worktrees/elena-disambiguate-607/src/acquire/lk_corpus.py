"""Acquire the LK Hadith Corpus from GitHub.

The LK corpus (Shatha Altammami) contains six Kutub al-Sittah collections
as CSV files: Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasai, Ibn Majah.
"""

from __future__ import annotations

from pathlib import Path

from src.acquire.base import clone_repo, ensure_dir, write_manifest
from src.utils.logging import get_logger

logger = get_logger(__name__)

LK_REPO_URL = "https://github.com/ShathaTm/LK-Hadith-Corpus.git"
MIN_EXPECTED_CSVS = 6


def run(raw_dir: Path) -> Path:
    """Clone the LK Hadith Corpus and validate CSV files exist."""
    dest = ensure_dir(raw_dir / "lk")
    clone_repo(LK_REPO_URL, dest)
    csv_files = list(dest.rglob("*.csv"))
    if len(csv_files) < MIN_EXPECTED_CSVS:
        msg = f"Expected >={MIN_EXPECTED_CSVS} CSVs, found {len(csv_files)}"
        raise AssertionError(msg)
    logger.info("lk_acquired", file_count=len(csv_files))
    write_manifest(dest, csv_files)
    return dest
