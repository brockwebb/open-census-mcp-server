# Judge Pipeline Implementation Summary

## Implementation Complete ✓

All Stage 2 judge scoring pipeline components have been implemented per `TASK_judge_pipeline.md`.

### Files Created

```
src/eval/
├── judge_config.yaml       # Multi-vendor judge configuration
├── judge_prompts.py        # CQS rubric prompt templates
├── judge_pipeline.py       # Main orchestration & API callers
├── judge_analysis.py       # Statistical analysis (§6B metrics)
└── models.py               # Updated with DimensionScore, JudgeRecord
```

## Architecture

### 1. Configuration (`judge_config.yaml`)

**Judges configured:**
- **Anthropic:** `claude-opus-4-5-20251101` (temperature=0.0)
- **OpenAI:** `gpt-5.2` (no temperature param)
- **Google:** `gemini-3-pro-preview` (temperature=1.0)

**Pipeline settings:**
- Random seed: 42 (reproducibility)
- Position bias mode: both orderings
- Test-retest count: 10 queries
- Checkpoint interval: 5 tasks
- Max tokens: 4096

**Expected output:**
- Base: 39 queries × 3 judges × 2 orderings = 234 records
- Test-retest: 10 queries × 3 judges × 2 orderings = 60 additional
- **Total: 294 records** (if all succeed)

### 2. Prompts (`judge_prompts.py`)

Embeds complete CQS rubric with:
- All 6 dimensions (D1-D6) with detailed scoring criteria
- General scoring principles (informed refusal, explanation, redirection)
- Structured JSON output format
- Confidence ratings (1-5 scale) per dimension

**Key features:**
- Judge sees query + two responses (A and B)
- Judge does NOT know which is control/treatment
- Scores each response independently on 0-1-2 scale
- Provides reasoning and overall preference

### 3. Pipeline (`judge_pipeline.py`)

**Main loop:**
```python
For each query_pair:
    For each judge (anthropic, openai, google):
        For each ordering (control_first, treatment_first):
            1. Build prompt with A/B randomization
            2. Call judge API
            3. Parse JSON response
            4. Map A/B scores back to control/treatment
            5. Write JudgeRecord to JSONL
            6. Checkpoint progress
```

**API callers** (adapted from barrier_pipeline.py pattern):
- `call_anthropic()` - Anthropic SDK with retry
- `call_openai()` - OpenAI SDK with conditional temperature
- `call_google()` - Google genai SDK with JSON response mode

**Robust JSON parsing:**
1. Direct `json.loads()`
2. Extract from markdown code blocks
3. Regex extraction of JSON object
4. Validation of expected structure

**Checkpointing:**
- Saves set of completed (query_id, judge, ordering) tuples
- Resume capability after interruption
- Checkpoint every N tasks (configurable)

**Test-retest subset:**
- First 10 queries (or configured IDs)
- Each judge runs twice with same ordering
- Enables ICC computation for reliability

### 4. Analysis (`judge_analysis.py`)

Implements ALL metrics from `test_plan/06b_statistical_analysis_plan.md`:

**§6B.3: Inter-rater Agreement**
- Krippendorff's α (ordinal) per dimension
- Fleiss' κ per dimension
- Cohen's κ (all pairwise)
- Percent agreement per dimension

**§6B.4: Bias Diagnostics**
- Position bias: swap consistency rate, per-dimension paired test
- Self-enhancement: per-vendor mean CQS, self-enhancement ratio
- Leniency/severity: per-judge mean CQS range

**§6B.5: Treatment Effects**
- Wilcoxon signed-rank test (total and per-dimension)
- Cohen's d (paired)
- Rank-biserial correlation
- Mean differences control vs treatment

**§6B.6: Reliability**
- Cronbach's α across dimensions (internal consistency)
- Test-retest ICC (placeholder - requires pairing logic)
- Confidence calibration (placeholder - requires ground truth)

**Outputs:**
- `results/stage2/analysis/analysis_report.json` - All metrics in JSON
- `results/stage2/analysis/summary_tables.md` - Publication-ready tables

### 5. Data Models (`models.py`)

Added two new classes:

