"""Chain node model for the isnad graph."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import ChainClassification

__all__ = ["Chain"]


class Chain(BaseModel):
    """A single chain of transmission (isnad) for a hadith.

    A hadith may have multiple chains; each chain is an ordered sequence
    of narrators connecting the source (Prophet/Imam) to the compiler.
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    id: str
    """Canonical ID with 'chn:' prefix, e.g. 'chn:bukhari-001-001-0'."""
    hadith_id: str
    """FK to Hadith.id."""
    chain_index: int
    """0-based index for multi-chain hadiths."""
    full_chain_text_ar: str | None = None
    """Full Arabic text of the chain."""
    full_chain_text_en: str | None = None
    """Full English text of the chain."""
    chain_length: int
    """Number of narrators in the chain."""
    is_complete: bool
    """Whether the chain has no missing links."""
    is_elevated: bool = False
    """Whether this is an ali isnad (short chain)."""
    classification: ChainClassification
    """Classification of the chain's continuity."""
    narrator_ids: list[str] = Field(default_factory=list)
    """Ordered list of Narrator IDs in this chain."""

    @field_validator("id")
    @classmethod
    def _validate_id_prefix(cls, v: str) -> str:
        if not v.startswith("chn:"):
            msg = f"Chain id must start with 'chn:', got '{v}'"
            raise ValueError(msg)
        return v
