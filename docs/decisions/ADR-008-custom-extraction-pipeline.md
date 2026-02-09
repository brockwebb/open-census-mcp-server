# ADR-008: Custom Extraction Pipeline over llm-graph-builder

**Status:** Accepted
**Date:** 2026-02-09
**Deciders:** Brock Webb
**Traces To:** KG.5, KG.8, KG.9, KG.10, Phase 5

## Context

Week 1 of the FCSM sprint requires a pipeline to extract structured knowledge from Census methodology PDFs into the quarry Neo4j database. The initial plan was to use neo4j-labs/llm-graph-builder as the extraction engine.

## Decision

**Build a custom extraction pipeline** in `scripts/quarry/` that ships with the census-mcp-server project, replacing llm-graph-builder for all extraction work.

## Rationale

After a full integration test with llm-graph-builder (CPS Handbook of Methods, 22 pages), we found:

### llm-graph-builder Limitations (Empirical)
1. **Schema API is read-only** — `/schema` POST endpoint only queries existing labels, does not accept schema definitions despite documentation suggesting otherwise. Required workaround: seed skeleton nodes directly via Cypher.
2. **Page-based chunking only** — PyMuPDFLoader returns one Document per page. No paragraph, section, or semantic chunking. Census methodology docs need section-aware chunking for coherent extraction.
3. **LLMGraphTransformer does not populate typed properties** — Of 6 QualityAttribute nodes extracted, all had null `dimension`, `name`, and `value_type`. The `additional_instructions` parameter suggests properties but doesn't enforce them. Tool-use mode extraction treats properties as optional.
4. **Only 3 PRODUCES edges from 93 MethodologicalChoice nodes** — The critical join path for harvest queries (REQUIRES → QualityAttribute ← PRODUCES) was nearly empty. Required a full enrichment pass to fix.
5. **Source document hallucination** — One PDF produced 9 distinct SourceDocument nodes ("CPS Handbook of Methods", "Handbook of Methods", "CPS Technical Documentation", "CPS History Timeline", etc.). No entity resolution.
6. **291 MENTIONS fallback relationships** — When LLMGraphTransformer can't match extracted relationships to the allowed schema, it falls back to generic MENTIONS. This is noise.
7. **Frontend-dependent configuration** — Schema setting via Graph Enhancement tab requires running the React frontend. The backend API has no equivalent.
8. **Neo4j MCP is single-database** — Claude Desktop config allows only one NEO4J_DATABASE. Switching between quarry and pragmatics requires config changes or direct Python scripts.
9. **Resulted in 4 disconnected manual scripts** — seed, extract, enrich, harvest — each with hardcoded paths and no error recovery.

### What Worked
- **The schema design (v3.1) is sound** — harvest queries produced real results once PRODUCES edges were populated by the enrichment pass.
- **Direct LLM extraction (enrichment script) outperformed LLMGraphTransformer** — 96% of MethodologicalChoice nodes got PRODUCES edges with properly typed QualityAttribute properties.
- **Harvest found one genuinely valuable insight** — 75% rotation group overlap in consecutive CPS months exceeding the 0.2 threshold.

### Custom Pipeline Advantages
- **Section-aware chunking** — respect document structure (headers, numbered sections, tables)
- **Direct structured JSON extraction** — one prompt per chunk with full property schema enforcement, no LLMGraphTransformer intermediary
- **Single pipeline** — PDF → chunk → extract → write → harvest in one script
- **Shippable as project tooling** — `scripts/quarry/` becomes a toolkit others can use to build their own pragmatics knowledge bases
- **Full property control** — controlled vocabularies (fact_category, dimension, value_type) enforced at extraction time
- **Entity resolution** — deduplicate at write time via MERGE on canonical names

## Consequences

- llm-graph-builder remains installed for reference/experimentation but is not part of the census-mcp-server pipeline
- All extraction tooling lives in census-mcp-server repo under `scripts/quarry/`
- Extraction depends on: Anthropic API key, Neo4j with quarry database, PyMuPDF, langchain-anthropic
- The quarry toolkit becomes a documented, reproducible methodology for the FCSM paper

## Alternatives Considered

1. **Fix llm-graph-builder** — Add section chunking, property enforcement, entity resolution. Rejected: fighting upstream design decisions. The tool is built for generic demo extraction, not domain-specific structured knowledge engineering.
2. **Use llm-graph-builder for extraction, custom scripts for enrichment** — This is what we tested. It works but doubles the API calls and adds complexity. The enrichment script proved direct extraction is cleaner.
3. **Skip KG entirely, author pragmatics manually** — Rejected: cross-document inference (CPS vs ACS definitional differences) requires graph traversal. Manual authoring can't scale to the full Census methodology corpus.
