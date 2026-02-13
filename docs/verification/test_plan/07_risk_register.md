# Chapter 7: Risk Register

[← Ch. 6](06_success_criteria.md) | [README](README.md) | [Ch. 8 →](08_execution_procedure.md)

---

## 7.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Census API downtime | Blocks treatment path | Low | Retry with backoff; run during business hours EST |
| Census API rate limit | Slows treatment path | Medium | Sequential queries (not parallel); ~78 API calls is well within limits |
| MCP server crash mid-battery | Loses current query | Low | Resume capability in harness; JSONL checkpointing |
| Claude API rate limit | Blocks both paths | Low | Sequential; 78 calls over ~20 min is light load |
| Model refusal on sensitive queries | Missing data for some queries | Low | No queries involve sensitive content |
| Agent loop infinite cycling | Hangs on one query | Low | Max 5 tool rounds safety limit |
| 2024 ACS API endpoint instability | Stale or missing data | Low | Verified endpoint live on 2026-02-12 (both acs5 and acs1) |

## 7.2 Methodological Risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Stale pack content | Pragmatics miss new guidance | Medium | Accepted for v0.1; packs represent 2020 ACS handbook + 2024 D&M |
| Judge model API changes | Breaks Stage 2 | Medium | Pin exact model strings; build Stage 2 close to execution |
| Insufficient power for equivalence test | Cannot claim "no harm" | Medium | 15 normal queries is minimum viable; acknowledged limitation in paper |
| Position bias in judging | Inflates one condition | Medium | A/B randomization per query; measure and report bias magnitude |
| Vendor bias in judging | One judge family systematically favors treatment | Medium | Three-family panel; test for judge×condition interaction |
| Non-determinism between runs | Results don't replicate exactly | Certain | Accepted; protocol uses statistical aggregation, not exact match |
