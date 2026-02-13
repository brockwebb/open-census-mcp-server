# Chapter 6: Success Criteria

[← Ch. 5](05_battery_summary.md) | [README](README.md) | [Ch. 7 →](07_risk_register.md)

---

## 6.1 Stage 1 (Response Generation)

| Criterion | Threshold | Measurement |
|---|---|---|
| Battery completion | 39/39 queries with both conditions | Count in JSONL |
| Treatment tool usage | ≥95% of treatment responses include ≥1 tool call | `tool_calls` field |
| Control tool absence | 0% of control responses include tool calls | `tool_calls` field |
| No crashes | 0 unhandled exceptions | Harness log |
| Latency | Treatment median <30s, control median <10s | `total_latency_ms` |

## 6.2 Stage 2 (Judge Scoring)

| Criterion | Threshold | Measurement |
|---|---|---|
| Judge completion | 117/117 judgments (39 × 3) | Count in scores JSONL |
| Inter-rater agreement | Krippendorff's α ≥ 0.4 (moderate) per dimension | α ordinal calculation |
| No dimension-level floor/ceiling | No dimension where all scores are 0 or all are 2 | Score distribution |
| Position bias | A/B assignment effect < 0.5 CQS points | Mean difference by position |

## 6.3 Stage 3 (Treatment Effect)

| Criterion | Threshold | Measurement |
|---|---|---|
| Edge case superiority | Treatment > Control on edge cases, p < 0.05 (Wilcoxon) | Paired signed-rank test |
| Normal equivalence | \|Treatment - Control\| < 1 CQS point on normal queries (TOST) | Two one-sided tests |
| D6 gate | Control D6=0 rate > Treatment D6=0 rate | Gate failure frequency |
| Dimension-specific effect | ≥2 dimensions show significant (p<0.05) treatment advantage | Per-dimension Wilcoxon |

## 6.4 What Constitutes Failure

These outcomes would invalidate or undermine the evaluation:

- If treatment scores **lower** than control on normal queries → pragmatics cause harm
- If inter-rater α < 0.2 → rubric is unreliable, cannot draw conclusions
- If judge panel shows >1 CQS point vendor bias → scoring contaminated
- If >20% of treatment responses fail to use tools → agent loop broken
- If treatment and control are statistically indistinguishable on edge cases → pragmatics don't help where they should

Each failure mode has a different implication. "Pragmatics cause harm" kills the thesis. "Rubric unreliable" means redesign the rubric and re-run. "Agent loop broken" means fix the harness and re-run. The distinction matters for how we respond to negative results.
