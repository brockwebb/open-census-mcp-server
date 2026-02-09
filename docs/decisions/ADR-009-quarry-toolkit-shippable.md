# ADR-009: Quarry Toolkit as Shippable Project Component

**Status:** Accepted
**Date:** 2026-02-09
**Deciders:** Brock Webb
**Traces To:** ADR-008, Phase 5, FCSM paper

## Context

The extraction pipeline (ADR-008) could be either internal tooling (scripts we run) or a documented toolkit that ships with the project for others to use.

## Decision

**Ship the quarry extraction toolkit** as part of census-mcp-server under `scripts/quarry/`. It becomes a reproducible methodology for building statistical consultation knowledge bases from methodology PDFs.

## Rationale

- The FCSM paper presents a *methodology*, not just a system. Reproducibility requires the extraction pipeline be available.
- Domain experts at Census, BLS, and state demography offices have methodology documents. They need extraction tooling, not just a consumer-facing MCP server.
- The project already has the consumption side (MCP server, pragmatics retriever). Adding the production side makes it a complete toolkit.
- The clinical assessment analogy (tests + standards → diagnoses) is the differentiating architecture. The toolkit embodies this.

## Structure

```
scripts/quarry/
├── README.md           # Setup, usage, extending to new surveys
├── schema.json         # v3.1 schema definition (machine-readable)
├── seed.py             # Layer 0: AnalysisTask + REQUIRES rules
├── extract.py          # PDF → structured KG (single pipeline)
├── harvest.py          # KG → candidate ContextItems
├── export.py           # Quarry → staging JSON → pragmatics packs
└── config.py           # Shared configuration (Neo4j, API keys, paths)
```

Users bring: Neo4j instance, LLM API key, methodology PDFs.
Users get: Pragmatics packs ready for the MCP server.

## Consequences

- Must document setup, configuration, and extension points
- Schema must be versioned and machine-readable (JSON, not just markdown)
- Need clear separation between CPS/ACS-specific seed data and the generic framework
- Extraction prompts become a maintained artifact (versioned with the schema)
