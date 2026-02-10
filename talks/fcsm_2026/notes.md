# FCSM 2026 Talk Notes

*Working notes for presentation development. Strategic/private notes maintained separately.*

## Key Themes

### The Semiotic Gap
Federal AI-ready data guidance addresses syntax (formats, APIs) and semantics (metadata, labels).
Implementation reveals a missing third layer: pragmatics — the expert judgment about fitness-for-use.

### The Semantic Layer Already Exists  
Large language models encode distributional semantics from training. The relational structure that 
formal ontology frameworks attempt to hand-build is already present in model weights. This suggests 
the productive direction is not rebuilding the semantic layer but supplying the pragmatic layer the 
model cannot learn from training data alone.

### Retrieval ≠ Understanding
A system that returns the correct number from the correct source has demonstrated retrieval accuracy.
It has not demonstrated understanding of fitness-for-use. The evaluation gap lies between "got the 
right answer" and "did what an expert would do."

## Open Questions
- How to precisely characterize what model weights encode vs. what formal ontologies provide
- Evaluation framework for pragmatic consultation quality (beyond retrieval accuracy)
- Scalability of expert-authored pragmatic content

## References
- Morris, C. W. (1938). Foundations of the Theory of Signs. University of Chicago Press.
- Census Bureau ACS documentation (census.gov)
- Xu, Y., Zhao, S., Song, J., Stewart, R., & Ermon, S. (2020). A Theory of Usable Information Under Computational Constraints. ICLR 2020. arXiv:2002.10689

---

## 2026-02-08 — Key Insight: Always-Ground Beats Sometimes-Ground

Discovered during Phase 2-3 implementation: the LLM cannot reliably assess its own confidence about domain knowledge. The pragmatics-always-accompany-data pattern (ADR-004) means one extra tool call per query is cheap insurance against confident wrongness from stale training data. This is the strongest empirical argument for the pragmatics layer — you can't trust the model to know when it doesn't know.

This directly supports the talk thesis: the semantic layer is in the weights, but the model can't distinguish "I learned this correctly in training" from "I'm confabulating plausible-sounding guidance." Pragmatics packs are the external ground truth that closes this gap.

**See also:** `reference_fcsm_ai_ready_data_landscape.md` added today — polished write-up of the practitioner's thesis, the trajectory from 2006 ML paradigm through transformers to pragmatics, and the philosophical honesty about error minimization vs. elimination.

---

## 2026-02-08 — V-Information as Formal Basis for Pragmatics Layer

Xu et al. (2020) "A Theory of Usable Information Under Computational Constraints" (ICLR 2020) provides formal grounding for three claims in this project:

1. **Always-ground is formally justified.** An LLM is a bounded observer (predictive family V). Its V-information about Census fitness-for-use from training data alone is strictly lower than when augmented with pragmatics packs. Pragmatics packs *create usable information* through preprocessing — exactly the mechanism in Section 3.2 that violates the data processing inequality. The DPI says you can't create information by computing on data; V-information says you can create *usable* information by computing on data for a bounded observer. That's what we do.

2. **Extraction is inherently lossy, and that's fine.** The asymmetry property (Section 3.3): IV(expert_knowledge → pack_thread) ≠ IV(pack_thread → expert_knowledge). We distill signal in one direction without preserving full reconstructability. We're not trying to reconstruct the expert — we're trying to ground the model.

3. **Misspecification robustness supports pragmatics-over-ontology.** Even when V is misspecified relative to the true distribution, V-information still outperforms MI estimators for structure learning (Section 6.1). You don't need a perfect knowledge representation — just one that's usable by the observer class you care about (reasoning LLMs). This is why structured pragmatics with latitude beats formal ontology.

**Not relevant:** V-information doesn't prescribe extraction methodology or support ensemble extraction strategies. It's about measurement of usable information, not about how to create the grounding content. Also not a quantum mechanics analog despite superficial resemblance to observer-dependent measurement.

