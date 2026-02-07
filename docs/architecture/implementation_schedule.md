# Census MCP Server — Implementation Schedule

*Created: 2026-02-08*
*Last Updated: 2026-02-07*

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

## Phase 2: Pragmatics Engine ⏳ NOT STARTED

Depends on: Phase 1 (pack loading) ✅

| Task | Location | Description |
|------|----------|-------------|
| E.1 | `router.py` | Query classification (domain, geo type, time) |
| E.2 | `router.py` | Trigger extraction from query text |
| E.3 | `retriever.py` | Context lookup by triggers |
| E.4 | `retriever.py` | Thread traversal (inheritance, relates_to) |
| E.5 | `retriever.py` | Latitude filtering |
| E.6 | `compiler.py` | Context items → natural language docstring |
| E.7 | `compiler.py` | Provenance citation formatting |
| E.8 | Integration test | query → compiled context |

**Deliverable:** `get_context("median income in small county")` → structured guidance text

---

## Phase 3: MCP Integration ⏳ NOT STARTED

Depends on: Phase 0A (API client) ✅, Phase 2 (pragmatics)

| Task | Location | Description |
|------|----------|-------------|
| F.1 | `tools/census_tools.py` | Tool schema definitions |
| F.2 | `tools/census_tools.py` | get_acs_data handler |
| F.3 | `tools/census_tools.py` | explore_variables handler |
| F.4 | `server.py` | MCP protocol setup (stdio) |
| F.5 | `server.py` | Dynamic tool description injection |
| F.6 | `server.py` | Pack loading at startup |
| F.7 | Manual test | Claude Desktop integration |

**Deliverable:** Working MCP server, installable and testable.

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
Phase 0A (API Client) ✅ ───────────────────────┐
                                                 ├──► Phase 3 (MCP) ──► Phase 4 (Eval)
Phase 1C (Pack Pipeline) ✅ ──► Phase 2 (Engine) ┘
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
| 2: Pragmatics Engine | ⏳ Not Started | — |
| 3: MCP Integration | ⏳ Not Started | — |
| 4: Evaluation | ⏳ Not Started | — |

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
