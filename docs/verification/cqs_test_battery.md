# CQS Test Query Battery

**Version:** 0.1 DRAFT
**Date:** 2026-02-12
**Traces To:** H.4–H.11 (Implementation Schedule)
**Design Principle:** 80% edge cases / 20% normal queries (per SRS VR-010)

---

## Battery Design

### Coverage Strategy

Each query is designed to exercise specific pragmatics pack categories and CQS dimensions.
A query may test multiple categories — real-world questions rarely have single-issue problems.

### Difficulty Ratings

- **Normal:** Straightforward query, correct answer is well-defined
- **Tricky:** Requires specific domain knowledge the pragmatics layer provides
- **Trap:** Query that invites a common methodological error

### Query Format

```yaml
id: Unique query identifier
query: The natural language question as a user would ask it
category: Primary test category (H.5–H.11)
pragmatics_exercised: Which pack items should fire
difficulty: normal | tricky | trap
cqs_dimensions_tested: Which CQS dimensions are most relevant
expected_behavior_treatment: What the MCP-augmented response should do
expected_failure_control: What the unaugmented response will likely get wrong
notes: Additional context for scoring
```

---

## H.5: Normal Baseline Queries (20%)

These should be answered well by both control and treatment. They establish a baseline
and verify the treatment path doesn't break simple cases.

```yaml
- id: NORM-001
  query: "What is the total population of California according to the most recent Census data?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D5, D6]
  expected_behavior_treatment: "Retrieves ACS or Decennial, cites table, provides number"
  expected_failure_control: "May answer from training data without citation"
  notes: "Both should get the number right. Difference is traceability."

- id: NORM-002
  query: "What is the median household income in Cook County, Illinois?"
  category: normal
  pragmatics_exercised: [ACS-MOE-001]
  difficulty: normal
  cqs_dimensions_tested: [D1, D3, D5]
  expected_behavior_treatment: "B19013, includes MOE, cites ACS 5-year"
  expected_failure_control: "May give number without MOE or table citation"
  notes: "Cook County is large enough for 1-year. Product selection is informative."

- id: NORM-003
  query: "How many housing units are in Harris County, Texas?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "B25001 or DP04, distinguishes housing units from households"
  expected_failure_control: "May conflate housing units and households"
  notes: "Definitional accuracy test — housing units ≠ households."

- id: NORM-004
  query: "What percentage of people in New York City have a bachelor's degree or higher?"
  category: normal
  pragmatics_exercised: [ACS-MOE-001]
  difficulty: normal
  cqs_dimensions_tested: [D1, D2, D5]
  expected_behavior_treatment: "B15003 or S1501, correct denominator (pop 25+), cites table"
  expected_failure_control: "May use total population as denominator instead of 25+"
  notes: "Denominator test — educational attainment universe is 25+."

- id: NORM-005
  query: "What is the poverty rate in Maricopa County, Arizona?"
  category: normal
  pragmatics_exercised: [ACS-MOE-003]
  difficulty: normal
  cqs_dimensions_tested: [D1, D2, D4, D5]
  expected_behavior_treatment: "S1701 or B17001, correct universe (population for whom poverty status is determined), cites table"
  expected_failure_control: "May not specify the poverty universe exclusion (institutionalized, military, etc.)"
  notes: "Universe test — poverty universe ≠ total population."

- id: NORM-006
  query: "What percentage of households in Miami-Dade County rent rather than own their home?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D2, D5]
  expected_behavior_treatment: "B25003 or DP04, occupied housing units as denominator, cites table"
  expected_failure_control: "Should get this right. May lack table citation."
  notes: "Straightforward tenure question. Both should handle well."

- id: NORM-007
  query: "How many people in King County, Washington are 65 or older?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D5, D6]
  expected_behavior_treatment: "B01001 age breakdown or S0101, cites table and vintage"
  expected_failure_control: "May answer from training data without source"
  notes: "Simple age query. Tests traceability more than methodology."

- id: NORM-008
  query: "What is the unemployment rate in Wayne County, Michigan?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D2, D4, D5]
  expected_behavior_treatment: "Correct denominator (civilian labor force 16+), cites ACS table"
  expected_failure_control: "May get the number but not specify denominator universe"
  notes: "Labor force concept test — denominator is civilian labor force, not total pop."

- id: NORM-009
  query: "What is the median age in Travis County, Texas?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D5]
  expected_behavior_treatment: "B01002 or DP05, simple retrieval with citation"
  expected_failure_control: "Should get this right. Traceability test."
  notes: "No traps. Pure baseline."

- id: NORM-010
  query: "What percentage of people in Hennepin County, Minnesota have health insurance?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "S2701 or B27001, notes civilian noninstitutionalized universe, cites ACS"
  expected_failure_control: "May provide number without universe specification"
  notes: "Health insurance coverage — straightforward but has specific universe."

- id: NORM-011
  query: "How many people in Fulton County, Georgia were born in another country?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "B05002 or DP02, uses 'foreign born' as Census term, cites table"
  expected_failure_control: "May use colloquial terms instead of Census definitions"
  notes: "Definitional test — 'born in another country' = foreign born in Census terminology."

- id: NORM-012
  query: "What is the average household size in Salt Lake County, Utah?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "B25010 or H012, distinguishes average household size from average family size"
  expected_failure_control: "May conflate household and family measures"
  notes: "Mild definitional test — household ≠ family."

- id: NORM-013
  query: "What percentage of workers in Alameda County, California commute by public transit?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D2, D5]
  expected_behavior_treatment: "B08301 or S0801, correct denominator (workers 16+ who did not work from home), cites table"
  expected_failure_control: "May not specify the commute universe correctly"
  notes: "Commuting universe test — denominator excludes WFH workers."

- id: NORM-014
  query: "How many single-mother households are there in Philadelphia County, Pennsylvania?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "B11001 or B09002, uses correct Census terminology ('female householder, no spouse present, with own children'), cites table"
  expected_failure_control: "May use colloquial 'single mother' without mapping to Census concept"
  notes: "Census doesn't use 'single mother' — tests definitional translation."

- id: NORM-015
  query: "What is the median gross rent in Denver County, Colorado?"
  category: normal
  pragmatics_exercised: []
  difficulty: normal
  cqs_dimensions_tested: [D1, D5]
  expected_behavior_treatment: "B25064, simple retrieval with citation"
  expected_failure_control: "Should handle. Traceability test."
  notes: "Pure baseline. No traps."
```

