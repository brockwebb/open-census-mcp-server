# Appendices

## Appendix A: Complete Test Battery

The full 39-query test battery. Source: `src/eval/battery/queries.yaml`. **Distribution:** 15 standard queries (category `normal`) and 24 edge-case queries across 7 edge categories.

| # | Query Text | Category | Difficulty |
|---|-----------|----------|------------|
| 1 | What is the total population of California according to the most recent Census data? | normal | normal |
| 2 | What is the median household income in Cook County, Illinois? | normal | normal |
| 3 | How many housing units are in Harris County, Texas? | normal | normal |
| 4 | What percentage of people in New York City have a bachelor's degree or higher? | normal | normal |
| 5 | What is the poverty rate in Maricopa County, Arizona? | normal | normal |
| 6 | What percentage of households in Miami-Dade County rent rather than own their home? | normal | normal |
| 7 | How many people in King County, Washington are 65 or older? | normal | normal |
| 8 | What is the unemployment rate in Wayne County, Michigan? | normal | normal |
| 9 | What is the median age in Travis County, Texas? | normal | normal |
| 10 | What percentage of people in Hennepin County, Minnesota have health insurance? | normal | normal |
| 11 | How many people in Fulton County, Georgia were born in another country? | normal | normal |
| 12 | What is the average household size in Salt Lake County, Utah? | normal | normal |
| 13 | What percentage of workers in Alameda County, California commute by public transit? | normal | normal |
| 14 | How many single-mother households are there in Philadelphia County, Pennsylvania? | normal | normal |
| 15 | What is the median gross rent in Denver County, Colorado? | normal | normal |
| 16 | What is the population of Washington? | geographic_edge | trap |
| 17 | What is the median income in Portland? | geographic_edge | trap |
| 18 | Give me tract-level median income data for rural Loving County, Texas. | geographic_edge | trap |
| 19 | What is the median household income in Alexandria, Virginia? | geographic_edge | tricky |
| 20 | Compare poverty rates in the Bronx and Manhattan. | geographic_edge | tricky |
| 21 | What is the homeownership rate in Nashville, Tennessee? | geographic_edge | tricky |
| 22 | What is the unemployment rate in Washington, DC? | geographic_edge | tricky |
| 23 | What is the median household income in Kalawao County, Hawaii? | small_area | trap |
| 24 | Compare the poverty rates across all census tracts in rural Wyoming. | small_area | trap |
| 25 | What is the income of Asian Americans in Boise, Idaho? | small_area | tricky |
| 26 | I need ACS 1-year data for Gallatin County, Montana. | small_area | tricky |
| 27 | Compare the 2019 and 2020 ACS estimates for health insurance coverage in Florida. | temporal | trap |
| 28 | How has median household income in Philadelphia changed from 2010 to 2022? | temporal | tricky |
| 29 | Has the percentage of people working from home in Denver increased since 2015? | temporal | tricky |
| 30 | What was the median home value in San Francisco in 2005 dollars? | temporal | tricky |
| 31 | How many families are in poverty in Springfield? | ambiguity | trap |
| 32 | What's the income gap between whites and minorities in my area? | ambiguity | trap |
| 33 | Is the economy better in Texas or California? | ambiguity | trap |
| 34 | Give me ACS 1-year estimates for Sioux County, Nebraska. | product_mismatch | tricky |
| 35 | What does the decennial census say about income levels in Ohio? | product_mismatch | tricky |
| 36 | I need monthly employment data from the ACS. | product_mismatch | tricky |
| 37 | My 8th grade class is doing a project on our town. How many people live in Bozeman, Montana and is it growing? | persona_8th_grader | normal |
| 38 | I'm analyzing population trends in Bozeman, MT for a comprehensive plan update. I need the most recent ACS estimates with margins of error, and guidance on comparing to the 2010 baseline. | persona_city_planner | tricky |
| 39 | I'm writing a story about whether Bozeman is really 'booming' as people claim. What do the Census numbers actually show, and how confident should I be in those numbers? | persona_journalist | tricky |

**Difficulty key:** `normal` = standard query with clear answer; `tricky` = requires methodological care; `trap` = contains a latent error, ambiguity, or fitness-for-use failure that an uninformed response would miss.

---

## Appendix B: Consultation Quality Score (CQS) Rubric

