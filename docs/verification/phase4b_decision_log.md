# Phase 4B: Decision Log

**Purpose:** Record all design decisions made during Phase 4B development with rationale. Complements the methodology documentation in the rubric, battery, and prompt specs.

---

## DEC-4B-001: Single Model for MVP

**Date:** 2026-02-12
**Context:** Phase 4B originally specified multi-model evaluation (Claude, OpenAI, Gemini as test subjects). 
**Decision:** MVP uses Claude only as the test subject. Judge panel remains multi-model.
**Rationale:** The research question is "does pragmatics improve response quality?" not "which model benefits most from pragmatics." Proving the treatment effect on one model is prerequisite to justifying multi-model expansion. Building three model integrations before validating the approach wastes effort if the rubric or harness needs revision.
**Revisit when:** Treatment effect demonstrated on Claude. Then repeat with other models.

## DEC-4B-002: Live MCP Agent Loop (Not Simulated)

**Date:** 2026-02-12
**Context:** Three options considered for the test harness: (A) Direct API with simulated tools, (B) MCP subprocess with stdio, (C) Two-pass with pre-injected pragmatics.
**Decision:** Option B — live MCP subprocess with full agent loop.
**Rationale:** Option C strips out tool interaction, which is half of what the system does. The pragmatics layer shapes which data gets retrieved and how responses are structured, not just adding context to a prompt. Pre-injecting a static blob of guidance tests a different system than the one being built. Option A (simulated tools) adds complexity without fidelity. Option B tests the real system.
**Trade-off:** More complex harness code, but the results are credible because they test the actual architecture.

## DEC-4B-003: Three-Model Judge Panel

**Date:** 2026-02-12
**Context:** Scoring could use single-model LLM judge, multi-model panel, or human-only.
**Decision:** Three-model panel (Claude, OpenAI, Gemini) with human calibration subset.
**Rationale:** 
- Claude judging Claude is suspect (self-enhancement bias documented in Zheng et al. 2023)
- Three independent architectures provide inter-rater reliability measurement
- Bias mitigation: documented vendor bias patterns from harmonization study (Anthropic neutral p=0.159, OpenAI pro-self p<0.001, Google anti-self p<0.001)
- Scalability: can score full battery without weeks of expert time
- Human calibration subset (10-15 queries) anchors automated scores to expert judgment
**Precedent:** Validated in author's survey harmonization classification (κ=0.843 arbitrator agreement).

## DEC-4B-004: CQS Rubric — Six Dimensions

**Date:** 2026-02-12
**Context:** Source material suggested 5–12 dimensions across multiple frameworks (FCSM 20-04, NIST AI RMF, three LLM-generated proposals).
**Decision:** Six dimensions: Source Selection, Methodological Soundness, Uncertainty Communication, Definitional Accuracy, Reproducibility & Traceability, Groundedness & Faithfulness.
**Rationale:** 
- More than 6-7 dimensions degrades judge reliability (cognitive load on LLM judges)
- Six dimensions map cleanly to FCSM (Utility, Objectivity, Integrity) and NIST AI RMF
- Disclosure avoidance and temporal comparability fold into D1 and D4 as subcases — they aren't independent dimensions at the frequency encountered in test queries
- D6 (Groundedness) is the novel contribution — neither FCSM nor NIST covers AI hallucination in the statistical domain
**Framework crosswalk:** Documented in `cqs_rubric_specification.md` Section 2.

## DEC-4B-005: NIST Valid & Reliable as Gate Condition

**Date:** 2026-02-12
**Context:** How to handle the NIST AI RMF "Valid & Reliable" characteristic in the CQS mapping.
**Decision:** V&R is a pass/fail gate, not a scored dimension. Maps to D6 — if D6=0 (fabricated data), other scores are unreliable.
**Rationale:** NIST treats V&R as a gate, not a spectrum. If the system fabricates data, scoring its methodology or uncertainty communication is meaningless — you're scoring the quality of fiction. This matches how a federal statistician would react: "these numbers are made up" terminates the review.
**Implementation:** D6=0 noted as gate failure in rubric. Open question whether it should cap total CQS.

## DEC-4B-006: FCSM "N/A" Not "Gap"

