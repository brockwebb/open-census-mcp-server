# Lab Notes — Anthropic Parse Failure Gap Discovery

**Date:** 2026-02-21
**Severity:** Data integrity — 3 unusable judge records in production dataset

---

## Discovery

During numbers registry construction, programmatic verification of `results/v2_redo/stage2/rag_vs_pragmatics_20260216_092144.jsonl` revealed 3 records with `preference: parse_failed`:

| query_id | pass_number | vendor | 
|----------|-------------|--------|
| AMB-003 | 2 | Anthropic |
| PER-001c | 1 | Anthropic |
| PER-001c | 4 | Anthropic |

## What Happened

1. **Feb 16:** rag_vs_pragmatics production run completed. QC noted "3 Anthropic parse failures (1.3%) — records stored with `preference: parse_failed`" in `talks/fcsm_2026/2026-02-16_stage2_rag_vs_pragmatics_production.md`. Documented but not flagged for backfill.

2. **Feb 18-19:** control_vs_pragmatics had a different issue — 3 missing Google records (not parse failures, but records that were never generated). These were backfilled on Feb 19 from a separate targeted run, merged into the main JSONL.

3. **Feb 19:** Final aggregate analysis ran with `parse failures: 3` noted in output. The `aggregate_analysis.py` script excludes parse_failed records per VR-072, so the 3 records were silently dropped from all statistical computations.

4. **Feb 21:** Numbers registry verification caught the gap. The 3 parse failures were never backfilled because the Feb 19 backfill effort focused on the control_vs_pragmatics Google gap, which was the blocking issue at the time.

## Impact

- AMB-003 has 5/6 Anthropic passes (missing pass 2) in rag_vs_pragmatics
- PER-001c has 4/6 Anthropic passes (missing passes 1 and 4) in rag_vs_pragmatics  
- `aggregate_analysis.py` computes query-level medians across available passes, so these queries have slightly less Anthropic representation
- Statistical impact likely negligible (3/2106 = 0.14%) but the principle is violated: we claimed 702 usable records per comparison

## Corrective Action

CC task `2026-02-21_backfill_anthropic_parse_failures.md` created to:
1. Re-run Anthropic judge on the 3 specific query/pass combinations
2. Remove parse_failed records, merge backfill
3. QC verification (0 parse failures)
4. Re-run aggregate analysis
5. Update numbers registry if any certified values shift

## Root Cause

No systematic process to flag and track parse failures for backfill. The QC script (VR-072) reports them but doesn't create follow-up tasks. The Feb 19 backfill was triggered by a different failure mode (missing records, not parse failures) and didn't sweep for other gaps.

## Prevention

The `verify_registry_counts.py` V&V script (CC task `2026-02-21_verify_registry_counts.md`) now checks for parse failures as part of SD-006 verification. Future runs will catch this class of issue programmatically.
