"""Census MCP tool handlers.

Three tools per docs/design/agent_prompt.md:
1. get_methodology_guidance - Query pragmatics knowledge base by topics
2. get_acs_data - Retrieve ACS data with bundled pragmatics
3. explore_variables - Discover Census variables by concept
"""

from typing import Any

from census_mcp.server import mcp, get_server_context
from census_mcp.api.census_client import (
    CensusAPIError,
    CensusInvalidQueryError,
)


@mcp.tool()
async def get_methodology_guidance(
    topics: list[str],
    domain: str | None = None,
) -> dict[str, Any]:
    """Query statistical methodology guidance by topic.

    Call this FIRST for every query to ground your orientation.

    Topics include:
    - small_area: Population thresholds, estimate availability
    - temporal_comparison: Comparing across years, overlapping periods
    - margin_of_error: Reliability, coefficient of variation, precision
    - dollar_values: Inflation adjustment for income/rent/value comparisons
    - geography: Boundary changes, jurisdiction types, PUMA/tract availability
    - period_estimate: ACS period vs point-in-time interpretation
    - suppression: Data availability and reliability-based suppression
    - comparison: Rules for comparing estimates across products or geographies
    - population_threshold: Minimum population for data product availability

    When in doubt, request more topics rather than fewer.

    Args:
        topics: List of topic tags e.g. ["small_area", "margin_of_error"]
        domain: Optional domain filter: "acs", "census", or "general"

    Returns:
        {
            "guidance": [{context_id, text, latitude, source, tags}, ...],
            "related": [{context_id, text, edge_type, depth}, ...],
            "sources": [{document, section}, ...]
        }
    """
    # Access server context
    ctx = get_server_context()
    retriever = ctx.retriever

    # Call retriever
    result = retriever.get_guidance_by_topics(topics, domain)

    return result


@mcp.tool()
async def get_acs_data(
    variables: list[str],
    state: str,
    county: str | None = None,
    place: str | None = None,
    tract: str | None = None,
    year: int = 2022,
    product: str = "acs5",
) -> dict[str, Any]:
    """Retrieve ACS data with statistical methodology guidance.

    Returns estimates, margins of error, and pragmatic context about
    fitness-for-use, reliability, and interpretation caveats.

    Use this after grounding with get_methodology_guidance.
    Always review the pragmatics field before interpreting results.

    Args:
        variables: Census variable codes e.g. ["B01003_001E", "B19013_001E"]
        state: State FIPS code e.g. "42"
        county: County FIPS code (optional)
        place: Place FIPS code (optional)
        tract: Tract code (optional)
        year: Data year (default 2022)
        product: "acs5" or "acs1" (default "acs5")

    Returns:
        {
            "data": {estimates, MOEs, geography labels},
            "pragmatics": {guidance, related, sources},
            "source": {dataset, vintage, api_url}
        }

    Raises:
        CensusInvalidQueryError: For impossible requests (e.g., tract with acs1)
    """
    # Access server context
    ctx = get_server_context()
    retriever = ctx.retriever
    census_client = ctx.census_client

    # Validation: Hard stops on impossible requests
    if product == "acs1" and tract is not None:
        raise CensusInvalidQueryError(
            "ACS 1-year estimates are not available at the tract level. "
            "Tract-level data requires ACS 5-year estimates (product='acs5'). "
            "Per ACS methodology, 1-year estimates are only published for geographies "
            "with populations of 65,000 or more."
        )

    if product == "acs1" and county is not None:
        # Check if it's a small county (this is a simplification - ideally we'd check population)
        # For now, just warn but allow
        pass

    # Determine geography level for geo parameter
    geo_params = {"state": state}
    geo_level = "state"

    if tract is not None:
        geo_params["tract"] = tract
        if county is not None:
            geo_params["county"] = county
        geo_level = "tract"
    elif place is not None:
        geo_params["place"] = place
        geo_level = "place"
    elif county is not None:
        geo_params["county"] = county
        geo_level = "county"

    # Fetch data from Census API
    try:
        if product == "acs5":
            data_response = await census_client.get_acs5(
                variables=variables,
                year=year,
                **geo_params
            )
        elif product == "acs1":
            data_response = await census_client.get_acs1(
                variables=variables,
                year=year,
                **geo_params
            )
        else:
            raise CensusInvalidQueryError(
                f"Invalid product '{product}'. Must be 'acs5' or 'acs1'."
            )
    except CensusAPIError as e:
        # Re-raise with context
        raise CensusAPIError(
            f"Census API error while fetching {product} data for {year}: {str(e)}"
        ) from e

    # Bundle pragmatics based on request parameters
    pragmatics = retriever.get_guidance_by_parameters(
        product=product,
        geo_level=geo_level,
        variables=variables,
        year=year
    )

    # Build source metadata for citation
    source = {
        "dataset": f"American Community Survey {product.upper()}",
        "vintage": year,
        "product": product,
        "api_url": f"https://api.census.gov/data/{year}/acs/{product}",
        "geography": geo_params,
    }

    return {
        "data": data_response,
        "pragmatics": pragmatics,
        "source": source,
    }


