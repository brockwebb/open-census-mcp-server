# Claude Code Task: Build Judge Scoring Pipeline (Stage 2)

## Context

Stage 1 is complete. We have 39 query pairs with control + treatment responses
in `results/cqs_responses_20260212_184334.jsonl`. This task builds the Stage 2
judge pipeline that scores those responses using 3 LLM judges.

**Reference implementation:** The multi-vendor API calling pattern, checkpointing,
and stats library from `~/Documents/GitHub/federal-survey-concept-mapper/` should
be studied and adapted. Key files:
- `src/pipelines/01_barrier_pipeline.py` — Multi-vendor API callers with retry
- `config/report_03.yaml` — Config-driven model specification
- `src/lib/stats.py` — Cohen's κ, Fleiss' κ, Krippendorff's α

**Rubric:** `docs/verification/cqs_rubric_specification.md`
**Statistical plan:** `docs/verification/test_plan/06b_statistical_analysis_plan.md`
**Harmonization pipeline reference:** `~/Documents/GitHub/federal-survey-concept-mapper/`

## Architecture

```
src/eval/
├── config.py              # Existing — add judge model configs
├── models.py              # Existing — add JudgeRecord model
├── agent_loop.py          # Existing — Stage 1 (don't modify)
├── harness.py             # Existing — Stage 1 (don't modify)
├── judge_pipeline.py      # NEW — main judge orchestration
├── judge_prompts.py       # NEW — rubric prompt templates
├── judge_analysis.py      # NEW — all §6B statistical analysis
└── judge_config.yaml      # NEW — judge model configuration
```

## 1. Configuration: judge_config.yaml

```yaml
version: '1.0'
created: '2026-02-12'
purpose: 'CQS multi-vendor judge scoring with bias diagnostics'

judges:
  anthropic:
    model: 'claude-opus-4-5-20251101'
    provider: 'anthropic'
    api_key_env: 'ANTHROPIC_API_KEY'
    temperature: 0.0
    notes: 'Anthropic flagship — potential self-enhancement bias on Claude outputs'

  openai:
    model: 'gpt-5.2'
    provider: 'openai'
    api_key_env: 'OPENAI_API_KEY'
    temperature: null
    max_tokens_param: 'max_completion_tokens'
    notes: 'OpenAI flagship — does NOT accept temperature param'

  google:
    model: 'gemini-3-pro-preview'
    provider: 'google'
    api_key_env: 'GEMINI_API_KEY'
    temperature: 1.0
    notes: 'Google flagship — temperature must be 1.0 per Google docs'

pipeline:
  random_seed: 42
  max_tokens: 4096
  rate_limit_delay: 1.0
  checkpoint_interval: 5
  position_bias_mode: 'both'  # Run all queries in both orderings
  test_retest_count: 10       # Number of queries for test-retest
  test_retest_query_ids: null  # Auto-select if null

scoring:
  dimensions: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
  scale_min: 0
  scale_max: 2
  request_confidence: true     # Ask judges for per-dimension confidence
  confidence_scale: [1, 2, 3, 4, 5]

paths:
  stage1_results: 'results/cqs_responses_20260212_184334.jsonl'
  output_dir: 'results/stage2'
  checkpoint_dir: 'results/stage2/checkpoints'
  analysis_output: 'results/stage2/analysis'
```

## 2. Judge Prompt: judge_prompts.py

Build a function `build_judge_prompt(query_text, response_a, response_b)` that returns
the scoring prompt. Key requirements:

- Present query and two responses (A and B) — judge does NOT know which is treatment
- Include the full CQS rubric (6 dimensions, 0-1-2 scale, scoring principles)
- Request structured JSON output:

```json
{
  "response_a": {
    "D1": {"score": 2, "confidence": 4, "reasoning": "..."},
    "D2": {"score": 1, "confidence": 3, "reasoning": "..."},
    "D3": {"score": 0, "confidence": 5, "reasoning": "..."},
    "D4": {"score": 2, "confidence": 4, "reasoning": "..."},
    "D5": {"score": 1, "confidence": 3, "reasoning": "..."},
    "D6": {"score": 2, "confidence": 5, "reasoning": "..."}
  },
  "response_b": {
    "D1": {"score": 1, "confidence": 4, "reasoning": "..."},
    ...
  },
  "overall_preference": "A",
  "preference_reasoning": "..."
}
```

**Critical rubric principles to embed in the prompt:**
1. Informed refusal outscores confident delivery of unfit data
2. D6 = 0 is a gate failure — other scores unreliable
3. Score each response independently before comparing
4. The 0-1-2 scale: 0=absent/wrong, 1=partial, 2=complete

**Include dimension definitions verbatim from the rubric spec** (D1-D6 with
"What it measures", "Scoring", "What good looks like", "Failure modes").

## 3. Data Model: models.py additions

Add `JudgeRecord` to `src/eval/models.py`:

```python
@dataclass
class DimensionScore:
    score: int          # 0, 1, or 2
    confidence: int     # 1-5
    reasoning: str

@dataclass
class JudgeRecord:
    query_id: str
    judge_model: str
    judge_vendor: str
    presentation_order: str    # "control_first" or "treatment_first"
    scores_response_a: dict    # D1-D6 -> DimensionScore
    scores_response_b: dict    # D1-D6 -> DimensionScore
    preference: str            # "A" / "B" / "tie"
    preference_reasoning: str
    response_a_label: str      # "control" or "treatment"
    response_b_label: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    timestamp: str
    run_id: str
    raw_response: str          # Full judge response for debugging
    parse_success: bool        # Whether JSON parsing succeeded
```

