# Stage 2 Production Run — control_vs_rag

**Date:** 2026-02-17
**Run ID:** `control_vs_rag_20260217_083951`
**Comparison:** Control vs RAG
**Output:** `results/v2_redo/stage2/control_vs_rag_20260217_083951.jsonl`

---

## Run Summary

- **Total records:** 702/702 (39 queries × 6 passes × 3 vendors)
- **Parse failures:** 0 (100% success rate)
- **Wall clock time:** ~75 minutes (OpenAI ~14min, Anthropic ~15min, Google ~46min)

---

## Key Findings

### Overall CQS Scores

| Condition | CQS (D1-D5) |
|-----------|-------------|
| Control   | 1.056       |
| RAG       | 1.147       |
| **Delta** | **+0.091**  |

**Result:** RAG outperforms control, but the improvement is modest.

### Dimension Breakdown

| Dimension | Control | RAG   | Delta   | Interpretation |
|-----------|---------|-------|---------|----------------|
| D1 (Source Selection) | 1.375 | 1.379 | +0.004 | Essentially tied |
| D2 (Methodology) | 1.279 | 1.309 | +0.030 | RAG slightly better |
| **D3 (Uncertainty Communication)** | **0.483** | **0.764** | **+0.281** | **RAG much better** — largest gap |
| D4 (Statistical Appropriateness) | 1.415 | 1.500 | +0.085 | RAG better |
| D5 (Reproducibility) | 0.726 | 0.782 | +0.056 | RAG slightly better |

**Key insight:** RAG's primary benefit is in **D3 (uncertainty/context communication)**. The +0.281 improvement on D3 accounts for most of RAG's overall CQS advantage. RAG chunks likely contain methodology caveats that control lacks.

### Preference Analysis

| Preference | Count | Percentage |
|------------|-------|------------|
| RAG        | 376   | 53.6%      |
| Control    | 187   | 26.6%      |
| Tie        | 132   | 18.8%      |
| Other:Tie  | 7     | 1.0%       |

**Result:** RAG wins 2:1 over control. Judges prefer RAG when they can differentiate.

### Identical Score Vectors

- **Total:** 145/702 (20.7%)
- **Top queries:**
  - AMB-001: 18/18 (100% identical — judges cannot differentiate)
  - AMB-003: 15/18 (83%)
  - NORM-001: 14/18 (78%)
  - SML-003: 14/18 (78%)
  - SML-001: 12/18 (67%)

**Interpretation:** Higher than Day 1's rag_vs_pragmatics run (11%). Expected — control and RAG both use the same tool calls, so responses differ only in context snippets. On queries where RAG chunks don't add discriminative value, judges can't tell them apart.

### Vendor Calibration

| Vendor     | Control | RAG   |
|------------|---------|-------|
| Google     | 1.339   | 1.437 |
| Anthropic  | 1.087   | 1.201 |
| OpenAI     | 0.740   | 0.803 |

**Observations:**
- **Google lenient** (scores 1.3-1.4 range)
- **Anthropic middle** (scores 1.0-1.2 range)
- **OpenAI harsh** (scores 0.7-0.8 range)
- **All three vendors agree on direction** (RAG > control)
- Vendor spread is consistent with Day 1's rag_vs_pragmatics run

**Inter-rater reliability concern:** Vendors use different scoring standards. This is why we use all three — consensus on direction matters more than absolute scores.

---

## Comparison to Day 1 (rag_vs_pragmatics)

| Metric | control_vs_rag (Day 2) | rag_vs_pragmatics (Day 1) |
|--------|------------------------|---------------------------|
| Winner CQS | 1.147 (RAG) | 1.425 (pragmatics) |
| Loser CQS | 1.056 (control) | 1.104 (RAG) |
| Delta | +0.091 | +0.321 |
| Preference win rate | 53.6% (RAG) | 70.1% (pragmatics) |
| Identical vectors | 20.7% | 11.0% |

**Key insight:** The pragmatics delta (+0.321) is **3.5× larger** than the RAG delta (+0.091). RAG helps modestly on uncertainty communication; pragmatics helps across all dimensions.

---

## Interpretation

### Does RAG Help?

**Yes, but modestly.** RAG provides a +0.091 CQS improvement over control, driven primarily by D3 (uncertainty communication). This validates that metadata context has some value, but the effect is small.

### Why Is RAG's Effect Small?

1. **Semantic smearing** — Census variable metadata is semantically homogeneous. RAG retrieval often returns chunks that are topically related but not pragmatically useful.
2. **No fitness-for-use guidance** — RAG chunks describe what variables measure, but don't encode expert judgment about when/why to use them.
3. **Token overhead** — RAG responses are 120% larger than control (2.2MB vs 1.1MB) for a modest quality gain.

### Why Is Pragmatics Better?

Pragmatics outperforms RAG by 3.5× because it encodes **structured expert judgment** instead of raw metadata retrieval. Pragmatics tells the system *which data to use* and *how to interpret it*, not just *what exists*.

---

## QC Status

✅ All structural checks passed
- 702/702 records, balanced ordering, no same-condition pairs
- Comparison field: `control_vs_rag` (correct)
- Vendor distribution: 234 each (perfect balance)

**QC script:** `src/eval/qc_stage2.py` (consolidated from Day 1 manual QC + Day 2 validation)

---

## Next Steps

**Day 3 run:** `control_vs_pragmatics` ready to execute after Google rate limit reset (~0400 EST).

```bash
python -m src.eval.judge_pipeline --comparison control_vs_pragmatics
```

This will complete the three pairwise comparisons needed for Friedman omnibus test + Wilcoxon post-hoc analysis.

---

## Files

- **Input (Stage 1):**
  - `results/v2_redo/stage1/control_responses_20260216_055354.jsonl` (39 records)
  - `results/v2_redo/stage1/rag_responses_20260216_055354.jsonl` (39 records)

- **Output (Stage 2):**
  - `results/v2_redo/stage2/control_vs_rag_20260217_083951.jsonl` (702 records)

- **QC:**
  - `src/eval/qc_stage2.py` — reusable validation script
