# Software Requirements Specification (SRS)
## Census MCP Server

*Version 1.0 — February 2026*

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional, data, interface, and structural requirements for the Census MCP Server. It governs what gets built, where it goes, and what constraints apply.

### 1.2 Scope
As defined in the ConOps (`docs/requirements/conops.md`). This system is an MCP server providing Census data with pragmatic consultation.

### 1.3 Definitions
All domain terms (pragmatics, pack, thread, context, latitude) are defined in the Pragmatics Vocabulary (`docs/design/pragmatics_vocabulary.md`). That document is normative. This SRS references but does not redefine those terms.

---

## 2. Repository Structure

This section is law. Code and content go where specified. Deviations require an ADR.

```
census-mcp-server/
│
├── CLAUDE.md                      # Project conventions for AI assistants
├── README.md                      # Public-facing project description
├── pyproject.toml                 # Python project metadata and dependencies
├── LICENSE                        # License file
│
├── docs/                          # Systems engineering documentation
│   ├── requirements/              # ConOps, SRS (this file)
│   ├── architecture/              # System architecture documents
│   ├── decisions/                 # Architecture Decision Records (ADRs)
│   ├── design/                    # Detailed design docs, vocabulary, specs
│   ├── verification/              # Evaluation protocol, test results
│   └── lessons_learned/           # Project narrative, retrospectives
│
├── src/                           # ALL runtime source code
│   ├── census_mcp/                # Main package
│   │   ├── __init__.py
│   │   ├── server.py              # MCP server entry point
│   │   ├── api/                   # Census API client code
│   │   │   ├── __init__.py
│   │   │   └── census_client.py   # HTTP calls to api.census.gov
│   │   ├── geography/             # Geographic resolution
│   │   │   ├── __init__.py
│   │   │   └── resolver.py        # FIPS lookup, disambiguation
│   │   ├── pragmatics/            # Pragmatic consultation engine
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Query classification → domain/tags
│   │   │   ├── retriever.py       # Thread traversal, context collection
│   │   │   ├── compiler.py        # Context → natural language docstring
│   │   │   └── pack.py            # Pack loading, inheritance resolution
│   │   └── tools/                 # MCP tool definitions
│   │       ├── __init__.py
│   │       └── census_tools.py    # Tool schemas and handlers
│   └── __init__.py
│
├── packs/                         # Compiled SQLite packs (shipped artifact)
│   └── .gitkeep                   # Packs are build artifacts, gitignored
│
├── staging/                       # Source of truth for pack content
│   ├── general_statistics/        # Cross-survey statistical principles
│   ├── census/                    # Census Bureau domain context
│   └── acs/                       # ACS-specific context
│
├── knowledge-base/                # Source material (NOT runtime)
│   ├── source-docs/               # Census PDFs, handbooks (gitignored)
│   ├── rules/                     # Extracted pragmatic rules (JSON)
│   └── methodology/               # Processed methodology content
│
├── scripts/                       # Build and utility scripts
│   ├── compile_pack.py            # Build one .db from staging dir
│   ├── compile_all.py             # Build all packs
│   ├── extract/                   # Legacy extraction pipeline scripts
│   └── quarry/                    # Quarry extraction toolkit (ADR-008, ADR-009)
│       ├── config.py              # Shared config, controlled vocabularies
│       ├── schema.json            # Machine-readable KG schema v3.1
│       ├── seed.py                # Layer 0 setup
│       ├── chunk.py               # Docling PDF → structured chunks
│       ├── extract.py             # PDF → LLM extraction → Neo4j write
│       ├── prompts.py             # Extraction prompt templates
│       ├── harvest.py             # Layer 2 harvest queries
│       ├── export.py              # Quarry → staging JSON
│       └── utils.py               # Shared utilities
│
├── tests/                         # All tests
│   ├── unit/                      # Unit tests (pytest)
│   ├── integration/               # Integration tests
│   └── evaluation/                # CQS evaluation harness
│
├── talks/                         # Conference talk materials
│   └── fcsm_2026/                 # FCSM 2026 presentation
├── handoffs/                      # Thread handoff docs (gitignored)
├── cc_tasks/                      # Claude Code task files (gitignored)
└── tmp/                           # Scratch space (gitignored)
```

### 2.1 Placement Rules

