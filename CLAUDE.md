# CLAUDE.md — Census MCP Server v3

## Project Overview
AI-powered statistical consultant for U.S. Census data via Model Context Protocol (MCP).
Pure Python. No R dependency. Pragmatics-first architecture.

**Core insight:** Census data has a pragmatics problem, not a search problem. Knowing
WHICH data to use and HOW to interpret it matters more than finding it.

## Current State
**Current Phase:** 4B — Systematic Evaluation
- Stage 1 (response generation): ✅ Complete (39 queries, v3)
- Stage 2 (judge scoring): ⏳ OpenAI done, Anthropic + Google pending
- Stage 3 (pipeline fidelity): ✅ Complete (39 queries)

v1/v2 archived to `/Users/brock/Documents/GitHub/archive-opencensusmcp/v2`.

## FCSM Talk Lab Notebook
`talks/fcsm_2026/notes.md` is a **chronological lab notebook**. Add dated entries with lessons learned, insights, and observations. Never edit old entries — append corrections as new entries. Reference files in the same directory store polished context (e.g., `reference_*.md`).

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

**Content principles — MUST follow when authoring or extracting:**

1. **Encode principles, not instances.** Write "independent cities are county-equivalents
   that break the nesting assumption" — NOT "Virginia has 38 independent cities" or
   "Baltimore FIPS is 24:510". The LLM knows specific instances from training data.
   Pragmatics encode the *judgment* the LLM doesn't have.

2. **No lookup tables.** FIPS codes, state lists, city enumerations, variable codes —
   these belong in the geographic resolver, API layer, or LLM training data. Pragmatics
   encode *when and why* to use them, not the data itself.

3. **No LLM instructions.** Don't write "Always warn the user..." or "You must check..."
   Write the factual context: "MOE exceeding the estimate indicates unreliability."
   The LLM decides what to do with it.

4. **Test: Would a statistician say this to a colleague?** If yes, it's a pragmatic.
   If it reads like a database record, a prompt instruction, or an encyclopedia entry,
   it's in the wrong layer.

5. **1-3 sentences per item.** Dense, actionable, factual. No jargon without explanation.
   No hedging. No "it is important to note that..." filler.

6. **3-6 triggers per item.** Triggers are retrieval hooks, not tags. Over-triggering
   destroys retrieval specificity.

7. **Latitude must be justified.** `none` = hard constraint ("ACS 1-year requires 65K+ pop").
   `narrow` = strong guidance with rare exceptions. `wide` = genuinely context-dependent.
   `full` = background FYI. Most items should be `none` or `narrow`.

8. **Every item needs provenance grounded in documentation, NEVER from LLM training data.**
   Structured object with `sources` list (each source has document/section/page/extraction_method),
   `confidence` level (grounded/interpreted/expert_judgment), and optional `synthesis_note` and
   `limitations`. Unsourced expert opinion is not auditable. LLM training data may contain
   confabulations — the pragmatics layer exists to provide *auditable* expert judgment with
   traceable provenance. When authoring: read the source document first, extract the judgment,
   cite it with page/section. Never reverse-engineer citations onto pre-existing beliefs. If no
   source document exists for a domain, download it BEFORE authoring content. Source documents
   live in `docs/references/` and `knowledge-base/source-docs/`.

9. **Thread edges are for retrieval depth, not ontology.** Connect items a user might
   need together. Don't over-connect — if everything links to everything, traversal
   is useless.

**Staging directory:** `staging/{domain}/{category}.json` — one file per category.
Manifest in `staging/{domain}/manifest.json`. Compile with `python scripts/compile_all.py`.

## Implementation Schedule
**See:** `docs/architecture/implementation_schedule.md` for detailed task breakdown.

**Current Phase:** 4B — Systematic Evaluation

**Dependency order:**
```
Phase 0A (API Client) ────────────────────┐
                                           ├──► Phase 3 (MCP) ──► Phase 4 (Eval)
Phase 0B (Geography) ─────────────────────┤
                                           │
Phase 1C (Pack Pipeline) ──► Phase 2 (Pragmatics)┘
         │
Phase 1D (Seed Content) ───┘
```

Track A and B have no internal dependencies — start there.

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
- **Contains:** Context nodes (25 ACS), Pack nodes (1), thread edges (14 RELATES_TO, 17 BELONGS_TO)
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
- **Evaluation:** Three-stage CQS pipeline: (1) response generation, (2) multi-model judge scoring on D1-D5, (3) automated pipeline fidelity verification
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
`/Users/brock/Documents/GitHub/archive-opencensusmcp/v2` — Previous implementation. Useful as archaeology, not as code.

**What's there:**
- `knowledge-base/2023_ACS_Enriched_Universe.json` — 1GB+ enriched variable metadata for ALL 2023 ACS variables and tables. Dual lookup system with massive metadata per variable.
- `knowledge-base/concepts/` — Concept templates, ontology attempts
- `knowledge-base/methodology-db/` — Processed methodology content
- `knowledge-base/source-docs/` — May overlap with v3 source-docs
- `knowledge-base/variables-db/`, `variables-faiss/`, `vector-db/` — Multiple generations of embedding indexes
- `evaluation/` — Previous eval attempts
- 47+ debug/test/check scripts in root — diagnostic archaeology of what went wrong

**Why it failed (key lesson):**
RAG over Census variable metadata hits a dimensionality wall. When everything is statistical data about demographic variables, embeddings cluster too tightly — semantic smearing. A 1GB enriched variable file for ONE survey couldn't be effectively searched because the embedding space couldn't differentiate "median household income" from "median family income" from "aggregate income" with enough resolution. The problem isn't retrieval — it's that the domain is too semantically homogeneous for general-purpose embeddings to navigate.

This is WHY we moved to pragmatics (structured expert context with latitude) instead of RAG over metadata.

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
