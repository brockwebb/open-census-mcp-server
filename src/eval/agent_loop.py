"""Claude API agent loop with MCP tool dispatch — V2 Equal-Tool Design.

All three conditions (control, rag, pragmatics) use the same agent loop.
Single variable: methodology support form.

Tool access:
  - Control:    get_census_data, explore_variables
  - RAG:        get_census_data, explore_variables (+ RAG chunks in prompt)
  - Pragmatics: get_census_data, explore_variables, get_methodology_guidance
"""
import os
import re
import time
from datetime import datetime
from typing import Optional

from anthropic import AsyncAnthropic

from .models import ResponseRecord, ToolCall
from .mcp_client import MCPClient
from .rag_retriever import RAGRetriever


# ---------------------------------------------------------------------------
# System prompts — minimal, equal, no quality coaching
# ---------------------------------------------------------------------------

BASE_SYSTEM_PROMPT = (
    "You are a statistical consultant helping users access and understand "
    "U.S. Census data. Use your available tools to answer the question."
)

# Control and RAG share the same base prompt.
# RAG gets chunks appended by the retriever — no prompt change here.
CONTROL_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT

PRAGMATICS_SYSTEM_PROMPT = (
    BASE_SYSTEM_PROMPT
    + "\n\nYou also have access to get_methodology_guidance. "
    "Call it first to ground your response before retrieving data."
)

# Tool that ONLY the pragmatics condition gets
PRAGMATICS_ONLY_TOOL = "get_methodology_guidance"


