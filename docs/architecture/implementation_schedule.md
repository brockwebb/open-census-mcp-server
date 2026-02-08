# Census MCP Server — Implementation Schedule

*Created: 2026-02-08*
*Last Updated: 2026-02-08*

---

## Phase 0: Foundation

### Track A: Census API Client ✅ COMPLETE
**Location:** `src/census_mcp/api/census_client.py`

| Task | Description | Status |
|------|-------------|--------|
| A.1 | HTTP client skeleton (httpx) | ✅ |
| A.2 | ACS 5-year endpoint implementation | ✅ |
| A.3 | ACS 1-year endpoint implementation | ✅ |
| A.4 | API key handling | ✅ |
| A.5 | Rate limiting / retry logic | ✅ |
| A.6 | Error response parsing | ✅ |
| A.7 | Unit tests (13 passing) | ✅ |
| A.8 | Integration test (live API) | ✅ |

**TEVV:** Complete. 14/14 tests passing.

### ~~Track B: Geography Resolver~~ — DELETED

**Decision:** LLM handles geographic resolution. Edge cases (Virginia independent cities, NYC boroughs) go into pragmatics packs as context items. No separate resolver code.

**Rationale:** 90/10 rule. LLM gets 95%+ of geography right. Census API validates FIPS — wrong codes error. Edge cases are domain expertise = pragmatics, not code.

---

## Phase 1: Pack Pipeline

### Track C: Pack Schema & Compiler ✅ COMPLETE
**Location:** `src/census_mcp/pragmatics/`, `scripts/`

| Task | Description | Status |
|------|-------------|--------|
| C.1 | SQLite schema DDL (from vocabulary doc) | ✅ |
| C.2 | JSON staging format validation (Pydantic) | ✅ |
| C.3 | compile_pack.py: JSON → SQLite | ✅ |
| C.4 | Pack inheritance resolution | ✅ |
| C.5 | compile_all.py: batch compilation | ✅ |
| C.6 | pack.py: load .db at runtime | ✅ |
| C.7 | Integration test: round-trip JSON→DB→query | ✅ |

**TEVV:** Complete. 15/15 tests passing.

**Deliverables:**
- `scripts/compile_pack.py` - Single pack compiler
- `scripts/compile_all.py` - Batch compiler
- `src/census_mcp/pragmatics/schema.py` - SQLite DDL
- `src/census_mcp/pragmatics/models.py` - Pydantic validation
- `src/census_mcp/pragmatics/pack.py` - Runtime PackLoader

### Track D: Seed Content ✅ COMPLETE (Initial)
**Location:** `staging/`, `packs/`

| Task | Description | Status |
|------|-------------|--------|
| D.1 | General statistics rules | ✅ (3 items) |
| D.2 | Census-wide rules | ✅ (3 items) |
| D.3 | ACS-specific rules | ✅ (17 items) |
| D.4 | Thread edges between related rules | ✅ (6 threads) |
| D.5 | Validate against schema | ✅ |

**ACS Pack Details (17 contexts):**
- Population thresholds: 3 (65K rule, 20K supplemental, 5-year coverage)
- MOE/reliability: 3 (SE formula, CV threshold, precision comparison)
- Comparison rules: 3 (no 1yr/5yr mixing, overlapping periods, significance testing)
- Period estimates: 1 (labeling guidance)
- Dollar values: 1 (inflation adjustment)
- Geography: 4 (block groups, PUMAs, congressional districts, boundary dates)
- Breaks/discontinuities: 1 (2009-2010 population controls)
- Suppression: 1 (data availability)

**Latitude Distribution:**
- `none`: 5 (hard constraints)
- `narrow`: 7 (strong guidance)
- `wide`: 4 (context-dependent)
- `full`: 1 (background info)

**Source:** ACS-GEN-001 (Understanding and Using ACS Data handbook, 2020)

---

## Phase 2: Pragmatics Retriever ✅ COMPLETE (Revised)

Depends on: Phase 1 (pack loading) ✅

**Architecture Revision per ADR-003/004:** LLM caller handles routing and interpretation. MCP provides structured data retrieval only.

| Task | Location | Description | Status |
|------|----------|-------------|--------|
| ~~E.1~~ | ~~`router.py`~~ | ~~Query classification~~ | ❌ Deleted (LLM does routing) |
| ~~E.2~~ | ~~`router.py`~~ | ~~Trigger extraction~~ | ❌ Deleted (LLM does extraction) |
| E.3 | `retriever.py` | Context lookup by topics (tag match) | ✅ |
| E.4 | `retriever.py` | Thread traversal for related contexts | ✅ |
| E.5 | `retriever.py` | Parameter-based trigger mapping | ✅ |
| ~~E.6~~ | ~~`compiler.py`~~ | ~~Natural language formatting~~ | ❌ Deleted (LLM does formatting) |
| ~~E.7~~ | ~~`compiler.py`~~ | ~~Citation formatting~~ | ❌ Deleted (return raw citations) |
| E.8 | Unit tests | Retriever logic tested | ✅ (9/9) |