## H.6: Geographic Edge Cases

```yaml
- id: GEO-001
  query: "What is the median household income in Alexandria, Virginia?"
  category: geographic_edge
  pragmatics_exercised: [ACS-IC-001, ACS-IC-002]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "Recognizes Alexandria as independent city (FIPS 51510), not a county subdivision. Retrieves at place/county-equivalent level."
  expected_failure_control: "May look for Alexandria within a county, or confuse with Alexandria, LA or other Alexandrias"
  notes: "Virginia independent cities are county-equivalents. Classic geography trap."

- id: GEO-002
  query: "Compare poverty rates in the Bronx and Manhattan."
  category: geographic_edge
  pragmatics_exercised: [ACS-GEO-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D3, D4, D5]
  expected_behavior_treatment: "Knows Bronx = Bronx County (FIPS 36005), Manhattan = New York County (FIPS 36061). Provides both with MOEs and comparison caveat."
  expected_failure_control: "May struggle with borough-to-county mapping or omit MOE comparison"
  notes: "NYC borough names ≠ county names for Bronx and Manhattan."

- id: GEO-003
  query: "What is the population of Washington?"
  category: geographic_edge
  pragmatics_exercised: [ACS-GEO-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D4]
  expected_behavior_treatment: "Asks for clarification: Washington state, Washington DC, or a city named Washington? Does not guess."
  expected_failure_control: "May default to one interpretation without asking"
  notes: "Ambiguity test. The correct answer is to ask, not to guess."

- id: GEO-004
  query: "What is the median income in Portland?"
  category: geographic_edge
  pragmatics_exercised: [ACS-GEO-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D4]
  expected_behavior_treatment: "Asks for clarification: Portland OR or Portland ME (at minimum). Does not assume."
  expected_failure_control: "Likely defaults to Portland, OR without noting ambiguity"
  notes: "Ambiguity test — multiple valid Portlands."

- id: GEO-005
  query: "What is the homeownership rate in Nashville, Tennessee?"
  category: geographic_edge
  pragmatics_exercised: [ACS-GEO-001, ACS-IC-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D4, D5]
  expected_behavior_treatment: "Recognizes Nashville-Davidson is a consolidated city-county. FIPS 47037 for county, different FIPS for the balance vs full consolidated area. Specifies which geography."
  expected_failure_control: "May not distinguish consolidated city from county or specify which boundary"
  notes: "Consolidated city-county test."

- id: GEO-006
  query: "Give me tract-level median income data for rural Loving County, Texas."
  category: geographic_edge
  pragmatics_exercised: [ACS-POP-001, ACS-MOE-002, ACS-MOE-003, ACS-SAM-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D3, D6]
  expected_behavior_treatment: "Flags that Loving County has ~64 people. Tract-level estimate would be extremely unreliable. Recommends against use or suggests county-level with massive reliability caveat."
  expected_failure_control: "May attempt to retrieve data without reliability warning"
  notes: "Population threshold + reliability trap. This is where informed refusal should score highest."

- id: GEO-007
  query: "What is the unemployment rate in Washington, DC?"
  category: geographic_edge
  pragmatics_exercised: [ACS-GEO-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D2, D4, D5]
  expected_behavior_treatment: "DC is simultaneously a state-equivalent and a place. Specifies FIPS (11001). Uses correct labor force denominator (civilian labor force 16+)."
  expected_failure_control: "May get the number but miss the geographic nuance or denominator specification"
  notes: "DC is state + county + place. Also tests labor force denominator."
```