```python
class DimensionScore(BaseModel):
    score: int  # 0, 1, or 2
    confidence: int  # 1-5
    reasoning: str

class JudgeRecord(BaseModel):
    query_id: str
    judge_model: str
    judge_vendor: str
    presentation_order: str
    scores_response_a: dict[str, DimensionScore]
    scores_response_b: dict[str, DimensionScore]
    preference: str
    preference_reasoning: str
    response_a_label: str  # "control" or "treatment"
    response_b_label: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    timestamp: datetime
    run_id: str
    raw_response: str
    parse_success: bool
    is_retest: bool = False
```

## Dependencies

```bash
# Install required packages
pip install anthropic openai google-generativeai krippendorff scipy matplotlib seaborn pyyaml
```

Or use conda environment:

```bash
conda install -c conda-forge scipy matplotlib seaborn pyyaml
pip install anthropic openai google-generativeai krippendorff
```

## Usage

### Run Judge Pipeline

```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python -m eval.judge_pipeline
```

**Expected runtime:** ~2-3 hours (294 API calls × 3-5 seconds each + rate limiting)

**Output:**
- `results/stage2/judge_scores_YYYYMMDD_HHMMSS.jsonl`
- Checkpoint files in `results/stage2/checkpoints/`

### Run Analysis

```bash
/opt/anaconda3/envs/census-mcp/bin/python -m eval.judge_analysis results/stage2/judge_scores_YYYYMMDD_HHMMSS.jsonl
```

**Output:**
- `results/stage2/analysis/analysis_report.json`
- `results/stage2/analysis/summary_tables.md`

## Verification

After pipeline completes:

```bash
# 1. Check record count
wc -l results/stage2/judge_scores_*.jsonl
# Expected: ~294 lines (234 base + 60 retest)

# 2. Check parse success rate
python3 -c "
import json
records = []
with open('results/stage2/judge_scores_*.jsonl') as f:
    for line in f:
        records.append(json.loads(line))

parse_success = sum(1 for r in records if r['parse_success'])
print(f'Parse success: {parse_success}/{len(records)} ({parse_success/len(records)*100:.1f}%)')
"
# Expected: >95%

# 3. Check all judges produced scores
python3 -c "
import json, pandas as pd
records = []
with open('results/stage2/judge_scores_*.jsonl') as f:
    for line in f:
        records.append(json.loads(line))

df = pd.DataFrame(records)
print('Records per judge:')
print(df['judge_vendor'].value_counts())
"
# Expected: ~98 per judge (anthropic, openai, google)
```

## Implementation Notes

### Design Decisions

1. **Position bias mitigation:** Every query scored in both orderings (control_first, treatment_first)
2. **Reproducibility:** Seeded RNG (seed=42) for A/B assignment
3. **Checkpointing:** Resume capability for long-running pipeline
4. **Robust parsing:** Multiple fallback strategies for malformed JSON
5. **Test-retest:** Separate runs for first 10 queries to measure reliability

### Adapted Patterns

From `~/Documents/GitHub/federal-survey-concept-mapper/`:

- **barrier_pipeline.py:** Multi-vendor API callers with exponential backoff retry
- **stats.py:** Cohen's κ, Fleiss' κ, Krippendorff's α, ICC, Cronbach's α

### Known Limitations

1. **Test-retest ICC:** Placeholder implementation - requires proper test/retest pairing logic
2. **Confidence calibration:** Requires ground truth scores or consensus baseline
3. **Verbosity bias:** Requires Stage 1 response lengths (not currently stored in JudgeRecord)
4. **Google token counts:** Estimated (4 chars/token) since Gemini API doesn't return counts

### Next Steps (Optional Enhancements)

1. Add visualization plots:
   - Position bias by judge
   - Verbosity scatter (length vs CQS)
   - Vendor bias distributions
   - Treatment effect paired plots
   - Dimension heatmaps
   - Agreement matrices

2. Add human calibration module:
   - Load expert-scored subset
   - Compute judge-vs-human Cohen's κ
   - ICC for total CQS scores

3. Add TOST equivalence testing for normal queries subset

4. Add McNemar's test for D6 gate failures (control vs treatment)

## References

- Task specification: `src/eval/TASK_judge_pipeline.md`
- CQS rubric: `docs/verification/cqs_rubric_specification.md`
- Statistical plan: `docs/verification/test_plan/06b_statistical_analysis_plan.md`
- Reference implementation: `~/Documents/GitHub/federal-survey-concept-mapper/`
