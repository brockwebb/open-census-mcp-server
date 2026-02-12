"""Census MCP Server - Statistical consultation interface.

This server provides tools for querying U.S. Census data and statistical
methodology guidance. It implements the Model Context Protocol (MCP) to enable
LLM agents to access Census data with appropriate pragmatic context.

Architecture per ADR-003/004:
- MCP validates and retrieves data (no LLM reasoning)
- Caller (LLM agent) performs routing and interpretation
- Pragmatics bundled with every data response

Note (ADR-005): Uses low-level mcp.server.Server + stdio_server pattern
instead of FastMCP. FastMCP (mcp 1.9.4) handshake succeeds but tools
fail to surface in Claude Desktop. The low-level pattern is proven to
work (used by all Arnold MCPs). See docs/architecture/decisions/adr-005.md.
"""

import os
import json
import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from census_mcp.pragmatics.pack import PackLoader
from census_mcp.pragmatics.retriever import PragmaticsRetriever
from census_mcp.api.census_client import (
    CensusClient,
    CensusAPIError,
    CensusInvalidQueryError,
)
from census_mcp.config import (
    DEFAULT_YEAR,
    DEFAULT_PRODUCT,
    SUPPORTED_PRODUCTS,
    PACKS_DIR,
    LOG_LEVEL,
    LOG_FILE,
    SERVER_NAME,
    CENSUS_API_KEY,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Initialize server
server = Server(SERVER_NAME)

# Lazy-initialized context
_loader: PackLoader | None = None
_retriever: PragmaticsRetriever | None = None
_census_client: CensusClient | None = None


def _ensure_initialized():
    """Initialize server dependencies on first use."""
    global _loader, _retriever, _census_client
    if _loader is None:
        _loader = PackLoader(PACKS_DIR)
        _loader.load_pack("acs")
        _retriever = PragmaticsRetriever(_loader)
        _census_client = CensusClient()
        logger.info(f"Census MCP initialized. Packs loaded from {PACKS_DIR}")


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

@server.list_tools()
async def list_tools_handler() -> list[types.Tool]:
    """List available Census tools."""
    return [
        types.Tool(
            name="get_methodology_guidance",
            description="""Query statistical methodology guidance by topic.

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

When in doubt, request more topics rather than fewer.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": 'List of topic tags e.g. ["small_area", "margin_of_error"]',
                    },
                    "domain": {
                        "type": "string",
                        "description": 'Optional domain filter: "acs", "census", or "general"',
                    },
                },
                "required": ["topics"],
            },
        ),
        types.Tool(
            name="get_census_data",
            description="""Retrieve Census data with statistical methodology guidance.

Returns estimates, margins of error, and pragmatic context about
fitness-for-use, reliability, and interpretation caveats.

Use this after grounding with get_methodology_guidance.
Always review the pragmatics field before interpreting results.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": 'Census variable codes e.g. ["B01003_001E", "B19013_001E"]',
                    },
                    "state": {
                        "type": "string",
                        "description": 'State FIPS code e.g. "42"',
                    },
                    "county": {
                        "type": "string",
                        "description": "County FIPS code (optional)",
                    },
                    "place": {
                        "type": "string",
                        "description": "Place FIPS code (optional)",
                    },
                    "tract": {
                        "type": "string",
                        "description": "Tract code (optional). REQUIRES county to also be specified. "
                                        "Use '*' to enumerate all tracts in a county.",
                    },
                    "year": {
                        "type": "integer",
                        "description": f"Data year (default {DEFAULT_YEAR})",
                        "default": DEFAULT_YEAR,
                    },
                    "product": {
                        "type": "string",
                        "description": f'"{DEFAULT_PRODUCT}" or "acs1" (default "{DEFAULT_PRODUCT}")',
                        "default": DEFAULT_PRODUCT,
                    },
                },
                "required": ["variables", "state"],
            },
        ),
        types.Tool(
            name="explore_variables",
            description="""Discover Census variables by concept or keyword.

Use when the user describes what they want in plain language
and you need to identify the correct variable codes.

Returns matching variables with descriptions and table context.

NOTE: Variable search is a known weak spot. This provides basic
keyword matching. Results may be incomplete.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {
                        "type": "string",
                        "description": 'Natural language description e.g. "household income", "poverty rate"',
                    },
                    "year": {
                        "type": "integer",
                        "description": f"Data year (default {DEFAULT_YEAR})",
                        "default": DEFAULT_YEAR,
                    },
                    "product": {
                        "type": "string",
                        "description": f'"{DEFAULT_PRODUCT}" or "acs1" (default "{DEFAULT_PRODUCT}")',
                        "default": DEFAULT_PRODUCT,
                    },
                },
                "required": ["concept"],
            },
        ),
    ]


# =============================================================================
# TOOL DISPATCH
# =============================================================================

@server.call_tool()
async def call_tool_handler(name: str, arguments: dict) -> list[types.TextContent]:
    """Dispatch tool calls."""
    _ensure_initialized()

    # -----------------------------------------------------------------
    # get_methodology_guidance
    # -----------------------------------------------------------------
    if name == "get_methodology_guidance":
        try:
            topics = arguments["topics"]
            domain = arguments.get("domain")
            result = _retriever.get_guidance_by_topics(topics, domain)
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]
        except Exception as e:
            logger.error(f"Error in get_methodology_guidance: {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # -----------------------------------------------------------------
    # get_census_data (accepts legacy name get_acs_data)
    # -----------------------------------------------------------------
    elif name in ("get_census_data", "get_acs_data"):  # accept legacy name
        try:
            variables = arguments["variables"]
            state = arguments["state"]
            county = arguments.get("county")
            place = arguments.get("place")
            tract = arguments.get("tract")
            year = arguments.get("year", DEFAULT_YEAR)
            product = arguments.get("product", DEFAULT_PRODUCT)

            # Validation: hard stops on impossible requests
            if product == "acs1" and tract is not None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "ACS 1-year estimates are not available at the tract level. "
                                 "Tract-level data requires ACS 5-year estimates (product='acs5'). "
                                 "1-year estimates are only published for geographies with "
                                 "populations of 65,000 or more."
                    }),
                )]

            # Validation: tract requires county (ADR-006)
            if tract is not None and county is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Tract-level queries require a county FIPS code. "
                                 "The Census API needs both state and county to resolve tracts. "
                                 "Provide county parameter, or use tract='*' with a county "
                                 "to enumerate all tracts in that county."
                    }),
                )]

            if product not in SUPPORTED_PRODUCTS:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Invalid product '{product}'. Must be one of {SUPPORTED_PRODUCTS}."
                    }),
                )]

            # Build geography parameters
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
            if product == "acs5":
                data_response = await _census_client.get_acs5(
                    variables=variables, year=year, **geo_params
                )
            else:
                data_response = await _census_client.get_acs1(
                    variables=variables, year=year, **geo_params
                )

            # Bundle pragmatics
            pragmatics = _retriever.get_guidance_by_parameters(
                product=product,
                geo_level=geo_level,
                variables=variables,
                year=year,
            )

            source = {
                "dataset": f"American Community Survey {product.upper()}",
                "vintage": year,
                "product": product,
                "api_url": f"https://api.census.gov/data/{year}/acs/{product}",
                "geography": geo_params,
            }

            result = {
                "data": data_response,
                "pragmatics": pragmatics,
                "source": source,
            }

            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]

        except CensusAPIError as e:
            logger.error(f"Census API error: {e}", exc_info=True)
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": f"Census API error: {str(e)}"}),
            )]
        except Exception as e:
            logger.error(f"Error in get_acs_data: {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # -----------------------------------------------------------------
    # explore_variables
    # -----------------------------------------------------------------
    elif name == "explore_variables":
        try:
            concept = arguments["concept"]
            year = arguments.get("year", DEFAULT_YEAR)
            product = arguments.get("product", DEFAULT_PRODUCT)

            all_variables = await _census_client.get_variables(year=year, product=product)

            concept_lower = concept.lower()
            keywords = concept_lower.split()

            matching_vars = []
            tables_seen = set()

            for var_name, var_info in all_variables.items():
                if var_name.endswith(("M", "MA", "EA")):
                    continue

                label = var_info.get("label", "").lower()
                var_concept = var_info.get("concept", "").lower()

                if any(kw in label or kw in var_concept for kw in keywords):
                    matching_vars.append({
                        "name": var_name,
                        "label": var_info.get("label", ""),
                        "concept": var_info.get("concept", ""),
                        "group": var_info.get("group", ""),
                    })
                    if "group" in var_info:
                        tables_seen.add((
                            var_info["group"],
                            var_info.get("concept", ""),
                        ))

            tables = [
                {"code": code, "description": desc}
                for code, desc in sorted(tables_seen)
            ]

            suggestions = []
            if "income" in concept_lower:
                suggestions.append(
                    "Consider also: B19001 (Household Income in bins), "
                    "B19025 (Aggregate household income)"
                )
            if "poverty" in concept_lower:
                suggestions.append(
                    "Consider also: B17001 (Poverty status by age), "
                    "B17020 (Poverty status by age by household type)"
                )

            result = {
                "variables": matching_vars[:50],
                "tables": tables,
                "suggestions": suggestions,
                "caveat": "Variable search is limited to keyword matching. "
                          "Results may be incomplete.",
                "total_matches": len(matching_vars),
            }

            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]

        except CensusAPIError as e:
            logger.error(f"Variable fetch error: {e}", exc_info=True)
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": f"Failed to fetch variables: {str(e)}"}),
            )]
        except Exception as e:
            logger.error(f"Error in explore_variables: {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # -----------------------------------------------------------------
    # Unknown tool
    # -----------------------------------------------------------------
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}",
        )]


# =============================================================================
# MAIN
# =============================================================================

async def _run():
    """Run the MCP server."""
    logger.info("Starting Census MCP Server")
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        if _census_client:
            await _census_client.close()
        logger.info("Census MCP Server stopped")


def main():
    """Entry point for census-mcp CLI command."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
