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
│   └── extract/                   # Extraction pipeline scripts
│
├── tests/                         # All tests
│   ├── unit/                      # Unit tests (pytest)
│   ├── integration/               # Integration tests
│   └── evaluation/                # CQS evaluation harness
│
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
| Extraction pipeline scripts | `scripts/extract/` | No |
| Systems engineering docs | `docs/` (appropriate subdir) | No |
| ADRs | `docs/decisions/` | No |
| Test code | `tests/` (appropriate subdir) | No |
| Evaluation results | `docs/verification/` | No |
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
