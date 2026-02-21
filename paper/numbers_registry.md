# Numbers Registry — Publication Data Catalogue

**Purpose:** Single source of truth for every statistic cited in publication materials. Every number traces to a source file, computation script, SRS requirement, and V&V certification status.

**Rule:** No number appears in the paper, slides, or handout unless it has an entry here with status CERTIFIED or COUNTABLE. Numbers with status PENDING or UNTRACED must be resolved before citation.

**Last updated:** 2026-02-21 (session 2: SRS fix, determinism, design derivation, new gaps 011-014)

---

## Status Definitions

| Status | Meaning |
|--------|---------|
| CERTIFIED | Produced by SRS-documented script, independently verified by V&V script (exit 0) |
| COUNTABLE | Deterministic count from a static artifact (file line count, YAML entries, DB query). Reproducible by inspection. |
| COMPUTED | Produced by SRS-documented script but no independent V&V verification yet |
| PENDING | Known to exist in raw data but no documented script produces the aggregate |
| UNTRACED | Cited in handoffs/threads but source not yet confirmed |

---

## Section 1: Study Design Parameters

| ID | Number | Description | Source File | Script | SRS Req | V&V | Status |
|----|--------|-------------|-------------|--------|---------|-----|--------|
| SD-001 | 39 | Total queries in test battery | `src/eval/battery/queries.yaml` | N/A (count) | VR-010 | — | COUNTABLE |
| SD-002 | 3 | Experimental conditions (control, RAG, pragmatics) | `src/eval/judge_config.yaml` | N/A (design) | VR-024–026 | — | COUNTABLE |
| SD-003 | 3 | Judge vendors (Anthropic, OpenAI, Google) | `src/eval/judge_config.yaml` | N/A (design) | VR-031 | — | COUNTABLE |
| SD-004 | 6 | Passes per comparison (3 vendors × 2 orderings) | `src/eval/judge_config.yaml` | N/A (design) | VR-032 | — | COUNTABLE |
| SD-005 | 3 | Pairwise comparisons (C-R, C-P, R-P) | `src/eval/judge_config.yaml` | N/A (design) | VR-041 | — | COUNTABLE |
| SD-006 | 2,106 | Total Stage 2 judge records. 0 parse failures. Backfills: 3 Anthropic (rag_vs_pragmatics, 2026-02-21 commit 2112ec7), 3 Google (control_vs_pragmatics, 2026-02-19). All files 702/702 clean. Zero delta on aggregates confirmed. | `results/v2_redo/stage2/*.jsonl` | N/A (count) | VR-041 | verify_registry_counts.py | COUNTABLE |
| SD-007 | 702 | Judge records per comparison (39 × 6 passes × 3 vendors) | `results/v2_redo/stage2/*.jsonl` | N/A (count) | VR-041 | verify_registry_counts.py | COUNTABLE |
| SD-008 | 5 | CQS dimensions scored (D1–D5) | `src/eval/judge_prompts.py` | N/A (design) | VR-037 | — | COUNTABLE |
| SD-009 | 38% / 62% | Normal (15) / edge case (24) split. Categories: normal(15), geographic_edge(7), small_area(4), temporal(4), ambiguity(3), product_mismatch(3), persona(3). SRS VR-010 corrected from 41%/59% to match actual battery. | `src/eval/battery/queries.yaml` | N/A (count) | VR-010 | verify_registry_counts.py | COUNTABLE |
| SD-010 | 1 | Caller model (`claude-sonnet-4-5-20250929`) | `src/eval/judge_config.yaml` | N/A (config) | VR-021 | — | COUNTABLE |

---

## Section 2: Pragmatics Layer Parameters

| ID | Number | Description | Source File | Script | SRS Req | V&V | Status |
|----|--------|-------------|-------------|--------|---------|-----|--------|
| PL-001 | 36 | Curated pragmatic items in compiled ACS pack (36 context rows, 35 threads). **NOTE:** Previously cited as 35 — actual compiled pack has 36. | `packs/acs.db` (context table) | N/A (DB count) | verify_registry_counts.py | COUNTABLE |
| PL-002 | 36 | Staged pragmatic items in `staging/acs/*.json` (18 category files). **NOTE:** Previously cited as 47 — DISCREPANCY. Actual count is 36 from verify script. The 47 figure is untraced; may reflect an older version or items staged in other domains. | `staging/acs/*.json` | `verify_registry_counts.py` | — | `paper/registry_verification_report.md` | COUNTABLE |
| PL-003 | — | Source documents for pragmatic extraction | Quarry pipeline / provenance | — | VR-081 | — | PENDING |
| PL-004 | 39/39 (100%) | Grounding gate: Pragmatics called `get_methodology_guidance` on all 39 queries. Control 0/39 and RAG 0/39 is correct by design — VR-025 excludes the tool from their tool list, VR-027/028 verify zero contamination. **Not a discrepancy.** | `results/v2_redo/stage1/*_responses_*.jsonl` | `verify_registry_counts.py` | VR-025, VR-027, VR-028 | `paper/registry_verification_report.md` | COUNTABLE |

