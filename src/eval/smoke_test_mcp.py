"""Smoke test: Can we launch census-mcp as subprocess and call a tool?

This is the minimum viable test for the CQS harness MCP client layer.
If this works, the rest is plumbing. If it doesn't, we debug here first.

Usage:
    cd /Users/brock/Documents/GitHub/census-mcp-server
    /opt/anaconda3/envs/census-mcp/bin/python src/eval/smoke_test_mcp.py
"""

import asyncio
import json
import os

from dotenv import load_dotenv

# MCP SDK client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


async def main():
    """Launch census-mcp, handshake, call one tool, print result."""

    server_params = StdioServerParameters(
        command="/opt/anaconda3/envs/census-mcp/bin/python",
        args=["-m", "census_mcp.server"],
        env={
            "PYTHONPATH": "/Users/brock/Documents/GitHub/census-mcp-server/src",
            "PACKS_DIR": "/Users/brock/Documents/GitHub/census-mcp-server/packs",
            "CENSUS_API_KEY": os.environ.get("CENSUS_API_KEY", ""),
            "LOG_LEVEL": "WARNING",
            "PYTHONUNBUFFERED": "1",
            # Need to inherit PATH for python to find its stdlib
            "PATH": os.environ.get("PATH", ""),
        },
    )

    print("1. Launching MCP server subprocess...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("2. Initializing session...")
            await session.initialize()

            print("3. Listing tools...")
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"   Found {len(tool_names)} tools: {tool_names}")

            expected = {"get_methodology_guidance", "get_census_data", "explore_variables"}
            missing = expected - set(tool_names)
            if missing:
                print(f"   WARNING: Missing expected tools: {missing}")
                return

            print("4. Calling get_methodology_guidance(['margin_of_error'])...")
            result = await session.call_tool(
                "get_methodology_guidance",
                arguments={"topics": ["margin_of_error"]},
            )

            # Result is a list of content blocks
            for block in result.content:
                if hasattr(block, "text"):
                    parsed = json.loads(block.text)
                    context_ids = list(parsed.keys()) if isinstance(parsed, dict) else "unexpected format"
                    print(f"   Got response with keys: {context_ids}")
                    # Print first context item as sample
                    if isinstance(parsed, dict):
                        first_key = next(iter(parsed))
                        first_val = parsed[first_key]
                        if isinstance(first_val, dict):
                            print(f"   Sample context_id: {first_key}")
                            print(f"   Sample title: {first_val.get('title', 'N/A')}")
                        else:
                            print(f"   Sample: {str(first_val)[:200]}")

            print("\n5. Smoke test PASSED ✓")
            print("   MCP client can launch server, handshake, and call tools.")


if __name__ == "__main__":
    asyncio.run(main())
