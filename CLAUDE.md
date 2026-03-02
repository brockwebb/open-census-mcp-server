# CLAUDE.md — Census MCP Server v3

## Project Overview
AI-powered statistical consultant for U.S. Census data via Model Context Protocol (MCP).
Pure Python. No R dependency. Pragmatics-first architecture.

**Core insight:** Census data has a pragmatics problem, not a search problem. Knowing
WHICH data to use and HOW to interpret it matters more than finding it.

## Current State
**Current Phase:** 4B — Systematic Evaluation (V2 Redo)
- V1 results archived (confounded tool access — see ADR-011)
- Stage 1 V2 (response generation): ✅ Complete (39 queries × 3 conditions)
- Stage 2 V2 (judge scoring): ✅ Complete — all 3 pairwise comparisons, 2106 records
- Aggregate analysis: ✅ Complete — Prag d=1.440 vs Ctrl, d=0.922 vs RAG (certified)
- Stratum analysis: ✅ Complete — no overfit, d=2.347 normal, d=1.135 edge (SA-001–022)
- Cost analysis: ✅ Complete — pragmatics 2.2× more cost-effective than RAG (COST-001–013)
- Stage 3 (fidelity verification): ✅ Complete (Prag 91.2%, Control 78.3%, RAG 74.6%)
- Stage 4 (expert validation): ⏳ Pending
- Paper outline: ✅ Up to date — `paper/outline.md`, numbers in `paper/numbers_registry.md`
- Lab notebook: talks/fcsm_2026/ (dated entries with run details, QC, decisions)

v1/v2 archived to `/Users/brock/Documents/GitHub/archive-opencensusmcp/v2`.

## FCSM Talk Lab Notebook
`talks/fcsm_2026/notes.md` is a **chronological lab notebook**. Add dated entries with lessons learned, insights, and observations. Never edit old entries — append corrections as new entries. Reference files in the same directory store polished context (e.g., `reference_*.md`).

## FCSM 2026 Deliverables
**Master checklist:** `talks/fcsm_2026/fcsm_master_checklist.md`
**Talk script:** `talks/fcsm_2026/pragmatics_talking_script_v3.md`
**TEVV crosswalk (canonical, publication-ready):** `/Users/brock/Documents/GitHub/central_library/crosswalks/fcsm_nist/FCSM_NIST_Crosswalk_Article.md`
**TEVV crosswalk (earlier drafts, superseded):** `reports/tevv/pure_crosswalk_part1.md` + `part2.md`
**TEVV methodology:** `reports/tevv/TEVV_methodology_document.md`
**CQS rubric:** `docs/verification/cqs_rubric_specification.md`
**Figure/table registry:** `paper/assets/figure_table_map.yaml` — single source of truth for all figures (F1–F9) and tables (T1–T8); update here first when adding or modifying assets
**Deadline:** ~March 5, 2026 (slide deck). See checklist for daily targets.

## Repo Structure
Canonical structure is defined in `docs/requirements/srs.md` section 2 (that is law).
Quick reference:
```
docs/requirements/     # ConOps, SRS
docs/design/           # Pragmatics vocabulary, reference card, extraction pipeline spec
docs/architecture/     # System architecture
docs/decisions/        # ADRs
docs/verification/     # Evaluation results
docs/lessons_learned/  # Project narrative from v1/v2
src/census_mcp/        # Runtime package (api/, geography/, pragmatics/, tools/)
staging/               # Pack content source of truth (JSON, version controlled)
packs/                 # Compiled SQLite packs (build artifacts, gitignored)
knowledge-base/        # Source material (source-docs/ gitignored)
scripts/               # Build, compile, extraction scripts
tests/                 # unit/, integration/, evaluation/
src/eval/              # CQS evaluation pipeline (harness, judges, fidelity)
results/               # Evaluation outputs (gitignored)
docs/test/             # Human evaluator scoring materials
talks/fcsm_2026/       # FCSM conference talk materials
handoffs/              # Thread handoff docs (gitignored)
cc_tasks/              # Claude Code task files (gitignored)
tmp/                   # Scratch space (gitignored)
```

## Key Conventions
- **Never edit files without explicit permission.** Output to artifacts or chat.
- **TEVV every task.** Test-Evaluate-Verify-Validate before moving on. (NIST AI RMF 2023)
- **Prompt = how to think, Packs = what to know.** Never duplicate domain knowledge in both.
- **Adding knowledge?** See `docs/design/pragmatics_authoring_guide.md`
- **CC tasks go in `cc_tasks/`** with date prefix: `YYYY-MM-DD_description.md`
- **Thread handoffs go in `handoffs/`** with date prefix
- **Scratch work goes in `tmp/`**
- All three directories are gitignored.

