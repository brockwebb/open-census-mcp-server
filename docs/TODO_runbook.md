# TODO: Evaluation Pipeline Runbook

**Priority:** High — needed before anyone else touches this system

## Should include:
- Environment setup (conda env, API keys, MCP server startup)
- Stage 1 commands with all flags (--output, --query-ids)
- Stage 2 commands with checkpoint behavior
- File naming conventions and where things land
- How to resume interrupted runs
- How to merge split output files
- Rate limit budgets per vendor per day
- Common errors and fixes (explore_variables bug, Google truncation, etc.)
- Pre-flight checklist before each stage

## Where it goes:
- `docs/runbook_evaluation_pipeline.md`
- NOT in SRS (that's requirements, not operations)
- Link from README

## When:
- After Stage 1 v3 + Stage 2 v3 complete and results are analyzed
- Before FCSM submission prep
