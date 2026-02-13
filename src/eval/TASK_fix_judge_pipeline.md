# Claude Code Task: Fix Judge Pipeline Bugs + Configure 6-Pass Execution

## Context

The judge pipeline code exists but has bugs that will cause data loss and needs
configuration for the 6-pass design (DEC-4B-021). Fix these before execution.

Reference: `docs/verification/phase4b_decision_log_DEC021.md` for rationale.

## Bug Fix 1: Checkpoint excludes is_retest — causes retest data loss

**File:** `src/eval/judge_pipeline.py`

**Problem:** Line ~411 filters tasks with:
```python
if (task[0], task[1], task[2]) not in completed  # Ignore is_retest for checkpoint
```
This means retest tasks share checkpoint keys with first-run tasks. After pass 1
completes `(NORM-001, anthropic, control_first)`, ALL subsequent passes for that
combination are skipped on resume.

**Fix:** Include pass_number in checkpoint tuple. Replace the current task-building
and filtering logic. Tasks should be tuples of:
`(query_id, judge_key, ordering, pass_number)`

Where pass_number goes from 1 to 6 (not a boolean is_retest).

The checkpoint set stores `(query_id, judge_key, ordering, pass_number)` tuples.

Update `load_checkpoint`, `save_checkpoint`, task building loop, and filtering.

The `is_retest` field on JudgeRecord should be replaced with `pass_number: int`.
Update `src/eval/models.py` accordingly:
```python
# Replace:  is_retest: bool = False
# With:     pass_number: int = 1  # 1-6, which pass this measurement came from
```

## Bug Fix 2: Google SDK import

**File:** `src/eval/judge_pipeline.py`

The current code uses `from google import genai`. Verify this works by adding
a try/except with a helpful error message:

```python
def call_google(prompt, config, max_retries=5):
    try:
        from google import genai
    except ImportError:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Neither google-genai nor google-generativeai is installed. "
                "Run: pip install google-genai"
            )
    ...
```

## Configuration Update: 6-Pass Design

**File:** `src/eval/judge_config.yaml`

Replace the current pipeline section with:

```yaml
pipeline:
  random_seed: 42
  max_tokens: 4096
  rate_limit_delay: 1.0
  checkpoint_interval: 10
  num_passes: 6           # 6 passes per judge per query
  # Pass schedule:
  # Pass 1: control_first   (base scoring)
  # Pass 2: treatment_first (position bias)
  # Pass 3: control_first   (test-retest #1)
  # Pass 4: treatment_first (test-retest #1 x position)
  # Pass 5: control_first   (test-retest #2, CIs)
  # Pass 6: treatment_first (test-retest #2 x position, CIs)
```

Remove `position_bias_mode`, `test_retest_count`, and `test_retest_query_ids`.
Those are superseded by the 6-pass design.

**File:** `src/eval/judge_pipeline.py`

Update the task-building loop to generate 6 passes with alternating orderings:

```python
for pair in query_pairs:
    for judge_key in config['judges'].keys():
        for pass_num in range(1, num_passes + 1):
            ordering = 'control_first' if pass_num % 2 == 1 else 'treatment_first'
            tasks.append((pair.query_id, judge_key, ordering, pass_num))
```

Total tasks: 39 × 3 × 6 = 702

## Verification

1. Verify task count:
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python -c "
from eval.judge_pipeline import *
import yaml
with open('src/eval/judge_config.yaml') as f:
    config = yaml.safe_load(f)
