"""MCP subprocess client for Census MCP Server.

Manages census-mcp subprocess lifecycle and tool execution via stdio JSON-RPC.
Adapted from smoke_test_mcp.py pattern.
"""
import asyncio
import json
import os
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Manages census-mcp subprocess lifecycle and tool execution."""

    def __init__(
        self,
        python_path: str = "/opt/anaconda3/envs/census-mcp/bin/python",
        project_root: str = "/Users/brock/Documents/GitHub/census-mcp-server",
        census_api_key: Optional[str] = None,
    ):
        self.python_path = python_path
        self.project_root = project_root
        self.census_api_key = census_api_key or os.environ.get("CENSUS_API_KEY", "")

        self._session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._stdio_context = None

    async def start(self) -> None:
        """Launch MCP server subprocess, perform handshake."""
        server_params = StdioServerParameters(
            command=self.python_path,
            args=["-m", "census_mcp.server"],
            env={
                "PYTHONPATH": f"{self.project_root}/src",
                "PACKS_DIR": f"{self.project_root}/packs",
                "CENSUS_API_KEY": self.census_api_key,
                "LOG_LEVEL": "WARNING",
                "PYTHONUNBUFFERED": "1",
                "PATH": os.environ.get("PATH", ""),
            },
        )

        # Store the stdio_client context manager
        self._stdio_context = stdio_client(server_params)
        self._read_stream, self._write_stream = await self._stdio_context.__aenter__()

        # Create session
        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()

        # Initialize
        await self._session.initialize()

    async def health_check(self) -> bool:
        """Verify MCP connection: list tools, confirm 3 expected tools present.

        Returns:
            True if all expected tools are present, False otherwise.
        """
        if not self._session:
            return False

        tools_response = await self._session.list_tools()
        tool_names = {t.name for t in tools_response.tools}

        expected = {"get_methodology_guidance", "get_census_data", "explore_variables"}
        return expected.issubset(tool_names)

    async def list_tools(self) -> list[dict]:
        """List available tools with their schemas.

        Returns:
            List of tool definitions with name, description, and inputSchema.
        """
        if not self._session:
            raise RuntimeError("MCP client not started. Call start() first.")

        tools_response = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in tools_response.tools
        ]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool call and return the result.

        Args:
            name: Tool name to call
            arguments: Tool arguments as dict

        Returns:
            Parsed JSON result from tool response

        Raises:
            RuntimeError: If MCP client not started or tool call fails
        """
        if not self._session:
            raise RuntimeError("MCP client not started. Call start() first.")

        result = await self._session.call_tool(name, arguments=arguments)

        # Parse result from content blocks
        for block in result.content:
            if hasattr(block, "text"):
                return json.loads(block.text)

        raise RuntimeError(f"Tool {name} returned no text content")

    async def stop(self) -> None:
        """Gracefully shut down subprocess."""
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None

        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)
            self._stdio_context = None
            self._read_stream = None
            self._write_stream = None
