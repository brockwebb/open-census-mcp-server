# Design Document: Quarry Extraction Pipeline

*Version: 1.0 — 2026-02-09*
*Status: Approved for implementation*
*Traces to: ADR-008, ADR-009, SRS §3.6, `docs/design/raw_kg_schema.md` v3.1*

---

## 1. Purpose

This document specifies how Census methodology PDFs are transformed into structured knowledge graph nodes in the quarry Neo4j database. The pipeline replaces llm-graph-builder (ADR-008) with a custom toolkit that ships as a project component (ADR-009).

This is build tooling. Nothing in this pipeline runs at query time. It produces raw knowledge graph content that is later harvested, curated, and exported as pragmatics packs for runtime consumption.

**Relationship to `extraction_pipeline.md`:** That document describes the full pipeline from source docs to compiled SQLite packs. *This* document specifies the quarry stage in detail — the upstream portion that produces structured knowledge graph content from PDFs. The downstream stages (harvest → curate → export → staging → compile) are specified there.

---

## 2. Pipeline Architecture

```
PDF ──► Docling ──► Structured Chunks ──► LLM Extraction ──► Neo4j Quarry
         (parse)    (section-aware,       (structured JSON,    (MERGE writes,
                     tables preserved,     controlled vocab,     entity resolution)
                     reading order)        schema enforcement)
```

### 2.1 Pipeline Stages

| Stage | Input | Output | Tool |
|-------|-------|--------|------|
| 1. Parse | PDF file path | DoclingDocument (Pydantic) | Docling `DocumentConverter` |
| 2. Chunk | DoclingDocument | List of section-aware chunks with provenance | Docling `HierarchicalChunker` |
| 3. Extract | Chunk text + schema + prompt | Structured JSON (nodes + relationships) | Anthropic Claude API |
| 4. Write | Structured JSON | Neo4j nodes and relationships | Neo4j Python driver via MERGE |

### 2.2 What This Pipeline Does NOT Do

- **No harvest.** Harvest queries (Layer 2) are a separate script (`harvest.py`).
- **No curation.** Human review of harvested candidates is manual or LLM-assisted, separate from extraction.
- **No export.** Quarry → staging JSON → SQLite is handled by `export.py`.
- **No runtime inference.** The quarry is never queried by the MCP server.

---

## 3. Stage 1: PDF Parsing with Docling

### 3.1 Why Docling

Docling (IBM Research, LF AI & Data Foundation, MIT license) provides structure-aware PDF parsing that solves our primary failure mode: page-based chunking destroying section context.

**Capabilities used:**
- Layout detection: titles, headings, paragraphs, tables, lists, page headers/footers
- Reading order preservation across multi-column layouts
- Table structure reconstruction (rows, columns, multi-level headers)
- Unified `DoclingDocument` representation (Pydantic) with provenance metadata
- Built-in `HierarchicalChunker` for section-aware chunking
- Local execution (no external API calls for parsing)
- Apple Silicon MLX acceleration

**Capabilities NOT needed:**
- OCR (Census methodology PDFs are programmatic/digital)
- Formula extraction
- Image classification
- Audio/ASR support

### 3.2 Configuration

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False  # Programmatic PDFs only
pipeline_options.do_table_structure = True  # Preserve table structure

converter = DocumentConverter(pipeline_options=pipeline_options)
result = converter.convert(pdf_path)
doc = result.document
```

### 3.3 Output

A `DoclingDocument` containing:
- Hierarchical structure (sections, subsections, paragraphs)
- Tables as structured objects (exportable to DataFrame/CSV)
- Reading order metadata
- Per-element provenance (page number, bounding box)

### 3.4 Alternatives Considered

| Tool | Rejection Rationale |
|------|-------------------|
| PyMuPDF (current) | Page-based chunking only. No structural understanding. Caused the primary failure mode in llm-graph-builder extraction. |
| MinerU | Viable alternative but less mature ecosystem. Docling's `HierarchicalChunker` eliminates the need for custom chunking logic. |
| Unstructured.io | Heavier dependency, cloud-oriented, less predictable section detection on government PDFs. |
| Manual chunking | Does not scale to 100+ documents over project lifetime. |

---

## 4. Stage 2: Section-Aware Chunking

### 4.1 Chunking Strategy

Use Docling's `HierarchicalChunker` to produce chunks that respect document structure:

```python
from docling.chunking import HierarchicalChunker

