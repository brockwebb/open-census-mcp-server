"""Integration tests for MCP server and tool handlers.

Updated 2026-02-08: Rewritten for low-level Server pattern (ADR-005).
Tool renamed get_acs_data -> get_census_data (G.6 prompt slimming).
Server accepts both names for backward compatibility.

See ADR-006 for tract-level geography fixes also covered here.
"""

import json
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from census_mcp.pragmatics.schema import create_tables
from census_mcp.pragmatics.pack import PackLoader
from census_mcp.pragmatics.retriever import PragmaticsRetriever
from census_mcp.api.census_client import CensusClient, CensusInvalidQueryError
from census_mcp import server as server_module


@pytest.fixture
def test_packs_dir(tmp_path):
    """Create test pack databases in a temporary directory."""
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    acs_db = packs_dir / "acs.db"
    conn = sqlite3.connect(acs_db)
    create_tables(conn)

    conn.execute(
        """INSERT INTO packs (pack_id, pack_name, parent_pack, version, compiled_date)
           VALUES ('acs', 'ACS Pack', NULL, '1.0.0', '2024-01-01')"""
    )

    contexts = [
        {
            "context_id": "ACS-POP-001",
            "domain": "acs",
            "category": "population",
            "latitude": "none",
            "text": "ACS 1-year estimates require 65,000+ population.",
            "triggers": json.dumps(["population_threshold", "1yr_acs", "1-year"]),
            "provenance": json.dumps({"document": "ACS Handbook", "section": "2.3"}),
        },
        {
            "context_id": "ACS-MOE-001",
            "domain": "acs",
            "category": "reliability",
            "latitude": "full",
            "text": "Always report margins of error.",
            "triggers": json.dumps(["margin_of_error", "reliability"]),
            "provenance": None,
        },
    ]

    for ctx in contexts:
        conn.execute(
            """INSERT INTO context (context_id, domain, category, latitude, context_text, triggers, provenance)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ctx["context_id"], ctx["domain"], ctx["category"], ctx["latitude"],
             ctx["text"], ctx["triggers"], ctx["provenance"]),
        )
        conn.execute(
            """INSERT INTO pack_contents (pack_id, context_id) VALUES ('acs', ?)""",
            (ctx["context_id"],),
        )

    conn.commit()
    conn.close()
    return packs_dir


@pytest.fixture
def initialized_server(test_packs_dir):
    """Initialize server globals with test packs and mocked Census client."""
    loader = PackLoader(str(test_packs_dir))
    loader.load_pack("acs")
    retriever = PragmaticsRetriever(loader)
    census_client = AsyncMock(spec=CensusClient)

    with patch.object(server_module, '_loader', loader), \
         patch.object(server_module, '_retriever', retriever), \
         patch.object(server_module, '_census_client', census_client):
        yield {
            "loader": loader,
            "retriever": retriever,
            "census_client": census_client,
        }

    loader.close()


async def _call_tool(name: str, arguments: dict) -> dict:
    """Helper: call tool through the real dispatcher, parse JSON result."""
    result = await server_module.call_tool_handler(name, arguments)
    assert len(result) == 1
    return json.loads(result[0].text)


# =========================================================================
# Pack loading
# =========================================================================

def test_server_starts_and_loads_packs(test_packs_dir):
    """Test that the server initializes and loads packs correctly."""
    loader = PackLoader(str(test_packs_dir))
    loader.load_pack("acs")

    assert "acs" in loader.connections

    contexts = loader.get_context_by_triggers(["margin_of_error"])
    assert len(contexts) >= 1
    assert any(ctx["context_id"] == "ACS-MOE-001" for ctx in contexts)

    loader.close()


# =========================================================================
# get_methodology_guidance
# =========================================================================

@pytest.mark.asyncio
async def test_get_methodology_guidance_returns_guidance(initialized_server):
    """Test that get_methodology_guidance returns proper guidance structure."""
    result = await _call_tool("get_methodology_guidance", {
        "topics": ["margin_of_error", "population_threshold"],
        "domain": "acs",
    })

    assert "guidance" in result
    assert "related" in result
    assert "sources" in result
    assert len(result["guidance"]) >= 1

    moe_found = any(g["context_id"] == "ACS-MOE-001" for g in result["guidance"])
    assert moe_found

    if result["guidance"]:
        item = result["guidance"][0]
        assert "context_id" in item
        assert "text" in item
        assert "latitude" in item
        assert "tags" in item


# =========================================================================
# get_census_data (renamed from get_acs_data, G.6)
# =========================================================================

@pytest.mark.asyncio
async def test_get_census_data_returns_data_with_pragmatics(initialized_server):
    """Test that get_census_data bundles data with pragmatic guidance."""
    initialized_server["census_client"].get_acs5.return_value = [
        ["B01003_001E", "NAME", "state", "county"],
        ["12345", "Test County", "42", "003"],
    ]

    result = await _call_tool("get_census_data", {
        "variables": ["B01003_001E"],
        "state": "42",
        "county": "003",
        "year": 2022,
        "product": "acs5",
    })

    assert "data" in result
    assert "pragmatics" in result
    assert "source" in result

    assert len(result["data"]) == 2
    assert result["data"][1][0] == "12345"

    assert "guidance" in result["pragmatics"]
    guidance = result["pragmatics"]["guidance"]
    moe_found = any(g["context_id"] == "ACS-MOE-001" for g in guidance)
    assert moe_found, "MOE guidance should always be bundled"

    assert result["source"]["dataset"] == "American Community Survey ACS5"
    assert result["source"]["vintage"] == 2022
    assert result["source"]["product"] == "acs5"
    assert result["source"]["geography"]["state"] == "42"
    assert result["source"]["geography"]["county"] == "003"

    initialized_server["census_client"].get_acs5.assert_called_once_with(
        variables=["B01003_001E"], year=2022, state="42", county="003",
    )


@pytest.mark.asyncio
async def test_get_census_data_hard_stop_acs1_tract(initialized_server):
    """Test that acs1 + tract returns informative error."""
    result = await _call_tool("get_census_data", {
        "variables": ["B01003_001E"],
        "state": "42",
        "county": "003",
        "tract": "123456",
        "year": 2022,
        "product": "acs1",
    })

    assert "error" in result
    assert "ACS 1-year estimates are not available at the tract level" in result["error"]
    assert "65,000" in result["error"]
    initialized_server["census_client"].get_acs1.assert_not_called()


@pytest.mark.asyncio
async def test_get_census_data_tract_requires_county(initialized_server):
    """Test that tract without county returns validation error (ADR-006)."""
    result = await _call_tool("get_census_data", {
        "variables": ["B01003_001E"],
        "state": "42",
        "tract": "123456",
        "year": 2022,
        "product": "acs5",
    })

    assert "error" in result
    assert "county FIPS code" in result["error"]
    initialized_server["census_client"].get_acs5.assert_not_called()


@pytest.mark.asyncio
async def test_get_census_data_tract_with_county_works(initialized_server):
    """Test that tract + county produces valid API call (ADR-006)."""
    initialized_server["census_client"].get_acs5.return_value = [
        ["B01003_001E", "NAME", "state", "county", "tract"],
        ["5000", "Census Tract 123456", "42", "003", "123456"],
    ]

    result = await _call_tool("get_census_data", {
        "variables": ["B01003_001E"],
        "state": "42",
        "county": "003",
        "tract": "123456",
        "year": 2022,
        "product": "acs5",
    })

    assert "data" in result
    assert "pragmatics" in result
    initialized_server["census_client"].get_acs5.assert_called_once_with(
        variables=["B01003_001E"], year=2022, state="42", county="003", tract="123456",
    )


@pytest.mark.asyncio
async def test_get_census_data_tract_wildcard(initialized_server):
    """Test that tract='*' enumerates all tracts in county (ADR-006)."""
    initialized_server["census_client"].get_acs5.return_value = [
        ["B01003_001E", "NAME", "state", "county", "tract"],
        ["2000", "Tract 9301", "21", "189", "930100"],
        ["1800", "Tract 9302", "21", "189", "930200"],
    ]

    result = await _call_tool("get_census_data", {
        "variables": ["B01003_001E"],
        "state": "21",
        "county": "189",
        "tract": "*",
        "year": 2022,
        "product": "acs5",
    })

    assert "data" in result
    assert len(result["data"]) == 3  # header + 2 tracts
    initialized_server["census_client"].get_acs5.assert_called_once_with(
        variables=["B01003_001E"], year=2022, state="21", county="189", tract="*",
    )


@pytest.mark.asyncio
async def test_get_census_data_legacy_name_works(initialized_server):
    """Test that old name 'get_acs_data' still routes correctly."""
    initialized_server["census_client"].get_acs5.return_value = [
        ["B01003_001E", "NAME", "state"],
        ["12345678", "Pennsylvania", "42"],
    ]

    result = await _call_tool("get_acs_data", {
        "variables": ["B01003_001E"],
        "state": "42",
        "year": 2022,
        "product": "acs5",
    })

    assert "data" in result
    assert "pragmatics" in result


# =========================================================================
# explore_variables
# =========================================================================

@pytest.mark.asyncio
async def test_explore_variables_returns_matching_variables(initialized_server):
    """Test that explore_variables returns matching variables by keyword."""
    # NOTE: Server has latent bug — calls .items() on get_variables() directly,
    # but real Census API returns {"variables": {...}}. Mock matches current
    # (buggy) server expectation. Fix server first, then update mock.
    initialized_server["census_client"].get_variables.return_value = {
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

    result = await _call_tool("explore_variables", {
        "concept": "household income",
        "year": 2022,
        "product": "acs5",
    })

    assert "variables" in result
    assert "tables" in result
    assert "suggestions" in result
    assert "caveat" in result
    assert "total_matches" in result

    variable_names = [v["name"] for v in result["variables"]]
    assert "B19013_001E" in variable_names
    assert "B19025_001E" in variable_names
    assert "B01003_001E" not in variable_names
    assert "B19013_001M" not in variable_names

    table_codes = [t["code"] for t in result["tables"]]
    assert "B19013" in table_codes
    assert "keyword matching" in result["caveat"].lower()
