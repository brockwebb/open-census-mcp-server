# Census MCP Server — Implementation Schedule

*Created: 2026-02-08*

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

Depends on: Nothing (but informs Phase 2)

### Track C: Pack Schema & Compiler
**Location:** `scripts/compile_pack.py`, `pragmatics/pack.py`

| Task | Description |
|------|-------------|
| C.1 | SQLite schema DDL (from vocabulary doc) |
| C.2 | JSON staging format validation |
| C.3 | compile_pack.py: JSON → SQLite |
| C.4 | Pack inheritance resolution |
| C.5 | compile_all.py: batch compilation |
| C.6 | pack.py: load .db at runtime |
| C.7 | Integration test: round-trip JSON→DB→query |

**Deliverable:** `python scripts/compile_pack.py staging/acs` → `packs/acs.db`

### Track D: Seed Content
**Location:** `staging/general_statistics/`, `staging/census/`, `staging/acs/`

| Task | Description |
|------|-------------|
| D.1 | 5-10 general statistics rules (MOE, CV thresholds) |
| D.2 | 5-10 Census-wide rules (vintage, geographic hierarchy) |
| D.3 | 10-20 ACS-specific rules (1yr vs 5yr, population thresholds) |
| D.4 | Thread edges between related rules |
| D.5 | Validate against schema |

**Deliverable:** Minimal but real pack content to test full pipeline.

---

## Phase 2: Pragmatics Engine

Depends on: Phase 1 (pack loading)

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

## Phase 3: MCP Integration

Depends on: Phase 0 (API client), Phase 2 (pragmatics)

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

## Phase 4: Evaluation & Hardening

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
Phase 0A (API Client) ──────────────────────────┐
                                                 ├──► Phase 3 (MCP) ──► Phase 4 (Eval)
Phase 0B (Geography) ───────────────────────────┤
                                                 │
Phase 1C (Pack Pipeline) ──► Phase 2 (Pragmatics)┘
         │
Phase 1D (Seed Content) ───┘
```

---

## Current Status

| Phase | Status |
|-------|--------|
| 0A: API Client | ✅ Complete (TEVV passed) |
| ~~0B: Geography~~ | ❌ Deleted (LLM handles, edge cases → packs) |
| 1C: Pack Pipeline | 🔄 In Progress |
| 1D: Seed Content | ⏳ Not Started |
| 2: Pragmatics | ⏳ Not Started |
| 3: MCP Integration | ⏳ Not Started |
| 4: Evaluation | ⏳ Not Started |

---

## Risk Items

| Risk | Mitigation |
|------|------------|
| Census API rate limits slow testing | Cache responses locally during dev |
| Geography disambiguation is hard | Start with unambiguous cases, iterate |
| Pack content takes longer than code | Timebox initial content, expand in Phase 4 |
| MCP protocol quirks | Test with simple tool first before pragmatics integration |