---

## 2026-02-08: Phase 4A Manual Validation — Three-Model Empirical Comparison

First live test of Census MCP with pragmatics packs against the Owsley County, KY poverty query across three model tiers. All models used the same MCP tools, same pragmatics packs, no extended thinking.

**Query:** "What's the poverty rate in a small rural tract in Owsley County, Kentucky?"

### Opus 4.6
- Called `get_methodology_guidance` first (packs fired)
- Recognized tract wildcard didn't resolve, made ONE clean pivot to web search
- Identified that the tract essentially IS the county (~4,400 people)
- "County-level reliability dressed up as tract-level data" — genuine statistical insight
- "That margin of error will eat your signal alive" — consultant-grade language
- Computed CV = 14.5%, correctly classified as reasonable but misleading given geography
- No vintage mixing, no contradictory numbers

### Sonnet 4.5
- Called `get_methodology_guidance` (packs fired)
- `get_acs_data` with tract parameter returned county data — same tool bug
- Fell back to web search, then raw `curl` when pushed to use tools
- **Mixed vintages** (2019-2023 from web, 2018-2022 from API) without flagging
- Reported 24.6% then 33.3% for same tract, different years, no acknowledgment of discrepancy
- Confidently wrong — characteristic Sonnet 4.5 failure mode

### Sonnet 4
- Called `get_methodology_guidance` (packs fired)
- Made 8+ flailing tool calls trying to resolve tract geography
- Couldn't find tract FIPS codes, claimed Owsley has "one census tract" (wrong: two)
- Eventually gave up and provided county-level data
- DID correctly apply CV formula from pragmatics packs

### Key Findings

**1. Pragmatics packs grounded all three models.** Every model called `get_methodology_guidance`, used CV = SE/estimate × 100 from ACS-MOE-002, and referenced the 40% threshold. The packs work as designed.

**2. Model tier determines recovery from tool failures.** When `get_acs_data` couldn't handle tract enumeration, Opus recovered in one step, Sonnet 4.5 compensated but introduced errors, Sonnet 4 flailed. This empirically validates ADR-003's Jobs Doctrine — minimum reasoning capability is not optional.

**3. The MCP has a tract-level bug.** `get_acs_data` doesn't support tract enumeration (`tract:*`) and silently returns county data when tract codes don't resolve. Missing capability: `list_geographies` or wildcard support.

**4. Missing pragmatics content identified:**
- No proactive warning about population thresholds for tract-level analysis
- No disclosure avoidance / privacy suppression guidance (small cells)
- No "tract effectively equals county" pattern recognition
- Tool description doesn't state county is required for tract queries

**5. The 90/10 thesis holds.** LLM training data carries 90% of statistical reasoning. The packs ensure consistency and auditability. The gap is in tool capability (geography resolution) and edge-case pragmatics — exactly the 10% that needs 90% of the engineering effort.

**FCSM talk implication:** The comparison across model tiers with identical infrastructure is the empirical story. "Same packs, same tools, different reasoning" is a concrete demonstration of why ADR-003 matters.

## 2026-02-08: ADR-005 Blast Radius — Integration Test Breakage

When ADR-005 rewrote `server.py` from FastMCP to low-level pattern, the integration tests in `tests/integration/test_mcp_server.py` were not updated. They imported `ServerContext` and `get_server_context` — constructs that no longer exist. Tests failed with `ImportError` on first run after bug fixes.

**Root cause:** ADR-005 changed the public interface of `server.py` but the blast radius wasn't traced. The tests were a downstream dependency that nobody checked.

**Fix:** Rewrote tests to match low-level pattern:
- Removed `ServerContext` / `get_server_context` imports
- Tests now patch module globals (`_loader`, `_retriever`, `_census_client`) directly
- Tool calls go through the real `call_tool_handler` dispatcher
- Added `_call_tool()` helper for clean JSON round-trip
- Added new tests for ADR-006 fixes (tract+county, tract-without-county, wildcard)

