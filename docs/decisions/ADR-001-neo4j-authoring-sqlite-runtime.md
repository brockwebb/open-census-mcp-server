# ADR-001: Neo4j as Authoring Tool, SQLite as Runtime

**Date:** 2026-02-07
**Status:** Accepted

## Context

The pragmatics layer requires a knowledge graph for:
- Modeling relationships between context items (threads)
- Visualizing and exploring domain structure
- Validating graph integrity before deployment

The runtime system (census-mcp-server) ships to users who need:
- Zero external dependencies
- Simple installation
- No database server configuration

## Decision

**Separate authoring from runtime:**

- **Authoring environment** (developer/researcher side): Neo4j for graph exploration, Cypher queries, visual validation
- **Runtime environment** (shipped to users): SQLite for zero-dependency pack loading
- **Interface contract**: JSON staging files (version controlled, diffable, reproducible)

## Workflow

```
[Research Environment - NOT in repo]
Source docs → LLM extraction → Neo4j (visual authoring, validation)
    ↓
Export script (Cypher → JSON)
    ↓
[census-mcp-server repo]
staging/*.json (version controlled)
    ↓
compile_pack.py (validation, compilation)
    ↓
packs/*.db (SQLite, gitignored artifacts)
    ↓
Runtime PackLoader
```

## Consequences

**Positive:**
- Users get zero-dependency installation
- Developers get powerful graph tools for authoring
- JSON staging files are git-diffable and PR-reviewable
- "Packs as code" enables modular, reproducible builds

**Negative:**
- Two systems to maintain (Neo4j for authoring, SQLite for runtime)
- Export/import scripts needed for round-trip
- Neo4j not required but recommended for non-trivial pack editing

## Alternatives Considered

1. **Neo4j everywhere**: Rejected — too heavy for end users
2. **SQLite only**: Rejected — graph editing in flat files is painful
3. **JSON only (no DB)**: Rejected — query performance matters at scale
