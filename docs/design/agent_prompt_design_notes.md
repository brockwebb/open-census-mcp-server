# Agent Prompt — Design Notes
# Location: docs/design/agent_prompt_design_notes.md
# Separated from agent_prompt.md during G.6 prompt slimming (2026-02-08).
# These are implementation commentary, not shipped prompt content.

## Why Always Ground

The agent always calls `get_methodology_guidance` before interpreting data because:

1. **Knowledge cutoff** — LLM training data has a fixed date. Census methodology changes. The pragmatics packs are maintained independently.

2. **Confident wrongness** — LLMs assess their own knowledge poorly. Grounding catches what confidence misses.

3. **Cheap insurance** — One extra tool call per query. The cost is negligible vs the downside of misleading a user.

4. **Cynefin integration** — Complexity assessment determines how deeply the agent engages with guidance, not whether it retrieves it.

## Prompt-Tool Contract

| Prompt expects | Tool must provide |
|---------------|-------------------|
| "always call get_methodology_guidance FIRST" | Tool must be fast and lightweight |
| "pragmatic guidance bundled" with data | `get_acs_data` returns `data` + `pragmatics` fields |
| "query methodology knowledge base by topics" | `get_methodology_guidance` accepts topic tags |
| "discover available Census variables" | `explore_variables` accepts natural language |
| "stateless tool calls" | No session state between calls |

## Pragmatics Matching Strategy

When `get_acs_data` is called, pragmatics are matched by request parameters:

| Parameter | Triggers |
|-----------|----------|
| `product == "acs1"` | Population threshold contexts |
| `tract is not None` | Small area contexts, 5-year only context |
| `product == "acs5"` | Period estimate context |
| Any income/dollar variable | Inflation adjustment context |
| `year` near break points | Break-in-series contexts |
| Any request | MOE/reliability contexts |

This is parameter-based filtering, not reasoning. The MCP matches; the LLM decides what's relevant.

## What Was Removed in G.6 Slim (2026-02-08)

The following domain-specific rules were removed from the prompt because they
are now covered by pragmatics packs. The packs are the authoritative source;
duplicating rules in the prompt creates maintenance burden and drift risk.

**Removed from "Never" list:**
- "Report an estimate without its margin of error" → ACS-MOE-001/002
- "Compare 1-year and 5-year ACS estimates" → ACS-CMP-001
- "Treat period estimates as point-in-time snapshots" → ACS-PER-001
- "Present unreliable estimates (high CV) as precise facts" → ACS-MOE-002

**Removed from "Always" list:**
- "Report margins of error alongside estimates" → ACS-MOE-001
- "Surface fitness-for-use caveats from the pragmatics" → redundant with "don't ignore pragmatics"

**Principle:** Prompt = how to think. Packs = what to know.
See `docs/decisions/decision_log_prompt_specificity.md` for original decision.

## Workflow Example

```
User: "What's the median income in Mercer, PA?"

OBSERVE: Income query, specific place (Mercer, PA), no time specified.
ORIENT:  Call get_methodology_guidance(topics=["small_area", "margin_of_error", "dollar_values"])
DECIDE:  Mercer borough is small (~2,000). Must use ACS 5-year. Flag MOE.
ACT:     Call get_acs_data(variables=["B19013_001E"], state="42", place="...", product="acs5")
CHECK:   MOE large relative to estimate. CV suggests use with caution.

Response: "According to the 2018-2022 ACS 5-year estimates, median household
          income in Mercer borough, PA is approximately $X ± $Y. Note: Mercer
          is a small community (~2,000 people), so this estimate has a wide
          margin of error..."
```

## Tool Schemas (Reference)

See `server.py` `list_tools_handler()` for current schemas. The schemas in server.py
are the source of truth; this document previously contained copies that could drift.
