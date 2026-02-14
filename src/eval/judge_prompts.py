"""Judge prompt templates for CQS scoring.

Embeds the full Consultation Quality Score (CQS) rubric for evaluating
AI-mediated federal statistical data consultation.
"""

CQS_RUBRIC = """
# Consultation Quality Score (CQS) Rubric

## Purpose
The CQS evaluates AI-mediated federal statistical data consultation against FCSM Data Quality Framework
(FCSM 20-04, 2020) and NIST AI Risk Management Framework (AI RMF 1.0, 2023).

## Scoring Scale
Each dimension scored 0–2:
- **0 (Absent):** Fundamental failure or completely missing
- **1 (Partial):** Present but incomplete or with issues
- **2 (Complete):** Meets professional statistical communication standards

Total CQS range: 0–12

## General Principles

**Principle 1: Informed refusal outscores confident delivery of unfit data.**
A response that correctly determines data are unavailable, unreliable, or unfit for the stated purpose —
and explains why — always outscores a response that confidently delivers questionable data without caveats.

**Principle 2: Explanation of why matters.**
Bare refusal ("I can't help with that") scores lower than informed refusal with reasoning
("ACS 1-year isn't available below 65K population; the 5-year estimate for this tract has a CV over 40%,
so I'd recommend the county-level estimate instead").

**Principle 3: Redirection is valuable.**
Pointing the user toward a better product, geography level, or approach — even when the original question
can't be answered as posed — demonstrates expert consultation.

## Dimensions

### D1: Source Selection & Fitness
**What it measures:** Did the response select the right Census product, vintage, geography level, and
population universe for the stated question?

**Scoring:**
- **0 (Absent):** Wrong product entirely (e.g., decennial for income), wrong vintage, wrong geography
  level for the population, or no product specified.
- **1 (Partial):** Correct product family but wrong parameters (e.g., ACS 1-year for a 15K-population area),
  or correct product but without justification.
- **2 (Complete):** Correct product, vintage, geography, and universe — with rationale appropriate to the
  query context. **Also scores 2:** correctly determining that no available product meets fitness-for-use
  requirements for the stated question and explaining why, with redirection to alternatives if applicable.

**What "good" looks like:** "ACS 2022 5-year estimates (table B19013) for Prince George's County, MD. 5-year
used because the county population exceeds 65,000 and supports 1-year estimates, but 5-year provides more
reliable tract-level breakdowns if needed."

**Failure modes:**
- Using ACS 1-year for geographies below 65K population threshold
- Mixing decennial and ACS concepts without noting design differences
- Not specifying vintage when temporal precision matters
- Ignoring disclosure avoidance implications for small-area requests

### D2: Methodological Soundness
**What it measures:** Are computations, weights, denominators, and formulas correct for the stated analysis?

**Scoring:**
- **0 (Absent):** Fundamental errors — wrong denominator, unweighted counts used for inference, incorrect
  derived statistics, or no computation shown.
- **1 (Partial):** Core computation correct but missing weight specification, incomplete formula, or minor
  unit inconsistency.
- **2 (Complete):** Correct computation with appropriate weights, denominators, and formulas — consistent
  units, proper aggregation methods.

**What "good" looks like:** "The poverty rate uses the official poverty threshold applied to the civilian
noninstitutionalized population. For multi-county aggregation, estimates are summed and MOEs combined using
the square root of the sum of squared MOEs."

**Failure modes:**
- Dividing by total population when the universe is civilian noninstitutionalized
- Adding MOEs directly instead of root-sum-of-squares
- Comparing rates with different bases without noting the difference
- Using person weights for housing-unit estimates

### D3: Uncertainty Communication
**What it measures:** Does the response acknowledge, quantify, and correctly interpret statistical uncertainty?

**Scoring:**
- **0 (Absent):** No mention of uncertainty, MOE, or reliability. Estimates presented as exact counts.
- **1 (Partial):** Uncertainty mentioned qualitatively ("estimates may vary") but not quantified, or MOE
  provided without interpretation.
- **2 (Complete):** MOE or SE provided with correct confidence level, significance testing appropriate to
  design, and explicit reliability assessment for small-area estimates. **Also scores 2:** determining that
  uncertainty is too high for the estimate to be useful and recommending against use, with explanation of
  why and suggested alternatives.

**What "good" looks like:** "The median household income estimate is $85,234 (±$3,102 at 90% confidence).
The coefficient of variation is 2.4%, indicating a reliable estimate. Note: comparing this to adjacent
County X ($82,100 ±$4,500) — the confidence intervals overlap, so we cannot conclude a statistically
significant difference."

**Failure modes:**
- Ranking estimates without checking MOE overlap
- Over-precision (reporting tract-level income to the dollar without MOE)
- Using 95% CI interpretation for ACS data reported at 90% confidence

### D4: Definitional Accuracy
**What it measures:** Are official Census concepts, classifications, and reference periods used correctly?

**Scoring:**
- **0 (Absent):** Key concepts conflated or used incorrectly (e.g., household vs family, nominal vs real
  dollars, point-in-time vs period estimate).
- **1 (Partial):** Correct concepts but imprecise language, or reference period not specified.
- **2 (Complete):** Official definitions used correctly, reference periods explicit, and cross-source
  differences flagged when applicable.

**What "good" looks like:** "ACS 'health insurance coverage' refers to coverage at the time of interview,
not an annual measure. This differs from the CPS ASEC, which asks about coverage during the prior calendar
year. Direct comparison requires understanding this reference-period difference."

**Failure modes:**
- Treating ACS period estimates as point-in-time snapshots
- Conflating "household income" with "family income"
- Comparing ACS and CPS estimates without noting design and definitional differences
- Using colloquial definitions ("poverty" without specifying official threshold vs supplemental measure)

### D5: Reproducibility & Traceability
**What it measures:** Can another analyst replicate the stated numbers from the cited sources?

**Scoring:**
- **0 (Absent):** "According to Census data..." — no table ID, no variable codes, no geography specification.
- **1 (Partial):** Dataset and year specified but missing table ID or variable codes, or geography described
  but not with FIPS/GEOID precision.
- **2 (Complete):** Full provenance: dataset, table ID or variable codes, geography (with identifiers),
  year/vintage, and any filters or transformations described.

**What "good" looks like:** "Source: ACS 2022 5-Year Estimates, Table B19013, variable B19013_001E (Median
Household Income), for Prince George's County, MD (FIPS 24033)."

**Failure modes:**
- Hallucinated table IDs (e.g., citing "Table B99999" that doesn't exist)
- Correct data but no way to verify the source
- Describing geography colloquially without FIPS or GEOID
- Blending multiple sources without describing the integration method

### D6: Groundedness & Faithfulness
**What it measures:** Are all claims traceable to cited Census sources, with no fabricated data, hallucinated
identifiers, or reasoning that contradicts source material?

**Scoring:**
- **0 (Absent):** Response contains fabricated statistics, hallucinated table/variable codes, or claims
  contradicted by cited sources. **Note: A score of 0 on D6 is a gate failure — other dimension scores
  are unreliable.**
- **1 (Partial):** Claims generally supported but some reasoning steps not traceable to source, or minor
  unsupported assertions mixed with grounded claims.
- **2 (Complete):** All quantitative claims traceable to cited Census tables or documentation. Reasoning
  chain consistent with source material. No hallucinated identifiers or datasets.

**What "good" looks like:** Every number in the response can be verified against the cited table.
Interpretive claims reference specific methodology documentation. The response stays within the scope
of what the data can support.

**Failure modes:**
- Fabricating plausible-sounding but nonexistent variable codes
- Citing a real table but reporting numbers not in that table
- Importing "knowledge" from training data that contradicts current Census methodology
- Semantic smearing: conflating estimates from different vintages or products

**Gate condition (per NIST AI RMF):** If D6 = 0, the response has fabricated data. The remaining dimension
scores cannot be trusted regardless of their values, because the grounding assumption — that the response
is working with real data — has failed.
"""


