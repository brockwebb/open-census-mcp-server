# Quarry Extraction Toolkit

Custom extraction pipeline for Census methodology PDFs → Neo4j quarry database. Replaces llm-graph-builder (see ADR-008) and ships as a project component (ADR-009).

## What It Does

The quarry toolkit implements a 4-layer knowledge graph extraction architecture:

1. **Layer 0 (Seed):** Expert-curated AnalysisTask + REQUIRES edges encoding quality standards
2. **Layer 1 (Extract):** LLM extraction of facts from PDFs → MethodologicalChoice, QualityAttribute, etc.
3. **Layer 2 (Harvest):** Pattern-matching queries generate candidate ContextItems
4. **Layer 3 (Curate):** Expert validation of harvest output (external to toolkit)
5. **Layer 4 (Export):** Transform to pragmatics staging JSON (stub, not yet implemented)

**Key insight:** Fitness implications are DERIVED by Cypher queries, not extracted from documents.

## Prerequisites

- **Python:** 3.11+
- **Neo4j:** 5.x with `quarry` database created and online
- **Anthropic API key:** Get from https://console.anthropic.com
- **Packages:** `pip install docling anthropic neo4j`

## Installation

From the repository root:

```bash
pip install docling anthropic neo4j
```

## Environment Variables

- `ANTHROPIC_API_KEY` — Required for extraction
- `NEO4J_PASSWORD` — Optional, defaults to `i'llbeback` in config
- `NEO4J_URI` — Optional, defaults to `bolt://localhost:7687`
- `LOG_LEVEL` — Optional, defaults to `INFO`

## Quick Start

```bash
# 1. Seed Layer 0 (AnalysisTask + REQUIRES edges)
python -m scripts.quarry.seed

# 2. Extract a document (22-page CPS Handbook example)
python -m scripts.quarry.extract --source cps_handbook

# 3. Run harvest queries
python -m scripts.quarry.harvest
```

## Usage

### Seed Layer 0

```bash
# Dry run: print Cypher without executing
python -m scripts.quarry.seed --dry-run

# Execute: create Layer 0 nodes and relationships
python -m scripts.quarry.seed
```

Idempotent (uses MERGE). Safe to run multiple times.

### Chunk a PDF

```bash
# Test Docling chunking on CPS Handbook
python -m scripts.quarry.chunk --source cps_handbook

# Show first 5 chunks
python -m scripts.quarry.chunk --source cps_handbook --limit 5
```

Verifies section-aware chunking (chunk count ≠ page count).

### Extract Knowledge

```bash
# Full extraction
python -m scripts.quarry.extract --source cps_handbook

# Dry run: show prompts and JSON output without writing to Neo4j
python -m scripts.quarry.extract --source cps_handbook --dry-run

# Limit to first 3 chunks (for testing)
python -m scripts.quarry.extract --source cps_handbook --limit 3
```

Extraction writes:
- MethodologicalChoice, QualityAttribute, ConceptDefinition, etc. (Layer 1 nodes)
- APPLIES_TO, PRODUCES, DEFINED_FOR, etc. (relationships per schema v3.1)
- SOURCED_FROM edges linking all extracted nodes to SourceDocument
- Exactly 1 SourceDocument node per PDF

### Run Harvest Queries

```bash
python -m scripts.quarry.harvest
```

Runs all harvest queries from `docs/design/raw_kg_schema.md` §6:
- §6.1a: Numeric threshold violations
- §6.1b: Categorical mismatches (reference periods, universes)
- §6.2: Temporal comparability breaks
- §6.4: Unanticipated interactions
- §6.5: Extraction coverage report
- §6.6: Unconnected facts (gaps)

Results saved to `tmp/harvest_results_{timestamp}.json`.

## Extending: Add a New Source Document

1. Add entry to `SOURCE_CATALOG` in `scripts/quarry/config.py`:

```python
"my_document": {
    "catalog_id": "my_doc_id_2024",
    "title": "My Document Title",
    "year": 2024,
    "survey": "acs",  # or "cps", "general"
    "local_path": "knowledge-base/source-docs/my-document.pdf"
}
```

2. Run extraction:

```bash
python -m scripts.quarry.extract --source my_document
```

3. Run harvest to generate ContextItems:

```bash
python -m scripts.quarry.harvest
```

## Schema Reference

- **Full schema:** `docs/design/raw_kg_schema.md` v3.1
- **Machine-readable:** `scripts/quarry/schema.json`
- **Architecture:** `docs/design/quarry_extraction_pipeline.md`
- **Design narrative:** `docs/design/kg_schema_design_narrative.md`

## File Structure

```
scripts/quarry/
├── __init__.py         # Package init
├── config.py           # Configuration, controlled vocabularies
├── schema.json         # Machine-readable schema
├── utils.py            # Shared utilities (Neo4j, Anthropic, validation)
├── chunk.py            # PDF → Docling chunks
├── prompts.py          # Extraction prompt templates
├── seed.py             # Layer 0 seeding
├── extract.py          # Main extraction pipeline (largest file)
├── harvest.py          # Layer 2 harvest queries
├── export.py           # Layer 4 export stub (not yet implemented)
└── README.md           # This file
```

## Decisions & Architecture

- **ADR-008:** Why llm-graph-builder was replaced (custom needs, Docling integration)
- **ADR-009:** Quarry toolkit ships as project component (not external dependency)
- **ADR-007:** KG-first authoring workflow
- **ADR-001:** Neo4j authoring vs SQLite runtime separation

## Troubleshooting

**"Missing ANTHROPIC_API_KEY"**
→ Set environment variable: `export ANTHROPIC_API_KEY='your-key'`

**"MENTIONS relationships found"**
→ Extraction prompt needs fixing. MENTIONS is not a valid relationship type.

**Chunk count equals page count**
→ Docling chunking not working correctly. Check `HierarchicalChunker` configuration.

**Validation errors**
→ Check logs for specific failures. Common: controlled vocabulary violations, missing required properties.

## Known Limitations

- Export pipeline (Layer 4) is stub only — harvest curation workflow not yet designed
- Entity resolution is basic (MERGE on ID/name) — may need deduplication pass
- No batch processing for multiple documents — run extract once per source
- Cost tracking is estimate only (Sonnet 4.5 pricing may change)
