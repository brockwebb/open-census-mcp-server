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
```
docs/                  # Systems engineering docs (SE template)
  requirements/        # ConOps, SRS
  architecture/        # System architecture
  decisions/           # ADRs, trade studies
  design/              # Detailed design
  verification/        # V&V, evaluation results
  lessons_learned/     # Project narrative from v1/v2
knowledge-base/        # Source material & extracted rules
  source-docs/         # Census methodology PDFs (gitignored)
  rules/               # Pragmatic rules JSON (the deliverable)
  methodology/         # Processed methodology content
src/                   # MCP server source (Week 2+)
tests/                 # Evaluation harness & unit tests
scripts/               # Build & utility scripts
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

## 5-Week Timeline
1. **Week 1 (current):** Extract pragmatic rules from KB source docs → `knowledge-base/rules/`
2. **Week 2:** Build minimal MCP server with rules engine → `src/`
3. **Week 3:** Run CQS evaluation protocol → `docs/verification/`
4. **Week 4-5:** Analyze results, prepare FCSM presentation

## Technical Context
- **Census API:** Direct Python HTTP calls to `api.census.gov`
- **Pragmatic Rules:** JSON rule sets covering MOE thresholds, coverage bias, temporal validity, geographic pitfalls, source selection, imputation quality
- **Evaluation:** Conversational Quality Score (CQS) protocol comparing baseline LLM vs rules-augmented responses
- **No vector DB yet** — rules are structured JSON, not embeddings

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
- Don't over-engineer the architecture before evaluation proves the concept
- Don't create files outside the repo without asking
- Don't use web search for Census data — use Census API or project knowledge base