| Content Type | Location | Gitignored? |
|-------------|----------|-------------|
| Runtime Python code | `src/census_mcp/` | No |
| MCP tool definitions | `src/census_mcp/tools/` | No |
| Pragmatics engine | `src/census_mcp/pragmatics/` | No |
| Compiled packs (.db) | `packs/` | Yes |
| Pack staging (JSON) | `staging/` | No |
| Source PDFs/docs | `knowledge-base/source-docs/` | Yes |
| Extracted rules | `knowledge-base/rules/` | No |
| Build/compile scripts | `scripts/` | No |
| Legacy extraction scripts | `scripts/extract/` | No |
| Quarry extraction toolkit | `scripts/quarry/` | No |
| Systems engineering docs | `docs/` (appropriate subdir) | No |
| ADRs | `docs/decisions/` | No |
| Test code | `tests/` (appropriate subdir) | No |
| Evaluation results | `docs/verification/` | No |
| Talk materials | `talks/` (by conference) | No |
| Handoffs | `handoffs/` | Yes |
| CC task files | `cc_tasks/` | Yes |
| Scratch/temp | `tmp/` | Yes |

### 2.2 Naming Conventions

- **Python files:** `snake_case.py`
- **Python packages:** `snake_case/`
- **Docs:** `snake_case.md`
- **ADRs:** `NNNN_short_description.md` (zero-padded sequence number)
- **Staging JSON:** `domain_name.json` within domain directory
- **CC tasks:** `YYYY-MM-DD_description.md`
- **Handoffs:** `YYYY-MM-DD_description.md`

### 2.3 What Does NOT Exist in This Repo

- No `crystals/` directory (legacy term, purged)
- No `crystal_ensemble.py` or similar (legacy term, purged)
- No R code or R dependencies
- No Docker infrastructure (deferred)
- No vector database or embedding infrastructure
- No frontend or UI code

---

## 3. Functional Requirements

### 3.1 Data Retrieval

| ID | Requirement | Priority |
|----|------------|----------|
| FR-DR-001 | System SHALL accept natural language queries describing demographic data needs | Must |
| FR-DR-002 | System SHALL resolve geographic references to valid Census FIPS codes | Must |
| FR-DR-003 | System SHALL disambiguate geographic references when multiple matches exist (e.g., "Portland" → Oregon vs. Maine) | Must |
| FR-DR-004 | System SHALL construct valid Census API URLs and retrieve data | Must |
| FR-DR-005 | System SHALL return data in structured format with variable labels | Must |
| FR-DR-006 | System SHALL handle Census API errors gracefully with user-readable messages | Must |
| FR-DR-007 | System SHALL support batch retrieval of multiple variables for a single geography in one call | Must |
| FR-DR-008 | System SHALL support batch retrieval of a single variable across multiple geographies in one call | Must |
| FR-DR-009 | System SHALL support multi-variable, multi-geography batch retrieval | Should |
| FR-DR-010 | System SHALL return batch results in a structured tabular format suitable for downstream analysis | Must |

### 3.2 Pragmatic Consultation

| ID | Requirement | Priority |
|----|------------|----------|
| FR-PC-001 | System SHALL provide pragmatic guidance when queried by topic (domain, geography, variable characteristics, time period), where topics are identified by the calling LLM [Updated 2026-02-11 per ADR-003/004] | Must |
| FR-PC-002 | System SHALL retrieve relevant pragmatic context based on query classification | Must |
| FR-PC-003 | System SHALL return pragmatic context as structured data bundled with tool responses, where the calling LLM interprets and applies the guidance [Updated 2026-02-11 per ADR-003/004] | Must |
| FR-PC-004 | System SHALL respect latitude levels: none-latitude context MUST NOT be overridden by the LLM | Must |
| FR-PC-005 | System SHALL support pack inheritance (ACS inherits from Census inherits from General) | Must |
| FR-PC-006 | System SHALL load context from compiled SQLite packs at runtime | Must |
| FR-PC-007 | System SHOULD include provenance (source document, section) for each context item | Should |

### 3.3 Source Routing

| ID | Requirement | Priority |
|----|------------|----------|
| FR-SR-001 | System SHALL identify when Census data is not the appropriate source for the user's question | Should |
| FR-SR-002 | System SHALL suggest alternative data sources when redirecting | Should |
| FR-SR-003 | System SHALL explain why a redirect is recommended | Should |

