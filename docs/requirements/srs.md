# Software Requirements Specification (SRS)
## Census MCP Server

*Version 2.0 — February 2026*

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

The system is evaluated using the Conversational Quality Score (CQS) protocol, a knowledge representation study comparing three conditions with equal data tool access. The study measures whether the form of methodology support — none, retrieved document chunks, or curated expert judgment — affects consultation quality when the underlying data access is held constant.

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
| VR-010 | Test battery split SHALL be driven by statistical power analysis: sufficient normal queries for equivalence testing (no-harm claim) and sufficient edge cases for superiority testing (effect detection). Current design: 41% normal / 59% edge cases (n=39 total). See DEC-4B-009 | Must |
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
| VR-020 | Response generation SHALL produce responses for three conditions per test query: control (data tools, no methodology), RAG (data tools, methodology via retrieved chunks), and pragmatics (data tools, methodology via curated MCP tool). All three conditions SHALL have equal access to `get_census_data` and `explore_variables`. The only experimental variable is the form of methodology support | Must |
| VR-021 | Response generation SHALL use a single caller model for all conditions within an evaluation round, controlled by `judge_config.yaml` | Must |
| VR-022 | Response generation SHALL record complete provenance: model string, system prompt (full text), tool call transcripts (including full unsanitized tool returns), pragmatics context IDs returned (pragmatics condition), retrieved chunk metadata (RAG condition), token counts, and latency | Must |
| VR-023 | All three conditions SHALL use the same agent loop with configurable `max_tool_rounds` (default: 20). If the loop exhausts without the model issuing a final response, the system SHALL perform forced synthesis and flag `tool_rounds_exhausted=True` | Must |
| VR-024 | Response generation SHALL output individual ResponseRecord objects in JSONL, one file per condition: `{condition}_responses_{timestamp}.jsonl`. Files SHALL be written to `results/v2_redo/stage1/` | Must |
| VR-025 | Tool filtering SHALL exclude `get_methodology_guidance` from the tool list passed to the Anthropic API for control and RAG conditions. The pragmatics condition SHALL receive the full tool list including `get_methodology_guidance` | Must |
| VR-026 | System prompts SHALL be minimal and equivalent across conditions. Control and RAG SHALL use an identical base prompt. RAG augments the base prompt with retrieved chunks only. The pragmatics prompt adds only the instruction to call `get_methodology_guidance` first. No condition's prompt SHALL contain quality coaching (e.g., "always provide margins of error") | Must |
| VR-027 | Response generation SHALL perform runtime contamination verification: an assertion SHALL confirm that `get_methodology_guidance` is absent from the tool set before every control and RAG query, and present before every pragmatics query. Assertion failure SHALL halt the run | Must |
| VR-028 | Response generation SHALL perform post-run contamination verification: scan all output files and report the count of `get_methodology_guidance` calls per condition. Any such call in control or RAG output SHALL be flagged as contaminated | Must |
| VR-029 | All three conditions SHALL be generated in a single harness run with a shared timestamp to eliminate temporal confounds (API behavior changes, model version drift). The `--condition all` flag SHALL execute control, RAG, and pragmatics sequentially within one MCP server session | Must |
| VR-030 | The agent loop SHALL sanitize `get_census_data` tool results before passing them to the model for control and RAG conditions: the `pragmatics` field SHALL be stripped from the result dict. The full unsanitized result SHALL be preserved in the `ToolCall` log record for fidelity verification. The pragmatics condition SHALL receive unsanitized tool results | Must |

**Rationale:** V1 confounded tool access with knowledge representation — control and RAG had no data tools while pragmatics had full tool access. 33 of 39 RAG responses directed users to data.census.gov because the model had no way to retrieve data. V2 equalizes tool access so the only variable is methodology support form: none (control), retrieved document chunks (RAG), or curated expert judgment via MCP tool (pragmatics). The contamination checks (VR-027, VR-028) are defense-in-depth against the class of confound that invalidated V1. VR-030 addresses a second contamination vector discovered during spot-checking: `get_census_data` bundles curated pragmatics content (context IDs, guidance text, thread edges) in every response via `retriever.get_guidance_by_parameters()`. Without sanitization, all three conditions receive curated expert judgment through the data tool response payload, defeating the experimental design. See ADR-011, `talks/fcsm_2026/2026-02-16_pragmatics_leakage.md`.