chunker = HierarchicalChunker(
    max_tokens=2000,       # LLM context budget per chunk
    merge_peers=True,      # Combine short adjacent sections
    include_metadata=True  # Carry section headers into chunks
)
chunks = list(chunker.chunk(doc))
```

### 4.2 Chunk Metadata

Each chunk carries:
- **Section path:** e.g., `["Chapter 3", "3.2 Sample Design", "3.2.1 Primary Sampling Units"]`
- **Page range:** Start and end page numbers
- **Content type:** `text`, `table`, `list`
- **Source document:** Catalog ID from `config.py`

### 4.3 Table Handling

Tables are chunked as atomic units. When a table appears:
1. Export as Markdown table (preserving headers and cell values)
2. Include surrounding context (section header, caption if detected)
3. Never split a table across chunks

### 4.4 Chunk Size Rationale

2000 tokens per chunk balances:
- **Too small (< 1000):** Loses cross-sentence context needed for methodology extraction
- **Too large (> 4000):** Extraction prompt + chunk + schema exceeds practical context budget; increases per-call cost; reduces extraction precision
- **Sweet spot (1500–2500):** Captures a complete section or subsection, enough context for the LLM to understand the methodology being described

---

## 5. Stage 3: LLM Extraction

### 5.1 Approach

Direct structured JSON extraction via prompted LLM calls. Each chunk is sent to the LLM with:
1. The chunk text with section context
2. The quarry schema (node types, property constraints, controlled vocabularies)
3. Extraction instructions with examples
4. The source document's catalog entry (title, year, survey)

The LLM returns a JSON object containing extracted nodes and relationships.

### 5.2 Why Not LLMGraphTransformer

Per ADR-008, LangChain's `LLMGraphTransformer`:
- Does not enforce typed properties (all QualityAttribute properties were null)
- Falls back to generic `MENTIONS` when it can't match relationships (291 noise edges)
- Does not support controlled vocabularies
- Does not resolve entities at extraction time

Direct prompting with JSON output produces strictly better results, as proven by the enrichment experiment (96% PRODUCES edge success rate vs 3% from LLMGraphTransformer).

### 5.3 Extraction Prompt Design

The extraction prompt enforces:

**Controlled vocabularies:**
- `fact_category`: `design`, `collection`, `weighting`, `estimation`, `variance`, `processing`, `adjustment`
- `dimension`: `temporal_comparability`, `precision`, `coverage`, `definitional_alignment`, `topcoding_effects`, `seasonal_adjustment`, `nonresponse_bias`, `processing_error`, `variance_estimation`
- `value_type`: `fraction`, `count`, `boolean`, `categorical`
- `latitude`: `none`, `narrow`, `wide`, `full`
- `assertion_type`: `fact`, `definition`, `procedure`, `threshold`, `caveat`, `change`

**Property completeness requirements:**
- Every `MethodologicalChoice` MUST have `fact_category` and `survey`
- Every `QualityAttribute` MUST have `dimension`, `value_type`, and either `value_number` or `value_string`
- Every `ConceptDefinition` MUST have `reference_period`, `unit_of_analysis`, and `granularity`
- Every `Threshold` MUST have `measure`, `value`, and `operator`

**Extraction rules:**
1. Extract FACTS and MEASUREMENTS, not opinions or implications
2. Prefer operational specifics over general descriptions
3. Fractions are 0–1, not percentages
4. Link to existing Layer 0 entities by canonical name (MERGE targets)
5. One `SourceDocument` node per PDF (canonical name from config)
6. Include section and page provenance on every `SOURCED_FROM` edge

### 5.4 Output Format

```json
{
  "nodes": [
    {
      "type": "MethodologicalChoice",
      "id": "cps_two_stage_stratified_cluster_design",
      "properties": {
        "fact_category": "design",
        "survey": "cps",
        "assertion_type": "fact"
      }
    },
    {
      "type": "QualityAttribute",
      "id": "rotation_group_overlap_fraction",
      "properties": {
        "dimension": "temporal_comparability",
        "value_type": "fraction",
        "value_number": 0.75,
        "name": "rotation_group_overlap"
      }
    }
  ],
  "relationships": [
    {
      "source": "cps_two_stage_stratified_cluster_design",
      "target": "rotation_group_overlap_fraction",
      "type": "PRODUCES",
      "properties": {
        "mechanism": "4-8-4 rotation pattern ensures 75% sample overlap between consecutive months"
      }
    },
    {
      "source": "cps_two_stage_stratified_cluster_design",
      "target": "CPS Basic Monthly",
      "type": "APPLIES_TO"
    },
    {
      "source": "cps_two_stage_stratified_cluster_design",
      "target": "cps_handbook_of_methods",
      "type": "SOURCED_FROM",
      "properties": {
        "source_section": "Chapter 3, Section 3.2.1",
        "source_page": 45
      }
    }
  ]
}
```

### 5.5 Batch Processing

- **Batch size:** 1 chunk per LLM call (extraction precision > throughput)
- **Concurrency:** Sequential (avoid rate limits, maintain determinism)
- **Cost control:** Log token usage per call, report total cost at end
- **Error handling:** Log failed chunks, continue processing, report summary

### 5.6 Model Selection

Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`). Rationale:
- Structured JSON output quality proven in enrichment experiment
- Cost-effective for extraction volume (~$3/1M input tokens)
- Schema enforcement via detailed prompting works reliably
- Opus is unnecessary for extraction (extraction is pattern-matching, not reasoning)

