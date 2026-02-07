# CLAUDE.md — Census MCP Server v3

## Project Overview
AI-powered statistical consultant for U.S. Census data via Model Context Protocol (MCP).
Pure Python. No R dependency. Pragmatics-first architecture.

**Core insight:** Census data has a pragmatics problem, not a search problem. Knowing
WHICH data to use and HOW to interpret it matters more than finding it.

## Current State
Fresh rebuild. v1/v2 archived to `/Users/brock/Documents/GitHub/archive-opencensusmcp/v2`.
Week 1 of 5-week sprint toward FCSM conference talk (empirical evaluation of pragmatic rules).

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
talks/fcsm_2026/       # FCSM conference talk materials
handoffs/              # Thread handoff docs (gitignored)
cc_tasks/              # Claude Code task files (gitignored)
tmp/                   # Scratch space (gitignored)
```

## Key Conventions
- **Never edit files without explicit permission.** Output to artifacts or chat.
- **CC tasks go in `cc_tasks/`** with date prefix: `YYYY-MM-DD_description.md`
- **Thread handoffs go in `handoffs/`** with date prefix
- **Scratch work goes in `tmp/`**
- All three directories are gitignored.

## Implementation Schedule
**See:** `docs/architecture/implementation_schedule.md` for detailed task breakdown.

**Current Phase:** 0A — Census API Client

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

## Technical Context
- **Census API:** Direct Python HTTP calls to `api.census.gov`
- **Pragmatic context:** Structured JSON in `staging/`, compiled to SQLite packs
- **Evaluation:** Conversational Quality Score (CQS) protocol comparing baseline LLM vs pragmatics-augmented responses
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
- Don't use the term "crystal" anywhere — it's purged
- Don't build throwaway MVPs — build the real thing correctly from the start
