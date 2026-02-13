# Chapter 9: Reproducibility Contract

[← Ch. 8](08_execution_procedure.md) | [README](README.md)

---

## 9.1 Reproducibility Components

Per QR-016, results are reproducible given these four components:

| Component | Artifact | Versioning Method |
|---|---|---|
| Server configuration | `src/census_mcp/config.py` | Git commit hash |
| Pack content | `packs/acs.db` | SHA-256 content hash |
| Test battery | `src/eval/battery/queries.yaml` | Git commit hash |
| Model identifiers | Recorded in JSONL output | Pinned checkpoint strings |

All four are recorded in `results/config_state.txt` and in the JSONL output metadata per QR-014.

## 9.2 What "Reproducible" Means Here

LLM outputs are non-deterministic. Exact response text will vary across runs even with identical configuration. The evaluation protocol accounts for this through statistical aggregation across 39 queries and 3 judges, not through exact reproducibility of individual responses.

**Reproducible means:** Given the same four components, a re-run should produce statistically consistent conclusions (same direction and approximate magnitude of treatment effect), not identical output text.

## 9.3 Configuration File as Single Source of Truth

Per DEC-4B-019 and C-006: ALL parameters that affect outputs reside in `src/census_mcp/config.py`. No output-affecting defaults are hardcoded in application logic. This is a permanent, non-negotiable project rule.

The config file supports environment variable overrides for deployment flexibility, but the file itself documents the defaults and serves as the audit trail for what values were in effect for any given git commit.

## 9.4 Versioning Discipline

Any change to any of the four reproducibility components creates a **new experiment**, not a reproduction of the old one. Results files include timestamps and git hashes to distinguish runs.

| Change | Consequence |
|---|---|
| Update `config.py` defaults | New experiment. Old results are from a different configuration. |
| Add/modify pack content | New experiment. Pragmatics available to treatment changed. |
| Add/modify battery queries | New experiment. Query set changed. |
| Model version update | New experiment. Different model checkpoint. |
| Re-run with identical components | Statistical replication. Expect consistent conclusions, not identical text. |