---

## 6. Stage 4: Neo4j Write with Entity Resolution

### 6.1 Write Strategy

All writes use `MERGE` (not `CREATE`) to implement entity resolution at write time:

```cypher
MERGE (mc:MethodologicalChoice {id: $id})
ON CREATE SET mc.fact_category = $fact_category, mc.survey = $survey, ...
ON MATCH SET mc += $properties
```

### 6.2 Entity Resolution Rules

| Entity Type | MERGE Key | Rationale |
|-------------|-----------|-----------|
| MethodologicalChoice | `id` (snake_case canonical name) | Prevents duplicate facts across chunks |
| QualityAttribute | `name` + `dimension` | Same attribute from different chunks merges |
| DataProduct | `name` | Controlled vocabulary: "CPS Basic Monthly", "CPS ASEC", "ACS 1-Year", "ACS 5-Year" |
| SurveyProcess | `name` | Controlled vocabulary from Layer 0 seed |
| CanonicalConcept | `name` | Controlled vocabulary from Layer 0 seed |
| ConceptDefinition | `id` (canonical name) | Per-survey operationalization |
| SourceDocument | `catalog_id` | One node per PDF, set in config |
| Threshold | `id` (canonical name) | Dedup by measure + scope |
| TemporalEvent | `id` (canonical name) | Dedup by date + subject |
| QualityCaveat | `id` (canonical name) | Dedup by topic |

### 6.3 OHIO Dedup

"Only Handle It Once" — deduplication happens at write time through MERGE semantics. If the same fact appears in overlapping chunks (section 3.2 chunk overlaps with section 3.3 chunk), MERGE on the canonical `id` collapses them.

If cross-document entity resolution becomes problematic (e.g., ACS and CPS documents describe the same concept with different phrasing), a post-extraction dedup pass can be added. This is deferred until empirically needed.

### 6.4 SourceDocument Handling

Each PDF maps to exactly one `SourceDocument` node. The `catalog_id` is set in `config.py`:

```python
SOURCE_CATALOG = {
    "cps_handbook": {
        "catalog_id": "cps_handbook_of_methods_2024",
        "title": "CPS Handbook of Methods",
        "year": 2024,
        "survey": "cps",
        "local_path": "knowledge-base/census_cps/cps_handbook_of_methods.pdf"
    },
    # ...
}
```

This prevents the 11-SourceDocument hallucination from the llm-graph-builder extraction.

---

## 7. File Structure

