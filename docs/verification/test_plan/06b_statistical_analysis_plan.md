# Chapter 6B: Statistical Analysis Plan

[← Ch. 6](06_success_criteria.md) | [README](README.md) | [Ch. 7 →](07_risk_register.md)

---

## 6B.1 Purpose

This chapter specifies every statistical test, bias diagnostic, and effect measure
to be computed from the judge scoring output. The governing principle is
**collect everything, analyze selectively** — computation is cheap, re-running
pipelines with API costs is not.

All metrics below are computed and stored. Reporting decisions (what goes in the
paper vs. supplementary materials) are made after seeing the data.

---

## 6B.2 Data Collection Requirements

### 6B.2.1 Per-Judge-Call Record

Every judge invocation must record:

| Field | Type | Purpose |
|---|---|---|
| `query_id` | str | Links to battery |
| `judge_model` | str | Exact model string |
| `judge_vendor` | str | anthropic / openai / google |
| `presentation_order` | str | "control_first" or "treatment_first" |
| `scores_response_a` | dict | D1-D6 scores for Response A |
| `scores_response_b` | dict | D1-D6 scores for Response B |
| `preference` | str | "A" / "B" / "tie" |
| `confidence` | dict | Per-dimension confidence (1-5 scale) |
| `reasoning` | str | Full judge reasoning text |
| `response_a_label` | str | "control" or "treatment" (for analysis, not shown to judge) |
| `response_b_label` | str | "control" or "treatment" |
| `latency_ms` | int | Judge call latency |
| `input_tokens` | int | Prompt tokens consumed |
| `output_tokens` | int | Judge response tokens |
| `timestamp` | str | ISO 8601 |
| `run_id` | str | Batch run identifier |

### 6B.2.2 Position Bias Subset

For a subset of queries (minimum 10, ideally all 39), run each judge in
**both orderings** (control-first and treatment-first). This doubles the
judge calls for this subset but enables direct measurement of position bias.

Total judge calls budget:
- Base: 39 queries × 3 judges = 117 calls
- Position bias (both orderings, all 39): 39 × 3 × 2 = 234 calls
- Test-retest (10-query subset, second run): 10 × 3 = 30 calls
- **Total: 264 calls**

### 6B.2.3 Derived Fields (computed post-hoc)

| Field | Derivation |
|---|---|
| `control_total_cqs` | Sum of D1-D6 for control response |
| `treatment_total_cqs` | Sum of D1-D6 for treatment response |
| `cqs_delta` | treatment_total - control_total |
| `control_char_count` | len(control response text) |
| `treatment_char_count` | len(treatment response text) |
| `char_ratio` | treatment_chars / control_chars |
| `gate_failure_control` | True if control D6 = 0 |
| `gate_failure_treatment` | True if treatment D6 = 0 |

---

## 6B.3 Inter-Rater Agreement

### 6B.3.1 Primary: Krippendorff's Alpha (ordinal)

Computed per dimension across all 3 judges. Uses ordinal scale (0 < 1 < 2)
which is appropriate for the CQS scale where distances are meaningful.

| Interpretation | α range |
|---|---|
| Poor | < 0.2 |
| Fair | 0.2 – 0.4 |
| Moderate | 0.4 – 0.6 |
| Substantial | 0.6 – 0.8 |
| Near-perfect | > 0.8 |

**Threshold:** α ≥ 0.4 (moderate) per dimension. If any dimension < 0.2,
that dimension's scores are unreliable and should be reported but flagged.

### 6B.3.2 Secondary: Fleiss' Kappa

Multi-rater agreement treating scores as nominal categories. Less appropriate
than α-ordinal for our scale but widely recognized. Report for comparability
with harmonization study (κ = 0.611 rater tier, 0.843 arbitrator tier).

### 6B.3.3 Pairwise: Cohen's Kappa

All 3 pairs (Claude-GPT, Claude-Gemini, GPT-Gemini). Identifies which judge
pairs agree most/least. If one judge is an outlier, this reveals it.

### 6B.3.4 Percent Agreement

Simple agreement rate per dimension and overall. Report alongside κ/α for
context (κ can be misleadingly low with skewed distributions).

---

## 6B.4 Bias Diagnostics

### 6B.4.1 Position Bias

**Method:** For each query scored in both orderings, compute:
- `swap_consistency`: Does the judge give the same preference regardless of order?
- `position_effect`: Mean score difference (Response A score - Response B score)
  across all calls, regardless of which is treatment. If > 0, first-position bias.

**Metric:** Swap consistency rate (% of queries where preference is invariant
to ordering). Per Zheng et al. 2023, position bias is significant when
consistency < 80%.

**Statistical test:** Paired t-test or Wilcoxon on per-dimension scores between
orderings for the same query-judge pair.

### 6B.4.2 Verbosity Bias

**Method:** Correlate response length (char count and token count) with
CQS total score across all judge calls.

**Metrics:**
- Spearman's ρ between `response_char_count` and `total_cqs` (across both conditions)
- Partial correlation controlling for condition (control/treatment)
- Regression: `CQS ~ length + condition + length:condition`

**Interpretation:** If ρ > 0.7, judges are rewarding length. If the interaction
term (length:condition) is significant, the length effect differs by condition —
which would mean treatment is getting a boost from verbosity, not content.

### 6B.4.3 Self-Enhancement / Vendor Bias

**Method:** For each judge, compute mean CQS awarded to control and treatment
responses. Then compare across judges to detect systematic vendor-specific inflation.

**Metrics:**
- Per-judge: Mean treatment CQS, mean control CQS, mean delta
- Self-vendor indicator: Does Claude-judge rate treatment (generated by Claude)
  higher than other judges rate treatment?
- Cross-vendor comparison table:

