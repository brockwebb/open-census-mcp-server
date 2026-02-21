# Consultation Quality Score (CQS) Rubric Specification

**Version:** 1.0
**Date:** 2026-02-18
**Author:** Brock Webb
**Status:** Post-V2 Production
**Traces To:** VR-006 (SRS), H.1–H.3 (Implementation Schedule)

---

## 1. Purpose

The Consultation Quality Score (CQS) is a domain-specific evaluation rubric for assessing AI-mediated federal statistical data consultation. It operationalizes two established frameworks for the novel context of LLM-delivered Census data responses:

- **FCSM Data Quality Framework (FCSM 20-04, 2020):** 11 dimensions across Utility, Objectivity, and Integrity — the federal standard for statistical data quality assessment.
- **NIST AI Risk Management Framework (AI RMF 1.0, 2023):** Trustworthiness characteristics for AI systems, including the TEVV (Test, Evaluation, Verification, Validation) methodology.

Neither framework alone covers AI-mediated statistical consultation. FCSM assumes a human analyst (who may err but will not fabricate a table ID). NIST assumes AI systems may hallucinate but does not define what hallucination means for ACS margin-of-error calculations. CQS bridges this gap.

## 2. Framework Crosswalk

### 2.1 Three-Framework Alignment

| CQS Dimension | FCSM 20-04 Dimensions | NIST AI RMF Characteristics | IQA Domain |
|---|---|---|---|
| **D1: Source Selection & Fitness** | Relevance, Granularity, Timeliness | Safe; Accountable & Transparent | Utility |
| **D2: Methodological Soundness** | Accuracy & Reliability; Scientific Integrity | *(Gate: Valid & Reliable)* | Objectivity |
| **D3: Uncertainty Communication** | Accuracy & Reliability (TSE component) | Explainable & Interpretable | Objectivity |
| **D4: Definitional Accuracy** | Coherence | Explainable & Interpretable | Objectivity |
| **D5: Reproducibility & Traceability** | Accessibility; Scientific Integrity; Credibility | Accountable & Transparent | Integrity |
| **D6: Groundedness & Faithfulness** | N/A — FCSM not designed for AI-mediated use | Valid & Reliable; Fair (epistemic bias) | *(CQS extension)* |

**Note on D6:** D6 is a binary grounding gate — treatment conditions (RAG, pragmatics) ground in authoritative sources by design; control does not. D6 is **excluded from the CQS composite score** — CQS uses D1-D5 only. Stage 3 fidelity verification provides automated claim-level grounding measurement.

### 2.2 Key Framework Notes

**NIST Valid & Reliable as Gate Condition:** NIST AI RMF treats Valid & Reliable as a pass/fail gate. If the AI system is not valid and reliable, the other trustworthiness characteristics are moot. In CQS terms: if D6 (Groundedness) scores 0 — the response fabricates data — the other dimensions are unreliable regardless of their individual scores.

**FCSM "N/A" not "Gap":** FCSM 20-04 was designed for human statistical practice, not AI-mediated data delivery. The absence of an AI-specific dimension is not a deficiency in the framework — it is simply outside its intended scope. CQS extends FCSM to this new application context.

**Safety as Emergent Property:** FCSM does not have a separate "Safety" dimension because in federal statistics, safety emerges from getting other dimensions right. Using the wrong ACS product for a small-area policy decision is the harm vector — it is captured by Relevance (wrong product), Accuracy (unreliable estimate), and Scientific Integrity (should have known better). NIST's "Safe" characteristic maps across multiple CQS dimensions rather than to a single one.

**Objectivity Subsumes Fairness:** The IQA definition of Objectivity — "accurate, clear, complete, and unbiased" — encompasses NIST's Fair/Bias-managed characteristic for this domain. The relevant bias in AI-mediated statistical consultation is epistemic (confident wrongness from training data) rather than demographic (disparate treatment of populations). This maps to D6 (Groundedness).

### 2.3 FCSM 20-04 Full Dimension Coverage

For completeness, the FCSM dimensions not directly scored in CQS and why:

