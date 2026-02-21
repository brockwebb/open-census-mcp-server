# Numbers Registry — Publication Data Catalogue

**Purpose:** Single source of truth for every statistic cited in publication materials. Every number traces to a source file, computation script, SRS requirement, and V&V certification status.

**Rule:** No number appears in the paper, slides, or handout unless it has an entry here with status CERTIFIED or COUNTABLE. Numbers with status PENDING or UNTRACED must be resolved before citation.

**Last updated:** 2026-02-21

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
| SD-006 | 2,106 (2,103 usable) | Total Stage 2 judge records. **BACKFILL PENDING:** 3 Anthropic parse failures in rag_vs_pragmatics (AMB-003 pass 2, PER-001c passes 1&4). See `talks/fcsm_2026/2026-02-21_anthropic_parse_failure_gap.md`. CC task: `2026-02-21_backfill_anthropic_parse_failures.md`. After backfill: expect 2,106 all usable. | `results/v2_redo/stage2/*.jsonl` | N/A (count) | VR-041, VR-072 | verify_registry_counts.py | BLOCKED |
| SD-007 | 702 | Judge records per comparison (39 × 6 passes × 3 vendors) | `results/v2_redo/stage2/*.jsonl` | N/A (count) | VR-041 | verify_registry_counts.py | COUNTABLE |
| SD-008 | 5 | CQS dimensions scored (D1–D5) | `src/eval/judge_prompts.py` | N/A (design) | VR-037 | — | COUNTABLE |
| SD-009 | 38% / 62% | Normal (15) / edge case (24) split in battery. **NOTE:** SRS VR-010 claims 41%/59% — discrepancy. Actual: 15 normal, 24 edge (geo_edge:7, small_area:4, temporal:4, ambiguity:3, product_mismatch:3, persona:3) | `src/eval/battery/queries.yaml` | N/A (count) | verify_registry_counts.py | DISCREPANCY |
| SD-010 | 1 | Caller model (`claude-sonnet-4-5-20250929`) | `src/eval/judge_config.yaml` | N/A (config) | VR-021 | — | COUNTABLE |

---

## Section 2: Pragmatics Layer Parameters

| ID | Number | Description | Source File | Script | SRS Req | V&V | Status |
|----|--------|-------------|-------------|--------|---------|-----|--------|
| PL-001 | 36 | Curated pragmatic items in compiled ACS pack (36 context rows, 35 threads). **NOTE:** Previously cited as 35 — actual compiled pack has 36. | `packs/acs.db` (context table) | N/A (DB count) | verify_registry_counts.py | COUNTABLE |
| PL-002 | 47 | Staged pragmatic items (includes unpromoted) | `staging/acs/` | — | — | — | UNTRACED |
| PL-003 | — | Source documents for pragmatic extraction | Quarry pipeline / provenance | — | VR-081 | — | PENDING |
| PL-004 | 100% | Methodology compliance (39/39 grounding gate) — pragmatics condition. Control and RAG compliance TBD from verify script. | `results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl` | verify_registry_counts.py | VR-029 | — | PENDING |

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
| S2-030 | D1 | 0.541 | 0.515 | — | CERTIFIED |
| S2-031 | D2 | 0.537 | 0.297 | — | CERTIFIED |
| S2-032 | D3 | 1.353 | 1.040 | — | CERTIFIED |
| S2-033 | D4 | 0.957 | 0.577 | — | CERTIFIED |
| S2-034 | D5 | 0.732 | 0.521 | — | CERTIFIED |

### 3e. Condition Means

| ID | Condition | CQS Mean | Status |
|----|-----------|----------|--------|
| S2-040 | Pragmatics | 1.5282 | CERTIFIED |
| S2-041 | RAG | 1.1436 | CERTIFIED |
| S2-042 | Control | 0.9897 | CERTIFIED |

---

## Section 4: Stage 3 — Fidelity & Auditability (CERTIFIED)