```
scripts/quarry/
├── README.md           # Setup, usage, extending to new surveys
├── config.py           # Shared config: Neo4j creds, API keys, source catalog,
│                       #   controlled vocabularies, schema version
├── schema.json         # Machine-readable v3.1 schema definition
├── seed.py             # Layer 0 recreation: AnalysisTask + REQUIRES + reference nodes
├── chunk.py            # Docling wrapper: PDF → list of structured chunks
├── extract.py          # Main pipeline: PDF → chunk → LLM extract → Neo4j write
├── prompts.py          # Extraction prompt templates with controlled vocab
├── harvest.py          # Layer 2 harvest queries (with value_type filtering)
├── export.py           # Quarry → staging JSON for pragmatics packs
└── utils.py            # Shared: Neo4j driver management, JSON parsing, logging
```

### 7.1 Dependencies

Runtime (extraction time, not MCP server runtime):
- `docling` — PDF parsing and hierarchical chunking
- `anthropic` — LLM API for structured extraction
- `neo4j` — Python driver for quarry database writes
- Standard library: `json`, `logging`, `pathlib`, `dataclasses`

These are development/build dependencies, not runtime dependencies of the MCP server.

### 7.2 Not Included

- No LangChain dependency (direct Anthropic API calls)
- No vector database (structured extraction, not embeddings)
- No web framework (CLI scripts only)
- No llm-graph-builder dependency (fully replaced)

---

## 8. Quality Controls

### 8.1 Extraction Validation

After each LLM extraction call, validate the returned JSON:
1. All node `type` values are in the schema's allowed node types
2. All relationship `type` values are in the schema's allowed relationships
3. All controlled vocabulary fields contain valid values
4. Required properties are present and non-null
5. Fractions are in [0, 1] range
6. Node IDs are snake_case and non-empty

Invalid extractions are logged with the chunk text and LLM response for debugging. The chunk is skipped (not retried — retry with same input produces same output).

### 8.2 Post-Extraction Quality Metrics

After a full document extraction, report:
- Node counts by type (compare against expected distribution)
- Relationship counts by type (flag if MENTIONS > 10% of total — indicates fallback)
- Property completeness rate per node type
- SourceDocument node count (must be exactly 1)
- MERGE collision count (same node matched from multiple chunks — expected, not an error)

### 8.3 Baseline Comparison

The llm-graph-builder extraction of CPS Handbook serves as the quality baseline:
- 401 nodes (many duplicates and noise)
- 291 MENTIONS relationships (should be 0 in new pipeline)
- 11 SourceDocument nodes (should be 1)
- 3 PRODUCES edges from extraction (should be proportional to MethodologicalChoice count)
- 1 genuine harvest finding out of 8 results (should improve with value_type filtering)

The new pipeline must demonstrably outperform this baseline on all metrics.

---

## 9. Target Documents

For the FCSM March 2026 talk, extract these four documents:

| # | Document | Pages | Purpose |
|---|----------|-------|---------|
| 1 | CPS Handbook of Methods | 22 | Baseline comparison against llm-graph-builder |
| 2 | ACS Design & Methodology 2024 | ~150 | Primary ACS methodology source |
| 3 | CPS Technical Paper 77 | 180 | Scale test |
| 4 | Census Quality Standards | ~50 | Normative reference for Layer 0 standards |

### 9.1 Processing Order

1. CPS Handbook first — validates pipeline against known baseline
2. Quality Standards — enriches Layer 0 with authoritative standards
3. ACS D&M — enables cross-survey harvest queries (CPS vs ACS)
4. CPS TP-77 — scale validation

---

## 10. Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| `raw_kg_schema.md` v3.1 | Schema this pipeline writes to |
| `extraction_pipeline.md` | Parent pipeline (this is the upstream stage) |
| `ADR-008` | Decision to build this pipeline |
| `ADR-009` | Decision to ship as toolkit |
| `pragmatics_authoring_guide.md` | Downstream consumer of harvested content |
| `implementation_schedule.md` Phase 5B | Task breakdown for building this |

---

*This document specifies the quarry extraction pipeline. It does not specify harvest, curation, export, or runtime behavior.*
