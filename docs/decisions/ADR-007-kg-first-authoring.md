# ADR-007: KG-First Authoring with LLM Graph Builder

**Date:** 2026-02-08
**Status:** Accepted
**Supersedes:** None (refines ADR-001 workflow)
**Related:** ADR-001 (authoring/runtime separation), ADR-002 (grounding not RAG)

## Context

ADR-001 established Neo4j as the authoring environment and SQLite as runtime. In practice, the authoring workflow devolved into humans writing JSON files by hand — effectively bypassing Neo4j as the primary authoring tool. This happened because no automated pipeline existed to populate Neo4j from source documents. The round-trip scripts (`staging_to_neo4j.py`, `neo4j_to_staging.py`) became symmetric, implying JSON and Neo4j were co-equal sources of truth. They shouldn't be.

The original vision was: pragmatics are graph threads managed via Cypher. Source documents feed the graph. Curated subgraphs are harvested as pragmatic packs. JSON staging files are an export artifact for version control and compilation — not an authoring surface.

Meanwhile, CPS documentation is fragmented across 12+ PDFs spanning 20 years of methodological changes. Manual extraction doesn't scale. The ACS handbook (89 pages, single document) took a full session to produce 7 findings. CPS would take weeks of manual reading.

Two open-source tools address this:
- **neo4j-labs/llm-graph-builder**: LLM-powered extraction from PDFs directly into Neo4j. LangChain-based, supports Anthropic, configurable entity schemas.
- **HKUDS/RAG-Anything**: MinerU-based PDF parsing with multimodal support (tables, equations, images) feeding LightRAG knowledge graphs.

## Decision

**Neo4j is the upstream source of truth for all pragmatics content. JSON staging is a downstream build artifact. The arrow goes one direction.**

### Authoring Pipeline

```
Source PDFs
    ↓
llm-graph-builder (or equivalent LLM extraction)
    ↓
Neo4j: raw knowledge graph ("the quarry")
    - Entities: concepts, methods, thresholds, caveats, definitions
    - Relationships: applies_to, contradicts, qualifies, supersedes
    - Properties: source document, page, section, extraction confidence
    ↓
Opus/human traverses raw KG via Cypher
    - Identifies pragmatic threads (fitness-for-use expert judgments)
    - Harvests subgraphs worth packaging
    - Assigns latitude, triggers, provenance
    ↓
Curated Context nodes in Neo4j pragmatics namespace
    - Schema: ContextItem model (context_id, domain, category, etc.)
    - Managed via Cypher, not JSON
    ↓
neo4j_to_staging.py (EXPORT ONLY — one direction)
    ↓
staging/*.json (version-controlled build artifact)
    ↓
compile_pack.py → packs/*.db (shipped SQLite)
```

### Two Neo4j Namespaces

1. **Raw KG** (`USE raw` or separate database): Everything extracted from source documents. Messy, comprehensive, unfiltered. This is the quarry.
2. **Pragmatics** (`USE pragmatics`): Curated expert judgments conforming to ContextItem schema. This is the cut stone.

### Tool Selection

- **Primary extraction**: neo4j-labs/llm-graph-builder — writes directly to Neo4j, configurable schema, supports Anthropic models.
- **PDF parsing** (if LangChain loaders insufficient): MinerU standalone for structure-preserving extraction of tables, equations, and complex layouts (CPS docs need this).
- **Graph mining**: Cypher queries + Opus reasoning over the raw KG to identify pragmatic threads.

### Script Roles (Clarified)

| Script | Role | Direction |
|--------|------|-----------|
| `neo4j_to_staging.py` | **Primary export** — produces staging JSON from curated pragmatics | Neo4j → JSON |
| `staging_to_neo4j.py` | **Bootstrap/recovery only** — seed Neo4j from existing JSON, not for regular authoring | JSON → Neo4j |
| `compile_pack.py` | Build step — staging JSON → SQLite packs | JSON → SQLite |
| `catalog_report.py` | Inventory — coverage tracking from compiled packs | Read-only |

### Relationship to ADR-002 (Grounding Not RAG)

The raw KG is effectively a RAG store for the **authoring environment** — you query it to find what's worth extracting. This does NOT change the shipped product. The runtime system remains grounding-only: pre-compiled SQLite packs with tag-based retrieval, no embeddings, no vector search. The RAG lives in the workshop, not the product.

## Consequences

**Positive:**
- Scales to arbitrary document volume (CPS, ACS, SIPP, decennial)
- Cypher is the natural authoring language for graph data — not JSON
- Raw KG preserves everything; pragmatics are selective
- LLM-assisted extraction + human/Opus curation = quality at scale
- Provenance catalog tracks what's been extracted from where
- "Once ingested, it's done" — each document is a completed extraction

**Negative:**
- Neo4j becomes a harder dependency for contributors (was optional, now essential for authoring)
- Two namespaces to manage (raw KG + pragmatics)
- llm-graph-builder adds LangChain dependency to dev toolchain (not runtime)
- Raw KG quality depends on extraction model quality — garbage in, garbage out
- Need to define raw KG schema conventions (what entity/relationship types)

**Risks:**
- Raw KG could become a junk drawer if entity types aren't disciplined
- Opus traversal requires well-crafted Cypher — need to develop a library of mining queries
- llm-graph-builder may need customization for Census domain (statistical terminology, table structures)

## Alternatives Considered

1. **Continue manual JSON authoring**: Rejected — doesn't scale, already causing pain with CPS docs.
2. **RAG-Anything as primary tool**: Rejected — writes to LightRAG internal store, not Neo4j. MinerU component useful for PDF parsing but graph builder goes to wrong target.
3. **Custom extraction pipeline from scratch**: Rejected — llm-graph-builder already solves the PDF→Neo4j problem. Don't rebuild.
4. **Keep JSON as co-equal source of truth**: Rejected — this is what caused the workflow confusion. One source of truth, one direction.

## Implementation Notes

- llm-graph-builder requires Neo4j 5.23+ with APOC. Verify current instance compatibility.
- Start with `cps_handbook_of_methods.pdf` (552K, manageable) as proof of concept before ingesting all 12 CPS docs.
- Raw KG schema conventions need a short design doc before first extraction (entity types, relationship types, required properties).
- Existing 25 ACS pragmatics were authored from LLM training data, not source docs (discovered 2026-02-08). These need re-verification against the raw KG once ACS-GEN-001 is ingested.
