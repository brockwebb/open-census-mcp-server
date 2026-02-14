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
| D.6 | ACS General Handbook deep extraction (7 non-obvious findings) — author with provenance | ✅ | ACS-GEN-001 |

**ACS Pack Details (35 contexts):**
- Population thresholds: 5 (65K rule, 20K supplemental, 5-year coverage, tract/BG controls, independent cities)
- MOE/reliability: 4 (SE formula, CV threshold, precision comparison, covariance bias)
- Comparison rules: 4 (no 1yr/5yr mixing, overlapping periods, significance testing, 4/5 smoothing, CI anti-pattern)
- Period estimates: 1 (labeling guidance)
- Dollar values: 1 (inflation adjustment, CPI-U-RS limitation)
- Geography: 5 (block groups, PUMAs, congressional districts, boundary dates, independent cities)
- Breaks/discontinuities: 3 (2009-2010 population controls)
- Suppression: 1 (data availability)
- Disclosure: 3 (swapping, perturbation, thresholds)
- Equivalence: 2 (geographic, temporal)
- Group quarters: 2 (inclusion, imputation)
- Nonresponse: 2 (allocation rates, hot-deck)
- Residence rules: 1 (current vs usual)
- Sampling: 1 (non-uniform rates)
- Independent cities: 1 (county-equivalent)

**Latitude Distribution:**
- `none`: 5 (hard constraints)
- `narrow`: 7 (strong guidance)
- `wide`: 4 (context-dependent)
- `full`: 1 (background info)

**Source:** ACS-GEN-001 (Understanding and Using ACS Data handbook, 2020)

**D.6 Complete:** 7 non-obvious findings from ACS handbook authored with page-level provenance (2026-02-11). New categories: population_controls, residence_rules, sampling. Strengthened: comparison (CMP-002, CMP-003), dollar_values (DOL-001), margin_of_error (MOE-004).

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
| F.1 | `server.py` | get_methodology_guidance tool | ✅ |
| F.2 | `server.py` | get_census_data handler (data + pragmatics) | ✅ (renamed from get_acs_data, G.6) |
| F.3 | `server.py` | explore_variables handler | ✅ |
| F.4 | `server.py` | Low-level Server + stdio (ADR-005) | ✅ (rewrote from FastMCP) |
| F.5 | `agent_prompt.md` | Agent prompt (slimmed G.6) | ✅ |
| F.6 | `server.py` | Pack loading (lazy initialization) | ✅ |
| F.7 | Integration tests | 10 tests: tools + tract fixes + legacy compat | ✅ (10/10) |
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

## Phase 4A: Manual Validation ✅ COMPLETE

Depends on: Phase 3 ✅

*Objective: Prove the system works end-to-end before investing in automated evaluation.*

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| G.1 | Fix PACKS_DIR: `server.py` reads from `os.environ.get("PACKS_DIR", "packs")` | ✅ | Blocks all testing |
| G.2 | Restart Claude Desktop, verify MCP connection healthy | ✅ | VR-002 |
| G.3 | Test: "What's the median income in Mercer, PA?" (MCP tools live) | ✅ | VR-012 |
| G.4 | Test: Owsley County, KY poverty — three-model comparison (Sonnet 4, 4.5, Opus 4.6) | ✅ | VR-012 |
| G.5 | SRS reconciliation: update FR-PC-001, FR-PC-003 to align with ADR-003/004 | ✅ | ADR-003, ADR-004 |
| G.6 | Prompt slimming: removed domain rules, renamed tool, FSS-general language | ✅ | Decision log (prompt specificity) |
| G.7 | Add independent cities pack content (ACS-IND-001/002/003) | ✅ | VR-011 |
| G.8 | Document results of manual tests in `docs/verification/` | ✅ (partial) | — |
| G.9 | **BUG FIX:** `get_census_data` tract parameter — add wildcard support + county validation (ADR-006) | ✅ | G.4 finding |
| G.10 | **PACK:** Disclosure avoidance (ACS-DIS-001/002/003) | ✅ | G.4 finding |
| G.11 | **PACK:** Population thresholds (ACS-THR-001/002) + geographic equivalence (ACS-EQV-001/002) | ✅ | G.4 finding |

