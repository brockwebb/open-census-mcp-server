"""Unit tests for Census API client."""

import os
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from census_mcp.api.census_client import (
    CensusClient,
    CensusAPIError,
    CensusRateLimitError,
    CensusNotFoundError,
    CensusInvalidQueryError,
)


@pytest.fixture
def mock_acs5_response():
    """Mock successful ACS5 response."""
    return [
        ["NAME", "B01001_001E", "state"],
        ["California", "39538223", "06"]
    ]


@pytest.fixture
def mock_acs1_response():
    """Mock successful ACS1 response."""
    return [
        ["NAME", "B01001_001E", "state"],
        ["California", "39512223", "06"]
    ]


@pytest.fixture
def mock_variables_response():
    """Mock variable metadata response."""
    return {
        "variables": {
            "B01001_001E": {
                "label": "Estimate!!Total:",
                "concept": "SEX BY AGE",
                "predicateType": "int"
            }
        }
    }


@pytest.mark.asyncio
async def test_successful_acs5_retrieval(httpx_mock: HTTPXMock, mock_acs5_response):
    """Test successful ACS5 data retrieval."""
    httpx_mock.add_response(
        url="https://api.census.gov/data/2022/acs/acs5?get=NAME%2CB01001_001E&for=state%3A06&key=test_key",
        json=mock_acs5_response
    )

    async with CensusClient(api_key="test_key") as client:
        result = await client.get_acs5(
            year=2022,
            variables=["NAME", "B01001_001E"],
            state="06"
        )

        assert result == mock_acs5_response
        assert len(result) == 2  # Header + 1 data row


@pytest.mark.asyncio
async def test_successful_acs1_retrieval(httpx_mock: HTTPXMock, mock_acs1_response):
    """Test successful ACS1 data retrieval."""
    httpx_mock.add_response(
        url="https://api.census.gov/data/2022/acs/acs1?get=NAME%2CB01001_001E&for=state%3A06&key=test_key",
        json=mock_acs1_response
    )

    async with CensusClient(api_key="test_key") as client:
        result = await client.get_acs1(
            year=2022,
            variables=["NAME", "B01001_001E"],
            state="06"
        )

        assert result == mock_acs1_response


@pytest.mark.asyncio
async def test_acs5_with_county(httpx_mock: HTTPXMock, mock_acs5_response):
    """Test ACS5 retrieval with county parameter."""
    httpx_mock.add_response(
        url="https://api.census.gov/data/2022/acs/acs5?get=NAME%2CB01001_001E&for=county%3A001&in=state%3A06&key=test_key",
        json=mock_acs5_response
    )
    
    async with CensusClient(api_key="test_key") as client:
        result = await client.get_acs5(
            year=2022,
            variables=["NAME", "B01001_001E"],
            state="06",
            county="001"
        )
        
        assert result == mock_acs5_response


@pytest.mark.asyncio
async def test_api_key_from_env(httpx_mock: HTTPXMock, mock_acs5_response, monkeypatch):
    """Test API key read from environment variable."""
    monkeypatch.setenv("CENSUS_API_KEY", "env_test_key")
    
    httpx_mock.add_response(
        url="https://api.census.gov/data/2022/acs/acs5?get=NAME&for=state%3A06&key=env_test_key",
        json=mock_acs5_response
    )
    
    async with CensusClient() as client:
        assert client.api_key == "env_test_key"
        result = await client.get_acs5(
            year=2022,
            variables=["NAME"],
            state="06"
        )
        assert result == mock_acs5_response


@pytest.mark.asyncio
async def test_api_key_from_constructor(httpx_mock: HTTPXMock, mock_acs5_response):
    """Test API key from constructor overrides environment."""
    httpx_mock.add_response(
        url="https://api.census.gov/data/2022/acs/acs5?get=NAME&for=state%3A06&key=constructor_key",
        json=mock_acs5_response
    )
    
    async with CensusClient(api_key="constructor_key") as client:
        assert client.api_key == "constructor_key"
        result = await client.get_acs5(
            year=2022,
            variables=["NAME"],
            state="06"
        )
        assert result == mock_acs5_response


@pytest.mark.asyncio
async def test_rate_limit_retry(httpx_mock: HTTPXMock, mock_acs5_response):
    """Test retry behavior on rate limit (429)."""
    # First request returns 429, second succeeds
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(json=mock_acs5_response)
    
    async with CensusClient(api_key="test_key") as client:
        result = await client.get_acs5(
            year=2022,
            variables=["NAME"],
            state="06"
        )
        assert result == mock_acs5_response


@pytest.mark.asyncio
async def test_rate_limit_exhausted(httpx_mock: HTTPXMock):
    """Test exception when rate limit retries exhausted."""
    # All requests return 429
    for _ in range(4):  # Initial + 3 retries
        httpx_mock.add_response(status_code=429)
    
    async with CensusClient(api_key="test_key") as client:
        with pytest.raises(CensusRateLimitError, match="Rate limit exceeded"):
            await client.get_acs5(
                year=2022,
                variables=["NAME"],
                state="06"
            )


@pytest.mark.asyncio
async def test_not_found_error(httpx_mock: HTTPXMock):
    """Test 404 raises CensusNotFoundError."""
    httpx_mock.add_response(status_code=404)
    
    async with CensusClient(api_key="test_key") as client:
        with pytest.raises(CensusNotFoundError, match="Resource not found"):
            await client.get_acs5(
                year=2022,
                variables=["NAME"],
                state="06"
            )


@pytest.mark.asyncio
async def test_invalid_query_error(httpx_mock: HTTPXMock):
    """Test 400 raises CensusInvalidQueryError."""
    httpx_mock.add_response(status_code=400, text="Invalid parameter")
    
    async with CensusClient(api_key="test_key") as client:
        with pytest.raises(CensusInvalidQueryError, match="Invalid query parameters"):
            await client.get_acs5(
                year=2022,
                variables=["INVALID_VAR"],
                state="06"
            )


@pytest.mark.asyncio
async def test_empty_result_error(httpx_mock: HTTPXMock):
    """Test empty results raise CensusNotFoundError."""
    httpx_mock.add_response(json=[["NAME"]])  # Only header, no data
    
    async with CensusClient(api_key="test_key") as client:
        with pytest.raises(CensusNotFoundError, match="Empty result set"):
            await client.get_acs5(
                year=2022,
                variables=["NAME"],
                state="99"  # Invalid state
            )


@pytest.mark.asyncio
async def test_server_error_retry(httpx_mock: HTTPXMock, mock_acs5_response):
    """Test retry on server errors (500, 502, 503)."""
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(json=mock_acs5_response)
    
    async with CensusClient(api_key="test_key") as client:
        result = await client.get_acs5(
            year=2022,
            variables=["NAME"],
            state="06"
        )
        assert result == mock_acs5_response


@pytest.mark.asyncio
async def test_get_variables(httpx_mock: HTTPXMock, mock_variables_response):
    """Test variable metadata retrieval."""
    httpx_mock.add_response(
        url="https://api.census.gov/data/2022/acs/acs5/variables.json",
        json=mock_variables_response
    )
    
    async with CensusClient(api_key="test_key") as client:
        result = await client.get_variables("acs/acs5", 2022)
        assert result == mock_variables_response
        assert "variables" in result


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager properly closes client."""
    async with CensusClient(api_key="test_key") as client:
        assert client.client is not None
    
    # Client should be closed after context exit
    # httpx client sets _state to CLOSED
    assert client.client.is_closed
