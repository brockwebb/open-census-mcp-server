# Paper Outline — Knowledge Representation Study
## Pragmatics as Point-of-Decision Expert Judgment for Federal Statistical Data

**Target:** arxiv preprint (cs.AI or cs.IR) → FCSM 2026 presentation
**Status:** Outline v1 — 2026-02-16

---

## How to Use This File

This is the single source of truth for paper structure. Each section has:
- **Thesis:** What this section argues (1-2 sentences)
- **Evidence:** File paths (relative to project root) to supporting artifacts
- **Figures/Tables:** What visual or quantitative output is needed
- **Tags:** `{paper}` `{slides:main}` `{slides:backup}` `{slides:appendix}`

When sections grow complex, create `paper/sections/NN_section_name.md` with detailed content. This file remains the TOC and index.

---

## 1. Introduction {paper} {slides:main}

**Thesis:** Federal statistical agencies have invested heavily in making data AI-ready (syntax, semantics) but implementation reveals a missing third layer — pragmatics — the expert judgment about fitness-for-use that LLMs cannot learn from training data alone.

**Evidence:**
- `talks/fcsm_2026/reference_fcsm_ai_ready_data_landscape.md`
- `talks/fcsm_2026/reference_core_thesis.md` § "The Problem We're NOT Solving"
- `docs/research/rag_fallacy_thinking.md`

**Figures/Tables:**
- Figure 1: Semiotic framework diagram (syntax → semantics → pragmatics) with Census examples at each layer. {slides:main}
- Table 1: AI-ready data landscape — what agencies provide vs what practitioners need. {slides:backup}

---

## 2. The Semantic Smearing Problem {paper} {slides:main}

**Thesis:** LLMs exhibit semantic smearing in statistical domains — they conflate information that should remain distinct across survey years, estimate types, geographic levels, and methodological contexts. The model doesn't lack knowledge; it lacks precision.

**Evidence:**
- `talks/fcsm_2026/reference_core_thesis.md` § "The Actual Problem," § "What the Model Already Knows"
- `results/v2_redo/stage1/control_responses_*.jsonl` — concrete examples of smearing

**Figures/Tables:**
- Figure 2: Example query showing control vs pragmatics response side-by-side. {slides:main}
- Table 2: Taxonomy of smearing types observed (temporal, geographic, product, threshold). {paper}

---

## 3. Pragmatics: Structured Expert Judgment {paper} {slides:main}

**Thesis:** Pragmatic context items are structured expert judgment with calibrated uncertainty (latitude), provenance, and defined retrieval triggers. They deliver clinical judgment at the point of decision — not comprehensive retrieval, but the precise guidance a senior statistician would provide.

**Evidence:**
- `talks/fcsm_2026/reference_core_thesis.md` § "What Pragmatics Actually Do," § "Three Layers of Noise"
- `docs/design/pragmatics_vocabulary.md`
- `docs/decisions/ADR-002-grounding-not-rag.md`
- `docs/decisions/ADR-003-reasoning-model-requirement.md`
- `docs/decisions/ADR-004-agent-reasoning-loop.md`
- `staging/acs/` — 35 pragmatic items
- `talks/fcsm_2026/notes.md` § "V-Information as Formal Basis"

**Figures/Tables:**
- Figure 3: Anatomy of a pragmatic context item (context_id, text, latitude, provenance, triggers). {slides:main}
- Figure 4: Latitude model — none/narrow/wide/full with Census examples. {slides:main}
- Table 3: The 35 pragmatic items by category and latitude level. {slides:backup}

---

## 4. System Architecture {paper} {slides:main}

**Thesis:** The Census MCP Server implements pragmatics as a composable tool in the Model Context Protocol. The MCP handles validation, fetching, and bundling; the calling LLM performs reasoning. Pragmatics are delivered as structured data alongside Census API responses.

**Evidence:**
- `docs/requirements/srs.md`
- `docs/requirements/conops.md`
- `src/census_mcp/tools/census_tools.py`
- `src/census_mcp/pragmatics/`
- `docs/decisions/ADR-001-neo4j-authoring-sqlite-runtime.md`
- `talks/fcsm_2026/ov0_sidecar_architecture.mermaid.md`
- `talks/fcsm_2026/v2_stage1_data_flow.mermaid.md`

