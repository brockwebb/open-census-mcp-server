# ADR-011: V2 Evaluation Design Correction — Equal Tool Access

**Status:** Accepted
**Date:** 2026-02-16
**Deciders:** Brock Webb

## Context

The V1 evaluation design (Phase 4B) contained a fundamental confound: control and RAG conditions had no access to Census data tools (`get_census_data`, `explore_variables`), while the pragmatics condition had full tool access. This meant the experiment measured tool access rather than knowledge representation form. 33 of 39 RAG responses directed users to data.census.gov because the model had no way to retrieve data.

A second contamination vector was discovered during V2 spot-checking: `get_census_data` bundles curated pragmatics content (context IDs, guidance text, thread edges) in every response via `retriever.get_guidance_by_parameters()`. Even with equal tool access, all three conditions would receive curated expert judgment through the data tool response payload unless actively sanitized.

## Decision

Redesign the evaluation as a three-condition knowledge representation study with equal data tool access. The single experimental variable is the form of methodology support.

**Conditions:**
- **Control:** `get_census_data` + `explore_variables`, base system prompt, no methodology support. Tool results sanitized to strip pragmatics field.
- **RAG:** Same tools as control, base system prompt augmented with retrieved document chunks (FAISS, top-5, section-level). Tool results sanitized.
- **Pragmatics:** All tools including `get_methodology_guidance`, base prompt plus instruction to call methodology first. Tool results unsanitized — model sees bundled pragmatics.

**Contamination controls:**
- Tool filtering: `get_methodology_guidance` excluded from API tool list for control/RAG.
- Result sanitization: `pragmatics` key stripped from tool result dicts before passing to model for control/RAG. Full unsanitized results logged in ToolCall records for fidelity verification.
- Runtime assertions: halt on filter failure.
- Post-run verification: scan output files for methodology tool calls and context ID references in control/RAG responses.

**Judge design:**
- Three pairwise comparisons: RAG vs Pragmatics, Control vs Pragmatics, Control vs RAG.
- Same rubric, counterbalancing, and vendor panel as V1.
- 6 passes × 3 vendors × 39 queries × 3 comparisons = 2,106 judge records.

**All V1 results archived.** No V1 data enters V2 analysis.

## Consequences

- All 117 Stage 1 responses regenerated with equal tool access and result sanitization.
- Judge pipeline updated for three pairwise comparisons instead of single control-vs-treatment.
- Analysis uses Friedman omnibus test with Wilcoxon post-hoc and Bonferroni correction (α = 0.0167).
- SRS Section 8 rewritten to reflect three-condition design. Terminology changed: "treatment" → "pragmatics," "ablation" removed.
- New SRS requirement VR-030 codifies tool result sanitization.
- Cost: 2,106 judge records vs 702 in V1. Google rate limit (250/day) creates 3-day minimum for Stage 2.
- The MCP server itself is unchanged — sanitization is an evaluation harness concern, not a production concern.

## Alternatives Considered

**Clone MCP with tools removed:** Rejected. The MCP is the production system; creating evaluation-only variants adds maintenance burden and doesn't address the bundled pragmatics issue.

**Configure MCP to optionally omit pragmatics:** Rejected. The bundled pragmatics in `get_census_data` is a design feature for production use. The evaluation harness should control what the model sees, not the production system.

**Two comparisons instead of three:** Rejected. Control vs RAG and Control vs Pragmatics are derivable baselines, but RAG vs Pragmatics is the core research question and deserves direct measurement rather than derived estimates with stacked measurement error.

## References

- `talks/fcsm_2026/2026-02-16_pragmatics_leakage.md` — discovery of bundled pragmatics contamination
- `handoffs/2026-02-16_v2_redo_handoff.md` — V1 post-mortem, V2 design specification
- `talks/fcsm_2026/v2_stage1_data_flow.mermaid.md` — data flow diagram
- SRS Section 8 (docs/requirements/srs.md) — updated verification requirements
