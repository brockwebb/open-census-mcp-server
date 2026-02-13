# Chapter 5: Test Battery Summary

[← Ch. 4](04_data_flows.md) | [README](README.md) | [Ch. 6 →](06_success_criteria.md)

---

Full battery specification: `docs/verification/cqs_test_battery.md`
Machine-readable battery: `src/eval/battery/queries.yaml`

## 5.1 Query Distribution

| Category | Code | Count | Difficulty | Purpose |
|---|---|---|---|---|
| Normal baseline | NORM | 15 | 15 normal | Equivalence testing (no harm) |
| Geographic edge | GEO | 7 | 2 tricky, 5 trap | Treatment effect — geography |
| Small area | SML | 4 | 2 trap, 2 tricky | Treatment effect — reliability |
| Temporal | TMP | 4 | 3 tricky, 1 trap | Treatment effect — time series |
| Ambiguity | AMB | 3 | 3 trap | Treatment effect — disambiguation |
| Product mismatch | MIS | 3 | 3 tricky | Treatment effect — product selection |
| Persona variants | PER | 3 | 1 normal, 2 tricky | Communication adaptation |
| **Total** | | **39** | **16 normal / 14 tricky / 9 trap** | |

**Split rationale (DEC-4B-009):** 41% normal / 59% edge, driven by power analysis for paired comparison.

## 5.2 Expected Behaviors by Category

| Category | Expected Treatment Advantage | Expected Control Failure Mode | Key CQS Dimensions |
|---|---|---|---|
| NORM | Traceability (D5), definitional precision (D4) | Answers from training data, no sources, may use stale numbers | D5, D6 |
| GEO | Correct FIPS resolution, independent city handling | Incorrect geographic assumptions, wrong FIPS | D1, D4, D5 |
| SML | Informed refusal, reliability warnings, CV assessment | Delivers unreliable estimates without caveats | D1, D3 |
| TMP | Period overlap warnings, inflation adjustment, break-in-series flags | Naive year-over-year comparison, no inflation, no COVID caveat | D2, D3, D4 |
| AMB | Asks for clarification, identifies ambiguity | Guesses without acknowledging ambiguity | D1, D4 |
| MIS | Correct product redirect, explains why | Uses wrong product or fabricates data | D1, D6 |
| PER | Adapts communication level to audience | Same response regardless of audience | D4 (communication) |

## 5.3 Key Sentinel Queries

These queries produce maximum differentiation and should be manually inspected regardless of automated scoring:

| Query ID | Why It Matters |
|---|---|
| GEO-006 | Loving County, TX (pop ~64) tract-level. Correct answer is informed refusal. |
| SML-001 | Kalawao County, HI (pop 82). Extreme unreliability. |
| SML-004 | Gallatin County, MT 1-year. False alarm test — should NOT over-warn. |
| TMP-002 | 2019-2020 health insurance. 2020 ACS 1-year not released. Break-in-series. |
| MIS-002 | Decennial for income. Decennial doesn't collect income since 2010. |
| AMB-002 | "Income gap between whites and minorities in my area." Multiple ambiguities. |
