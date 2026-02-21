# Numbers Registry Verification Report

**Generated:** 2026-02-21T09:48:33.689207
**Script:** src/eval/verify_registry_counts.py
**Reproduce:** `python -m src.eval.verify_registry_counts`

## Study Design Parameters

| ID | Claimed | Verified | Source | Status |
|----|---------|----------|--------|--------|
| SD-001 | 39 queries | 39 | src/eval/battery/queries.yaml | PASS |
| SD-006 | 2,106 records | 2106 | results/v2_redo/stage2/*.jsonl | PASS |
| SD-007 | 702/comparison | 702 (expected 234) | derived from SD-006 | PASS |
| SD-009 | 41%/59% | 38.5%/61.5% | src/eval/battery/queries.yaml | DISCREPANCY |

### SD-009 Category Breakdown
- ambiguity: 3
- geographic_edge: 7
- normal: 15
- persona_8th_grader: 1
- persona_city_planner: 1
- persona_journalist: 1
- product_mismatch: 3
- small_area: 4
- temporal: 4

### SD-006 Per-File Breakdown
- control_vs_pragmatics_20260218_065924.jsonl: 702 records (0 parse failures)
- control_vs_rag_20260217_083951.jsonl: 702 records (0 parse failures)
- rag_vs_pragmatics_20260216_092144.jsonl: 702 records (0 parse failures)

## Pragmatics Layer

| ID | Claimed | Verified | Source | Status |
|----|---------|----------|--------|--------|
| PL-001 | 36 items | 36 context, 35 threads | packs/acs.db (context table) | PASS |
| PL-002 | 47 staged | 36 | staging/acs/*.json (excluding manifest.json) | DISCREPANCY (got 36) |
| PL-004 | 39/39 (100%) | 39/39 (100.0%) | results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl | PASS |

### PL-001 Pack Inheritance
- acs: 36 items
- census: 1 items
- general: 1 items
- Total with inheritance: 38

### PL-002 Staged Items Per File
- break_in_series.json: 3
- comparison.json: 3
- disclosure_avoidance.json: 3
- dollar_values.json: 1
- geographic_equivalence.json: 2
- geography.json: 4
- group_quarters.json: 2
- independent_cities.json: 1
- margin_of_error.json: 4
- nonresponse.json: 2
- period_estimate.json: 1
- population_controls.json: 1
- population_threshold.json: 3
- release_schedule.json: 1
- residence_rules.json: 1
- sampling.json: 1
- suppression.json: 1
- threshold.json: 2

### PL-004 Grounding Compliance Per Condition
- Pragmatics: 39/39
- Control: 0/39
- Rag: 0/39

## Config Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Bootstrap iterations | 10000 | src/eval/judge_config.yaml (analysis section) |
| Bootstrap seed | NOT FOUND | src/eval/judge_config.yaml (analysis section) |

## GAP-009: RAG Index Files

- chunks.jsonl
- metadata.json
- sources.txt
- qc_report.txt
- faiss_index.bin

Metadata: {
  "extraction_method": "docling_hierarchical_chunker",
  "max_chunk_tokens": 2000,
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "n_chunks": 311,
  "n_source_docs": 3,
  "index_type": "FAISS IndexFlatIP (cosine similarity)",
  "build_date": "2026-02-15T13:53:27.744526",
  "content_type_breakdown": {
    "text": 311
  },
  "note": "Same extraction as quarry pipeline (Docling). See scripts/quarry/chunk.py"
}