**Changes:**
- Old: 6 tests, 2 import FastMCP constructs, call `census_tools.*` directly
- New: 8 tests, patch module globals, call through dispatcher
- Net new tests: `test_get_acs_data_tract_requires_county`, `test_get_acs_data_tract_with_county_works`, `test_get_acs_data_tract_wildcard`

**Trace system lesson:** This is exactly the kind of dependency the trace MCP should catch. If `server.py` had been registered as an artifact with `tests/integration/test_mcp_server.py` as a downstream `verifies` dependency, `trace:check_impact` would have flagged the tests before the ADR-005 rewrite shipped. Filing this as a concrete use case for when trace is integrated into the Census MCP workflow.

## 2026-02-08: G.6 Prompt Slimming — Tool Rename and FSS-General Language

**What changed:**
- Agent prompt: 280 → 55 lines. Domain-specific rules removed (packs cover them).
- "Never" list: 7 → 4 items (all behavioral, no domain knowledge).
- "Always" list: 5 → 4 items. Added "communicate uncertainty proportional to context."
- Added audience calibration line.
- Removed all ACS/survey-specific language from prompt. Now says "federal statistical system."
- Renamed tool `get_acs_data` → `get_census_data` (server accepts both for backward compat).
- Design notes separated from prompt into `agent_prompt_design_notes.md`.

**Principle:** Prompt = how to think. Packs = what to know. Naming specific surveys in the prompt is overfitting.

**External validation:** ChatGPT 5.2 SWOT analysis of the slim prompt identified audience calibration gap (adopted) and uncertainty communication gap (adopted). Also suggested causal inference guardrail and dual-output templating (rejected — wrong scope for descriptive survey system).

**FCSM talk implication:** The separation of epistemic discipline (prompt) from domain knowledge (packs) is a design principle worth presenting. The prompt doesn't know what survey it's working with — packs specialize at runtime. This enables cross-survey architecture where the same reasoning discipline works for ACS, CPS, SIPP, or any FSS product.

**Test impact:** Integration tests updated to new tool name. 10 tests total (was 9). Added legacy compatibility test.

## 2026-02-09: Quarry Database Setup, First Extraction, and Pipeline Pivot

### What Happened
Full end-to-end test of the KG extraction pipeline using neo4j-labs/llm-graph-builder against the CPS Handbook of Methods (22 pages).

**Environment setup (3 hours):**
- llm-graph-builder cloned, Python 3.12 venv configured
- torch CPU suffix broke on macOS ARM64 (sed fix for constraints.txt)
- RAGAS module has hard OpenAI import dependency — requires dummy API key even with local embeddings
- Backend started at localhost:8000 via uvicorn

**Schema API discovery (dead end):**
- Context7 docs suggested POST /schema to set extraction schema. Wrong.
- Code inspection revealed /schema is read-only (queries existing labels)
- Frontend-dependent schema configuration (Graph Enhancement tab → Data Importer JSON) — requires React app
- Pivoted to direct Cypher seeding via Python script

**Layer 0 seeding (success):**
- 21 nodes: 5 AnalysisTask, 5 QualityAttribute, 4 DataProduct, 6 SurveyProcess, 6 CanonicalConcept + 1 SourceDocument placeholder
- 5 REQUIRES edges with rule_type, threshold, violation_template, recommended_action
- 5 constraints, 8 indexes

**Layer 1 extraction (mixed):**
- 291 nodes, 349 relationships from 22-page PDF
- 93 MethodologicalChoice, 36 ConceptDefinition, 22 TemporalEvent, 17 Threshold
- BUT: Only 3 PRODUCES edges (critical harvest join path nearly empty)
- 291 MENTIONS (generic fallback — noise)
- 9 SourceDocument nodes from 1 PDF (entity hallucination)
- Page-based chunking (1 page = 1 chunk) — lost section context

