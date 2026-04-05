"""Acquire the Muhaddithat isnad datasets from GitHub.

Shallow-clones muhaddithat/isnad-datasets which contains hadith and
narrator CSV files from the muslimscholars.info project.
"""

from __future__ import annotations

from pathlib import Path

from src.acquire.base import clone_repo, ensure_dir, write_manifest
from src.utils.logging import get_logger

logger = get_logger(__name__)

REPO_URL = "https://github.com/muhaddithat/isnad-datasets.git"


def run(raw_dir: Path) -> Path:
    """Clone Muhaddithat isnad-datasets and validate hadiths.csv exists.

    Idempotent -- skips if destination already populated.
    """
    dest = ensure_dir(raw_dir / "muhaddithat")
    clone_repo(REPO_URL, dest)

    hadiths_csvs = list(dest.rglob("hadiths.csv"))
    if not hadiths_csvs:
        msg = "Expected hadiths.csv in repository, not found"
        raise AssertionError(msg)

    all_csvs = list(dest.rglob("*.csv"))
    logger.info("muhaddithat_acquired", file_count=len(all_csvs))
    write_manifest(dest, all_csvs)
    return dest
