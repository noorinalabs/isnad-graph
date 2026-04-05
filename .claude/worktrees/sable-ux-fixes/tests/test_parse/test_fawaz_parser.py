"""End-to-end tests for the Fawaz parser."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from src.parse.fawaz import run
from src.parse.schemas import COLLECTION_SCHEMA, HADITH_SCHEMA


def _make_fawaz_data(
    raw_dir: Path,
    *,
    include_arabic: bool = True,
    arabic_extra_hadith: bool = False,
    english_extra_hadith: bool = False,
) -> None:
    """Create minimal Fawaz edition JSON test data."""
    fawaz_dir = raw_dir / "fawaz"
    fawaz_dir.mkdir(parents=True)

    editions: dict[str, dict[str, str]] = {
        "eng-bukhari": {"name": "Sahih al-Bukhari", "collection": "bukhari"},
    }
    if include_arabic:
        editions["ara-bukhari"] = {"name": "صحيح البخاري", "collection": "bukhari"}

    (fawaz_dir / "editions.json").write_text(json.dumps(editions), encoding="utf-8")
    (fawaz_dir / "info.json").write_text(json.dumps({}), encoding="utf-8")

    # English edition
    eng_hadiths = [
        {"hadithnumber": 1, "text": "Actions are by intentions", "grades": []},
        {"hadithnumber": 2, "text": "Islam is built on five pillars", "grades": []},
        {"hadithnumber": 3, "text": "None of you truly believes", "grades": []},
    ]
    if english_extra_hadith:
        eng_hadiths.append({"hadithnumber": 4, "text": "English-only hadith", "grades": []})

    eng_data = {
        "metadata": {"name": "Sahih al-Bukhari", "author": "Imam al-Bukhari"},
        "hadiths": eng_hadiths,
    }
    (fawaz_dir / "eng-bukhari.json").write_text(json.dumps(eng_data), encoding="utf-8")

    # Arabic edition
    if include_arabic:
        ara_hadiths = [
            {"hadithnumber": 1, "text": "إنما الأعمال بالنيات", "grades": []},
            {"hadithnumber": 2, "text": "بني الإسلام على خمس", "grades": []},
            {"hadithnumber": 3, "text": "لا يؤمن أحدكم", "grades": []},
        ]
        if arabic_extra_hadith:
            ara_hadiths.append({"hadithnumber": 5, "text": "حديث عربي فقط", "grades": []})

        ara_data = {
            "metadata": {"name": "صحيح البخاري", "author": "الإمام البخاري"},
            "hadiths": ara_hadiths,
        }
        (fawaz_dir / "ara-bukhari.json").write_text(
            json.dumps(ara_data, ensure_ascii=False), encoding="utf-8"
        )


class TestFawazParser:
    def test_produces_parquet_files(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir)

        hadiths_path, collections_path = run(raw_dir, staging_dir)

        assert hadiths_path.exists()
        assert collections_path.exists()

    def test_hadith_schema_conforms(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir)

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        assert table.schema == HADITH_SCHEMA
        assert table.num_rows == 3

    def test_collection_schema_conforms(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir)

        _, collections_path = run(raw_dir, staging_dir)

        table = pq.read_table(collections_path)
        assert table.schema == COLLECTION_SCHEMA
        assert table.num_rows == 1

    def test_source_corpus_field(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir)

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        corpora = table.column("source_corpus").to_pylist()
        assert all(c == "fawaz" for c in corpora)

    def test_arabic_text_merged(self, tmp_path: Path) -> None:
        """Arabic matn_ar should be populated when Arabic edition exists."""
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir, include_arabic=True)

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        ar_texts = table.column("matn_ar").to_pylist()
        en_texts = table.column("matn_en").to_pylist()

        # All 3 hadiths should have both Arabic and English
        assert all(t is not None for t in ar_texts)
        assert all(t is not None for t in en_texts)
        assert ar_texts[0] == "إنما الأعمال بالنيات"
        assert en_texts[0] == "Actions are by intentions"

    def test_no_arabic_edition(self, tmp_path: Path) -> None:
        """When no Arabic edition exists, matn_ar should be None."""
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir, include_arabic=False)

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        ar_texts = table.column("matn_ar").to_pylist()
        assert all(t is None for t in ar_texts)

    def test_arabic_only_hadith(self, tmp_path: Path) -> None:
        """Hadiths present only in Arabic should still appear in output."""
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir, include_arabic=True, arabic_extra_hadith=True)

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        # 3 shared + 1 Arabic-only = 4
        assert table.num_rows == 4

        numbers = table.column("hadith_number").to_pylist()
        ar_texts = table.column("matn_ar").to_pylist()
        en_texts = table.column("matn_en").to_pylist()

        # Arabic-only hadith (number 5) should have Arabic but no English
        idx = numbers.index(5)
        assert ar_texts[idx] == "حديث عربي فقط"
        assert en_texts[idx] is None

    def test_english_only_hadith(self, tmp_path: Path) -> None:
        """Hadiths present only in English should have no Arabic text."""
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(raw_dir, include_arabic=True, english_extra_hadith=True)

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        # 3 shared + 1 English-only = 4
        assert table.num_rows == 4

        numbers = table.column("hadith_number").to_pylist()
        ar_texts = table.column("matn_ar").to_pylist()
        en_texts = table.column("matn_en").to_pylist()

        # English-only hadith (number 4) should have English but no Arabic
        idx = numbers.index(4)
        assert ar_texts[idx] is None
        assert en_texts[idx] == "English-only hadith"

    def test_mixed_missing_languages(self, tmp_path: Path) -> None:
        """Both Arabic-only and English-only hadiths in the same collection."""
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(
            raw_dir,
            include_arabic=True,
            arabic_extra_hadith=True,
            english_extra_hadith=True,
        )

        hadiths_path, _ = run(raw_dir, staging_dir)

        table = pq.read_table(hadiths_path)
        # 3 shared + 1 English-only + 1 Arabic-only = 5
        assert table.num_rows == 5

    def test_collection_total_includes_merged(self, tmp_path: Path) -> None:
        """Collection total_hadiths should count all merged rows."""
        raw_dir = tmp_path / "raw"
        staging_dir = tmp_path / "staging"
        _make_fawaz_data(
            raw_dir,
            include_arabic=True,
            arabic_extra_hadith=True,
        )

        _, collections_path = run(raw_dir, staging_dir)

        table = pq.read_table(collections_path)
        totals = table.column("total_hadiths").to_pylist()
        # 3 shared + 1 Arabic-only = 4
        assert totals[0] == 4