## H.7: Small-Area Reliability Cases

```yaml
- id: SML-001
  query: "What is the median household income in Kalawao County, Hawaii?"
  category: small_area
  pragmatics_exercised: [ACS-POP-001, ACS-MOE-002, ACS-SUP-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D3, D6]
  expected_behavior_treatment: "Kalawao has ~82 residents. ACS 1-year unavailable. 5-year estimate will have enormous MOE or be suppressed. Should warn about extreme unreliability."
  expected_failure_control: "May present whatever number it finds (or hallucinates) without reliability context"
  notes: "Smallest county in US. Poster child for small-area reliability."

- id: SML-002
  query: "Compare the poverty rates across all census tracts in rural Wyoming."
  category: small_area
  pragmatics_exercised: [ACS-MOE-002, ACS-MOE-003, ACS-MOE-004, ACS-PCL-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D2, D3, D4]
  expected_behavior_treatment: "Warns that tract-level poverty rates in sparse areas will have very high CVs. Cross-tract comparison is especially problematic when MOEs overlap. Notes population controls do not apply at tract level."
  expected_failure_control: "May rank tracts by poverty rate without any reliability assessment"
  notes: "Compound trap: small area + comparison + sparse population."

- id: SML-003
  query: "What is the income of Asian Americans in Boise, Idaho?"
  category: small_area
  pragmatics_exercised: [ACS-POP-001, ACS-MOE-002, ACS-SUP-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D3, D4]
  expected_behavior_treatment: "Boise is large enough for total estimates, but the Asian subpopulation may be small enough that the subgroup estimate has high MOE or is suppressed. Should flag this."
  expected_failure_control: "May provide number without subgroup reliability warning"
  notes: "Subgroup reliability test — geography is fine but subpopulation may be too small."

- id: SML-004
  query: "I need ACS 1-year data for Gallatin County, Montana."
  category: small_area
  pragmatics_exercised: [ACS-POP-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D3]
  expected_behavior_treatment: "Gallatin County is ~120K — above the 65K threshold, so 1-year IS available. Should provide it. Not every small-area query is a trap."
  expected_failure_control: "Should also get this right, but may not explain the threshold logic"
  notes: "False alarm test — verifies system doesn't over-warn. Gallatin is above threshold."
```

