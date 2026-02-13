# CQS Test Harness — Architecture & Implementation Plan

**Version:** 0.1 DRAFT
**Date:** 2026-02-12
**Traces To:** H.12–H.17 (Implementation Schedule), DEC-4B-002

---

## Overview

The test harness generates paired response data (control vs treatment) for CQS evaluation.
For each test query, it produces two responses from the same model (Claude):

- **Control:** Claude API with no tools, no system prompt augmentation
- **Treatment:** Claude API with live MCP tools via agent loop

Both responses are recorded with full metadata for downstream judge scoring.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  cqs_test_harness.py                 │
│                                                     │
│  1. Load test battery (YAML)                        │
│  2. For each query:                                 │
│     a. Run CONTROL path (Claude API, no tools)      │
│     b. Run TREATMENT path (Claude API + MCP tools)  │
│     c. Record both responses + metadata             │
│  3. Output: JSONL file of paired results            │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
     ┌─────▼─────┐        ┌──────▼──────────────────┐
     │  Claude    │        │  Claude API             │
     │  API       │        │  + Agent Loop           │
     │  (no tools)│        │                         │
     │            │        │  tool_use request        │
     │            │        │    ↓                     │
     │            │        │  MCP Client (stdio)      │
     │            │        │    ↓                     │
     │            │        │  census-mcp subprocess   │
     │            │        │    ↓                     │
     │            │        │  tool_result → Claude    │
     │            │        │    ↓                     │
     │            │        │  final response          │
     └────────────┘        └─────────────────────────┘
```

---

## File Structure

```
src/eval/
├── __init__.py
├── harness.py            # Main test runner (H.12–H.17)
├── mcp_client.py         # MCP subprocess client (H.12, H.13)
├── agent_loop.py         # Claude API agent loop with tool dispatch (H.14)
├── models.py             # Pydantic models for all data structures
├── judge_pipeline.py     # Judge scoring pipeline (H.18–H.20, Step 4)
├── analysis.py           # Agreement & treatment effect analysis (H.20, H.24)
├── lib/
│   └── stats.py          # Copied from federal-survey-concept-mapper
└── battery/
    └── queries.yaml      # Machine-readable test battery (H.4)