**Exit Criteria:** ✅ Met. System produces pragmatics-grounded responses for test queries. Tract-level geography works. SRS reflects actual architecture. Agent prompt slim (no domain overfitting).

---

## Phase 4B: Systematic Evaluation ⏳ IN PROGRESS

Depends on: Phase 4A ✅

*Objective: Empirical evaluation for FCSM talk. Does pragmatics improve statistical consultation quality?*

### Experimental Design
- **Treatment:** Claude + MCP (live tools, live pragmatics, full agent loop)
- **Control:** Claude alone (same query, no tools, no pragmatics)
- **Scoring:** CQS rubric applied to paired responses by LLM judge panel + human expert calibration
- **Judge panel:** Gemini, OpenAI, Claude (3-model panel for inter-rater reliability, bias mitigation)
- **Human calibration:** Expert-scored subset (10-15 queries) to anchor automated scoring validity

### Build Order

**Step 1: CQS Rubric Definition**

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| H.1 | Define CQS scoring dimensions and scale | ✅ | VR-006 |
| H.2 | Draft scoring prompt template for LLM judge panel | ✅ | VR-006 |
| H.3 | Validate rubric against manually scored examples | ✅ | Manual calibration packet |

**Step 2: Test Query Battery**

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| H.4 | Data-driven test definitions (YAML/JSON, no code changes to add queries) | ✅ | VR-007 |
| H.5 | Test battery: 41% normal / 59% edge case weighting (power-based) | ✅ | DEC-4B-009 |
| H.6 | Geographic edge cases (independent cities, NYC boroughs, DC, consolidated city-counties) | ✅ | GEO-001 through GEO-006 |
| H.7 | Small-area reliability cases (<65K, <20K, tract-level) | ✅ | SML-001 through SML-004 |
| H.8 | Temporal edge cases (cross-vintage, overlapping periods, breaks, inflation) | ✅ | TMP-001 through TMP-004 |
| H.9 | Ambiguity cases (Portland, Springfield, Washington) | ✅ | AMB-001 through AMB-003 |
| H.10 | Product-mismatch cases (1-year for small geo, decennial→ACS) | ✅ | MIS-001 through MIS-003 |
| H.11 | Persona-based query variants (8th grader, city planner, journalist) | ✅ | PER-001a through PER-001c |

**Step 3: Test Harness**

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| H.12 | MCP client: programmatic subprocess launch + stdio JSON-RPC connection | ✅ | VR-001 |
| H.13 | Health check: verify MCP connection before test run | ✅ | VR-002 |
| H.14 | Agent loop: Claude API tool_use → MCP tool execution → tool_result → final response | ✅ | VR-001 |
| H.15 | Control path: Claude API same query, no tools, no system prompt augmentation | ✅ | VR-001 |
| H.16 | Structured result recording (query, condition, model, response, tool calls, pragmatics returned, latency) | ✅ | VR-005 |
| H.17 | Output format: JSON lines for scoring pipeline | ✅ | VR-006 |

**Step 4: Judge Prompt & Scoring Pipeline**

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| H.18 | Scoring prompt: domain-specific rubric for LLM judges (Gemini, OpenAI, Claude) | ✅ | VR-006 |
| H.19 | Judge harness: send paired responses to 3 models, collect dimension scores | ✅ | VR-003, VR-004 |
| H.20 | Inter-rater agreement calculation (Krippendorff's α or Fleiss' κ) | ⏳ | Aggregate analysis pending |
| H.21 | Human calibration set: expert-scored subset | ⏳ | Manual scoring packet created |

**Step 5: Run & Analyze**

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| H.22 | Execute full battery: control + treatment for all queries | ✅ | Stage 1 v3 complete |
| H.23 | Execute judge panel scoring on all paired results | ⏳ | OpenAI ✅, Anthropic + Google pending |
| H.24 | Aggregate results: CQS by dimension, treatment effect, agreement stats | ⏳ | Pending all vendors |
| H.25 | Bug fixes and pack content expansion from evaluation failures | ✅ | Truncation + temporal + dataset mapping |
| H.26 | Results documentation in `docs/verification/` | ⏳ | — |

