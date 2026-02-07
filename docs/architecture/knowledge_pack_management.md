# Knowledge Pack Management Architecture

*Decided: 2026-02-08*

---

## Overview

Pragmatics packs encode domain expertise as traversable graph structures. Managing these at scale requires treating knowledge as code: version-controlled, reviewable, modular, and reproducible.

This document defines the architecture for authoring, versioning, and delivering pragmatics packs.

---

## Design Principles

| Principle | Implication |
|-----------|-------------|
| **Packs as code** | Knowledge lives in version control, not databases |
| **Authoring ≠ Runtime** | Development tools don't ship with the product |
| **JSON is the contract** | Interchange format between authoring and delivery |
| **Zero runtime dependencies** | SQLite only — no external databases at runtime |
| **Modular expansion** | New domains = new directories, not restructuring |

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHORING ENVIRONMENT                        │
│                    (separate from this repo)                    │
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │   Source    │───▶│  LLM-Assist │───▶│   Neo4j     │        │
│   │   Docs      │    │  Extraction │    │   Graph     │        │
│   └─────────────┘    └─────────────┘    └──────┬──────┘        │
│                                                 │               │
│   • Census handbooks                    • Visual editing        │
│   • Methodology PDFs                    • Cypher queries        │
│   • Expert interviews                   • Thread validation     │
│   • ACS documentation                   • Relationship viz      │
│                                                 │               │
│                                                 ▼               │
│                                        ┌─────────────┐          │
│                                        │   Export    │          │
│                                        │   Script    │          │
│                                        └──────┬──────┘          │
└───────────────────────────────────────────────┼─────────────────┘
                                                │
                        Cypher → JSON           │
                                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         VERSION CONTROL                           │
│                         (this repo: census-mcp-server)            │
│                                                                   │
│   staging/                                                        │
│   ├── general_statistics/                                         │
│   │   ├── manifest.json          ◄── Pack metadata                │
│   │   ├── temporal.json          ◄── Context items + edges        │
│   │   └── uncertainty.json                                        │
│   ├── census/                                                     │
│   │   ├── manifest.json                                           │
│   │   ├── geography.json                                          │
│   │   └── vintage.json                                            │
│   └── acs/                                                        │
│       ├── manifest.json                                           │
│       ├── population.json                                         │
│       ├── income.json                                             │
│       └── housing.json                                            │
│                                                                   │
│   • Git diffable           • PR reviewable                        │
│   • Reproducible builds    • Open data format                     │
└───────────────────────────────────────────────┬───────────────────┘
                                                │
                        python scripts/compile_all.py
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         BUILD ARTIFACTS                           │
│                         (gitignored)                              │
│                                                                   │
│   packs/                                                          │
│   ├── general_statistics.db                                       │
│   ├── census.db                                                   │
│   └── acs.db                                                      │
│                                                                   │
│   • SQLite databases       • Compiled from staging                │
│   • Inheritance resolved   • Shipped with MCP                     │
└───────────────────────────────────────────────┬───────────────────┘
                                                │
                        PackLoader at runtime
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         RUNTIME                                   │
│                         (MCP Server)                              │
│                                                                   │
│   • Load packs from packs/                                        │
│   • Query by triggers                                             │
│   • Traverse threads                                              │
│   • Compile context for LLM                                       │
│   • Zero external dependencies                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## Why This Separation?

### Graph Authoring is Complex

Thread relationships form a directed graph. Managing this in flat files is error-prone:
- Hard to visualize relationships
- Easy to create orphaned nodes
- Difficult to validate thread traversal
- No query language for exploration

Neo4j (or similar graph DB) provides:
- Visual graph exploration
- Cypher queries for validation ("find all orphan nodes")
- Relationship visualization
- Bulk editing with query results

### Runtime Must Be Simple

The MCP server ships to users. It cannot require:
- Neo4j installation
- Database server configuration
- Network connectivity to graph DB
- Complex dependency management

SQLite provides:
- Single file deployment
- Zero configuration
- Standard library support (Python sqlite3)
- Fast reads for query-time access

### JSON is the Bridge

The staging JSON format serves as:

