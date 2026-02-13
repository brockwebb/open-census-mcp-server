# Chapter 4: Data Flow Specification

[← Ch. 3](03_configuration.md) | [README](README.md) | [Ch. 5 →](05_battery_summary.md)

---

## 4.1 Stage 1: Response Generation

**Input:**

| Artifact | Format | Content |
|---|---|---|
| `queries.yaml` | YAML | 39 query definitions with id, text, category, difficulty, metadata |

**Process:**

For each query (sequential):
1. **Control:** Single Claude API call. No tools. System prompt = CONTROL_SYSTEM_PROMPT. Record response text, tokens, latency.
2. **Treatment:** Claude API call with tools from MCP `list_tools()`. Agent loop: if response contains `tool_use` blocks, execute via MCP client, return `tool_result`, repeat until text-only response or max 5 rounds. Record response text, all tool calls with arguments and results, pragmatics context_ids, tokens, latency.
3. **Write:** Serialize `QueryPair` (control + treatment) to JSONL. One line per query.

**Output:**

| Artifact | Format | Content | Size estimate |
|---|---|---|---|
| `results/cqs_responses_{timestamp}.jsonl` | JSON Lines | 39 QueryPair objects | ~2-5 MB |

**QueryPair schema:**

```json
{
  "query_id": "NORM-001",
  "query_text": "...",
  "category": "normal",
  "difficulty": "normal",
  "control": {
    "condition": "control",
    "model": "claude-sonnet-4-5-20250929",
    "system_prompt": "...",
    "response_text": "...",
    "tool_calls": [],
    "pragmatics_returned": [],
    "total_latency_ms": 4748.0,
    "input_tokens": 49,
    "output_tokens": 199,
    "timestamp": "2026-02-12T22:46:11.400801"
  },
  "treatment": {
    "condition": "treatment",
    "model": "claude-sonnet-4-5-20250929",
    "system_prompt": "...",
    "response_text": "...",
    "tool_calls": [
      {
        "tool_name": "get_methodology_guidance",
        "arguments": {"topics": ["period_estimate", "margin_of_error"]},
        "result": {"guidance": ["..."], "related": ["..."]},
        "latency_ms": 32.5
      }
    ],
    "pragmatics_returned": ["ACS-MOE-001", "ACS-PER-001", "..."],
    "total_latency_ms": 14233.5,
    "input_tokens": 15774,
    "output_tokens": 595,
    "timestamp": "2026-02-12T22:46:25.634445"
  }
}
```

## 4.2 Stage 2: Judge Scoring (Stubbed)

**Input:** `cqs_responses_{timestamp}.jsonl` + judge prompt template

**Process:** For each QueryPair × 3 judges:
1. Construct judge prompt with original query + blind-masked responses (A/B randomized per DEC-4B-008)
2. Send to judge model with structured output request
3. Parse CQSJudgment (6 dimensions × 2 responses + overall preference)
4. Write to scores JSONL

**Output:** `results/cqs_scores_{timestamp}.jsonl` — 39 × 3 = 117 CQSJudgment objects

**Detailed spec deferred** to Stage 2 implementation. Judge prompt template in `cqs_judge_prompt_template.md`.

## 4.3 Stage 3: Analysis (Stubbed)

**Input:** `cqs_scores_{timestamp}.jsonl`

**Process:**
1. Inter-rater agreement (Krippendorff's α ordinal, per dimension)
2. Treatment effect by stratum (edge cases: Wilcoxon signed-rank; normal: TOST equivalence)
3. Dimension-level analysis (which dimensions show largest treatment effect)
4. Vendor bias detection (does any judge systematically favor A or B)
5. Position bias quantification (effect of A/B randomization)

**Output:** Tables, figures, narrative for FCSM talk

**Detailed spec deferred** to Stage 3 implementation.
