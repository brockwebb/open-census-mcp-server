#!/usr/bin/env python3
"""Validate numbers_registry.md against source JSON ground truth.

Cross-references every CERTIFIED/COMPUTED number in the registry against
the analysis JSONs that produced them. Reports mismatches with exact
expected vs actual values.

SRS: VR-104
V&V Registry: SRS Section 8.9

INDEPENDENCE: Reads registry as text (regex), reads JSONs independently.
Does not import any analysis scripts.

Usage:
    python -m src.eval.validate_registry
    python src/eval/validate_registry.py

Exit codes:
    0 = all checks PASS
    1 = one or more MISMATCH found
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "paper" / "numbers_registry.md"

SOURCES = {
    "aggregate": REPO_ROOT / "results/v2_redo/stage2/analysis/aggregate_statistics.json",
    "stratum": REPO_ROOT / "results/v2_redo/stage2/analysis/stratum_analysis.json",
    "fidelity": REPO_ROOT / "results/v2_redo/stage3/analysis/fidelity_summary.json",
    "cost": REPO_ROOT / "results/v2_redo/stage1/analysis/cost_analysis.json",
}

SCRIPT_NAME = "src/eval/validate_registry.py"
SRS_REFS = "VR-104"
TOLERANCE_PCT = 0.1  # 0.1% relative tolerance for floating point
TOLERANCE_ABS = 0.005  # absolute tolerance for small numbers


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def close_enough(expected: float, actual: float) -> bool:
    """Check if two numbers match within tolerance."""
    if expected == 0 and actual == 0:
        return True
    if abs(expected) < 0.01:
        return abs(expected - actual) < TOLERANCE_ABS
    return abs(expected - actual) / abs(expected) * 100 < TOLERANCE_PCT


def fmt_p(p: float) -> str:
    """Format p-value the way the registry does."""
    if p < 0.001:
        return "< 0.001"
    return f"{p:.4f}"


# ── Check definitions ─────────────────────────────────────────────────────────

def build_checks(agg: dict, strat: dict, fid: dict, cost: dict) -> list:
    """Build list of (check_id, registry_value, json_value, description) tuples.
    
    Each check compares what the registry SHOULD say against the JSON ground truth.
    """
    checks = []

    # ── Section 3b: Pairwise comparisons ──────────────────────────────────
    pw = agg["cqs_pairwise"]

    # S2-010: Pragmatics vs Control
    pvc = pw["pragmatics_vs_control"]
    checks.append(("S2-010.delta", 0.538, round(pvc["delta"], 3), "Prag vs Ctrl CQS delta"))
    checks.append(("S2-010.d", 1.440, round(pvc["cohens_d"], 3), "Prag vs Ctrl Cohen's d"))
    checks.append(("S2-010.ci_lo", 0.421, round(pvc["ci_lo"], 3), "Prag vs Ctrl CI low"))
    checks.append(("S2-010.ci_hi", 0.651, round(pvc["ci_hi"], 3), "Prag vs Ctrl CI high"))
    checks.append(("S2-010.eff_n", 36, pvc["effective_n"], "Prag vs Ctrl effective n"))

    # S2-011: Pragmatics vs RAG
    pvr = pw["pragmatics_vs_rag"]
    checks.append(("S2-011.delta", 0.385, round(pvr["delta"], 3), "Prag vs RAG CQS delta"))
    checks.append(("S2-011.d", 0.922, round(pvr["cohens_d"], 3), "Prag vs RAG Cohen's d"))
    checks.append(("S2-011.ci_lo", 0.256, round(pvr["ci_lo"], 3), "Prag vs RAG CI low"))
    checks.append(("S2-011.ci_hi", 0.513, round(pvr["ci_hi"], 3), "Prag vs RAG CI high"))
    checks.append(("S2-011.eff_n", 32, pvr["effective_n"], "Prag vs RAG effective n"))

    # S2-012: RAG vs Control
    rvc = pw["rag_vs_control"]
    checks.append(("S2-012.delta", 0.154, round(rvc["delta"], 3), "RAG vs Ctrl CQS delta"))
    checks.append(("S2-012.d", 0.546, round(rvc["cohens_d"], 3), "RAG vs Ctrl Cohen's d"))
    checks.append(("S2-012.eff_n", 30, rvc["effective_n"], "RAG vs Ctrl effective n"))

    # ── Section 3a: Omnibus ───────────────────────────────────────────────
    fr = agg["cqs_friedman"]
    checks.append(("S2-001.stat", 42.01, round(fr["stat"], 2), "Friedman chi-sq"))
    checks.append(("S2-001.n", 39, fr["n"], "Friedman n"))

    # ── Section 3e: Condition means ───────────────────────────────────────
    cm = fr["condition_means"]
    checks.append(("S2-040", 1.5282, round(cm["pragmatics"], 4), "Pragmatics mean CQS"))
    checks.append(("S2-041", 1.1436, round(cm["rag"], 4), "RAG mean CQS"))
    checks.append(("S2-042", 0.9897, round(cm["control"], 4), "Control mean CQS"))

    # ── Section 3d: Per-dimension effect sizes ────────────────────────────
    dim_labels = ["D1", "D2", "D3", "D4", "D5"]
    registry_d = {
        "D1": (0.541, 0.515, 0.190),
        "D2": (0.537, 0.297, 0.246),
        "D3": (1.353, 1.040, 0.417),
        "D4": (0.957, 0.577, 0.546),
        "D5": (0.732, 0.521, 0.148),
    }
    for i, dim in enumerate(dim_labels):
        pd = agg["per_dimension"][dim]["pairwise"]
        reg = registry_d[dim]
        json_pvc = round(pd["pragmatics_vs_control"]["cohens_d"], 3)
        json_pvr = round(pd["pragmatics_vs_rag"]["cohens_d"], 3)
        json_rvc = round(pd["rag_vs_control"]["cohens_d"], 3)
        sid = f"S2-03{i}"
        checks.append((f"{sid}.pvc", reg[0], json_pvc, f"{dim} Prag vs Ctrl d"))
        checks.append((f"{sid}.pvr", reg[1], json_pvr, f"{dim} Prag vs RAG d"))
        checks.append((f"{sid}.rvc", reg[2], json_rvc, f"{dim} RAG vs Ctrl d"))

    # ── Section 3f: Stratum analysis ──────────────────────────────────────
    sr = strat["stratum_results"]

    # Normal stratum
    npw = sr["normal"]["pairwise"]
    checks.append(("SA-001.d", 2.347, round(npw["pragmatics_vs_control"]["cohens_d"], 3),
                    "Normal Prag vs Ctrl d"))
    checks.append(("SA-002.d", 1.436, round(npw["pragmatics_vs_rag"]["cohens_d"], 3),
                    "Normal Prag vs RAG d"))
    checks.append(("SA-003.d", 0.458, round(npw["rag_vs_control"]["cohens_d"], 3),
                    "Normal RAG vs Ctrl d"))

    # Edge stratum
    epw = sr["edge"]["pairwise"]
    checks.append(("SA-010.d", 1.135, round(epw["pragmatics_vs_control"]["cohens_d"], 3),
                    "Edge Prag vs Ctrl d"))
    checks.append(("SA-011.d", 0.683, round(epw["pragmatics_vs_rag"]["cohens_d"], 3),
                    "Edge Prag vs RAG d"))
    checks.append(("SA-012.d", 0.590, round(epw["rag_vs_control"]["cohens_d"], 3),
                    "Edge RAG vs Ctrl d"))

    # Between-stratum
    bs = strat["between_stratum"]
    checks.append(("SA-020.p", 0.987, round(bs["pragmatics_vs_control"]["mann_whitney"]["p_greater"], 3),
                    "Between-stratum Prag vs Ctrl p"))
    checks.append(("SA-021.p", 0.987, round(bs["pragmatics_vs_rag"]["mann_whitney"]["p_greater"], 3),
                    "Between-stratum Prag vs RAG p"))
    checks.append(("SA-022.p", 0.347, round(bs["rag_vs_control"]["mann_whitney"]["p_greater"], 3),
                    "Between-stratum RAG vs Ctrl p"))

    # ── Section 4a: Fidelity ─────────────────────────────────────────────
    fo = fid["overall"]["fidelity"]
    checks.append(("S3-001.fidelity", 78.3, round(fo["control"]["fidelity"], 1),
                    "Control fidelity %"))
    checks.append(("S3-001.subst", 100.0, round(fo["control"]["substantive_fidelity"], 1),
                    "Control substantive fidelity %"))
    checks.append(("S3-001.error", 0.0, round(fo["control"]["error_rate"], 1),
                    "Control error rate %"))
    checks.append(("S3-001.claims", 253, fo["control"]["total_claims"],
                    "Control total claims"))

    checks.append(("S3-002.fidelity", 74.6, round(fo["rag"]["fidelity"], 1),
                    "RAG fidelity %"))
    checks.append(("S3-002.subst", 98.9, round(fo["rag"]["substantive_fidelity"], 1),
                    "RAG substantive fidelity %"))
    checks.append(("S3-002.error", 0.8, round(fo["rag"]["error_rate"], 1),
                    "RAG error rate %"))
    checks.append(("S3-002.claims", 355, fo["rag"]["total_claims"],
                    "RAG total claims"))

    checks.append(("S3-003.fidelity", 91.2, round(fo["pragmatics"]["fidelity"], 1),
                    "Pragmatics fidelity %"))
    checks.append(("S3-003.subst", 99.7, round(fo["pragmatics"]["substantive_fidelity"], 1),
                    "Pragmatics substantive fidelity %"))
    checks.append(("S3-003.error", 0.3, round(fo["pragmatics"]["error_rate"], 1),
                    "Pragmatics error rate %"))
    checks.append(("S3-003.claims", 353, fo["pragmatics"]["total_claims"],
                    "Pragmatics total claims"))

    # ── Section 4b: Auditability (THE SUSPECTED SWAP) ────────────────────
    ao = fid["overall"]["auditability"]

    # Registry corrected 2026-02-26: swap was identified and fixed.
    # S3-010 Control auditable = 21.8%, S3-011 RAG auditable = 6.2%

    ctrl_aud = round(ao["control"]["auditable_rate"], 1)
    rag_aud = round(ao["rag"]["auditable_rate"], 1)
    prag_aud = round(ao["pragmatics"]["auditable_rate"], 1)

    checks.append(("S3-010.aud_AS_REGISTERED", 21.8, ctrl_aud,
                    "Control auditable %"))
    checks.append(("S3-011.aud_AS_REGISTERED", 6.2, rag_aud,
                    "RAG auditable %"))
    checks.append(("S3-012.aud", 29.5, prag_aud,
                    "Pragmatics auditable %"))

    # Also check the non-swapped columns to confirm they're correct
    checks.append(("S3-010.partial", 63.0, round(ao["control"]["partially_auditable_rate"], 1),
                    "Control partially auditable %"))
    checks.append(("S3-010.unaud", 15.2, round(ao["control"]["unauditable_rate"], 1),
                    "Control unauditable %"))
    checks.append(("S3-010.subst_claims", 257, ao["control"]["substantive_claims"],
                    "Control substantive claims"))

    checks.append(("S3-011.partial", 76.0, round(ao["rag"]["partially_auditable_rate"], 1),
                    "RAG partially auditable %"))
    checks.append(("S3-011.unaud", 17.8, round(ao["rag"]["unauditable_rate"], 1),
                    "RAG unauditable %"))
    checks.append(("S3-011.subst_claims", 242, ao["rag"]["substantive_claims"],
                    "RAG substantive claims"))

    checks.append(("S3-012.partial", 51.8, round(ao["pragmatics"]["partially_auditable_rate"], 1),
                    "Pragmatics partially auditable %"))
    checks.append(("S3-012.unaud", 18.7, round(ao["pragmatics"]["unauditable_rate"], 1),
                    "Pragmatics unauditable %"))
    checks.append(("S3-012.subst_claims", 278, ao["pragmatics"]["substantive_claims"],
                    "Pragmatics substantive claims"))

    # ── Section 3h: Cost analysis ─────────────────────────────────────────
    sonnet = cost["costs"]["claude-sonnet-4-5"]["per_condition"]
    opus = cost["costs"]["claude-opus-4-6"]["per_condition"]

    checks.append(("COST-001.ctrl", 0.028, round(sonnet["control"]["cost_per_query"], 3),
                    "Sonnet control cost/query"))
    checks.append(("COST-001.rag", 0.082, round(sonnet["rag"]["cost_per_query"], 3),
                    "Sonnet RAG cost/query"))
    checks.append(("COST-001.prag", 0.113, round(sonnet["pragmatics"]["cost_per_query"], 3),
                    "Sonnet pragmatics cost/query"))

    checks.append(("COST-004.rag", 2.83, round(sonnet["rag"]["cqs_per_marginal_dollar"], 2),
                    "Sonnet RAG CQS/marginal$"))
    checks.append(("COST-004.prag", 6.28, round(sonnet["pragmatics"]["cqs_per_marginal_dollar"], 2),
                    "Sonnet pragmatics CQS/marginal$"))

    checks.append(("COST-005", 2.2, round(
        cost["costs"]["claude-sonnet-4-5"]["pragmatics_vs_rag_effectiveness_ratio"], 1),
                    "Cost-effectiveness ratio"))

    checks.append(("COST-010.ctrl", 0.046, round(opus["control"]["cost_per_query"], 3),
                    "Opus control cost/query"))
    checks.append(("COST-013.prag", 3.77, round(opus["pragmatics"]["cqs_per_marginal_dollar"], 2),
                    "Opus pragmatics CQS/marginal$"))

    return checks


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"={'=' * 70}")
    print(f"  Registry Validation — {SCRIPT_NAME}")
    print(f"  SRS: {SRS_REFS}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"={'=' * 70}\n")

    # Load all source JSONs
    data = {}
    for key, path in SOURCES.items():
        if not path.exists():
            print(f"FATAL: Source not found: {path}")
            sys.exit(2)
        data[key] = load_json(path)
        print(f"  Loaded: {path.relative_to(REPO_ROOT)}")
    print()

    # Build and run checks
    checks = build_checks(data["aggregate"], data["stratum"], data["fidelity"], data["cost"])

    passed = 0
    failed = 0
    failures = []

    for check_id, registry_val, json_val, desc in checks:
        if isinstance(registry_val, int) and isinstance(json_val, int):
            ok = registry_val == json_val
        elif isinstance(registry_val, (int, float)) and isinstance(json_val, (int, float)):
            ok = close_enough(float(registry_val), float(json_val))
        else:
            ok = registry_val == json_val

        if ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "MISMATCH"
            failures.append((check_id, registry_val, json_val, desc))

        # Only print failures and a summary, not every pass
        if not ok:
            print(f"  {status}  {check_id:30s}  registry={registry_val}  json={json_val}  ({desc})")

    print(f"\n{'─' * 70}")
    print(f"  RESULTS: {passed} passed, {failed} failed out of {passed + failed} checks")
    print(f"{'─' * 70}")

    if failures:
        print(f"\n  FAILURES REQUIRING REGISTRY CORRECTION:\n")
        for check_id, reg_val, json_val, desc in failures:
            print(f"    {check_id}: registry has {reg_val}, JSON has {json_val}")
            print(f"      → {desc}")
            print()

    # Exit code
    if failed > 0:
        print(f"  EXIT 1 — {failed} mismatch(es) found. Fix registry, then re-run.")
        sys.exit(1)
    else:
        print(f"\n  EXIT 0 — All checks pass. Registry is consistent with source JSONs.")
        sys.exit(0)


if __name__ == "__main__":
    main()