### 3.4 Response Quality

| ID | Requirement | Priority |
|----|------------|----------|
| FR-RQ-001 | System SHALL include margin of error when reporting ACS estimates | Must |
| FR-RQ-002 | System SHALL flag estimates with unacceptable coefficient of variation | Must |
| FR-RQ-003 | System SHALL communicate fitness-for-use relative to the user's apparent purpose | Should |
| FR-RQ-004 | System SHALL warn about temporal comparability issues (methodology changes, COVID disruption) | Should |

### 3.5 Extraction Pipeline

| ID | Requirement | Priority |
|----|------------|----------|
| FR-EP-001 | System SHALL provide a script to export Context nodes, Pack nodes, and thread edges from the Neo4j `pragmatics` database to staging JSON conforming to the Pydantic ContextItem model | Must |
| FR-EP-002 | System SHALL provide a script to import staging JSON into the Neo4j `pragmatics` database, creating or updating Context nodes and thread edges | Must |
| FR-EP-003 | Export script SHALL produce JSON files organized by domain subdirectory (`staging/acs/`, `staging/census/`, `staging/general_statistics/`) with items grouped by category | Must |
| FR-EP-004 | Import script SHALL validate all items against Pydantic models before writing to Neo4j | Must |
| FR-EP-005 | Export script SHALL be idempotent — running it twice produces identical output | Must |
| FR-EP-006 | Import script SHALL support incremental updates — new items added, existing items updated, no items deleted without explicit flag | Should |
| FR-EP-007 | System SHALL support LLM-assisted bulk extraction from source documents (PDFs) via section-aware chunking and structured JSON prompting | Must |
| FR-EP-008 | System SHALL use Docling for PDF parsing with structure-aware chunking (section boundaries, table preservation, reading order) | Must |
| FR-EP-009 | Export and import scripts SHALL live in `scripts/` and be documented in CLAUDE.md | Must |
| FR-EP-010 | Compiled SQLite packs SHALL include a `provenance_catalog` table that indexes each source citation per context item, enabling redundancy detection and extraction coverage tracking | Must |

**Rationale:** ADR-001 separates authoring (Neo4j) from runtime (SQLite). The round-trip scripts are the bridge. Without them, the pipeline is conceptual architecture with no implementation. In-session extraction feeds Neo4j directly; the export script then produces staging JSON for version control and compilation. Future scale uses agent swarms for extraction, but the foundation is these two scripts.

**Pipeline:**
```
Source docs → (LLM extraction, in-session or automated) → Neo4j pragmatics DB
    → neo4j_to_staging.py → staging/*.json → compile_pack.py → packs/*.db
    ← staging_to_neo4j.py ← (for bootstrap/sync)
```

### 3.6 Quarry Extraction Pipeline

| ID | Requirement | Priority |
|----|------------|----------|
| FR-QE-001 | Quarry extraction toolkit SHALL live in `scripts/quarry/` and ship as a project component | Must |
| FR-QE-002 | Extraction pipeline SHALL use Docling `HierarchicalChunker` for section-aware chunking (not page-based) | Must |
| FR-QE-003 | Extraction SHALL produce structured JSON conforming to raw KG schema v3.1 with controlled vocabulary enforcement | Must |
| FR-QE-004 | All writes to quarry SHALL use MERGE for entity resolution at write time | Must |
| FR-QE-005 | Each source PDF SHALL produce exactly one SourceDocument node (canonical name from config) | Must |
| FR-QE-006 | Extraction SHALL enforce controlled vocabularies: `fact_category`, `dimension`, `value_type`, `assertion_type` with three-tier validation (core, provisional, rejected) per ADR-010 | Must |
| FR-QE-007 | Extraction SHALL validate returned JSON before writing: schema-valid types, required properties, range checks | Must |
| FR-QE-008 | Pipeline SHALL report post-extraction quality metrics: node counts by type, relationship distribution, property completeness, MERGE collision count | Must |
| FR-QE-009 | Pipeline SHALL NOT produce MENTIONS relationships (indicates schema fallback failure) | Must |
| FR-QE-010 | Quarry toolkit SHALL include `seed.py` to recreate Layer 0 (AnalysisTask + REQUIRES + reference nodes) from scratch | Must |
| FR-QE-011 | Harvest queries SHALL filter on `value_type` to prevent cross-type threshold comparison false positives | Must |
| FR-QE-012 | Quarry toolkit SHALL include `export.py` to transform harvested candidates into staging JSON | Should |
| FR-QE-013 | Toolkit dependencies (docling, anthropic, neo4j) SHALL be development dependencies, not runtime MCP server dependencies | Must |
| FR-QE-014 | Controlled vocabularies SHALL support evolutionary extension: new terms accepted provisionally with warnings, promoted to core after recurrence across 2+ documents, rejected with correction mapping if determined to be errors. Vocabulary changes SHALL be auditable with source document, date, and occurrence count. (ADR-010) | Must |