The CQS rubric specifies five quality dimensions (D1–D5), each scored 0–2. Full specification is available at `docs/verification/cqs_rubric_specification.md`. Grounding compliance is reported as a Stage 3 pipeline verification metric alongside fidelity and auditability.

| Dimension | Name | What It Measures | Scoring |
|-----------|------|-----------------|---------|
| D1 | Source Selection & Fitness | Right Census product, vintage, geography, and universe | 0 / 1 / 2 |
| D2 | Methodological Soundness | Correct computations, weights, denominators, and formulas | 0 / 1 / 2 |
| D3 | Uncertainty Communication | MOE acknowledged, quantified, and correctly interpreted | 0 / 1 / 2 |
| D4 | Definitional Accuracy | Official Census concepts and reference periods used correctly | 0 / 1 / 2 |
| D5 | Reproducibility & Traceability | Another analyst can replicate the cited numbers | 0 / 1 / 2 |

**Stage 3 verification metrics (pipeline behavior, not CQS dimensions):**
Fidelity and auditability metrics are reported in Table 5 (§5). See numbers_registry.md S3-001–S3-012.
- Grounding compliance: 100%; all 39 pragmatics queries consulted methodology guidance before data interpretation

### Full Scoring Criteria

#### D1: Source Selection & Fitness

**What it measures:** Did the response select the right Census product, vintage, geography level, and population universe for the stated question?

- **Score 0 (Absent):** Wrong product entirely (e.g., decennial for income), wrong vintage, wrong geography level for the population, or no product specified.
- **Score 1 (Partial):** Correct product family but wrong parameters (e.g., ACS 1-year for a 15K-population area), or correct product but without justification.
- **Score 2 (Complete):** Correct product, vintage, geography, and universe, with rationale appropriate to the query context. Also scores 2: correctly determining that no available product meets fitness-for-use requirements and explaining why, with redirection to alternatives.

**Failure modes:** Using ACS 1-year for geographies below 65K population threshold; mixing decennial and ACS concepts without noting design differences; not specifying vintage when temporal precision matters.

#### D2: Methodological Soundness

**What it measures:** Are computations, weights, denominators, and formulas correct for the stated analysis?

- **Score 0 (Absent):** Fundamental errors: wrong denominator, unweighted counts used for inference, incorrect derived statistics, or no computation shown.
- **Score 1 (Partial):** Core computation correct but missing weight specification, incomplete formula, or minor unit inconsistency.
- **Score 2 (Complete):** Correct computation with appropriate weights, denominators, and formulas: consistent units, proper aggregation methods.

**Failure modes:** Dividing by total population when the universe is civilian noninstitutionalized; adding MOEs directly instead of root-sum-of-squares; comparing rates with different bases without noting the difference.

#### D3: Uncertainty Communication

**What it measures:** Does the response acknowledge, quantify, and correctly interpret statistical uncertainty?

- **Score 0 (Absent):** No mention of uncertainty, MOE, or reliability. Estimates presented as exact counts.
- **Score 1 (Partial):** Uncertainty mentioned qualitatively ("estimates may vary") but not quantified, or MOE provided without interpretation.
- **Score 2 (Complete):** MOE or SE provided with correct confidence level, significance testing appropriate to design, and explicit reliability assessment. Also scores 2: determining that uncertainty is too high for the estimate to be useful and recommending against use.

**Failure modes:** Ranking estimates without checking MOE overlap; over-precision (reporting tract-level income to the dollar without MOE); using 95% CI interpretation for ACS data reported at 90% confidence.

#### D4: Definitional Accuracy

**What it measures:** Are official Census concepts, classifications, and reference periods used correctly?

- **Score 0 (Absent):** Key concepts conflated or used incorrectly (e.g., household vs. family, nominal vs. real dollars, point-in-time vs. period estimate).
- **Score 1 (Partial):** Correct concepts but imprecise language, or reference period not specified.
- **Score 2 (Complete):** Official definitions used correctly, reference periods explicit, and cross-source differences flagged when applicable.

**Failure modes:** Treating ACS period estimates as point-in-time snapshots; conflating "household income" with "family income"; comparing ACS and CPS estimates without noting design and definitional differences.

#### D5: Reproducibility & Traceability

**What it measures:** Can another analyst replicate the stated numbers from the cited sources?

