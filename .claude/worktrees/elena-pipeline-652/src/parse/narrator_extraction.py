"""Shared narrator mention extraction from isnad text.

Supports both English and Arabic isnad strings. English extraction uses
keyword-based splitting; Arabic extraction uses transmission phrase detection
from ``src.utils.arabic``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.utils.arabic import extract_transmission_phrases, normalize_arabic

__all__ = ["NarratorSpan", "extract_narrator_mentions"]

# English transmission keywords used as chain delimiters.
_EN_DELIMITERS: re.Pattern[str] = re.compile(
    r"\b(?:Narrated|reported\s+by|on\s+the\s+authority\s+of|from|who\s+heard\s+from)\b",
    re.IGNORECASE,
)

# Trailing punctuation to strip from extracted names.
_TRAILING_PUNCT_RE: re.Pattern[str] = re.compile(r"[.,;:!?()]+$")


@dataclass(frozen=True)
class NarratorSpan:
    """A narrator mention extracted from isnad text."""

    name: str
    position: int
    transmission_method: str | None = None


def _clean_name(raw: str) -> str | None:
    """Strip whitespace and trailing punctuation. Return None if empty."""
    cleaned = _TRAILING_PUNCT_RE.sub("", raw.strip())
    return cleaned if cleaned else None


def _extract_english(text: str) -> list[NarratorSpan]:
    """Extract narrator mentions from English isnad text."""
    parts = _EN_DELIMITERS.split(text)
    spans: list[NarratorSpan] = []
    for i, part in enumerate(parts):
        name = _clean_name(part)
        if name:
            spans.append(NarratorSpan(name=name, position=i))
    return spans


def _extract_arabic(text: str) -> list[NarratorSpan]:
    """Extract narrator mentions from Arabic isnad text."""
    phrases = extract_transmission_phrases(text)
    if not phrases:
        name = normalize_arabic(text.strip())
        if name:
            return [NarratorSpan(name=name, position=0)]
        return []

    spans: list[NarratorSpan] = []
    position = 0

    # Text before the first transmission phrase may contain a name.
    if phrases[0][0] > 0:
        prefix = text[: phrases[0][0]]
        prefix_name = _clean_name(normalize_arabic(prefix))
        if prefix_name:
            spans.append(NarratorSpan(name=prefix_name, position=position))
            position += 1

    for idx, (start, end, label) in enumerate(phrases):
        # The name follows the transmission phrase, up to the next phrase or end of text.
        next_start = phrases[idx + 1][0] if idx + 1 < len(phrases) else len(text)
        segment = text[end:next_start]
        seg_name = _clean_name(normalize_arabic(segment))
        if seg_name:
            spans.append(NarratorSpan(name=seg_name, position=position, transmission_method=label))
            position += 1

    return spans


def extract_narrator_mentions(isnad_text: str, language: str) -> list[NarratorSpan]:
    """Extract narrator mentions from isnad text.

    Args:
        isnad_text: Raw isnad string.
        language: ``"en"`` for English, ``"ar"`` for Arabic.

    Returns:
        List of :class:`NarratorSpan` in chain order.
    """
    if not isnad_text or not isnad_text.strip():
        return []
    if language == "ar":
        return _extract_arabic(isnad_text)
    return _extract_english(isnad_text)
