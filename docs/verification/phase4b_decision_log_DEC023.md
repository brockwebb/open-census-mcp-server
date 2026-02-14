# DEC-4B-023: D6 Rubric Revision — Groundedness → Pipeline Fidelity

## Date: 2026-02-13

## Discovery

D6 "Groundedness & Faithfulness" consistently scored treatment LOWER than 
control (d=-0.23) across all judge vendors. Investigation revealed this is 
a rubric design flaw, not a treatment deficiency.

### Root Cause

D6 asks: "Are all claims traceable to cited Census sources?"

- **Control** makes vague, unfalsifiable claims ("about 15% according to Census data"). 
  Nothing to trace → nothing to penalize → scores well by default.
- **Treatment** cites specific variables (B17001_002E), FIPS codes (04013), exact 
  values with MOEs. Each is a verifiable claim that can be wrong → more surface 
  area for penalty.

The rubric rewards vagueness and penalizes specificity. This is **arbitrary 
coherence** — the judge has no tools to verify claims, so it scores plausibility, 
not actual groundedness.

### Key Insight

Groundedness of API-retrieved data is not a subjective judgment. It is a 
deterministic measurement: did the response faithfully report what the API 
returned? We already have both sides of this comparison in the Stage 1 data 
(tool_calls contain API responses; response_text contains what was reported).

## Decision

**Replace D6 subjective judge scoring with automated Pipeline Fidelity metric.**

- Extract verifiable claims from treatment response_text
- Compare against tool_call results in Stage 1 JSONL
- Compute match rate (exact for codes/FIPS, approximate for values)
- Control scored N/A (no verifiable claims to check)
- Report as separate metric, not part of 5-dimension judge composite

## Framing

This maps to established frameworks:
- **NIST AI RMF (AI 600-1)**: Valid and reliable AI outputs
- **OMB Circular A-130**: Information quality and traceability
- **FCSM Data Quality Framework**: Auditability of statistical outputs

"Pipeline fidelity" not "groundedness" — measures whether the system 
faithfully transmits what authoritative sources provide.

## Rubric Impact

- CQS composite becomes D1-D5 (5 dimensions, judge-scored)
- Pipeline Fidelity reported separately (automated, deterministic)
- D6 scores from existing runs retained for methodological discussion
- Paper discusses why subjective LLM-judge scoring is insufficient for 
  accuracy measurement and proposes automated alternative

## Status

- [x] Discovery documented
- [x] Fidelity extraction script designed and built
- [x] Fidelity metric computed against v3 Stage 1 data
- [x] Symmetric auditability measurement (both conditions)
- [ ] Paper section drafted
- [ ] Integrate into aggregate analysis with Stage 2 results
