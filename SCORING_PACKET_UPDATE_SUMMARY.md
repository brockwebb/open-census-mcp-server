# Manual Scoring Packet Update to v3 - Summary
**Date:** 2026-02-13
**Task:** Update manual calibration packet from v2 (6-dimension) to v3 (5-dimension)

## Changes Made

### 1. Updated `docs/test/cqs_manual_scoring_packet.md`

#### Header Updates
- Date: 2026-02-12 → **2026-02-13**
- Battery: cqs_responses_20260212_184334.jsonl → **cqs_responses_20260213_091530.jsonl**

#### Rubric Changes
- Changed "six CQS dimensions" → **"five CQS dimensions"**
- **Removed D6 (Groundedness)** from dimensions table
- **Added Pipeline Fidelity note:**
  > **Note:** Groundedness/faithfulness (formerly D6) is measured separately via
  > automated Pipeline Fidelity verification, not by human raters. This metric
  > compares response claims against API tool call logs and is reported independently.

#### Principle Updates
- **Removed:** "D6 = 0 is a gate failure" principle
- Renumbered remaining principles (now 1-3 instead of 1-4)

#### Scoring Tables (18 tables updated)
- **Removed D6 row** from all scoring tables (9 queries × 2 responses each)
- Changed **Total from /12 → /10** in all tables
- All tables now show only D1-D5

#### Response Content (9 queries replaced)
Replaced all response pairs with v3 data from Stage 1 validation run:

| Query | A | B | Notable Changes |
|-------|---|---|----------------|
| NORM-001 | treatment | control | Updated ACS 5-year data |
| NORM-008 | treatment | control | Updated unemployment data |
| NORM-015 | control | treatment | Updated education data |
| GEO-006 | treatment | control | Updated geographic comparison |
| SML-001 | treatment | control | Updated small-area data |
| **TMP-002** | **treatment** | **control** | **CRITICAL: Was truncated fragment in v2, now complete response** |
| MIS-002 | treatment | control | Updated misalignment case |
| AMB-002 | treatment | control | Updated ambiguous query |
| PER-001a | control | treatment | Still has Bozeman geography bug (documented) |

**TMP-002 Fix Verified:**
- v2: "Good! Now let me get the margins of error..." (72 chars - fragment)
- v3: "Excellent! Now I have comprehensive data..." (4,640 chars - complete)

### 2. Updated `docs/test/scoring_answer_key.txt`

**Added metadata:**
```
RUBRIC VERSION: v3 (5-dimension CQS, D1-D5)
STAGE 1 DATA: cqs_responses_20260213_091530.jsonl
DATE GENERATED: 2026-02-13

NOTES:
- D6 (Groundedness) removed from human scoring
- Total score per response: /10 (was /12 in v2)

KNOWN ISSUES:
- PER-001a treatment: Reports ~117K for Bozeman city (actual ~53K)
  This is Gallatin County data. Known FIPS resolution bug in MCP tool.
```

**Preserved:**
- Random seed: 42
- All A/B assignments unchanged (same randomization)

## Verification Results

### ✅ All Checks Pass

```
D6 occurrences: 1 (Pipeline Fidelity note only)
/10 occurrences: 18 (9 queries × 2 responses)
/12 occurrences: 0 (all removed)
```

### ✅ Critical Fixes Verified

**TMP-002 Response A:**
- Now contains complete health insurance comparison
- Has detailed data tables with 2019 vs 2020 ACS
- No longer a truncated fragment

**PER-001a Known Issue:**
- Documented in answer key
- Geography bug still present (expected - MCP tool issue, not harness)
- Raters will be aware of the issue

### ✅ Structural Integrity

- All 9 queries present and complete
- All scoring tables have correct 5-dimension structure
- No D6 references except in explanatory note
- All totals correctly show /10
- Answer key matches packet structure

## Files Modified

1. `docs/test/cqs_manual_scoring_packet.md` - Updated with v3 rubric and responses
2. `docs/test/scoring_answer_key.txt` - Updated with version info and known issues
3. Created `update_scoring_packet.py` - Automation script (can be removed after review)

## Files NOT Modified (As Required)

- ✅ `src/eval/judge_prompts.py` - LLM judges still score D6 for data retention
- ✅ `src/eval/judge_config.yaml` - D6 kept in dimensions list for backward compat
- ✅ `results/*` - No result files touched

## Impact

### For Manual Raters
- Simpler scoring: 5 dimensions instead of 6
- Total score /10 instead of /12
- D6 (groundedness) handled automatically - no subjective judgment needed
- All responses are complete (no truncated fragments)

### For Statistical Analysis
- Human scores (D1-D5) directly comparable to LLM judge scores
- D6 scores still available from LLM judges for comparison to automated fidelity
- Clean separation: subjective quality (D1-D5) vs objective groundedness (automated)

### For Reproducibility
- All responses traceable to specific JSONL file with timestamp
- Known issues documented
- Same random seed ensures A/B assignments are reproducible

## Next Steps

After manual scoring:
1. Compare manual D1-D5 scores to LLM judge D1-D5 scores
2. Compare manual D6-equivalent intuitions to automated Pipeline Fidelity scores
3. Analyze if removing D6 from composite changes overall score distribution
4. Document in Phase 4B decision logs

## Automation Script

Created `update_scoring_packet.py` for systematic transformation:
- Loads v3 JSONL data
- Maps responses to A/B using answer key
- Updates all scoring tables (removes D6, changes totals)
- Replaces response content
- Updates header and metadata
- Adds Pipeline Fidelity note

Can be deleted after verification or kept for future updates.
