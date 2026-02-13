# Chapter 8: Execution Procedure

[← Ch. 7](07_risk_register.md) | [README](README.md) | [Ch. 9 →](09_reproducibility.md)

---

## 8.1 Pre-Execution Checklist

- [ ] Verify config: `python -c "from census_mcp.config import DEFAULT_YEAR; print(DEFAULT_YEAR)"` → 2024
- [ ] Verify packs: smoke test passes, 36 items loaded
- [ ] Verify API keys: `.env` has `CENSUS_API_KEY` and `ANTHROPIC_API_KEY`
- [ ] Verify battery: `queries.yaml` has 39 entries
- [ ] Clear stale results: remove any previous `cqs_responses_*.jsonl`
- [ ] Record git hash: `git rev-parse HEAD` → document in results

## 8.2 Stage 1 Execution

```bash
cd /Users/brock/Documents/GitHub/census-mcp-server

# Record environment
git rev-parse HEAD > results/git_hash.txt
python -c "from census_mcp.config import DEFAULT_YEAR, DEFAULT_PRODUCT; print(f'{DEFAULT_YEAR},{DEFAULT_PRODUCT}')" > results/config_state.txt
shasum -a 256 packs/acs.db >> results/config_state.txt

# Execute
/opt/anaconda3/envs/census-mcp/bin/python -m eval.harness 2>&1 | tee results/harness_log.txt
```

## 8.3 Post-Execution Validation

- [ ] JSONL has 39 lines (one per query)
- [ ] All 39 query_ids present
- [ ] All treatment responses have ≥1 tool call
- [ ] No treatment responses have 0-length response_text
- [ ] No control responses have tool calls
- [ ] Spot-check 3 sentinel queries (GEO-006, TMP-002, MIS-002) manually

## 8.4 Stage 2 Execution

Pending Stage 1 completion and judge pipeline implementation.

**Prerequisites:**
- Stage 1 JSONL complete and validated per §8.3
- Judge pipeline built (`src/eval/judge_pipeline.py`)
- All three judge model API keys configured
- Judge prompt template finalized

## 8.5 Stage 3 Execution

Pending Stage 2 completion and analysis pipeline implementation.

**Prerequisites:**
- Stage 2 scores JSONL complete (117 judgments)
- Analysis pipeline built (`src/eval/analysis.py`)
- Statistical library available (Krippendorff α, Wilcoxon, TOST)