**Rationale:** ADR-008 demonstrated that llm-graph-builder produces unacceptable extraction quality (291 MENTIONS fallback edges, 11 hallucinated SourceDocument nodes, null properties on QualityAttribute). ADR-009 establishes the toolkit as a reproducible methodology for the FCSM paper. The requirements encode the specific failure modes discovered empirically.

**Design spec:** `docs/design/quarry_extraction_pipeline.md`

### 3.7 Composability

| ID | Requirement | Priority |
|----|------------|----------|
| FR-CO-001 | MCP tools SHALL be independently callable — no tool should require prior tool calls to function | Must |
| FR-CO-002 | Tool responses SHALL be structured data suitable for consumption by other tools or agents | Must |
| FR-CO-003 | System SHALL support an analysis planning mode where the host LLM can discover available variables and geographies before committing to retrieval | Should |
| FR-CO-004 | System SHALL NOT maintain session state between tool calls — each call is self-contained | Must |

**Rationale:** The MCP is one component in larger agentic workflows. An LLM planning a full analysis (retrieve data, compare geographies, assess trends) will call these tools repeatedly and compose results. Tools must be stateless, independently callable, and return machine-readable output.

---

## 4. Data Requirements

### 4.1 Pack Schema

Packs are SQLite databases conforming to the schema defined in the Pragmatics Vocabulary document. The core tables are:

- **context** — Individual context items with latitude, domain, and compiled text
- **threads** — Edges connecting context items (inherits, applies_to, relates_to)
- **packs** — Pack metadata with parent pack references and version
- **pack_contents** — Maps context items to packs

The full schema DDL is specified in `docs/design/pragmatics_vocabulary.md` § Schema Implication.

### 4.2 Pack Hierarchy

```
general_statistics (root)
    └── census
        ├── acs          (v1 scope)
        ├── decennial    (future)
        ├── pep          (future)
        └── saipe        (future)
```

### 4.3 Staging Format

Pack content is authored and version-controlled as JSON files in `staging/`. Each JSON file contains an array of context items conforming to:

```json
{
  "context_id": "ACS-POP-001",
  "domain": "acs",
  "category": "population_threshold",
  "latitude": "none",
  "context_text": "The 1-year ACS is not published for geographies with population under 65,000. Use 5-year ACS for these areas.",
  "triggers": ["small_geography", "population", "1yr_acs"],
  "thread_edges": [
    {"target": "GEN-TV-001", "edge_type": "inherits"},
    {"target": "ACS-MOE-001", "edge_type": "relates_to"}
  ],
  "source": {
    "document": "ACS Handbook Chapter 7",
    "section": "Table 7.1",
    "extraction_method": "manual"
  }
}
```

### 4.4 Geographic Data

The system requires a geographic lookup capability for resolving place names to FIPS codes. Implementation approach (gazetteer DB, API lookup, or embedded table) is a design decision, not a requirement.

---

## 5. Interface Requirements

### 5.1 MCP Interface

| ID | Requirement | Priority |
|----|------------|----------|
| IR-001 | System SHALL implement MCP protocol (stdio transport) | Must |
| IR-002 | System SHALL expose Census data retrieval as MCP tools | Must |
| IR-003 | System SHALL dynamically modify tool descriptions based on pragmatic context | Must |
| IR-004 | System SHOULD support SSE transport for remote deployment | Should |

### 5.2 Census API Interface

| ID | Requirement | Priority |
|----|------------|----------|
| IR-010 | System SHALL make HTTP GET requests to `api.census.gov` | Must |
| IR-011 | System SHALL support ACS 5-year and 1-year endpoints | Must |
| IR-012 | System SHALL handle API rate limiting gracefully | Must |
| IR-013 | System SHALL support Census API key authentication | Must |