| FCSM Dimension | CQS Treatment |
|---|---|
| Relevance | → D1 (Source Selection) |
| Accessibility | → D5 (Reproducibility) |
| Timeliness | → D1 (vintage selection) |
| Punctuality | Not applicable — CQS evaluates response quality, not release schedules |
| Granularity | → D1 (geography level selection) |
| Accuracy & Reliability | → D2 (Methodology) + D3 (Uncertainty) |
| Coherence | → D4 (Definitions) |
| Scientific Integrity | → D2 (Methodology) + D5 (Traceability) |
| Credibility | → D5 (Traceability) + D6 (Groundedness) |
| Computer & Physical Security | Not applicable — out of scope for response evaluation |
| Confidentiality | Subcase within D1 (disclosure avoidance for small-area queries) |

## 3. Evaluation Methodology

CQS validation uses a four-stage pipeline with three-condition pairwise comparisons and multi-vendor LLM judges.

### 3.1 Evaluation Design (V2)

**Three conditions:**
- **Control:** Claude Sonnet 4.5 API, no tools, no pragmatics augmentation (baseline LLM performance)
- **RAG:** Claude Sonnet 4.5 API with variable metadata retrieval (semantic search over Census variable descriptions)
- **Pragmatics:** Claude Sonnet 4.5 API with MCP tools (live Census data retrieval + pragmatic consultation layer)

**Pairwise comparisons:**
1. `control_vs_rag` — Does RAG over metadata help?
2. `control_vs_pragmatics` — Does pragmatics help?
3. `rag_vs_pragmatics` — Which context strategy is better?

Three pairwise comparisons enable full three-group analysis while preserving the validated A-vs-B judge methodology.

### 3.2 Multi-Vendor Judge Panel

**Judges:**
- Anthropic `claude-opus-4-5`
- OpenAI `gpt-5.2`
- Google `gemini-3-pro-preview`

**Rationale:** Three-vendor panel detects self-enhancement bias (models preferentially scoring their own outputs) and vendor-specific scoring tendencies. All three vendors use the same rubric and receive identical prompts.

### 3.3 Counterbalanced Scoring

Each judge scores each query 6 times per comparison:
- **Passes 1, 3, 5:** `condition_a_first` (Response A = condition A, Response B = condition B)
- **Passes 2, 4, 6:** `condition_b_first` (Response A = condition B, Response B = condition A)

**Total judgments per comparison:** 39 queries × 3 vendors × 6 passes = 702 judgment records

Counterbalancing mitigates position bias (judges preferring the first or second response regardless of content).

### 3.4 Four-Stage Pipeline

**Stage 1: Response Generation**
- Generate responses for all three conditions using the CQS test battery (39 queries)
- Output: `control_responses.jsonl`, `rag_responses.jsonl`, `pragmatics_responses.jsonl`

**Stage 2: LLM-as-Judge Scoring**
- Pairwise judge scoring on D1-D6 rubric with counterbalanced presentation
- Output: `rag_vs_pragmatics.jsonl`, `control_vs_rag.jsonl`, `control_vs_pragmatics.jsonl`
- Specification: VR-031 through VR-046 (SRS Section 8.4)

**Stage 3: Fidelity Verification**
- Automated verification of quantitative claims against tool call returns and retrieved chunks
- Replaces flawed D6 rubric dimension with objective groundedness measurement
- Specification: VR-050 through VR-056 (SRS Section 8.5)

**Stage 4: Expert Validation**
- Human expert scoring on blinded subset for calibration
- Interview-based tacit knowledge elicitation for pragmatics layer improvements

### 3.5 Implementation

**Key files:**
- `src/eval/judge_pipeline.py` — Stage 2 pairwise comparison pipeline
- `src/eval/judge_prompts.py` — CQS rubric prompts (condition-agnostic)
- `src/eval/judge_config.yaml` — Judge panel config, comparison definitions
- `src/eval/battery/queries.yaml` — CQS test battery (39 queries across 6 categories)
- `src/eval/qc_stage2.py` — Stage 2 QC validation script

## 4. Generalizability

The CQS development pattern is reusable across domains requiring AI-mediated expert consultation:

**Pattern:**
1. Identify domain quality framework (FCSM 20-04 for federal statistics)
2. Cross-reference with NIST AI RMF trustworthiness characteristics
3. Identify N/A cells where domain framework doesn't cover AI-specific risks
4. Operationalize novel dimensions for those gaps (D6: Groundedness)
5. Validate via pairwise LLM judges + expert calibration

