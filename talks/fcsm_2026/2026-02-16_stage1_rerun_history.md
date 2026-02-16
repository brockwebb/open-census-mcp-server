# Lab Notes — Stage 1 Pragmatics Rerun History

**Date:** 2026-02-16

## Timeline

| Run | Timestamp | Condition | Issue | Disposition |
|-----|-----------|-----------|-------|-------------|
| 1 | 20260216_055354 | All three | Pragmatics 82% methodology compliance (7/39 skipped) | Control + RAG KEPT. Pragmatics archived. |
| 2 | 20260216_073058 | Pragmatics only | Grounding gate missed zero-tool clarification path (4/39 still skipped) | Archived as incomplete. |
| 3 | 20260216_074817 | Pragmatics only | Both gate paths implemented (tool-skip + zero-tool). 39/39 (100%) compliance. | FINAL. Commits c47ad9e, 5a19737. |

## Final Stage 1 Dataset

- `control_responses_20260216_055354.jsonl` — 39 records, 1.1MB
- `rag_responses_20260216_055354.jsonl` — 39 records, 2.2MB
- `pragmatics_responses_20260216_074817.jsonl` — 39 records

Timestamp mismatch is expected. Control and RAG were clean from Run 1. Only pragmatics 
required reruns to fix harness bugs in the methodology grounding gate. All runs use:
- Model pin: `claude-sonnet-4-5-20250929`
- MCP server version (commit 33a6a96+)
- Test battery: `queries.yaml` (39 queries, unchanged)
- Tool set: `get_census_data`, `explore_variables`, `get_methodology_guidance`

The timestamp difference reflects harness bug fixes for construct validity, not 
changes to experimental conditions.

## Always-Ground Evidence from the 7 Affected Queries

CC compared pre/post responses. Key findings:
- **Strong evidence (2 queries):** SML-004 and MIS-001 — methodology grounding 
  prevented futile data requests by warning about 65K population threshold upfront. 
  Model would have requested data that doesn't exist.
- **Moderate evidence (3 queries):** Added statistical context to clarifications
- **Marginal improvement (2 queries):** Methodology grounding present but minimal 
  impact on clarification quality

Full comparison: `talks/fcsm_2026/always_ground_comparison.md`

## Archived Files

`results/v2_redo/stage1/archive_pre_grounding_gate/` contains:
- Run 1 pragmatics (82% compliance, 7 skipped methodology)
- Run 2 pragmatics (incomplete, 4 still skipped zero-tool path)

## Bugs Fixed

### Bug 1: Soft prompt language (Run 1 → Run 2)
- Prompt said "Call it first" — model treated as advisory
- Fix: "You MUST call get_methodology_guidance FIRST... no exceptions"
- Added harness grounding gate after tool execution (Gate 2, line 184)

### Bug 2: Zero-tool code path (Run 2 → Run 3)
- Grounding gate only triggered when tool calls were processed
- Pure clarification responses (zero tools) broke out of loop before reaching gate
- Fix: Added Gate 1 (line 119) before the zero-tool break
