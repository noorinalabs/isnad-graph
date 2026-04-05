"""Tests for the Fawaz metadata enrichment module."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.parse.enrich_metadata import run
from src.parse.schemas import HADITH_SCHEMA


def _make_fawaz_parquet(staging_dir: Path, rows: list[dict] | None = None) -> Path:
    """Write a minimal hadiths_fawaz.parquet for testing."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    if rows is None:
        rows = [
            {
                "source_id": "fawaz:bukhari:1",
                "source_corpus": "fawaz",
                "collection_name": "bukhari",
                "book_number": None,
                "chapter_number": None,
                "hadith_number": 1,
                "matn_ar": None,
                "matn_en": "Actions are by intentions",
                "isnad_raw_ar": None,
                "isnad_raw_en": None,
                "full_text_ar": None,
                "full_text_en": "Actions are by intentions",
                "grade": None,
                "chapter_name_ar": None,
                "chapter_name_en": None,
                "sect": "sunni",
            },
            {
                "source_id": "fawaz:bukhari:2",
                "source_corpus": "fawaz",
                "collection_name": "bukhari",
                "book_number": None,
                "chapter_number": None,
                "hadith_number": 2,
                "matn_ar": None,
                "matn_en": "Islam is built on five pillars",
                "isnad_raw_ar": None,
                "isnad_raw_en": None,
                "full_text_ar": None,
                "full_text_en": "Islam is built on five pillars",
                "grade": None,
                "chapter_name_ar": None,
                "chapter_name_en": None,
                "sect": "sunni",
            },
            {
                "source_id": "fawaz:muslim:10",
                "source_corpus": "fawaz",
                "collection_name": "muslim",
                "book_number": None,
                "chapter_number": None,
                "hadith_number": 10,
                "matn_ar": None,
                "matn_en": "A Muslim is one from whose tongue...",
                "isnad_raw_ar": None,
                "isnad_raw_en": None,
                "full_text_ar": None,
                "full_text_en": "A Muslim is one from whose tongue...",
                "grade": None,
                "chapter_name_ar": None,
                "chapter_name_en": None,
                "sect": "sunni",
            },
        ]

    table = pa.table(
        {field.name: [r[field.name] for r in rows] for field in HADITH_SCHEMA},
        schema=HADITH_SCHEMA,
    )
    path = staging_dir / "hadiths_fawaz.parquet"
    pq.write_table(table, path)
    return path


def _make_scraped_data(raw_dir: Path, records: list[dict] | None = None) -> Path:
    """Write mock sunnah_scraped JSON files."""
    scraped_dir = raw_dir / "sunnah_scraped"
    scraped_dir.mkdir(parents=True, exist_ok=True)
    if records is None:
        records = [
            {
                "collection": "bukhari",
                "hadithNumber": 1,
                "bookNumber": 1,
                "chapterNumber": 1,
                "chapterNameAr": "\u0628\u062f\u0621 \u0627\u0644\u0648\u062d\u064a",
                "chapterNameEn": "Revelation",
            },
            {
                "collection": "bukhari",
                "hadithNumber": 2,
                "bookNumber": 1,
                "chapterNumber": 1,
                "chapterNameAr": "\u0628\u062f\u0621 \u0627\u0644\u0648\u062d\u064a",
                "chapterNameEn": "Revelation",
            },
        ]
    path = scraped_dir / "bukhari.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return scraped_dir