**Deliverables:**
- `src/census_mcp/pragmatics/retriever.py` - PragmaticsRetriever with two methods:
  - `get_guidance_by_topics(topics, domain)` - Tag-based lookup
  - `get_guidance_by_parameters(product, geo_level, variables, year)` - Auto-bundling for data responses
- Unit tests: 9/9 passing

**TEVV:** Complete. Returns structured guidance dict with `{guidance, related, sources}` fields.

---

## Phase 3: MCP Server & Tools ✅ COMPLETE

Depends on: Phase 0A (API client) ✅, Phase 2 (retriever) ✅

**Primary Artifact:** `docs/design/agent_prompt.md` defines agent behavior, tool schemas, and workflow.

| Task | Location | Description | Status |
|------|----------|-------------|--------|
| F.1 | `tools/census_tools.py` | get_methodology_guidance tool | ✅ |
| F.2 | `tools/census_tools.py` | get_acs_data handler (data + pragmatics) | ✅ |
| F.3 | `tools/census_tools.py` | explore_variables handler | ✅ |
| F.4 | `server.py` | FastMCP server setup (stdio transport) | ✅ |
| F.5 | `server.py` | System prompt from agent_prompt.md | ✅ |
| F.6 | `server.py` | Pack loading (lazy initialization) | ✅ |
| F.7 | Integration tests | Tool handlers tested with mocked context | ✅ (6/6) |
| F.8 | `pyproject.toml` | MCP dependency, entry point | ✅ |

**Deliverables:**
- `src/census_mcp/server.py` - FastMCP server with lifespan management
- `src/census_mcp/tools/census_tools.py` - Three tool handlers implementing agent_prompt.md schemas
- Integration tests: 6/6 passing
- Entry point: `census-mcp` CLI command

**TEVV:** Complete. Server starts, loads packs, tools respond with proper structure. Ready for manual Claude Desktop integration test.

**Implementation Notes:**
- Used FastMCP (mcp.server.fastmcp) instead of deprecated MCPServer pattern
- Tools access ServerContext via get_server_context() (lazy init)
- Hard stops implemented (e.g., tract + acs1 raises CensusInvalidQueryError)
- Pragmatics auto-bundled with every get_acs_data response

---

## Phase 4: Evaluation & Hardening ⏳ NOT STARTED

Depends on: Phase 3

| Task | Location | Description |
|------|----------|-------------|
| G.1 | `tests/evaluation/` | CQS test harness skeleton |
| G.2 | `tests/evaluation/` | 20 curated test queries |
| G.3 | `tests/evaluation/` | Expert judgment baseline |
| G.4 | `docs/verification/` | Evaluation results documentation |
| G.5 | — | Bug fixes from evaluation |
| G.6 | — | Pack content expansion based on failures |

**Deliverable:** Documented evaluation with CQS scores.

---

## Dependency Graph

```
Phase 0A (API Client) ✅ ────────────────────────┐
                                                  ├──► Phase 3 (MCP) ✅ ──► Phase 4 (Eval)
Phase 1C (Pack Pipeline) ✅ ──► Phase 2 (Retriever) ✅ ┘
         │
Phase 1D (Seed Content) ✅ ────┘
```

---

## Current Status

| Phase | Status | Tests |
|-------|--------|-------|
| 0A: API Client | ✅ Complete | 14/14 |
| ~~0B: Geography~~ | ❌ Deleted | — |
| 1C: Pack Pipeline | ✅ Complete | 15/15 |
| 1D: Seed Content | ✅ Complete (initial) | — |
| 2: Retriever | ✅ Complete (revised) | 9/9 |
| 3: MCP Server | ✅ Complete | 6/6 |
| 4: Evaluation | ⏳ Not Started | — |

**Total Tests:** 44/44 (1 pre-existing failure in pack_roundtrip unrelated to new work)

---

## Infrastructure & CI

| Component | Status |
|-----------|--------|
| GitHub Actions CI | ✅ `.github/workflows/ci.yml` |
| Unit tests | ✅ pytest |
| Pack compilation | ✅ In CI pipeline |
| Ruff linting | ✅ Separate job |

---

## Documentation Added

| Document | Purpose |
|----------|---------|
| `docs/references/CATALOG.md` | Source document registry with provenance |
| `docs/references/theory/semiotic_dq_foundations.md` | Theoretical foundation citations |
| `docs/architecture/knowledge_pack_management.md` | Authoring vs runtime separation |
| `docs/design/pragmatics_vocabulary.md` | Canonical terms + theoretical foundation |

---

## Tech Debt / Future Work

| Item | Priority | Notes |
|------|----------|-------|
| Automated extraction from PDFs | Medium | Manual extraction doesn't scale |
| Bulk Neo4j loader script | Medium | Currently loading via MCP manually |
| Neo4j → JSON export script | Medium | Round-trip automation |
| CPS pack | Low | Needed for user's other project |
| Additional ACS docs extraction | Low | Researchers handbook, PUMS handbook |

---

## Risk Items

| Risk | Mitigation | Status |
|------|------------|--------|
| Census API rate limits | Cache responses locally | Mitigated |
| Geography disambiguation | LLM handles + edge cases in packs | Resolved |
| Pack content takes longer than code | Timebox initial content | Initial content done |
| MCP protocol quirks | Test with simple tool first | Not yet started |
