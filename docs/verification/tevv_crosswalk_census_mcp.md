# TEVV Crosswalk: Census MCP Pragmatics Evaluation

**Date:** 2026-02-19
**Status:** Draft
**Frameworks:** FCSM 20-04, FCSM 25-03, NIST AI RMF 1.0
**Companion to:** `federal-survey-concept-mapper/docs/stages/tevv/TEVV_methodology_document.md`

---

## Relationship to Shared Framework

Sections 2.1–2.4 of the concept mapper TEVV document define the framework foundations (FCSM 20-04, NIST AI RMF 1.0, the gap between them, FCSM 25-03). Those foundations apply identically here. This document provides the **project-specific crosswalk** mapping Census MCP evaluation measures to both frameworks.

The concept mapper evaluates an AI **classification** pipeline (barrier codes, feasibility tiers).
The Census MCP evaluates an AI **consultation** pipeline (statistical data retrieval + interpretation).
Same frameworks, different failure modes, different quality measures.

---

## 1. Evaluation Architecture and Framework Alignment

The Census MCP evaluation separates quality measurement from trustworthiness measurement:

| Evaluation Stage | What It Measures | Framework Alignment |
|-----------------|------------------|-------------------|
| Stage 2: CQS rubric (D1–D5) | Consultation quality | FCSM 20-04 (fitness-for-use) |
| Stage 3: Pipeline fidelity | System trustworthiness | NIST AI RMF (valid, reliable, accountable) |
| Stage 4: Expert validation | Ground truth accuracy | Both (bridges quality and trustworthiness) |

This is not a hierarchy — it's a complementary measurement design. Stage 2 answers "is the consultation good?" Stage 3 answers "can we trust the pipeline?" Stage 4 answers "do experts agree?"

---

## 2. Crosswalk Table: Stage 2 CQS Dimensions → FCSM × NIST

### 2.1 D1 — Accuracy of Data Values

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Accuracy & Reliability** | Direct: are the statistical values presented to the user correct? |
| FCSM 20-04 | **Objectivity of Presentation** | Values must be presented without distortion |
| NIST AI RMF | **Valid & Reliable** | System produces correct outputs under expected conditions |

**What it catches:** Hallucinated numbers, transposed values, wrong geographic level, wrong vintage year.

### 2.2 D2 — Completeness of Response

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Relevance** | Response addresses what the user actually needs |
| FCSM 20-04 | **Granularity** | Sufficient detail provided for the use case |
| NIST AI RMF | **Valid & Reliable** | System performs as intended (answering the question asked) |

**What it catches:** Partial answers, missing context, failure to address sub-questions, incomplete geographic coverage.

### 2.3 D3 — Uncertainty Communication

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Accuracy & Reliability** | MOE reporting is core to statistical data quality |
| FCSM 20-04 | **Transparency** | Openness about limitations of estimates |
| FCSM 20-04 | **Scientific Integrity/Credibility** | Statistical standards require uncertainty quantification |
| NIST AI RMF | **Accountable & Transparent** | Limitations documented and communicated |
| NIST AI RMF | **Explainable & Interpretable** | User can understand confidence level of data |

**What it catches:** Missing MOEs, unreported CVs, no mention of sample size limitations, false precision. This is where pragmatics showed the largest effect (d=1.440 vs control) — expert guidance about when and how to report uncertainty.

### 2.4 D4 — Appropriate Sourcing

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Accessibility** | Data sources identified and retrievable |
| FCSM 20-04 | **Transparency** | Methods and sources disclosed |
| FCSM 20-04 | **Scientific Integrity/Credibility** | Proper attribution of statistical claims |
| NIST AI RMF | **Accountable & Transparent** | Traceability of information to authoritative sources |

**What it catches:** Unattributed claims, wrong table references, fabricated variable codes, conflation of ACS 1-year vs 5-year products.

### 2.5 D5 — Fitness-for-Use Guidance

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Relevance** | Guidance helps user determine if data fits their need |
| FCSM 20-04 | **Coherence** | Explains how data relate to other products/vintages |
| FCSM 20-04 | **Transparency** | Discloses limitations specific to the use case |
| NIST AI RMF | **Explainable & Interpretable** | User understands what the data can and cannot support |

**What it catches:** Missing population threshold warnings, no ACS 1-year vs 5-year product guidance, failure to flag geographic boundary changes, no temporal comparison caveats. This is the pragmatics core competency — the 65K threshold, period estimate interpretation, dollar value inflation adjustment.

### 2.6 D6 — Grounding (Binary Gate)

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| NIST AI RMF | Valid & Reliable | Structural design property: treatment conditions ground in authoritative sources; control does not. Pass/fail by design. Verified at Stage 3. |

**What it measures:** Whether the system grounded its response in authoritative sources. Treatment conditions (RAG, pragmatics) ground in Census API returns and methodology documentation. Control does not. D6 is a binary gate, not a scored quality dimension — Stage 3 pipeline fidelity verifies grounding at the claim level.

---

## 3. Crosswalk Table: Stage 3 Pipeline Inspection → FCSM × NIST

### 3.1 Fidelity — Claim-Level Verification

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Accuracy & Reliability** | Pipeline accurately transmits retrieved data |
| NIST AI RMF | **Valid & Reliable** | System produces consistent, correct results |

**What it measures:** For each quantitative claim in the response, does it match what the Census API actually returned? Claims classified as match, mismatch, no_source, calculation_correct, calculation_incorrect.

