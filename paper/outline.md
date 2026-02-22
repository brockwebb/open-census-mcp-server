# Paper Outline — UPDATED to match draft sections
## Pragmatics as Point-of-Decision Expert Judgment for Federal Statistical Data

**Target:** arxiv preprint (cs.AI or cs.IR) → FCSM 2026 presentation
**Status:** Draft v1 complete — 2026-02-21
**Sections:** 8 + appendices (~7,700 words body)

---

## Section → File Map

| # | Section | File | ~Words |
|---|---------|------|--------|
| 0 | Abstract | `00_abstract.md` | TODO |
| 1 | Introduction | `01_introduction.md` | 900 |
| 2 | The Semantic Smearing Problem | `02_semantic_smearing.md` | 1,000 |
| 3 | Pragmatics — Structured Expert Judgment | `03_pragmatics.md` | 1,200 |
| 4 | Method | `04_method.md` | 1,100 |
| 5 | Results | `05_results.md` | 1,100 |
| 6 | Discussion | `06_discussion.md` | 1,300 |
| 7 | Limitations and Future Work | `07_limitations_future.md` | 800 |
| 8 | Conclusion | `08_conclusion.md` | 300 |
| R | References | `09_references.md` | — |
| A | Appendices | `10_appendices.md` | — |

---

## Figures and Tables Plan

### Figures
| ID | Description | Section | Source |
|----|-------------|---------|--------|
| F1 | Semiotic framework (syntax→semantics→pragmatics) with Census examples | §1 | Create |
| F2 | Semantic smearing: enrichment experiment results (MiniLM + RoBERTa) | §2 | `talks/fcsm_2026/analysis/` |
| F3 | Anatomy of a pragmatic context item (5 components) | §3 | Create |
| F4 | Latitude model — none/narrow/wide/full with examples | §3 | Create |
| F5 | Three-condition experimental design diagram | §4 | Create |
| F6 | Evaluation pipeline (3 stages) | §4 | `talks/fcsm_2026/evaluation_pipeline_overview.mermaid.md` |
| F7 | Cohen's d effect sizes forest plot (all comparisons × dimensions) | §5 | `results/v2_redo/stage2/analysis/` |
| F8 | Fidelity scores by condition (bar chart) | §5 | `results/v2_redo/stage3/analysis/` |
| F9 | Cost-effectiveness: CQS per marginal dollar | §6 | Numbers registry COST section |

### Tables
| ID | Description | Section | Source |
|----|-------------|---------|--------|
| T1 | CQS composite scores by condition with bootstrap CIs | §5 | S2-010–012, S2-015–017 |
| T2 | Friedman omnibus + Wilcoxon post-hoc with Holm correction | §5 | S2-001–012 |
| T3 | Per-dimension effect sizes (d values, all 5 dims × 3 comparisons) | §5 | S2-020–042 |
| T4 | Stratum analysis: normal vs edge effect sizes | §5 | SA-001–022 |
| T5 | Pipeline fidelity summary (claims, auditability, fidelity by condition) | §5 | S3-001–012 |
| T6 | Cost per query by condition and model tier | §6 | COST-001–013 |
| T7 | Test battery composition by category | App A | `queries.yaml` |
| T8 | Pragmatic item catalog summary (36 items by category/latitude) | App D | `staging/acs/` |

---

## Appendices (revised)

### A. Complete Test Battery
- Table of 39 queries by category, edge case flag, topic
- Source: `src/eval/battery/queries.yaml`

### B. CQS Rubric Specification
- Full 5-dimension rubric with scoring criteria
- Source: `src/eval/judge_prompts.py` or `docs/verification/cqs_rubric_specification.md`

### C. System Prompts
- Base system prompt and pragmatics-specific prompt segment
- Source: `src/eval/agent_loop.py`

### D. Pragmatic Item Catalog
- Full catalog of 36 items with context text, latitude, triggers, thread edges
- Source: `staging/acs/*.json`

---

## Citation Files (raw material, not in paper)
- `paper/citations/ethayarajh_2019_anisotropy.md`
- `paper/citations/semantic_smearing_evidence.md`
- `paper/citations/d3_uncertainty_deep_dive.md`
- `paper/citations/ncses_norc_mlmu25.md`
- `paper/citations/nsf_norc_landscape.md`
- `paper/citations/federal_data_evolution_arc.md`
- `paper/citations/rag_graphrag_cost_comparison.md`
- `paper/citations/stochastic_tax_framing.md`
- `paper/core_argument.md`