```

---

## Module Specifications

### mcp_client.py (H.12, H.13)

**Responsibility:** Launch census-mcp server as subprocess, communicate via stdio JSON-RPC.

```python
class MCPClient:
    """Manages census-mcp subprocess lifecycle and tool execution."""

    async def start(self) -> None:
        """Launch MCP server subprocess, perform handshake."""
        # subprocess: /opt/anaconda3/envs/census-mcp/bin/python -m census_mcp.server
        # env: PYTHONPATH, PACKS_DIR, CENSUS_API_KEY, LOG_LEVEL
        # Protocol: JSON-RPC over stdio (stdin/stdout)
        # Handshake: initialize → initialized → tools/list

    async def health_check(self) -> bool:
        """Verify MCP connection: list tools, confirm 3 expected tools present."""
        # Expected: get_methodology_guidance, get_census_data, explore_variables

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool call and return the result."""
        # JSON-RPC: tools/call → result

    async def stop(self) -> None:
        """Gracefully shut down subprocess."""
```

**Key design:** Uses `mcp` SDK client classes (`ClientSession`, `StdioServerParameters`) rather than raw subprocess management. The SDK handles JSON-RPC framing.

### agent_loop.py (H.14, H.15)

**Responsibility:** Send queries to Claude API, handle tool_use responses by dispatching to MCP client.

```python
class AgentLoop:
    """Claude API agent loop with MCP tool dispatch."""

    def __init__(self, mcp_client: MCPClient, model: str = "claude-sonnet-4-5-20250514"):
        # Using Sonnet for cost efficiency on 39×2=78 API calls
        # Treatment gets tools; control does not

    async def run_treatment(self, query: str, system_prompt: str) -> ResponseRecord:
        """Run query with tools available. Loops until no more tool_use."""
        # 1. Send message with tool definitions from MCP tools/list
        # 2. If response has tool_use blocks:
        #    a. Execute each via mcp_client.call_tool()
        #    b. Append tool_result to messages
        #    c. Send again
        # 3. Repeat until response has no tool_use (just text)
        # 4. Record: final text, all tool calls made, all pragmatics returned, latency

    async def run_control(self, query: str) -> ResponseRecord:
        """Run query with no tools, no system prompt augmentation."""
        # Plain messages API call. No tools parameter.
        # Record: final text, latency
```

**Agent prompt (treatment):** Minimal. Per ADR-003/004, the MCP does validation and retrieval; the LLM does routing and interpretation. System prompt should instruct Claude to use the Census tools to answer the user's question, calling get_methodology_guidance first.

**Control prompt:** Same base instruction ("You are a helpful assistant answering questions about U.S. Census data") but NO tools and NO methodology grounding.

### models.py

```python
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class ToolCall(BaseModel):
    """Record of a single tool call during agent loop."""
    tool_name: str
    arguments: dict
    result: dict
    latency_ms: float

class ResponseRecord(BaseModel):
    """Complete record of one response (control or treatment)."""
    query_id: str
    condition: Literal["control", "treatment"]
    model: str
    system_prompt: str
    response_text: str
    tool_calls: list[ToolCall] = []
    pragmatics_returned: list[str] = []  # context_ids
    total_latency_ms: float
    input_tokens: int
    output_tokens: int
    timestamp: datetime

class QueryPair(BaseModel):
    """Paired control + treatment for one query."""
    query_id: str
    query_text: str
    category: str
    difficulty: str
    control: ResponseRecord
    treatment: ResponseRecord
```

### harness.py (H.16, H.17)

**Responsibility:** Orchestrate the full test run.

```python
class CQSTestHarness:
    """Main test runner for CQS evaluation."""

    def __init__(self, battery_path: str, output_path: str):
        # Load YAML battery
        # Initialize MCP client
        # Initialize agent loop

    async def run(self, query_ids: list[str] | None = None) -> None:
        """Run full battery or subset. Writes JSONL incrementally."""
        # 1. Start MCP server, health check
        # 2. For each query:
        #    a. Run control (no tools)
        #    b. Run treatment (with tools)
        #    c. Write QueryPair to JSONL (incremental, resume-safe)
        # 3. Stop MCP server
        # 4. Summary stats to stdout

    async def resume(self) -> None:
        """Resume from last checkpoint (skip completed queries)."""
```

**Output format:** One JSON object per line in `results/cqs_responses_YYYYMMDD_HHMMSS.jsonl`. Each line is a serialized `QueryPair`.

---

## System Prompts

### Treatment System Prompt

```
You are a statistical consultant helping users access and understand U.S. Census data.

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
```

### Control System Prompt

```
You are a helpful assistant answering questions about U.S. Census data.
Provide accurate, well-sourced information.
```

**Design note:** The control prompt is intentionally minimal. We're testing what pragmatics ADD, not what a carefully engineered prompt can do. The treatment advantage should come from tools and grounding, not from a better system prompt.

---

## Configuration

All environment-specific values in a config file, not hardcoded:

```yaml
# config/eval_config.yaml
mcp:
  python_path: "/opt/anaconda3/envs/census-mcp/bin/python"
  module: "census_mcp.server"
  env:
    PYTHONPATH: "/Users/brock/Documents/GitHub/census-mcp-server/src"
    PACKS_DIR: "/Users/brock/Documents/GitHub/census-mcp-server/packs"
    CENSUS_API_KEY: "${CENSUS_API_KEY}"  # from .env
    LOG_LEVEL: "WARNING"

claude:
  model: "claude-sonnet-4-5-20250514"
  max_tokens: 2048
  max_tool_rounds: 5  # safety limit on agent loop iterations

output:
  results_dir: "results/"
  filename_template: "cqs_responses_{timestamp}.jsonl"
```

---

## Error Handling & Resume

- **JSONL checkpointing:** Each QueryPair written immediately after completion. On resume, skip query_ids already present in output file.
- **MCP failure:** If MCP server crashes mid-run, log error for that query, mark treatment as failed, continue to next query. Don't abort the full battery.
- **API rate limits:** Exponential backoff with jitter, per model. Max 3 retries per API call.
- **Agent loop safety:** Max 5 tool rounds per query. If exceeded, record partial response and move on.

---

## Dependencies (additions to pyproject.toml)

```toml
[project.optional-dependencies]
eval = [
    "anthropic>=0.40.0",     # Claude API client
    "pyyaml>=6.0",           # Battery YAML loading
    "python-dotenv>=1.0.0",  # .env for API keys
    "krippendorff>=0.7.0",   # Agreement analysis
]
```

---

## Resolved Design Questions

- **Test subject model:** Sonnet 4.5 (`claude-sonnet-4-5-20250929`). Median real-user model. See DEC-4B-013.
- **System prompt:** Minimal, generic. No CLAUDE.md. External tester perspective. See DEC-4B-015.
- **Max tokens:** 2048. Sufficient for statistical consultation responses.
- **Statefulness:** Zero-shot, single-turn, stateless. See DEC-4B-016.
- **Judge models:** Opus-class (more capable than test subject). See DEC-4B-014.
- **Configuration:** All output-affecting parameters in `src/census_mcp/config.py`. No hardcodes. See DEC-4B-019, QR-010, C-006.

## Reproducibility Contract (per QR-016)

Evaluation results are fully reproducible given these four components:

| Component | Location | Versioning |
|---|---|---|
| Server config | `src/census_mcp/config.py` | Git hash |
| Pack content | `packs/acs.db` | Content hash (SHA-256) |
| Test battery | `src/eval/battery/queries.yaml` | Git hash |
| Model strings | Harness config + JSONL metadata | Pinned exact checkpoint |

The harness SHALL record all four in the JSONL output header (per QR-014) so any result file is self-documenting.
