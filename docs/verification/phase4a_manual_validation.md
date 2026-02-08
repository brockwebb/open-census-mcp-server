# Phase 4A Manual Validation Results

**Date:** 2026-02-08
**Tester:** Brock Webb + Claude (AI pair)
**Server Version:** 3.0.0 (post ADR-005 rewrite)

## Test Environment

- Claude Desktop (macOS)
- MCP SDK: 1.9.4
- Python: 3.11 (conda env: census-mcp)
- Server pattern: Low-level `mcp.server.Server` + `stdio_server` (per ADR-005)
- Packs loaded: acs.db, census.db, general_statistics.db

## G.1: PACKS_DIR Environment Variable Fix

**Status:** ✅ PASS
**Date:** 2026-02-08

Server.py reads `PACKS_DIR` from environment, falling back to `"packs"`.
Claude Desktop config passes absolute path. Server starts without error.

## G.2: Claude Desktop MCP Connection

**Status:** ✅ PASS (after ADR-005)
**Date:** 2026-02-08

### Initial Failure (FastMCP)

Original `server.py` used `FastMCP` from `mcp.server.fastmcp`. Server:
- Started without errors
- Responded to JSON-RPC `initialize` handshake correctly
- Showed "running" in Claude Desktop settings
- **Tools never surfaced in any conversation** (project or non-project)

Debugging confirmed: all 9 working MCPs in the same config use low-level
`Server` + `stdio_server`. Census-mcp was the only FastMCP user.

### Fix (ADR-005)

Rewrote `server.py` to use `mcp.server.Server` + `mcp.server.stdio.stdio_server`
with explicit `@server.list_tools()` and `@server.call_tool()` handlers.

### Verification

After rewrite and Desktop restart, `get_methodology_guidance` tool called
successfully from a project conversation:

```
Tool: get_methodology_guidance
Input: {"topics": ["small_area", "margin_of_error"]}
Result: 5 guidance items returned from pragmatics packs
  - ACS-POP-003: 5-year availability for all geographies
  - ACS-MOE-001: SE = MOE / 1.645 formula
  - ACS-MOE-002: CV threshold (40% unreliable)
  - ACS-MOE-003: 5-year vs 1-year MOE comparison
  - ACS-GEO-001: Block group only in 5-year
Related context: 4 items via graph traversal
Sources: ACS-GEN-001 Ch. 3, Ch. 7
```

This confirms:
- Tool registration works with low-level pattern
- Pack loading works (acs.db with inheritance)
- PragmaticsRetriever returns structured guidance
- Graph traversal returns related context
- Source citations are present

## Pre-ADR-005 Observations (LLM-Only Testing)

Before the MCP tools were connected, we tested Census queries using LLM
training data alone (no pragmatics packs). These results inform the
FCSM talk narrative about what LLMs know vs. what they need grounding for.

### Mercer County, PA — Median Income (Opus, no MCP tools)

**Query:** "What's the median income in Mercer, PA?"

LLM correctly:
- Identified Mercer as county (FIPS 42-085)
- Used B19013_001E + B19013_001M variables
- Pulled ACS 5-year 2023 data via direct API URL construction
- Computed CV ≈ 2.1%, flagged as "very reliable"
- Noted county vs borough ambiguity, asked for clarification
- Distinguished household vs individual vs family income

**Source of reasoning:** LLM training data. No MCP tools called.

### St. Louis, MO — Population (Opus, no MCP tools)

**Query:** "What's the population of St. Louis, MO?"

LLM correctly:
- Identified St. Louis as independent city (not in any county)
- Interpreted -555555555 MOE sentinel value correctly
- Warned about city vs county distinction
- Noted 5-year pooling smooths post-COVID shifts

**Source of reasoning:** LLM training data + agent prompt rules.

### Owsley County, KY — Tract-Level Poverty (Opus, no MCP tools)

**Query:** "What's the poverty rate in a small rural tract in Owsley County, Kentucky?"

LLM correctly:
- Pulled county-level AND both tract-level estimates
- Computed CVs: 14.5% (county), 22-24% (tracts)
- Classified reliability correctly ("barely reliable" to "unreliable")
- Stated tracts are statistically indistinguishable
- Recommended county-level over tract-level
- Noted "the true poverty rate could plausibly be anywhere from ~15% to ~35%"

**Source of reasoning:** LLM training data. Only CV threshold (15%/30%)
came from a snippet in project knowledge. All MOE interpretation,
propagation, and fitness-for-use reasoning was from training data.

### Owsley County, KY — Same Query (Sonnet 4, no MCP tools)

**Query:** Same as above, Sonnet 4 model.

Sonnet used **web search** (not Census API). Answer quality was comparable:
- Correct poverty rate and MOE
- Flagged tract-level unreliability
- Noted "practically useless for precise decision-making"

**Source of reasoning:** Web search results + training data. No MCP tools
available (not connected in that session).

### Key Finding

Both Opus and Sonnet 4 provide sound statistical reasoning for these
test cases **without** pragmatics packs. The packs' value proposition
is not "LLMs can't do this" but rather:
1. **Reliability across models** — will Haiku get it right?
2. **Consistency** — same guidance every time, not dependent on prompt
3. **Auditability** — traceable to specific Census Bureau documentation
4. **Edge cases** — inflation adjustment, period overlap, geographic hierarchy

Phase 4B systematic evaluation will test these dimensions empirically.

## G.3: Mercer County, PA — Median Income (MCP Tools Live)

**Status:** ✅ PASS
**Date:** 2026-02-08
**Model:** Opus 4.6 (this project conversation)

Both `get_methodology_guidance` and `get_acs_data` called successfully.