**Enrichment pass (success):**
- Direct LLM prompt: "What quality consequence does this MethodologicalChoice produce?"
- 89/93 choices got PRODUCES edges with typed QualityAttribute properties
- All 5 REQUIRES dimensions now have matching observations
- 96% coverage from a simple, well-prompted LLM call — outperformed LLMGraphTransformer

**First harvest (partially successful):**
- 8 numeric threshold results: 1 genuine (75% rotation overlap), 7 false positives (type mismatch)
- 20 interaction candidates: some useful (rotation × population controls), some noise (cartesian products)
- Cross-survey queries: 0 results (expected — single survey in document)
- Only 4 orphaned MethodologicalChoice nodes — good coverage

### Key Decisions
- **ADR-008:** Replace llm-graph-builder with custom pipeline. LLMGraphTransformer doesn't populate typed properties, requires enrichment cleanup, page-based chunking is inadequate.
- **ADR-009:** Ship quarry toolkit as project component. Extraction pipeline = reproducible methodology for FCSM paper + toolkit for domain experts.

### Lessons Learned
1. **Direct LLM extraction > LLMGraphTransformer.** The enrichment script (structured JSON output, controlled vocabulary prompt) produced better results in one pass than extraction + enrichment combined.
2. **Section-aware chunking is mandatory.** Page boundaries split mid-paragraph, mid-table. Methodology docs have clear structure (numbered sections, headers). Use it.
3. **Entity resolution at write time prevents hallucinated duplicates.** MERGE on canonical names, not LLM-generated names.
4. **Harvest query false positives come from missing type constraints.** Need `WHERE qa_obs.value_type = qa_std.value_type` to prevent comparing PSU counts against overlap fractions.
5. **Neo4j MCP is single-database.** Claude Desktop config allows one NEO4J_DATABASE. Multi-database work requires direct Python scripts.
6. **llm-graph-builder is a demo tool, not a production extraction pipeline.** Good for pretty graph pictures. Not for domain-specific structured knowledge engineering.

### The Genuine Finding
CPS rotation group design creates 75% sample overlap in consecutive months. The harvest correctly identified this exceeds the 0.2 threshold for temporal comparability. This is exactly the kind of warning a senior statistician would give — and it was derived by graph pattern-matching, not extracted directly from the document. **The architecture works. The tooling doesn't.**

### Files Created
- `docs/decisions/ADR-008-custom-extraction-pipeline.md`
- `docs/decisions/ADR-009-quarry-toolkit-shippable.md`
- `docs/lessons_learned/session_2026-02-09_quarry_setup.md`
- `~/Documents/GitHub/llm-graph-builder/extract_to_quarry.py` (test script)
- `~/Documents/GitHub/llm-graph-builder/enrich_quarry.py` (enrichment script)
- `~/Documents/GitHub/llm-graph-builder/harvest_quarry_v2.py` (harvest script)

---

### 2026-02-09 (Session 2): Quarry Archive & Pipeline Pivot to Docling

**Quarry baseline snapshot before wipe** (llm-graph-builder extraction, CPS Handbook 22 pages):
- 401 nodes: 112 QualityAttribute, 93 MethodologicalChoice, 35 ConceptDefinition, 32 DataProduct, 22 Document, 22 TemporalEvent, 19 SurveyProcess, 17 Threshold, 16 QualityCaveat, 11 SourceDocument, 9 UniverseDefinition, 8 CanonicalConcept, 5 AnalysisTask
- 745 relationships: 291 MENTIONS (noise fallback), 110 SOURCED_FROM, 107 PRODUCES (104 from enrichment pass, 3 from extraction), 54 APPLIES_TO, 37 PART_OF, 35 DEFINED_FOR, 32 OPERATIONALIZES, 17 CONSTRAINS, 16 QUALIFIES, 15 IMPLEMENTS, 15 SUPERSEDES, 10 TARGETS, 5 REQUIRES (Layer 0 seed), 1 MITIGATES

