# Results

<!-- Registry references: S2-001–042, S3-001–012, SA-001–022, EFF-001–008, COST-001–013, DET-001–004 -->

## Overall Consultation Quality

The Friedman test revealed a significant omnibus difference across the three conditions (χ²(2, N = 39) = 42.01, p < 0.001). All three pairwise comparisons were significant after Holm-Bonferroni correction.

| Condition | Mean CQS | *n* |
|-----------|----------|-----|
| Pragmatics | 1.528 | 39 |
| RAG | 1.144 | 39 |
| Control | 0.990 | 39 |

: CQS composite scores by condition (D1–D5 mean of per-query medians). {#tbl-cqs-means}

**Panel A: Omnibus**

| Test | Statistic | *p* | *n* |
|------|-----------|-----|-----|
| Friedman χ²(2) | 42.01 | < .001 | 39 |

**Panel B: Pairwise (Holm-corrected)**

| Comparison | Δ CQS | Cohen’s *d* | 95% CI | *p* (Holm) | Eff. *n* |
|------------|-------|-------------|--------|------------|----------|
| Pragmatics vs Control | +0.538 | 1.440 | [0.421, 0.651] | < .001 | 36 |
| Pragmatics vs RAG | +0.385 | 0.922 | [0.256, 0.513] | < .001 | 32 |
| RAG vs Control | +0.154 | 0.546 | [0.072, 0.244] | .002 | 30 |

: Friedman omnibus and Wilcoxon signed-rank pairwise comparisons with Holm–Bonferroni correction. Bootstrap 95% CIs (10,000 iterations) on CQS deltas. {#tbl-pairwise}

Pragmatics produced a very large improvement over the control condition (Δ CQS = +0.539, Cohen's d = 1.440, 95% CI [0.421, 0.651], p < 0.001) and a large improvement over RAG (Δ CQS = +0.385, d = 0.922, 95% CI [0.256, 0.513], p < 0.001). RAG produced a medium improvement over control (Δ CQS = +0.154, d = 0.546, 95% CI [0.072, 0.244], p = 0.0017). Mean composite scores were 1.528 (pragmatics), 1.144 (RAG), and 0.990 (control).

The ordering was consistent: pragmatics outperformed RAG, which outperformed control, across every level of analysis.

## Per-Dimension Effects

![Cohen's *d* effect sizes by dimension. Vertical lines: *d* = 0.2 (small), 0.5 (medium), 0.8 (large).](assets/figures/F7_effect_sizes_forest.pdf){#fig-effect-sizes width=6.5in}

| Dimension | Prag vs Ctrl *d* | Prag vs RAG *d* | RAG vs Ctrl *d* |
|-----------|-----------------|-----------------|-----------------|
| D1 (Accuracy) | 0.541 | 0.515 | 0.190 |
| D2 (Completeness) | 0.537 | 0.297 | 0.246 |
| D3 (Uncertainty Communication) | **1.353** | **1.040** | 0.417 |
| D4 (Contextual Clarity) | **0.957** | 0.577 | 0.546 |
| D5 (Fitness-for-Use Assessment) | 0.732 | 0.521 | 0.148 |

: Per-dimension Cohen’s *d* effect sizes. Bold indicates *d* > 0.8 (large). {#tbl-dimension-effects}

All five quality dimensions showed significant omnibus effects (p < 0.001 for each). The effect sizes for pragmatics versus control varied across dimensions, revealing where expert judgment matters most:

Uncertainty communication (D3) showed the largest effect (d = 1.353 vs. control, d = 1.040 vs. RAG). This dimension captures whether responses appropriately communicate reliability limitations, margins of error, and data fitness: the core of what pragmatics are designed to deliver. The magnitude of this effect is consistent with the mechanism: pragmatics encode specific reliability thresholds, interpretation formulas, and informed-refusal criteria that the model cannot derive from training data or retrieved document chunks.

Clarity of explanation (D4) showed the second-largest effect (d = 0.957 vs. control). Accuracy (D1, d = 0.541), completeness (D2, d = 0.537), and harm avoidance (D5, d = 0.732) showed medium to large effects. The consistency across all five dimensions indicates that pragmatics improve the overall quality of statistical consultation rather than optimizing a single aspect.

RAG showed its largest advantage over control on clarity (D4, d = 0.546) and uncertainty (D3, d = 0.417), with smaller effects on accuracy (D1, d = 0.190) and harm avoidance (D5, d = 0.148). The pattern suggests that retrieved document chunks provide some contextual value but lack the precision to substantially improve reliability assessment or harm prevention.

## Stratum Analysis: Normal vs. Edge Cases

The evaluation was stratified to test whether pragmatics disproportionately help on edge cases (queries involving small areas, geographic exceptions, temporal comparisons, and ambiguous requests) or whether benefits extend to routine statistical queries.

| Comparison | Normal *d* (*n*=15) | Edge *d* (*n*=24) | Δ*d* (Edge−Normal) | *p* (Edge > Normal) |
|------------|--------------------|--------------------|---------------------|---------------------|
| Prag vs Ctrl | **2.347** | 1.135 | -0.273 | .987 |
| Prag vs RAG | **1.436** | 0.683 | -0.318 | .987 |
| RAG vs Ctrl | 0.458 | 0.590 | +0.044 | .347 |

: Stratum analysis comparing normal (*n*=15) and edge-case (*n*=24) queries. Δ*d* is the delta-of-deltas (edge minus normal mean CQS delta). Mann-Whitney *p* tests whether edge deltas exceed normal deltas. {#tbl-stratum}

The results contradicted the initial hypothesis. Pragmatics showed a *larger* effect on normal queries (d = 2.347 vs. control, d = 1.436 vs. RAG) than on edge cases (d = 1.135 vs. control, d = 0.683 vs. RAG). Permutation testing confirmed that the edge-greater hypothesis was not supported (p = 0.987 for pragmatics vs. control).

This finding rules out overfitting to edge cases. Pragmatics do not merely catch exotic failure modes; they improve routine statistical consultation by providing the fitness-for-use context that even straightforward queries benefit from. A normal query about median household income in a large county still benefits from knowing that the five-year estimate is a 60-month average, that the margin of error defines a 90% confidence interval, and that direct comparison to decennial census figures requires methodological adjustment.

The normal-stratum finding should be interpreted with a power caveat: at n = 15, the Wilcoxon test has approximately 0.56 power to detect a d = 0.5 effect. The observed effects (d = 2.347) are large enough to detect at this sample size, but RAG versus control on normal queries (d = 0.458, p = 0.137) was not significant, consistent with underpowering rather than a null effect.

## Pipeline Fidelity

Stage 3 automated verification assessed whether responses accurately reported what Census API tools returned, measuring both auditability (whether claims could be traced to specific API calls) and fidelity (whether traced claims were accurate).

| Condition | Claims | Fidelity | Subst. Fidelity | Error Rate | Auditable |
|-----------|--------|----------|-----------------|------------|-----------|
| Pragmatics | 353 | 91.2% | 99.7% | 0.3% | 29.5% |
| RAG | 355 | 74.6% | 98.9% | 0.8% | 6.2% |
| Control | 253 | 78.3% | 100.0% | 0.0% | 21.8% |

: Stage 3 fidelity verification. Fidelity = (matched + calculation_correct) / total_claims. Substantive fidelity excludes no_source claims. Error rate = (mismatched + calculation_incorrect) / total_claims. Auditable = fully auditable claims / substantive claims. {#tbl-fidelity}

![Stage 3 pipeline fidelity by condition. Substantive fidelity (98.9–100.0%) and error rates (0.0–0.8%) annotated in caption.](assets/figures/F8_fidelity_bars.pdf){#fig-fidelity width=5.0in}

Pragmatics achieved 91.2% fidelity across 353 claims, compared to 74.6% for RAG (355 claims) and 78.3% for control (253 claims). Substantive fidelity (the rate among claims that could be fully verified) was 99.7% for pragmatics, 98.9% for RAG, and 100.0% for control.

The fidelity gap between pragmatics and RAG (16.6 percentage points) reflects a structural difference. Pragmatics provide specific criteria for interpreting data, leading the model to make more precise and verifiable claims. RAG-retrieved chunks provide general context that can lead the model to make claims that are plausible but difficult to verify or subtly misaligned with the specific data returned.

The control condition's lower claim count (253 vs. 353) reflects a pattern where models without methodology support produce vaguer, less specific responses: responses that are harder to verify not because they are wrong but because they are not specific enough to check. This is itself a pragmatically significant finding: ungrounded responses evade accountability by avoiding specificity.

## Determinism

Pragmatic context retrieval was 100% deterministic across all 39 queries, verified through two independent replications producing zero mismatches with the original evaluation run. Given identical topic parameters, the graph traversal returns identical context sets every time. This determinism is a structural property of the retrieval mechanism (graph lookup rather than similarity search), not a statistical regularity of the evaluation.

## Cost and Efficiency

Pragmatics incurred higher per-query token costs than RAG. Mean input tokens per query were 32,929 for pragmatics, 23,746 for RAG, and 5,830 for control, reflecting the structured context delivered alongside data. At Claude Sonnet 4.5 pricing ($3/$15 per million tokens input/output), per-query costs were $0.113 (pragmatics), $0.082 (RAG), and $0.028 (control).

| Metric | Control | RAG | Pragmatics |
|--------|---------|-----|------------|
| **Sonnet 4.5** ($3/$15 per MTok) | | | |
| Cost per query | $0.028 | $0.082 | $0.113 |
| Marginal cost vs control | — | $0.054 | $0.086 |
| CQS per marginal $ | — | 2.83 | **6.28** |
| **Opus 4.6** ($5/$25 per MTok) | | | |
| Cost per query | $0.046 | $0.137 | $0.189 |
| Marginal cost vs control | — | $0.090 | $0.143 |
| CQS per marginal $ | — | 1.70 | 3.77 |
| | | | |
| Cost-effectiveness ratio (Prag/RAG) | — | — | **2.2×** |

: Cost analysis at two pricing tiers. Marginal cost = condition cost minus control baseline. CQS per marginal dollar = CQS improvement over control / marginal cost per query. Cost-effectiveness ratio is constant across pricing tiers. {#tbl-cost}

![Cost-effectiveness: CQS improvement per marginal dollar. Pragmatics is 2.2× more cost-effective than RAG.](assets/figures/F9_cost_effectiveness.pdf){#fig-cost-effectiveness width=4.5in}

However, cost-effectiveness, measured as CQS improvement per marginal dollar spent relative to control, favored pragmatics at 2.2 times the cost-effectiveness of RAG (6.28 vs. 2.83 CQS points per marginal dollar). Pragmatics costs 38% more per query than RAG but delivers disproportionately more quality improvement.

The marginal cost of pragmatic guidance was $0.09 per query at Sonnet pricing and $0.14 at Opus pricing. The full 39-query evaluation battery cost $4.42 at production rates. These figures reflect token costs only; pragmatics requires no vector database, no embedding model, and no retrieval infrastructure at runtime; the pack is a SQLite file served via an API call. The total cost of ownership for pragmatics is dominated by the one-time authoring investment rather than ongoing infrastructure.