### 5.3 Pack Interface

| ID | Requirement | Priority |
|----|------------|----------|
| IR-020 | System SHALL read packs from `packs/` directory at startup | Must |
| IR-021 | System SHALL resolve pack inheritance at load time | Must |
| IR-022 | System SHALL support hot-reload of packs without server restart | Should |

---

## 6. Quality Requirements

### 6.1 Performance

| ID | Requirement | Priority |
|----|------------|----------|
| QR-001 | System SHALL respond to single queries within 10 seconds (excluding Census API latency) | Should |
| QR-002 | Pack loading SHALL complete within 2 seconds at startup | Should |
| QR-003 | System SHALL log all Census API calls for debugging | Must |
| QR-004 | System SHALL be installable via `pip install` with no system dependencies beyond Python 3.11+ | Must |
| QR-005 | Compiled packs SHALL be under 10MB each | Should |

### 6.2 Reproducibility & Configuration Management

| ID | Requirement | Priority |
|----|------------|----------|
| QR-010 | ALL parameters that affect system outputs SHALL be externalized to configuration files. No output-affecting defaults SHALL be hardcoded in application logic. | Must |
| QR-011 | Configuration SHALL be managed through a single-source-of-truth config module (`src/census_mcp/config.py`) with environment variable overrides for deployment flexibility. | Must |
| QR-012 | Configuration module SHALL load `.env` from project root when `python-dotenv` is available, falling back gracefully when it is not. | Must |
| QR-013 | Data product defaults (year, product type) SHALL be documented with comments indicating release schedule and update procedures. | Must |
| QR-014 | Evaluation harness SHALL record all configuration state (model strings, default year, default product, system prompts) in output metadata for every run. | Must |
| QR-015 | Model version strings SHALL be pinned to exact checkpoint identifiers (e.g., `claude-sonnet-4-5-20250929`), never aliases (e.g., `claude-sonnet`). | Must |
| QR-016 | Evaluation results SHALL be fully reproducible given: (a) the config file state, (b) the pack content hash, (c) the test battery version, and (d) the pinned model strings. | Must |

**Rationale (QR-010):** A hardcoded `default: 2022` in a tool schema silently determined every query result when the caller did not specify year. When ACS 2024 5-year data was released, the system served stale data and claimed it was current — a D6 (Groundedness) failure. Hidden parameters that affect outputs are the most dangerous class of bug because they produce systematically wrong results that look correct. See DEC-4B-019.

**Rationale (QR-016):** Evaluation results that cannot be reproduced have no scientific value. The four components (config, packs, battery, models) fully determine the experimental conditions. Any change to any of these components produces a new experiment, not a reproduction of the old one.

---

## 7. Constraints

| ID | Constraint |
|----|-----------|
| C-001 | Pure Python. No R, no compiled extensions requiring build tools. |
| C-002 | SQLite for pack storage. No external database servers at runtime. |
| C-003 | Census API is the sole data source for demographic data. No scraping. |
| C-004 | Pragmatic context is pre-compiled, not generated at query time. |
| C-005 | The term "crystal" SHALL NOT appear in any code, documentation, or file names. |
| C-006 | No output-affecting parameter SHALL be hardcoded in application code. All such parameters SHALL reside in `src/census_mcp/config.py` with environment variable overrides. This is a permanent, non-negotiable project rule. See QR-010, DEC-4B-019. |

---

## 8. Verification

The system is evaluated using the Conversational Quality Score (CQS) protocol, which compares system responses against expert judgment on curated test queries. The protocol is specified in `docs/verification/`.

Test dimensions:
1. **Source appropriateness** — Did it use the right data product?
2. **Uncertainty communication** — Did it report MOE and fitness caveats?
3. **Redirect correctness** — Did it redirect when Census wasn't appropriate?
4. **Explanation quality** — Did it explain its reasoning?
5. **Harm avoidance** — Did it avoid enabling bad analysis?

### 8.1 API Testbench

