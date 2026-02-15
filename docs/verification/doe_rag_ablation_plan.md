# DOE Plan: RAG Ablation Experiment

## Experiment ID: EXP-RAG-001
## Status: PLANNING
## Start Date: 2026-02-15
## Deadline: 2026-03-01 (slides due)

---

## 1. Hypothesis

**H₀:** Section-level RAG on the same source documents produces equivalent CQS dimension scores to the bare LLM control condition.

**H₁:** RAG produces higher scores on some dimensions (likely D4 Definitions, possibly D2 Methodology) but NOT on D3 (Uncertainty) or D5 (Reproducibility).

**H₂ (the paper's claim):** Pragmatics >> RAG > Control on D3/D5, demonstrating that curated expert judgment adds value beyond document retrieval.

## 2. Experimental Design

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Design | Within-query paired comparison | Same 39 queries, matched to existing control |
| Conditions | RAG vs Control (pairwise) | Mirrors existing Pragmatics vs Control design |
| Queries | 39 (15 normal, 24 edge) | Same test battery as primary evaluation |
| Judge vendors | 3 (Anthropic, OpenAI, Google) | Same panel |
| Passes per vendor | 6 (3 control-first, 3 treatment-first) | Same counterbalancing |
| Total judge records | 702 (39 × 3 × 6) | Matches primary evaluation exactly |
| Rubric | CQS D1-D5 (D6 excluded per DEC-4B-023) | Same rubric |
| Fidelity check | Yes, Stage 3 on RAG responses | Equal treatment |
| Caller model | Same as primary eval (check judge_config.yaml) | Must match |

## 3. RAG Condition Specification

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunking | Section-level, ~600 tokens, 100 overlap | Reasonable default, deliberately untuned |
| Embedding | all-MiniLM-L6-v2 (384-dim) | Already in project |
| Index | FAISS IndexFlatIP, L2-normalized | Simplest possible |
| Retrieval | Top-5 chunks per query | Standard default |
| Injection | System prompt prepend as "Reference Materials" | How RAG actually works |
| Agent loop | None — single-shot completion | RAG doesn't use tools |
| Tool access | None | Fair comparison to control |

### Source Documents (from neo4j provenance)

| Doc ID | File | Role |
|--------|------|------|
| ACS-GEN-001 | `knowledge-base/source-docs/OtherACS/acs_general_handbook_2020.pdf` | Primary — Ch. 1,3,4,7,8,10,12 |
| ACS-DM-2024 | `knowledge-base/source-docs/census-methodology/acs_design_methodology_report_2024.pdf` | Primary |
| Census Geography | `knowledge-base/source-docs/OtherACS/acs_geography_handbook_2020.pdf` | Primary |
| ACS Accuracy | `knowledge-base/source-docs/OtherACS/ACS_Accuracy_of_Data_2023.pdf` | Secondary |
| Multiyear Accuracy | `knowledge-base/source-docs/OtherACS/MultiyearACSAccuracyofData2023.pdf` | Secondary |
| Understanding ACS | `knowledge-base/source-docs/OtherACS/Understanding and Using ACS Data_ What All Data Users Need to Know.pdf` | Secondary |

## 4. Output Locations

ALL outputs go to `results/rag_ablation/`. Nothing touches existing results.

```
results/
├── stage2_pragmatics_v_control/     ← Snapshot of existing analysis (Step 0)
│   ├── README.md
│   ├── effect_sizes.csv
│   ├── irr_scores.csv
│   ├── bias_diagnostics.csv
│   ├── preference_summary.csv
│   ├── stratified_effects.csv
│   ├── fidelity_summary.csv
│   ├── test_retest.csv
│   └── aggregate_report.md
├── rag_ablation/
│   ├── index/
│   │   ├── chunks.jsonl
│   │   ├── faiss_index.bin
│   │   ├── metadata.json
│   │   └── sources.txt
│   ├── stage1/
│   │   └── rag_responses.jsonl
│   ├── stage2/
│   │   ├── judge_scores_*.jsonl
│   │   └── checkpoints/
│   ├── stage3/
│   │   └── fidelity_results.jsonl
│   └── analysis/
│       ├── three_group_comparison.csv
│       ├── friedman_tests.csv
│       ├── posthoc_pairwise.csv
│       ├── rag_vs_control_effects.csv
│       ├── rag_fidelity.csv
│       ├── rag_preferences.csv
│       ├── rag_bias_diagnostics.csv
│       ├── rag_test_retest.csv
│       └── aggregate_report.md
```

## 5. QC Procedure

**Principle: CC executes, CC self-checks, human verifies.**

Each pipeline step that produces artifacts follows three layers:
1. **Execution** — CC runs the script
2. **Automated QC** — CC runs a QC script with pass/fail criteria, writes report
   to `qc_report.txt` alongside artifacts. CC stops on FAIL.
3. **Human inspection** — We review QC report and spot-check before next phase.

QC reports are committed for provenance. See lab notebook entry 2026-02-15 in
`talks/fcsm_2026/notes.md` for rationale (lesson learned from Phase 4B data
contamination where CC "fixed" a bug without ground-truth verification).

## 6. Execution Plan

### Phase A: Infrastructure (Day 1)
| Step | Task | CC Task | Depends On | Est. Time | Status |
|------|------|---------|------------|-----------|--------|
| A0 | Snapshot existing results to `stage2_pragmatics_v_control/` | Part of main CC task | — | 2 min | ☐ |
| A1 | Build RAG index from source documents | CC task Step 1 | A0 | 30 min | ☐ |
| A2 | Create RAG retriever module | CC task Step 2 | A1 | 15 min | ☐ |
| A3 | Add RAG condition to generate_responses.py | CC task Step 3 | A2 | 20 min | ☐ |

**Gate Check A:** Verify index has reasonable chunk count (expect 150-300 chunks from ~300 pages). Spot-check 3 retrieval queries manually — do the returned chunks seem relevant?

### Phase B: Data Generation (Day 1-2)
| Step | Task | CC Task | Depends On | Est. Time | Status |
|------|------|---------|------------|-----------|--------|
| B1 | Generate RAG responses for 39 queries | CC task Step 4 | A3 | 30 min + ~$3 API | ☐ |
| B2 | Manual spot-check: read 5 RAG responses vs control | Manual | B1 | 15 min | ☐ |

**Gate Check B:** Read NORM-001, GEO-002, SML-002, AMB-001, NORM-008 RAG responses. Do they cite handbook language? Do they have table IDs? (Expected: handbook language yes, table IDs no.) If RAG responses look identical to control, something is wrong with retrieval injection.

### Phase C: Judge Scoring (Day 2-3)
| Step | Task | CC Task | Depends On | Est. Time | Est. Cost |Status |
|------|------|---------|------------|-----------|-----------|-------|
| C1 | OpenAI judge: RAG vs Control | CC task Step 5 | B1 | 30 min | ~$4 | ☐ |
| C2 | Anthropic judge: RAG vs Control | CC task Step 5 | B1 | 30 min | ~$12 | ☐ |
| C3 | Google judge: RAG vs Control | CC task Step 5 | B1 | 20 min | ~$8 | ☐ |

**Gate Check C:** Verify 702 records, 0 parse failures, 234 per vendor. Check that presentation order counterbalancing is correct.

### Phase D: Fidelity (Day 3)
| Step | Task | CC Task | Depends On | Est. Time | Status |
|------|------|---------|------------|-----------|--------|
| D1 | Stage 3 fidelity check on RAG responses | CC task Step 6 | B1 | 20 min | ☐ |

**Gate Check D:** RAG auditability should be close to control's 8.1%, not treatment's 72.8%. If it's above 30%, investigate — the RAG chunks may be leaking table IDs from accuracy documents.

### Phase E: Analysis (Day 3-4)
| Step | Task | CC Task | Depends On | Est. Time | Status |
|------|------|---------|------------|-----------|--------|
| E1 | Build analyze_three_group.py | CC task Step 7 | C1-C3, D1 | 45 min | ☐ |
| E2 | Run analysis, generate CSVs and report | E1 | E1 | 5 min | ☐ |
| E3 | Review numbers, sanity check against hypotheses | Manual | E2 | 30 min | ☐ |

**Gate Check E:** The three-group table should tell a clear story. If RAG ≈ Pragmatics on any dimension, we have a problem. If RAG ≈ Control on all dimensions, the critique is dead but the experiment was overkill.

### Phase F: Documentation (Day 4)
| Step | Task | Depends On | Status |
|------|------|------------|--------|
| F1 | Update SRS with VR-080 through VR-083 | E3 | ☐ |
| F2 | Update rag_fallacy_thinking.md with actual numbers | E3 | ☐ |
| F3 | Create decision record DEC-RAG-001 | E3 | ☐ |
| F4 | Commit everything | F1-F3 | ☐ |

## 6. Analysis Plan

### Primary analysis: Three-group repeated-measures

Unit of analysis: query (n=39)
For each dimension D1-D5:
1. Compute query-level means for each condition (averaging across vendors and passes)
2. Friedman test across 3 conditions (nonparametric repeated-measures)
3. If Friedman p < 0.05: pairwise Wilcoxon signed-rank with Bonferroni correction (α = 0.05/3 = 0.0167)

### Secondary analyses (equal treatment to primary eval):
- Cohen's d (paired and independent) for RAG vs Control
- Inter-rater reliability (Krippendorff's α) for RAG vs Control scoring
- Position bias check
- Self-enhancement bias check
- Verbosity bias check  
- Test-retest reliability per pass-pair
- Judge preference rates (RAG vs Control)
- Stratified effects (normal vs edge cases)
- Fidelity/auditability comparison across all 3 conditions

### The money outputs:

**Table 1: Three-Group CQS Comparison**
| Dimension | Control M(SD) | RAG M(SD) | Pragmatics M(SD) | Friedman χ² | p |
|-----------|--------------|-----------|-------------------|-------------|---|

**Table 2: Pairwise Effect Sizes**
| Dimension | RAG > Ctrl d [CI] | Prag > RAG d [CI] | Prag > Ctrl d [CI] |
|-----------|-------------------|--------------------|--------------------|

**Table 3: Auditability**
| Metric | Control | RAG | Pragmatics |
|--------|---------|-----|------------|
| Auditable | 8.1% | [X]% | 72.8% |
| Fidelity | N/A | [X]% | 91.6% |

## 7. Decision Criteria

| Outcome | Interpretation | Paper Impact |
|---------|---------------|--------------|
| RAG ≈ Control on all dims | Documents in context don't help | Strongest: curation is essential |
| RAG > Control on D4, ≈ on D3/D5 | Retrieval helps definitions, not judgment | Expected: validates the category argument |
| RAG > Control on D3/D5 | Retrieval helps uncertainty/reproducibility | Weakens claim — but check fidelity |
| RAG ≈ Pragmatics | Curation unnecessary, retrieval sufficient | Problem — rethink contribution |

If RAG ≈ Pragmatics: look at fidelity. If RAG auditability is still low, pragmatics still
win on reproducibility even if judge scores are similar (judges may not penalize
non-auditability harshly enough).

## 8. Risks and Mitigations

| Risk | Probability | Mitigation |
|------|-------------|------------|
| RAG chunks contain table IDs from accuracy docs | Low | Check chunks manually before running |
| Judge scores inflated by Anthropic self-enhancement | Known | Report OpenAI+Google pooled as primary |
| RAG responses identical to control (retrieval fails) | Low | Gate Check B catches this |
| Cost overrun | Low | Budget ~$27 matching primary eval |
| Pipeline code breaks with new condition | Medium | Build incrementally with gate checks |
| Results don't clearly differentiate | Medium | Fidelity is the backstop metric |

## 9. Estimated Total Cost

| Component | Cost |
|-----------|------|
| Stage 1 RAG generation | ~$3 |
| Stage 2 OpenAI judge | ~$4 |
| Stage 2 Anthropic judge | ~$12 |
| Stage 2 Google judge | ~$8 |
| Stage 3 fidelity | ~$0.50 |
| **Total** | **~$27.50** |

---

## CC Task Location
`cc_tasks/2026-02-15_rag_ablation_condition.md`

## Key Files (will be created)
- `scripts/build_rag_index.py`
- `src/eval/rag_retriever.py`
- `src/eval/analyze_three_group.py`
- `results/rag_ablation/` (entire directory tree)
