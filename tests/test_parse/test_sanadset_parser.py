"""Tests for the Sanadset parser."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pyarrow.parquet as pq

from src.parse.sanadset import parse_sanadset
from src.parse.schemas import HADITH_SCHEMA, NARRATOR_MENTION_SCHEMA


def _make_sanadset_csv(path: Path) -> Path:
    """Write a mock Sanadset CSV with NAR-tagged rows and a 'No SANAD' row."""
    header = "hadith_id,book_id,hadith,grade"
    rows = [
        (
            "1",
            "1",
            "<SANAD><NAR>محمد بن عبدالله</NAR> عن <NAR>علي بن أبي طالب</NAR></SANAD>"
            "<MATN>إنما الأعمال بالنيات</MATN>",
            "Sahih",
        ),
        (
            "2",
            "1",
            "<SANAD><NAR>أبو هريرة</NAR> عن <NAR>أنس بن مالك</NAR> عن "
            "<NAR>مالك بن أنس</NAR></SANAD><MATN>لا ضرر ولا ضرار</MATN>",
            "Hasan",
        ),
        (
            "3",
            "2",
            "<SANAD>No SANAD</SANAD><MATN>بعض المتن هنا</MATN>",
            "",
        ),
    ]
    lines = [header]
    for r in rows:
        # Quote the hadith field to handle embedded commas
        lines.append(f'{r[0]},{r[1]},"{r[2]}",{r[3]}')
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class TestSanadsetParser:
    def test_produces_parquet_files(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        _make_sanadset_csv(raw_dir / "hadiths.csv")

        with patch("src.parse.sanadset.get_settings") as mock_settings:
            mock_settings.return_value.data_raw_dir = tmp_path / "raw"
            mock_settings.return_value.data_staging_dir = staging_dir
            outputs = parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)

        assert "hadiths" in outputs
        assert (staging_dir / "hadiths_sanadset.parquet").exists()

    def test_hadith_row_count(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        _make_sanadset_csv(raw_dir / "hadiths.csv")

        with patch("src.parse.sanadset.get_settings") as mock_settings:
            mock_settings.return_value.data_raw_dir = tmp_path / "raw"
            mock_settings.return_value.data_staging_dir = staging_dir
            parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sanadset.parquet")
        assert table.num_rows == 3

    def test_hadith_schema_conforms(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        _make_sanadset_csv(raw_dir / "hadiths.csv")

        with patch("src.parse.sanadset.get_settings") as mock_settings:
            mock_settings.return_value.data_raw_dir = tmp_path / "raw"
            mock_settings.return_value.data_staging_dir = staging_dir
            parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sanadset.parquet")
        assert table.schema == HADITH_SCHEMA

    def test_narrator_mentions_extracted(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        _make_sanadset_csv(raw_dir / "hadiths.csv")

        with patch("src.parse.sanadset.get_settings") as mock_settings:
            mock_settings.return_value.data_raw_dir = tmp_path / "raw"
            mock_settings.return_value.data_staging_dir = staging_dir
            outputs = parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)

        assert "narrator_mentions" in outputs
        table = pq.read_table(staging_dir / "narrator_mentions_sanadset.parquet")
        assert table.schema == NARRATOR_MENTION_SCHEMA
        # Row 1 has 2 narrators, row 2 has 3, row 3 (No SANAD) has 0 => 5 total
        assert table.num_rows == 5

    def test_position_in_chain_sequential(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        _make_sanadset_csv(raw_dir / "hadiths.csv")

        with patch("src.parse.sanadset.get_settings") as mock_settings:
            mock_settings.return_value.data_raw_dir = tmp_path / "raw"
            mock_settings.return_value.data_staging_dir = staging_dir
            parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)

        table = pq.read_table(staging_dir / "narrator_mentions_sanadset.parquet")
        positions = table.column("position_in_chain").to_pylist()
        # First hadith: [0, 1], second: [0, 1, 2]
        assert positions == [0, 1, 0, 1, 2]

    def test_no_sanad_row_has_null_isnad(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        _make_sanadset_csv(raw_dir / "hadiths.csv")

        with patch("src.parse.sanadset.get_settings") as mock_settings:
            mock_settings.return_value.data_raw_dir = tmp_path / "raw"
            mock_settings.return_value.data_staging_dir = staging_dir
            parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)

        table = pq.read_table(staging_dir / "hadiths_sanadset.parquet")
        isnads = table.column("isnad_raw_ar").to_pylist()
        # Third row should be None (No SANAD)
        assert isnads[2] is None
        # First two should have values
        assert isnads[0] is not None
        assert isnads[1] is not None

    def test_no_csv_raises(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw" / "sanadset"
        raw_dir.mkdir(parents=True)
        staging_dir = tmp_path / "staging"

        import pytest

        with pytest.raises(FileNotFoundError):
            with patch("src.parse.sanadset.get_settings") as mock_settings:
                mock_settings.return_value.data_raw_dir = tmp_path / "raw"
                mock_settings.return_value.data_staging_dir = staging_dir
                parse_sanadset(raw_dir=raw_dir, staging_dir=staging_dir)
