# Chapter 1: Purpose, Scope & References

[← README](README.md) | [Ch. 2 →](02_system_architecture.md)

---

## 1.1 Purpose

This test plan specifies the complete experimental protocol for evaluating whether a pragmatics layer improves AI-mediated Census data consultation quality.

**Research question:** Does grounding an LLM with structured statistical methodology guidance (via MCP tools) produce measurably better Census data consultation than the same LLM operating from training data alone?

## 1.2 Scope

**In scope (v0.1):** ACS data consultation via the Census MCP Server. Single-turn, zero-shot queries. One test subject model (Claude Sonnet 4.5). Three-model judge panel. CQS rubric scoring.

**Out of scope (v0.1):** Multi-turn consultation, non-Anthropic test subjects, decennial/CPS data products, real-time geographic resolution.

## 1.3 Reference Documents

| Document | Location | Content |
|---|---|---|
| CQS Rubric Specification | `docs/verification/cqs_rubric_specification.md` | Six scoring dimensions, framework crosswalk |
| Judge Prompt Template | `docs/verification/cqs_judge_prompt_template.md` | Judge instructions, Pydantic output schema |
| Test Battery | `docs/verification/cqs_test_battery.md` | 39 queries with expected behaviors |
| Harness Architecture | `docs/verification/cqs_harness_architecture.md` | Module specs, reproducibility contract |
| Decision Log | `docs/verification/phase4b_decision_log.md` | 19 design decisions with rationale |
| Code Provenance | `docs/verification/code_provenance_log.md` | Reuse map from harmonization project |
| SRS | `docs/requirements/srs.md` | Requirements QR-010–016, C-006, VR-010 |
