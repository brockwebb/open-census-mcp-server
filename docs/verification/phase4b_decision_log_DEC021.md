# DEC-4B-021: Judge Pass Count and Statistical Power

**Date:** 2026-02-13
**Context:** Determining how many judge passes to run within Gemini 3 Pro's 250 calls/day rate limit. Each pass = 39 queries × 1 ordering. Budget allows up to 6 passes per judge per day (234 calls).

## Power Analysis

### Primary Test: Paired Wilcoxon Signed-Rank (N=39)

| Effect size d | Power | Detectable Δ (sd=2) | Detectable Δ (sd=3) |
|---|---|---|---|
| 0.3 (small) | 0.55 | 0.6 CQS pts | 0.9 CQS pts |
| 0.4 | 0.77 | 0.8 pts | 1.2 pts |
| 0.5 (medium) | 0.91 | 1.0 pts | 1.5 pts |
| 0.8 (large) | 0.999 | 1.6 pts | 2.4 pts |

### Subgroup Power (the real constraint)

| Subgroup | N | d=0.5 power | d=0.8 power |
|---|---|---|---|
| All queries | 39 | 0.91 | 0.999 |
| Edge cases | 23 | 0.72 | 0.975 |
| Normal queries | 16 | 0.56 | 0.90 |
| Traps only | 11 | 0.41 | 0.75 |

### Diminishing Returns of Additional Passes

With noise/signal ratio = 1.0 (conservative assumption):

| Passes | Measurements/query | Effective d | Power (N=39) | Power (N=23) | Marginal gain |
|---|---|---|---|---|---|
| 2 | 6 | 0.463 | 0.87 | 0.68 | — |
| 4 | 12 | 0.480 | 0.89 | 0.70 | +0.02 |
| 6 | 18 | 0.487 | 0.90 | 0.71 | +0.01 |
| 8 | 24 | 0.490 | 0.91 | 0.72 | +0.005 |
| 12 | 36 | 0.493 | 0.90 | 0.71 | -0.002 |

**Key insight:** Additional passes reduce measurement error but do not increase the number of independent observations. The bottleneck is N=39 queries, not judge noise. Going from 6 to 12 passes buys ~1% power — not worth a second day of API calls.

## Decision

**6 passes per judge (234 calls/judge, 702 total), single day execution.**

| Pass | Ordering | Purpose |
|---|---|---|
| 1 | control_first | Base scoring |
| 2 | treatment_first | Position bias measurement |
| 3 | control_first | Test-retest #1 |
| 4 | treatment_first | Test-retest #1 × position |
| 5 | control_first | Test-retest #2 (confidence intervals) |
| 6 | treatment_first | Test-retest #2 × position (CIs) |

### What this enables
- Position bias: full battery, both orderings, 3 replications each
- Test-retest ICC: 6 measurements per query per judge (3 per ordering)
- Per-query confidence intervals: bootstrappable from 18 measurements (3 judges × 6 passes)
- Google position bias reproduction: direct comparison to FedSurvConceptMapper finding
- Split-half reliability: can split 6 passes into two groups of 3

### What this does NOT fix
- Trap-query subgroup (N=11) is underpowered at d=0.5 (power=0.41)
- Normal-query subgroup (N=16) is underpowered at d=0.5 (power=0.56)
- If subgroup effects matter, **add more queries** in a future battery, don't add passes

### Rate limit compliance
- Gemini 3 Pro hard limit: 250/day
- Our usage: 234/day (93.6% utilization)
- Headroom: 16 calls for retries on parse failures

## Trade-off
More passes vs. more queries. Passes reduce noise; queries increase statistical power. At N=39, we are noise-limited only for the overall comparison. For subgroup analysis, we are sample-size-limited. Future work should expand the battery (especially edge cases and traps) rather than increase passes.

> "Model stochasticity is a parameter to manage; system nondeterminism is a failure mode to control." — B. Webb

The 6-pass design manages judge stochasticity (measurement noise) while accepting the fixed N=39 as a known limitation documented for future improvement.
