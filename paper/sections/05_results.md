# Section 5: Results

<!-- Registry references: S2-001–042, S3-001–012, SA-001–022, EFF-001–008, COST-001–013, DET-001–004 -->

## 5.1 Overall Consultation Quality

The Friedman test revealed a significant omnibus difference across the three conditions (χ²(2, N = 39) = 42.01, p < 0.001). All three pairwise comparisons were significant after Holm-Bonferroni correction.

> **[INSERT TABLE T1: CQS composite scores by condition with bootstrap 95% CIs]**

> **[INSERT TABLE T2: Friedman omnibus + Wilcoxon pairwise post-hoc with Holm-Bonferroni correction]**

Pragmatics produced a very large improvement over the control condition (Δ CQS = +0.539, Cohen's d = 1.440, 95% CI [0.421, 0.651], p < 0.001) and a large improvement over RAG (Δ CQS = +0.385, d = 0.922, 95% CI [0.256, 0.513], p < 0.001). RAG produced a medium improvement over control (Δ CQS = +0.154, d = 0.546, 95% CI [0.072, 0.244], p = 0.0017). Mean composite scores were 1.528 (pragmatics), 1.144 (RAG), and 0.990 (control).

The ordering was consistent: pragmatics outperformed RAG, which outperformed control, across every level of analysis.

## 5.2 Per-Dimension Effects

> **[INSERT FIGURE F7: Cohen's d effect sizes by dimension — forest plot showing all comparisons × 5 dimensions]**

> **[INSERT TABLE T3: Per-dimension effect sizes (d values) for all 3 comparisons × 5 dimensions]**

All five quality dimensions showed significant omnibus effects (p < 0.001 for each). The effect sizes for pragmatics versus control varied across dimensions, revealing where expert judgment matters most:

Uncertainty communication (D3) showed the largest effect (d = 1.353 vs. control, d = 1.040 vs. RAG). This dimension captures whether responses appropriately communicate reliability limitations, margins of error, and data fitness — the core of what pragmatics are designed to deliver. The magnitude of this effect is consistent with the mechanism: pragmatic items encode specific reliability thresholds, interpretation formulas, and informed-refusal criteria that the model cannot derive from training data or retrieved document chunks.

Clarity of explanation (D4) showed the second-largest effect (d = 0.957 vs. control). Accuracy (D1, d = 0.541), completeness (D2, d = 0.537), and harm avoidance (D5, d = 0.732) showed medium to large effects. The consistency across all five dimensions indicates that pragmatics improve the overall quality of statistical consultation rather than optimizing a single aspect.

RAG showed its largest advantage over control on clarity (D4, d = 0.546) and uncertainty (D3, d = 0.417), with smaller effects on accuracy (D1, d = 0.190) and harm avoidance (D5, d = 0.148). The pattern suggests that retrieved document chunks provide some contextual value but lack the precision to substantially improve reliability assessment or harm prevention.

## 5.3 Stratum Analysis: Normal vs. Edge Cases

The evaluation was stratified to test whether pragmatics disproportionately help on edge cases — queries involving small areas, geographic exceptions, temporal comparisons, and ambiguous requests — or whether benefits extend to routine statistical queries.

> **[INSERT TABLE T4: Stratum analysis — normal vs edge effect sizes for all 3 comparisons]**

The results contradicted the initial hypothesis. Pragmatics showed a *larger* effect on normal queries (d = 2.347 vs. control, d = 1.436 vs. RAG) than on edge cases (d = 1.135 vs. control, d = 0.683 vs. RAG). Permutation testing confirmed that the edge-greater hypothesis was not supported (p = 0.987 for pragmatics vs. control).

This finding rules out overfitting to edge cases. Pragmatics do not merely catch exotic failure modes — they improve routine statistical consultation by providing the fitness-for-use context that even straightforward queries benefit from. A normal query about median household income in a large county still benefits from knowing that the five-year estimate is a 60-month average, that the margin of error defines a 90% confidence interval, and that direct comparison to decennial census figures requires methodological adjustment.

The normal-stratum finding should be interpreted with a power caveat: at n = 15, the Wilcoxon test has approximately 0.56 power to detect a d = 0.5 effect. The observed effects (d = 2.347) are large enough to detect at this sample size, but RAG versus control on normal queries (d = 0.458, p = 0.137) was not significant — consistent with underpowering rather than a null effect.

## 5.4 Pipeline Fidelity

Stage 3 automated verification assessed whether responses accurately reported what Census API tools returned, measuring both auditability (whether claims could be traced to specific API calls) and fidelity (whether traced claims were accurate).

> **[INSERT TABLE T5: Pipeline fidelity — claims count, auditability %, substantive fidelity % by condition]**

> **[INSERT FIGURE F8: Fidelity scores by condition — bar chart]**

Pragmatics achieved 91.2% fidelity across 353 claims, compared to 74.6% for RAG (355 claims) and 78.3% for control (253 claims). Substantive fidelity — the rate among claims that could be fully verified — was 99.7% for pragmatics, 98.9% for RAG, and 100.0% for control.

The fidelity gap between pragmatics and RAG (16.6 percentage points) reflects a structural difference. Pragmatic items provide specific criteria for interpreting data, leading the model to make more precise and verifiable claims. RAG-retrieved chunks provide general context that can lead the model to make claims that are plausible but difficult to verify or subtly misaligned with the specific data returned.

The control condition's lower claim count (253 vs. 353) reflects a pattern where models without methodology support produce vaguer, less specific responses — responses that are harder to verify not because they are wrong but because they are not specific enough to check. This is itself a pragmatically significant finding: ungrounded responses evade accountability by avoiding specificity.

## 5.5 Determinism

Pragmatic context retrieval was 100% deterministic across all 39 queries, verified through two independent replications producing zero mismatches with the original evaluation run. Given identical topic parameters, the graph traversal returns identical context sets every time. This determinism is a structural property of the retrieval mechanism — graph lookup rather than similarity search — not a statistical regularity of the evaluation.

## 5.6 Cost and Efficiency

Pragmatics incurred higher per-query token costs than RAG. Mean input tokens per query were 32,929 for pragmatics, 23,746 for RAG, and 5,830 for control — reflecting the structured context delivered alongside data. At Claude Sonnet 4.5 pricing ($3/$15 per million tokens input/output), per-query costs were $0.113 (pragmatics), $0.082 (RAG), and $0.028 (control).

> **[INSERT TABLE T6: Cost per query by condition and model tier (Sonnet/Opus) with cost-effectiveness ratios]**

> **[INSERT FIGURE F9: Cost-effectiveness — CQS improvement per marginal dollar by condition]**

However, cost-effectiveness — measured as CQS improvement per marginal dollar spent relative to control — favored pragmatics at 2.2 times the cost-effectiveness of RAG (6.28 vs. 2.83 CQS points per marginal dollar). Pragmatics costs 38% more per query than RAG but delivers disproportionately more quality improvement.

The marginal cost of pragmatic guidance was $0.09 per query at Sonnet pricing and $0.14 at Opus pricing. The full 39-query evaluation battery cost $4.42 at production rates. These figures reflect token costs only; pragmatics requires no vector database, no embedding model, and no retrieval infrastructure at runtime — the pack is a SQLite file served via an API call. The total cost of ownership for pragmatics is dominated by the one-time authoring investment rather than ongoing infrastructure.