---

## Section 3: Stage 2 — CQS Judge Scores (CERTIFIED)

Source: `results/v2_redo/stage2/analysis/aggregate_statistics.md` + `.json`
Script: `src/eval/aggregate_analysis.py`
V&V: `src/eval/aggregate_analysis.py` (self-documenting per VR-048; SRS Section 8.9 registry)
SRS: VR-048, VR-060–065

### 3a. Omnibus Test

| ID | Number | Description | Status |
|----|--------|-------------|--------|
| S2-001 | 42.01 | Friedman χ²(2, N=39) composite CQS | CERTIFIED |
| S2-002 | p < 0.001 | Omnibus p-value | CERTIFIED |

### 3b. Pairwise Comparisons (Holm-corrected)

| ID | Comparison | CQS Δ | Cohen's d | 95% CI | p (Holm) | Eff. N | Status |
|----|------------|-------|-----------|--------|----------|--------|--------|
| S2-010 | Pragmatics vs Control | +0.539 | 1.440 | [0.421, 0.651] | < 0.001 | 36/39 | CERTIFIED |
| S2-011 | Pragmatics vs RAG | +0.385 | 0.922 | [0.256, 0.513] | < 0.001 | 32/39 | CERTIFIED |
| S2-012 | RAG vs Control | +0.154 | 0.546 | [0.072, 0.244] | 0.0017 | 30/39 | CERTIFIED |

### 3c. Per-Dimension Omnibus

| ID | Dimension | χ²(2) | p | Status |
|----|-----------|-------|---|--------|
| S2-020 | D1 (Accuracy) | 16.25 | < 0.001 | CERTIFIED |
| S2-021 | D2 (Completeness) | 14.59 | < 0.001 | CERTIFIED |
| S2-022 | D3 (Uncertainty) | 44.83 | < 0.001 | CERTIFIED |
| S2-023 | D4 (Clarity) | 29.36 | < 0.001 | CERTIFIED |
| S2-024 | D5 (Harm Avoidance) | 16.13 | < 0.001 | CERTIFIED |

### 3d. Per-Dimension Effect Sizes (Cohen's d)

| ID | Dimension | Prag vs Ctrl | Prag vs RAG | RAG vs Ctrl | Status |
|----|-----------|-------------|-------------|-------------|--------|
| S2-030 | D1 | 0.541 | 0.515 | 0.190 | CERTIFIED |
| S2-031 | D2 | 0.537 | 0.297 | 0.246 | CERTIFIED |
| S2-032 | D3 | 1.353 | 1.040 | 0.417 | CERTIFIED |
| S2-033 | D4 | 0.957 | 0.577 | 0.546 | CERTIFIED |
| S2-034 | D5 | 0.732 | 0.521 | 0.148 | CERTIFIED |

### 3e. Condition Means

| ID | Condition | CQS Mean | Status |
|----|-----------|----------|--------|
| S2-040 | Pragmatics | 1.5282 | CERTIFIED |
| S2-041 | RAG | 1.1436 | CERTIFIED |
| S2-042 | Control | 0.9897 | CERTIFIED |

### 3f. Stratum Analysis (Normal vs Edge)

Source: `results/v2_redo/stage2/analysis/stratum_analysis.md` + `.json`
Script: `src/eval/stratum_analysis.py`
SRS: VR-101, VR-102, VR-103

*Key finding: No overfit. Pragmatics effect is LARGER on normal queries (d=2.347) than edge (d=1.135). Edge-greater hypothesis not supported (p=0.987).*

#### Normal Queries (n=15)

| ID | Comparison | Δ CQS | Cohen's d | Wilcoxon p | Status |
|----|------------|-------|-----------|-----------|--------|
| SA-001 | Pragmatics vs Control | +0.707 | 2.347 | < 0.001 | COMPUTED |
| SA-002 | Pragmatics vs RAG | +0.580 | 1.436 | 0.0011 | COMPUTED |
| SA-003 | RAG vs Control | +0.127 | 0.458 | 0.1370 (ns) | COMPUTED |

