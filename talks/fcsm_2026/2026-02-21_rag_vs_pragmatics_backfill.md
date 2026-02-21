# Lab Note — rag_vs_pragmatics Anthropic Parse Failure Backfill

**Date:** 2026-02-21
**Task ref:** cc_tasks/2026-02-21_backfill_anthropic_parse_failures.md

---

## What

Backfilled 3 Anthropic parse failures in `results/v2_redo/stage2/rag_vs_pragmatics_20260216_092144.jsonl`.

| query_id | pass_number | vendor |
|----------|-------------|--------|
| AMB-003 | 2 | anthropic |
| PER-001c | 1 | anthropic |
| PER-001c | 4 | anthropic |

## Why These Were Missing

The Feb 16 rag_vs_pragmatics run completed 702 records but 3 Anthropic judges returned unparseable JSON responses. These were recorded as `preference: parse_failed` and excluded from analysis.

The Feb 19 backfill effort (focused on Google/control_vs_pragmatics) did not address these Anthropic failures. This task was the follow-up.

## Method

1. Removed the 3 parse_failed entries from the checkpoint (`judge_checkpoint_rag_vs_pragmatics.json`): 702 → 699 entries.
2. Removed the 3 parse_failed records from the canonical JSONL: 702 → 699 records.
3. Re-ran pipeline with `--anthropic --comparison rag_vs_pragmatics`. Pipeline identified exactly 3 unchecked combinations and processed them all successfully (3/3 parse_success=True).
4. New run produced `rag_vs_pragmatics_20260221_094023.jsonl` (3 records). Appended to canonical JSONL: 699 + 3 = 702 records.
5. Removed stale 3-record run file (records now in canonical JSONL).
6. Verified canonical JSONL: 702 records, 0 parse failures. PASS.

## Impact on Aggregate Numbers

Zero. The 3 parse_failed records were already excluded from all prior aggregate analysis. Replacing them with valid scores does not change query-level CQS values (each query has sufficient coverage from the other 5 judge × pass combinations that were successful). Re-running `aggregate_analysis.py` confirmed numbers are identical:

| Metric | Before | After |
|--------|--------|-------|
| Control mean CQS | 0.9897 | 0.9897 |
| RAG mean CQS | 1.1436 | 1.1436 |
| Pragmatics mean CQS | 1.5282 | 1.5282 |
| Friedman χ²(2) | 42.01 | 42.01 |
| pragmatics vs control d | 1.440 | 1.440 |
| pragmatics vs rag d | 0.922 | 0.922 |
| rag vs control d | 0.546 | 0.546 |

`numbers_registry.md` not updated (no change).

## QC

`python -m src.eval.qc_stage2 --file rag_vs_pragmatics_20260216_092144.jsonl` → PASS
702 records, 0 parse failures, balanced ordering (351/351), balanced vendors (234/234/234), all structural checks passed.
