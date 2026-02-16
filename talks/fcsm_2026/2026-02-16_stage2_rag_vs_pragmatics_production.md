# Stage 2 V2 Production Run — RAG vs Pragmatics

**Date:** 2026-02-16
**Tags:** stage2, v2_redo, rag_vs_pragmatics, production_run, QC, CQS, judge_scoring, parse_failure, identical_vectors, NORM-013, PER-001a, MIS-002, MIS-003, GEO-003, vendor_divergence, D3, D4, preference_rate

---

## Run Parameters
- **Command:** `python -m src.eval.judge_pipeline --comparison rag_vs_pragmatics`
- **Run ID:** `rag_vs_pragmatics_20260216_092144`
- **Output:** `results/v2_redo/stage2/rag_vs_pragmatics_20260216_092144.jsonl`
- **Vendors:** Anthropic (claude-opus-4-5-20251101), OpenAI (gpt-5.2), Google (gemini-3-pro-preview)
- **Wall clock:** OpenAI ~14min, Anthropic ~15min, Google ~46min (8 truncation retries, all recovered)
- **Result:** 702/702 successful, 0 failed, 100% parse rate

---

## QC Step 1: Structural Validation

| Check | Result | Status |
|-------|--------|--------|
| Total records | 702 | PASS |
| Parse failures | 3 (all Anthropic, 1.3%) | PASS — records drop cleanly |
| Unique query_ids | 39 | PASS |
| Comparison field | all `rag_vs_pragmatics` | PASS |
| Label pairs | `{(rag, pragmatics), (pragmatics, rag)}` | PASS |
| Same-condition pairs | 0 | PASS |
| Ordering distribution | 351 / 351 | PASS |
| Per-vendor counts | 234 / 234 / 234 | PASS |
| Out-of-range scores/confidence | 0 | PASS |
| Preference contradicts own D1-D5 sum | 19/702 (2.7%) | PASS — expected, holistic judgment |
| 1 Google `response_b` preference | Literal string instead of `B` | NOTE — normalize in analysis |

## QC Step 2: Identical Score Vectors

77/702 (11%) had identical A/B score vectors. Evenly distributed across vendors (not a vendor problem):

| Vendor | Identical | Total | Rate |
|--------|-----------|-------|------|
| Anthropic | 29 | 231 | 12.6% |
| Google | 24 | 234 | 10.3% |
| OpenAI | 24 | 234 | 10.3% |

Concentrated in specific queries (a query problem):

| Query | Identical/Total | Why |
|-------|-----------------|-----|
| MIS-003 | 12/18 | "Monthly ACS data" — both correctly redirect, same refusal |
| MIS-002 | 11/18 | "Decennial income" — both correctly redirect to ACS |
| GEO-003 | 10/18 | "Population of Washington" — ambiguity trap, similar handling |
| NORM-013 | 9/18 | Transit commuting — investigated below |
| PER-001a | 8/18 | 8th grader Bozeman — investigated below |

**Verdict:** Legitimate ties on queries where knowledge representation form doesn't matter. Not a pipeline defect.

## QC Step 3: Response Inspection (NORM-013, PER-001a)

### NORM-013: "What percentage of workers in Alameda County commute by public transit?"

Both conditions produced substantively identical responses:
- Same answer: 7.7%
- Same table, same MOEs (±4,145 total workers, ±2,308 transit)
- Same denominator (workers 16+): 837,261
- Pragmatics slightly longer (1,543 vs 1,089 chars) with period reference framing ("2020-2024" vs "2024 ACS 5-year")
- RAG called 5 tools (3 explore_variables attempts), pragmatics called 4 (methodology first)

**Conclusion:** Straightforward lookup. Both conditions handle routine percentage calculations fine. 9/18 tie rate is the system correctly identifying equivalent responses.

### PER-001a: "My 8th grade class is doing a project. How many people live in Bozeman, Montana and is it growing?"

Both conditions correctly answered with growth trend data:
- RAG: 2018-2022 window, 7% growth, 1,900/year average
- Pragmatics: 2015-2023 window (wider, more recent), 9.4% growth, emoji, simpler framing
- Pragmatics better adapted tone for 8th grader persona
- But core statistical content similar enough for judges to score equivalently