*Power note: n=15 Wilcoxon power ~0.56 at d=0.5, ~0.94 at d=1.0. SA-003 underpowered for small effects.*

#### Edge Queries (n=24)

| ID | Comparison | Δ CQS | Cohen's d | Wilcoxon p | Status |
|----|------------|-------|-----------|-----------|--------|
| SA-010 | Pragmatics vs Control | +0.433 | 1.135 | < 0.001 | COMPUTED |
| SA-011 | Pragmatics vs RAG | +0.263 | 0.683 | 0.0041 | COMPUTED |
| SA-012 | RAG vs Control | +0.171 | 0.590 | 0.0024 | COMPUTED |

#### Between-Stratum (VR-103)

| ID | Comparison | Normal Δ | Edge Δ | ΔΔ (Edge−Normal) | p(Edge>Normal) | Status |
|----|------------|---------|--------|------------------|----------------|--------|
| SA-020 | Pragmatics vs Control | +0.707 | +0.433 | −0.273 | 0.9866 | COMPUTED |
| SA-021 | Pragmatics vs RAG | +0.580 | +0.263 | −0.318 | 0.9873 | COMPUTED |
| SA-022 | RAG vs Control | +0.127 | +0.171 | +0.044 | 0.3471 | COMPUTED |

### 3g. Efficiency Analysis

Source: `results/v2_redo/stage1/analysis/overhead_analysis.md` + `.json`
Script: `src/eval/overhead_analysis.py`
Note: Uses actual API token counts (input_tokens, output_tokens) per record.

*Key finding: Pragmatics has higher raw token overhead than RAG (+465% vs +307% over control), but delivers targeted context (21.8 of 36 items = 61% per query, API-served) vs RAG's fixed top-5 brute-force injection. Quality difference: pragmatics CQS 1.53 vs RAG 1.14.*

| ID | Metric | Control | RAG | Pragmatics | Status |
|----|--------|---------|-----|------------|--------|
| EFF-001 | Response file size (bytes) | 1,169,849 | 2,262,441 | 1,631,664 | COMPUTED |
| EFF-002 | Mean input tokens/query | 5,830 | 23,746 | 32,929 | COMPUTED |
| EFF-003 | Mean output tokens/query | 679 | 714 | 975 | COMPUTED |
| EFF-004 | Input overhead vs control | — | +307.3% | +464.8% | COMPUTED |
| EFF-005 | Mean tool calls/query | 3.5 | 3.3 | 4.0 | COMPUTED |
| EFF-006 | Mean retrieval context (RAG) | — | 16,026 chars | — | COMPUTED |
| EFF-007 | Mean guidance response (pragmatics) | — | — | 16,106 chars | COMPUTED |
| EFF-008 | Mean pragmatic items/query | — | — | 21.8 of 36 (61%) | COMPUTED |

---

## Section 4: Stage 3 — Fidelity & Auditability (CERTIFIED)

Source: `results/v2_redo/stage3/analysis/fidelity_summary.md` + `.json`
Script: `src/eval/fidelity_aggregate.py`
V&V: `src/eval/fidelity_qc.py` (exit 0, all 35 checks pass)
SRS: VR-091–096 (aggregate), VR-097–100 (QC)

### 4a. Overall Fidelity

| ID | Condition | Fidelity | Subst. Fidelity | Error Rate | Total Claims | Status |
|----|-----------|----------|-----------------|------------|-------------|--------|
| S3-001 | Control | 78.3% | 100.0% | 0.0% | 253 | CERTIFIED |
| S3-002 | RAG | 74.6% | 98.9% | 0.8% | 355 | CERTIFIED |
| S3-003 | Pragmatics | 91.2% | 99.7% | 0.3% | 353 | CERTIFIED |

*Note: Substantive fidelity, error rate, and claim counts are in fidelity_summary.md but not yet extracted to this registry. Fill from certified source.*

### 4b. Overall Auditability

| ID | Condition | Auditable | Partially | Unauditable | Subst. Claims | Status |
|----|-----------|-----------|-----------|-------------|---------------|--------|
| S3-010 | Control | 6.2% | 63.0% | 15.2% | 257 | CERTIFIED |
| S3-011 | RAG | 21.8% | 76.0% | 17.8% | 242 | CERTIFIED |
| S3-012 | Pragmatics | 29.5% | 51.8% | 18.7% | 278 | CERTIFIED |

*All values from `fidelity_summary.json` (certified source). Non-claims excluded from auditability denominators per VR-054.*

---

## Section 5: V1 vs V2 Reconciliation

