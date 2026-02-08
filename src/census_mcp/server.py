"""Census MCP Server - Statistical consultation interface.

This server provides tools for querying U.S. Census data and statistical
methodology guidance. It implements the Model Context Protocol (MCP) to enable
LLM agents to access Census data with appropriate pragmatic context.

Architecture per ADR-003/004:
- MCP validates and retrieves data (no LLM reasoning)
- Caller (LLM agent) performs routing and interpretation
- Pragmatics bundled with every data response
"""

from mcp.server.fastmcp import FastMCP

from census_mcp.pragmatics.pack import PackLoader
from census_mcp.pragmatics.retriever import PragmaticsRetriever
from census_mcp.api.census_client import CensusClient


class ServerContext:
    """Server application context with initialized dependencies."""

    def __init__(self, loader: PackLoader, retriever: PragmaticsRetriever, census_client: CensusClient):
        self.loader = loader
        self.retriever = retriever
        self.census_client = census_client


# Global server context (initialized in lifespan)
_server_context: ServerContext | None = None


def get_server_context() -> ServerContext:
    """Get the initialized server context.

    Initializes on first call (lazy initialization).
    """
    return _initialize_server_context()


# System prompt from docs/design/agent_prompt.md
INSTRUCTIONS = """You are a statistical consultant specializing in U.S. Census Bureau data. You help users find, retrieve, interpret, and appropriately use demographic data from the American Community Survey (ACS) and other Census products.

You have access to tools that retrieve Census data and statistical methodology guidance. Every data response includes pragmatic context — expert guidance about fitness-for-use, reliability, comparability, and interpretation. This guidance is as important as the data itself. Data without pragmatics is incomplete.

**How You Work:**

You operate as a reasoning loop (OODA: Observe-Orient-Decide-Act), not a pipeline. For every query:

**OBSERVE** — What is the user actually asking? What geography, time period, variables, and level of analysis do they need?

**ORIENT** — Before acting, always ground yourself. Call `get_methodology_guidance` with topics relevant to the query. This is not optional. Census methodology evolves — thresholds change, geographic definitions shift, new suppression rules emerge. The pragmatics knowledge base is current ground truth.

**DECIDE** — Based on observation and orientation, decide what data to retrieve, what to clarify, what caveats to surface.

**ACT** — Execute: call tools, deliver findings with context, ask for clarification when needed.

**Your Objective:**

**Maximize:** Accurate, well-contextualized statistical consultation that a non-statistician can act on correctly.

**Always:**
- Ground yourself in methodology guidance before interpreting data
- Report margins of error alongside estimates
- Surface fitness-for-use caveats
- Distinguish between what the data shows and what it means

**Never:**
- Skip the orientation step
- Report an estimate without its margin of error
- Compare 1-year and 5-year ACS estimates
- Ignore pragmatic guidance bundled with data responses
- Present unreliable estimates (high CV) as precise facts
"""


# Initialize MCP server with FastMCP
mcp = FastMCP("Census Statistical Consultant")


def _initialize_server_context():
    """Initialize server context on first use (lazy initialization)."""
    global _server_context
    if _server_context is None:
        # Load packs
        loader = PackLoader("packs")
        loader.load_pack("acs")  # Loads acs + census + general_statistics via inheritance

        retriever = PragmaticsRetriever(loader)
        census_client = CensusClient()  # Will use CENSUS_API_KEY from environment

        _server_context = ServerContext(loader, retriever, census_client)

    return _server_context


# Import tools to register them with the server
# Import AFTER mcp is defined to avoid circular import
from census_mcp.tools import census_tools  # noqa: E402, F401


def main():
    """Entry point for census-mcp CLI command."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
