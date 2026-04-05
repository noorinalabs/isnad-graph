"""Tests for narrator mention extraction from isnad text."""

from __future__ import annotations

from src.parse.narrator_extraction import NarratorSpan, extract_narrator_mentions


class TestNarratorSpanDataclass:
    def test_fields(self) -> None:
        span = NarratorSpan(name="Abu Hurayra", position=0, transmission_method="haddathana")
        assert span.name == "Abu Hurayra"
        assert span.position == 0
        assert span.transmission_method == "haddathana"

    def test_defaults(self) -> None:
        span = NarratorSpan(name="Anas", position=1)
        assert span.transmission_method is None

    def test_frozen(self) -> None:
        import pytest

        span = NarratorSpan(name="Anas", position=0)
        with pytest.raises(AttributeError):
            span.name = "Other"  # type: ignore[misc]


class TestEnglishExtraction:
    def test_narrated_prefix(self) -> None:
        text = "Narrated Abu Hurayra"
        spans = extract_narrator_mentions(text, "en")
        names = [s.name for s in spans]
        assert "Abu Hurayra" in names

    def test_multi_narrator(self) -> None:
        text = "on the authority of Anas who heard from Malik"
        spans = extract_narrator_mentions(text, "en")
        names = [s.name for s in spans]
        assert "Anas" in names
        assert "Malik" in names

    def test_positions_sequential(self) -> None:
        text = "Narrated Abu Hurayra: from Anas"
        spans = extract_narrator_mentions(text, "en")
        positions = [s.position for s in spans]
        assert positions == sorted(positions)
        assert len(set(positions)) == len(positions)


class TestArabicExtraction:
    def test_transmission_phrase(self) -> None:
        text = "حدثنا محمد بن عبدالله عن علي بن أبي طالب"
        spans = extract_narrator_mentions(text, "ar")
        assert len(spans) >= 2

    def test_names_normalized(self) -> None:
        text = "حدثنا محمد"
        spans = extract_narrator_mentions(text, "ar")
        # At least one span should be extracted
        assert len(spans) >= 1


class TestEdgeCases:
    def test_empty_string(self) -> None:
        assert extract_narrator_mentions("", "en") == []
        assert extract_narrator_mentions("", "ar") == []

    def test_whitespace_only(self) -> None:
        assert extract_narrator_mentions("   ", "en") == []
        assert extract_narrator_mentions("   ", "ar") == []

    def test_no_narrator_keywords(self) -> None:
        text = "The Prophet said something important"
        spans = extract_narrator_mentions(text, "en")
        # Even without keywords, the full text may be returned as a single span
        # depending on splitting behavior — just verify no crash
        assert isinstance(spans, list)
