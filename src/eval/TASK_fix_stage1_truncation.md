# Claude Code Task: Fix Stage 1 Treatment Response Truncation

## Problem

7 of 39 treatment responses (18%) are fragments like "Good! Now let me get 
the margins of error..." instead of complete synthesized answers. These are
the LLM's intermediate chain-of-thought captured when `max_tool_rounds=5` 
was hit before the model finished its tool loop.

**Root cause:** `src/eval/agent_loop.py` line ~160 extracts text from the 
last API response. When the agent loop exits because `max_tool_rounds` is 
exhausted (not because the model stopped using tools), the last response 
contains transitional text, not a final answer.

**Affected queries:** NORM-004, NORM-005, AMB-003, GEO-002, SML-002, TMP-002, 
NORM-010 — all had 4-7 tool calls and fragment responses < 200 chars.

**Impact:** 45% of the D1 score paradox. Judges correctly scored these 
fragments as D1=0 (no source selection, no answer).

## Fix 1: Increase max_tool_rounds

In `src/eval/agent_loop.py`, change the default:

```python
max_tool_rounds: int = 20,  # was 5 — engineering safety factor, log actual usage
```

Census queries that need methodology guidance + data retrieval + MOE retrieval 
+ follow-up corrections routinely need 6-8 rounds.

## Fix 2: Detect and recover from exhausted loop

After the while loop exits, check if we hit the limit with tools still pending:

```python
        # After the while loop:
        
        # Check if loop exhausted without final answer
        if rounds >= self.max_tool_rounds and response.stop_reason == "tool_use":
            # Model wanted to make more tool calls but we hit the limit.
            # Force a final synthesis by calling once more WITHOUT tools.
            synthesis_response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=TREATMENT_SYSTEM_PROMPT,
                messages=messages + [
                    {"role": "user", "content": [{"type": "text", "text": 
                        "You have reached the maximum number of tool calls. "
                        "Please provide your best answer based on the data "
                        "you have already retrieved."}]}
                ],
                # NO tools parameter — forces text-only response
            )
            total_input_tokens += synthesis_response.usage.input_tokens
            total_output_tokens += synthesis_response.usage.output_tokens
            response = synthesis_response  # Use this for final text extraction
```

This ensures we ALWAYS get a synthesized answer, even when the tool budget 
is exhausted. The model has all the tool results in context from previous 
rounds — it just needs to be told to synthesize.

## Fix 3: Flag truncated responses in metadata

Add a field to ResponseRecord to track this:

In `src/eval/models.py`, add to ResponseRecord:
```python
tool_rounds_used: int = 0
tool_rounds_exhausted: bool = False  # True if forced synthesis was needed
```

Set these after the loop:
```python
tool_rounds_used=rounds,
tool_rounds_exhausted=(rounds >= self.max_tool_rounds),
```

## Validation: Re-run only the 7 broken queries

After implementing fixes, run ONLY the known-bad queries to validate:

```python
# In harness.py or via command line, filter to:
test_queries = ['NORM-004', 'NORM-005', 'AMB-003', 'GEO-002', 'SML-002', 'TMP-002', 'NORM-010']
```

The harness should support a `--query-ids` filter. If it doesn't, add one:

```python
parser.add_argument('--query-ids', nargs='+', help='Run only these query IDs')
```

**Expected result:** All 7 should produce treatment responses > 500 chars with 
actual data and analysis, not transitional fragments.

## Run ONLY the 7 broken queries for validation.
User will run the remaining 32 after inspecting results.
Checkpoint will let the remaining 32 pick up where these leave off.

## Geography Issue (separate — document only, do not fix)

The PER-001 Bozeman queries show wrong FIPS codes returning county data 
(~117K) instead of city data (~53K). This is a FIPS resolution problem in 
the Census MCP tool, not the harness. Document for separate investigation.

## OUTPUT FILES — CRITICAL

All output MUST go to NEW files. Do NOT append to or overwrite existing results.

- Stage 1 output: `results/stage1/cqs_responses_v3_YYYYMMDD_HHMMSS.jsonl`
- Checkpoint: `results/stage1/checkpoints/` (new checkpoint file)
- Do NOT touch anything in `results/stage2/`
- Do NOT touch `results/stage1/cqs_responses_20260212_*.jsonl`

Verify the output directory exists: `mkdir -p results/stage1/checkpoints`

## Verification

1. max_tool_rounds default is 20
2. Forced synthesis logic exists after the while loop
3. ResponseRecord has tool_rounds_used and tool_rounds_exhausted fields
4. harness.py supports --query-ids filter
5. Run validation on 7 broken queries ONLY
6. All 7 produce responses > 500 chars
7. Print response lengths, tool_rounds_used, and first 200 chars for manual inspection
8. Output goes to NEW file (not existing results)
9. Verify no existing result files were modified: `ls -la results/stage1/`
