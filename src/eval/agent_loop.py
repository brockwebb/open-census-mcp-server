"""Claude API agent loop with MCP tool dispatch.

Handles both control (no tools) and treatment (with tools) paths.
"""
import asyncio
import os
import re
import time
from datetime import datetime
from typing import Optional

from anthropic import AsyncAnthropic

from .models import ResponseRecord, ToolCall
from .mcp_client import MCPClient


# System prompts
TREATMENT_SYSTEM_PROMPT = """You are a statistical consultant helping users access and understand U.S. Census data.

You have access to Census data tools. For every query:
1. FIRST call get_methodology_guidance with relevant topics to ground your response
2. Use get_census_data to retrieve actual data with margins of error
3. Use explore_variables if you need to find the right variable codes

Always provide:
- Specific table/variable codes and geography identifiers
- Margins of error and reliability context
- Appropriate caveats about fitness-for-use

If the data is unavailable or unreliable for the stated purpose, say so and explain why.
Recommend alternatives when possible.

IMPORTANT: ALWAYS call get_methodology_guidance first, even when you plan to ask for
clarification. Use the guidance to provide informed clarification that helps the user
understand what data is available and what limitations apply to their request.
Grounding first produces better questions."""

CONTROL_SYSTEM_PROMPT = """You are a helpful assistant answering questions about U.S. Census data.
Provide accurate, well-sourced information."""


class AgentLoop:
    """Claude API agent loop with MCP tool dispatch."""

    def __init__(
        self,
        mcp_client: MCPClient,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 2048,
        max_tool_rounds: int = 5,
        api_key: Optional[str] = None,
    ):
        """Initialize agent loop.

        Args:
            mcp_client: MCP client instance for tool calls
            model: Claude model identifier (pinned for reproducibility)
            max_tokens: Maximum tokens per response
            max_tool_rounds: Safety limit on agent loop iterations
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.mcp_client = mcp_client
        self.model = model
        self.max_tokens = max_tokens
        self.max_tool_rounds = max_tool_rounds

        self.client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    async def run_control(self, query: str, query_id: str) -> ResponseRecord:
        """Run query with no tools, no system prompt augmentation.

        Args:
            query: User query text
            query_id: Query identifier for tracking

        Returns:
            ResponseRecord with control path metadata
        """
        start_time = time.time()

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=CONTROL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": query}],
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract text from response
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        return ResponseRecord(
            query_id=query_id,
            condition="control",
            model=self.model,
            system_prompt=CONTROL_SYSTEM_PROMPT,
            response_text=response_text,
            tool_calls=[],
            pragmatics_returned=[],
            total_latency_ms=latency_ms,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            timestamp=datetime.utcnow(),
            tools_offered=False,
        )

    async def run_treatment(self, query: str, query_id: str) -> ResponseRecord:
        """Run query with tools available. Loops until no more tool_use.

        Args:
            query: User query text
            query_id: Query identifier for tracking

        Returns:
            ResponseRecord with treatment path metadata including all tool calls
        """
        start_time = time.time()

        # Get tool definitions from MCP
        mcp_tools = await self.mcp_client.list_tools()
        anthropic_tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["inputSchema"],
            }
            for t in mcp_tools
        ]

        messages = [{"role": "user", "content": query}]
        tool_calls_made = []
        pragmatics_context_ids = set()
        total_input_tokens = 0
        total_output_tokens = 0
        rounds = 0

        while rounds < self.max_tool_rounds:
            rounds += 1

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=TREATMENT_SYSTEM_PROMPT,
                tools=anthropic_tools,
                messages=messages,
            )

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            # Check if response has tool_use blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
                # No more tools to call, extract final text
                break

            # Process tool calls
            assistant_content = []
            tool_results = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

                    # Execute tool call via MCP
                    tool_start = time.time()
                    try:
                        tool_result = await self.mcp_client.call_tool(block.name, block.input)
                        tool_latency = (time.time() - tool_start) * 1000

                        # Record tool call
                        tool_calls_made.append(
                            ToolCall(
                                tool_name=block.name,
                                arguments=block.input,
                                result=tool_result,
                                latency_ms=tool_latency,
                            )
                        )

                        # Extract pragmatics context_ids from tool result
                        context_ids = self._extract_context_ids(tool_result)
                        pragmatics_context_ids.update(context_ids)

                        # Build tool_result for Claude
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(tool_result),
                            }
                        )

                    except Exception as e:
                        # Tool call failed, report error back to Claude
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error calling tool: {str(e)}",
                                "is_error": True,
                            }
                        )

            # Append assistant response and tool results to messages
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        # Extract final text from last response
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text += block.text

        total_latency_ms = (time.time() - start_time) * 1000

        return ResponseRecord(
            query_id=query_id,
            condition="treatment",
            model=self.model,
            system_prompt=TREATMENT_SYSTEM_PROMPT,
            response_text=response_text,
            tool_calls=tool_calls_made,
            pragmatics_returned=sorted(list(pragmatics_context_ids)),
            total_latency_ms=total_latency_ms,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            timestamp=datetime.utcnow(),
            tools_offered=True,
        )

    def _extract_context_ids(self, tool_result: dict) -> set[str]:
        """Extract pragmatics context_ids from tool result.

        Looks for context_id patterns (e.g., ACS-MOE-001) in the tool result.

        Args:
            tool_result: Parsed JSON tool result

        Returns:
            Set of context_ids found
        """
        context_ids = set()

        # Pattern for context IDs like ACS-MOE-001, CPS-SAM-001, etc.
        pattern = r"\b[A-Z]{3}-[A-Z]{3}-\d{3}\b"

        # Search in stringified result
        result_str = str(tool_result)
        matches = re.findall(pattern, result_str)
        context_ids.update(matches)

        # Also check if result has a 'guidance' key with context items
        if isinstance(tool_result, dict):
            guidance = tool_result.get("guidance", [])
            if isinstance(guidance, list):
                for item in guidance:
                    if isinstance(item, dict) and "context_id" in item:
                        context_ids.add(item["context_id"])

        return context_ids