@mcp.tool()
async def explore_variables(
    concept: str,
    year: int = 2022,
    product: str = "acs5",
) -> dict[str, Any]:
    """Discover Census variables by concept or keyword.

    Use when the user describes what they want in plain language
    and you need to identify the correct variable codes.

    Returns matching variables with descriptions and table context.

    NOTE: Variable search is a known weak spot (see v1/v2 lessons). This
    implementation provides basic keyword matching. Results may be incomplete
    or require manual filtering.

    Args:
        concept: Natural language description e.g. "household income", "poverty rate"
        year: Data year (default 2022)
        product: "acs5" or "acs1" (default "acs5")

    Returns:
        {
            "variables": [
                {
                    "name": "B19013_001E",
                    "label": "Estimate!!Median household income in the past 12 months",
                    "concept": "MEDIAN HOUSEHOLD INCOME IN THE PAST 12 MONTHS",
                    "group": "B19013"
                },
                ...
            ],
            "tables": [
                {
                    "code": "B19013",
                    "description": "MEDIAN HOUSEHOLD INCOME IN THE PAST 12 MONTHS"
                },
                ...
            ],
            "suggestions": [...],
            "caveat": "Variable search is limited. Results filtered by keyword matching."
        }
    """
    # Access server context
    ctx = get_server_context()
    census_client = ctx.census_client

    # Fetch all variables for the product/year
    try:
        all_variables = await census_client.get_variables(year=year, product=product)
    except CensusAPIError as e:
        raise CensusAPIError(
            f"Failed to fetch variables for {product} {year}: {str(e)}"
        ) from e

    # Basic keyword matching (case-insensitive)
    concept_lower = concept.lower()
    keywords = concept_lower.split()

    matching_vars = []
    tables_seen = set()

    for var_name, var_info in all_variables.items():
        # Skip margin of error and annotation variables for initial search
        if var_name.endswith(("M", "MA", "EA")):
            continue

        # Check if any keyword matches in label or concept
        label = var_info.get("label", "").lower()
        var_concept = var_info.get("concept", "").lower()

        if any(kw in label or kw in var_concept for kw in keywords):
            matching_vars.append({
                "name": var_name,
                "label": var_info.get("label", ""),
                "concept": var_info.get("concept", ""),
                "group": var_info.get("group", ""),
            })

            # Track unique tables
            if "group" in var_info:
                tables_seen.add((
                    var_info["group"],
                    var_info.get("concept", "")
                ))

    # Build tables list
    tables = [
        {"code": code, "description": desc}
        for code, desc in sorted(tables_seen)
    ]

    # Generate suggestions (related tables)
    suggestions = []
    if "income" in concept_lower:
        suggestions.append("Consider also: B19001 (Household Income in bins), B19025 (Aggregate household income)")
    if "poverty" in concept_lower:
        suggestions.append("Consider also: B17001 (Poverty status by age), B17020 (Poverty status by age by household type)")

    return {
        "variables": matching_vars[:50],  # Limit to top 50 to avoid overwhelming response
        "tables": tables,
        "suggestions": suggestions,
        "caveat": "Variable search is limited to keyword matching. Results may be incomplete. "
                  "Consider reviewing the full table (group) for additional related variables.",
        "total_matches": len(matching_vars),
    }