**Domain-specific vs generalizable:**
- The six CQS dimensions (D1-D6) are specific to Census data consultation
- The crosswalk methodology and evaluation pipeline are domain-agnostic
- Other domains (clinical guidelines, legal research, engineering standards) can apply the same pattern with domain-appropriate quality frameworks

The contribution is not the rubric itself — it's the systematic method for deriving trustworthy AI evaluation rubrics from established domain standards.

## 5. General Scoring Principles

**Principle 1: Informed refusal outscores confident delivery of unfit data.** A response that correctly determines data are unavailable, unreliable, or unfit for the stated purpose — and explains why — always outscores a response that confidently delivers questionable data without caveats. A senior federal statistician who says "we can't answer that reliably with available data" is doing better statistical work than one who hands over a number with a CV of 60%.

**Principle 2: Explanation of why matters.** Bare refusal ("I can't help with that") scores lower than informed refusal with reasoning ("ACS 1-year isn't available below 65K population; the 5-year estimate for this tract has a CV over 40%, so I'd recommend the county-level estimate instead or consulting the PUMS for custom tabulation"). The reasoning demonstrates statistical judgment.

**Principle 3: Redirection is valuable.** Pointing the user toward a better product, geography level, or approach — even when the original question can't be answered as posed — demonstrates the kind of expert consultation the system is designed to provide.

## 6. CQS Dimensions — Detailed Specification

### D1: Source Selection & Fitness

**What it measures:** Did the response select the right Census product, vintage, geography level, and population universe for the stated question?

**Scoring:**
- **0 (Absent):** Wrong product entirely (e.g., decennial for income), wrong vintage, wrong geography level for the population, or no product specified.
- **1 (Partial):** Correct product family but wrong parameters (e.g., ACS 1-year for a 15K-population area), or correct product but without justification.
- **2 (Complete):** Correct product, vintage, geography, and universe — with rationale appropriate to the query context. **Also scores 2:** correctly determining that no available product meets fitness-for-use requirements for the stated question and explaining why, with redirection to alternatives if applicable.

**What "good" looks like:** "ACS 2022 5-year estimates (table B19013) for Prince George's County, MD. 5-year used because the county population exceeds 65,000 and supports 1-year estimates, but 5-year provides more reliable tract-level breakdowns if needed."

**Failure modes:**
- Using ACS 1-year for geographies below 65K population threshold
- Mixing decennial and ACS concepts without noting design differences
- Not specifying vintage when temporal precision matters
- Ignoring disclosure avoidance implications for small-area requests

### D2: Methodological Soundness

**What it measures:** Are computations, weights, denominators, and formulas correct for the stated analysis?

**Scoring:**
- **0 (Absent):** Fundamental errors — wrong denominator, unweighted counts used for inference, incorrect derived statistics, or no computation shown.
- **1 (Partial):** Core computation correct but missing weight specification, incomplete formula, or minor unit inconsistency.
- **2 (Complete):** Correct computation with appropriate weights, denominators, and formulas — consistent units, proper aggregation methods.

**What "good" looks like:** "The poverty rate uses the official poverty threshold applied to the civilian noninstitutionalized population. For multi-county aggregation, estimates are summed and MOEs combined using the square root of the sum of squared MOEs."

**Failure modes:**
- Dividing by total population when the universe is civilian noninstitutionalized
- Adding MOEs directly instead of root-sum-of-squares
- Comparing rates with different bases without noting the difference
- Using person weights for housing-unit estimates

### D3: Uncertainty Communication

**What it measures:** Does the response acknowledge, quantify, and correctly interpret statistical uncertainty?

**Scoring:**
- **0 (Absent):** No mention of uncertainty, MOE, or reliability. Estimates presented as exact counts.
- **1 (Partial):** Uncertainty mentioned qualitatively ("estimates may vary") but not quantified, or MOE provided without interpretation.
- **2 (Complete):** MOE or SE provided with correct confidence level, significance testing appropriate to design, and explicit reliability assessment for small-area estimates. **Also scores 2:** determining that uncertainty is too high for the estimate to be useful and recommending against use, with explanation of why and suggested alternatives.