**Known quality issues in baseline:**
1. 291 MENTIONS relationships = LLMGraphTransformer fallback when it can't match schema. Pure noise.
2. 11 SourceDocument nodes from 1 PDF — entity resolution failure ("CPS Handbook of Methods", "Handbook of Methods", "CPS Technical Documentation", etc.)
3. 32 DataProduct nodes — should be ~4 (CPS Basic Monthly, CPS ASEC, etc.). Explosion from uncontrolled entity creation.
4. Harvest false positives: `mode_change_year=1994` compared against `threshold_number=0.2` because no `value_type` filtering. `psu_count=1987` and `sample_size=60000` matching precision thresholds meant for different measures.
5. Only genuine finding: `rotation_group_overlap=0.75` exceeding `temporal_comparability` threshold of `0.2` for EstimateChangeOverTime task. Schema architecture validated despite tooling failure.

**Decision: Docling for PDF parsing** (replaces PyMuPDF page-based extraction)
- IBM Research / LF AI Foundation, MIT license, 8K+ GitHub stars
- Built-in `HierarchicalChunker` respects section boundaries (our #1 failure mode solved)
- Table structure detection with multi-level headers → DataFrame export
- Local execution, Apple Silicon MLX acceleration
- Unified DoclingDocument (Pydantic) with layout metadata, reading order, provenance
- Risk: "computationally intensive" per docs, but irrelevant for 3-4 documents

**Dual Neo4j MCP configuration confirmed:**
- `neo4j-pragmatics` → pragmatics database (25 Context, 1 Pack)
- `neo4j-quarry` → quarry database (to be wiped and rebuilt)
- Resolves previous single-database MCP limitation

**Pipeline design: `scripts/quarry/`** — Docling for parsing, direct structured JSON extraction via LLM, MERGE-based entity resolution, single-pass with OHIO dedup (second pass if needed).

**Target documents for March talk:**
1. CPS Handbook of Methods (22 pages — baseline comparison)
2. ACS Design & Methodology 2024 (100+ pages)
3. CPS Tech Paper 77 (180 pages — scale test)
4. TBD: Census geography hierarchy or statistical quality standards

---

## 2026-02-09 — Extraction Pipeline Results: CPS Handbook, ACS D&M, TP-77

### CPS Handbook (22 pages) — Sonnet
- 157 chunks, 465 nodes, 73 relationships created
- $1.75, ~15 min sequential, ~5.5 min with 3 workers
- 0 validation errors (after evolutionary vocabulary fix)
- 0 MENTIONS, 1 SourceDocument (both pass)
- Baseline comparison vs llm-graph-builder: every failure mode resolved (see ADR-008)

### ACS Design & Methodology 2024 (~150 pages) — Sonnet
- 1347 chunks, 4278 nodes, 741 relationships
- $16.87, ~31 min with 3 workers
- 2 validation errors (0.15% error rate)
- Cross-document harvest working: 3 temporal breaks detected

### CPS Technical Paper 77 (~180 pages) — Haiku ❌
- 1531 chunks, 5077 nodes created (but unreliable)
- **25.7% chunk failure rate** — 394/1531 chunks lost to JSON parse errors
- 5.98% validation error rate (above 5% threshold)
- Haiku hallucinated node and relationship types not in the schema
- $7.23 — cheaper per-dollar but wasteful given 25.7% data loss
- **Verdict: Haiku is not suitable for structured JSON extraction with strict schema compliance.** Haiku works for classification and simple tasks, but cannot reliably produce valid JSON conforming to a controlled vocabulary with 12 node types and 16 relationship types. The cost savings evaporate when a quarter of chunks fail.
- TP-77 must be re-extracted with Sonnet.

### Harvest Results (CPS + ACS, pre-TP77 reextract)
- 0 numeric threshold violations (value_type filter working)
- 0 categorical mismatches (only one survey pair so far)
- 3 temporal breaks (ACS continuous collection 2005, military service question 2024)
- 40 unanticipated interactions (medium confidence, structurally connected via shared QualityAttribute)
- 50 unconnected facts (MethodologicalChoices with no PRODUCES edges — expected for single-survey extraction)
- 0 MENTIONS (pass)

### Key Decisions Made Today
- **ADR-010: Evolutionary Vocabulary** — Three-tier controlled vocab (core/provisional/rejected). LLM found `dissemination` as legitimate category we missed. `definition` was node-type error, not vocab gap. Requirement FR-QE-014.
- **`scope` property added to QualityAttribute** — Distinguishes national/state/sub_state/subgroup/unit measurement level. Eliminates false positives where national sample size (60K) matched per-area threshold (100). Combined with `value_type` filter for belt-and-suspenders.
- **Harvest interaction query fixed** — Was doing cartesian join on dimension (n² noise). Fixed to require shared QualityAttribute node via PRODUCES. Went from 50 low-confidence to 40 medium-confidence structurally-connected results.
- **Parallel workers** — `--workers N` (1-5) via ThreadPoolExecutor. 3x speedup on CPS (18 min → 5.5 min).

### Model Selection Lesson
The "Jobs Doctrine" applies to model selection too, but in the opposite direction from what you'd expect. Smaller/cheaper models don't always clear out complexity — sometimes they introduce it. Haiku's 25.7% failure rate on structured extraction means you'd need error handling, retry logic, output repair, and validation complexity that doesn't exist with Sonnet's <1% failure rate. The cheapest model is the one that works the first time.

Exception: when the task is genuinely simple (classification, yes/no, short-answer), smaller models are appropriate. The discriminator is output structure complexity, not task conceptual difficulty.

### Cost Summary
| Document | Model | Chunks | Cost | Failure Rate |
|----------|-------|--------|------|--------------|
| CPS Handbook | Sonnet | 157 | $1.75 | 0% |
| ACS D&M | Sonnet | 1347 | $16.87 | 0.15% |
| TP-77 | Haiku | 1531 | $7.23 | 25.7% |
| TP-77 (redo) | Sonnet | 1531 | ~$19 | <1% |
| Quality Standards | Sonnet batch-3 | 2476 | $10.02 | <2% (post-cleanup) |
| ACS General Handbook | Sonnet batch-2 | 1326 | $5.89 | <2% (post-cleanup) |

Total extraction spend: ~$55. Budget holding.
Batch mode savings: ~$10-15 vs single-chunk.

### Final Quarry State (5 documents)
- 13,227 nodes, 100% schema compliant (12 types)
- 5 SourceDocuments: CPS Handbook, ACS D&M, CPS TP-77, Quality Standards, ACS General Handbook
- 10 threshold violations, 34 temporal breaks, 147 unanticipated interactions
- Post-extraction cleanup required for Quality Standards and ACS Handbook (~12% invalid types from confabulated node labels, reclassified or deleted)

### Terminology: Confabulation, Not Hallucination
"Hallucination" implies sensory/perceptual phenomenon — models perceiving something that isn't there. LLMs don't perceive anything. They do statistical pattern-completion and generate plausible outputs that aren't grounded in fact.

"Confabulation" is the precise term from neuropsychology — filling in gaps with fabricated information without awareness of doing so. Mechanistically closer to what's actually happening: the model has incomplete information and pattern-completes confidently, producing outputs that look right but aren't sourced.

For a project built on auditable provenance and source-grounded expert judgment, the distinction matters. The entire pragmatics layer exists because LLMs confabulate — they produce statistically plausible Census guidance that isn't traceable to any methodology document. "Hallucination" obscures the mechanism. "Confabulation" points directly at the failure mode the architecture is designed to prevent.

*Potential FCSM talking point — probably only lands with the few nerds who care about precision. Which is exactly the audience.*

---
*Add entries chronologically. Append corrections as new entries, don't edit old ones.*
