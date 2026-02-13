# Lesson Learned: Tool Non-Use in Treatment Path

**Date:** 2026-02-12
**Phase:** 4B Stage 1
**Severity:** Moderate — affects 5/39 queries (13%)

## Observation

Five treatment-path responses contained zero tool calls despite tools being available and the system prompt instructing "FIRST call get_methodology_guidance." All five were ambiguity, mismatch, or underspecified queries where the model chose to request clarification rather than call tools.

| Query ID | Category | Model Decision |
|---|---|---|
| GEO-004 | geographic_edge/trap | "Which Portland?" — asked for disambiguation |
| SML-004 | small_area/tricky | "What variables?" — query underspecified |
| AMB-001 | ambiguity/trap | "Which Springfield?" — asked for disambiguation |
| AMB-002 | ambiguity/trap | "What area?" — no geography provided |
| MIS-003 | product_mismatch/tricky | Redirected away from ACS for monthly data |

## Root Cause

Stochastic model behavior. Sonnet evaluated the query, determined clarification was more appropriate than tool use, and responded directly without calling any tools. The system prompt said "FIRST call get_methodology_guidance" but did not say "ALWAYS, regardless of whether you need clarification."

This is a cost of stochastic models with behavior variance as a feature, not a bug.

## Why This Matters

1. **Diagnostic ambiguity:** The harness records tool calls that happened, not tool calls that were considered and rejected. We cannot distinguish "model chose not to call tools" from "tools were unavailable" in the output data.

2. **Missed pragmatics-informed clarification:** A model that grounds first could provide *better* clarification. Example: "Which Springfield? Note that for Springfields under 65,000 population, only ACS 5-year estimates are available, which affects what we can tell you." This is strictly superior to generic clarification.

3. **Experimental confound:** These 5 queries will score similarly in control and treatment because the treatment didn't actually *use* the treatment. This dilutes the measured treatment effect.

## Corrective Actions

### Fix 1: Strengthen treatment system prompt

Add explicit instruction to always ground first, even when clarification is needed:

```
IMPORTANT: ALWAYS call get_methodology_guidance first, even when you need 
to ask for clarification. Use the guidance to provide informed clarification 
that helps the user understand what data is available and what limitations 
apply to their request.
```

### Fix 2: Add diagnostic logging to harness

Add `tools_offered: bool` field to ResponseRecord. Set to True when tools were passed to the API regardless of whether the model used them. This distinguishes "tools available but unused" from "tools unavailable."

### Fix 3: Re-run battery

With both fixes applied, re-run all 39 queries. Compare tool usage rates. Previous stale results archived.

## Principle

Non-determinism in LLM behavior is a feature, not a bug. The correct response is:
- **Account for it** in experimental design (statistical aggregation, not exact reproducibility)
- **Log it** for diagnostic transparency (tools_offered vs tools_used)
- **Strengthen contracts** where behavior matters (prompt engineering for tool compliance)
- **Document it** as a known source of variance

This is analogous to measurement error in survey methodology — you don't eliminate it, you quantify it and account for it in your analysis.

> "Model stochasticity is a parameter to manage; system nondeterminism is a failure mode to control." — B. Webb
