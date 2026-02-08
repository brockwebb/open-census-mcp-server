"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from census_mcp.pragmatics.models import ContextItem, ThreadEdge, Source, Provenance, PackManifest


def test_valid_context_item():
    """Test valid context item creation."""
    item = ContextItem(
        context_id="ACS-POP-001",
        domain="acs",
        category="population",
        latitude="none",
        context_text="Test context",
        triggers=["test"],
        thread_edges=[],
        provenance=Provenance(
            sources=[Source(document="Test Doc")],
            confidence="grounded"
        )
    )
    assert item.context_id == "ACS-POP-001"
    assert item.latitude == "none"


def test_invalid_latitude():
    """Test invalid latitude value is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ContextItem(
            context_id="ACS-POP-001",
            domain="acs",
            category="population",
            latitude="invalid",  # Invalid
            context_text="Test",
            provenance=Provenance(
                sources=[Source(document="Test")],
                confidence="grounded"
            )
        )
    assert "latitude" in str(exc_info.value)


def test_invalid_context_id_pattern():
    """Test invalid context_id pattern is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ContextItem(
            context_id="invalid-id",  # Wrong format
            domain="acs",
            category="population",
            latitude="none",
            context_text="Test",
            provenance=Provenance(
                sources=[Source(document="Test")],
                confidence="grounded"
            )
        )
    assert "context_id" in str(exc_info.value)


def test_valid_context_id_patterns():
    """Test various valid context_id patterns."""
    valid_ids = ["ACS-POP-001", "GEN-TV-123", "CEN-GEO-999"]

    for context_id in valid_ids:
        item = ContextItem(
            context_id=context_id,
            domain="test",
            category="test",
            latitude="none",
            context_text="Test",
            provenance=Provenance(
                sources=[Source(document="Test")],
                confidence="grounded"
            )
        )
        assert item.context_id == context_id


def test_thread_edge_validation():
    """Test thread edge validation."""
    edge = ThreadEdge(target="ACS-POP-001", edge_type="inherits")
    assert edge.target == "ACS-POP-001"
    assert edge.edge_type == "inherits"
    
    # Invalid edge type
    with pytest.raises(ValidationError):
        ThreadEdge(target="ACS-POP-001", edge_type="invalid")


def test_source_validation():
    """Test source validation."""
    source = Source(document="Test Doc", extraction_method="manual")
    assert source.document == "Test Doc"
    assert source.extraction_method == "manual"
    
    # Invalid extraction method
    with pytest.raises(ValidationError):
        Source(document="Test", extraction_method="invalid")


def test_pack_manifest_validation():
    """Test pack manifest validation."""
    manifest = PackManifest(
        pack_id="acs",
        pack_name="ACS",
        version="1.0.0"
    )
    assert manifest.pack_id == "acs"
    assert manifest.parent_pack is None
    
    # With parent
    manifest2 = PackManifest(
        pack_id="acs",
        pack_name="ACS",
        parent_pack="census",
        version="2.0.0"
    )
    assert manifest2.parent_pack == "census"


def test_context_item_defaults():
    """Test context item default values."""
    item = ContextItem(
        context_id="ACS-POP-001",
        domain="acs",
        category="test",
        latitude="none",
        context_text="Test",
        provenance=Provenance(
            sources=[Source(document="Test")],
            confidence="grounded"
        )
    )
    assert item.triggers == []
    assert item.thread_edges == []