**Location:** `src/eval/agent_loop.py`, `src/eval/harness.py`, config in `src/eval/judge_config.yaml`.

### 8.4 Stage 2: LLM-as-Judge Scoring Pipeline

| ID | Requirement | Priority |
|----|------------|----------|
| VR-031 | Judge scoring SHALL use at minimum three independent LLM vendors to detect self-enhancement bias | Must |
| VR-032 | Judge scoring SHALL implement counterbalanced presentation: each query SHALL be scored with both A-first and B-first orderings across passes | Must |
| VR-033 | Judge scoring SHALL use a minimum of 6 passes per vendor per query per comparison (3 A-first, 3 B-first) to enable test-retest reliability measurement | Must |
| VR-034 | Judge prompt SHALL present responses as anonymized "Response A" and "Response B" with no condition labels visible to the judge | Must |
| VR-035 | Judge prompt SHALL NOT contain temporal anchors (dates, "current year" references) that could bias scoring based on judge training cutoff. See DEC-4B-015 | Must |
| VR-036 | Judge scoring SHALL use the CQS rubric with dimensions D1 (Source Selection), D2 (Methodology), D3 (Uncertainty Communication), D4 (Definitions), D5 (Reproducibility). Each dimension scored 0-2 with confidence 1-5 and free-text reasoning | Must |
| VR-037 | D6 (Grounding) SHALL be excluded from the CQS composite score. D6 is a binary gate — treatment conditions ground in authoritative sources by design; control does not. Grounding is verified by Stage 3 automated fidelity. | Must |
| VR-038 | Judge scoring SHALL record complete JudgeRecord metadata: run_id, pass_number, presentation_order, response label mapping, raw response text, parse_success flag, and token counts | Must |
| VR-039 | Judge scoring SHALL use checkpoint-based deduplication with full tuple matching (query_id, judge_key, ordering, pass_number) to enable safe pipeline restarts without re-scoring completed tasks | Must |
| VR-040 | Judge scoring pipeline SHALL filter to configured valid run IDs (`stage2_valid_run_ids` in config) to prevent contamination from prior pipeline versions. All run parameters SHALL be read from `judge_config.yaml` per C-006 | Must |
| VR-041 | Judge scoring SHALL evaluate three pairwise comparisons: (1) control vs RAG, (2) control vs pragmatics, (3) RAG vs pragmatics. Each comparison is a separate judge run using the same rubric, counterbalancing, and vendor panel | Must |
| VR-042 | JudgeRecord SHALL include a `comparison` field identifying which pairwise comparison produced the record (e.g., "control_vs_rag", "control_vs_pragmatics", "rag_vs_pragmatics") | Must |
| VR-043 | Pairwise judge outputs SHALL be written to separate files per comparison to prevent cross-contamination during analysis | Must |
| VR-044 | Judge pipeline SHALL load response pairs from separate per-condition JSONL files using the `comparisons` section of `judge_config.yaml`, joining on query_id with query metadata from the test battery. The V1 `QueryPair` model (single file with paired records) SHALL NOT be used for V2 evaluation | Must |
| VR-045 | Checkpoint files SHALL be scoped per comparison (one checkpoint file per pairwise comparison) to prevent cross-comparison deduplication collisions | Must |
| VR-046 | Judge pipeline SHALL accept a `--comparison` CLI parameter selecting which pairwise comparison to execute. Valid values: `rag_vs_pragmatics`, `control_vs_pragmatics`, `control_vs_rag` | Must |
| VR-047 | Stage 2 QC script SHALL consolidate structural validation (record count, same-condition pairs, comparison field presence), preference analysis, identical vector detection with per-query counts, and per-vendor CQS breakdown. Script SHALL accept `--file` argument and exit with code 1 if structural checks fail | Must |
| VR-048 | V2 aggregate statistical analysis SHALL implement: (1) Friedman omnibus test across 3 conditions (control, RAG, pragmatics) on per-query CQS and per-dimension D1-D5; (2) pairwise Wilcoxon signed-rank post-hoc tests using Pratt zero-difference method (zero_method='pratt'); (3) Holm-Bonferroni correction on the 3 pairwise p-values; (4) paired Cohen's d effect sizes; (5) bootstrap 95% CIs on CQS deltas (10,000 iterations). CQS SHALL use D1-D5 only (D6 excluded). Unit of analysis SHALL be per-query median score (N=39). All analysis parameters SHALL be configured in judge_config.yaml under analysis: section. Script SHALL output formatted summary to stdout, detailed JSON to results/v2_redo/stage2/analysis/aggregate_statistics.json, and markdown summary to results/v2_redo/stage2/analysis/aggregate_statistics.md | Must |