class AgentLoop:
    """Claude API agent loop with MCP tool dispatch."""

    def __init__(
        self,
        mcp_client: MCPClient,
        model: str = "claude-sonnet-4-5-20250929",  # Fallback — should come from judge_config.yaml
        max_tokens: int = 2048,
        max_tool_rounds: int = 20,
        api_key: Optional[str] = None,
    ):
        self.mcp_client = mcp_client
        self.model = model
        self.max_tokens = max_tokens
        self.max_tool_rounds = max_tool_rounds
        self.client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    # ------------------------------------------------------------------
    # Shared agent loop — all three conditions use this
    # ------------------------------------------------------------------

    async def _run_agent_loop(
        self,
        query: str,
        query_id: str,
        condition: str,
        system_prompt: str,
        anthropic_tools: list[dict],
        tool_names_offered: set[str],
    ) -> ResponseRecord:
        """Core agent loop shared by all conditions.

        Args:
            query: User query text
            query_id: Query identifier for tracking
            condition: "control", "rag", or "pragmatics"
            system_prompt: System prompt (may include RAG chunks)
            anthropic_tools: Tool definitions to pass to the Anthropic API
            tool_names_offered: Set of tool names offered (for logging/verification)

        Returns:
            ResponseRecord with full metadata
        """
        start_time = time.time()

        messages = [{"role": "user", "content": query}]
        tool_calls_made = []
        pragmatics_context_ids = set()
        total_input_tokens = 0
        total_output_tokens = 0
        rounds = 0
        response = None

        while rounds < self.max_tool_rounds:
            rounds += 1

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                tools=anthropic_tools,
                messages=messages,
            )

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            # Check if response has tool_use blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
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

                        tool_calls_made.append(
                            ToolCall(
                                tool_name=block.name,
                                arguments=block.input,
                                result=tool_result,
                                latency_ms=tool_latency,
                            )
                        )

                        # Extract pragmatics context_ids (only relevant for pragmatics condition)
                        if condition == "pragmatics":
                            context_ids = self._extract_context_ids(tool_result)
                            pragmatics_context_ids.update(context_ids)

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(tool_result),
                            }
                        )

                    except Exception as e:
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error calling tool: {str(e)}",
                                "is_error": True,
                            }
                        )

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        # Check if loop exhausted without final answer
        tool_rounds_exhausted = False
        if rounds >= self.max_tool_rounds and response and response.stop_reason == "tool_use":
            tool_rounds_exhausted = True
            synthesis_response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages + [
                    {"role": "user", "content": [{"type": "text", "text":
                        "You have reached the maximum number of tool calls. "
                        "Please provide your best answer based on the data "
                        "you have already retrieved."}]}
                ],
                # NO tools — forces text-only response
            )
            total_input_tokens += synthesis_response.usage.input_tokens
            total_output_tokens += synthesis_response.usage.output_tokens
            response = synthesis_response

        # Extract final text
        response_text = ""
        if response:
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

        total_latency_ms = (time.time() - start_time) * 1000

        return ResponseRecord(
            query_id=query_id,
            condition=condition,
            model=self.model,
            system_prompt=system_prompt,
            response_text=response_text,
            tool_calls=tool_calls_made,
            pragmatics_returned=sorted(list(pragmatics_context_ids)),
            total_latency_ms=total_latency_ms,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            timestamp=datetime.utcnow(),
            tools_offered=True,
            tool_rounds_used=rounds,
            tool_rounds_exhausted=tool_rounds_exhausted,
        )

    # ------------------------------------------------------------------
    # Tool filtering
    # ------------------------------------------------------------------

    async def _get_filtered_tools(self, include_pragmatics: bool = False) -> tuple[list[dict], set[str]]:
        """Get tool definitions from MCP, optionally filtering out pragmatics tool.

        Args:
            include_pragmatics: If True, include get_methodology_guidance.
                                If False, exclude it (control + RAG conditions).

        Returns:
            (anthropic_tools, tool_names) — formatted for API and name set for logging
        """
        mcp_tools = await self.mcp_client.list_tools()

        if not include_pragmatics:
            mcp_tools = [t for t in mcp_tools if t["name"] != PRAGMATICS_ONLY_TOOL]

        anthropic_tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["inputSchema"],
            }
            for t in mcp_tools
        ]

        tool_names = {t["name"] for t in anthropic_tools}
        return anthropic_tools, tool_names

    # ------------------------------------------------------------------
    # Public condition methods
    # ------------------------------------------------------------------

    async def run_control(self, query: str, query_id: str) -> ResponseRecord:
        """Control: data tools only, base system prompt."""
        anthropic_tools, tool_names = await self._get_filtered_tools(include_pragmatics=False)

        assert PRAGMATICS_ONLY_TOOL not in tool_names, \
            f"CONTAMINATION: {PRAGMATICS_ONLY_TOOL} found in control tool set!"

        return await self._run_agent_loop(
            query=query,
            query_id=query_id,
            condition="control",
            system_prompt=CONTROL_SYSTEM_PROMPT,
            anthropic_tools=anthropic_tools,
            tool_names_offered=tool_names,
        )

    async def run_rag(self, query: str, query_id: str, retriever: RAGRetriever) -> ResponseRecord:
        """RAG: data tools + RAG chunks in system prompt, base prompt."""
        anthropic_tools, tool_names = await self._get_filtered_tools(include_pragmatics=False)

        assert PRAGMATICS_ONLY_TOOL not in tool_names, \
            f"CONTAMINATION: {PRAGMATICS_ONLY_TOOL} found in RAG tool set!"

        # Retrieve chunks and augment system prompt
        augmented_prompt, retrieval_metadata = retriever.format_system_prompt(
            CONTROL_SYSTEM_PROMPT, query
        )

        record = await self._run_agent_loop(
            query=query,
            query_id=query_id,
            condition="rag",
            system_prompt=augmented_prompt,
            anthropic_tools=anthropic_tools,
            tool_names_offered=tool_names,
        )

        # Attach RAG-specific metadata
        record.retrieved_chunks = retrieval_metadata["retrieved_chunks"]
        record.retrieval_context_chars = retrieval_metadata["total_context_chars"]

        return record

    async def run_pragmatics(self, query: str, query_id: str) -> ResponseRecord:
        """Pragmatics: all tools including get_methodology_guidance."""
        anthropic_tools, tool_names = await self._get_filtered_tools(include_pragmatics=True)

        assert PRAGMATICS_ONLY_TOOL in tool_names, \
            f"MISSING: {PRAGMATICS_ONLY_TOOL} not found in pragmatics tool set!"

        return await self._run_agent_loop(
            query=query,
            query_id=query_id,
            condition="pragmatics",
            system_prompt=PRAGMATICS_SYSTEM_PROMPT,
            anthropic_tools=anthropic_tools,
            tool_names_offered=tool_names,
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _extract_context_ids(self, tool_result: dict) -> set[str]:
        """Extract pragmatics context_ids from tool result."""
        context_ids = set()

        pattern = r"\b[A-Z]{3}-[A-Z]{3}-\d{3}\b"
        result_str = str(tool_result)
        matches = re.findall(pattern, result_str)
        context_ids.update(matches)

        if isinstance(tool_result, dict):
            guidance = tool_result.get("guidance", [])
            if isinstance(guidance, list):
                for item in guidance:
                    if isinstance(item, dict) and "context_id" in item:
                        context_ids.add(item["context_id"])

        return context_ids
