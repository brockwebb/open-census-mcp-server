# Extraction Pipeline Specification
## From Source Documents to Compiled Packs

*Version 1.0 — February 2026*

---

## 1. Purpose

This document specifies how Census methodology source documents are transformed into structured pragmatic context items, staged as JSON, and compiled into SQLite packs that ship with the MCP server.

This is build tooling, not runtime code. Nothing in this pipeline runs when a user asks a question. It runs once (or on repack) to produce the artifacts the runtime system consumes.

---

## 2. Pipeline Overview

```
SOURCE DOCS              EXTRACTION           STAGING              COMPILATION
─────────────           ──────────           ───────              ───────────
PDFs, HTML,    ──►  LLM-assisted     ──►  JSON files     ──►  SQLite packs
handbooks,          extraction with        in staging/         in packs/
methodology         schema template        (version            (build
docs                                       controlled)         artifacts)

knowledge-base/     scripts/extract/       staging/            packs/
source-docs/                               ├── general/        ├── general_statistics.db
                                           ├── census/         ├── census.db
                                           └── acs/            └── acs.db
```

**Source of truth is staging JSON, not source docs and not compiled packs.**

- Source docs are reference material (gitignored, large, binary)
- Staging JSON is the curated, reviewed, version-controlled content
- Packs are deterministic build artifacts from staging

---

## 3. Stage 1: Source Document Preparation

### 3.1 Input
Census methodology documents stored in `knowledge-base/source-docs/`. These include:
- ACS Handbook chapters (PDF)
- Census Bureau methodology pages (HTML)
- Statistical methodology papers
- FCSM guidance documents
- Internal handbooks and training materials

### 3.2 Processing
Documents must be chunked for LLM consumption. Chunking strategy:

- **PDF:** Extract text, split by section headings where detectable, otherwise by paragraph groups (~500-800 tokens per chunk)
- **HTML:** Parse, strip boilerplate, split by section
- **Preserve provenance:** Each chunk retains source document name, page/section number

### 3.3 Output
Chunked text files or in-memory chunks ready for extraction. Stored in `tmp/` during processing (ephemeral, not committed).

### 3.4 Tooling
`scripts/extract/chunk_sources.py` — Reads source docs, produces chunks with provenance metadata.

---

## 4. Stage 2: Context Extraction

### 4.1 Approach
LLM-assisted extraction using the pragmatics schema as output template. Each chunk is presented to the LLM with a structured prompt that asks for context items conforming to the staging format.

### 4.2 Model Requirements
The extraction model must be capable of:
- Reading technical statistical methodology text
- Making judgment calls about latitude levels (none/narrow/wide/full)
- Assigning domain and category tags
- Writing clear, actionable context text (what an expert would say)
- Identifying thread connections between concepts

**Minimum capability:** Claude Sonnet or equivalent. A 7B parameter model will not reliably assign latitude or write expert-quality context text. The judgment required is the hard part — this is not summarization, it is expertise encoding.

### 4.3 Extraction Prompt Template

The extraction prompt provides:
1. The text chunk with provenance
2. The pragmatics vocabulary (latitude definitions, category list)
3. The output schema (JSON format)
4. Examples of well-formed context items
5. Instructions to extract ALL pragmatic knowledge from the chunk, not just summaries

```
You are extracting pragmatic context from Census Bureau methodology 
documentation. Pragmatic context is expert knowledge about fitness-for-use 
— when, whether, and how to use data appropriately.

For each piece of expert knowledge in this chunk, produce a context item:

{
  "context_id": "[DOMAIN]-[CATEGORY]-[NNN]",
  "domain": "acs|census|general_statistics",
  "category": "population_threshold|temporal_validity|geographic_pitfall|
               source_selection|margin_of_error|coverage_bias|
               imputation_quality|comparison_validity|subject_specific|
               data_vintage",
  "latitude": "none|narrow|wide|full",
  "context_text": "[What the expert would tell you. Natural language. 
                    Actionable. Specific.]",
  "triggers": ["[tags that should cause this context to be retrieved]"],
  "source": {
    "document": "[source document name]",
    "section": "[page or section]",
    "extraction_method": "llm_assisted"
  }
}

LATITUDE GUIDE:
- none: Physics or law. Data literally doesn't exist. No freedom.
- narrow: Strong guidance. Deviate only with explicit justification.
- wide: Real judgment call. Context-dependent.
- full: Background info. Reason freely.

Extract conservatively. If the text states a hard rule, it's none/narrow.
If the text suggests or recommends, it's wide/full.
Do NOT invent context not present in the source text.
```

### 4.4 Batch Processing
Extraction runs in batches of chunks. Each batch:
1. Sends N chunks to the LLM (batch size tuned to context window)
2. Receives JSON context items
3. Validates against schema
4. Writes to `tmp/extraction_batch_NNN.json`
5. Logs cost and token usage

**Cost control:** Run a small batch first (50 chunks) to calibrate cost per context item before full corpus run.

### 4.5 Output
Raw extracted context items in `tmp/`. These are NOT the staging files — they require human review.

### 4.6 Tooling
`scripts/extract/extract_context.py` — Runs extraction batches against an LLM API. Configurable for Claude API, OpenAI API, or local model.

---

## 5. Stage 3: Review and Staging

