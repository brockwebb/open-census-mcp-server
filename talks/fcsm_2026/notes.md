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

---
*Add entries chronologically. Append corrections as new entries, don't edit old ones.*
