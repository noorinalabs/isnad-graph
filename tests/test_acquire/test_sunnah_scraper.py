"""Tests for the sunnah.com web scraper."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from src.acquire.sunnah_scraper import (
    SCRAPE_COLLECTIONS,
    _extract_hadith_from_row,
    _get_book_numbers,
    _scrape_book_page,
    run,
)

SAMPLE_COLLECTION_HTML = """
<html><body>
<a href="/musnad-ahmad/1">Book 1</a>
<a href="/musnad-ahmad/2">Book 2</a>
<a href="/musnad-ahmad/3">Book 3</a>
<a href="/other-link">Other</a>
</body></html>
"""

SAMPLE_BOOK_HTML = """
<html><body>
<div class="book_page_english_name">The Book of Purification</div>
<div class="book_page_arabic_name">كتاب الطهارة</div>
<div class="actualHadithContainer">
  <div class="hadith_reference"><span class="hadith_num">1</span></div>
  <div class="arabic_hadith_full">نص الحديث بالعربية</div>
  <div class="english_hadith_full">The hadith text in English</div>
  <div class="hadith_grade">Sahih</div>
</div>
<div class="actualHadithContainer">
  <div class="hadith_reference"><span class="hadith_num">2</span></div>
  <div class="arabic_hadith_full">حديث ثاني</div>
  <div class="english_hadith_full">Second hadith</div>
</div>
</body></html>
"""

ROBOTS_TXT = "User-agent: *\nAllow: /\n"


def _mock_response(text: str, status_code: int = 200) -> httpx.Response:
    """Build a mock httpx.Response."""
    return httpx.Response(
        status_code=status_code,
        text=text,
        request=httpx.Request("GET", "https://sunnah.com/test"),
    )


class TestExtractHadithFromRow:
    def test_extracts_full_record(self) -> None:
        from bs4 import BeautifulSoup

        html = """
        <div class="actualHadithContainer">
          <div class="hadith_reference"><span class="hadith_num">42</span></div>
          <div class="arabic_hadith_full">عربي</div>
          <div class="english_hadith_full">English text</div>
          <div class="hadith_grade">Hasan</div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one(".actualHadithContainer")
        assert row is not None
        result = _extract_hadith_from_row(row)

        assert result is not None
        assert result["hadith_number"] == 42
        assert result["text_ar"] == "عربي"
        assert result["text_en"] == "English text"
        assert result["grade"] == "Hasan"

    def test_returns_none_when_no_text(self) -> None:
        from bs4 import BeautifulSoup

        html = '<div class="actualHadithContainer"><span>empty</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one(".actualHadithContainer")
        assert row is not None
        result = _extract_hadith_from_row(row)
        assert result is None


class TestGetBookNumbers:
    def test_parses_book_links(self) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.return_value = _mock_response(SAMPLE_COLLECTION_HTML)

        books = _get_book_numbers(client, "musnad-ahmad")
        assert books == [1, 2, 3]

    def test_returns_empty_on_404(self) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=httpx.Request("GET", "https://sunnah.com/test"),
            response=httpx.Response(404),
        )

        books = _get_book_numbers(client, "nonexistent")
        assert books == []


class TestScrapeBookPage:
    def test_extracts_hadiths(self) -> None:
        client = MagicMock(spec=httpx.Client)
        client.get.return_value = _mock_response(SAMPLE_BOOK_HTML)

        hadiths = _scrape_book_page(client, "musnad-ahmad", 1)
        assert len(hadiths) == 2
        assert hadiths[0]["hadith_number"] == 1
        assert hadiths[0]["text_ar"] == "نص الحديث بالعربية"
        assert hadiths[0]["book_number"] == 1
        assert hadiths[0]["chapter_name_en"] == "The Book of Purification"
        assert hadiths[0]["chapter_name_ar"] == "كتاب الطهارة"


class TestRun:
    @patch("src.acquire.sunnah_scraper.SCRAPE_COLLECTIONS", ["test-collection"])
    @patch("src.acquire.sunnah_scraper.RATE_LIMIT_SECONDS", 0)
    def test_scrapes_and_saves_json(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"

        with patch("src.acquire.sunnah_scraper.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value = client

            # robots.txt
            client.get.side_effect = [
                _mock_response(ROBOTS_TXT),  # robots.txt
                _mock_response(SAMPLE_COLLECTION_HTML.replace("musnad-ahmad", "test-collection")),
                _mock_response(SAMPLE_BOOK_HTML),  # book 1
                _mock_response(SAMPLE_BOOK_HTML),  # book 2
                _mock_response(SAMPLE_BOOK_HTML),  # book 3
            ]

            result = run(raw_dir)

        assert result is not None
        assert (raw_dir / "sunnah_scraped" / "test-collection.json").exists()
        with open(raw_dir / "sunnah_scraped" / "test-collection.json") as f:
            data = json.load(f)
        assert len(data) == 6  # 2 hadiths per book * 3 books

    @patch("src.acquire.sunnah_scraper.SCRAPE_COLLECTIONS", ["test-collection"])
    @patch("src.acquire.sunnah_scraper.RATE_LIMIT_SECONDS", 0)
    def test_idempotent_skips_existing(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"
        dest = raw_dir / "sunnah_scraped"
        dest.mkdir(parents=True)
        (dest / "test-collection.json").write_text('[{"hadith_number": 1}]')

        with patch("src.acquire.sunnah_scraper.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value = client
            client.get.return_value = _mock_response(ROBOTS_TXT)

            result = run(raw_dir)

        assert result is not None

    @patch("src.acquire.sunnah_scraper.RATE_LIMIT_SECONDS", 0)
    def test_robots_denied(self, tmp_path: Path) -> None:
        raw_dir = tmp_path / "raw"

        with patch("src.acquire.sunnah_scraper.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value = client
            client.get.return_value = _mock_response("User-agent: *\nDisallow: /\n")

            result = run(raw_dir)

        assert result is None

    def test_target_collections_defined(self) -> None:
        assert len(SCRAPE_COLLECTIONS) == 8
        assert "musnad-ahmad" in SCRAPE_COLLECTIONS
        assert "riyadussalihin" in SCRAPE_COLLECTIONS