### 5.1 Review
Extracted context items must be reviewed before staging. Review checks:
- **Latitude correctness:** Is the latitude assignment appropriate? (Most common error)
- **Context text quality:** Would an expert say this? Is it actionable?
- **Category assignment:** Right bucket?
- **Trigger tags:** Will this context be retrieved for the right queries?
- **Deduplication:** Same knowledge stated in different chunks?
- **Thread connections:** What should this connect to?

### 5.2 Review Tooling
Review can be manual (read JSON, edit) or assisted (LLM second-pass review with cross-reference). The review step is where thread_edges are assigned — extraction may miss connections that only become visible when viewing items in context with each other.

### 5.3 Staging
Reviewed items are placed in `staging/[domain]/[category].json`. Each file contains an array of context items for that domain and category.

File naming: `staging/acs/population_threshold.json`, `staging/acs/margin_of_error.json`, etc.

### 5.4 Version Control
Staging files are the source of truth and are committed to git. Changes to staging files should include commit messages describing what changed and why (especially latitude changes).

### 5.5 Tooling
`scripts/extract/review_helper.py` — Optional. Presents extracted items for review, flags likely issues (duplicate triggers, missing edges, latitude outliers).

---

## 6. Stage 4: Pack Compilation

### 6.1 Process
Compile staging JSON files into SQLite pack databases.

For each pack (e.g., `acs`):
1. Read all JSON files in `staging/acs/`
2. Read parent pack staging files (`staging/census/`, `staging/general_statistics/`)
3. Create SQLite database conforming to pack schema
4. Insert context items
5. Insert thread edges
6. Insert pack metadata (version, parent, compile date)
7. Build indexes
8. Write to `packs/acs.db`

### 6.2 Inheritance
Pack compilation does NOT copy parent context into child packs. At runtime, the system loads the pack hierarchy and resolves inheritance by traversal. The compiled pack contains only its own context items plus edge references to parent items.

### 6.3 Determinism
Same staging files MUST produce identical pack databases (byte-identical modulo SQLite internal ordering). This means:
- No timestamps in row data (compile date goes in pack metadata only)
- Deterministic insertion order (sorted by context_id)
- Fixed SQLite pragmas

### 6.4 Validation
Post-compilation checks:
- All context_ids unique within pack
- All thread edge targets exist (in this pack or declared parent)
- All latitude values valid
- No orphan context items (no triggers, no edges)
- Pack size under 10MB

### 6.5 Tooling
- `scripts/compile_pack.py` — Compile one pack from its staging directory
- `scripts/compile_all.py` — Compile all packs in dependency order (general first, then census, then acs)

---

## 7. Pipeline Execution Summary

```bash
# Step 1: Chunk source documents
python scripts/extract/chunk_sources.py \
  --input knowledge-base/source-docs/ \
  --output tmp/chunks/

# Step 2: Extract context items (costs money — runs LLM API)
python scripts/extract/extract_context.py \
  --input tmp/chunks/ \
  --output tmp/extracted/ \
  --model claude-sonnet-4-20250514 \
  --batch-size 20

# Step 3: Review (human in the loop)
python scripts/extract/review_helper.py \
  --input tmp/extracted/ \
  --output staging/acs/

# Step 4: Compile packs
python scripts/compile_all.py \
  --staging staging/ \
  --output packs/
```

---

## 8. Repack Triggers

Rerun the pipeline (or relevant stages) when:
- New source documents are added to knowledge-base
- Existing context items are corrected (latitude, text, edges)
- New domain pack is created (expansion pack)
- Census Bureau releases new methodology or vintage
- Evaluation reveals missing or incorrect context

Repack is cheap. The expensive step is extraction (LLM cost). Review and compilation are fast.

---

## 9. Cost Estimation

Rough estimates for planning (actual costs depend on model and chunk count):

| Stage | Cost Driver | Estimate |
|-------|------------|----------|
| Chunking | Compute | Free (local) |
| Extraction | LLM API tokens | ~$0.50-2.00 per source document |
| Review | Human time | 2-5 min per context item |
| Compilation | Compute | Free (local) |

For the v1 ACS pack, expect ~100-200 context items extracted from ~10-15 source documents. Total extraction cost: ~$10-30. Total review time: ~4-8 hours.

---

## 10. Alternatives Considered

### 10.1 General Knowledge Graph Extraction (e.g., rahulnyk approach)
Extracts concepts and co-occurrence relationships. Produces topology ("ACS relates to margin of error") but not structured pragmatic context with latitude, triggers, and actionable text. Useful for discovery, wrong for production context encoding.

### 10.2 RAG over Source Docs
Retrieve chunks at query time instead of pre-extracting. Loses the expert review step, latitude assignment, and thread structure. Returns "text that mentions this topic" rather than "expert guidance for this situation." Already tried in v1/v2 — produced semantic smearing.

### 10.3 Manual Authoring Only
Write all context items by hand without LLM assistance. Highest quality but doesn't scale. The pipeline uses LLM for first-draft extraction and human for review — best of both.

### 10.4 7B Local Model for Extraction
Insufficient reasoning capability for latitude assignment and expert-quality context text writing. Latitude is a judgment call, not a classification task. Save the local model for chunking or deduplication, use a capable model for extraction.

---

*This document specifies the build pipeline. It does not run at query time.*