**Rationale:** The three-vendor panel (VR-031) addresses a known limitation of LLM-as-judge: models may preferentially score their own outputs higher. Counterbalancing (VR-032) enables position bias measurement. The temporal anchor prohibition (VR-035) was added after discovering that judges penalized pragmatics responses for citing data vintages beyond their training cutoff, creating a systematic confound. Run ID filtering (VR-040) was added after discovering that stale v2 judge scores contaminated aggregate analysis when the glob pattern loaded all JSONL files indiscriminately. The pairwise comparison approach (VR-041) preserves the validated A-vs-B judge methodology while enabling three-group analysis through paired comparisons.

**Location:** `src/eval/judge_pipeline.py`, prompts in `src/eval/judge_prompts.py`, config in `src/eval/judge_config.yaml`.

### 8.5 Stage 3: Pipeline Fidelity Verification

Stage 3 is the trustworthiness verification stage. D6 (Grounding) is a binary gate — treatment conditions ground in authoritative sources by design; control does not. Stage 3 provides automated claim-level verification that each condition faithfully reports what its evidence sources contain.

#### 8.5.1 Inputs

| Input | Source | Format |
|-------|--------|--------|
| Control responses | `results/v2_redo/stage1/control_responses_{timestamp}.jsonl` | One ResponseRecord per line, keyed by `query_id` |
| RAG responses | `results/v2_redo/stage1/rag_responses_{timestamp}.jsonl` | One ResponseRecord per line, keyed by `query_id` |
| Pragmatics responses | `results/v2_redo/stage1/pragmatics_responses_{timestamp}.jsonl` | One ResponseRecord per line, keyed by `query_id` |
| Pipeline config | `src/eval/judge_config.yaml` | YAML; `fidelity:` section specifies model, provider, rate limits |
| Test battery | `src/eval/battery/queries.yaml` | Query metadata (category, expected behavior) |

**ResponseRecord fields consumed by Stage 3:**

| Field | Used By | Purpose |
|-------|---------|---------|
| `query_id` | All conditions | Join key across condition files |
| `response_text` | All conditions | Text to extract and verify claims from |
| `tool_calls[]` | All conditions | Evidence for claim verification (see 8.5.3 for sanitization) |
| `tool_calls[].result.data` | Pragmatics, Control | Census API return values (the verification ground truth) |
| `retrieved_chunks[]` | RAG only | Document chunks used as additional verification evidence |
| `retrieved_chunks[].source` | RAG only | Source document identifier |
| `retrieved_chunks[].section_path` | RAG only | Section hierarchy within source |
| `retrieved_chunks[].page_start/end` | RAG only | Page range for traceability |
| `retrieved_chunks[].text` | RAG only | Full chunk text for claim matching |
| `retrieved_chunks[].score` | RAG only | Retrieval similarity score |

#### 8.5.2 Outputs

| Output | Location | Format |
|--------|----------|--------|
| Fidelity results | `results/v2_redo/stage3/fidelity_{timestamp}.jsonl` | One FidelityRecord per query, all three conditions per record |
| Summary statistics | stdout | Formatted tables printed at end of run |

**FidelityRecord schema (per query):**

