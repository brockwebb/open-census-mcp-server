# Results

<!-- Registry references: S2-001–042, S3-001–012, SA-001–022, EFF-001–008, COST-001–013, DET-001–004 -->

## Overall Consultation Quality

The Friedman test revealed a significant difference across the three conditions (χ²(2, N = 39) = 42.01, p < 0.001). All three pairwise comparisons were significant after Holm-Bonferroni correction.

| Condition | Mean CQS | *n* |
|-----------|----------|-----|
| Pragmatics | 1.528 | 39 |
| RAG | 1.144 | 39 |
| Control | 0.990 | 39 |

: CQS composite scores by condition (D1–D5 mean of per-query medians). {#tbl-cqs-means}

| Comparison | Statistic | *r* | 95% CI | *p* | Eff. *n* |
|------------|-----------|-----|--------|-----|----------|
| Friedman omnibus | χ²(2) = 42.01 | — | — | < .001 | 39 |
| Pragmatics vs Control | Δ = +0.538, d = 1.440 | 0.938 | [0.421, 0.651] | < .001 | 36 |
| Pragmatics vs RAG | Δ = +0.385, d = 0.922 | 0.754 | [0.256, 0.513] | < .001 | 32 |
| RAG vs Control | Δ = +0.154, d = 0.546 | 0.378 | [0.072, 0.244] | .002 | 30 |

: Friedman omnibus and Wilcoxon signed-rank pairwise comparisons with Holm–Bonferroni correction. *r* = rank-biserial correlation from Wilcoxon statistic. Bootstrap 95% CIs (10,000 iterations) on CQS deltas. {#tbl-pairwise}

Pragmatics produced a very large improvement over the control condition (Δ CQS = +0.538, d = 1.440, r = 0.938, 95% CI [0.421, 0.651], p < 0.001) and a large improvement over RAG (Δ CQS = +0.385, d = 0.922, r = 0.754, 95% CI [0.256, 0.513], p < 0.001). RAG produced a medium improvement over control (Δ CQS = +0.154, d = 0.546, r = 0.378, 95% CI [0.072, 0.244], p = 0.0017). The rank-biserial r of 0.938 indicates that pragmatics outperformed control on 94% of query pairs. Mean composite scores were 1.528 (pragmatics), 1.144 (RAG), and 0.990 (control). The ordering was consistent: pragmatics outperformed RAG, which outperformed control, across every level of analysis.

## Per-Dimension Effects

Effect sizes varied substantially across the five quality dimensions (@fig-effect-sizes).

![Cohen's *d* effect sizes by dimension. Vertical lines: *d* = 0.2 (small), 0.5 (medium), 0.8 (large).](assets/figures/F8_effect_sizes_forest.pdf){#fig-effect-sizes width=6.5in}

| Dimension | Prag vs Ctrl *d* | Prag vs RAG *d* | RAG vs Ctrl *d* |
|-----------|-----------------|-----------------|-----------------|
| D1 (Accuracy) | 0.541 | 0.515 | 0.190 |
| D2 (Completeness) | 0.537 | 0.297 | 0.246 |
| D3 (Uncertainty Communication) | **1.353** | **1.040** | 0.417 |
| D4 (Contextual Clarity) | **0.957** | 0.577 | 0.546 |
| D5 (Reproducibility & Traceability) | 0.732 | 0.521 | 0.148 |

: Per-dimension Cohen's *d* effect sizes. Bold indicates *d* > 0.8 (large). {#tbl-dimension-effects}

All five quality dimensions showed significant effects (p < 0.001 for each). The effect sizes for pragmatics versus control varied across dimensions, revealing where expert judgment matters most:

Uncertainty communication (D3) showed the largest effect (d = 1.353 vs. control, d = 1.040 vs. RAG). This dimension captures whether responses appropriately communicate reliability limitations, margins of error, and data fitness: the core of what pragmatics are designed to deliver. The magnitude of this effect is consistent with the mechanism: pragmatics encode specific reliability thresholds, interpretation formulas, and informed-refusal criteria that the model cannot derive from training data or retrieved document chunks.

Clarity of explanation (D4) showed the second-largest effect (d = 0.957 vs. control), while accuracy (D1, d = 0.541), completeness (D2, d = 0.537), and reproducibility (D5, d = 0.732) showed medium to large effects. The consistency across all five dimensions indicates that pragmatics improve the overall quality of statistical consultation rather than optimizing a single aspect.

RAG showed its largest advantage over control on clarity (D4, d = 0.546) and uncertainty (D3, d = 0.417), with smaller effects on accuracy (D1, d = 0.190) and reproducibility (D5, d = 0.148). The pattern suggests that retrieved document chunks provide some contextual value but lack the expert guidance to substantially improve reliability assessment or harm prevention.

## Stratum Analysis: Normal vs. Edge Cases

The evaluation was stratified to test whether pragmatics disproportionately help on edge cases (queries involving small areas, geographic exceptions, temporal comparisons, and ambiguous requests) or whether benefits extend to routine statistical queries.

| Comparison | Normal *d* (*n*=15) | Edge *d* (*n*=24) | Δ*d* (Edge−Normal) | *p* (Edge > Normal) |
|------------|--------------------|--------------------|---------------------|---------------------|
| Prag vs Ctrl | **2.347** | 1.135 | -0.273 | .987 |
| Prag vs RAG | **1.436** | 0.683 | -0.318 | .987 |
| RAG vs Ctrl | 0.458 | 0.590 | +0.044 | .347 |

: Stratum analysis comparing normal (*n*=15) and edge-case (*n*=24) queries. Δ*d* is the delta-of-deltas (edge minus normal mean CQS delta). Mann-Whitney *p* tests whether edge deltas exceed normal deltas. {#tbl-stratum}

Pragmatics showed a *larger* effect on normal queries (d = 2.347 vs. control, d = 1.436 vs. RAG) than on edge cases (d = 1.135 vs. control, d = 0.683 vs. RAG). Permutation testing confirmed that edge cases did not benefit disproportionately (p = 0.987 for pragmatics vs. control).

This finding is inconsistent with an overfitting explanation. Pragmatics do not merely catch exotic failure modes; they improve routine statistical consultation by providing the fitness-for-use context that even straightforward queries benefit from. A normal query about median household income in a large county still benefits from knowing that the five-year estimate is a 60-month average and that the margin of error defines a 90% confidence interval. Direct comparison to decennial census figures requires methodological adjustment that the model cannot infer without guidance.

The normal-stratum finding should be interpreted with a power caveat: at n = 15, the Wilcoxon test has approximately 0.56 power to detect a d = 0.5 effect. The observed effects (d = 2.347) are large enough to detect at this sample size, but RAG versus control on normal queries (d = 0.458, p = 0.137) was not significant, consistent with underpowering rather than a null effect. The between-group comparison uses Mann-Whitney U because the 15 normal and 24 edge-case queries are independent groups. Within each group, per-query deltas are computed from paired conditions (the same query tested under each treatment). The comparison across groups treats those deltas as independent samples.

## Pipeline Fidelity

Stage 3 automated verification assessed whether responses accurately reported what Census API tools returned, measuring both auditability (whether claims could be traced to specific API calls) and fidelity (whether traced claims were accurate).

| Condition | Claims | Fidelity | Subst. Fidelity | Error Rate | Auditable |
|-----------|--------|----------|-----------------|------------|-----------|
| Pragmatics | 353 | 91.2% | 99.7% | 0.3% | 29.5% |
| RAG | 355 | 74.6% | 98.9% | 0.8% | 6.2% |
| Control | 253 | 78.3% | 100.0% | 0.0% | 21.8% |

: Stage 3 fidelity verification. Fidelity = (matched + calculation_correct) / total_claims. Substantive fidelity excludes no_source claims. Error rate = (mismatched + calculation_incorrect) / total_claims. Auditable = fully auditable claims / substantive claims. {#tbl-fidelity}

Pragmatics achieved 91.2% fidelity across 353 claims, compared to 74.6% for RAG (355 claims) and 78.3% for control (253 claims). Substantive fidelity (the rate among claims that could be fully verified) was high across all conditions: 99.7% for pragmatics, 98.9% for RAG, and 100.0% for control. Control's perfect rate reflects a smaller denominator, not greater accuracy. With the fewest total claims and the lowest auditability (21.8%), control responses avoided errors by avoiding specificity. Pragmatics made more claims than control, with higher auditability, and still achieved near-perfect substantive fidelity: more specific, more verifiable, and comparably accurate. The control condition's lower claim count (253 vs. 353) illustrates the inverse: without methodology support, models produce vaguer responses that are harder to verify not because they are wrong but because they are not specific enough to check. Vagueness is not accuracy; it is the absence of accountability.

The fidelity gap between pragmatics and RAG (16.6 percentage points) reflects a structural difference. Pragmatics provide specific criteria for interpreting data, leading the model to make more precise and verifiable claims. RAG-retrieved chunks provide general context that can lead the model to make claims that are plausible but difficult to verify or subtly misaligned with the specific data returned.

Pragmatics' middling auditability (29.5%) despite its highest fidelity reflects a complementary pattern: structured expert judgment encourages conditional and interpretive claims (e.g., "unreliable if CV exceeds 40%") that are methodologically sound but cannot be traced to a specific API return value. High fidelity with moderate auditability indicates precise claims grounded in methodology rather than in raw data alone.

## Determinism

Pragmatic context retrieval was 100% deterministic across all 39 queries, verified through two independent replications producing zero mismatches with the original evaluation run. Given identical topic parameters, the SQLite lookup returns identical context sets every time. This determinism is a structural property of the retrieval mechanism (SQLite lookup rather than similarity search), not a statistical regularity of the evaluation.

## Cost and Efficiency

Pragmatics costs more per query than RAG but delivers substantially more quality improvement per dollar spent. Beyond per-query economics, the total cost of ownership favors pragmatics: no vector database, no embedding model, and no index maintenance at runtime.

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

Cost-effectiveness, measured as quality improvement per marginal dollar relative to control, favored pragmatics at 2.2 times the cost-effectiveness of RAG (6.28 vs. 2.83 quality points per marginal dollar). Pragmatics costs 38% more per query than RAG but delivers disproportionately more quality improvement. The 2.2x ratio assumes quality points are linearly valued. In practice, moving a response from harmful to adequate likely has greater utility than moving from adequate to excellent, so the ratio should be read as a relative comparison rather than a precise welfare measure.

These figures reflect token costs only. The runtime infrastructure is a SQLite file served via an API call, and the full 39-query evaluation cost $4.42 at production rates. The total cost of ownership is dominated by the one-time authoring investment, not ongoing infrastructure.