## 4. Pipeline: judge_pipeline.py

### 4.1 Main Loop

```
For each query_pair in stage1_results:
    For each judge in [anthropic, openai, google]:
        For each ordering in [control_first, treatment_first]:
            1. Build prompt with randomized A/B assignment
            2. Call judge API
            3. Parse JSON response
            4. Map A/B scores back to control/treatment
            5. Write JudgeRecord to output JSONL
            6. Checkpoint every N queries
```

### 4.2 A/B Randomization

Use seeded RNG (seed from config) for reproducibility. For each (query, judge, ordering):
- ordering="control_first": A=control, B=treatment
- ordering="treatment_first": A=treatment, B=control

### 4.3 API Callers

Adapt from harmonization pipeline `01_barrier_pipeline.py`:
- `call_anthropic(prompt, config)` — uses anthropic SDK
- `call_openai(prompt, config)` — uses openai SDK, respect null temperature
- `call_google(prompt, config)` — uses google-generativeai SDK, temperature=1.0

Each caller must:
- Return raw response text + token counts + latency
- Retry with exponential backoff (max 5 retries)
- Handle rate limits gracefully
- Log failures without crashing

### 4.4 JSON Parsing

Judge responses may not be valid JSON. Implement robust parsing:
1. Try direct `json.loads(response)`
2. Try extracting JSON from markdown code blocks
3. Try regex extraction of JSON object
4. If all fail, set `parse_success=False`, store raw response, skip scoring

### 4.5 Test-Retest Subset

For the first `test_retest_count` queries, run each judge a second time
(same ordering, separate API call). Store with a `retest=True` flag.
This enables ICC computation for test-retest reliability.

### 4.6 Checkpointing

Write checkpoint after every `checkpoint_interval` queries. Checkpoint contains:
- Set of completed (query_id, judge, ordering) tuples
- Last query_id processed
- Resume logic: skip already-completed tuples on restart

### 4.7 Output

Write to `results/stage2/judge_scores_YYYYMMDD_HHMMSS.jsonl`
One JudgeRecord per line.

## 5. Analysis: judge_analysis.py

This script reads the judge scores JSONL and computes ALL metrics from
`docs/verification/test_plan/06b_statistical_analysis_plan.md`.

### 5.1 Required Metrics

Copy `stats.py` functions from harmonization project, then add:

**Inter-rater agreement (§6B.3):**
- Krippendorff's α ordinal per dimension
- Fleiss' κ per dimension
- Cohen's κ all pairwise
- Percent agreement per dimension

**Bias diagnostics (§6B.4):**
- Position bias: swap consistency rate, per-dimension paired test
- Verbosity bias: Spearman ρ (length vs CQS), partial correlation, regression
- Self-enhancement: per-vendor mean CQS, self-enhancement ratio, Kruskal-Wallis
- Leniency/severity: per-judge mean CQS range

**Treatment effects (§6B.5):**
- Wilcoxon signed-rank (total and per-dimension, overall and by subgroup)
- Cohen's d paired
- Rank-biserial correlation r
- TOST equivalence (normal queries)
- McNemar's test (D6 gate failures)
- Per-category and per-difficulty subgroup analysis

**Reliability (§6B.6):**
- ICC test-retest per dimension
- Confidence calibration correlation
- Cronbach's α across dimensions

**Human calibration (§6B.7) — if human scores available:**
- Cohen's κ judge-vs-human per dimension
- ICC judge-vs-human for total CQS

### 5.2 Output

Write `results/stage2/analysis/analysis_report.json` with all metrics.
Write `results/stage2/analysis/summary_tables.md` with publication-ready tables.
Write diagnostic plots to `results/stage2/analysis/plots/`:
- `position_bias.png` — swap consistency by judge
- `verbosity_scatter.png` — length vs CQS score
- `vendor_bias.png` — per-judge score distributions
- `treatment_effect.png` — paired CQS by condition
- `dimension_heatmap.png` — mean scores per dimension per condition
- `agreement_matrix.png` — pairwise judge agreement

## 6. Execution

```bash
# Install dependencies if needed
pip install anthropic openai google-generativeai krippendorff --break-system-packages

# Run judge pipeline
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python -m eval.judge_pipeline

# Run analysis (after pipeline completes)
/opt/anaconda3/envs/census-mcp/bin/python -m eval.judge_analysis
```

## 7. Verification

1. Check output has expected record count:
   - Base: 39 × 3 × 2 orderings = 234
   - Test-retest: 10 × 3 = 30
   - Total: 264 records (if all succeed)

2. Check parse_success rate: should be > 95%

3. Check all judges produced scores for all queries

4. Run analysis and verify all §6B metrics are present in output JSON

## 8. Constraints

- Do NOT modify Stage 1 code (agent_loop.py, harness.py)
- Do NOT modify the battery or Stage 1 results
- API keys must come from environment variables
- All model names come from judge_config.yaml, never hardcoded
- Checkpoint format must allow resume after interruption
- The judge must NEVER see which response is treatment/control
- Raw judge responses must be stored for debugging
- Failed parse attempts must not crash the pipeline
