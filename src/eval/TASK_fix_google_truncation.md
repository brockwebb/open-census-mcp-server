# Claude Code Task: Full Judge Re-run — Temporal Fix + Google Truncation Fix

## Context

Two issues found in the first judge run (702 records):

1. **Temporal evaluation confound (ALL vendors):** All three judges penalized 
   treatment responses for citing "2024 ACS 5-year" data, scoring it as a 
   hallucinated/nonexistent vintage. In reality, the 2020-2024 ACS 5-year was 
   released January 29, 2026 — two weeks before the battery ran. The judges' 
   training data predates this release. This caused a systematic D1 score 
   reversal (control outscored treatment, d=-0.51, p=0.004).

2. **Google truncation (Google only):** 92/234 Google responses (39.3%) were 
   truncated mid-JSON due to insufficient output token budget.

Both fixes require a full re-run of all three vendors.

## Fix 1: Temporal grounding in judge prompt

**File:** `src/eval/judge_prompts.py`

Add ONE line at the very beginning of the judge prompt (before the rubric),
inside `build_judge_prompt()`:

```
Today's date is February 13, 2026. Score based on data availability as of this date.
```

This is the ONLY addition. Do NOT enumerate specific Census releases. Do NOT 
add scoring instructions about temporal issues. The timestamp alone is the 
minimal intervention — we document whether it's sufficient.

**Decision rationale:** DEC-4B-022. Minimal temporal grounding avoids 
over-coaching the judge toward treatment answers. Domain-agnostic (works for 
ACS, CPS, any survey). If D1 paradox persists, that's a stronger finding about 
LLM-as-judge limitations.

## Fix 2: Google max_output_tokens

**File:** `src/eval/judge_config.yaml`

Add per-vendor override for Google:
```yaml
judges:
  google:
    max_output_tokens: 8192
```

**File:** `src/eval/judge_pipeline.py`

Update config merging so per-vendor max_output_tokens overrides pipeline default:
```python
judge_config['max_tokens'] = judge_config.get('max_output_tokens',
    config['pipeline'].get('max_tokens', 4096))
```

## Fix 3: Google truncation retry

**File:** `src/eval/judge_pipeline.py`

In `call_google()`, after getting the response text, validate JSON completeness
before returning. If truncated, raise an error to trigger retry:

```python
content = response.text.strip()
# Validate JSON completeness before returning
try:
    json.loads(content)
except json.JSONDecodeError:
    raise ValueError(f"Truncated JSON response ({len(content)} chars)")
```

## Fix 4: Analysis deduplication

**File:** `src/eval/judge_analysis.py`

Since we're appending to the same JSONL, the analysis script must deduplicate.
When loading records, keep the LAST occurrence per unique key:

```python
def load_and_deduplicate(scores_path):
    records = []
    with open(scores_path) as f:
        for line in f:
            records.append(json.loads(line))
    
    seen = {}
    for r in records:
        key = (r['query_id'], r['judge_vendor'], r['presentation_order'], r['pass_number'])
        seen[key] = r
    
    deduped = list(seen.values())
    print(f"Loaded {len(records)} raw, deduplicated to {len(deduped)}")
    return deduped
```

Use this function wherever records are loaded for analysis.

## Fix 5: Clear ALL checkpoint entries

Since we're re-running all three vendors (not just Google), clear the entire
checkpoint:

```python
import json
from pathlib import Path

checkpoint_path = Path('results/stage2/checkpoints/judge_checkpoint.json')
if checkpoint_path.exists():
    with open(checkpoint_path) as f:
        data = json.load(f)
    print(f"Clearing {len(data.get('completed', []))} checkpoint entries")
    data['completed'] = []
    with open(checkpoint_path, 'w') as f:
        json.dump(data, f)
```

The old records stay in the JSONL. Deduplication (Fix 4) handles it.

## Decision Log Entry

Create `docs/verification/phase4b_decision_log_DEC022.md`:

```markdown
# DEC-4B-022: Temporal Grounding for Judge Prompt

**Date:** 2026-02-13
**Context:** All three LLM judges penalized treatment responses for citing
2020-2024 ACS 5-year data (released Jan 29, 2026), scoring it as hallucinated.
This caused a D1 score reversal: control d=1.35, treatment d=0.96, p=0.004.

**Root cause:** Judge training data predates the Jan 29, 2026 ACS release.
Judges correctly applied their (stale) knowledge that the latest 5-year was
2019-2023.

**Decision:** Add minimal temporal grounding — a single timestamp line in the
judge prompt. No enumeration of specific releases (avoids over-coaching).
No CPS-specific or ACS-specific context (domain-agnostic).

**Intervention:** "Today's date is February 13, 2026. Score based on data
availability as of this date."

**Rationale:** If timestamp alone fixes D1, clean result. If it doesn't,
that's a stronger finding about LLM-as-judge temporal limitations in
fast-moving domains. Either outcome is publishable.

**Finding:** Temporal evaluation confounds are a systematic risk in
LLM-as-judge evaluation of time-sensitive domains. This generalizes beyond
Census to finance, medicine, law, and any domain where ground truth changes
faster than model training cycles.

**Cost:** Full re-run of all 3 vendors × 6 passes × 39 queries = 702 calls.
```

## Verification

1. Verify judge prompt starts with temporal grounding line
2. Verify Google max_output_tokens = 8192 in yaml
3. Verify call_google has JSON truncation check
4. Verify analysis script has deduplication
5. Verify checkpoint is cleared (0 entries)
6. Verify decision log created
7. Run pytest

## Do NOT run the pipeline — user will execute manually.

## Constraints
- Do NOT run the judge pipeline
- Do NOT delete the existing JSONL — append only
- The temporal grounding line must be EXACTLY: 
  "Today's date is February 13, 2026. Score based on data availability as of this date."
- No other changes to the judge prompt or rubric