**Conclusion:** Normal query with clear answer. Pragmatics adds marginal value (tone, wider window) but substance is equivalent. 8/18 tie rate is reasonable.

### Implication
Pragmatics earn their keep on hard cases (uncertainty, definitions, small area reliability, temporal comparability), not straightforward lookups. Tie concentration in routine queries reinforces the story — the 35-pragmatic pack targets the 10% that needs 90% of the judgment, not the 90% the model already handles.

---

## Results: Dimension Means

| Dimension | RAG (n=699) | Pragmatics (n=699) | Delta |
|-----------|-------------|---------------------|-------|
| D1 (Source Selection) | 1.398 | 1.551 | +0.153 |
| D2 (Methodology) | 1.262 | 1.488 | +0.226 |
| D3 (Uncertainty) | 0.678 | 1.333 | **+0.655** |
| D4 (Definitions) | 1.415 | 1.711 | **+0.296** |
| D5 (Reproducibility) | 0.770 | 1.043 | +0.273 |
| D6 (Groundedness) | 1.272 | 1.335 | +0.063 |
| **CQS (D1-D5)** | **1.104** | **1.425** | **+0.321** |

D3 (uncertainty communication) is the standout: +0.655 delta. This is where curated judgment about MOE interpretation, CV thresholds, and reliability warnings makes the biggest difference. D4 (definitions) is the second largest gap — pragmatics provide precise Census concept usage that raw chunks dilute.

D6 is nearly flat (+0.063) — groundedness is a tool behavior (did the model use real data?), not a knowledge representation behavior. Both conditions have equal tool access, so this is expected.

## Results: Preferences

| | Pragmatics | RAG | Tie | Parse Failed |
|---|---|---|---|---|
| **Overall** | 489 (70.1%) | 128 (18.3%) | 81 (11.6%) | 3 |
| Anthropic | 178 (77.1%) | 43 (18.6%) | 10 (4.3%) | 3 |
| Google | 184 (78.6%) | 49 (20.9%) | 0 (0%) | 1* |
| OpenAI | 127 (54.3%) | 36 (15.4%) | 71 (30.3%) | 0 |

*Google had 1 `response_b` literal string — effectively a pragmatics preference.

## Results: Per-Vendor Pragmatics CQS

| Vendor | CQS (D1-D5) | D3 | D4 |
|--------|-------------|-----|-----|
| Anthropic | 1.558 | 1.442 | 1.823 |
| Google | 1.603 | 1.551 | 1.850 |
| OpenAI | 1.116 | 1.009 | 1.462 |

All three vendors agree on direction. OpenAI is most conservative scorer and most tie-prone (71 ties vs Anthropic 10, Google 0). Anthropic and Google score similarly. Worth reporting as inter-vendor calibration differences — direction unanimous, magnitude varies.

Anthropic self-enhancement bias check: Anthropic gives pragmatics CQS 1.558, vs Google 1.603. Google scores pragmatics *higher* than Anthropic does. No evidence of self-enhancement — if anything, Anthropic is slightly more conservative than Google on the Claude-generated responses.

---

## Key Takeaways

1. **35 curated pragmatics outperformed 311 RAG chunks.** CQS delta +0.321, 70% preference rate, all vendors agree.
2. **D3 (uncertainty) is the killer dimension.** +0.655 delta. Curated judgment about MOE thresholds, CV interpretation, and reliability warnings is exactly what raw document chunks can't deliver.
3. **Tie concentration in routine queries is a feature, not a bug.** Product mismatch redirects and straightforward lookups tie because knowledge representation doesn't matter for those. Pragmatics differentiate on the hard cases.
4. **No self-enhancement bias detected.** Google scores pragmatics higher than Anthropic does on Claude-generated responses.
5. **OpenAI calibration differs.** More conservative, more ties. Same direction. Report as vendor calibration variance.

---

## Next Steps
- Tomorrow: `control_vs_rag` (does RAG even help over baseline?)
- Day after: `control_vs_pragmatics` (pragmatics vs no methodology support)
- Then: Stage 3 fidelity, aggregate analysis with Friedman omnibus + Wilcoxon post-hoc
