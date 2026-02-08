# Decision Log: Agent Prompt Specificity

**Date:** 2026-02-07
**Context:** ADR-004 implementation, agent prompt draft review

## Decision
The agent prompt's "Never" list and prescriptive rules (e.g., "never compare 
1-year and 5-year ACS estimates") are likely overfitting. The prompt encodes 
specific Census methodology that belongs in the pragmatics packs, not the 
system prompt.

**Principle:** The prompt should encode *how to think*, not *what to know*. 
The packs encode what to know.

## Current State
Leaving as-is for testing. The current prompt works well enough to validate 
the architecture. Specific Census rules in the prompt are redundant with pack 
content but not harmful for initial testing.

## Future Action
After testing, slim the "Never" list to thinking-process rules only:
- Never skip orientation
- Never ignore bundled pragmatics  
- Never trust training over methodology guidance
- Never assume a simple question is actually simple

Remove all domain-specific rules that the packs already cover. This prevents 
the prompt from going stale when packs update.

## Risk
If we don't revisit: prompt and packs drift apart, contradictions emerge, 
maintenance burden doubles.

## Resolution (2026-02-08, G.6)

**DONE.** Prompt slimmed per this decision.

Removed 4 domain-specific items from "Never" list, 2 from "Always" list.
All removed items are covered by pragmatics packs (ACS-MOE-001/002, ACS-CMP-001,
ACS-PER-001). Design notes moved to `agent_prompt_design_notes.md`.

Added audience calibration line based on external SWOT review (ChatGPT 5.2
assessment identified audience adaptation as a gap; assessment was correct
on this point).

Prompt went from ~280 lines to ~55 lines. Domain knowledge now lives
exclusively in packs.