## H.8: Temporal Edge Cases

```yaml
- id: TMP-001
  query: "How has median household income in Philadelphia changed from 2010 to 2022?"
  category: temporal
  pragmatics_exercised: [ACS-DOL-001, ACS-CMP-001, ACS-CMP-002]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D2, D3, D4]
  expected_behavior_treatment: "Adjusts for inflation using CPI-U-RS. Notes ACS 5-year periods overlap (2008-2012 vs 2018-2022). Uses Z-test or CI comparison for significance. Warns about comparability across vintages."
  expected_failure_control: "May compare nominal dollars directly. May not flag overlapping periods."
  notes: "Triple trap: inflation + overlapping periods + significance testing."

- id: TMP-002
  query: "Compare the 2019 and 2020 ACS estimates for health insurance coverage in Florida."
  category: temporal
  pragmatics_exercised: [ACS-BIS-001, ACS-CMP-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D3, D4]
  expected_behavior_treatment: "Flags COVID-era disruption. 2020 ACS 1-year experimental estimates were released separately with different methodology. The standard 2020 1-year was NOT released. Must use 5-year or the experimental product with caveats."
  expected_failure_control: "May not know about the 2020 ACS disruption"
  notes: "COVID break-in-series. This is exactly what pragmatics are for."

- id: TMP-003
  query: "Has the percentage of people working from home in Denver increased since 2015?"
  category: temporal
  pragmatics_exercised: [ACS-BIS-001, ACS-DOL-001, ACS-CMP-003]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D3, D4]
  expected_behavior_treatment: "Notes commuting question wording/response options may have changed. COVID created a structural break in WFH patterns. Comparison is descriptively valid but requires noting the behavioral and methodological context."
  expected_failure_control: "May present trend without methodological context"
  notes: "Behavioral break (COVID WFH surge) overlaid on possible questionnaire changes."

- id: TMP-004
  query: "What was the median home value in San Francisco in 2005 dollars?"
  category: temporal
  pragmatics_exercised: [ACS-DOL-001]
  difficulty: tricky
  cqs_dimensions_tested: [D2, D4]
  expected_behavior_treatment: "Notes CPI-U-RS is the standard deflator for Census income/value comparisons. Applies correct adjustment. Notes CPI-U-RS is national, not San Francisco-specific."
  expected_failure_control: "May use wrong deflator or not flag the national-only limitation"
  notes: "Inflation adjustment with CPI-U-RS national limitation."
```

## H.9: Ambiguity Cases

```yaml
- id: AMB-001
  query: "How many families are in poverty in Springfield?"
  category: ambiguity
  pragmatics_exercised: [ACS-GEO-001]
  difficulty: trap
  cqs_dimensions_tested: [D1, D4]
  expected_behavior_treatment: "Asks which Springfield — there are 30+ in the US. Does not guess."
  expected_failure_control: "May default to Springfield, IL or the largest Springfield"
  notes: "Maximum geographic ambiguity."

- id: AMB-002
  query: "What's the income gap between whites and minorities in my area?"
  category: ambiguity
  pragmatics_exercised: []
  difficulty: trap
  cqs_dimensions_tested: [D1, D4]
  expected_behavior_treatment: "Asks: (1) what geography? (2) 'minorities' is not a Census category — which race/ethnicity groups? (3) household or family or per capita income? Multiple ambiguities require clarification."
  expected_failure_control: "May assume a geography and an operationalization of 'minorities'"
  notes: "Multiple simultaneous ambiguities. Good response asks before answering."

- id: AMB-003
  query: "Is the economy better in Texas or California?"
  category: ambiguity
  pragmatics_exercised: []
  difficulty: trap
  cqs_dimensions_tested: [D1, D2, D4]
  expected_behavior_treatment: "Notes 'better economy' is not a Census variable. Asks what specific measures interest the user (income, employment, poverty, GDP). Separates descriptive statistics from causal/evaluative claims."
  expected_failure_control: "May cherry-pick metrics and present them as answering the question"
  notes: "Evaluative question that requires decomposition into measurable concepts."
```