1. **Version control artifact** — Git tracks changes, PRs review additions
2. **Build input** — Deterministic compilation to SQLite
3. **Open data format** — Others can use knowledge without our tooling
4. **Contract** — Decouples authoring tools from runtime

---

## Workflow: Adding New Knowledge

### 1. Author in Neo4j (your environment)

```cypher
// Create context node
CREATE (c:Context {
  context_id: 'ACS-MOE-001',
  domain: 'acs',
  category: 'margin_of_error',
  latitude: 'narrow',
  context_text: 'ACS estimates with CV > 40% are considered unreliable...',
  triggers: ['margin_of_error', 'cv', 'reliability', 'moe']
})

// Create relationship
MATCH (c:Context {context_id: 'ACS-MOE-001'})
MATCH (parent:Context {context_id: 'GEN-UNC-001'})
CREATE (c)-[:INHERITS]->(parent)
```

### 2. Validate graph structure

```cypher
// Find orphan nodes (no incoming or outgoing edges)
MATCH (c:Context)
WHERE NOT (c)-[:INHERITS|:RELATES_TO|:APPLIES_TO]-() 
  AND NOT ()-[:INHERITS|:RELATES_TO|:APPLIES_TO]->(c)
RETURN c.context_id

// Find broken references
MATCH (c:Context)-[r]->(target)
WHERE target IS NULL
RETURN c.context_id, type(r)

// Verify thread traversal depth
MATCH path = (c:Context {context_id: 'ACS-MOE-001'})-[:INHERITS*1..5]->(root)
RETURN length(path), [n IN nodes(path) | n.context_id]
```

### 3. Export to JSON

```cypher
// Export pack contents
MATCH (c:Context {domain: 'acs'})
OPTIONAL MATCH (c)-[r:INHERITS|:RELATES_TO|:APPLIES_TO]->(target)
RETURN c.context_id, c.domain, c.category, c.latitude, 
       c.context_text, c.triggers,
       collect({target: target.context_id, edge_type: type(r)}) as thread_edges
```

Export script transforms Cypher results → staging JSON format.

### 4. PR to census-mcp-server

```bash
# In census-mcp-server repo
cp ~/exports/acs_moe.json staging/acs/margin_of_error.json
git add staging/acs/margin_of_error.json
git commit -m "Add MOE reliability guidance to ACS pack"
git push origin feature/acs-moe-guidance
# Open PR
```

### 5. CI validates and compiles

GitHub Actions:
- Validates JSON against Pydantic models
- Compiles packs
- Runs tests including pack round-trip
- Lint checks

### 6. Merge and release

On merge to main:
- Packs recompile
- New .db files generated
- Release includes updated packs

---

## Modular Expansion

Adding a new survey (e.g., CPS) is additive:

```
staging/
├── general_statistics/    # existing
├── census/                # existing  
├── acs/                   # existing
└── cps/                   # NEW - just add directory
    ├── manifest.json      # parent_pack: "census"
    ├── employment.json
    └── labor_force.json
```

No restructuring required. The inheritance chain handles cross-survey context.

---

## Open Source Considerations

### This Repo (census-mcp-server)
- MIT licensed
- Contains: runtime code, staging JSON, compilation scripts
- Anyone can compile and run without your Neo4j

### Separate Repo (pragmatics-knowledge-base) — Future
- Contains: Neo4j exports, extraction scripts, source doc references
- Enables collaboration on knowledge authoring
- Not required to use census-mcp-server

---

## Trade-offs Accepted

| Trade-off | Rationale |
|-----------|-----------|
| Manual export step | Keeps repos decoupled; authoring workflow is personal |
| JSON duplication | Version control benefits outweigh storage cost |
| SQLite query limits | Graph traversal is bounded (max_depth); complex queries happen at authoring |
| No live sync | Packs are releases, not live data; stability > freshness |

---

## Related Documents

- `docs/design/pragmatics_vocabulary.md` — Term definitions and schema
- `docs/requirements/srs.md` — Constraints (C-002: SQLite only)
- `docs/design/extraction_pipeline.md` — How source docs become context

---

*This architecture enables knowledge management at scale while keeping the runtime minimal.*
