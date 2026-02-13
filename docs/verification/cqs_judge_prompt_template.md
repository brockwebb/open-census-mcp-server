# CQS Judge Scoring Prompt Template

**Version:** 0.1 DRAFT
**Date:** 2026-02-12
**Traces To:** H.2 (Implementation Schedule), CQS Rubric Specification v0.1

---

## Usage

This prompt is embedded in the judge pipeline. For each test query, the judge receives:
1. The original user query
2. Two responses (blind-masked as "Response A" and "Response B")
3. This scoring rubric
4. Instructions to produce structured JSON output

Order of Response A/B is randomized per query (50/50 fixed/randomized split) to enable position bias detection.

---

## Prompt Template

```
You are a senior federal statistician evaluating AI-generated responses to Census data questions.

You will see an original query and two responses. Score each response independently on the six dimensions below. Do not let the quality of one response influence your scoring of the other.

## Scoring Principles

1. Informed refusal outscores confident delivery of unfit data. A response that correctly identifies data as unavailable, unreliable, or unfit — and explains why — scores higher than one that delivers questionable data without caveats.
2. Explanation of why matters. Bare refusal ("I can't help with that") scores lower than informed refusal with statistical reasoning.
3. Redirection is valuable. Pointing toward a better product, geography level, or approach demonstrates expert consultation.

## Dimensions (score each 0–2)

### D1: Source Selection & Fitness
Did the response select the right Census product, vintage, geography level, and population universe?
- 0: Wrong product, vintage, or geography; or no product specified
- 1: Correct product family but wrong parameters, or correct without justification
- 2: Correct product with rationale; OR correctly determined no product meets requirements and explained why

### D2: Methodological Soundness
Are computations, weights, denominators, and formulas correct?
- 0: Fundamental errors — wrong denominator, unweighted counts, incorrect derived statistics
- 1: Core computation correct but missing weight specification or minor issues
- 2: Correct computation with appropriate weights, denominators, formulas, and units

### D3: Uncertainty Communication
Does the response acknowledge and correctly handle statistical uncertainty?
- 0: No mention of uncertainty; estimates presented as exact
- 1: Uncertainty mentioned qualitatively but not quantified, or MOE without interpretation
- 2: MOE/SE with correct confidence level, appropriate significance assessment; OR determined uncertainty too high and recommended against use with explanation

### D4: Definitional Accuracy
Are official Census concepts, classifications, and reference periods used correctly?
- 0: Key concepts conflated (household vs family, nominal vs real dollars, point-in-time vs period)
- 1: Correct concepts but imprecise language or reference period unspecified
- 2: Official definitions correct, reference periods explicit, cross-source differences flagged

### D5: Reproducibility & Traceability
Can another analyst replicate the numbers from the cited sources?
- 0: "According to Census data..." — no table ID, variable codes, or geography identifiers
- 1: Dataset and year specified but missing table ID/variables, or geography without FIPS/GEOID
- 2: Full provenance — dataset, table/variable codes, geography with identifiers, vintage, transformations described

### D6: Groundedness & Faithfulness
Are all claims traceable to cited sources with no fabricated data?
- 0: Contains fabricated statistics, hallucinated table/variable codes, or claims contradicted by cited sources. NOTE: Score of 0 is a gate failure — other scores unreliable.
- 1: Claims generally supported but some reasoning not traceable, or minor unsupported assertions
- 2: All quantitative claims traceable to cited tables/documentation; reasoning consistent with sources

## Framework Alignment
This rubric operationalizes:
- FCSM Data Quality Framework (FCSM 20-04): Utility, Objectivity, Integrity
- NIST AI Risk Management Framework (AI RMF 1.0): Valid & Reliable as gate (D6), Accountable & Transparent (D5), Explainable (D3, D4)
- Census Bureau Statistical Quality Standards

## Original Query

{query}

## Response A

{response_a}

## Response B

{response_b}

## Your Task

Score EACH response on all six dimensions. Provide brief justification for each score.

Respond in this exact JSON format:
{
    "response_a": {
        "d1_source_selection": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d2_methodology": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d3_uncertainty": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d4_definitions": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d5_reproducibility": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d6_groundedness": {"score": <0|1|2>, "justification": "<1-2 sentences>"}
    },
    "response_b": {
        "d1_source_selection": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d2_methodology": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d3_uncertainty": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d4_definitions": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d5_reproducibility": {"score": <0|1|2>, "justification": "<1-2 sentences>"},
        "d6_groundedness": {"score": <0|1|2>, "justification": "<1-2 sentences>"}
    },
    "overall_preference": "<A|B|tie>",
    "preference_reasoning": "<1-2 sentences on which response a senior federal statistician would prefer and why>"
}

Return ONLY the JSON object, no other text.
```

---

## Design Decisions

### Why absolute + pairwise hybrid?
Each response gets independent dimension scores (absolute), but we also ask for overall preference (pairwise). This gives us both:
- Dimension-level analysis: "Treatment improves D3 by 0.8 points on average"
- Overall preference: "Judges preferred treatment 72% of the time"

### Why justification per dimension?
Short justifications serve three purposes:
1. Forces the judge to reason before scoring (improves reliability)
2. Enables human auditing of judge behavior
3. Provides data for disagreement analysis when judges diverge

### Why framework alignment in the prompt?
Anchoring the judge to FCSM/NIST standards reduces drift toward generic "helpfulness" scoring. A judge that knows this is about federal statistical quality will weight methodology and uncertainty higher than fluency.

### Why "senior federal statistician" persona?
Consistent with the CQS rubric framing. Also constrains the judge's interpretation — a "helpful AI assistant" might score verbose responses higher; a "senior statistician" should penalize verbosity without substance.

---

## Pydantic Schema (for structured output)

```python
from pydantic import BaseModel
from typing import Literal, Optional

class DimensionScore(BaseModel):
    """Score for a single CQS dimension."""
    score: Literal[0, 1, 2]
    justification: str

class ResponseScores(BaseModel):
    """All dimension scores for one response."""
    d1_source_selection: DimensionScore
    d2_methodology: DimensionScore
    d3_uncertainty: DimensionScore
    d4_definitions: DimensionScore
    d5_reproducibility: DimensionScore
    d6_groundedness: DimensionScore

class CQSJudgment(BaseModel):
    """Complete judge output for a query pair."""
    response_a: ResponseScores
    response_b: ResponseScores
    overall_preference: Literal["A", "B", "tie"]
    preference_reasoning: str
```

---

## Open Items

- [ ] Should the prompt include a "confidence" field per dimension? (Adds complexity but enables weighted agreement)
- [ ] Should the framework alignment section be shortened to reduce prompt length / token cost?
- [ ] Validate against 3-5 manually scored examples (H.3) before use in production runs
