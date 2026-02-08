"""Unit tests for PragmaticsRetriever."""

import json
import sqlite3
from pathlib import Path

import pytest

from census_mcp.pragmatics.schema import create_tables
from census_mcp.pragmatics.pack import PackLoader
from census_mcp.pragmatics.retriever import PragmaticsRetriever


@pytest.fixture
def test_pack_db(tmp_path):
    """Create a test pack database with ACS-like content."""
    db_path = tmp_path / "acs.db"
    conn = sqlite3.connect(db_path)

    create_tables(conn)

    # Insert pack metadata
    conn.execute(
        """INSERT INTO packs (pack_id, pack_name, parent_pack, version, compiled_date)
           VALUES ('acs', 'ACS Pack', NULL, '1.0.0', '2024-01-01')"""
    )

    # Insert test contexts with various triggers
    contexts = [
        {
            "context_id": "ACS-POP-001",
            "domain": "acs",
            "category": "population",
            "latitude": "none",
            "text": "ACS 1-year estimates are only available for areas with 65,000+ population.",
            "triggers": ["population_threshold", "1yr_acs", "1-year"],
            "source": json.dumps({"document": "ACS Handbook", "section": "2.3"}),
        },
        {
            "context_id": "ACS-GEO-001",
            "domain": "acs",
            "category": "geography",
            "latitude": "narrow",
            "text": "Small area estimation requires ACS 5-year data. Tract and block group data not available in 1-year.",
            "triggers": ["small_area", "block_group", "tract"],
            "source": json.dumps({"document": "ACS Handbook", "section": "3.1"}),
        },
        {
            "context_id": "ACS-MOE-001",
            "domain": "acs",
            "category": "reliability",
            "latitude": "full",
            "text": "Always report margins of error. Estimates with CV > 40% are unreliable.",
            "triggers": ["margin_of_error", "reliability"],
            "source": json.dumps({"document": "ACS Handbook", "section": "7.2"}),
        },
        {
            "context_id": "ACS-DOL-001",
            "domain": "acs",
            "category": "comparability",
            "latitude": "narrow",
            "text": "Dollar values must be inflation-adjusted for temporal comparisons.",
            "triggers": ["dollar_values", "inflation"],
            "source": json.dumps({"document": "ACS Handbook", "section": "6.4"}),
        },
        {
            "context_id": "ACS-PER-001",
            "domain": "acs",
            "category": "interpretation",
            "latitude": "wide",
            "text": "ACS 5-year estimates are period estimates, not point-in-time snapshots.",
            "triggers": ["period_estimate", "5-year"],
            "source": None,
        },
    ]

    for ctx in contexts:
        conn.execute(
            """INSERT INTO context (context_id, domain, category, latitude, context_text, triggers, source)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                ctx["context_id"],
                ctx["domain"],
                ctx["category"],
                ctx["latitude"],
                ctx["text"],
                json.dumps(ctx["triggers"]),
                ctx["source"],
            )
        )
        conn.execute(
            """INSERT INTO pack_contents (pack_id, context_id) VALUES ('acs', ?)""",
            (ctx["context_id"],)
        )

    # Add a thread relationship
    conn.execute(
        """INSERT INTO threads (from_context_id, to_context_id, edge_type)
           VALUES ('ACS-GEO-001', 'ACS-POP-001', 'relates_to')"""
    )

    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture
def retriever(test_pack_db):
    """Create a PragmaticsRetriever with test pack loaded."""
    loader = PackLoader(str(test_pack_db))
    loader.load_pack("acs")
    return PragmaticsRetriever(loader)


def test_guidance_by_topics_returns_matching_contexts(retriever):
    """Test that get_guidance_by_topics returns contexts matching the requested topics."""
    result = retriever.get_guidance_by_topics(topics=["small_area", "margin_of_error"])

    # Should return guidance for contexts matching either topic
    assert "guidance" in result
    assert len(result["guidance"]) >= 2

    # Check that ACS-GEO-001 (small_area) is present
    geo_found = any(g["context_id"] == "ACS-GEO-001" for g in result["guidance"])
    assert geo_found

    # Check that ACS-MOE-001 (margin_of_error) is present
    moe_found = any(g["context_id"] == "ACS-MOE-001" for g in result["guidance"])
    assert moe_found

    # Verify structure of guidance items
    first_item = result["guidance"][0]
    assert "context_id" in first_item
    assert "text" in first_item
    assert "latitude" in first_item
    assert "tags" in first_item


def test_guidance_by_topics_includes_thread_related(retriever):
    """Test that get_guidance_by_topics includes thread-related contexts."""
    result = retriever.get_guidance_by_topics(topics=["small_area"])

    # Should find ACS-GEO-001 directly
    assert any(g["context_id"] == "ACS-GEO-001" for g in result["guidance"])

    # Should also include related contexts via threads
    assert "related" in result
    # ACS-POP-001 is related to ACS-GEO-001 via thread
    if len(result["related"]) > 0:
        # Related contexts should have edge_type and depth
        assert "edge_type" in result["related"][0]
        assert "depth" in result["related"][0]


def test_guidance_by_topics_includes_sources(retriever):
    """Test that sources are tracked and returned."""
    result = retriever.get_guidance_by_topics(topics=["population_threshold"])

    assert "sources" in result
    # Should have at least one source from ACS-POP-001
    assert len(result["sources"]) >= 1
    assert any(s["document"] == "ACS Handbook" for s in result["sources"])


def test_guidance_by_parameters_acs1_triggers_population(retriever):
    """Test that ACS1 product triggers population threshold contexts."""
    result = retriever.get_guidance_by_parameters(
        product="acs1",
        geo_level="state",
        variables=["B01003_001E"],
        year=2022
    )

    # Should match ACS-POP-001 which has "1yr_acs" and "population_threshold" triggers
    assert "guidance" in result
    pop_found = any(
        g["context_id"] == "ACS-POP-001"
        for g in result["guidance"]
    )
    assert pop_found, "ACS1 product should trigger population threshold guidance"


def test_guidance_by_parameters_tract_triggers_small_area(retriever):
    """Test that tract geography triggers small area contexts."""
    result = retriever.get_guidance_by_parameters(
        product="acs5",
        geo_level="tract",
        variables=["B01003_001E"],
        year=2022
    )

    # Should match ACS-GEO-001 which has "small_area" and "tract" triggers
    assert "guidance" in result
    geo_found = any(
        g["context_id"] == "ACS-GEO-001"
        for g in result["guidance"]
    )
    assert geo_found, "Tract geography should trigger small area guidance"


def test_guidance_by_parameters_dollar_variables_trigger_inflation(retriever):
    """Test that income/dollar variables trigger inflation contexts."""
    result = retriever.get_guidance_by_parameters(
        product="acs5",
        geo_level="county",
        variables=["B19013_001E", "B25077_001E"],  # Income and housing value
        year=2022
    )

    # Should match ACS-DOL-001 which has "dollar_values" and "inflation" triggers
    assert "guidance" in result
    dollar_found = any(
        g["context_id"] == "ACS-DOL-001"
        for g in result["guidance"]
    )
    assert dollar_found, "Dollar variables should trigger inflation guidance"


def test_guidance_by_parameters_always_includes_moe(retriever):
    """Test that MOE/reliability guidance is always included."""
    result = retriever.get_guidance_by_parameters(
        product="acs5",
        geo_level="state",
        variables=["B01003_001E"],
        year=2022
    )

    # Should always include ACS-MOE-001 because "margin_of_error" is always added
    assert "guidance" in result
    moe_found = any(
        g["context_id"] == "ACS-MOE-001"
        for g in result["guidance"]
    )
    assert moe_found, "Every request should include MOE/reliability guidance"


def test_guidance_by_topics_domain_filter(retriever):
    """Test that domain filter works correctly."""
    result = retriever.get_guidance_by_topics(
        topics=["margin_of_error"],
        domain="acs"
    )

    # Should only return ACS domain contexts
    assert "guidance" in result
    for item in result["guidance"]:
        # All returned items should be from ACS pack
        assert item["context_id"].startswith("ACS-")


def test_guidance_by_topics_no_matches_returns_empty(retriever):
    """Test that non-matching topics return empty results gracefully."""
    result = retriever.get_guidance_by_topics(topics=["nonexistent_topic"])

    assert "guidance" in result
    assert "related" in result
    assert "sources" in result
    assert len(result["guidance"]) == 0
    assert len(result["related"]) == 0
    assert len(result["sources"]) == 0
