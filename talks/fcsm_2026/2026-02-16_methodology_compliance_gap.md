# Lab Notes — 2026-02-16 — Methodology Grounding Compliance Gap

## Discovery

After Stage 1 rerun (post-leakage fix), CC reported 32/39 (82%) pragmatics queries 
called `get_methodology_guidance`. 7 queries skipped it despite the prompt instruction 
"Call it first to ground your response before retrieving data."

## Why This Matters

The always-ground thesis (ADR-004) requires that the model consult methodology 
guidance for EVERY query, even when it thinks it doesn't need it. RAG achieves this 
structurally — chunks are injected into the system prompt before the model reasons. 
There is no opt-out. Pragmatics must have an equivalent structural guarantee.

18% non-compliance means the pragmatics condition is testing a weaker claim than 
intended: "sometimes-ground" rather than "always-ground." This is a bug, not a finding.

## Root Cause

The system prompt used soft language: "Call it first to ground your response before 
retrieving data." The model treated this as advisory, not mandatory.

## Fix

Two-part fix:
1. Strengthen prompt: "You MUST call get_methodology_guidance FIRST before any other 
   tool calls. This is required for every query — no exceptions."
2. Harness enforcement: if pragmatics round 1 completes without a methodology call, 
   the harness sends a redirect message requiring compliance. The model makes the real 
   call with its own topics. No fake data injected.

## Impact

Only pragmatics responses need rerun (39 queries, ~45 min). Control and RAG are clean.
New pragmatics file will have a different timestamp — documented.

## Rejected Alternative

Force-injecting a fake `get_methodology_guidance` call. This fabricates experimental 
data. The model must make the real call with its own topic selection.
