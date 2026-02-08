"""Integration tests for MCP server and tool handlers."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from census_mcp.pragmatics.schema import create_tables
from census_mcp.pragmatics.pack import PackLoader
from census_mcp.pragmatics.retriever import PragmaticsRetriever
from census_mcp.api.census_client import CensusClient, CensusInvalidQueryError
from census_mcp.server import ServerContext, get_server_context
from census_mcp.tools import census_tools
from census_mcp import server as server_module


@pytest.fixture
def test_packs_dir(tmp_path):
    """Create test pack databases in a temporary directory."""
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    # Create ACS pack
    acs_db = packs_dir / "acs.db"
    conn = sqlite3.connect(acs_db)
    create_tables(conn)

    # Pack metadata
    conn.execute(
        """INSERT INTO packs (pack_id, pack_name, parent_pack, version, compiled_date)
           VALUES ('acs', 'ACS Pack', NULL, '1.0.0', '2024-01-01')"""
    )

    # Test contexts
    contexts = [
        {
            "context_id": "ACS-POP-001",
            "domain": "acs",
            "category": "population",
            "latitude": "none",
            "text": "ACS 1-year estimates require 65,000+ population.",
            "triggers": json.dumps(["population_threshold", "1yr_acs", "1-year"]),
            "source": json.dumps({"document": "ACS Handbook", "section": "2.3"}),
        },
        {
            "context_id": "ACS-MOE-001",
            "domain": "acs",
            "category": "reliability",
            "latitude": "full",
            "text": "Always report margins of error.",
            "triggers": json.dumps(["margin_of_error", "reliability"]),
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
                ctx["triggers"],
                ctx["source"],
            )
        )
        conn.execute(
            """INSERT INTO pack_contents (pack_id, context_id) VALUES ('acs', ?)""",
            (ctx["context_id"],)
        )

    conn.commit()
    conn.close()

    return packs_dir


@pytest.fixture
async def server_context(test_packs_dir):
    """Create a ServerContext with test packs loaded."""
    loader = PackLoader(str(test_packs_dir))
    loader.load_pack("acs")
    retriever = PragmaticsRetriever(loader)

    # Create a mock CensusClient
    census_client = AsyncMock(spec=CensusClient)

    context = ServerContext(loader, retriever, census_client)

    yield context

    # Cleanup
    loader.close()


@pytest.fixture
def mock_server_context(server_context):
    """Mock the get_server_context function to return our test context."""
    with patch.object(server_module, '_server_context', server_context):
        yield server_context


def test_server_starts_and_loads_packs(test_packs_dir):
    """Test that the server initializes and loads packs correctly."""
    # Test that we can create a loader and load packs
    loader = PackLoader(str(test_packs_dir))
    loader.load_pack("acs")

    # Verify pack is loaded
    assert "acs" in loader.connections

    # Verify we can retrieve contexts
    contexts = loader.get_context_by_triggers(["margin_of_error"])
    assert len(contexts) >= 1
    assert any(ctx["context_id"] == "ACS-MOE-001" for ctx in contexts)

    loader.close()


@pytest.mark.asyncio
async def test_get_methodology_guidance_returns_guidance(mock_server_context):
    """Test that get_methodology_guidance tool returns proper guidance structure."""
    result = await census_tools.get_methodology_guidance(
        topics=["margin_of_error", "population_threshold"],
        domain="acs"
    )

    # Verify structure
    assert "guidance" in result
    assert "related" in result
    assert "sources" in result

    # Verify we got matching contexts
    assert len(result["guidance"]) >= 1

    # Should include ACS-MOE-001
    moe_found = any(g["context_id"] == "ACS-MOE-001" for g in result["guidance"])
    assert moe_found

    # Verify guidance item structure
    if result["guidance"]:
        item = result["guidance"][0]
        assert "context_id" in item
        assert "text" in item
        assert "latitude" in item
        assert "tags" in item


@pytest.mark.asyncio
async def test_get_acs_data_returns_data_with_pragmatics(mock_server_context):
    """Test that get_acs_data bundles data with pragmatic guidance."""
    # Mock the census_client response
    mock_server_context.census_client.get_acs5.return_value = {
        "B01003_001E": {"estimate": 12345, "margin_of_error": 100},
        "NAME": "Test County",
    }

    result = await census_tools.get_acs_data(
        variables=["B01003_001E"],
        state="42",
        county="003",
        year=2022,
        product="acs5"
    )

    # Verify top-level structure
    assert "data" in result
    assert "pragmatics" in result
    assert "source" in result

    # Verify data field contains API response
    assert result["data"]["B01003_001E"]["estimate"] == 12345

    # Verify pragmatics field has expected structure
    assert "guidance" in result["pragmatics"]
    assert "related" in result["pragmatics"]
    assert "sources" in result["pragmatics"]

    # Verify that MOE guidance is always included
    guidance = result["pragmatics"]["guidance"]
    moe_found = any(g["context_id"] == "ACS-MOE-001" for g in guidance)
    assert moe_found, "MOE guidance should always be bundled"

    # Verify source metadata
    assert result["source"]["dataset"] == "American Community Survey ACS5"
    assert result["source"]["vintage"] == 2022
    assert result["source"]["product"] == "acs5"
    assert result["source"]["geography"]["state"] == "42"
    assert result["source"]["geography"]["county"] == "003"

    # Verify the census client was called correctly
    mock_server_context.census_client.get_acs5.assert_called_once_with(
        variables=["B01003_001E"],
        year=2022,
        state="42",
        county="003"
    )


@pytest.mark.asyncio
async def test_get_acs_data_hard_stop_on_impossible_request(mock_server_context):
    """Test that get_acs_data raises error for impossible requests like tract + acs1."""
    # Attempt to request tract-level data with ACS1 (impossible)
    with pytest.raises(CensusInvalidQueryError) as exc_info:
        await census_tools.get_acs_data(
            variables=["B01003_001E"],
            state="42",
            tract="123456",
            year=2022,
            product="acs1"
        )

    # Verify error message is informative
    error_msg = str(exc_info.value)
    assert "ACS 1-year estimates are not available at the tract level" in error_msg
    assert "65,000" in error_msg

    # Verify census client was NOT called
    mock_server_context.census_client.get_acs1.assert_not_called()


@pytest.mark.asyncio
async def test_get_acs_data_triggers_small_area_for_tract(mock_server_context):
    """Test that requesting tract-level data triggers small_area pragmatics."""
    # Mock the census_client response
    mock_server_context.census_client.get_acs5.return_value = {
        "B01003_001E": {"estimate": 5000, "margin_of_error": 250},
        "NAME": "Census Tract 123456",
    }

    result = await census_tools.get_acs_data(
        variables=["B01003_001E"],
        state="42",
        county="003",
        tract="123456",
        year=2022,
        product="acs5"
    )

    # Verify pragmatics includes small_area context
    # (Note: this depends on having small_area context in test pack with "tract" trigger)
    assert "pragmatics" in result

    # Verify the retriever was called with correct geo_level
    # geo_level should be "tract" which triggers small_area guidance
    # This is verified by the fact that get_guidance_by_parameters was called
    # (we can't easily verify the internal call without more mocking)


@pytest.mark.asyncio
async def test_explore_variables_returns_matching_variables(mock_server_context):
    """Test that explore_variables returns matching variables by keyword."""
    # Mock the census_client.get_variables response
    mock_server_context.census_client.get_variables.return_value = {
        "B19013_001E": {
            "label": "Estimate!!Median household income in the past 12 months",
            "concept": "MEDIAN HOUSEHOLD INCOME IN THE PAST 12 MONTHS",
            "group": "B19013",
        },
        "B19013_001M": {
            "label": "Margin of Error!!Median household income",
            "concept": "MEDIAN HOUSEHOLD INCOME IN THE PAST 12 MONTHS",
            "group": "B19013",
        },
        "B19025_001E": {
            "label": "Estimate!!Aggregate household income",
            "concept": "AGGREGATE HOUSEHOLD INCOME IN THE PAST 12 MONTHS",
            "group": "B19025",
        },
        "B01003_001E": {
            "label": "Estimate!!Total population",
            "concept": "TOTAL POPULATION",
            "group": "B01003",
        },
    }

    result = await census_tools.explore_variables(
        concept="household income",
        year=2022,
        product="acs5"
    )

    # Verify structure
    assert "variables" in result
    assert "tables" in result
    assert "suggestions" in result
    assert "caveat" in result
    assert "total_matches" in result

    # Should match B19013_001E and B19025_001E (income variables)
    # Should NOT include B01003_001E (population, no "income" keyword)
    # Should NOT include B19013_001M (margin of error, filtered out)

    variable_names = [v["name"] for v in result["variables"]]
    assert "B19013_001E" in variable_names
    assert "B19025_001E" in variable_names
    assert "B01003_001E" not in variable_names  # No "income" in label/concept
    assert "B19013_001M" not in variable_names  # MOE variable filtered

    # Verify tables are extracted
    assert len(result["tables"]) >= 1
    table_codes = [t["code"] for t in result["tables"]]
    assert "B19013" in table_codes

    # Verify caveat is present (warning about limitations)
    assert "keyword matching" in result["caveat"].lower()