def build_judge_prompt(query_text: str, response_a: str, response_b: str) -> str:
    """Build judge scoring prompt with full CQS rubric.

    Args:
        query_text: The user's original query
        response_a: First response (either control or treatment, randomly assigned)
        response_b: Second response (either control or treatment, randomly assigned)

    Returns:
        Complete judge prompt requesting structured JSON scoring
    """

    prompt = f"""Today's date is February 13, 2026. When evaluating source selection, you must assess data availability based on what has been published as of this date, not based on your training data. Logically, if API calls use a date to obtain data, and that date was not valid, no data would be retrieved to judge. Do not penalize citations of recently released products that you may not have been trained on.

{CQS_RUBRIC}

## Your Task

You are evaluating two responses to a Census data query. Both responses attempt to answer the same question.

**User Query:**
{query_text}

**Response A:**
{response_a}

**Response B:**
{response_b}

## Instructions

1. **Score each response independently** on all 6 dimensions (D1-D6) using the 0-1-2 scale defined above.

2. **Provide confidence ratings** (1-5 scale) for each dimension score:
   - 1 = Very uncertain
   - 2 = Somewhat uncertain
   - 3 = Moderately confident
   - 4 = Confident
   - 5 = Very confident

3. **Write brief reasoning** (1-2 sentences) explaining each dimension score.

4. **Compare overall**: After scoring independently, state which response better adheres to Census
   statistical quality standards (A, B, or tie), with reasoning.

## Output Format

Return a JSON object with this exact structure:

```json
{{
  "response_a": {{
    "D1": {{"score": 2, "confidence": 4, "reasoning": "..."}},
    "D2": {{"score": 1, "confidence": 3, "reasoning": "..."}},
    "D3": {{"score": 0, "confidence": 5, "reasoning": "..."}},
    "D4": {{"score": 2, "confidence": 4, "reasoning": "..."}},
    "D5": {{"score": 1, "confidence": 3, "reasoning": "..."}},
    "D6": {{"score": 2, "confidence": 5, "reasoning": "..."}}
  }},
  "response_b": {{
    "D1": {{"score": 1, "confidence": 4, "reasoning": "..."}},
    "D2": {{"score": 2, "confidence": 4, "reasoning": "..."}},
    "D3": {{"score": 1, "confidence": 3, "reasoning": "..."}},
    "D4": {{"score": 2, "confidence": 5, "reasoning": "..."}},
    "D5": {{"score": 2, "confidence": 4, "reasoning": "..."}},
    "D6": {{"score": 2, "confidence": 5, "reasoning": "..."}}
  }},
  "overall_preference": "A",
  "preference_reasoning": "Response A demonstrates better methodological soundness and uncertainty communication despite weaker source traceability."
}}
```

**Critical reminders:**
- Score 0-1-2 only (no other values)
- Score each response independently before comparing
- D6=0 is a gate failure — if a response fabricates data, note that other scores may be unreliable
- Informed refusal outscores confident delivery of unfit data

Return ONLY the JSON object, no other text."""

    return prompt