## Pragmatics Content Quality Rules

**What is a pragmatic?** A context item encoding expert statistical judgment about
fitness-for-use — what a senior statistician would tell a colleague before they use
data. Pragmatics are NOT rules, constraints, lookup tables, or LLM instructions.
They are structured expert knowledge with latitude (Morris 1938 semiotics).

**Canonical schema:** `src/census_mcp/pragmatics/models.py` (Pydantic). All content
MUST conform. Key fields: `context_id`, `domain`, `category`, `latitude`, `context_text`,
`triggers` (NOT `tags`), `thread_edges`, `provenance` (required: sources list with document/section/page, confidence level, optional synthesis_note and limitations).

**Content principles (summary) — full details in `docs/design/pragmatics_authoring_guide.md`:**
- **Principles, not instances** — encode the judgment, not the data. The LLM knows FIPS codes; it doesn't know when the nesting assumption breaks.
- **No lookup tables, no LLM instructions** — factual context only ("MOE exceeding estimate indicates unreliability"), not directives ("always warn the user").
- **1-3 sentences, 3-6 triggers, latitude justified** — `none`=hard constraint, `narrow`=strong guidance, `wide`=context-dependent, `full`=background FYI.
- **Provenance from documentation only** — read source first, cite page/section. Never reverse-engineer citations or use LLM training data as source.
- **Thread edges for retrieval depth** — connect items a user might need together; don't over-connect.

**Staging directory:** `staging/{domain}/{category}.json` — one file per category.
Manifest in `staging/{domain}/manifest.json`. Compile with `python scripts/compile_all.py`.

## Eval Pipeline Commands
All scripts runnable as modules from repo root:
```bash
python -m src.eval.aggregate_analysis          # Stage 2 CQS aggregate + effect sizes
python -m src.eval.stratum_analysis            # Normal vs edge stratum breakdown
python -m src.eval.overhead_analysis           # Token/resource overhead per condition
python -m src.eval.cost_analysis               # Dollar cost per query per condition
python -m src.eval.fidelity_aggregate          # Stage 3 fidelity scores
python -m src.eval.fidelity_qc                 # Stage 3 QC checks (VR-097–100)
python -m src.eval.verify_registry_counts      # Verify numbers_registry.md claims
python scripts/compile_all.py                  # Compile staging/ → packs/ SQLite
```

## Implementation Schedule
**See:** `docs/architecture/implementation_schedule.md` for detailed task breakdown.
**Current Phase:** 4B — Systematic Evaluation

## Vocabulary
All terms defined in `docs/design/pragmatics_vocabulary.md` (normative). Key terms:
- **Pragmatics** — fitness-for-use expert judgment layer (Morris 1938)
- **Pack** — domain-specific shippable bundle (compiles to SQLite)
- **Thread** — connected graph path through context nodes
- **Context** — expert knowledge content (not rules, not constraints)
- **Latitude** — freedom to bend: none / narrow / wide / full
- **NEVER use:** crystal, constraint, rule, guardrail, directive, ontology, weight, severity

## Neo4j Pragmatics Database (Authoring Environment)
- **Database name:** `pragmatics` — prefix ALL Cypher queries with `USE pragmatics`
- **Contains:** Context nodes (36 ACS), Pack nodes (1), thread edges (14 RELATES_TO, 17 BELONGS_TO)
- **This is the authoring/research environment per ADR-001**
- **Pipeline:** Neo4j → export script → staging JSON → compile_pack.py → SQLite packs
- **Arnold/training graph is in the default database — DO NOT mix them**
- **Round-trip scripts:** `scripts/neo4j_to_staging.py` (export) and `scripts/staging_to_neo4j.py` (import). Require NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD env vars.
- **LLM extraction scripts:** `scripts/extract/` is empty — future home of PDF chunking + LLM extraction (MinerU, agent swarms). Not yet implemented.
- **Schema:** All staging files use canonical Pydantic format (triggers, thread_edges, structured source). Old flat format purged 2026-02-08.

## Neo4j MCP Configuration (Claude Desktop)
- **neo4j-pragmatics** — points to `pragmatics` database (authoring environment for Context/Pack nodes)
- **neo4j-quarry** — points to `quarry` database (raw KG extraction target)
- Both accessible directly from Claude Desktop MCP tools. No Python scripts needed to query either database.
- Previous single-database limitation resolved by running two separate MCP server instances.