**Step 6: Pipeline Fidelity (Stage 3)**

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| H.27 | Design automated fidelity metric (DEC-4B-023) | ✅ | D6 revision |
| H.28 | Build fidelity extraction pipeline (`src/eval/fidelity_check.py`) | ✅ | VR pipeline |
| H.29 | Run fidelity verification on all Stage 1 data | ✅ | H.22 |
| H.30 | Symmetric auditability measurement (both conditions) | ✅ | Experimental design |
| H.31 | Integrate fidelity results into aggregate analysis | ⏳ | H.24 |

**Exit Criteria:** Documented CQS scores for Claude with vs without pragmatics. LLM judge panel + human calibration. Results in `docs/verification/`.

**Deliverable:** Empirical evaluation suitable for FCSM talk.

---

## Dependency Graph

```
Phase 0A (API Client) ✅ ────────────────────────┐
                                                  ├─► Phase 3 (MCP) ✅ ─► Phase 4A (Manual) ─► Phase 4B (Eval)
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
| 1D: Seed Content | ✅ Complete | — |
| 2: Retriever | ✅ Complete | 9/9 |
| 3: MCP Server | ✅ Complete | 10/10 |
| 4A: Manual Validation | ✅ Complete | — |
| 4B: Systematic Evaluation | ⏳ Stage 2-3 in progress | — |

**Total Tests:** 47/47 (all passing)

**Last Updated:** 2026-02-13

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

## Architecture Decision Records

| ADR | Title | Status |
|-----|-------|--------|
| ADR-003 | Reasoning Model Requirement | Accepted |
| ADR-004 | Agent Reasoning Loop (ReAct + OODA + Cynefin) | Accepted |
| ADR-005 | Low-level Server Pattern (FastMCP bypass) | Accepted |
| ADR-006 | Tract-Level Geography Bug Fixes | Accepted |
| ADR-007 | KG-First Authoring Workflow | Accepted |
| ADR-008 | Custom Extraction Pipeline over llm-graph-builder | Accepted |
| ADR-009 | Quarry Toolkit as Shippable Project Component | Accepted |
| — | Prompt Specificity Concern | ✅ Resolved (G.6) |

---

## Open Items (Post Phase 3)

| Item | Priority | Notes |
|------|----------|-------|
| `server.py` reads PACKS_DIR from env | **Immediate** | Hardcoded `"packs"` relative path fails when Claude Desktop launches from arbitrary CWD. Must read `os.environ.get("PACKS_DIR", "packs")`. Blocks manual testing. |
| Claude Desktop integration test | **Immediate** | Config updated (2026-02-08). Restart Desktop, test "What's the median income in Mercer, PA?" |
| SRS reconciliation with ADR-003/004 | High | FR-PC-001 (system classifies queries) and FR-PC-003 (inject into tool descriptions) contradict ADRs. Update FRs. |
| ~~Slim agent prompt "Never" list~~ | ~~Medium~~ | ✅ Done (G.6). 280→55 lines. Tool renamed `get_census_data`. |
| API testbench (multi-model CQS) | Medium | CLI harness to run test queries against Claude/GPT/Gemini via API. Validates pragmatics work regardless of reasoning model (ADR-003). |

---

## Phase 4A.5: Pipeline Repair & Schema Migration ⏳ IN PROGRESS

Discovered 2026-02-08: Round-trip scripts were never built. Neo4j nodes use stale schema.
See `docs/lessons_learned/session_2026-02-08_pipeline_gap.md` for root cause.

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| P.1 | Create `scripts/neo4j_to_staging.py` (export) | ✅ | FR-EP-001 |
| P.2 | Create `scripts/staging_to_neo4j.py` (import) | ✅ | FR-EP-002 |
| P.3 | Add FR-EP-001–009 to SRS § 3.5 | ✅ | SRS |
| P.4 | Document pipeline gap in lessons learned | ✅ | — |
| P.5 | Update CLAUDE.md with Neo4j details + script refs | ✅ | — |
| P.6 | Migrate Neo4j nodes in-place: `tags`→`triggers`, add `category`, restructure `source` | ✅ | FR-EP-004 |
| P.7 | Run `neo4j_to_staging.py` to generate canonical staging JSON | ✅ (manual) | FR-EP-001, FR-EP-003 |
| P.8 | Remove old `staging/acs.json` (replaced by `staging/acs/*.json` per-category files) | ✅ | FR-EP-003 |
| P.9 | Run `compile_all.py` to rebuild packs from new staging | ✅ | — |
| P.10 | Validate: run tests, confirm pack round-trip | ✅ | — |
| P.11 | Author G.10/G.11/G.7 content in Neo4j using canonical schema (10 new nodes, 10 new edges) | ✅ | G.10, G.11, G.7 |
| P.12 | Run full pipeline: Neo4j → staging → compile → test | ✅ | End-to-end |
| P.13 | Provenance schema migration: models.py, staging JSON, Neo4j scripts, CLAUDE.md, tests | ✅ | ADR (provenance) |

**Exit Criteria:** Full round-trip works. All staging JSON matches Pydantic model. No stale formats.

---

## Phase 5: Knowledge Graph Extraction Pipeline ⏳ DESIGN COMPLETE

**Schema:** `docs/design/raw_kg_schema.md` v3.1 — reviewed by 4 AI models across 5 rounds.
**Architecture:** 4-layer harvest (seed → extract → harvest → curate → export)
**ADR:** ADR-007 (KG-first authoring)

| Task | Description | Status |
|------|-------------|--------|
| KG.1 | Raw KG schema design (13 node types, 16 relationships) | ✅ v3.1 |
| KG.2 | Multi-model adversarial review (5 rounds, 4 models) | ✅ |
| KG.3 | Bug fixes from structural review (8 fixes) | ✅ |
| KG.4 | Design narrative / explainer document | ⏳ (CC task pending) |
| KG.5 | Setup llm-graph-builder (neo4j-labs) | ✅ Done — then abandoned (ADR-008) |
| KG.6 | Seed Layer 0: AnalysisTask + REQUIRES edges | ✅ (5 tasks, 5 REQUIRES) |
| KG.7 | Seed Layer 0: CanonicalConcept, DataProduct, SurveyProcess nodes | ✅ (6 concepts, 4 products, 6 processes) |
| KG.8 | First extraction: CPS Handbook of Methods (22 pages) | ✅ (291 nodes, 349 rels) |
| KG.9 | Post-extraction enrichment: PRODUCES edge generation | ✅ (93→89 with PRODUCES, 9 dimensions) |
| KG.10 | First harvest: violation detection queries | ✅ (8 threshold results, 20 interactions) |
| KG.11 | Harvest quality assessment | ✅ (1 genuine finding, 7 false positives — see ADR-008) |
| KG.12 | **DECISION:** Replace llm-graph-builder with custom pipeline | ✅ ADR-008, ADR-009 |
| KG.13 | CPS-ACS income pack (15-30 context items) | ⏳ Blocked on pipeline rebuild |

---

## Phase 5B: Quarry Extraction Toolkit ✅ COMPLETE

**ADRs:** ADR-008 (custom pipeline), ADR-009 (shippable toolkit)
**Location:** `scripts/quarry/`
**Design spec:** `docs/design/quarry_extraction_pipeline.md`
**Depends on:** Phase 5 (schema + Layer 0 seed in quarry DB)
**Built:** 2026-02-09 (Claude Code session — 15 files, ~1,690 lines, 4 bugs fixed)

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| QT.1 | `config.py` — shared configuration (Neo4j creds, API keys, paths, schema version) | ✅ | ADR-009 |
| QT.2 | `seed.py` — Layer 0 setup (idempotent MERGE, --dry-run) | ✅ | KG.6, KG.7 |
| QT.3 | `chunk.py` — Docling section-aware PDF chunker (22pg → 157 chunks) | ✅ | ADR-008 |
| QT.4 | `extract.py` — PDF → LLM extraction → Neo4j write (MERGE, entity resolution) | ✅ | ADR-008 |
| QT.5 | `prompts.py` — Extraction prompt with controlled vocabulary enforcement | ✅ | KG.9 |
| QT.6 | Entity resolution at write time (MERGE on canonical names) — built into extract.py | ✅ | ADR-008 |
| QT.7 | `harvest.py` — Layer 2 queries with value_type filtering (fixes false positives) | ✅ | KG.10, KG.11 |
| QT.8 | `export.py` — stub only (blocked on harvest curation design) | ⏳ stub | ADR-007 |
| QT.9 | `schema.json` — machine-readable v3.1 schema definition | ✅ | ADR-009 |
| QT.10 | `README.md` — setup, usage, extending to new surveys | ✅ | ADR-009 |
| QT.11 | Test: CPS Handbook re-extraction with new pipeline, compare quality vs llm-graph-builder | ✅ | TEVV |
| QT.12 | Test: CPS Technical Paper 77 (1,531 chunks) — scalability test | ✅ | TEVV |
| QT.13 | Test: ACS General Handbook — cross-survey queries light up | ✅ | KG.13 |

**Verification passed:** Chunking (157 chunks, section-aware ✓), seed dry-run (valid Cypher ✓), extraction dry-run (prompts generated ✓)

**Results:** 5 documents extracted, 13,227 nodes, 15,355 valid edges. 100% schema compliance after cleanup.
Batch mode (--batch-size N) reduces cost ~50% for large documents. ~$55 total extraction cost.
Sonnet is minimum viable model (Haiku failed at 25.7% error rate).
~12% confabulated node types, 60% recoverable via reclassification.

**Exit Criteria:** ✅ Met. Pipeline extracts PDFs, harvest produces candidates, quality exceeds llm-graph-builder baseline.

---

## Phase 5C: Harvest Curation & Export ⏳ NOT STARTED

Depends on: Phase 5B ✅

*Objective: Turn quarry raw material into packaged pragmatics for the MCP runtime.*

| Task | Description | Status | Traces To |
|------|-------------|--------|----------|
| HC.1 | Finish relationship cleanup (delete 556 long-tail invalid edges) | ⏳ CC task ready | QT cleanup |
| HC.2 | Run clean harvest, document baseline signal quality | ⏳ | KG.10 |
| HC.3 | Build export.py (harvest → staging JSON template generation) | ⏳ | ADR-007 |
| HC.4 | Curate temporal comparability batch (~34 candidates → ~15 items) | ⏳ | D.6 |
| HC.5 | Curate threshold violations batch (~10 candidates → ~5 items) | ⏳ | D.6 |
| HC.6 | Compile new packs, test with MCP server | ⏳ | Phase 3 |
| HC.7 | Feed results into Phase 4B evaluation | ⏳ | H.1 |

**Exit Criteria:** ≥15 new pragmatics items curated from quarry harvest with full provenance, compiled into packs, tested via MCP.

---

## Tech Debt / Future Work

| Item | Priority | Notes |
|------|----------|-------|
| Source-grounded authoring for all existing content | High | Existing 25 ACS items cite ACS-GEN-001 but were authored from LLM training data, not source docs. Need re-verification against handbook. |
| CPS pack (manual) | Medium | Can be authored manually while KG pipeline matures |
| Additional ACS docs extraction | Low | Researchers handbook, PUMS handbook |

---

## Risk Items

| Risk | Mitigation | Status |
|------|------------|--------|
| Census API rate limits | Cache responses locally | Mitigated |
| Geography disambiguation | LLM handles + edge cases in packs | Resolved |
| Pack content takes longer than code | Timebox initial content | Initial content done |
| MCP protocol quirks | Test with simple tool first | Not yet started |
| Context7 shows unreleased APIs | Always verify against `pip index versions` before assuming API exists | Learned 2026-02-08 |
| Agent prompt overfits domain rules | Slim "Never" list, remove survey-specific language | ✅ Resolved (G.6) |