## H.10: Product Mismatch Cases

```yaml
- id: MIS-001
  query: "Give me ACS 1-year estimates for Sioux County, Nebraska."
  category: product_mismatch
  pragmatics_exercised: [ACS-POP-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D3]
  expected_behavior_treatment: "Sioux County has ~1,100 people — well below 65K threshold. ACS 1-year not available. Redirects to 5-year with reliability caveat."
  expected_failure_control: "May attempt the call and return an error, or hallucinate data"
  notes: "Direct product threshold test."

- id: MIS-002
  query: "What does the decennial census say about income levels in Ohio?"
  category: product_mismatch
  pragmatics_exercised: [ACS-PE-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D4]
  expected_behavior_treatment: "Notes the decennial census does not collect income data (since 2010 when the long form was replaced by ACS). Redirects to ACS as the correct source."
  expected_failure_control: "May not know the decennial doesn't collect income"
  notes: "Common misconception that decennial collects everything."

- id: MIS-003
  query: "I need monthly employment data from the ACS."
  category: product_mismatch
  pragmatics_exercised: [ACS-PE-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D4]
  expected_behavior_treatment: "ACS does not produce monthly estimates. Redirects to CPS (monthly labor force survey) or BLS Current Employment Statistics. Notes ACS employment is a period estimate."
  expected_failure_control: "May not know ACS periodicity or may try to provide data"
  notes: "Product confusion — ACS vs CPS for labor force data."
```

## H.11: Persona-Based Query Variants

Same underlying data question, different user sophistication levels.

```yaml
- id: PER-001a
  query: "My 8th grade class is doing a project on our town. How many people live in Bozeman, Montana and is it growing?"
  category: persona_8th_grader
  pragmatics_exercised: [ACS-PE-001, ACS-CMP-003]
  difficulty: normal
  cqs_dimensions_tested: [D1, D3, D5, D6]
  expected_behavior_treatment: "Provides population estimate in accessible language. Explains what ACS is briefly. If comparing years, uses appropriate comparison method but communicates simply."
  expected_failure_control: "Should handle this, but may be overly technical or not cite sources"
  notes: "Accessibility test — can the system adapt to audience?"

- id: PER-001b
  query: "I'm analyzing population trends in Bozeman, MT for a comprehensive plan update. I need the most recent ACS estimates with margins of error, and guidance on comparing to the 2010 baseline."
  category: persona_city_planner
  pragmatics_exercised: [ACS-MOE-001, ACS-CMP-001, ACS-CMP-002, ACS-CMP-003, ACS-DOL-001]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D2, D3, D4, D5]
  expected_behavior_treatment: "Provides specific table/variable, MOEs, significance test for 2010-vs-current comparison. Notes period estimate overlap, recommends non-overlapping periods if possible. Technical depth appropriate for planner."
  expected_failure_control: "May provide data but miss comparison methodology"
  notes: "Same geography, professional audience. Full methodology expected."

- id: PER-001c
  query: "I'm writing a story about whether Bozeman is really 'booming' as people claim. What do the Census numbers actually show, and how confident should I be in those numbers?"
  category: persona_journalist
  pragmatics_exercised: [ACS-MOE-001, ACS-MOE-003, ACS-CMP-003]
  difficulty: tricky
  cqs_dimensions_tested: [D1, D3, D4, D5]
  expected_behavior_treatment: "Provides data with plain-language uncertainty explanation. Explains what MOE means for the claim. Separates statistical evidence from narrative. Notes what the data can and cannot support."
  expected_failure_control: "May provide numbers that support the 'booming' narrative without appropriate uncertainty"
  notes: "Journalist needs accuracy + narrative guidance. Should neither hype nor dismiss."
```

