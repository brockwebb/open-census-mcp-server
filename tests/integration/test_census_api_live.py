"""Integration tests for Census API client against live API.

These tests require a valid CENSUS_API_KEY environment variable.
Run with: pytest tests/integration/test_census_api_live.py -v
"""

import os

import pytest

from census_mcp.api.census_client import CensusClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_acs5_california_population():
    """Test live API retrieval of California total population.
    
    This test requires CENSUS_API_KEY to be set in environment.
    """
    api_key = os.getenv("CENSUS_API_KEY")
    if not api_key:
        pytest.skip("CENSUS_API_KEY not set, skipping live API test")
    
    async with CensusClient(api_key=api_key) as client:
        result = await client.get_acs5(
            year=2022,
            variables=["NAME", "B01001_001E"],
            state="06"  # California
        )
        
        # Verify response structure
        assert isinstance(result, list)
        assert len(result) >= 2  # Header row + at least 1 data row
        
        # Verify header
        header = result[0]
        assert "NAME" in header
        assert "B01001_001E" in header
        assert "state" in header
        
        # Verify data row
        data_row = result[1]
        assert len(data_row) == len(header)
        
        # Verify California is in the response
        name_idx = header.index("NAME")
        assert "California" in data_row[name_idx]
        
        # Verify population value is present and numeric
        pop_idx = header.index("B01001_001E")
        population = data_row[pop_idx]
        assert population is not None
        # Population should be a large number (California has ~39M people)
        assert int(population) > 30_000_000
        
        print(f"✓ Successfully retrieved California population: {population}")