| Judge | Mean Ctrl CQS | Mean Treat CQS | Δ | Treat Preference % |
|---|---|---|---|---|
| Claude Opus | | | | |
| GPT-5.2 | | | | |
| Gemini 3 Pro | | | | |

**Statistical test:** Kruskal-Wallis on treatment CQS scores grouped by judge
vendor. If p < 0.05, at least one judge scores systematically differently.

**Self-enhancement ratio:** Claude_treatment_mean / non_Claude_treatment_mean.
Values > 1.05 suggest self-enhancement bias.

### 6B.4.4 Leniency / Severity Bias

**Method:** Some judges may be systematically lenient or harsh across all responses.

**Metric:** Per-judge mean CQS across both conditions. Report the range.
If one judge's mean is > 1.5 CQS points above or below the others, flag as
leniency/severity bias.

---

## 6B.5 Treatment Effect Analysis

### 6B.5.1 Primary: Paired Wilcoxon Signed-Rank Test

Paired by query_id. Tests whether treatment CQS differs from control CQS.
Non-parametric (appropriate for ordinal scale, N=39).

Computed for:
- Total CQS (0-12)
- Each dimension D1-D6 individually
- Query subgroups (normal vs edge)

### 6B.5.2 Effect Size: Cohen's d (paired)

`d = mean(Δ) / sd(Δ)` where Δ = treatment_cqs - control_cqs per query.

| Interpretation | d |
|---|---|
| Small | 0.2 |
| Medium | 0.5 |
| Large | 0.8 |

Also compute rank-biserial correlation r as a non-parametric alternative.

### 6B.5.3 Subgroup Analysis

Split by `difficulty` (normal / tricky / trap):
- Normal queries: expect small or no treatment effect (TOST equivalence test)
- Tricky queries: expect moderate treatment advantage
- Trap queries: expect large treatment advantage

Split by `category`:
- Per-category mean delta and significance test
- Identifies which failure modes pragmatics most effectively addresses

### 6B.5.4 TOST Equivalence Testing

For normal queries where we hypothesize no treatment effect,
Two One-Sided Tests (TOST) with equivalence margin of ±1 CQS point.
If TOST p < 0.05, we can claim treatment and control are equivalent on
easy queries (pragmatics don't hurt).

### 6B.5.5 D6 Gate Analysis

- Proportion of D6=0 (gate failure) in control vs treatment
- McNemar's test for paired proportions
- If treatment has significantly fewer gate failures, this is a key finding
  about grounding preventing hallucination

---

## 6B.6 Internal Consistency / Reliability

### 6B.6.1 Test-Retest Reliability

Run 10-query subset through each judge twice (same prompt, different API call).
Compute ICC (intraclass correlation coefficient, two-way random, absolute agreement)
per dimension and total CQS.

| Interpretation | ICC |
|---|---|
| Poor | < 0.5 |
| Moderate | 0.5 – 0.75 |
| Good | 0.75 – 0.9 |
| Excellent | > 0.9 |

### 6B.6.2 Confidence Calibration

If judges provide per-dimension confidence (1-5 scale):
- Compute correlation between confidence and agreement with majority vote
- High confidence should predict agreement; low confidence should predict disagreement
- If inverse or null relationship, confidence scores are uninformative

### 6B.6.3 Cronbach's Alpha (internal consistency of CQS dimensions)

Treat D1-D6 as items on a 6-item scale. Compute Cronbach's α to assess
whether the dimensions measure a coherent underlying construct.

| Interpretation | α |
|---|---|
| Unacceptable | < 0.5 |
| Poor | 0.5 – 0.6 |
| Questionable | 0.6 – 0.7 |
| Acceptable | 0.7 – 0.8 |
| Good | > 0.8 |

Note: Very high α (> 0.95) would suggest dimension redundancy — the 6
dimensions may be measuring the same thing with different labels.

---

## 6B.7 Human Calibration Metrics

When human scoring is available from the calibration packet:

### 6B.7.1 Judge-Human Agreement

- Cohen's κ per dimension: each judge vs. human expert
- ICC between each judge and human for total CQS
- Identify which judge most closely matches human expert judgment

### 6B.7.2 Systematic Disagreement Patterns

- Where judges disagree with humans, is the pattern systematic?
- Do judges consistently over-score or under-score specific dimensions?
- Plot per-dimension: human score vs. judge score (scatter + regression line)

---

## 6B.8 Summary Metrics Table

For the paper, the minimum reporting set:

| Metric | Purpose | Section |
|---|---|---|
| Krippendorff's α per dimension | Inter-rater reliability | 6B.3.1 |
| Position swap consistency % | Position bias magnitude | 6B.4.1 |
| Length-CQS Spearman ρ | Verbosity bias magnitude | 6B.4.2 |
| Self-enhancement ratio | Vendor bias magnitude | 6B.4.3 |
| Wilcoxon p (edge cases) | Treatment effect significance | 6B.5.1 |
| Cohen's d (edge cases) | Treatment effect size | 6B.5.2 |
| TOST p (normal queries) | Equivalence on easy queries | 6B.5.4 |
| McNemar p (D6 gate) | Grounding prevents hallucination | 6B.5.5 |
| ICC test-retest | Judge reliability | 6B.6.1 |
| Cronbach's α | CQS internal consistency | 6B.6.3 |

Everything else is supplementary / diagnostic.

---

## 6B.9 Analysis Scripts Specification

All analysis code must:
1. Read from the judge scoring JSONL (single input file)
2. Output all metrics to a structured JSON report
3. Generate publication-ready tables (LaTeX and Markdown)
4. Generate diagnostic plots (saved as PNG/SVG)
5. Be deterministic (seeded where applicable)
6. Run without modification after judge scoring completes