Source: `results/v2_redo/stage3/analysis/fidelity_summary.md` + `.json`
Script: `src/eval/fidelity_aggregate.py`
V&V: `src/eval/fidelity_qc.py` (exit 0, all 35 checks pass)
SRS: VR-091–096 (aggregate), VR-097–100 (QC)

### 4a. Overall Fidelity

| ID | Condition | Fidelity | Subst. Fidelity | Error Rate | Total Claims | Status |
|----|-----------|----------|-----------------|------------|-------------|--------|
| S3-001 | Control | 78.3% | — | — | — | CERTIFIED |
| S3-002 | RAG | 74.6% | — | — | — | CERTIFIED |
| S3-003 | Pragmatics | 91.2% | — | — | — | CERTIFIED |

*Note: Substantive fidelity, error rate, and claim counts are in fidelity_summary.md but not yet extracted to this registry. Fill from certified source.*

### 4b. Overall Auditability

| ID | Condition | Auditable | Partially | Unauditable | Subst. Claims | Status |
|----|-----------|-----------|-----------|-------------|---------------|--------|
| S3-010 | Control | 6.2% | — | — | — | CERTIFIED |
| S3-011 | RAG | 21.8% | — | — | — | CERTIFIED |
| S3-012 | Pragmatics | 29.5% | — | — | — | CERTIFIED |

*Note: Partial/unauditable rates and substantive claim counts in fidelity_summary.md. Fill from certified source.*

---

## Section 5: V1 vs V2 Reconciliation

These numbers are NOT cited in the paper. They document why V1 numbers differ from V2, per `talks/fcsm_2026/2026-02-21_v1_to_v2_redesign.md`.

| ID | Metric | V1 Value | V2 Value | Reason for Divergence | Status |
|----|--------|----------|----------|----------------------|--------|
| RC-001 | Pragmatics fidelity | 91.6% | 91.2% | Different Stage 1 responses (pre/post leakage fix) | DOCUMENTED |
| RC-002 | Pragmatics auditability | 72.8% | 29.5% | V1 measured treatment-only; V2 symmetric across conditions; different responses | DOCUMENTED |
| RC-003 | Control auditability | 8.1% | 6.2% | Different Stage 1 responses | DOCUMENTED |

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
| GAP-001 | 2,106 judge record count | `wc -l` on Stage 2 JSONL files | Verify count, add to SD-006 |
| GAP-002 | 35 pragmatic item count | SQLite pack or staging YAML count | Verify count, add to PL-001 |
| GAP-003 | 47 staged item count | `ls staging/acs/*.yaml \| wc -l` or similar | Verify or remove if wrong |
| GAP-004 | 39/39 grounding compliance | Stage 1 response analysis | Need script or manual verification |
| GAP-005 | Normal/edge split percentages | Category counts in queries.yaml | Count and compute |
| GAP-006 | Per-dimension RAG vs Ctrl effect sizes | aggregate_statistics.md | Extract — may already be in certified output |
| GAP-007 | Substantive fidelity, error rates, claim counts | fidelity_summary.md | Extract — already in certified output, just not registered |
| GAP-008 | Bootstrap CI parameters (10,000 iterations, seed) | judge_config.yaml analysis section | Extract from config |
| GAP-009 | RAG index parameters (chunk count, embedding model, top-k) | `results/rag_ablation/index/` + `rag_retriever.py` | Document for methods section |
| GAP-010 | Source document count and page count for pragmatics extraction | Quarry pipeline / provenance records | Need to trace |

---

## Maintenance Rules

1. **Adding a number:** Create entry with appropriate status. If PENDING/UNTRACED, add to Section 7 gaps.
2. **Promoting to CERTIFIED:** Requires V&V script in SRS Section 8.9 registry with exit 0.
3. **Promoting to COUNTABLE:** Requires deterministic source (file count, config value, YAML entry count). Document the exact command to reproduce.
4. **Citing in paper:** Reference by ID (e.g., "S2-010"). Section files in `paper/sections/` should use these IDs in comments to maintain traceability.
5. **Number changes:** If a certified number changes due to reanalysis, update here AND note the previous value in Section 5 (reconciliation) with reason.
