"""Census Bureau API client with async support and retry logic."""

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# Product-to-Dataset mapping
PRODUCT_TO_DATASET = {
    "acs5": "acs/acs5",
    "acs1": "acs/acs1",
    "acs5/profile": "acs/acs5/profile",
    "acs5/subject": "acs/acs5/subject",
    "acs1/profile": "acs/acs1/profile",
    "acs1/subject": "acs/acs1/subject",
    "sf1": "dec/sf1",
    "dhc": "dec/dhc",
    "pl": "dec/pl",
    "pep": "pep/population",
}


def resolve_dataset(product: str) -> str:
    """Resolve shorthand product code to Census API dataset path.

    Args:
        product: Shorthand product code (e.g., "acs5") or full dataset path

    Returns:
        Full dataset path (e.g., "acs/acs5")

    Examples:
        >>> resolve_dataset("acs5")
        "acs/acs5"
        >>> resolve_dataset("acs/acs5")  # passthrough if already full path
        "acs/acs5"
    """
    return PRODUCT_TO_DATASET.get(product, product)


# Exceptions
class CensusAPIError(Exception):
    """Base exception for Census API errors."""
    pass


class CensusRateLimitError(CensusAPIError):
    """Raised when rate limit is exceeded (429)."""
    pass


class CensusNotFoundError(CensusAPIError):
    """Raised when resource is not found (404) or results are empty."""
    pass


class CensusInvalidQueryError(CensusAPIError):
    """Raised when query parameters are invalid (400)."""
    pass


class CensusClient:
    """HTTP client for Census Bureau API.
    
    Supports ACS 5-year and 1-year datasets with automatic retry on transient failures.
    """
    
    BASE_URL = "https://api.census.gov/data"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    RETRY_BACKOFF = 2.0  # exponential backoff multiplier
    
    def __init__(self, api_key: str | None = None):
        """Initialize Census API client.
        
        Args:
            api_key: Census API key. If None, reads from CENSUS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("CENSUS_API_KEY")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _request(
        self,
        url: str,
        params: dict[str, Any],
        retry_count: int = 0
    ) -> dict:
        """Make HTTP request with retry logic.
        
        Args:
            url: Full URL to request
            params: Query parameters
            retry_count: Current retry attempt (internal)
            
        Returns:
            Parsed JSON response
            
        Raises:
            CensusAPIError: On API errors
            CensusRateLimitError: On rate limit exceeded
            CensusNotFoundError: On 404 or empty results
            CensusInvalidQueryError: On invalid query parameters
        """
        # Add API key if available
        if self.api_key:
            params["key"] = self.api_key
        
        logger.debug(f"Census API request: {url} with params {params}")
        
        try:
            response = await self.client.get(url, params=params)
            
            # Handle specific HTTP status codes
            if response.status_code == 429:
                if retry_count < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** retry_count)
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    return await self._request(url, params, retry_count + 1)
                else:
                    raise CensusRateLimitError("Rate limit exceeded after retries")
            
            elif response.status_code == 404:
                raise CensusNotFoundError(f"Resource not found: {url}")
            
            elif response.status_code == 400:
                raise CensusInvalidQueryError(f"Invalid query parameters: {response.text}")
            
            elif response.status_code in (500, 502, 503):
                if retry_count < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** retry_count)
                    logger.warning(f"Server error {response.status_code}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    return await self._request(url, params, retry_count + 1)
                else:
                    raise CensusAPIError(f"Server error {response.status_code} after retries")
            
            # Raise for other error status codes
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Check for empty results
            if not data or len(data) <= 1:  # API returns header row + data rows
                raise CensusNotFoundError("Empty result set")
            
            return data
            
        except httpx.HTTPError as e:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (self.RETRY_BACKOFF ** retry_count)
                logger.warning(f"HTTP error: {e}, retrying in {delay}s")
                await asyncio.sleep(delay)
                return await self._request(url, params, retry_count + 1)
            else:
                raise CensusAPIError(f"HTTP error after retries: {e}")
    
    async def get_acs5(
        self,
        year: int,
        variables: list[str],
        state: str,
        county: str | None = None,
        place: str | None = None,
        tract: str | None = None,
    ) -> dict:
        """Retrieve ACS 5-year data.
        
        Args:
            year: Data year (e.g., 2022)
            variables: List of variable codes (e.g., ["B01001_001E", "NAME"])
            state: State FIPS code (e.g., "06" for California)
            county: County FIPS code (optional, e.g., "001")
            place: Place FIPS code (optional)
            tract: Tract code (optional)
            
        Returns:
            Parsed JSON response from Census API
            
        Raises:
            CensusAPIError: On API errors
        """
        url = f"{self.BASE_URL}/{year}/acs/acs5"
        
        # Build geography specification
        # Priority: tract > place > county > state
        # Census API requires: for=<geo_level>:<code>&in=<parent_levels>
        # Tract requires both state and county in 'in' clause (ADR-006)
        if tract:
            in_geo = f"state:{state}"
            if county:
                in_geo += f"+county:{county}"
            params = {
                "get": ",".join(variables),
                "for": f"tract:{tract}",
                "in": in_geo,
            }
        elif place:
            params = {
                "get": ",".join(variables),
                "for": f"place:{place}",
                "in": f"state:{state}",
            }
        elif county:
            params = {
                "get": ",".join(variables),
                "for": f"county:{county}",
                "in": f"state:{state}",
            }
        else:
            params = {
                "get": ",".join(variables),
                "for": f"state:{state}",
            }
        
        return await self._request(url, params)
    
    async def get_acs1(
        self,
        year: int,
        variables: list[str],
        state: str,
        county: str | None = None,
    ) -> dict:
        """Retrieve ACS 1-year data.
        
        Args:
            year: Data year (e.g., 2022)
            variables: List of variable codes (e.g., ["B01001_001E", "NAME"])
            state: State FIPS code (e.g., "06" for California)
            county: County FIPS code (optional, e.g., "001")
            
        Returns:
            Parsed JSON response from Census API
            
        Raises:
            CensusAPIError: On API errors
        """
        url = f"{self.BASE_URL}/{year}/acs/acs1"
        
        # Build geography specification
        for_geo = f"state:{state}"
        if county:
            for_geo = f"county:{county}"
        
        params = {
            "get": ",".join(variables),
            "for": for_geo,
        }
        
        # Add state context if needed
        if county:
            params["in"] = f"state:{state}"
        
        return await self._request(url, params)
    
    async def get_variables(
        self,
        dataset: str,
        year: int,
    ) -> dict:
        """Get variable metadata for a dataset.

        Args:
            dataset: Dataset name (e.g., "acs5" or "acs/acs5")
            year: Data year

        Returns:
            Variable metadata dictionary

        Raises:
            CensusAPIError: On API errors
        """
        # Resolve shorthand product codes to full dataset paths
        dataset_path = resolve_dataset(dataset)
        url = f"{self.BASE_URL}/{year}/{dataset_path}/variables.json"
        
        # Variable endpoint doesn't use query params the same way
        response = await self.client.get(url)
        
        if response.status_code == 404:
            raise CensusNotFoundError(f"Variables not found for {dataset}/{year}")
        
        response.raise_for_status()
        return response.json()
