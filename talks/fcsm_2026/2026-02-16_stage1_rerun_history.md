# Lab Notes — Stage 1 Pragmatics Rerun History

**Date:** 2026-02-16

## Timeline

| Run | Timestamp | Condition | Issue | Disposition |
|-----|-----------|-----------|-------|-------------|
| 1 | 20260216_055354 | All three | Pragmatics 82% methodology compliance (7/39 skipped) | Control + RAG KEPT. Pragmatics archived. |
| 2 | 20260216_073058 | Pragmatics only | Grounding gate missed zero-tool clarification path (4/39 still skipped) | Archived as incomplete. |
| 3 | TBD | Pragmatics only | Both gate paths implemented (tool-skip + zero-tool) | FINAL — must be 39/39 compliance. |

## Timestamp Mismatch

The final Stage 1 dataset has mismatched timestamps:
- `control_responses_20260216_055354.jsonl` — from Run 1
- `rag_responses_20260216_055354.jsonl` — from Run 1
- `pragmatics_responses_{run3_ts}.jsonl` — from Run 3

This is expected. Control and RAG were clean from Run 1. Only pragmatics required 
reruns to fix harness bugs in the methodology grounding gate. All runs use the same:
- Model pin: `claude-sonnet-4-5-20250929`
- MCP server version (commit 33a6a96+)
- Test battery: `queries.yaml` (39 queries, unchanged)
- Tool set: `get_census_data`, `explore_variables`, `get_methodology_guidance`

The timestamp difference reflects harness bug fixes for construct validity, not 
changes to experimental conditions.

## Archived Files

`results/v2_redo/stage1/archive_pre_grounding_gate/` contains:
- Original Run 1 pragmatics (82% compliance, 7 skipped methodology)
- Incomplete Run 2 pragmatics (gate missed zero-tool path, 4 still skipped)

These are preserved for before/after comparison on the affected queries — evidence 
for the always-ground thesis.

## Bugs Fixed

### Bug 1: Soft prompt language (Run 1 → Run 2)
- Prompt said "Call it first" — model treated as advisory
- Fix: Changed to "You MUST call get_methodology_guidance FIRST... no exceptions"
- Added harness grounding gate after tool execution

### Bug 2: Zero-tool code path (Run 2 → Run 3)
- Grounding gate only triggered when tool calls were processed
- Model responding with pure clarification (zero tools) broke out of loop before 
  reaching the gate
- Fix: Added gate check before the zero-tool break, redirecting model to call 
  methodology guidance before clarifying