```
Tool: get_methodology_guidance
Input: {"topics": ["small_area", "margin_of_error", "geography"], "domain": "acs"}
Result: 10 guidance items, 5 related, 3 source documents

Tool: get_acs_data
Input: {"variables": ["B19013_001E", "B19013_001M"], "state": "42", "county": "085", "year": 2022, "product": "acs5"}
Result: $57,353 (±$2,084 MOE)
```

Pragmatics bundled with data response: 8 guidance items including:
- ACS-MOE-001: SE = MOE / 1.645 formula
- ACS-MOE-002: CV threshold (40%)
- ACS-DOL-001: Inflation adjustment warning for dollar comparisons
- ACS-PER-001: Period estimate labeling

CV = (2084/1.645) / 57353 × 100 = 2.2% — very reliable.

Full stack validated: tool registration → pack loading → API call → pragmatics bundling.

## G.4: Owsley County, KY — Three-Model Comparison

**Status:** ✅ PASS (with findings)
**Date:** 2026-02-08
**Models tested:** Sonnet 4, Sonnet 4.5, Opus 4.6
**Extended thinking:** OFF for all models

**Query:** "What's the poverty rate in a small rural tract in Owsley County, Kentucky?"

This test was run across three model tiers to evaluate how pragmatics packs
interact with different reasoning capabilities.

### Results by Model

| Dimension | Sonnet 4 | Sonnet 4.5 | Opus 4.6 |
|---|---|---|---|
| Called get_methodology_guidance | ✅ | ✅ | ✅ |
| Used CV formula from packs | ✅ | ✅ | ✅ |
| Resolved tract geography | ❌ (8+ attempts) | ❌ (fell back to web+curl) | ⚠️ (1 pivot to web) |
| Correct tract count | ❌ (claimed 1) | N/A | ⚠️ (found 1, actual: 2) |
| Vintage consistency | ✅ | ❌ (mixed 2019-2023 and 2018-2022) | ✅ |
| Statistical interpretation | Basic | Confident but wrong | Consultant-grade |
| Recovery from tool failure | Flailed | Routed around (introduced errors) | Clean single pivot |

### Tool Bug Identified

`get_acs_data` does not support tract enumeration. When passed a tract code
that doesn't resolve, the Census API silently returns county-level data. All
three models hit this bug. None received an error message.

**Root cause:** Missing `tract:*` wildcard support and no validation that
county is provided when tract is requested.

### Missing Pragmatics Content Identified

1. No proactive warning about population thresholds for tract-level analysis
2. No disclosure avoidance / privacy suppression guidance for small cells
3. No "tract effectively equals county" geographic pattern
4. Tool description doesn't state county is required for tract queries

### Implications

- Pragmatics packs **grounded all three models** on methodology (CV formulas,
  thresholds, period estimate interpretation). The packs work as designed.
- Model tier determines **recovery quality** when tools fail. This validates
  ADR-003's minimum reasoning requirement.
- The MCP needs geographic enumeration capability and better tract-level
  validation before systematic evaluation (Phase 4B).

## G.6: Prompt Slimming + Tool Rename

**Status:** ✅ PASS
**Date:** 2026-02-08

### Changes Made

| Item | Before | After |
|------|--------|-------|
| Prompt length | ~280 lines | ~55 lines |
| "Never" list | 7 items (3 behavioral + 4 domain) | 4 items (all behavioral) |
| "Always" list | 5 items (2 behavioral + 3 domain) | 4 items (all behavioral) |
| Survey language | ACS-specific | FSS-general |
| Tool name | `get_acs_data` | `get_census_data` (legacy accepted) |
| Design notes | Inline in prompt | Separated to `agent_prompt_design_notes.md` |

### Principle

Prompt = how to think. Packs = what to know.

Domain-specific rules removed from the prompt ("never compare 1-year and 5-year",
"always report MOE", etc.) because packs already encode them. Duplicating domain
knowledge in both prompt and packs creates drift risk.

### New Rules Added

- "Communicate uncertainty proportional to the user's decision context and expertise"
  (behavioral, not domain — packs say *what* uncertainty to report, prompt says *scale it to the audience*)
- Audience calibration line: "Match language and detail to user's expertise"

### Validation

Post-restart, both tools respond under new names:

```
Tool: get_methodology_guidance
Input: {"topics": ["small_area", "margin_of_error"]}
Result: 5 guidance items ✔️

Tool: get_census_data
Input: {"variables": ["B19013_001E", "B19013_001M", "B01003_001E"], "state": "42", "county": "085"}
Result: $57,353 (±$2,084) + 8 pragmatics items ✔️
```

ADR-006 tract validation also confirmed live:
- Tract without county → error message ✔️
- Tract wildcard → enumerates both Owsley tracts ✔️
- Legacy name `get_acs_data` still routes correctly ✔️

### External Input

ChatGPT 5.2 SWOT analysis of slim prompt identified audience calibration gap
(adopted) and uncertainty communication gap (adopted). Also suggested causal
inference guardrail (rejected — descriptive survey system, not in scope) and
dual-output template (rejected — over-engineering).

## G.9: Tract-Level Geography Bug Fixes (ADR-006)

**Status:** ✅ PASS
**Date:** 2026-02-08

See `docs/architecture/decisions/adr-006.md` for full rationale.

Three bugs fixed:
1. `elif` chain made tract unreachable when county also provided
2. No validation that county accompanies tract
3. No wildcard (`*`) support for tract enumeration

Live validation confirmed all three fixes work (see G.6 validation above).

## Remaining Phase 4A Tasks

| Task | Status |
|------|--------|
| G.5: SRS reconciliation | ⏳ |
| G.7: Independent cities pack | ⏳ |
| G.8: Documentation | ✅ (this doc) |
| G.10: Disclosure avoidance pack content | ⏳ |
| G.11: Population threshold + geographic equivalence pack content | ⏳ |