These numbers are NOT cited in the paper. They document why V1 numbers differ from V2, per `talks/fcsm_2026/2026-02-21_v1_to_v2_redesign.md`.

| ID | Metric | V1 Value | V2 Value | Reason for Divergence | Status |
|----|--------|----------|----------|----------------------|--------|
| RC-001 | Pragmatics fidelity | 91.6% | 91.2% | Different Stage 1 responses (pre/post leakage fix) | DOCUMENTED |
| RC-002 | Pragmatics auditability | 72.8% | 29.5% | V1 measured treatment-only; V2 symmetric across conditions; different responses | DOCUMENTED |
| RC-003 | Control auditability | 8.1% | 6.2% | Different Stage 1 responses | DOCUMENTED |

---

## Section 5b: RAG Condition Parameters

Source: `src/eval/rag_retriever.py`, `results/rag_ablation/index/metadata.json`
Verified by: `verify_registry_counts.py`

| ID | Parameter | Value | Source | Status |
|----|-----------|-------|--------|--------|
| RAG-001 | Embedding model | all-MiniLM-L6-v2 (384-dim) | `rag_retriever.py` | COUNTABLE |
| RAG-002 | Index type | FAISS IndexFlatIP (cosine) | `rag_retriever.py` | COUNTABLE |
| RAG-003 | Top-k retrieval | 5 | `rag_retriever.py:27` | COUNTABLE |
| RAG-004 | Total chunks indexed | 311 | `results/rag_ablation/index/metadata.json` | COUNTABLE |
| RAG-005 | Source documents | 3 | `results/rag_ablation/index/metadata.json` | COUNTABLE |
| RAG-006 | Bootstrap iterations | 10,000 | `judge_config.yaml` (analysis section) | COUNTABLE |
| RAG-007 | Bootstrap seed | Not set (non-deterministic) | `judge_config.yaml` | COUNTABLE |

---

## Section 5c: Determinism Verification

Source: `results/rag_ablation/analysis/determinism_test_real.json`
Script: `scripts/test_determinism_real.py`
CC Task: `cc_tasks/2026-02-15_real_determinism_test.md`

| ID | Number | Description | Source | Status |
|----|--------|-------------|--------|--------|
| DET-001 | 39/39 | Queries with identical context retrieval across 2 replications + original | `determinism_test_real.json` | COUNTABLE |
| DET-002 | 0 | Mismatches (run1 vs run2) | `determinism_test_real.json` | COUNTABLE |
| DET-003 | 0 | Mismatches (run1 vs original Stage 1) | `determinism_test_real.json` | COUNTABLE |
| DET-004 | 100% | Deterministic reproducibility rate | DET-001 / SD-001 | COUNTABLE |

**What this proves:** Given identical topic parameters, the pragmatics retrieval layer returns identical context sets every time. The system is deterministic — no stochastic retrieval, no embedding drift, no random sampling. This is by design: topic→thread→context is a graph traversal, not a vector search.

---

## Section 5d: Study Design Derivation

Decision pedigree for key design parameters.

| ID | Parameter | Value | Derivation | Decision Record |
|----|-----------|-------|------------|----------------|
| DRV-001 | Battery size (n=39) | 39 | Paired Wilcoxon at d=0.5, α=0.05, power=0.80 requires ~35 pairs. Stratified: 15 normal + 24 edge. Constrained by Gemini 250/day rate limit (234 calls = 93.6% utilization) | DEC-4B-009, DEC-4B-021 |
| DRV-002 | Normal/edge split | 38%/62% | Equivalence testing (no-harm claim on normal) needs 15-20; superiority testing (edge cases) at d=0.8 needs 15-20. Edge oversampled because that's where pragmatics value-add is hypothesized | DEC-4B-009 |
| DRV-003 | Judge passes per comparison | 6 | 3 vendors × 2 orderings. 6→12 passes buys ~1% power — not worth cost. Bottleneck is N=39 queries, not judge noise | DEC-4B-021 |
| DRV-004 | Edge case oversampling rationale | 62% edge | Hypothesis is directional: pragmatics help on hard queries, neutral on easy. More power needed where effect matters. Not arbitrary. | DEC-4B-009 |

---

## Section 5e: Pending Analysis (CC Tasks Created)

| ID | Analysis | CC Task | Registry Section (after completion) |
|----|----------|---------|------------------------------------|
| PEND-001 | Stratum treatment effect (edge vs normal) | `cc_tasks/2026-02-21_stratum_analysis.md` | Section 3f: Stratum Analysis |
| PEND-002 | Token overhead comparison | `cc_tasks/2026-02-21_overhead_analysis.md` | Section 3g: Efficiency Analysis |

