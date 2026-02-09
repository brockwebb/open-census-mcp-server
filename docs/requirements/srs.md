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
| FR-PC-001 | System SHALL classify incoming queries by domain, geography type, variable category, and time period | Must |
| FR-PC-002 | System SHALL retrieve relevant pragmatic context based on query classification | Must |
| FR-PC-003 | System SHALL compile retrieved context into natural language and inject it into MCP tool descriptions | Must |
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

| ID | Requirement | Priority |
|----|------------|----------|
| QR-001 | System SHALL respond to single queries within 10 seconds (excluding Census API latency) | Should |
| QR-002 | Pack loading SHALL complete within 2 seconds at startup | Should |
| QR-003 | System SHALL log all Census API calls for debugging | Must |
| QR-004 | System SHALL be installable via `pip install` with no system dependencies beyond Python 3.11+ | Must |
| QR-005 | Compiled packs SHALL be under 10MB each | Should |

---

## 7. Constraints

| ID | Constraint |
|----|-----------|
| C-001 | Pure Python. No R, no compiled extensions requiring build tools. |
| C-002 | SQLite for pack storage. No external database servers at runtime. |
| C-003 | Census API is the sole data source for demographic data. No scraping. |
| C-004 | Pragmatic context is pre-compiled, not generated at query time. |
| C-005 | The term "crystal" SHALL NOT appear in any code, documentation, or file names. |

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
| VR-010 | Test battery SHALL weight 80% edge cases, 20% normal queries | Must |
| VR-011 | Test battery SHALL include geographic edge cases: independent cities (St. Louis MO, 38 Virginia independent cities), consolidated city-counties, NYC boroughs, DC as state-equivalent | Must |
| VR-012 | Test battery SHALL include small-area reliability cases: places under 65K, under 20K, tract-level requests | Must |
| VR-013 | Test battery SHALL include temporal edge cases: cross-vintage comparison, overlapping ACS periods, break-in-series years, inflation-unadjusted dollar comparisons | Must |
| VR-014 | Test battery SHALL include ambiguity cases: "Portland" (OR vs ME), "Springfield" (multiple states), "Washington" (state vs DC) | Must |
| VR-015 | Test battery SHALL include product-mismatch cases: 1-year request for small geography, decennial question sent to ACS | Should |
| VR-016 | Test battery SHOULD include persona-based query variants that test accessibility across user sophistication levels | Should |

**Rationale (VR-016):** The system's stated goal is accessibility — "any 8th grader with an active imagination." Testing with persona-based queries (curious student, small business planner, retiree exploring data, city planner, journalist on deadline) validates that pragmatics produce useful consultations across the full user spectrum, not just for statisticians. Persona development is a future requirement; the testbench must support it when ready.

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