**What "good" looks like:** "The median household income estimate is $85,234 (±$3,102 at 90% confidence). The coefficient of variation is 2.4%, indicating a reliable estimate. Note: comparing this to adjacent County X ($82,100 ±$4,500) — the confidence intervals overlap, so we cannot conclude a statistically significant difference."

**Failure modes:**
- Ranking estimates without checking MOE overlap
- Declaring "significant" difference based on non-overlapping CIs alone (conservative but not wrong — should note the anti-pattern)
- Over-precision (reporting tract-level income to the dollar without MOE)
- Using 95% CI interpretation for ACS data reported at 90% confidence

### D4: Definitional Accuracy

**What it measures:** Are official Census concepts, classifications, and reference periods used correctly?

**Scoring:**
- **0 (Absent):** Key concepts conflated or used incorrectly (e.g., household vs family, nominal vs real dollars, point-in-time vs period estimate).
- **1 (Partial):** Correct concepts but imprecise language, or reference period not specified.
- **2 (Complete):** Official definitions used correctly, reference periods explicit, and cross-source differences flagged when applicable.

**What "good" looks like:** "ACS 'health insurance coverage' refers to coverage at the time of interview, not an annual measure. This differs from the CPS ASEC, which asks about coverage during the prior calendar year. Direct comparison requires understanding this reference-period difference."

**Failure modes:**
- Treating ACS period estimates as point-in-time snapshots
- Conflating "household income" with "family income"
- Comparing ACS and CPS estimates without noting design and definitional differences
- Using colloquial definitions ("poverty" without specifying official threshold vs supplemental measure)

### D5: Reproducibility & Traceability

**What it measures:** Can another analyst replicate the stated numbers from the cited sources?

**Scoring:**
- **0 (Absent):** "According to Census data..." — no table ID, no variable codes, no geography specification.
- **1 (Partial):** Dataset and year specified but missing table ID or variable codes, or geography described but not with FIPS/GEOID precision.
- **2 (Complete):** Full provenance: dataset, table ID or variable codes, geography (with identifiers), year/vintage, and any filters or transformations described.

**What "good" looks like:** "Source: ACS 2022 5-Year Estimates, Table B19013, variable B19013_001E (Median Household Income), for Prince George's County, MD (FIPS 24033)."

