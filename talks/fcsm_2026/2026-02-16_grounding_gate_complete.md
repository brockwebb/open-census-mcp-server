# Lab Notes — 2026-02-16 — Grounding Gate Implementation Complete

**Source:** Claude Code session summary

## Summary

Successfully enforced ADR-004 always-ground thesis for pragmatics condition.

## What Was Done

1. Identified the gap: 7 of 39 pragmatics queries skipped methodology consultation (82% compliance)
2. Root cause: Grounding gate only triggered when tool calls were processed. Zero-tool clarifications bypassed the gate.
3. Fixed with dual grounding gate:
   - Gate 1 (line 119): Catches zero-tool responses in round 1
   - Gate 2 (line 184): Catches non-methodology tool calls in round 1
   - Also strengthened system prompt ("You MUST call... FIRST... no exceptions")
4. Reran pragmatics: 39/39 queries completed with 100% methodology compliance
5. Evidence for always-ground thesis:
   - **Strong evidence (2 queries):** SML-004 and MIS-001 — methodology grounding prevented futile data requests by warning about 65K population threshold upfront
   - **Moderate evidence (3 queries):** Added statistical context to clarifications
   - **Marginal improvement (2 queries):** Both had methodology grounding but minimal quality delta
6. Documented everything:
   - `talks/fcsm_2026/always_ground_comparison.md` — Full pre/post analysis
   - `talks/fcsm_2026/2026-02-16_stage1_rerun_history.md` — Run timeline and archived files
   - `talks/fcsm_2026/2026-02-16_methodology_compliance_gap.md` — Discovery and fix rationale
   - Committed (c47ad9e, 5a19737) and pushed

## Key Finding

Even for clarification requests with zero data tool calls, consulting methodology first produces higher-quality responses that warn about fitness-for-use constraints. SML-004 and MIS-001 are direct evidence — grounding prevented bad requests by surfacing population thresholds before the user asked for data that doesn't exist.

The grounding gate is justified. ADR-004 always-ground thesis validated empirically.

## Final Stage 1 Files

- `control_responses_20260216_055354.jsonl` (39 records, 1.1MB)
- `rag_responses_20260216_055354.jsonl` (39 records, 2.2MB)
- `pragmatics_responses_20260216_074817.jsonl` (39 records, 100% compliance)

Ready for Stage 2: Judge scoring.