---

## Section 6: Derived / Interpretive Numbers

Numbers computed from certified data for narrative use (e.g., "X times higher"). These must trace to certified source numbers.

| ID | Statement | Derivation | Source IDs | Status |
|----|-----------|------------|------------|--------|
| DV-001 | "very large effect size" (d > 1.0) | Cohen's d = 1.440 for Prag vs Ctrl | S2-010 | CERTIFIED |
| DV-002 | "large effect size" (d > 0.8) | Cohen's d = 0.922 for Prag vs RAG | S2-011 | CERTIFIED |
| DV-003 | "medium effect size" (d > 0.5) | Cohen's d = 0.546 for RAG vs Ctrl | S2-012 | CERTIFIED |
| DV-004 | D3 largest effect | d = 1.353 Prag vs Ctrl, largest of D1–D5 | S2-032 | CERTIFIED |
| DV-005 | Fidelity gap Prag vs RAG | 91.2% - 74.6% = 16.6 pp | S3-003, S3-002 | CERTIFIED |
| DV-006 | Fidelity gap Prag vs Ctrl | 91.2% - 78.3% = 12.9 pp | S3-003, S3-001 | CERTIFIED |

---

## Section 7: Gaps — Numbers Needed But Not Yet Traceable

| ID | Description | Likely Source | Action Needed |
|----|-------------|--------------|---------------|
| ~~GAP-001~~ | ~~2,106 judge record count~~ | — | **CLOSED** → SD-006 COUNTABLE (2,106 confirmed, 0 parse failures) |
| ~~GAP-002~~ | ~~35 pragmatic item count~~ | — | **CLOSED** → PL-001 COUNTABLE (36 in compiled pack) |
| ~~GAP-003~~ | ~~47 staged item count~~ | — | **CLOSED** → PL-002 COUNTABLE (36 actual; 47 was untraced ghost number) |
| ~~GAP-004~~ | ~~Grounding compliance~~ | — | **CLOSED** → PL-004 COUNTABLE (39/39 pragmatics; 0/39 control/RAG correct by design per VR-025) |
| ~~GAP-005~~ | ~~Normal/edge split~~ | — | **CLOSED** → SD-009 COUNTABLE (38%/62%; SRS VR-010 corrected to match) |
| ~~GAP-006~~ | ~~Per-dimension RAG vs Ctrl d~~ | — | **CLOSED** → S2-030–034 filled from aggregate_statistics.json |
| ~~GAP-007~~ | ~~Substantive fidelity, error rates~~ | — | **CLOSED** → S3-001–003, S3-010–012 filled from fidelity_summary.json |
| ~~GAP-008~~ | ~~Bootstrap CI parameters~~ | — | **CLOSED** → 10,000 iterations (`judge_config.yaml analysis.bootstrap_iterations`); no seed documented in config |
| ~~GAP-009~~ | ~~RAG index parameters~~ | — | **CLOSED** → FAISS IndexFlatIP cosine, all-MiniLM-L6-v2 (384-dim), top-k=5 (`rag_retriever.py:27`), 311 chunks, 3 source docs (`results/rag_ablation/index/metadata.json`) |
| GAP-010 | Source document count and page count for pragmatics | Quarry provenance records | Methods section needs this |
| GAP-011 | Stratum treatment effect (edge vs normal) | CC task `2026-02-21_stratum_analysis.md` | **PENDING** → PEND-001 |
| GAP-012 | Token overhead per condition | CC task `2026-02-21_overhead_analysis.md` | **PENDING** → PEND-002 |
| GAP-013 | Pragmatics development procedure narrative | `docs/design/quarry_extraction_pipeline.md`, ADR-008, ADR-009 | Methods section needs creation story: extract → thread ID → curate → compile → embed in MCP |
| GAP-014 | API-driven architecture advantage | System design docs | Discussion section: packs are server-side MCP, centrally maintained, no client files, multi-vendor test bench |

---

## Maintenance Rules

1. **Adding a number:** Create entry with appropriate status. If PENDING/UNTRACED, add to Section 7 gaps.
2. **Promoting to CERTIFIED:** Requires V&V script in SRS Section 8.9 registry with exit 0.
3. **Promoting to COUNTABLE:** Requires deterministic source (file count, config value, YAML entry count). Document the exact command to reproduce.
4. **Citing in paper:** Reference by ID (e.g., "S2-010"). Section files in `paper/sections/` should use these IDs in comments to maintain traceability.
5. **Number changes:** If a certified number changes due to reanalysis, update here AND note the previous value in Section 5 (reconciliation) with reason.
