# Lab Notebook: Statistical Test Selection for V2 Aggregate Analysis

**Date:** 2026-02-18  
**Context:** All three Stage 2 pairwise comparisons complete (699+702+702 = 2,103 judge records). Need to select appropriate statistical tests for omnibus and post-hoc analysis across 3 conditions (control, RAG, pragmatics) with ordinal 0-1-2 scores on 39 matched queries.

---

## Independent Verification

Test selection was independently verified via two external sources before implementation. The query posed to both:

> "For a repeated-measures design with 3 conditions, ordinal outcome data (0-2 scale), and 39 matched observations, what are the appropriate statistical tests for (a) omnibus comparison across all 3 conditions, and (b) pairwise post-hoc comparisons? What multiple comparison correction is standard? What are alternatives to Friedman + Wilcoxon with Bonferroni/Holm?"

### Source 1: Google Gemini Pro (2026-02-18, web chat)

**Confirmed:** Friedman test as omnibus, Wilcoxon signed-rank for post-hoc, Holm-Bonferroni as preferred correction over plain Bonferroni.

**Critical additional findings:**

1. **Tie problem.** With a 3-point ordinal scale (0-1-2), massive ties are guaranteed. Standard rank-based tests struggle with this. The Friedman calculation requires a tie correction or p-values will be inaccurate. The Wilcoxon test drops pairs where the difference is zero (tied scores between conditions), drastically reducing effective sample size from 39. Recommended using the **Pratt method** for handling zero-differences in Wilcoxon.

2. **Modern alternatives recommended:**
   - **Cumulative Link Mixed Models (CLMM)** — ordinal mixed-effects regression via R `ordinal` package (`clmm` function). Models probability of falling into each category. Handles ties natively. Random intercept for query. Post-hocs via `emmeans` package with Tukey or Holm adjustment.
   - **Generalized Estimating Equations (GEE)** with ordinal link — population-averaged effects, accounts for correlated repeated measures. R packages: `geepack`, `multgee`.
   - **Brunner-Langer nonparametric marginal models** — computes "relative effects" (probability that observation from Condition A > Condition B) rather than standard ranks. Solves tie and zero-difference issues. R package: `nparLD`.

3. **Recommendation from source:** "If your audience expects traditional tests, use Friedman + Wilcoxon with Holm correction, but aggressively check for tie/zero-difference distortions. If you want the most mathematically sound approach for a 3-point scale, use an Ordinal Mixed-Effects Model (CLMM)."

4. **Bonferroni vs Holm:** "There is rarely a mathematical justification to use Bonferroni when Holm is available." Holm is uniformly more powerful while maintaining the same FWER control.

### Source 2: Perplexity AI (2026-02-18, web search with citations)

**Confirmed:** Friedman test as omnibus, Wilcoxon signed-rank for post-hoc, both Bonferroni and Holm as standard corrections.

**Cited sources:**
- Six Sigma Study Guide (Friedman test usage)
- Real Statistics (post-hoc alternatives)
- PMC/NCBI (multiple comparison corrections)
- R-statistics resources (implementation alternatives)

**Additional alternatives mentioned:**
- Nemenyi or Conover tests — use rank sums directly for all pairs (integrated post-hoc without separate Wilcoxon calls)
- Rank-transform + repeated-measures ANOVA — hybrid parametric approach
- Ordinal cumulative logit mixed models (CLMM) — treats 0-2 scale as ordered categories
- FDR / Benjamini-Hochberg — controls false discovery rate rather than FWER

---

## Consensus Across Sources

Both sources independently confirm:

| Component | Recommended Test | Agreement |
|-----------|-----------------|-----------|
| Omnibus | Friedman test (with tie correction) | Both sources |
| Post-hoc pairwise | Wilcoxon signed-rank | Both sources |
| Correction | Holm-Bonferroni preferred over plain Bonferroni | Both sources |
| Modern alternative | CLMM (ordinal mixed-effects) | Both sources |
| Key risk | Tie inflation on 0-1-2 scale reducing effective N | Google source (detailed) |

---

## Design Characteristics Relevant to Test Selection

| Characteristic | Our Data |
|----------------|----------|
| Conditions | 3 (control, RAG, pragmatics) |
| Observations | 39 matched queries |
| Scale | Ordinal 0-1-2 per dimension (D1-D5) |
| Repeated measures | Same queries across all conditions |
| Judges | 3 vendors × 6 passes = 18 judgments per query per comparison |
| Nesting | Judges nested within queries — need to aggregate to per-query scores before Friedman |
| Expected ties | High — 3-point scale guarantees many zero-differences |

---

## Decision: Analysis Approach

**Primary analysis (FCSM audience):** Friedman omnibus + Wilcoxon signed-rank post-hoc with Holm correction. Apply tie correction to Friedman. Use Pratt method for Wilcoxon zero-differences. Report effective N after dropping ties per comparison.

**Robustness check (appendix/supplementary):** CLMM via R `ordinal::clmm()` with random intercept for query, post-hocs via `emmeans` with Holm adjustment. If primary and robustness agree on significance and direction, report primary. If they disagree, report CLMM as primary with discussion of tie distortion.

**Effect sizes:** Cohen's d (paired) for each comparison. Bootstrap 95% CIs on CQS deltas (10,000 resamples).

**Rationale for dual approach:** Traditional tests are expected by the FCSM audience and provide comparability with existing literature. CLMM is the more defensible method for ordinal data with heavy ties but is less familiar to the target audience. Running both provides robustness without sacrificing accessibility.

---

## Implementation Notes

- Aggregate judge scores to per-query median CQS before running Friedman (unit of analysis = query, not individual judgment)
- 3 pairwise comparisons = 3 Wilcoxon tests → Holm correction with k=3
- Bootstrap CIs: resample queries with replacement, compute CQS delta per resample
- All three Stage 2 files needed: `rag_vs_pragmatics_20260216_092144.jsonl`, `control_vs_rag_20260217_083951.jsonl`, `control_vs_pragmatics_20260218_065924.jsonl`
- control_vs_pragmatics has 699/702 records (3 Google failures, TMP-003 and TMP-004) — backfill after Google rate limit reset, but 699 is sufficient for analysis