## Neo4j Raw Knowledge Graph (Quarry)
- **Database name:** `quarry` (separate from `pragmatics` database)
- **Schema:** `docs/design/raw_kg_schema.md` v3.1 — 4-layer harvest architecture
- **Architecture:** Extract facts (Layer 1) → pattern-match against standards (Layer 2) → curate (Layer 3) → export to pragmatics DB
- **Key insight:** Fitness implications are DERIVED by Cypher queries, not extracted from documents
- **Tool:** Custom extraction pipeline in `scripts/quarry/` (ADR-008, ADR-009). Replaces llm-graph-builder.
- **llm-graph-builder:** Installed at `~/Documents/GitHub/llm-graph-builder` for reference only. See ADR-008 for rationale.
- **Large quarry operations:** Use Claude Code to conserve context window in Claude Desktop.
- **NEXT:** Build `scripts/quarry/` toolkit (Phase 5B). Section-aware chunking, direct structured extraction, entity resolution.

## Key Architecture Docs for Pragmatics
- `docs/decisions/ADR-001-neo4j-authoring-sqlite-runtime.md` — Authoring vs runtime separation
- `docs/architecture/knowledge_pack_management.md` — Full pipeline architecture
- `docs/design/extraction_pipeline.md` — Source docs → LLM extraction → staging
- `docs/design/pragmatics_authoring_guide.md` — How to add content
- `docs/design/pragmatics_vocabulary.md` — Normative terminology
- `docs/design/pragmatics_data_flow.md` — End-to-end data flow explainer
- `docs/design/theoretical_foundations.md` — ReAct, OODA, Cynefin, Morris semiotic triad
- `src/census_mcp/pragmatics/models.py` — Pydantic models (canonical schema)
- `docs/design/raw_kg_schema.md` — Raw KG schema v3.1 (13 node types, 16 relationships, 4-layer harvest architecture)
- `docs/design/kg_schema_design_narrative.md` — Design process narrative (multi-model adversarial review)
- `docs/design/reviews/README.md` — External review audit trail
- `docs/decisions/ADR-007-kg-first-authoring.md` — KG-first authoring workflow
- `docs/decisions/ADR-008-custom-extraction-pipeline.md` — Why llm-graph-builder was replaced
- `docs/decisions/ADR-009-quarry-toolkit-shippable.md` — Quarry toolkit ships as project component
- `docs/design/quarry_extraction_pipeline.md` — Quarry pipeline design (Docling + direct LLM extraction)

## Technical Context
- **Census API:** Direct Python HTTP calls to `api.census.gov`
- **Pragmatic context:** Authored in Neo4j (`USE pragmatics`), exported to JSON in `staging/`, compiled to SQLite packs in `packs/`
- **Evaluation:** Four-stage CQS pipeline: (1) response generation, (2) multi-vendor pairwise judge scoring on D1-D5 with 6-pass counterbalancing, (3) automated fidelity verification, (4) expert validation. Config: src/eval/judge_config.yaml
- **Eval config:** `src/eval/judge_config.yaml` (all parameters, SRS C-006)
- **No vector DB, no RAG over metadata** — structured context with latitude, not embeddings
- **No ontology layer** — the LLM's weights are the semantic layer; we supply pragmatics only

## Key Lessons from v1/v2
- **Geography resolver is critical** — FIPS resolution was the one thing that actually worked and mattered. Prioritize.
- **RAG over variable metadata fails** — Census domain is too semantically homogeneous for embeddings to differentiate. Semantic smearing.
- **Don't rebuild the semantic layer** — COOS/enrichment/ontology work was duplicating what the LLM already knows.
- **Batch API calls are essential** — real analysis needs multi-variable, multi-geography retrieval, not single lookups.
- **The MCP is a component** — design tools as composable, stateless units for agentic workflows.

## Archive Reference
`/Users/brock/Documents/GitHub/archive-opencensusmcp/v2` — Previous implementation (v1/v2). Contains embedding indexes, 1GB+ enriched variable metadata, ontology attempts, and 47+ diagnostic scripts. Useful as archaeology, not as code. Key lesson: RAG over semantically homogeneous Census metadata causes semantic smearing — this is why we moved to pragmatics.

## What NOT to Do
- Don't add R, tidycensus, or Docker infrastructure (that's v1/v2)
- Don't build ontology, COOS, or semantic enrichment layers — the LLM handles semantics
- Don't use RAG over variable metadata — semantic smearing kills it
- Don't create files outside the repo without asking
- Don't use web search for Census data — use Census API or project knowledge base
- Tool is `get_census_data` not `get_acs_data` (legacy name accepted but deprecated)
- Don't use the term "crystal" anywhere — it's purged
- Don't use "hallucination" — the correct term is **confabulation** (pattern-completion from training distribution, not perception of nonexistent stimuli)
- Don't build throwaway MVPs — build the real thing correctly from the start
- Don't add external databases (Neo4j, Postgres, etc.) — SQLite only per SRS C-002
- Don't add dependencies without justification — minimal footprint, prove we need it first