- **Score 0 (Absent):** "According to Census data..." (no table ID, no variable codes, no geography specification).
- **Score 1 (Partial):** Dataset and year specified but missing table ID or variable codes, or geography described but not with FIPS/GEOID precision.
- **Score 2 (Complete):** Full provenance: dataset, table ID or variable codes, geography (with identifiers), year/vintage, and any filters or transformations described.

**Failure modes:** Confabulated table IDs; correct data but no way to verify the source; describing geography colloquially without FIPS or GEOID.

---

## Appendix C: System Prompts

System prompts used for each experimental condition. Source: `src/eval/agent_loop.py` and `src/eval/rag_retriever.py`. All three conditions share the same base system prompt; conditions differ only in what augments or extends it.

### Base System Prompt (shared across all conditions)

```
You are a statistical consultant helping users access and understand U.S. Census data. Use your available tools to answer the question.
```

### Control Condition

Identical to base system prompt. No augmentation. Receives data retrieval tools (`get_census_data`, `explore_variables`) only.

### RAG Condition

Base system prompt augmented at runtime with retrieved methodology documentation chunks. The following template is applied before each query:

```
{base_prompt}

## Reference Materials

The following excerpts from Census methodology documentation may be relevant:

{retrieved_chunks}

Use these materials to inform your response where applicable.
```

Where `{retrieved_chunks}` is the top-5 chunks retrieved from a 311-chunk FAISS index of ACS methodology documentation, ranked by cosine similarity to the query. Receives the same data retrieval tools as control.

### Pragmatics Condition

Extends the base prompt with a grounding gate instruction that forces consultation of methodology guidance before data retrieval:

```
You are a statistical consultant helping users access and understand U.S. Census data. Use your available tools to answer the question.

You MUST call get_methodology_guidance FIRST before any other tool calls. This is required for every query; no exceptions. Select topics relevant to the query. After reviewing the methodology guidance, proceed with data retrieval.
```

Receives data retrieval tools plus `get_methodology_guidance` (excluded from control and RAG conditions). The `get_methodology_guidance` tool queries the compiled ACS pragmatics pack (SQLite) and returns structured expert judgment relevant to the query topics.

---

## Appendix D: Design Correction Post-Mortem

The V1 evaluation design contained a confound: the pragmatics condition had access to a methodology guidance tool that the control and RAG conditions lacked, making tool access, not knowledge representation, the independent variable. This was identified and corrected in V2, where all conditions received identical data tools and differed only in methodology support form. Full documentation is in `docs/decisions/ADR-011-v2-evaluation-design-correction.md`.

---

## Appendix E: Pragmatics Catalog

The 36 pragmatics in the ACS pack. Full content (context text, triggers, thread edges, provenance) is available in `staging/acs/*.json` (18 category files). Items sorted by category.

```{=latex}
\begin{landscape}
```