class TestEnrichMetadata:
    def test_enriches_matching_hadiths(self, tmp_path: Path) -> None:
        staging_dir = tmp_path / "staging"
        raw_dir = tmp_path / "raw"
        _make_fawaz_parquet(staging_dir)
        _make_scraped_data(raw_dir)

        result = run(staging_dir, raw_dir)

        assert len(result) == 1
        enriched = pq.read_table(result[0])
        assert enriched.schema == HADITH_SCHEMA

        rows = enriched.to_pydict()
        # Bukhari hadith 1 should be enriched
        assert rows["book_number"][0] == 1
        assert rows["chapter_number"][0] == 1
        assert rows["chapter_name_ar"][0] == "\u0628\u062f\u0621 \u0627\u0644\u0648\u062d\u064a"
        assert rows["chapter_name_en"][0] == "Revelation"

        # Bukhari hadith 2 should also be enriched
        assert rows["book_number"][1] == 1
        assert rows["chapter_number"][1] == 1

    def test_unmatched_hadiths_kept_unchanged(self, tmp_path: Path) -> None:
        staging_dir = tmp_path / "staging"
        raw_dir = tmp_path / "raw"
        _make_fawaz_parquet(staging_dir)
        _make_scraped_data(raw_dir)

        result = run(staging_dir, raw_dir)

        enriched = pq.read_table(result[0])
        rows = enriched.to_pydict()
        # Muslim hadith 10 has no match in scraped data
        assert rows["book_number"][2] is None
        assert rows["chapter_number"][2] is None
        assert rows["chapter_name_ar"][2] is None
        assert rows["chapter_name_en"][2] is None
        # But original data is preserved
        assert rows["collection_name"][2] == "muslim"
        assert rows["hadith_number"][2] == 10

    def test_idempotency(self, tmp_path: Path) -> None:
        """Enriching already-enriched data should not change values."""
        staging_dir = tmp_path / "staging"
        raw_dir = tmp_path / "raw"
        _make_fawaz_parquet(staging_dir)
        _make_scraped_data(raw_dir)

        # First enrichment
        result1 = run(staging_dir, raw_dir)
        first_enriched = pq.read_table(result1[0])

        # Copy enriched back as fawaz source for second run
        pq.write_table(first_enriched, staging_dir / "hadiths_fawaz.parquet")

        # Second enrichment
        result2 = run(staging_dir, raw_dir)
        second_enriched = pq.read_table(result2[0])

        assert first_enriched.equals(second_enriched)

    def test_no_scraped_data_returns_empty(self, tmp_path: Path) -> None:
        staging_dir = tmp_path / "staging"
        raw_dir = tmp_path / "raw"
        _make_fawaz_parquet(staging_dir)
        # No scraped data directory

        result = run(staging_dir, raw_dir)
        assert result == []

    def test_no_fawaz_parquet_returns_empty(self, tmp_path: Path) -> None:
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir(parents=True)
        raw_dir = tmp_path / "raw"
        _make_scraped_data(raw_dir)

        result = run(staging_dir, raw_dir)
        assert result == []

    def test_does_not_overwrite_existing_values(self, tmp_path: Path) -> None:
        """If a field already has a value, enrichment should not overwrite it."""
        staging_dir = tmp_path / "staging"
        raw_dir = tmp_path / "raw"

        rows = [
            {
                "source_id": "fawaz:bukhari:1",
                "source_corpus": "fawaz",
                "collection_name": "bukhari",
                "book_number": 99,  # pre-existing value
                "chapter_number": 88,
                "hadith_number": 1,
                "matn_ar": None,
                "matn_en": "Actions are by intentions",
                "isnad_raw_ar": None,
                "isnad_raw_en": None,
                "full_text_ar": None,
                "full_text_en": "Actions are by intentions",
                "grade": None,
                "chapter_name_ar": "existing_ar",
                "chapter_name_en": "existing_en",
                "sect": "sunni",
            },
        ]
        _make_fawaz_parquet(staging_dir, rows)
        _make_scraped_data(raw_dir)

        result = run(staging_dir, raw_dir)
        enriched = pq.read_table(result[0])
        enriched_rows = enriched.to_pydict()

        # Pre-existing values should be preserved
        assert enriched_rows["book_number"][0] == 99
        assert enriched_rows["chapter_number"][0] == 88
        assert enriched_rows["chapter_name_ar"][0] == "existing_ar"
        assert enriched_rows["chapter_name_en"][0] == "existing_en"

    def test_alternate_scraped_key_format(self, tmp_path: Path) -> None:
        """Test scraped data using snake_case field names."""
        staging_dir = tmp_path / "staging"
        raw_dir = tmp_path / "raw"
        _make_fawaz_parquet(staging_dir)

        records = [
            {
                "collection": "bukhari",
                "hadith_number": 1,
                "book_number": 5,
                "chapter_number": 3,
                "chapter_name_ar": "\u0628\u0627\u0628",
                "chapter_name_en": "Chapter",
            },
        ]
        _make_scraped_data(raw_dir, records)

        result = run(staging_dir, raw_dir)
        enriched = pq.read_table(result[0])
        rows = enriched.to_pydict()
        assert rows["book_number"][0] == 5
        assert rows["chapter_number"][0] == 3