```json
{
  "query_id": "NORM-001",
  "query_text": "What is the population of California?",
  "category": "normal",
  "timestamp": "2026-02-19T...",
  "conditions": {
    "pragmatics": {
      "fidelity": {
        "has_data": true,
        "claims": [{"claim_text": "...", "claim_type": "value", "tool_source": "...", "verdict": "match", "detail": "..."}],
        "summary": {"total_claims": N, "matched": N, "mismatched": N, "no_source": N, "calculation_correct": N, "calculation_incorrect": N}
      },
      "auditability": {
        "claims": [{"claim_text": "...", "claim_type": "quantitative", "specificity": "auditable", "detail": "..."}],
        "summary": {"total_claims": N, "auditable": N, "partially_auditable": N, "unauditable": N, "non_claims": N}
      }
    },
    "rag": { "fidelity": {...}, "auditability": {...} },
    "control": { "fidelity": {...}, "auditability": {...} }
  }
}
```

**Aggregate metrics (computed from FidelityRecords):**

| Metric | Formula | Denominator |
|--------|---------|-------------|
| Fidelity score | (matched + calculation_correct) / total_claims × 100 | All claims including `no_source` |
| Substantive fidelity | (matched + calculation_correct) / (total_claims − no_source) × 100 | Claims with traceable source only |
| Error rate | (mismatched + calculation_incorrect) / total_claims × 100 | All claims |
| Auditability rate | auditable / (total_claims − non_claims) × 100 | Excludes `non_claim` items (VR-053) |

#### 8.5.3 Data Transformations

**CRITICAL: Tool result sanitization for fidelity verification.**

Stage 1 ResponseRecords store full unsanitized tool results, which for `get_census_data` calls include the complete pragmatics guidance payload (context IDs, guidance text, thread edges, provenance, related contexts). A single `get_census_data` return can be 100K+ characters, of which ~1.5K is the actual Census API data and ~98.5K is pragmatics guidance.

Before sending tool call data to the fidelity verification model (Haiku 4.5), the `extract_slim_tool_data()` function strips the tool results to essential fields only:

| Field | Retained | Stripped |
|-------|----------|----------|
| `tool_calls[].arguments` | ✓ (query parameters: variables, state, county, year, product) | |
| `tool_calls[].result.data` | ✓ (Census API data array: header row + value rows) | |
| `tool_calls[].result.pragmatics` | | ✗ Stripped (guidance, related, sources — 98%+ of payload) |
| `tool_calls[].result.source` | | ✗ Stripped (dataset metadata, API URL, geography dict) |

**Why this matters:** Without sanitization, the verification model receives the full pragmatics payload as "evidence," which would (a) overwhelm the context window, (b) cause the model to produce empty or truncated responses, and (c) conflate curated expert guidance with Census API data as verification ground truth. The fidelity check must verify claims against what the Census API actually returned, not against the pragmatics guidance that influenced the response.

**Implementation:** `extract_slim_tool_data()` in `src/eval/fidelity_check.py` filters to `get_census_data` and `get_acs_data` tool calls only, extracting `{arguments, data}` pairs. All other tool calls (e.g., `get_methodology_guidance`, `explore_variables`) are excluded from the verification evidence — their outputs are not quantitative claims.

**RAG chunk formatting:** `extract_rag_chunk_data()` formats retrieved chunks as numbered entries with source, section path, page range, similarity score, and full text. This provides the verification model with the same evidence the RAG condition had when generating its response.

#### 8.5.4 Verification Strategy by Condition

| Condition | Fidelity Verification | Auditability |
|-----------|----------------------|--------------|
| **Pragmatics** | Claims checked against slim tool data (arguments + Census API data array). Tool calls to `get_methodology_guidance` excluded from evidence | ✓ Symmetric measurement |
| **RAG** | Claims checked against slim tool data (if tool calls present) AND retrieved chunks. Claim types expanded to include methodology, definition, geographic, threshold, recommendation | ✓ Symmetric measurement |
| **Control** | Claims checked against slim tool data (if tool calls present). Note: V2 control has full tool access, so tool-grounded claims are verifiable | ✓ Symmetric measurement |