| ID | Requirement | Priority |
|----|------------|----------|
| VR-001 | System SHALL provide a command-line testbench that launches the MCP server and executes test queries programmatically | Must |
| VR-002 | Testbench SHALL verify healthy MCP connection before running test queries | Must |
| VR-003 | Testbench SHALL support multiple LLM backends (Claude, OpenAI, Gemini) as the reasoning caller | Must |
| VR-004 | Testbench SHALL run identical test queries against each configured backend and collect responses | Must |
| VR-005 | Testbench SHALL record structured results (query, model, response, tool calls, pragmatics returned, latency) for analysis | Must |
| VR-006 | Testbench SHALL output results in a format suitable for CQS scoring (CSV or JSON) | Must |
| VR-007 | Testbench SHOULD support adding new test queries without code changes (data-driven test definitions) | Should |

**Rationale:** The pragmatics layer (packs + retriever) should improve consultation quality regardless of which LLM reasons over the tools. Multi-model comparison validates that the value is in the MCP (data + pragmatics), not in any single model's training data. This directly tests the ADR-003 claim that reasoning belongs to the caller — if pragmatics work, even weaker models should produce better consultations than stronger models without pragmatics.

**Location:** `tests/evaluation/` for harness code, `docs/verification/` for results.

### 8.2 Test Battery Design

| ID | Requirement | Priority |
|----|------------|----------|
| VR-010 | Test battery split SHALL be driven by statistical power analysis: sufficient normal queries for equivalence testing (no-harm claim) and sufficient edge cases for superiority testing (treatment effect). Current design: 41% normal / 59% edge cases (n=39 total). See DEC-4B-009. | Must |
| VR-011 | Test battery SHALL include geographic edge cases: independent cities (St. Louis MO, 38 Virginia independent cities), consolidated city-counties, NYC boroughs, DC as state-equivalent | Must |
| VR-012 | Test battery SHALL include small-area reliability cases: places under 65K, under 20K, tract-level requests | Must |
| VR-013 | Test battery SHALL include temporal edge cases: cross-vintage comparison, overlapping ACS periods, break-in-series years, inflation-unadjusted dollar comparisons | Must |
| VR-014 | Test battery SHALL include ambiguity cases: "Portland" (OR vs ME), "Springfield" (multiple states), "Washington" (state vs DC) | Must |
| VR-015 | Test battery SHALL include product-mismatch cases: 1-year request for small geography, decennial question sent to ACS | Should |
| VR-016 | Test battery SHOULD include persona-based query variants that test accessibility across user sophistication levels | Should |

**Rationale (VR-016):** The system's stated goal is accessibility — "any 8th grader with an active imagination." Testing with persona-based queries (curious student, small business planner, retiree exploring data, city planner, journalist on deadline) validates that pragmatics produce useful consultations across the full user spectrum, not just for statisticians. Persona development is a future requirement; the testbench must support it when ready.

### 8.3 Stage 1: Response Generation Pipeline

| ID | Requirement | Priority |
|----|------------|----------|
| VR-020 | Response generation SHALL produce paired control/treatment responses for each test query, where control receives no MCP tools and treatment receives full tool access | Must |
| VR-021 | Response generation SHALL use a single caller model for both conditions within an evaluation round, controlled by `judge_config.yaml` | Must |
| VR-022 | Response generation SHALL record complete provenance: model string, system prompt hash, tool call transcripts, pragmatics context IDs returned, token counts, and latency | Must |
| VR-023 | Treatment condition SHALL use an agent loop with configurable `max_tool_rounds` (default: 20). If the loop exhausts without the model issuing a final response, the system SHALL perform forced synthesis and flag `tool_rounds_exhausted=True` | Must |
| VR-024 | Response generation SHALL output QueryPair records in JSONL with category and difficulty metadata for downstream stratification | Must |

**Rationale:** The paired design ensures the only experimental difference is MCP tool access. Complete provenance enables Stage 3 fidelity verification. The forced synthesis mechanism (VR-023) prevents data loss from agent loops that fail to converge, a bug discovered in v1/v2 where 7/39 queries produced truncated responses. See DEC-4B-016.

**Location:** `src/eval/generate_responses.py`, config in `src/eval/judge_config.yaml`.

### 8.4 Stage 2: LLM-as-Judge Scoring Pipeline

