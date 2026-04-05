"""Grading node model for the isnad graph."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.models.enums import HadithGrade

__all__ = ["Grading"]


class Grading(BaseModel):
    """A scholar's grading of a specific hadith.

    Multiple scholars may grade the same hadith differently based on
    their methodology school and era.
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    id: str
    """Unique identifier for this grading record."""
    hadith_id: str
    """FK to Hadith.id."""
    scholar_name: str
    """Name of the scholar who issued the grading."""
    grade: HadithGrade
    """Authenticity grade assigned by the scholar."""
    methodology_school: str | None = None
    """Methodology school, e.g. 'Hanbali', 'Imami'."""
    era: str | None = None
    """Era of the grading, e.g. 'classical', 'modern'."""
