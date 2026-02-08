"""Pydantic models for pragmatic context staging JSON validation.

Models defined per docs/design/pragmatics_vocabulary.md schema.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ThreadEdge(BaseModel):
    """A directed edge in the context thread graph."""
    target: str  # context_id of target
    edge_type: Literal["inherits", "applies_to", "relates_to"]


class Source(BaseModel):
    """A single source citation with locator information."""
    document: str                    # Catalog ID, e.g., "ACS-GEN-001"
    section: str | None = None       # Chapter/section, e.g., "Ch. 7"
    page: int | str | None = None    # Page number or range, e.g., 53 or "53-57"
    extraction_method: Literal["manual", "llm_assisted", "automated"] = "manual"


class Provenance(BaseModel):
    """Full provenance for a context item.

    Single-source grounded items need only sources + confidence.
    Multi-source interpreted/expert items require synthesis_note
    explaining how the sources combine to form the judgment.
    Limitations flag known boundary conditions where guidance breaks down.
    """
    sources: list[Source] = Field(..., min_length=1)
    synthesis_note: str | None = None        # Required when len(sources) > 1
    confidence: Literal["grounded", "interpreted", "expert_judgment"] = "grounded"
    limitations: str | None = None           # Where this guidance breaks down


class ContextItem(BaseModel):
    """A unit of pragmatic context."""
    context_id: str = Field(..., pattern=r'^[A-Z]+-[A-Z]+-\d{3}$')  # e.g., ACS-POP-001
    domain: str
    category: str
    latitude: Literal["none", "narrow", "wide", "full"]
    context_text: str
    triggers: list[str] = []
    thread_edges: list[ThreadEdge] = []
    provenance: Provenance


class PackManifest(BaseModel):
    """Metadata for a pragmatic context pack."""
    pack_id: str
    pack_name: str
    parent_pack: str | None = None
    version: str = "1.0.0"