#### 8.5.5 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| VR-050 | Fidelity verification SHALL load three separate per-condition JSONL files from Stage 1 and join on `query_id`. The V1 paired-record format SHALL NOT be used | Must |
| VR-051 | Fidelity verification SHALL verify claims for all three conditions per query, producing a single FidelityRecord per query containing results for all conditions | Must |
| VR-052 | For each condition, fidelity verification SHALL extract every quantitative claim from the response text and classify it against available evidence as: `match`, `mismatch`, `no_source`, `calculation_correct`, or `calculation_incorrect` | Must |
| VR-053 | Fidelity verification SHALL compute auditability for all three conditions symmetrically, classifying claims as `auditable`, `partially_auditable`, `unauditable`, or `non_claim` | Must |
| VR-054 | Auditability rate denominators SHALL exclude `non_claim` items. See data contamination incident where including non_claims diluted pragmatics auditability from 72.8% to 46.0% | Must |
| VR-055 | Fidelity score SHALL be computed as (matched + calculation_correct) / total_claims × 100. A secondary `substantive_fidelity` metric SHALL exclude `no_source` from the denominator and be reported separately | Must |
| VR-056 | RAG fidelity SHALL use the `retrieved_chunks` field as additional evidence beyond tool call data. Each chunk's source, section path, page range, and full text SHALL be included in the verification prompt | Must |
| VR-057 | Tool result sanitization SHALL strip all fields except `arguments` and `result.data` from tool calls before constructing the verification prompt. Specifically, the `pragmatics`, `source`, `related`, and `provenance` fields SHALL be removed. The full unsanitized tool results SHALL remain in the Stage 1 ResponseRecords for archival purposes | Must |
| VR-058 | Only `get_census_data` and `get_acs_data` tool calls SHALL be included in verification evidence. Tool calls to `get_methodology_guidance`, `explore_variables`, and other non-data-retrieval tools SHALL be excluded from the fidelity evidence set | Must |
| VR-059 | Fidelity verification SHALL use a cost-efficient model (currently Haiku 4.5) configured in `judge_config.yaml` `fidelity:` section. The verification model SHALL NOT be the same model used for Stage 1 response generation to avoid self-verification bias | Must |
| VR-070 | Stage 3 aggregate analysis SHALL compute per-condition fidelity scores using the formula: (matched + calculation_correct) / total_claims × 100 (VR-055). SHALL also compute substantive_fidelity excluding no_source from denominator, reported separately | Must |
| VR-071 | Stage 3 aggregate analysis SHALL compute per-condition auditability rates with denominators excluding non_claims items (VR-054). Rates for auditable, partially_auditable, and unauditable SHALL each be reported as percentage of substantive claims | Must |
| VR-072 | Stage 3 aggregate analysis SHALL compute per-condition error rates: (mismatched + calculation_incorrect) / total_claims × 100 | Must |
| VR-073 | Stage 3 aggregate analysis SHALL output formatted markdown to results/{run}/stage3/analysis/fidelity_summary.md and structured JSON to fidelity_summary.json. Both files SHALL include the input file path, record count, and generation timestamp | Must |
| VR-074 | Stage 3 aggregate analysis SHALL break down fidelity and auditability by query category (from battery metadata) in addition to overall totals | Must |
| VR-075 | Stage 3 aggregate analysis SHALL be implemented in src/eval/fidelity_aggregate.py and configured via judge_config.yaml fidelity: section | Must |

**Rationale:** VR-057 and VR-058 encode the "skinny packet" design: sending full tool results (100K+ chars including pragmatics guidance) to the verification model produced empty or truncated responses, while sending slim data (~1.5K per tool call) produced reliable claim-level verification. This is not an optimization — it is a correctness requirement. The pragmatics guidance is not Census API ground truth and must not be presented as verification evidence.

**Location:** `src/eval/fidelity_check.py`, `src/eval/fidelity_prompts.py`, config in `src/eval/judge_config.yaml` `fidelity:` section, output in `results/v2_redo/stage3/`.

