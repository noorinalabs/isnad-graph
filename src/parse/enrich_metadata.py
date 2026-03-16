"""Enrich staging hadiths with book/chapter metadata from sunnah.com.

Matches Fawaz hadiths to sunnah.com scraped data by collection name + hadith
number, filling in book_number, chapter_number, chapter_name_ar, and
chapter_name_en where they are null.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from src.parse.base import write_parquet
from src.parse.schemas import HADITH_SCHEMA
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Mapping from Fawaz collection names to sunnah.com collection slugs.
# Fawaz uses short names like "bukhari"; sunnah.com uses the same or similar.
_COLLECTION_ALIASES: dict[str, str] = {
    "bukhari": "bukhari",
    "muslim": "muslim",
    "nasai": "nasai",
    "abudawud": "abudawud",
    "tirmidhi": "tirmidhi",
    "ibnmajah": "ibnmajah",
    "malik": "malik",
    "riyadussalihin": "riyadussalihin",
    "adab": "adab",
    "bulugh": "bulugh",
    "nawawi40": "nawawi40",
    "qudsi40": "qudsi40",
}


def _load_scraped_index(raw_dir: Path) -> dict[str, dict[str, Any]]:
    """Build a lookup index from sunnah.com scraped data.

    Returns a dict keyed by ``"collection:hadith_number"`` with values
    containing book_number, chapter_number, chapter_name_ar, chapter_name_en.
    """
    scraped_dir = raw_dir / "sunnah_scraped"
    if not scraped_dir.exists():
        logger.warning("sunnah_scraped_dir_missing", path=str(scraped_dir))
        return {}

    index: dict[str, dict[str, Any]] = {}

    for json_path in sorted(scraped_dir.glob("*.json")):
        try:
            with open(json_path, encoding="utf-8") as f:
                data: list[dict[str, Any]] = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("scraped_file_error", path=str(json_path), error=str(exc))
            continue

        for record in data:
            collection = record.get("collection", "")
            hadith_number = record.get("hadithNumber") or record.get("hadith_number")
            if not collection or hadith_number is None:
                continue

            key = f"{collection}:{hadith_number}"
            index[key] = {
                "book_number": record.get("bookNumber") or record.get("book_number"),
                "chapter_number": record.get("chapterNumber") or record.get("chapter_number"),
                "chapter_name_ar": record.get("chapterNameAr") or record.get("chapter_name_ar"),
                "chapter_name_en": record.get("chapterNameEn") or record.get("chapter_name_en"),
            }

    logger.info("scraped_index_built", total_entries=len(index))
    return index


def _resolve_collection_slug(fawaz_name: str) -> str:
    """Map a Fawaz collection name to the sunnah.com slug."""
    return _COLLECTION_ALIASES.get(fawaz_name, fawaz_name)


def run(staging_dir: Path, raw_dir: Path) -> list[Path]:
    """Match Fawaz hadiths to sunnah.com by collection + hadith number.

    Updates null book_number, chapter_number, chapter_name_ar, chapter_name_en
    fields with values from scraped data. Writes enriched Parquet back to
    staging as ``hadiths_fawaz_enriched.parquet``.

    Returns list of output file paths.
    """
    fawaz_path = staging_dir / "hadiths_fawaz.parquet"
    if not fawaz_path.exists():
        logger.warning("fawaz_parquet_missing", path=str(fawaz_path))
        return []

    # Load scraped lookup
    index = _load_scraped_index(raw_dir)
    if not index:
        logger.warning("enrichment_skipped", reason="no scraped data available")
        return []

    # Read Fawaz hadiths
    table = pq.read_table(fawaz_path)
    rows = table.to_pydict()
    num_rows = table.num_rows

    enriched_count = 0
    unmatched_count = 0
    collection_stats: dict[str, dict[str, int]] = {}

    for i in range(num_rows):
        collection = rows["collection_name"][i]
        hadith_number = rows["hadith_number"][i]

        if collection not in collection_stats:
            collection_stats[collection] = {"total": 0, "matched": 0}
        collection_stats[collection]["total"] += 1

        if hadith_number is None:
            unmatched_count += 1
            continue

        slug = _resolve_collection_slug(collection)
        key = f"{slug}:{hadith_number}"
        meta = index.get(key)

        if meta is None:
            unmatched_count += 1
            continue

        # Only fill in null fields (don't overwrite existing data)
        if rows["book_number"][i] is None and meta.get("book_number") is not None:
            rows["book_number"][i] = int(meta["book_number"])
        if rows["chapter_number"][i] is None and meta.get("chapter_number") is not None:
            rows["chapter_number"][i] = int(meta["chapter_number"])
        if rows["chapter_name_ar"][i] is None and meta.get("chapter_name_ar"):
            rows["chapter_name_ar"][i] = str(meta["chapter_name_ar"])
        if rows["chapter_name_en"][i] is None and meta.get("chapter_name_en"):
            rows["chapter_name_en"][i] = str(meta["chapter_name_en"])

        enriched_count += 1
        collection_stats[collection]["matched"] += 1

    # Log match rates per collection
    for coll_name, stats in sorted(collection_stats.items()):
        total = stats["total"]
        matched = stats["matched"]
        rate = round(100.0 * matched / total, 2) if total > 0 else 0.0
        logger.info(
            "enrichment_match_rate",
            collection=coll_name,
            matched=matched,
            total=total,
            rate_pct=rate,
        )

    logger.info(
        "enrichment_complete",
        enriched=enriched_count,
        unmatched=unmatched_count,
        total=num_rows,
    )

    # Build enriched table
    enriched_table = pa.table(rows, schema=HADITH_SCHEMA)
    output_path = write_parquet(
        enriched_table, staging_dir / "hadiths_fawaz_enriched.parquet", HADITH_SCHEMA
    )

    return [output_path]