---

## Battery Summary

| Category | Code | Count | Difficulty Mix | Purpose |
|----------|------|-------|----------------|----------|
| Normal baseline | NORM | 15 | 15 normal | No-harm equivalence testing |
| Geographic edge | GEO | 7 | 2 tricky, 3 trap, 2 tricky | Pragmatics value-add |
| Small area | SML | 4 | 2 trap, 1 tricky, 1 tricky | Pragmatics value-add |
| Temporal | TMP | 4 | 3 tricky, 1 trap | Pragmatics value-add |
| Ambiguity | AMB | 3 | 3 trap | Pragmatics value-add |
| Product mismatch | MIS | 3 | 3 tricky | Pragmatics value-add |
| Persona variants | PER | 3 | 1 normal, 2 tricky | Communication adaptation |
| **Total** | | **39** | **16 normal (41%) / 14 tricky (36%) / 9 trap (23%)** |

### Statistical Design Rationale

**Split: 41% normal / 59% edge cases.**

Driven by power analysis, not arbitrary ratio:

- **Edge case stratum (24 queries):** Superiority test (treatment > control). Expected large effect (d≈0.8). Wilcoxon signed-rank at α=0.05, power=0.80 requires ~15 pairs. 24 provides comfortable margin.
- **Normal stratum (15 queries):** Equivalence test (treatment ≈ control, no harm). TOST at α=0.05 with equivalence margin ±1 CQS point ideally wants 25-30, but 15 is sufficient for a preliminary "no degradation" claim with 3 judges per pair providing variance reduction.
- **Total: 39 queries × 2 conditions × 3 judges = 234 judge API calls.** Manageable in one run.

**Analysis plan:** Results reported stratified by category. Primary hypothesis tested on edge cases only. Normal queries reported as equivalence/no-harm analysis separately.

---

## Pragmatics Coverage Check

| Pack Category | Items | Queries That Exercise It |
|---|---|---|
| margin_of_error | ACS-MOE-001–004 | NORM-002, SML-001–003, PER-001b/c, TMP-001 |
| comparison | ACS-CMP-001–003 | TMP-001–003, PER-001b/c, SML-002 |
| dollar_values | ACS-DOL-001 | TMP-001, TMP-004, PER-001b |
| geography | ACS-GEO-001 | GEO-001–007, AMB-001 |
| independent_cities | ACS-IC-001–002 | GEO-001, GEO-005 |
| population_threshold | ACS-POP-001 | GEO-006, SML-001, SML-004, MIS-001 |
| period_estimate | ACS-PE-001 | MIS-002, MIS-003, PER-001a |
| suppression | ACS-SUP-001 | SML-001, SML-003 |
| sampling | ACS-SAM-001 | GEO-006, SML-002 |
| population_controls | ACS-PCL-001 | SML-002 |
| break_in_series | ACS-BIS-001 | TMP-002, TMP-003 |
| residence_rules | ACS-RES-001 | *(not directly tested — add in v0.2)* |
| nonresponse | — | *(not directly tested — add in v0.2)* |
| disclosure_avoidance | ACS-DA-001 | *(not directly tested — add in v0.2)* |
| group_quarters | ACS-GQ-001–002 | *(not directly tested — add in v0.2)* |

**Coverage: 11/16 categories exercised in v0.1. Remaining 5 deferred to v0.2.**

---

## Open Items

- [ ] Convert to machine-readable YAML for harness consumption
- [ ] Add expected CQS score ranges per query for calibration validation
- [ ] Expand persona variants (researcher, advocacy org, general public)
- [ ] Add CPS-specific queries once CPS pack content is expanded
- [ ] Coverage for residence_rules, nonresponse, disclosure_avoidance, group_quarters, geographic_equivalence
