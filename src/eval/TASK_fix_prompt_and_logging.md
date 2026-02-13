# Claude Code Task: Strengthen Treatment Prompt + Add Tool Availability Logging

## Context
Stage 1 battery run revealed 5/39 treatment queries (13%) where the model 
answered without calling any tools, despite tools being available. We need
two fixes before re-running.

See: `docs/lessons_learned/2026-02-12_tool_nonuse_treatment_path.md`

## Fix 1: Strengthen Treatment System Prompt

File: `src/eval/agent_loop.py`

In the `TREATMENT_SYSTEM_PROMPT` string, add the following paragraph after 
the existing "Recommend alternatives when possible." line:

```
IMPORTANT: ALWAYS call get_methodology_guidance first, even when you plan to
ask for clarification. Use the guidance to provide informed clarification 
that helps the user understand what data is available and what limitations 
apply to their request. Grounding first produces better questions.
```

The full prompt should read (preserving existing content, adding new paragraph at end):
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

IMPORTANT: ALWAYS call get_methodology_guidance first, even when you plan to ask for
clarification. Use the guidance to provide informed clarification that helps the user
understand what data is available and what limitations apply to their request. 
Grounding first produces better questions.
```

Do NOT change the CONTROL_SYSTEM_PROMPT.

## Fix 2: Add `tools_offered` field to ResponseRecord

File: `src/eval/models.py`

Add a boolean field `tools_offered` to the `ResponseRecord` model:
```python
tools_offered: bool = False  # True when tools were passed to the API
```

File: `src/eval/agent_loop.py`

In `run_control()`: set `tools_offered=False` in the returned ResponseRecord.

In `run_treatment()`: set `tools_offered=True` in the returned ResponseRecord 
(set it after the `list_tools()` call succeeds, confirming tools were actually available).

This way, when we see `tools_offered=True` and `tool_calls=[]`, we know the model
chose not to use tools (prompt compliance issue), not that tools were unavailable
(infrastructure issue).

## Fix 3: Update Test Plan Configuration Chapter

File: `docs/verification/test_plan/03_configuration.md`

In §3.2, update the Treatment prompt to match the new version.

## Verification

1. Run the smoke test to confirm MCP still works:
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python src/eval/smoke_test_mcp.py
```

2. Run existing tests:
```bash
/opt/anaconda3/envs/census-mcp/bin/python -m pytest tests/ -x -q
```

3. Run NORM-001 single query to verify treatment still works:
```bash
/opt/anaconda3/envs/census-mcp/bin/python -m eval.harness --query-ids NORM-001
```

4. Check the output JSONL to confirm `tools_offered` field is present:
```bash
python3 -c "
import json
with open('results/cqs_responses_*.jsonl') as f:
    r = json.loads(f.readline())
    print('control tools_offered:', r['control'].get('tools_offered'))
    print('treatment tools_offered:', r['treatment'].get('tools_offered'))
"
```

## Constraints
- Do NOT change the control system prompt
- Do NOT change tool definitions or MCP interface
- Do NOT change the battery queries
- Do NOT delete previous results files (archive them)
- The `tools_offered` field must default to False for backward compatibility with existing JSONL