pairs = load_query_pairs(config)
# Count expected tasks
n = len(pairs) * len(config['judges']) * config['pipeline']['num_passes']
print(f'Expected tasks: {n}')
assert n == 702, f'Expected 702, got {n}'
print('PASS')
"
```

2. Verify checkpoint includes pass_number:
```bash
/opt/anaconda3/envs/census-mcp/bin/python -c "
from eval.judge_pipeline import *
completed = {('NORM-001', 'anthropic', 'control_first', 1)}
# Pass 3 should NOT be in completed
assert ('NORM-001', 'anthropic', 'control_first', 3) not in completed
print('Checkpoint isolation: PASS')
"
```

3. Verify models.py has pass_number:
```bash
/opt/anaconda3/envs/census-mcp/bin/python -c "
from eval.models import JudgeRecord
import inspect
sig = inspect.signature(JudgeRecord)
assert 'pass_number' in sig.parameters, 'Missing pass_number field'
assert 'is_retest' not in sig.parameters, 'is_retest should be removed'
print('Model schema: PASS')
"
```

4. Dry-run first 3 tasks only (verify API connectivity):
```bash
# Quick test - modify pipeline to stop after 3 tasks for testing
# OR just verify API keys work:
/opt/anaconda3/envs/census-mcp/bin/python -c "
import os
from dotenv import load_dotenv
load_dotenv()
keys = {
    'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', '')[:10],
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', '')[:10],
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'),
}
for k, v in keys.items():
    status = 'SET' if v else 'MISSING'
    print(f'{k}: {status}')
    if not v:
        print(f'  ERROR: {k} is required!')
"
```

5. Run pytest:
```bash
/opt/anaconda3/envs/census-mcp/bin/python -m pytest tests/ -x -q
```

## Concurrency: Parallel Execution per Vendor

**Reference implementation:** `~/Documents/GitHub/federal-survey-concept-mapper/src/pipelines/01_barrier_pipeline.py`
uses `ThreadPoolExecutor` with `as_completed`, thread-safe checkpoint writes via
`checkpoint_lock = threading.Lock()`, and thread-safe JSONL appends via `write_lock`.

The current judge_pipeline.py is fully serial. Refactor to:

1. **Three vendor-level workers** running in parallel (Anthropic, OpenAI, Google)
2. **Up to 3 concurrent calls per vendor** (configurable in yaml)
3. Thread-safe JSONL writes and checkpoint saves (use threading.Lock)
4. Per-vendor rate limiting (respect `rate_limit_delay` per call, not per batch)

Add to `judge_config.yaml`:
```yaml
pipeline:
  max_workers_per_vendor: 5   # concurrent calls per API vendor (3 safe, 5 tested OK)
```

Architecture:
```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

write_lock = threading.Lock()
checkpoint_lock = threading.Lock()

def process_vendor(vendor_key, vendor_tasks, config, output_file, completed):
    """Process all tasks for one vendor with concurrent workers."""
    max_workers = config['pipeline'].get('max_workers_per_vendor', 3)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(score_single_task, task, config): task for task in vendor_tasks}
        for future in as_completed(futures):
            record = future.result()
            with write_lock:
                # append to JSONL
            with checkpoint_lock:
                # update checkpoint

# Main: launch 3 vendor threads
with ThreadPoolExecutor(max_workers=3) as vendor_executor:
    for vendor_key in config['judges']:
        vendor_tasks = [t for t in remaining_tasks if t[1] == vendor_key]
        vendor_executor.submit(process_vendor, vendor_key, vendor_tasks, ...)
```

This gives 9 concurrent API calls max (3 vendors × 3 workers). Pipeline should
complete in ~30-40 minutes instead of ~3 hours.

Keep the `rate_limit_delay` between calls within each vendor to avoid
per-minute rate limits. The delay only applies within a vendor's worker pool.

## Cleanup: Delete Aborted Run Artifacts

A prior buggy run was killed at ~6%. Delete any partial outputs:
```bash
rm -rf results/stage2/judge_scores_*.jsonl
rm -rf results/stage2/checkpoints/
```
The checkpoint from the aborted run would cause the fixed pipeline to skip
already-completed tasks — but those tasks used the old buggy schema (is_retest
instead of pass_number). Clean slate.

## After Fixes — Do NOT Execute Pipeline

After implementing fixes and passing all 5 verification checks, report back.
Do NOT run the full pipeline yet — it costs real money.
The user will execute manually after reviewing.

## Constraints

- Do NOT modify Stage 1 code (agent_loop.py, harness.py)
- Do NOT modify battery queries or Stage 1 results
- Do NOT run the full judge pipeline — only verification checks
- All model names must come from judge_config.yaml
- Preserve the existing judge_analysis.py (it will need updating for
  pass_number but that's a separate task after pipeline execution)
