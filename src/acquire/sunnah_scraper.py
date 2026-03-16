"""Web scraper for sunnah.com hadith collections.

Scrapes collections not available via the Fawaz dataset or when the
Sunnah.com API key is not configured.  Uses BeautifulSoup + httpx with
rate limiting (500 ms+ between requests).  Resumable: tracks per-collection
progress and skips already-scraped pages.

Output directory: ``data/raw/sunnah_scraped/``
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup, Tag

from src.acquire.base import ensure_dir, write_manifest
from src.utils.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://sunnah.com"
RATE_LIMIT_SECONDS = 0.5
REQUEST_TIMEOUT = 30.0
USER_AGENT = "isnad-graph/1.0 (hadith-research)"

# Collections not in Fawaz dataset that we need to scrape.
SCRAPE_COLLECTIONS = [
    "musnad-ahmad",
    "sunan-darimi",
    "riyadussalihin",
    "adab",
    "shamail",
    "mishkat",
    "bulugh",
    "hisn",
]


def _check_robots_txt(client: httpx.Client) -> bool:
    """Check robots.txt to ensure scraping is allowed."""
    try:
        rp = RobotFileParser()
        resp = client.get(f"{BASE_URL}/robots.txt")
        rp.parse(resp.text.splitlines())
        allowed: bool = rp.can_fetch(USER_AGENT, f"{BASE_URL}/bukhari")
        if not allowed:
            logger.warning("sunnah_scraper_robots_denied")
        return allowed
    except Exception:  # noqa: BLE001
        # If we cannot fetch robots.txt, proceed cautiously.
        logger.warning("sunnah_scraper_robots_unavailable")
        return True


def _fetch_page(client: httpx.Client, url: str) -> BeautifulSoup | None:
    """Fetch a page and return parsed BeautifulSoup, or None on error."""
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        logger.warning("sunnah_scraper_http_error", url=url, status=exc.response.status_code)
        return None
    except httpx.HTTPError:
        logger.warning("sunnah_scraper_request_error", url=url)
        return None


def _extract_hadith_from_row(row: Tag) -> dict[str, Any] | None:
    """Extract a single hadith record from a hadith container element."""
    # Hadith number
    num_tag = row.select_one(".hadith_reference .hadith_num, .hadithNar498")
    hadith_number: int | None = None
    if num_tag:
        text = num_tag.get_text(strip=True).replace(":", "").strip()
        try:
            hadith_number = int(text)
        except ValueError:
            pass

    # Arabic text
    ar_tag = row.select_one(".arabic_hadith_full, .text_details .arabic_text_details")
    text_ar = ar_tag.get_text(strip=True) if ar_tag else None

    # English text
    en_tag = row.select_one(".english_hadith_full, .text_details .english_hadith_full")
    text_en = en_tag.get_text(strip=True) if en_tag else None

    # Grade
    grade_tag = row.select_one(".hadith_grade, .hadith-grade")
    grade = grade_tag.get_text(strip=True) if grade_tag else None

    if not text_ar and not text_en:
        return None

    return {
        "hadith_number": hadith_number,
        "text_ar": text_ar,
        "text_en": text_en,
        "grade": grade,
    }


def _scrape_book_page(
    client: httpx.Client,
    collection: str,
    book_number: int,
) -> list[dict[str, Any]]:
    """Scrape all hadiths from a single book page."""
    url = f"{BASE_URL}/{collection}/{book_number}"
    soup = _fetch_page(client, url)
    if soup is None:
        return []

    # Chapter info
    chapter_name_en: str | None = None
    chapter_name_ar: str | None = None
    chapter_tag = soup.select_one(".book_page_english_name, .englishchapter")
    if chapter_tag:
        chapter_name_en = chapter_tag.get_text(strip=True)
    chapter_ar_tag = soup.select_one(".book_page_arabic_name, .arabicchapter")
    if chapter_ar_tag:
        chapter_name_ar = chapter_ar_tag.get_text(strip=True)

    hadiths: list[dict[str, Any]] = []
    # Each hadith is in a container div
    rows = soup.select(".actualHadithContainer, .hadith")
    for row in rows:
        record = _extract_hadith_from_row(row)
        if record is not None:
            record["book_number"] = book_number
            record["chapter_number"] = book_number  # sunnah.com uses book=chapter often
            record["chapter_name_ar"] = chapter_name_ar
            record["chapter_name_en"] = chapter_name_en
            hadiths.append(record)

    return hadiths


def _get_book_numbers(client: httpx.Client, collection: str) -> list[int]:
    """Get list of book numbers for a collection from its index page."""
    soup = _fetch_page(client, f"{BASE_URL}/{collection}")
    if soup is None:
        return []

    book_numbers: list[int] = []
    # Books are linked as /{collection}/{number}
    links = soup.select("a[href]")
    prefix = f"/{collection}/"
    seen: set[int] = set()
    for link in links:
        href = link.get("href", "")
        if isinstance(href, str) and href.startswith(prefix):
            segment = href[len(prefix) :].rstrip("/")
            if segment.isdigit():
                num = int(segment)
                if num not in seen:
                    seen.add(num)
                    book_numbers.append(num)

    book_numbers.sort()
    return book_numbers


def _scrape_collection(
    client: httpx.Client,
    collection: str,
    dest: Path,
) -> Path | None:
    """Scrape all hadiths for a single collection. Returns output path."""
    output_path = dest / f"{collection}.json"

    # Idempotent: skip if already scraped
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("sunnah_scraper_cached", collection=collection)
        return output_path

    # Progress file for resumability
    progress_path = dest / f".{collection}_progress.json"
    scraped_books: dict[str, list[dict[str, Any]]] = {}
    if progress_path.exists():
        with open(progress_path, encoding="utf-8") as f:
            scraped_books = json.load(f)

    book_numbers = _get_book_numbers(client, collection)
    if not book_numbers:
        logger.warning("sunnah_scraper_no_books", collection=collection)
        return None

    time.sleep(RATE_LIMIT_SECONDS)

    logger.info(
        "sunnah_scraper_starting",
        collection=collection,
        total_books=len(book_numbers),
        already_scraped=len(scraped_books),
    )

    for book_num in book_numbers:
        book_key = str(book_num)
        if book_key in scraped_books:
            continue

        hadiths = _scrape_book_page(client, collection, book_num)
        scraped_books[book_key] = hadiths

        # Save progress after each book
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(scraped_books, f, ensure_ascii=False)

        time.sleep(RATE_LIMIT_SECONDS)

    # Flatten all hadiths into a single list
    all_hadiths: list[dict[str, Any]] = []
    for hadiths in scraped_books.values():
        all_hadiths.extend(hadiths)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_hadiths, f, ensure_ascii=False, indent=2)

    # Clean up progress file
    if progress_path.exists():
        progress_path.unlink()

    logger.info(
        "sunnah_scraper_complete",
        collection=collection,
        books=len(scraped_books),
        hadiths=len(all_hadiths),
    )
    return output_path


def run(raw_dir: Path) -> Path | None:
    """Scrape hadiths from sunnah.com.

    Returns the output directory on success, or ``None`` if robots.txt
    disallows scraping.
    """
    dest = ensure_dir(raw_dir / "sunnah_scraped")

    client = httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    )

    try:
        if not _check_robots_txt(client):
            return None

        saved_files: list[Path] = []
        total_hadiths = 0

        for collection in SCRAPE_COLLECTIONS:
            output_path = _scrape_collection(client, collection, dest)
            if output_path is not None:
                saved_files.append(output_path)
                with open(output_path, encoding="utf-8") as f:
                    data: list[Any] = json.load(f)
                total_hadiths += len(data)

        if saved_files:
            write_manifest(dest, saved_files)

        logger.info(
            "sunnah_scraper_acquired",
            collections=len(saved_files),
            total_hadiths=total_hadiths,
        )
        return dest
    finally:
        client.close()