**Figures/Tables:**
- Figure 5: High-level architecture — user → LLM agent → MCP → Census API + pragmatics. {slides:main}
- Figure 6: Production data flow showing tool response with bundled pragmatics. {slides:backup}

---

## 5. Extraction Pipeline {paper} {slides:backup}

**Thesis:** Pragmatic content is extracted from authoritative source documents through a structured pipeline: PDF → section-aware chunking → LLM extraction → knowledge graph → harvest → curation → SQLite packs. Each stage is a noise reduction step.

**Evidence:**
- `docs/decisions/ADR-008-custom-extraction-pipeline.md`
- `docs/decisions/ADR-009-quarry-toolkit-shippable.md`
- `docs/decisions/ADR-010-evolutionary-vocabulary.md`
- `scripts/quarry/`
- `docs/design/quarry_extraction_pipeline.md`

**Figures/Tables:**
- Figure 7: Extraction pipeline stages with noise reduction at each step. {slides:backup}
- Table 4: Extraction quality metrics — nodes by type, relationship distribution, MENTIONS=0. {paper}

---

## 6. Evaluation Design {paper} {slides:main}

**Thesis:** We evaluate through a knowledge representation study comparing three conditions with equal data tool access. The single variable is methodology support form: none, retrieved document chunks, or curated expert judgment.

**Evidence:**
- `docs/decisions/ADR-011-v2-evaluation-design-correction.md`
- `docs/requirements/srs.md` § 8
- `src/eval/battery/queries.yaml`
- `src/eval/agent_loop.py`
- `src/eval/harness.py`
- `talks/fcsm_2026/2026-02-16_pragmatics_leakage.md`
- `talks/fcsm_2026/evaluation_pipeline_overview.mermaid.md`

**Figures/Tables:**
- Figure 8: Three-condition experimental design (control/RAG/pragmatics). {slides:main}
- Figure 9: Four-stage evaluation pipeline. {slides:main}
- Table 5: Test battery composition — categories, counts, edge case rationale. {paper}
- Table 6: Experimental controls — tool filtering, result sanitization, contamination checks. {paper}

---

## 7. Results {paper} {slides:main}

**Thesis:** Pragmatics achieves very large effect sizes (d=1.440 vs control, d=0.922 vs RAG) across all query types. Benefits are not limited to edge cases — effect is larger on normal queries (d=2.347) than edge cases (d=1.135), ruling out overfit. Fidelity gap: pragmatics 91.2% vs RAG 74.6% vs control 78.3%.

**Evidence:**
- `results/v2_redo/stage1/` — 117 responses (39 queries × 3 conditions)
- `results/v2_redo/stage2/analysis/aggregate_statistics.md` — CQS scores (CERTIFIED)
- `results/v2_redo/stage2/analysis/stratum_analysis.md` — normal vs edge breakdown (COMPUTED)
- `results/v2_redo/stage3/analysis/fidelity_summary.md` — fidelity/auditability (CERTIFIED)
- Numbers: `paper/numbers_registry.md` Sections 3, 3f, 4

**Key results available:**
- Omnibus Friedman χ²(2, N=39) = 42.01, p < 0.001 (registry: S2-001)
- Pragmatics vs Control: Δ=+0.539, d=1.440 (very large), p < 0.001 (registry: S2-010)
- Pragmatics vs RAG: Δ=+0.385, d=0.922 (large), p < 0.001 (registry: S2-011)
- RAG vs Control: Δ=+0.154, d=0.546 (medium), p=0.0017 (registry: S2-012)
- D3 (Uncertainty Calibration) largest effect: d=1.353 Prag vs Ctrl (registry: S2-032)
- Normal queries: d=2.347 Prag vs Ctrl — no overfit (registry: SA-001)
- Edge queries: d=1.135 Prag vs Ctrl (registry: SA-010)
- Pragmatics fidelity 91.2% vs RAG 74.6% vs Control 78.3% (registry: S3-001–003)

