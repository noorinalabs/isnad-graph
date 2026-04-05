"""Tests for the sunnah.com scraped data parser."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from src.parse.schemas import COLLECTION_SCHEMA, HADITH_SCHEMA
from src.parse.sunnah_scraped import run


def _make_scraped_data(raw_dir: Path) -> None:
    """Create minimal scraped JSON test data."""
    scraped_dir = raw_dir / "sunnah_scraped"
    scraped_dir.mkdir(parents=True)

    hadiths = [
        {
            "hadith_number": 1,
            "book_number": 1,
            "chapter_number": 1,
            "text_ar": "نص الحديث بالعربية",
            "text_en": "Hadith text in English",
            "grade": "Sahih",
            "chapter_name_ar": "كتاب الطهارة",
            "chapter_name_en": "The Book of Purification",
        },
        {
            "hadith_number": 2,
            "book_number": 1,
            "chapter_number": 1,
            "text_ar": "حديث ثاني",
            "text_en": "Second hadith",
            "grade": None,
            "chapter_name_ar": None,
            "chapter_name_en": None,
        },
    ]
    (scraped_dir / "musnad-ahmad.json").write_text(json.dumps(hadiths), encoding="utf-8")


class TestSunnahScrapedParser:
    def test_produces_parquet_files(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)

        output_files = run(raw_dir, staging_dir)

        assert len(output_files) == 2
        assert all(p.exists() for p in output_files)

    def test_hadith_schema_conforms(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sunnah_scraped.parquet")
        assert table.schema == HADITH_SCHEMA
        assert table.num_rows == 2

    def test_collection_schema_conforms(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "collections_sunnah_scraped.parquet")
        assert table.schema == COLLECTION_SCHEMA
        assert table.num_rows == 1

    def test_skips_when_no_raw_data(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"

        output_files = run(raw_dir, staging_dir)

        assert output_files == []

    def test_source_corpus_is_sunnah(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sunnah_scraped.parquet")
        corpora = table.column("source_corpus").to_pylist()
        assert all(c == "sunnah" for c in corpora)

    def test_sect_is_sunni(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sunnah_scraped.parquet")
        sects = table.column("sect").to_pylist()
        assert all(s == "sunni" for s in sects)

    def test_chapter_metadata_preserved(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sunnah_scraped.parquet")
        chapters_en = table.column("chapter_name_en").to_pylist()
        assert chapters_en[0] == "The Book of Purification"
        assert chapters_en[1] is None

    def test_ignores_manifest_json(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)
        # Add manifest.json that should be ignored
        (raw_dir / "sunnah_scraped" / "manifest.json").write_text("{}")

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sunnah_scraped.parquet")
        assert table.num_rows == 2  # Only from musnad-ahmad.json

    def test_ignores_progress_files(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_scraped_data(raw_dir)
        # Add progress file that should be ignored
        (raw_dir / "sunnah_scraped" / ".test_progress.json").write_text("{}")

        run(raw_dir, staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sunnah_scraped.parquet")
        assert table.num_rows == 2