| ID | Requirement | Priority |
|----|------------|----------|
| VR-030 | Judge scoring SHALL use at minimum three independent LLM vendors to detect self-enhancement bias | Must |
| VR-031 | Judge scoring SHALL implement counterbalanced presentation: each query SHALL be scored with both control-first and treatment-first orderings across passes | Must |
| VR-032 | Judge scoring SHALL use a minimum of 6 passes per vendor per query (3 control-first, 3 treatment-first) to enable test-retest reliability measurement | Must |
| VR-033 | Judge prompt SHALL present responses as anonymized "Response A" and "Response B" with no condition labels visible to the judge | Must |
| VR-034 | Judge prompt SHALL NOT contain temporal anchors (dates, "current year" references) that could bias scoring based on judge training cutoff. See DEC-4B-015 | Must |
| VR-035 | Judge scoring SHALL use the CQS rubric with dimensions D1 (Source Selection), D2 (Methodology), D3 (Uncertainty Communication), D4 (Definitions), D5 (Reproducibility). Each dimension scored 0-2 with confidence 1-5 and free-text reasoning | Must |
| VR-036 | D6 (Groundedness) SHALL be excluded from the CQS composite score and reported separately as a methodological note. Groundedness is measured by Stage 3 automated fidelity instead. See DEC-4B-023 | Must |
| VR-037 | Judge scoring SHALL record complete JudgeRecord metadata: run_id, pass_number, presentation_order, response label mapping, raw response text, parse_success flag, and token counts | Must |
| VR-038 | Judge scoring SHALL use checkpoint-based deduplication with full tuple matching (query_id, judge_key, ordering, pass_number) to enable safe pipeline restarts without re-scoring completed tasks | Must |
| VR-039 | Judge scoring pipeline SHALL filter to configured valid run IDs (`stage2_valid_run_ids` in config) to prevent contamination from prior pipeline versions. All run parameters SHALL be read from `judge_config.yaml` per C-006 | Must |

**Rationale:** The three-vendor panel (VR-030) addresses a known limitation of LLM-as-judge: models may preferentially score their own outputs higher. Counterbalancing (VR-031) enables position bias measurement. The temporal anchor prohibition (VR-034) was added after discovering that judges penalized treatment responses for citing data vintages beyond their training cutoff, creating a systematic confound. Run ID filtering (VR-039) was added after discovering that stale v2 judge scores contaminated aggregate analysis when the glob pattern loaded all JSONL files indiscriminately.

**Location:** `src/eval/judge_pipeline.py`, prompts in `src/eval/judge_prompts.py`, config in `src/eval/judge_config.yaml`.

### 8.5 Stage 3: Pipeline Fidelity Verification

| ID | Requirement | Priority |
|----|------------|----------|
| VR-040 | Fidelity verification SHALL compare every quantitative claim in the treatment response against the actual tool call data that produced it | Must |
| VR-041 | Fidelity verification SHALL classify each claim as: `match`, `mismatched`, `no_source`, `calculation_correct`, or `calculation_incorrect` | Must |
| VR-042 | Fidelity verification SHALL compute auditability for both treatment and control responses symmetrically, classifying claims as `auditable`, `partially_auditable`, `unauditable`, or `non_claim` | Must |
| VR-043 | Auditability percentages SHALL exclude `non_claim` items (methodological statements, source citations) from the denominator. See data contamination incident where including non_claims diluted treatment auditability from 72.8% to 46.0% | Must |
| VR-044 | Fidelity score SHALL be computed as (matched + calculation_correct) / total_claims × 100, including `no_source` claims in the denominator. A secondary `substantive_fidelity` metric MAY exclude `no_source` from the denominator and SHALL be reported separately | Must |

**Rationale:** Stage 3 replaces the flawed D6 rubric dimension (DEC-4B-023) with automated verification. D6 rewarded vagueness and penalized specificity — judges scored unverifiable hedged claims higher than precise tool-grounded claims because vague claims are harder to falsify. Automated fidelity directly measures whether the system faithfully reports what its tools returned, which is the actual property D6 was intended to measure.

**Location:** `src/eval/fidelity_check.py`, output in `results/stage3/`.

### 8.6 Aggregate Analysis

