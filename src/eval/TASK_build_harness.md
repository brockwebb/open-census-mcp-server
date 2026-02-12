# Claude Code Task: CQS Test Harness Implementation

## Context
You are building the test harness for Phase 4B of the Census MCP Server evaluation.
The smoke test (`src/eval/smoke_test_mcp.py`) already proves the MCP client layer works.
Now build the full harness that generates paired control/treatment responses.

## Architecture Reference
Read FIRST: `/Users/brock/Documents/GitHub/census-mcp-server/docs/verification/cqs_harness_architecture.md`
Decision log: `/Users/brock/Documents/GitHub/census-mcp-server/docs/verification/phase4b_decision_log.md`
Test battery: `/Users/brock/Documents/GitHub/census-mcp-server/docs/verification/cqs_test_battery.md`

## Working Environment
- Python env: `/opt/anaconda3/envs/census-mcp/bin/python`
- Project root: `/Users/brock/Documents/GitHub/census-mcp-server`
- Source dir: `src/eval/`
- .env file at project root has CENSUS_API_KEY and ANTHROPIC_API_KEY
- MCP server module: `census_mcp.server` (launched via `-m census_mcp.server`)
- Smoke test pattern in `src/eval/smoke_test_mcp.py` — reuse the MCP client approach

## Files to Create

### 1. `src/eval/__init__.py` (empty)

### 2. `src/eval/models.py` — Pydantic data models

```python
"""Pydantic models for CQS evaluation data structures."""
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class ToolCall(BaseModel):
    """Record of a single tool call during agent loop."""
    tool_name: str
    arguments: dict
    result: dict  # parsed JSON from tool response
    latency_ms: float

class ResponseRecord(BaseModel):
    """Complete record of one response (control or treatment)."""
    query_id: str
    condition: Literal["control", "treatment"]
    model: str
    system_prompt: str
    response_text: str
    tool_calls: list[ToolCall] = []
    pragmatics_returned: list[str] = []  # context_ids extracted from tool results
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

### 3. `src/eval/mcp_client.py` — MCP subprocess client

Adapt the smoke test pattern. Key requirements:
- `MCPClient` class with `start()`, `call_tool()`, `list_tools()`, `stop()` 
- Uses `mcp.ClientSession` + `mcp.client.stdio.stdio_client`
- Env vars loaded from .env via dotenv
- MCP server params match claude_desktop_config.json:
  - command: `/opt/anaconda3/envs/census-mcp/bin/python`
  - args: `["-m", "census_mcp.server"]`
  - env: PYTHONPATH, PACKS_DIR, CENSUS_API_KEY, LOG_LEVEL, PYTHONUNBUFFERED, PATH
- Health check: list tools, confirm 3 expected tools present
- NOTE: The `stdio_client` is an async context manager. The session must stay open
  for the lifetime of the harness run. Design accordingly (context manager or explicit
  lifecycle management).

### 4. `src/eval/agent_loop.py` — Claude API agent loop

Key requirements:
- Uses `anthropic` Python SDK (AsyncAnthropic)
- Two methods: `run_control(query)` and `run_treatment(query, mcp_client)`
- Model: `claude-sonnet-4-5-20250514` (pinned per DEC-4B-013)
- max_tokens: 2048
- max_tool_rounds: 5 (safety limit)

**Control path:**
- System prompt: "You are a helpful assistant answering questions about U.S. Census data. Provide accurate, well-sourced information."
- No tools parameter
- Single API call, record response text + token usage + latency

**Treatment path:**
- System prompt (from architecture doc):
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
- Tools parameter: built from `mcp_client.list_tools()` — convert MCP tool schemas to Anthropic tool format
- Agent loop:
  1. Send message
  2. If response has `tool_use` content blocks:
     a. For each tool_use block, call `mcp_client.call_tool(name, input)`
     b. Build tool_result content blocks
     c. Append assistant response + tool_results to messages
     d. Send again
  3. Repeat until response has no tool_use blocks OR max_tool_rounds exceeded
  4. Collect final text from all text content blocks
  5. Extract pragmatics context_ids from tool results (look for keys like "ACS-MOE-001" etc)
  6. Return ResponseRecord with all metadata

**Tool schema conversion:**
MCP tools have `inputSchema` (JSON Schema). Anthropic tools need `input_schema`.
The conversion is: `{"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}`

### 5. `src/eval/harness.py` — Main test runner

Key requirements:
- Loads test battery from `src/eval/battery/queries.yaml`
- For each query: runs control, then treatment, writes QueryPair to JSONL
- JSONL output to `results/cqs_responses_{timestamp}.jsonl`
- Resume capability: on start, check output file for existing query_ids, skip them
- CLI interface: `python -m eval.harness [--query-ids NORM-001 GEO-006] [--output path]`
- On MCP or API failure for a single query: log error, skip, continue battery
- Summary stats at end: queries completed, failed, total time

### 6. `src/eval/battery/queries.yaml` — Machine-readable test battery

Convert the test battery markdown into YAML. Structure:
```yaml
queries:
  - id: "NORM-001"
    text: "What is the total population of Harris County, Texas?"
    category: "normal"
    difficulty: "normal"
    pragmatics_exercised: []
    cqs_dimensions_tested: ["D1", "D5", "D6"]
  - id: "NORM-002"
    ...
```

Extract ALL 39 queries from `docs/verification/cqs_test_battery.md`.
Use the `query` field as `text`. Include all metadata fields.

## Key Constraints
- Do NOT modify any existing files outside `src/eval/`
- Do NOT modify server.py or any census_mcp code
- Load API keys from .env only, never hardcode
- All new code goes in `src/eval/`
- Create `results/` directory if it doesn't exist (add .gitkeep)
- Create `src/eval/battery/` directory for queries.yaml

## Testing
After building, run a single-query test:
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python -m eval.harness --query-ids NORM-001
```
This should produce one QueryPair in the JSONL output with both control and treatment responses.

## Do NOT build yet (deferred to later tasks):
- judge_pipeline.py (H.18-H.20)
- analysis.py (H.24)
- lib/stats.py (copy from harmonization project)

These depend on the response data this harness generates.