**Date:** 2026-02-12
**Context:** D6 (Groundedness) has no FCSM equivalent. How to frame this in the crosswalk.
**Decision:** Label as "N/A — FCSM not designed for AI-mediated use" rather than "gap."
**Rationale:** FCSM 20-04 was designed for human statistical practice. The absence of an AI hallucination dimension is not a deficiency — it's outside the framework's intended scope. Calling it a "gap" implies FCSM should have covered it, which is unfair to a framework written for a different context. CQS extends FCSM to a new application, not patches it.

## DEC-4B-007: Informed Refusal Scoring Principle

**Date:** 2026-02-12
**Context:** How should the rubric score a response that correctly declines to provide data?
**Decision:** Informed refusal with explanation always outscores confident delivery of unfit data. Added as General Scoring Principle 1, with specific "Also scores 2" language in D1 and D3.
**Rationale:** A senior statistician who says "we can't answer that reliably with available data" is doing better work than one who delivers a number with a CV of 60%. The alternative — only scoring responses that provide data — creates a perverse incentive for the system to always deliver something, even when the responsible action is to decline. Three tiers: bare refusal (low) < informed refusal with reasoning (high) < successful delivery with appropriate caveats (high).
**Impact:** This is essential for queries like GEO-006 (Loving County, pop ~64) where the correct answer is "don't use this data."

## DEC-4B-008: Absolute + Pairwise Hybrid Scoring

**Date:** 2026-02-12
**Context:** LLM-as-judge literature supports both absolute scoring (rate each response independently) and pairwise comparison (which is better).
**Decision:** Hybrid — each response scored independently on all 6 dimensions (absolute), plus overall preference judgment (pairwise).
**Rationale:** 
- Absolute scores enable dimension-level analysis: "Treatment improves D3 by 0.8 points on average"
- Pairwise preference enables headline result: "Judges preferred treatment 72% of the time"
- Justification per dimension forces judge to reason before scoring, improving reliability
- Pairwise alone wouldn't tell us which dimensions drive the preference
- Absolute alone misses the holistic judgment a statistician would make

## DEC-4B-009: Battery Split — 41% Normal / 59% Edge Cases

**Date:** 2026-02-12
**Context:** Original battery was 80/20 edge cases per SRS VR-010. Revised after recognizing need for equivalence testing on normal queries.
**Decision:** 15 normal (41%) / 24 edge cases (59%), total 39 queries.
**Rationale:** Driven by statistical power requirements, not arbitrary ratio.
- Edge case stratum: Superiority test (treatment > control). Expected large effect (d≈0.8). Wilcoxon signed-rank at α=0.05, power=0.80 needs ~15 pairs. 24 queries provides margin.
- Normal stratum: Equivalence test (treatment ≈ control). TOST with ±1 CQS margin ideally wants 25-30, but 15 sufficient for preliminary "no degradation" claim with 3 judges providing variance reduction.
- Total: 39 queries × 2 conditions × 3 judges = 234 judge API calls. Manageable.
**Analysis plan:** Results reported stratified. Primary hypothesis on edge cases. Normal queries as separate equivalence analysis.
**Supersedes:** SRS VR-010 80/20 ratio (which was a testing principle, not a statistical design parameter).

## DEC-4B-010: Reuse of Harmonization Ensemble Architecture

**Date:** 2026-02-12
**Context:** Building a judge pipeline from scratch vs adapting existing validated code.
**Decision:** Adapt architecture from `federal-survey-concept-mapper/src/pipelines/02_arbitration_pipeline.py` with documented modifications.
**Rationale:**
- Blind masking, order randomization, JSONL checkpointing, parallel execution, multi-model API callers already built and tested against 1,598 pairs
- Agreement analysis functions (`stats.py`) already validated
- Vendor bias detection methodology already proven
- Reduces development time and introduces fewer bugs than greenfield
- Key adaptation: classification (categorical) → scoring (ordinal), requiring Krippendorff's α with ordinal measurement instead of Fleiss' κ
**Provenance:** Documented in `code_provenance_log.md`.

## DEC-4B-011: Safety as Emergent Property (Not Separate Dimension)