| ID | Requirement | Priority |
|----|------------|----------|
| VR-050 | Aggregate analysis SHALL compute Cohen's d effect sizes with 95% bootstrap confidence intervals (n=1000 iterations, seed=42) for each CQS dimension (D1-D5) and the composite (mean of D1-D5) | Must |
| VR-051 | Aggregate analysis SHALL compute both independent-samples and paired Cohen's d. Paired d (computed on query-level means) SHALL be the primary metric for stratified analysis. Independent d is reported as a secondary conservative estimate | Must |
| VR-052 | Aggregate analysis SHALL compute Krippendorff's alpha (ordinal scale) across all judge vendors for each dimension as the inter-rater reliability metric | Must |
| VR-053 | Aggregate analysis SHALL test for position bias by comparing treatment scores when presented as Response A vs Response B, per vendor per dimension. Differences exceeding 0.2 with p < 0.05 SHALL be flagged | Must |
| VR-054 | Aggregate analysis SHALL test for self-enhancement bias by comparing Anthropic's treatment-control effect size delta against the average of other vendors' deltas. Differences exceeding 0.3 SHALL be flagged | Must |
| VR-055 | Aggregate analysis SHALL test for verbosity bias by computing Spearman's ρ between response character length and composite CQS score, separately for treatment and control conditions | Must |
| VR-056 | Aggregate analysis SHALL compute test-retest reliability as Pearson r separately for each pass-pair (1,2), (3,4), (5,6) per vendor per dimension, and report the overall lumped r as a secondary metric | Must |
| VR-057 | Statistical tests on paired conditions (Wilcoxon signed-rank) SHALL aggregate to the query level before testing to respect the experimental unit. The experimental unit is the query (n=39), not the judge record (n=702). All p-values SHALL be reported as exact two-tailed values | Must |
| VR-058 | Aggregate analysis SHALL stratify results by query category (normal vs edge cases) and report per-stratum effect sizes with bootstrap CIs | Must |
| VR-059 | Aggregate analysis SHALL compute judge preference rates (treatment preferred, control preferred, tie) per vendor and pooled, mapping the anonymized A/B preference back to condition labels | Must |
| VR-060 | Aggregate analysis SHALL output: CSV files for each analysis type, a markdown report with publication-ready tables, and a JSON archive of all computed statistics | Must |
| VR-061 | Aggregate analysis SHALL load only records matching valid run IDs from config. The script SHALL report total records loaded, per-vendor counts, and parse failure counts. If any vendor has fewer than expected records, it SHALL emit a warning | Must |

**Rationale:** These requirements encode methodological decisions that were made iteratively during Phase 4B development. VR-051 addresses the paired vs independent d decision — the experimental design is paired (every query has both conditions), so paired d is the correct primary metric, but independent d provides a conservative lower bound. VR-057 was added after discovering that running Wilcoxon on 1,002 non-independent records (multiple vendors × passes per query) produced meaningless p-values of 0.0000 for every comparison. VR-061 was added after the v2 data contamination incident where stale judge scores inflated the apparent sample size from 702 to 2,821.

**Location:** `src/eval/analyze_results.py`, output in `results/stage2/analysis/`.

### 8.7 Data Provenance

| ID | Requirement | Priority |
|----|------------|----------|
| VR-070 | Each pipeline run SHALL generate a unique run_id (timestamp-based) embedded in every output record | Must |
| VR-071 | Stale or superseded pipeline outputs SHALL be archived to a versioned subdirectory (e.g., `archive_v2/`) with a README documenting why the data was superseded and what bugs or methodology changes invalidated it | Must |
| VR-072 | The active results directory SHALL contain only data from the current valid pipeline version. Aggregate analysis SHALL NOT glob indiscriminately across all available files | Must |

**Rationale:** The Phase 4B evaluation went through three pipeline versions (v1: truncation bugs, v2: temporal confound, v3: clean). At one point, aggregate analysis inadvertently loaded all three versions' outputs simultaneously, contaminating every computed statistic. These requirements formalize the hard-won lesson that data provenance in iterative evaluation pipelines requires active management, not passive file accumulation.

**Location:** Config in `judge_config.yaml` (`stage2_valid_run_ids`), archive in `results/stage2/archive_v2/`.

---

## 9. Traceability

Requirements in this document trace to:
- **ConOps** (`docs/requirements/conops.md`) — Operational need
- **Design docs** (`docs/design/`) — Implementation approach
- **Tests** (`tests/`) — Verification
- **ADRs** (`docs/decisions/`) — Design rationale

The trace system (`.trace/`) maintains these relationships.

---

*This document specifies what must be built. Design documents specify how.*