**Results:** Pragmatics 91.2%, Control 78.3%, RAG 74.6%.

### 3.2 Auditability — Claim Traceability

| Framework | Dimension/Characteristic | Mapping Rationale |
|-----------|-------------------------|-------------------|
| FCSM 20-04 | **Transparency** | Claims can be independently verified |
| FCSM 20-04 | **Accessibility** | Source references provided for verification |
| NIST AI RMF | **Accountable & Transparent** | Mechanisms exist to attribute and verify claims |
| NIST AI RMF | **Explainable & Interpretable** | Claims are specific enough to be meaningful |

**What it measures:** Can a third party trace each claim to its source? Claims classified as auditable (table + vintage + geography + value), partially_auditable, unauditable, non_claim.

**Results:** Pragmatics 29.5%, Control 21.8%, RAG 6.2%.

---

## 4. Crosswalk Table: Evaluation Design Measures → FCSM × NIST

These are process quality measures — properties of the evaluation itself, not of the system being evaluated.

| Evaluation Design Measure | FCSM 20-04 | NIST AI RMF | What It Demonstrates |
|--------------------------|------------|-------------|---------------------|
| **Three-condition symmetric design** — identical rubric applied to control, RAG, pragmatics | Accuracy & Reliability; Coherence | Valid & Reliable | Fair comparison: no condition receives preferential measurement |
| **Multi-vendor LLM judges** — Anthropic, OpenAI, Google score independently | Accuracy & Reliability; Coherence | Valid & Reliable; Fair with Harmful Bias Managed | Vendor independence: scores are not artifacts of a single vendor's biases |
| **Counterbalanced scoring** — judges see responses in alternating presentation order | Accuracy & Reliability | Valid & Reliable | Order invariance: no primacy/recency effects |
| **Model independence (Stage 3)** — Haiku 4.5 verifies Sonnet 4.5 responses | Scientific Integrity/Credibility | Valid & Reliable | No self-verification: the generator doesn't grade its own work |
| **Skinny packet sanitization** — pragmatics guidance stripped from verification evidence | Scientific Integrity/Credibility; Transparency | Accountable & Transparent | Verification uses Census API ground truth, not the treatment itself |
| **Deterministic methodology compliance** — 39/39 queries trigger guidance consultation | Accuracy & Reliability; Scientific Integrity/Credibility | Valid & Reliable | Reproducibility: the "always-ground" approach is testable |
| **Statistical validation** — Friedman omnibus + Wilcoxon pairwise with Holm-Bonferroni | Scientific Integrity/Credibility | Valid & Reliable | Inferential rigor: differences are not attributable to chance |
| **Expert validation protocol** (Stage 4) | Accuracy & Reliability; Scientific Integrity/Credibility | Valid & Reliable | Ground truth: domain experts confirm consultation quality |

---

## 5. FCSM Dimensions Not Directly Addressed

| Dimension | Reason |
|-----------|--------|
| Timeliness/Punctuality | System is interactive (real-time consultation), not a scheduled release product |
| Confidentiality | No respondent-level data processed; all inputs are public aggregate statistics |
| Computer & Physical Security | Standard commercial API security; not a novel contribution |

## 6. NIST Characteristics Not Directly Addressed

| Characteristic | Reason |
|---------------|--------|
| Safe | Consultation errors may mislead users but do not create physical safety risk. Mitigated by uncertainty communication (D3) and fitness-for-use guidance (D5) |
| Secure & Resilient | No adversarial attack surfaces relevant to statistical consultation |
| Privacy-Enhanced | No PII processed; all data is public aggregate statistics from Census API |

---

## 7. D6 Grounding Gate: FCSM × NIST Alignment

D6 is a binary grounding gate, not a scored quality dimension. Treatment conditions (RAG, pragmatics) ground in authoritative sources — Census API returns and methodology documentation — by design. Control does not. Pass/fail. Stage 3 pipeline fidelity verifies grounding at the claim level (see Section 3).

This separation of quality (D1–D5, Stage 2) from trustworthiness (D6, Stage 3) reflects the structural gap between FCSM and NIST identified in Section 1: quality asks "is this consultation useful?" and trustworthiness asks "can we verify this pipeline's claims?" These require different measurement instruments.

---

## 8. Cross-Project Synthesis

Both projects in this research program (Census MCP pragmatics, Federal Survey Concept Mapper) implement the same dual-framework evaluation methodology:

| Element | Census MCP | Concept Mapper |
|---------|-----------|----------------|
| **FCSM-aligned quality** | CQS rubric D1–D5 (consultation quality) | Inter-rater agreement + arbitration (classification quality) |
| **NIST-aligned trustworthiness** | Stage 3 fidelity + auditability | Multi-vendor independence + behavioral analysis |
| **Ground truth validation** | Stage 4 expert review | SME review protocol |
| **AI-specific failure mode** | Semantic smearing (imprecise training data → wrong statistical guidance) | Confident fabrication (LLM invents harmonization paths) |
| **Mitigation** | Pragmatics (curated expert judgment at point of decision) | Multi-vendor agreement + structured arbitration |

The shared insight: **FCSM 20-04 was designed for survey data quality, not AI system quality. NIST AI RMF was designed for AI system trustworthiness, not domain quality. Federal statistical AI systems require both frameworks simultaneously.** Neither can be dropped without losing a critical evaluation dimension.

This dual-framework approach is the methodological contribution. The two projects provide independent implementations demonstrating its applicability across different AI-assisted statistical tasks (data consultation, survey harmonization).