### 8.6 Aggregate Analysis

| ID | Requirement | Priority |
|----|------------|----------|
| VR-060 | Aggregate analysis SHALL compute Cohen's d effect sizes with 95% bootstrap confidence intervals (n=1000 iterations, seed=42) for each CQS dimension (D1-D5) and the composite (mean of D1-D5), for each pairwise comparison | Must |
| VR-061 | Aggregate analysis SHALL compute both independent-samples and paired Cohen's d. Paired d (computed on query-level means) SHALL be the primary metric for stratified analysis. Independent d is reported as a secondary conservative estimate | Must |
| VR-062 | Aggregate analysis SHALL compute Krippendorff's alpha (ordinal scale) across all judge vendors for each dimension as the inter-rater reliability metric | Must |
| VR-063 | Aggregate analysis SHALL test for position bias by comparing scores when presented as Response A vs Response B, per vendor per dimension. Differences exceeding 0.2 with p < 0.05 SHALL be flagged | Must |
| VR-064 | Aggregate analysis SHALL test for self-enhancement bias by comparing Anthropic's effect size delta against the average of other vendors' deltas. Differences exceeding 0.3 SHALL be flagged | Must |
| VR-065 | Aggregate analysis SHALL test for verbosity bias by computing Spearman's ρ between response character length and composite CQS score, separately for each condition | Must |
| VR-066 | Aggregate analysis SHALL compute test-retest reliability as Pearson r separately for each pass-pair (1,2), (3,4), (5,6) per vendor per dimension, and report the overall lumped r as a secondary metric | Must |
| VR-067 | Statistical tests on paired conditions (Wilcoxon signed-rank, using the Pratt method (`zero_method='pratt'`) for zero-difference handling) SHALL aggregate to the query level before testing to respect the experimental unit. The experimental unit is the query (n=39), not the judge record. All p-values SHALL be reported as exact two-tailed values | Must |
| VR-068 | Three-group omnibus analysis SHALL use Friedman test (repeated-measures) with query as the experimental unit, followed by Wilcoxon signed-rank post-hoc with Holm-Bonferroni correction (3 comparisons) | Must |
| VR-069 | Aggregate analysis SHALL stratify results by query category (normal vs edge cases) and report per-stratum effect sizes with bootstrap CIs | Must |
| VR-070 | Aggregate analysis SHALL compute judge preference rates (per pairwise comparison) per vendor and pooled, mapping the anonymized A/B preference back to condition labels | Must |
| VR-071 | Aggregate analysis SHALL output: CSV files for each analysis type, a markdown report with publication-ready tables, and a JSON archive of all computed statistics | Must |
| VR-072 | Aggregate analysis SHALL load only records matching valid run IDs from config. The script SHALL report total records loaded, per-vendor counts, and parse failure counts. If any vendor has fewer than expected records, it SHALL emit a warning | Must |
| VR-073 | Three-group analysis SHALL map A/B judge scores back to condition labels using `response_a_label` and `response_b_label` per record. The mapping SHALL NOT assume fixed position — counterbalancing alternates which condition appears as A vs B | Must |
| VR-074 | Query-level means SHALL be computed by averaging across all vendors and passes for each query before statistical testing. The experimental unit is the query (n=39), not the judge record. This aggregation step SHALL be verified by reporting the per-query mean for at least one query alongside its constituent records | Must |
| VR-075 | Three-group analysis output SHALL be spot-checked by computing query-level means for at least 3 queries (one normal, one geographic edge, one small-area edge) by hand from raw JSONL and comparing against the script's intermediate values. The raw D3 vectors (n=39) entering the Friedman test SHALL be dumped to CSV for manual inspection | Must |
| VR-090 | All aggregate analysis parameters (alpha level, bootstrap iterations, correction method, included dimensions, output paths) SHALL be loaded from the `analysis:` section of `judge_config.yaml`. No analysis parameters SHALL be hardcoded in scripts | Must |

