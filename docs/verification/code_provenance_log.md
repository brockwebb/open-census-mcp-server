# Phase 4B: Code Provenance and Reuse Log

**Purpose:** Track the origin, rationale, and modifications of all code reused in the CQS evaluation framework. Future-you (and collaborators) should be able to trace any component back to its source and understand why it was adapted.

---

## Source Project

**Repository:** `federal-survey-concept-mapper`
**Report:** 03 — Harmonization Constraints
**Context:** Multi-model LLM ensemble for survey question harmonization classification. Three-tier architecture (raters → arbitrators → triage) processing 1,598 question pairs across CPS-ACS and FoodAPS-ACS. Validated methodology with published results: rater κ=0.611, arbitrator κ=0.843.

**Presentation:** `reports/03_harmonization_constraints/presentation/slides_3b_methodology.qmd`

---

## Components Reused

### 1. Statistical Agreement Functions

**Source:** `federal-survey-concept-mapper/src/lib/stats.py`
**Target:** `census-mcp-server/src/eval/lib/stats.py` (planned)
**Modification level:** None — direct copy

**Functions:**
- `cohens_kappa()` — pairwise inter-rater agreement
- `fleiss_kappa()` — multi-rater agreement (3 judges)
- `krippendorff_alpha()` — reliability coefficient (ordinal support needed for CQS 0-2 scale)
- `percent_agreement()` — simple agreement baseline
- `interpret_kappa()` — Landis & Koch interpretation bands
- `interpret_kappa_mchugh()` — McHugh (2012) health research interpretation with quality gate

**Why reused:** These are standard statistical functions, already tested against 1,598 pairs × 3 raters. No reason to rewrite.

**CQS note:** For CQS, Krippendorff's α with `level_of_measurement='ordinal'` is preferred over Fleiss' κ (which assumes nominal categories) because CQS dimensions use an ordered 0-1-2 scale.

### 2. Judge Pipeline Architecture

**Source:** `federal-survey-concept-mapper/src/pipelines/02_arbitration_pipeline.py`
**Target:** `census-mcp-server/src/eval/cqs_judge_pipeline.py` (planned)
**Modification level:** Significant — structural adaptation

**Reused patterns:**
- **Blind masking:** Responses presented as "Response A" / "Response B" instead of "control" / "treatment" — prevents judge from knowing which has pragmatics. Adapted from "Rater A/B/C" masking in harmonization pipeline.
- **Order randomization:** 50/50 fixed vs randomized presentation order, deterministic via query_id hash (`should_randomize()`, `get_rater_order()`). Enables position bias detection. Direct reuse of logic.
- **Pydantic structured output:** `ArbitrationResult` schema → `CQSJudgment` schema. Same pattern, different fields.
- **JSONL checkpointing with thread locks:** Resume-safe processing for long runs. Direct reuse.
- **ThreadPoolExecutor parallelism:** Concurrent judge API calls. Direct reuse.
- **Multi-model API callers with retry:** `call_google()`, `call_openai()`, `call_anthropic()` patterns. Adapted for judge models.

**What changes:**
| Harmonization | CQS |
|---|---|
| Input: 3 rater codings per pair | Input: 2 responses (control + treatment) per query |
| Output: barrier code + feasibility (categorical) | Output: 6 dimensions × 0-2 score (ordinal) |
| Taxonomy reference in prompt | CQS rubric specification in prompt |
| `ArbitrationResult` Pydantic model | `CQSJudgment` Pydantic model |
| 1,598 pairs | ~50-100 test queries (initial battery) |

### 3. Agreement Analysis Pipeline

**Source:** `federal-survey-concept-mapper/src/pipelines/03_analysis_pipeline.py` and `03_stage2_agreement.py`
**Target:** `census-mcp-server/src/eval/cqs_analysis.py` (planned)
**Modification level:** Moderate — same metrics, different data structure

**Reused patterns:**
- Pairwise κ between each judge pair
- Fleiss' κ across all 3 judges (→ Krippendorff's α for ordinal CQS)
- Vendor bias detection: same-vendor selection rate analysis
- Position bias detection: fixed vs randomized order comparison
- Agreement heatmaps and behavioral profile analysis

**What changes:**
- Harmonization used categorical agreement (exact match on barrier codes)
- CQS uses ordinal agreement (0-2 scale per dimension) — need weighted κ or Krippendorff's α ordinal
- Treatment effect analysis is new: paired comparison of control vs treatment CQS scores

### 4. Methodology Documentation Pattern

**Source:** `federal-survey-concept-mapper/docs/methodology/` and `reports/03_harmonization_constraints/`
**Target:** `census-mcp-server/docs/verification/`
**Modification level:** Structural reuse of documentation approach

**Reused patterns:**
- Methodology log with numbered decisions
- Explicit bias documentation (vendor bias, position bias, verbosity bias)
- Construct validity argument through independent architecture convergence
- Cost/quality tradeoff analysis (2-model vs 3-model)

---

## Components NOT Reused

| Harmonization Component | Why Not Applicable |
|---|---|
| `01_barrier_pipeline.py` (rater tier) | CQS has no rater tier — we generate responses, not classify them |
| `04_findings_pipeline.py` | Domain-specific to survey harmonization findings |
| `05_deliverables_pipeline.py` | Domain-specific deliverable generation |
| `src/core/` | Harmonization-specific domain logic |
| `src/lib/taxonomy.py` | Barrier taxonomy — replaced by CQS rubric |

---

## New Components (no harmonization precedent)

### 1. Agent Harness (`cqs_agent_harness.py`)

**Purpose:** Run Claude API with live MCP tools in an agent loop (tool_use → execute → tool_result → response). Also run control path (no tools).

**No precedent in harmonization project** — that project sent static prompts to LLMs. This project needs a live tool-calling agent loop with an MCP subprocess.

### 2. MCP Client

**Purpose:** Programmatic subprocess launch of census-mcp-server, stdio JSON-RPC connection, tool execution.

**New code** — uses `mcp` Python SDK client classes.

### 3. Test Battery (`cqs_test_battery.yaml`)

**Purpose:** Data-driven test query definitions with expected edge cases, persona variants, and difficulty ratings.

**New content** — informed by Phase 4A manual validation experience and pragmatics pack coverage.

### 4. Treatment Effect Analysis

**Purpose:** Paired comparison of CQS scores (control vs treatment) with statistical significance testing.

**New analysis** — the harmonization project compared models to each other, not treatment vs control conditions.

---

## Validation of Reuse

The harmonization methodology was validated empirically:
- **Rater tier:** κ=0.611 (substantial) — task well-defined
- **Arbitrator tier:** κ=0.843 (almost perfect) — deeper reasoning improves convergence
- **Vendor bias:** Anthropic unbiased (p=0.159), Google anti-self (p<0.001), OpenAI pro-self (p<0.001)
- **Position bias:** Detected and quantified through 50/50 randomization design

These validation results give confidence that the same architectural patterns will produce reliable CQS scoring, adapted for the different domain and task structure.

---

## Citation

If referencing this methodology in publications:

> The CQS judge panel methodology adapts the multi-model ensemble approach validated in Webb (2026) for survey harmonization classification, which achieved arbitrator agreement of κ=0.843 across three frontier models with documented vendor and position bias controls.
