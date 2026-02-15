# Stage 3 Pipeline Fidelity Check - Implementation Summary
**Date:** 2026-02-13
**Status:** Implemented and tested

## Files Created

1. **`src/eval/fidelity_prompts.py`** - Verification prompts
   - Treatment verification: Extract and verify claims against tool data
   - Control auditability: Classify claim specificity

2. **`src/eval/fidelity_check.py`** - Main pipeline (492 lines)
   - Async LLM calls with retry logic
   - Incremental checkpointing to JSONL
   - Summary statistics computation
   - Per-category breakdown

3. **`src/eval/judge_config.yaml`** - Updated with fidelity section
   - Model: gpt-5-mini-2025-08-07
   - Temperature: 1.0 (required for this model)
   - Rate limiting: 0.5s delay

4. **`results/stage3/`** - Output directory created

## Test Results (3 Queries)

### Control Auditability: ✅ Working Perfectly

```
Total claims: 35
Auditable: 0 (0.0%)
Partially auditable: 9
Unauditable: 18
Non-claims: 8
```

**Sample classifications (NORM-004):**
- **Partially auditable**: "38.4% of NYC residents aged 25+ have bachelor's degree" (has value, geography, vintage but no table code)
- **Unauditable**: "reflecting NYC's role as educational hub" (interpretive, no data source)
- **Non-claim**: "These figures are estimates with margins of error" (methodological note)

The classifier correctly:
- Distinguishes specific claims from methodological context
- Identifies missing identifiers (table codes)
- Recognizes partially auditable claims with some but not all required metadata

### Treatment Fidelity: ⚠️ Needs Debugging

All 3 queries failed JSON parsing:
```
Fidelity LLM error: Expecting value: line 1 column 1 (char 0)
```

**Likely causes:**
1. LLM returning empty response (check token limits)
2. Tool data formatting overwhelming the prompt
3. JSON mode not working with gpt-5-mini

**Next steps for debugging:**
- Add raw response capture before JSON parsing
- Check if prompt exceeds model context window
- Try with different model (gpt-5.2 or claude-sonnet)
- Simplify tool data formatting

## Architecture

### Configuration (SRS C-006 compliant)
- All parameters in YAML (no hardcoded values)
- Paths, model, temperature, retries all configurable
- Follows judge_pipeline.py pattern

### Checkpointing
- Writes each result immediately after processing
- On restart, skips already-completed queries
- Append-only JSONL for durability

### Output Format
```json
{
  "query_id": "NORM-005",
  "query_text": "...",
  "category": "normal",
  "timestamp": "ISO8601",
  "treatment_fidelity": {
    "has_data": true,
    "claims": [...],
    "summary": {
      "total_claims": 6,
      "matched": 5,
      "calculation_correct": 1
    }
  },
  "control_auditability": {
    "claims": [...],
    "summary": {
      "total_claims": 4,
      "auditable": 0,
      "partially_auditable": 1
    }
  }
}
```

## CLI Usage

```bash
# Test run (first 3 queries)
python -m eval.fidelity_check --batch 3

# Full run (all 39 queries)
python -m eval.fidelity_check

# Custom config/input
python -m eval.fidelity_check --config path/to/config.yaml --input path/to/stage1.jsonl
```

## Key Design Decisions

### Why gpt-5-mini?
- Lightweight, fast, cost-effective for structured extraction
- JSON mode for reliable parsing
- Sufficient for claim extraction (doesn't need reasoning depth)

### Why temperature=1.0?
- Model requirement (gpt-5-mini only supports default temperature)
- Acceptable for extraction tasks (not generating creative content)

### Why separate prompts for treatment vs control?
- Different verification tasks:
  - Treatment: Compare against ground truth (tool data)
  - Control: Classify auditability (no ground truth available)
- Different output schemas
- Cleaner separation of concerns

## Integration with Evaluation Pipeline

**Stage 1** (harness.py) → control/treatment responses
**Stage 2** (judge_pipeline.py) → LLM judge scores on 6 dimensions
**Stage 3** (fidelity_check.py) → Automated groundedness verification
**Stage 4** → Statistical analysis and reporting

Stage 3 provides:
- Objective fidelity metric (% claims matched to tool data)
- Control baseline for comparison (what's auditable without tools)
- Automated alternative to D6 "Groundedness" rubric

## Production Readiness

✅ **Ready:**
- Control auditability classification
- Configuration management
- Checkpointing and error handling
- Summary statistics
- CLI interface

⚠️ **Needs work:**
- Treatment verification JSON parsing
- Error diagnostics (capture raw LLM responses)
- Prompt optimization for large tool data
- Model selection testing

## Next Steps

1. Debug treatment verification JSON parsing
2. Add raw response logging for failed parses
3. Test with alternative models (gpt-5.2, claude-sonnet)
4. Run full 39-query evaluation after fix
5. Compare fidelity scores to D6 judge scores
6. Document in DEC-4B-023 decision log