**Failure modes:**
- Hallucinated table IDs (e.g., citing "Table B99999" that doesn't exist)
- Correct data but no way to verify the source
- Describing geography colloquially without FIPS or GEOID
- Blending multiple sources without describing the integration method

### D6: Groundedness & Faithfulness

**What it measures:** Are all claims traceable to cited Census sources, with no fabricated data, hallucinated identifiers, or reasoning that contradicts source material?

**Scoring:**
- **0 (Absent):** Response contains fabricated statistics, hallucinated table/variable codes, or claims contradicted by cited sources. **Note: A score of 0 on D6 is a gate failure — other dimension scores are unreliable.**
- **1 (Partial):** Claims generally supported but some reasoning steps not traceable to source, or minor unsupported assertions mixed with grounded claims.
- **2 (Complete):** All quantitative claims traceable to cited Census tables or documentation. Reasoning chain consistent with source material. No hallucinated identifiers or datasets.

**What "good" looks like:** Every number in the response can be verified against the cited table. Interpretive claims reference specific methodology documentation. The response stays within the scope of what the data can support.

**Failure modes:**
- Fabricating plausible-sounding but nonexistent variable codes
- Citing a real table but reporting numbers not in that table
- Importing "knowledge" from training data that contradicts current Census methodology
- Semantic smearing: conflating estimates from different vintages or products

**Gate condition (per NIST AI RMF):** If D6 = 0, the response has fabricated data. The remaining dimension scores cannot be trusted regardless of their values, because the grounding assumption — that the response is working with real data — has failed.

## 7. Scoring Protocol

### 7.1 Scale

Each dimension scored 0–2 (Absent / Partial / Complete).

**Total CQS range: 0–12.**

Interpretation bands (preliminary — to be calibrated against human expert scoring):
- **10–12:** Production quality — suitable for federal statistical communication
- **7–9:** Adequate with caveats — usable with expert review
- **4–6:** Significant methodological issues — requires substantial correction
- **0–3:** Unreliable — should not be used without full rework

### 7.2 Evaluation Mode

**Pairwise comparison** (per MT-Bench/Chatbot Arena methodology and the author's prior harmonization ensemble work):

For each test query, two responses are generated:
- **Control:** Claude API, no tools, no pragmatics augmentation
- **Treatment:** Claude API with live MCP tools (Census data retrieval + pragmatics)

Both responses presented to each judge (order randomized to mitigate position bias).

Judge prompt asks: "Which response better adheres to Census statistical quality standards?" and scores each response on all 6 dimensions independently.

### 7.3 Judge Panel

Three-model ensemble (per author's validated methodology from survey harmonization classification):

| Judge Model | Known Behavioral Profile |
|---|---|
| Claude Opus 4.5 | High synthesis, neutral vendor bias (p=0.159 from harmonization study) |
| OpenAI GPT-5.2 (or o3) | Moderate synthesis, slight pro-self bias (documented) |
| Google Gemini 2.5 Pro | Conservative/deferential, anti-self vendor bias (documented) |

**Inter-rater agreement:** Fleiss' κ computed across all three judges for each dimension. Target: κ ≥ 0.6 (substantial agreement), consistent with harmonization study rater tier.

**Vendor bias monitoring:** Same-vendor selection rates tracked and reported, consistent with harmonization study methodology.

### 7.4 Human Calibration

Expert-scored subset of 10–15 queries to anchor automated scoring:
- Human experts score both control and treatment responses on all 6 dimensions
- LLM judge scores compared to human scores for calibration
- Disagreements analyzed for rubric refinement
- Cohen's κ between each LLM judge and human expert panel reported

## 8. Relationship to Prior Work

### 8.1 Survey Harmonization Ensemble (Webb, 2026)

The judge panel methodology directly reuses the author's validated multi-model ensemble approach for survey harmonization classification:

| Harmonization Study | CQS Application |
|---|---|
| 3-model rater tier (fast), κ=0.611 | Not needed — single query, not 1,598 pairs |
| 3-model arbitrator tier (flagship), κ=0.843 | → LLM judge panel (same 3 models) |
| Fleiss' κ for inter-rater agreement | → Same metric, same purpose |
| Vendor bias analysis | → Same analysis, same reporting |
| Pairwise F1/F2/F3 classification | → Pairwise CQS dimension scoring |
| Construct validity through convergence | → Same argument for FCSM presentation |

### 8.2 LLM-as-Judge Literature

- **MT-Bench (Zheng et al., 2023):** Pairwise comparison protocol, position bias mitigation through randomization.
- **FActScore (Min et al., 2023):** Atomic claim decomposition for factual support — informs D6 (Groundedness).
- **RAGAS (Es et al., 2023):** Faithfulness, answer relevance, context recall for RAG evaluation — informs D6 and D5.
- **Documented biases:** Position bias, verbosity bias, self-enhancement bias (Zheng et al., 2023) — mitigated by 3-model panel and order randomization.

### 8.3 Semantic Smearing Research (Webb, 2026)

The CQS evaluation framework is motivated by empirical findings on semantic smearing in federal statistical metadata:
- 82% increase in mean cosine similarity when Census variable metadata is enriched
- 86.5% collapse in inter-group discrimination under embedding
- Cross-model validation (MiniLM-384, RoBERTa-large) confirming larger models amplify rather than correct smearing

D6 (Groundedness) specifically targets semantic smearing failure modes where LLMs conflate estimates across vintages, products, or geographic levels.

## 9. Open Questions

- [ ] Should D6 gate failure (score = 0) automatically cap total CQS at a maximum value (e.g., 4)?
- [ ] Should dimension weights be equal, or should some dimensions carry more weight for specific query types?
- [ ] What is the minimum number of test queries needed for statistical power in treatment vs control comparison?
- [ ] Should the scoring prompt present responses in isolation (absolute scoring) or always pairwise (relative scoring)?

## 10. References

- FCSM. (2020). A Framework for Data Quality (FCSM 20-04). Federal Committee on Statistical Methodology.
- NIST. (2023). Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1.
- Information Quality Act. (2000). Section 515 of the Treasury and General Government Appropriations Act for FY 2001.
- U.S. Census Bureau. Statistical Quality Standards (2013, revised).
- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.
- Min, S., et al. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision.
- Es, S., et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation.
- Xia, T., et al. (2026). SkillRL: Skill-Driven LLM Reasoning Reinforcement Learning.