**Rationale:** These requirements encode methodological decisions that were made iteratively during Phase 4B development. VR-061 addresses the paired vs independent d decision — the experimental design is paired (every query has all conditions), so paired d is the correct primary metric, but independent d provides a conservative lower bound. VR-067 was added after discovering that running Wilcoxon on non-independent records (multiple vendors × passes per query) produced meaningless p-values. VR-068 specifies the omnibus test for the three-group design with appropriate multiple comparison correction. VR-072 was added after the data contamination incident where stale judge scores inflated the apparent sample size.

**Location:** `src/eval/analyze_results.py`, `src/eval/analyze_three_group.py`, output in `results/v2_redo/analysis/`.

### 8.7 Data Provenance

| ID | Requirement | Priority |
|----|------------|----------|
| VR-076 | Each pipeline run SHALL generate a unique run_id (timestamp-based) embedded in every output record | Must |
| VR-077 | Stale or superseded pipeline outputs SHALL be archived to a versioned subdirectory (e.g., `results/archive_v1_confounded/`) with a README documenting why the data was superseded and what design flaw or bug invalidated it | Must |
| VR-078 | The active results directory SHALL contain only data from the current valid pipeline version. Aggregate analysis SHALL NOT glob indiscriminately across all available files | Must |

**Rationale:** The Phase 4B evaluation went through multiple pipeline versions (V1: confounded tool access, intermediate: truncation bugs, temporal confounds). At one point, aggregate analysis inadvertently loaded multiple versions' outputs simultaneously, contaminating every computed statistic. These requirements formalize the hard-won lesson that data provenance in iterative evaluation pipelines requires active management, not passive file accumulation.

**Location:** Config in `judge_config.yaml` (`stage2_valid_run_ids`), archive in `results/archive_v1_confounded/`.

**V2 Stage 2 production runs (valid run IDs):**
```
rag_vs_pragmatics_20260216_092144      (702/702 records)
control_vs_rag_20260217_083951         (702/702 records)
control_vs_pragmatics_20260218_065924  (699/702, 3 Google failures — pending backfill per TMP-003/TMP-004)
```

### 8.8 RAG Condition Specification

| ID | Requirement | Priority |
|----|------------|----------|
| VR-080 | The RAG condition SHALL use the same source documents from which pragmatics were extracted, chunked at section level with no retrieval optimization | Must |
| VR-081 | RAG source documents SHALL be provenance-traced to pragmatics citations. Only documents cited in `Context.provenance.sources[].document` in neo4j-pragmatics SHALL be included. Documents not cited by any pragmatic SHALL be excluded regardless of availability in the knowledge base | Must |
| VR-082 | RAG extraction SHALL use the same method as the quarry pipeline (Docling HierarchicalChunker). RAG and pragmatics conditions SHALL differ only in knowledge representation (raw chunks vs curated expert judgment), not in extraction methodology | Must |
| VR-083 | RAG condition SHALL receive identical evaluation treatment: same rubric, same 3 judge vendors, same 6-pass counterbalanced design, same fidelity verification methodology | Must |
| VR-084 | All RAG index artifacts SHALL be stored in `results/rag_ablation/index/` and version-controlled separately from runtime evaluation outputs | Must |

**Rationale:** The RAG condition addresses the anticipated critique that simple document retrieval could match curated expert judgment. This is a knowledge representation study comparing three forms: no methodology support (control), methodology via retrieved document chunks (RAG), and methodology via curated expert judgment delivered through a structured MCP tool (pragmatics). The "no optimization" requirement (VR-080) ensures a fair comparison — the RAG condition uses standard defaults (section-level chunking, top-5 retrieval, all-MiniLM-L6-v2 embeddings) rather than being tuned to compete with the pragmatics system. VR-081 was added after a provenance audit revealed that 3 of 6 documents in the initial RAG index were never cited by any pragmatic. VR-082 was added after discovering the initial RAG build used pypdf extraction while pragmatics used Docling, introducing an uncontrolled extraction quality variable.

**Location:** `scripts/build_rag_index.py`, `src/eval/rag_retriever.py`, index in `results/rag_ablation/index/`.

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
