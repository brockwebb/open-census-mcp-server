# Lab Notes — V1 to V2 Evaluation Redesign

**Date:** 2026-02-21 (retroactive documentation)
**Period covered:** 2026-02-13 (V1 final) → 2026-02-16 through 2026-02-19 (V2 redo)

---

## Why V2 Exists

V1 evaluation had two fatal design flaws that confounded the experimental variable (knowledge representation form) with uncontrolled variables (tool access and data leakage).

### Flaw 1: Asymmetric Tool Access

V1 gave the three conditions unequal data retrieval capabilities:

| Condition | Census API Tools | Methodology Support |
|-----------|-----------------|-------------------|
| Control | **None** | None |
| RAG | **None** | Retrieved document chunks |
| Pragmatics | `get_census_data`, `explore_variables`, `get_methodology_guidance` | Curated expert judgment via MCP |

The study claimed to measure the effect of methodology support form. But it actually measured tool access + methodology support, conflated. Result: 33 of 39 RAG responses directed users to data.census.gov because the model had no way to retrieve data itself. The RAG condition couldn't demonstrate data consultation quality because it couldn't consult data.

### Flaw 2: Pragmatics Leakage

Discovered 2026-02-16 during V2 implementation. The `get_census_data` MCP tool bundles curated pragmatics content (context IDs, guidance text, thread edges) in every response payload via `retriever.get_guidance_by_parameters()`. Without sanitization, ALL three conditions would receive curated expert judgment through the data tool response — defeating the experimental design entirely.

Even with equal tool access, the control and RAG conditions would get pragmatics for free in the tool return payload.

### Reference Documents

- **Leakage discovery:** `talks/fcsm_2026/2026-02-16_pragmatics_leakage.md`
- **SRS rationale:** VR-030 rationale block (docs/requirements/srs.md)
- **Design of Experiments:** `docs/verification/doe_rag_ablation_plan.md` (V1 framing, superseded by V2 SRS Section 8)

---

## V2 Design Corrections

### Equal Tool Access (VR-024–026)

All three conditions now receive identical Census API tool access:

| Condition | Census API Tools | Methodology Support |
|-----------|-----------------|-------------------|
| Control | `get_census_data`, `explore_variables`, `get_methodology_guidance` | None (guidance stripped from tool results) |
| RAG | Same | Retrieved document chunks prepended to system prompt |
| Pragmatics | Same | Curated expert judgment delivered in tool results |

The only experimental variable is the form of methodology support. Data access is held constant.

### Pragmatics Sanitization (VR-030)

The agent loop strips the `pragmatics`, `source`, `related`, and `provenance` fields from `get_census_data` tool results before passing them to the model for control and RAG conditions. The full unsanitized results are preserved in Stage 1 ResponseRecords for archival and fidelity verification.

### Contamination Checks (VR-027, VR-028)

Defense-in-depth: automated verification that control/RAG responses contain zero pragmatics vocabulary and zero context IDs that could only come from leaked guidance.

### Grounding Gate (VR-029)

The agent loop enforces that all conditions call `get_methodology_guidance` before data retrieval. For control/RAG, the guidance is called but the pragmatics payload is stripped — the model gets the tool call pattern but not the expert judgment content. This ensures the methodology consultation behavior is constant across conditions; only the content of that consultation varies.

---

## V2 Redo Timeline

| Date | Activity | Output |
|------|----------|--------|
| Feb 16 | Stage 1: Full battery run, all 3 conditions. Pragmatics needed 3 runs to fix grounding gate bugs (see `2026-02-16_stage1_rerun_history.md`) | `results/v2_redo/stage1/` — 3 JSONL files |
| Feb 16 | Stage 2: RAG vs Pragmatics judge scoring (702 records) | `results/v2_redo/stage2/rag_vs_pragmatics_20260216_092144.jsonl` |
| Feb 17 | Stage 2: Control vs RAG judge scoring (702 records) | `results/v2_redo/stage2/control_vs_rag_20260217_083951.jsonl` |
| Feb 18 | Stage 2: Control vs Pragmatics judge scoring (699 records + 3 backfilled) | `results/v2_redo/stage2/control_vs_pragmatics_20260218_065924.jsonl` |
| Feb 19 | Stage 2: Backfill 3 missing Google records | Appended to `_065924.jsonl` |
| Feb 19 | Stage 2: Final aggregate analysis | `results/v2_redo/stage2/analysis/aggregate_statistics.md` |
| Feb 19 | Stage 3: V2 fidelity verification (3-condition format) | `results/v2_redo/stage3/fidelity_20260219_214225.jsonl` |
| Feb 21 | Stage 3: Fidelity aggregation script (VR-091–096) | `results/v2_redo/stage3/analysis/fidelity_summary.md` |
| Feb 21 | Stage 3: Fidelity QC verification (VR-097–100) | `results/v2_redo/stage3/analysis/fidelity_qc_report.md` — PASS |

---

## V1 Data Disposition

All V1 data remains in place for archival:

| V1 Location | Contents | Status |
|-------------|----------|--------|
| `results/stage1/` | V1 paired responses (asymmetric tool access) | Archived — do not cite |
| `results/stage2/` | V1 judge scores | Archived — do not cite |
| `results/stage3/` | V1 fidelity (2-condition format) | Archived — do not cite |
| `results/rag_ablation/` | V1 RAG experiment (no tool access for RAG/control) | Archived — do not cite |

**The term "RAG ablation" is V1 legacy naming.** The V2 evaluation is a "knowledge representation study" comparing three conditions with equal data tool access. File paths in `results/rag_ablation/` retain the old name for git history continuity but the conceptual framing is superseded.

---

## Canonical Citation Dataset

All publication numbers trace to `results/v2_redo/`:

| Stage | Certified Output | V&V Script | SRS |
|-------|-----------------|------------|-----|
| Stage 2 | `aggregate_statistics.md` | `aggregate_analysis.py` | VR-048, VR-060–065 |
| Stage 3 | `fidelity_summary.md` | `fidelity_qc.py` (exit 0) | VR-091–100 |

No V1 numbers should appear in the paper. If V1 numbers are referenced for methodological comparison (e.g., "V1 had asymmetric tool access which we corrected"), they must be explicitly labeled as V1/superseded.