| Item ID | Category | Latitude | Context (first 100 chars) | Triggers | Thread Edges |
|---------|----------|----------|--------------------------|----------|-------------|
| ACS-BRK-001 | break_in_series | narrow | The 2009-2010 transition marks a break in population controls due to shift from Census 2000... | 4 | 1 |
| ACS-BRK-002 | break_in_series | narrow | The ACS transitioned from long-form decennial census to continuous monthly collection in 200... | 7 | 2 |
| ACS-BRK-003 | break_in_series | narrow | Starting with 2024 data, ACS updated the Period of Military Service question to align with D... | 6 | 1 |
| ACS-CMP-001 | comparison | none | Never directly compare ACS 1-year estimates with 5-year estimates. They represent different ... | 3 | 1 |
| ACS-CMP-002 | comparison | narrow | Consecutive 5-year estimates share 4 out of 5 years of underlying data. This means they are... | 6 | 2 |
| ACS-CMP-003 | comparison | none | Overlapping confidence intervals do NOT prove two estimates are statistically indistinguisha... | 5 | 1 |
| ACS-DIS-001 | disclosure_avoidance | narrow | ACS applies data swapping and noise injection to protect respondent confidentiality. Small-a... | 5 | 2 |
| ACS-DIS-002 | disclosure_avoidance | none | ACS does NOT use differential privacy. The 2020 Decennial Census used differential privacy,... | 4 | 0 |
| ACS-DIS-003 | disclosure_avoidance | narrow | When ACS estimates show a margin of error equal to the estimate itself, or when the Census B... | 5 | 1 |
| ACS-DOL-001 | dollar_values | narrow | When comparing dollar-denominated estimates (income, rent, home value) across different ACS ... | 5 | 1 |
| ACS-EQV-001 | geographic_equivalence | narrow | Some census tracts contain an entire county's population, which occurs in very rural or spar... | 5 | 1 |
| ACS-EQV-002 | geographic_equivalence | narrow | Census Designated Places (CDPs) are statistical entities, not legal jurisdictions. CDPs have... | 5 | 0 |
| ACS-GEO-001 | geography | none | Block group level data is only available in ACS 5-year estimates, not 1-year estimates. This... | 4 | 1 |
| ACS-GEO-002 | geography | wide | Public Use Microdata Areas (PUMAs) have a minimum population of 100,000. PUMA boundaries do ... | 4 | 0 |
| ACS-GEO-003 | geography | wide | Congressional district boundaries change after each decennial census reapportionment. ACS es... | 4 | 0 |
| ACS-GEO-004 | geography | full | ACS geographic boundaries reflect boundaries as of January 1 of the final year in the survey... | 4 | 0 |
| ACS-GQ-001 | group_quarters | narrow | ACS includes group quarters population (college dorms, military barracks, prisons). For comm... | 8 | 2 |
| ACS-GQ-002 | group_quarters | wide | ACS group quarters imputation rates can be very high, up to 30-50% of GQ persons may have... | 6 | 2 |
| ACS-IND-001 | independent_cities | none | Some US cities are county-equivalents (independent cities); they do NOT nest inside a count... | 5 | 0 |
| ACS-MOE-001 | margin_of_error | narrow | To calculate standard error from ACS margin of error: SE = MOE / 1.645. ACS MOEs are report... | 3 | 1 |
| ACS-MOE-002 | margin_of_error | narrow | Coefficient of variation (CV) = (SE / estimate) × 100. CV above 40% indicates the estimate ... | 3 | 1 |
| ACS-MOE-003 | margin_of_error | wide | 5-year estimates have smaller margins of error than 1-year estimates for the same geography,... | 3 | 0 |
| ACS-MOE-004 | margin_of_error | narrow | MOE approximation formulas for derived estimates (sums, differences, ratios) assume independ... | 5 | 2 |
| ACS-NRS-001 | nonresponse | narrow | ACS publishes allocation rates (item imputation rates) for every characteristic. High alloca... | 6 | 2 |
| ACS-NRS-002 | nonresponse | narrow | ACS uses hot-deck imputation, which assigns values from a statistically similar responding u... | 7 | 1 |
| ACS-PER-001 | period_estimate | narrow | ACS produces period estimates, not point-in-time estimates. A 5-year estimate represents an ... | 3 | 0 |
| ACS-PCL-001 | population_controls | narrow | ACS estimates at the tract and block group level are NOT controlled to independent populatio... | 5 | 2 |
| ACS-POP-001 | population_threshold | none | ACS 1-year estimates are only published for geographic areas with population of 65,000 or mo... | 3 | 1 |
| ACS-POP-002 | population_threshold | none | ACS 1-year Supplemental Estimates are available for areas with population of 20,000 or more,... | 3 | 0 |
| ACS-POP-003 | population_threshold | none | ACS 5-year estimates are available for all geographic areas, including census tracts and bloc... | 3 | 0 |
| ACS-REL-001 | release_schedule | narrow | As of December 2025, the most recent ACS releases are: ACS 1-year 2024 (released September ... | 4 | 0 |
| ACS-RES-001 | residence_rules | narrow | ACS uses a 'current residence' rule: a person must have lived at an address for 2 months or... | 6 | 2 |
| ACS-SAM-001 | sampling | wide | ACS sampling rates are not uniform. Sparsely populated areas are sampled at rates up to 5x h... | 6 | 2 |
| ACS-SUP-001 | suppression | wide | Some 1-year ACS tables may be suppressed if estimates are deemed too unreliable. Suppression... | 3 | 0 |
| ACS-THR-001 | threshold | narrow | For geographies with total population under approximately 1,000, ACS 5-year estimates may st... | 5 | 2 |
| ACS-THR-002 | threshold | narrow | When a user requests data for a small place (population under 5,000), proactively check whet... | 4 | 1 |

**Latitude key:** `none` = hard constraint (no exceptions); `narrow` = strong guidance with rare exceptions; `wide` = context-dependent; `full` = background information.

```{=latex}
\end{landscape}
```
