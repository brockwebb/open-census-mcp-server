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
    """Provenance information for a context item."""
    document: str
    section: str | None = None
    extraction_method: Literal["manual", "llm_assisted", "automated"] = "manual"


class ContextItem(BaseModel):
    """A unit of pragmatic context."""
    context_id: str = Field(..., pattern=r'^[A-Z]+-[A-Z]+-\d{3}$')  # e.g., ACS-POP-001
    domain: str
    category: str
    latitude: Literal["none", "narrow", "wide", "full"]
    context_text: str
    triggers: list[str] = []
    thread_edges: list[ThreadEdge] = []
    source: Source | None = None


class PackManifest(BaseModel):
    """Metadata for a pragmatic context pack."""
    pack_id: str
    pack_name: str
    parent_pack: str | None = None
    version: str = "1.0.0"