**Date:** 2026-02-12
**Context:** NIST AI RMF includes "Safe" as a trustworthiness characteristic. Should CQS have a safety dimension?
**Decision:** No separate safety dimension. Safety is distributed across D1, D2, D4.
**Rationale:** In federal statistics, the safety risk is using wrong data for policy decisions. If a school board allocates funding based on an ACS 1-year estimate for a 15K-population county, that's the harm. This is captured by D1 (wrong product = Relevance failure), D2 (unreliable estimate = Accuracy failure), and D4 (misunderstood concept = Coherence failure). FCSM handles safety the same way — as an emergent property of getting the other dimensions right, not a separate checkbox.

## DEC-4B-012: Objectivity Subsumes Fairness for This Domain

**Date:** 2026-02-12
**Context:** NIST AI RMF includes "Fair (Bias-managed)" as a characteristic. Should CQS address fairness separately?
**Decision:** Fairness folded into Objectivity (IQA definition: "accurate, clear, complete, and unbiased"). Relevant bias is epistemic, not demographic.
**Rationale:** For AI-mediated statistical consultation, the bias risk is epistemic — the LLM confidently asserting something wrong because training data blurs distinctions (semantic smearing). This is Objectivity in the IQA sense. Demographic fairness (NIST's primary concern with "Fair") applies to AI classification/prediction systems, not to data consultation where the goal is accurately describing all populations. CQS addresses epistemic bias through D6 (Groundedness).

---

## DEC-4B-013: Test Subject Model — Sonnet 4.5

**Date:** 2026-02-12
**Decision:** Use Claude Sonnet 4.5 (`claude-sonnet-4-5-20250514`) as the test subject (the model answering Census queries).
**Rationale:**
- Sonnet is the median model real users encounter in Claude Desktop
- Sonnet is more dependent on tool-provided guidance than Opus, maximizing observable treatment effect
- Model-specific results are ephemeral (Jobs Doctrine: in a year, Sonnet 4.5 will be in the dustbin). The architecture and methodology are the contribution, not the model-specific scores.
- Testing additional models is yak shaving. If it works on one, repeat later. The framework is model-agnostic.

## DEC-4B-014: Judges Must Be More Capable Than Test Subject

**Date:** 2026-02-12
**Decision:** Judge panel uses Opus-class models (Claude Opus 4.5, GPT-5.2, Gemini 2.5 Pro). Test subject is Sonnet-class. Opus does not judge Opus.
**Rationale:** A judge must be more capable than the thing it evaluates. Using the same capability tier for both test subject and judge conflates their error modes. Opus-class judges can reliably assess Sonnet-class outputs; the reverse would not hold.

## DEC-4B-015: No CLAUDE.md in Test — External Tester Perspective

**Date:** 2026-02-12
**Decision:** Treatment system prompt does NOT include project-specific CLAUDE.md rules. Uses minimal generic prompt.
**Rationale:** The test must represent an external user's experience. An external tester has the MCP server and its tools — nothing more. Including CLAUDE.md would confound the test: measuring "better prompt + tools" vs "bare prompt" rather than isolating the tool/pragmatics effect. The MCP architecture must stand on its own.

## DEC-4B-016: Stateless API Calls (Zero-Shot)

**Date:** 2026-02-12
**Decision:** All test queries are single-turn, stateless API calls. No conversation history, no memory, no chain-of-thought follow-up.
**Rationale:**
- API calls are stateless by design — each query is zero-shot, no accumulated context
- This removes system memory effects that could confound results
- Reflects realistic worst-case: most users will accept the first response as authoritative because the subject area expertise to challenge it is uncommon
- Pros outweigh cons: loses chain-of-thought refinement, but gains experimental cleanliness and reproducibility
- A follow-up study could test multi-turn interactions, but the MVP must establish single-turn treatment effect first
**Acknowledged limitation:** Single-turn is a lower-bound test. A competent user would follow up. Frame in paper as "we evaluate single-turn consultation as a lower bound on consultation quality."
**v0.2 extension:** Automated multi-turn: use a non-Anthropic consultant model (e.g., GPT-5.2) to evaluate the response, generate a follow-up question, and score the resulting two-turn exchange. This avoids Opus judging Opus's continuation.

## DEC-4B-017: Cross-Family Validation (v0.2)

**Date:** 2026-02-12
**Decision:** v0.2 will include a cross-family validation using a non-Anthropic model (GPT-5-mini or equivalent) as an additional test subject calling the same MCP tools.
**Rationale:**
- Preempts "this only works because it's Claude calling Claude's tools" critique
- Different model family provides breadth — not another model within the same family
- Not a blocker for v0.1 MVP. 5-10 queries, not full battery.
- Judge/rater panel scores cross-family responses using same CQS rubric.
**Note:** Requires confirming GPT-5-mini supports tool_use/function_calling with MCP-compatible schema.

## DEC-4B-018: Pin Exact Model Strings for Reproducibility

**Date:** 2026-02-12
**Decision:** All model strings pinned to exact version identifiers in config and paper.
**Rationale:** Model capabilities change across versions. Results from `claude-sonnet-4-5-20250514` may not replicate on a subsequent Sonnet release. Paper must document exact strings. Harness config already enforces this, but it must be called out in methodology section.

## DEC-4B-019: No Hardcoded Defaults — All Parameters in Config Files

**Date:** 2026-02-12
**Context:** Server.py contained six instances of hardcoded `2022` as the default year, plus hardcoded `"acs5"` as default product. The latest ACS 5-year release covers 2020-2024 (year=2024), making the hardcoded default stale. The stale default caused the NORM-001 smoke test to serve 2022 data while claiming it was "most current available" — a silent D6 (Groundedness) failure baked into the system.
**Decision:** ALL parameters that affect outputs MUST be externalized to config files. No exceptions. No hardcoded defaults in application code.
**Implementation:**
- Created `src/census_mcp/config.py` as single source of truth
- All defaults (year, product, log level, log file, packs dir, server name) read from config
- Environment variables override config defaults for runtime flexibility
- Tool schema descriptions dynamically reference config values (f-strings)
- Tool dispatch fallbacks reference config constants
**Rationale:**
- Hidden parameters that affect outputs are reproducibility killers
- A buried `default: 2022` silently determines every query result when the caller doesn't specify year
- Stale defaults produce systematically wrong results that look correct (the most dangerous failure mode)
- Config-as-code makes the parameter state auditable, diff-able, and version-controlled
- Env var overrides allow deployment flexibility without code changes
**Rule:** This is a hard, fixed, permanent project rule. Every future parameter that could affect outputs goes in config.py, not in application logic.
**Files:** `src/census_mcp/config.py` (created), `src/census_mcp/server.py` (modified)

## DEC-4B-020: Mandatory Grounding Even for Clarification Requests

**Date:** 2026-02-12
**Context:** Stage 1 battery run revealed 5/39 treatment queries (13%) where Sonnet answered without calling any tools, despite tools being available and the prompt saying "FIRST call get_methodology_guidance." All five were ambiguity/mismatch queries where the model chose clarification over tool use. This is stochastic model behavior — non-determinism is a feature, not a bug. But it created two problems: (1) diagnostic ambiguity — we couldn't distinguish "model chose not to use tools" from "tools were unavailable", and (2) missed pragmatics-informed clarification — grounding first produces better questions.
**Decision:** Strengthen treatment prompt to mandate grounding even when clarification is needed. Add `tools_offered` boolean to ResponseRecord for diagnostic transparency.
**Rationale:**
- Pragmatics-informed clarification is strictly superior to generic clarification (e.g., "Which Springfield? Note that small Springfields only have 5-year estimates...")
- Diagnostic logging (tools_offered vs tool_calls) accounts for stochastic variance without trying to eliminate it
- This is analogous to measurement error in survey methodology — you don't eliminate it, you quantify and account for it
**Files:** `src/eval/agent_loop.py` (prompt + logging), `src/eval/models.py` (new field)
**Lesson learned:** `docs/lessons_learned/2026-02-12_tool_nonuse_treatment_path.md`

## DEC-4B-023: D6 Rubric Revision — Groundedness → Pipeline Fidelity

**Date:** 2026-02-13
**Context:** D6 "Groundedness & Faithfulness" consistently scored treatment LOWER than control (d=-0.23) across all judge vendors. Investigation revealed a rubric design flaw: judges reward vagueness and penalize specificity because they have no verification capability.
**Decision:** Replace D6 subjective judge scoring with automated Pipeline Fidelity metric. CQS composite becomes D1-D5 (5 dimensions). Fidelity reported separately.
**Rationale:** Groundedness of API-retrieved data is a deterministic measurement, not a subjective judgment. Stage 1 data contains both tool call results and response text — fidelity is a diff operation. This is "arbitrary coherence" — judges score plausibility without verification tools.
**Implementation:** `src/eval/fidelity_check.py` extracts claims from response_text, compares against tool_call data, computes match rate. Treatment gets fidelity score (verified claims / total claims). Control gets auditability classification (how specific are claims for external verification).
**Framework mapping:** NIST AI RMF (Valid and reliable outputs), OMB A-130 (Auditability), FCSM (Transparency).
**Full documentation:** `docs/verification/phase4b_decision_log_DEC023.md`

## DEC-4B-024: Symmetric Measurement — Both Conditions Get All Instruments

**Date:** 2026-02-13
**Context:** Initial Stage 3 design only measured treatment fidelity and control auditability, producing an asymmetric comparison table with N/A cells.
**Decision:** Run the auditability classifier on BOTH conditions. Fidelity checking remains treatment-only (control has no tool logs to diff against).
**Rationale:** Both conditions must receive the same measurement instruments. Asymmetric measurement invites reviewer objection ("why didn't you measure X on both?") and the only honest answer is "we assumed" — an untested assumption in a paper about testing assumptions. The asymmetry in fidelity (measurable for treatment, unmeasurable for control) is itself a finding: control claims lack sufficient specificity for independent verification.
**Impact:** Stage 3 outputs now include both `treatment_fidelity` and `treatment_auditability` plus `control_auditability`. Treatment can be compared to control on auditability dimension, demonstrating specificity improvement.
**Files:** `src/eval/fidelity_check.py` (symmetric measurement)

## Decision Index

| ID | Short Title | Key Trade-off |
|---|---|---|
| DEC-4B-001 | Single model MVP | Speed vs breadth |
| DEC-4B-002 | Live MCP agent loop | Harness complexity vs result credibility |
| DEC-4B-003 | Three-model judge panel | Cost vs bias mitigation |
| DEC-4B-004 | Six CQS dimensions | Granularity vs judge reliability |
| DEC-4B-005 | V&R as gate condition | Binary gate vs continuous scoring |
| DEC-4B-006 | FCSM "N/A" framing | Academic precision in framework crosswalk |
| DEC-4B-007 | Informed refusal scoring | Rewarding caution vs rewarding data delivery |
| DEC-4B-008 | Absolute + pairwise hybrid | Analysis depth vs judge complexity |
| DEC-4B-009 | 41/59 battery split | Equivalence power vs treatment effect power |
| DEC-4B-010 | Harmonization code reuse | Development speed vs clean-room implementation |
| DEC-4B-011 | Safety as emergent | Dimension count vs NIST completeness |
| DEC-4B-012 | Objectivity subsumes fairness | Domain specificity vs framework completeness |
| DEC-4B-013 | Sonnet 4.5 as test subject | Realistic median vs ceiling performance |
| DEC-4B-014 | Judges more capable than subject | Capability hierarchy for valid evaluation |
| DEC-4B-015 | No CLAUDE.md in test | Isolating tool effect vs real-world fidelity |
| DEC-4B-016 | Stateless zero-shot calls | Experimental cleanliness vs multi-turn realism |
| DEC-4B-017 | Cross-family validation (v0.2) | Breadth vs scope creep |
| DEC-4B-018 | Pin exact model strings | Reproducibility hygiene |
| DEC-4B-019 | No hardcoded defaults | Auditability vs convenience |
| DEC-4B-020 | Mandatory grounding even for clarification | Tool compliance vs model autonomy |
| DEC-4B-021 | 6 judge passes, 234 calls/judge | Measurement precision vs rate limits vs statistical power |
| DEC-4B-023 | D6 → Pipeline Fidelity | Subjective judging vs automated verification |
| DEC-4B-024 | Symmetric measurement | Experimental rigor vs assumed equivalence |
