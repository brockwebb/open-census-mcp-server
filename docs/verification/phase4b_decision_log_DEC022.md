# DEC-4B-022: Temporal Grounding for Judge Prompt

**Date:** 2026-02-13
**Context:** All three LLM judges penalized treatment responses for citing
2020-2024 ACS 5-year data (released Jan 29, 2026), scoring it as hallucinated.
This caused a D1 score reversal: control d=1.35, treatment d=0.96, p=0.004.

**Root cause:** Judge training data predates the Jan 29, 2026 ACS release.
Judges correctly applied their (stale) knowledge that the latest 5-year was
2019-2023.

**Decision:** Add minimal temporal grounding — a single timestamp line in the
judge prompt. No enumeration of specific releases (avoids over-coaching).
No CPS-specific or ACS-specific context (domain-agnostic).

**Intervention:** "Today's date is February 13, 2026. Score based on data
availability as of this date."

**Rationale:** If timestamp alone fixes D1, clean result. If it doesn't,
that's a stronger finding about LLM-as-judge temporal limitations in
fast-moving domains. Either outcome is publishable.

**Finding:** Temporal evaluation confounds are a systematic risk in
LLM-as-judge evaluation of time-sensitive domains. This generalizes beyond
Census to finance, medicine, law, and any domain where ground truth changes
faster than model training cycles.

**Cost:** Full re-run of all 3 vendors × 6 passes × 39 queries = 702 calls.
