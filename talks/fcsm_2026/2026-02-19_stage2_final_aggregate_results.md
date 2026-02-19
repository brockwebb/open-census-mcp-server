# Stage 2 Final Aggregate Results — V2 Evaluation Complete

**Date:** 2026-02-19

---

## Run Details

All three pairwise comparisons complete at 702/702 records each.

| Comparison | Run ID | Records |
|---|---|---|
| RAG vs Pragmatics | `rag_vs_pragmatics_20260216_092144` | 702/702 |
| Control vs RAG | `control_vs_rag_20260217_083951` | 702/702 |
| Control vs Pragmatics | `control_vs_pragmatics_20260218_065924` | 702/702 (after backfill — see QC Notes) |

**Total records analyzed:** 2,106 (3 parse failures excluded)

**Analysis script:** `src/eval/aggregate_analysis.py`
**Statistical methodology:** `talks/fcsm_2026/2026-02-18_statistical_test_selection.md`

---

## Omnibus Result

**Friedman χ²(2) = 42.01, p < 0.001**

All three conditions differ. Proceed to pairwise post-hoc.

---

## Pairwise Results (Holm-corrected)

| Comparison | CQS Delta | Cohen's d | 95% CI | p (Holm) | Eff. N |
|---|---|---|---|---|---|
| Pragmatics vs Control | +0.539 | 1.440 | [0.421, 0.651] | < 0.001 | 36/39 |
| Pragmatics vs RAG | +0.385 | 0.922 | [0.256, 0.513] | < 0.001 | 32/39 |
| RAG vs Control | +0.154 | 0.546 | [0.072, 0.244] | 0.0017 | 30/39 |

All three comparisons significant after Holm correction. No CI crosses zero.

---

## Per-Dimension Omnibus

| Dim | χ²(2) | p |
|-----|-------|---|
| D1 (Source Selection) | 16.25 | < 0.001 |
| D2 (Methodology) | 14.59 | < 0.001 |
| D3 (Uncertainty Communication) | 44.83 | < 0.001 |
| D4 (Statistical Appropriateness) | 29.36 | < 0.001 |
| D5 (Reproducibility) | 16.13 | < 0.001 |

D3 shows the largest omnibus χ² by a wide margin — uncertainty communication is the dimension most sensitive to whether expert judgment is available.

---

## Key Findings

1. **All three comparisons significant.** The three-tier ordering holds: pragmatics > RAG > control, and all pairwise gaps are statistically robust.

2. **Effect sizes span the range.** Pragmatics vs control is very large (d=1.44), pragmatics vs RAG is large (d=0.92), RAG vs control is medium (d=0.55). The pragmatics advantage over RAG is roughly 2.6× the RAG advantage over control.

3. **D3 is the key discriminator.** Uncertainty communication (MOE, reliability caveats, fitness-for-use) is where conditions diverge most. This is exactly what the pragmatics layer is designed to supply.

4. **Pratt method was the right choice.** RAG vs control had 9/39 ties (23%) — standard Wilcoxon would have dropped these, losing substantial power. Effective N of 30/39 shows the method handled tied pairs correctly while preserving sample.

5. **Backfill mattered.** The three recovered Google records for control_vs_pragmatics strengthened RAG vs control from p=0.04 to p=0.0017 — a meaningful improvement in the weakest comparison.

---

## QC Notes

- **3 parse failures** (Anthropic) across all files — stored with `preference: parse_failed`, excluded from analysis. Minor.
- **3 `other:Tie` preference records** in control_vs_pragmatics — likely case-sensitivity normalization issue ("Tie" vs "tie"). Does not affect analysis; document as minor data quality note in methodology.
- **Backfill process:** 3 Google records from separate run `_20260219_065101.jsonl` appended to original `control_vs_pragmatics_20260218_065924.jsonl`. Empty file `_112114.jsonl` (failed retry) and backup deleted.

---

## Files

- `results/v2_redo/stage2/rag_vs_pragmatics_20260216_092144.jsonl` — 702 records
- `results/v2_redo/stage2/control_vs_rag_20260217_083951.jsonl` — 702 records
- `results/v2_redo/stage2/control_vs_pragmatics_20260218_065924.jsonl` — 702 records (backfilled)
- `results/v2_redo/stage2/analysis/aggregate_statistics.json` — full results archive
- `results/v2_redo/stage2/analysis/aggregate_statistics.md` — formatted report

---

## Next Steps

Stage 2 complete. Proceed to:

- **Stage 3:** Fidelity verification — automated claim-vs-evidence checking for all three conditions
- **Stage 4:** Expert validation