**Figures/Tables:**
- Figure 10: Cohen's d effect sizes by dimension per comparison (forest plot). {slides:main}
- Figure 11: Fidelity scores by condition. {slides:main}
- Table 7: CQS composite scores by condition with bootstrap CIs. {slides:main}
- Table 8: Friedman + Wilcoxon post-hoc. {paper}
- Table 9: Bias check results (position, self-enhancement, verbosity). {paper}
- Table 10: Per-stratum effect sizes (normal vs edge, d values). {slides:backup} — `stratum_analysis.md`
- Table 11: Judge agreement (Krippendorff's alpha). {paper}

---

## 8. Discussion {paper} {slides:main}

**Thesis:** Information selectivity at inference time follows the same pattern as training data curation — precision beats volume. The three-layer noise model (training data, expert judgment, latitude) provides a generalizable framework.

**Evidence:**
- `talks/fcsm_2026/reference_core_thesis.md` § "Three Layers of Noise"
- `talks/fcsm_2026/notes.md` § "V-Information as Formal Basis"
- Xu et al. (2020) V-information — formal grounding
- Kahneman, Sibony & Sunstein (2021) Noise — expert variance

**Subsections:**
- 8.1 Why 35 items beat 311 chunks — selectivity principle. *Cost data available: pragmatics 2.2× more cost-effective than RAG per CQS point gained (COST-005). Registry: Section 3h.*
- 8.2 Latitude as calibrated uncertainty over expertise
- 8.3 Implications for federal statistical agencies — the sidecar pattern. *Cost data: $0.09/query marginal cost for expert statistical guidance (Sonnet 4.5, COST-003). Negligible at Opus pricing too ($0.14/query, COST-012).*
- 8.4 The Jobs Doctrine — obsolescence over compensatory complexity

**Figures/Tables:**
- Figure 12: Information selectivity — training data curation ↔ expert judgment curation. {slides:main}

---

## 9. Limitations {paper}

**Thesis:** Honest accounting of scope and constraints.

- n=39 queries, single caller model (Sonnet 4.5), single domain (ACS)
- LLM-as-judge biases mitigated but not eliminated
- Pragmatic content hand-curated by one expert — scalability unproven
- No user study — evaluation is automated
- Generalization requires domain-specific pragmatics

---

## 10. Future Work {paper} {slides:backup}

**Thesis:** Cross-survey expansion, scalable content generation, community-maintained pragmatics ecosystem.

**Evidence:**
- `talks/fcsm_2026/ov0_sidecar_architecture.mermaid.md`

**Items:**
- CPS, SIPP, decennial — shared geographic intelligence
- Hybrid authoring: LLM-assisted batch generation + human review
- Community contribution model
- User study with actual Census data consumers

---

## 11. Conclusion {paper} {slides:main}

**Thesis:** Pragmatics fills the gap between AI-ready data (syntax, semantics) and practitioner needs (expert judgment). Operational system, empirical validation, generalizable principle.

---

## Appendices {paper} {slides:appendix}

### A. Complete Test Battery
- `src/eval/battery/queries.yaml`

### B. CQS Rubric
- `src/eval/judge_prompts.py`

### C. System Prompts
- `src/eval/agent_loop.py` — BASE_SYSTEM_PROMPT, PRAGMATICS_SYSTEM_PROMPT

### D. Design Correction Post-Mortem
- `docs/decisions/ADR-011-v2-evaluation-design-correction.md`
- `talks/fcsm_2026/2026-02-16_pragmatics_leakage.md`

### E. Pragmatic Item Catalog
- `staging/acs/`

---

## Publishing Strategy

### arxiv Preprint
- Post BEFORE FCSM presentation to establish priority date
- Category: cs.AI or cs.IR (or cross-list both)
- Requires endorsement from existing arxiv author in category
- No PhD required, no peer review — it's a preprint server
- Cite the arxiv preprint in FCSM slides

### FCSM 2026 Presentation
- Conference talk establishes institutional credibility
- Slides filter from this outline using `{slides:main}` tags
- Backup slides from `{slides:backup}` tags
- arxiv preprint link on final slide

### Priority Chain
arxiv preprint (date-stamped) → FCSM talk (credibility) → journal submission (optional, peer review)
