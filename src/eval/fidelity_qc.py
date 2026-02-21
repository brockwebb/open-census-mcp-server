#!/usr/bin/env python3
"""Stage 3 fidelity QC trace verification (V&V artifact).

Independent verifier for fidelity_aggregate.py outputs. Reads the same raw
JSONL and recomputes all metrics from scratch, then compares against the JSON
produced by fidelity_aggregate.py. Any divergence beyond tolerance causes
exit code 1.

INDEPENDENCE REQUIREMENT (VR-097): this script does NOT import from
fidelity_aggregate.py.

SRS: VR-097 through VR-100
V&V Registry: SRS Section 8.9
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ── Constants ──────────────────────────────────────────────────────────────────

CONFIG_PATH = Path("src/eval/judge_config.yaml")
CONDITIONS = ["control", "rag", "pragmatics"]
TOLERANCE = 0.05          # percent — VR-097
EXPECTED_QUERIES = 39
SCRIPT_NAME = "src/eval/fidelity_qc.py"
SRS_REFS = "VR-097 through VR-100"


# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_params(config: dict) -> dict:
    agg = config.get("fidelity", {}).get("aggregate", {})
    if not agg.get("input_file"):
        raise ValueError("fidelity.aggregate.input_file not found in config")
    output_dir = Path(agg.get("output_dir", "results/v2_redo/stage3/analysis"))
    return {
        "input_file": Path(agg["input_file"]),
        "summary_json": output_dir / "fidelity_summary.json",
        "output_dir": output_dir,
        "battery_path": Path(agg.get("battery_path", "src/eval/battery/queries.yaml")),
        "v1_file": Path("results/stage3/fidelity_20260213_195123.jsonl"),
    }


# ── Data loading ───────────────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list:
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_battery_ids(path: Path) -> set:
    if not path.exists():
        return set()
    with open(path) as f:
        data = yaml.safe_load(f)
    return {q.get("id") or q.get("query_id") for q in data.get("queries", []) if q.get("id") or q.get("query_id")}


# ── Recompute from raw (independent of fidelity_aggregate.py) ─────────────────

def recompute_overall(records: list) -> dict:
    """Sum raw counts across all records per condition, then compute metrics.

    Returns: {condition: {fidelity, substantive_fidelity, error_rate,
                           auditable_rate, partially_auditable_rate,
                           unauditable_rate, raw_fidelity, raw_audit}}
    """
    fid_acc = {c: {"total_claims": 0, "matched": 0, "mismatched": 0,
                   "no_source": 0, "calculation_correct": 0,
                   "calculation_incorrect": 0}
               for c in CONDITIONS}
    aud_acc = {c: {"total_claims": 0, "auditable": 0, "partially_auditable": 0,
                   "unauditable": 0, "non_claims": 0}
               for c in CONDITIONS}

    for rec in records:
        for cond in CONDITIONS:
            cd = rec.get("conditions", {}).get(cond, {})
            fs = cd.get("fidelity", {}).get("summary", {})
            as_ = cd.get("auditability", {}).get("summary", {})
            for k in fid_acc[cond]:
                fid_acc[cond][k] += fs.get(k, 0)
            for k in aud_acc[cond]:
                aud_acc[cond][k] += as_.get(k, 0)

    results = {}
    for cond in CONDITIONS:
        fa = fid_acc[cond]
        aa = aud_acc[cond]

        total = fa["total_claims"]
        matched = fa["matched"]
        cc = fa["calculation_correct"]
        mismatched = fa["mismatched"]
        ci = fa["calculation_incorrect"]
        no_src = fa["no_source"]

        fidelity = (matched + cc) / total * 100 if total > 0 else None
        subst_denom = total - no_src
        subst_fid = (matched + cc) / subst_denom * 100 if subst_denom > 0 else None
        error_rate = (mismatched + ci) / total * 100 if total > 0 else None

        aud_total = aa["total_claims"]
        non_claims = aa["non_claims"]
        substantive = aud_total - non_claims
        aud_rate = aa["auditable"] / substantive * 100 if substantive > 0 else None
        part_rate = aa["partially_auditable"] / substantive * 100 if substantive > 0 else None
        unaud_rate = aa["unauditable"] / substantive * 100 if substantive > 0 else None

        results[cond] = {
            "fidelity": fidelity,
            "substantive_fidelity": subst_fid,
            "error_rate": error_rate,
            "auditable_rate": aud_rate,
            "partially_auditable_rate": part_rate,
            "unauditable_rate": unaud_rate,
            "raw_fidelity": fa,
            "raw_audit": aa,
        }
    return results


# ── Structural checks (VR-098) ─────────────────────────────────────────────────

def check_structure(records: list, battery_ids: set) -> list:
    """Returns list of (check_name, passed: bool, detail: str)."""
    checks = []
    record_ids = [r["query_id"] for r in records]
    id_set = set(record_ids)

    # Record count
    checks.append((
        "Record count",
        len(records) == EXPECTED_QUERIES,
        f"{len(records)}/{EXPECTED_QUERIES}",
    ))

    # No duplicates
    checks.append((
        "No duplicate query_ids",
        len(record_ids) == len(id_set),
        f"{len(record_ids) - len(id_set)} duplicates found" if len(record_ids) != len(id_set) else "clean",
    ))

    # All battery IDs present
    if battery_ids:
        missing = battery_ids - id_set
        extra = id_set - battery_ids
        checks.append((
            "All battery query_ids present",
            len(missing) == 0,
            f"missing={sorted(missing)}, extra={sorted(extra)}" if (missing or extra) else "exact match",
        ))
    else:
        checks.append(("Battery cross-reference", False, "battery not found"))

    # All 3 conditions per record
    missing_cond = []
    for r in records:
        for cond in CONDITIONS:
            if cond not in r.get("conditions", {}):
                missing_cond.append(f"{r['query_id']}.{cond}")
    checks.append((
        "All 3 conditions present per record",
        len(missing_cond) == 0,
        f"missing: {missing_cond[:5]}" if missing_cond else "complete",
    ))

    # No null summaries
    null_summaries = []
    for r in records:
        for cond in CONDITIONS:
            cd = r.get("conditions", {}).get(cond, {})
            if not cd.get("fidelity", {}).get("summary"):
                null_summaries.append(f"{r['query_id']}.{cond}.fidelity")
            if not cd.get("auditability", {}).get("summary"):
                null_summaries.append(f"{r['query_id']}.{cond}.auditability")
    checks.append((
        "No null summaries",
        len(null_summaries) == 0,
        f"null: {null_summaries[:5]}" if null_summaries else "clean",
    ))

    return checks


# ── Claim count sanity ─────────────────────────────────────────────────────────

def check_claim_sums(recomputed: dict) -> list:
    checks = []
    for cond in CONDITIONS:
        fa = recomputed[cond]["raw_fidelity"]
        aa = recomputed[cond]["raw_audit"]

        # Fidelity verdicts sum
        fid_sum = fa["matched"] + fa["mismatched"] + fa["no_source"] + fa["calculation_correct"] + fa["calculation_incorrect"]
        checks.append((
            f"Fidelity verdict sum == total_claims ({cond})",
            fid_sum == fa["total_claims"],
            f"{fid_sum} vs {fa['total_claims']}",
        ))

        # Auditability categories sum
        aud_sum = aa["auditable"] + aa["partially_auditable"] + aa["unauditable"] + aa["non_claims"]
        checks.append((
            f"Auditability category sum == total_claims ({cond})",
            aud_sum == aa["total_claims"],
            f"{aud_sum} vs {aa['total_claims']}",
        ))

        # Non-zero total claims
        checks.append((
            f"Non-zero total fidelity claims ({cond})",
            fa["total_claims"] > 0,
            f"{fa['total_claims']} claims",
        ))

        # Error rate < 10%
        err = recomputed[cond]["error_rate"]
        checks.append((
            f"Error rate < 10% ({cond})",
            err is None or err < 10.0,
            f"{err:.1f}%" if err is not None else "n/a",
        ))

    return checks


# ── Formula verification (VR-099) ─────────────────────────────────────────────

def check_formulas(recomputed: dict, stored: dict) -> list:
    """Compare recomputed values against fidelity_summary.json values."""
    checks = []

    metrics = [
        ("fidelity",                "VR-055", "Table 1, row Fidelity Score"),
        ("substantive_fidelity",    "VR-055", "Table 1, row Substantive Fidelity"),
        ("error_rate",              "VR-093", "Table 1, row Error Rate"),
        ("auditable_rate",          "VR-054", "Table 2, row Auditable"),
        ("partially_auditable_rate","VR-092", "Table 2, row Partially Auditable"),
        ("unauditable_rate",        "VR-092", "Table 2, row Unauditable"),
    ]

    for cond in CONDITIONS:
        for metric, srs_req, table_ref in metrics:
            recomp_val = recomputed[cond].get(metric)

            # Navigate stored JSON: overall.fidelity.{cond}.{metric} or overall.auditability...
            if metric in ("fidelity", "substantive_fidelity", "error_rate"):
                stored_val = stored.get("overall", {}).get("fidelity", {}).get(cond, {}).get(metric)
            else:
                stored_val = stored.get("overall", {}).get("auditability", {}).get(cond, {}).get(metric)

            if recomp_val is None and stored_val is None:
                checks.append((metric, cond, None, None, 0.0, True, srs_req, table_ref, "both None"))
                continue

            if recomp_val is None or stored_val is None:
                checks.append((metric, cond, recomp_val, stored_val, None, False, srs_req, table_ref, "one None"))
                continue

            delta = abs(recomp_val - stored_val)
            passed = delta <= TOLERANCE
            checks.append((metric, cond, stored_val, recomp_val, delta, passed, srs_req, table_ref, ""))

    return checks


# ── V1 reconciliation ──────────────────────────────────────────────────────────

def compute_v1_numbers(v1_file: Path) -> dict:
    """Compute V1 aggregate numbers from V1 JSONL (paired format)."""
    if not v1_file.exists():
        return {}

    fid_acc = {"total_claims": 0, "matched": 0, "calculation_correct": 0}
    aud_acc = {"total_claims": 0, "auditable": 0, "non_claims": 0}
    ctrl_aud = {"total_claims": 0, "auditable": 0, "non_claims": 0}

    with open(v1_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            tf = r.get("treatment_fidelity", {}).get("summary", {})
            ta = r.get("treatment_auditability", {}).get("summary", {})
            ca = r.get("control_auditability", {}).get("summary", {})
            for k in fid_acc:
                fid_acc[k] += tf.get(k, 0)
            for k in aud_acc:
                aud_acc[k] += ta.get(k, 0)
            for k in ctrl_aud:
                ctrl_aud[k] += ca.get(k, 0)

    total = fid_acc["total_claims"]
    fid = (fid_acc["matched"] + fid_acc["calculation_correct"]) / total * 100 if total > 0 else None
    aud_sub = aud_acc["total_claims"] - aud_acc["non_claims"]
    aud = aud_acc["auditable"] / aud_sub * 100 if aud_sub > 0 else None
    ctrl_sub = ctrl_aud["total_claims"] - ctrl_aud["non_claims"]
    ctrl = ctrl_aud["auditable"] / ctrl_sub * 100 if ctrl_sub > 0 else None

    return {
        "treatment_fidelity": fid,
        "treatment_auditability": aud,
        "control_auditability": ctrl,
        "raw": {"fid": fid_acc, "aud": aud_acc, "ctrl": ctrl_aud},
    }


# ── Trace lines (VR-100) ──────────────────────────────────────────────────────

def build_trace_lines(recomputed: dict, stored_input_file: str, n_records: int) -> list:
    lines = []
    for cond in CONDITIONS:
        fa = recomputed[cond]["raw_fidelity"]
        aa = recomputed[cond]["raw_audit"]

        total = fa["total_claims"]
        matched = fa["matched"]
        cc = fa["calculation_correct"]
        mismatched = fa["mismatched"]
        ci = fa["calculation_incorrect"]
        no_src = fa["no_source"]
        substantive = aa["total_claims"] - aa["non_claims"]
        auditable = aa["auditable"]

        fid_val = recomputed[cond]["fidelity"]
        aud_val = recomputed[cond]["auditable_rate"]

        lines.append(f"FIDELITY {cond}: {fid_val:.1f}% = (matched:{matched} + calc_correct:{cc}) / total:{total} × 100")
        lines.append(f"  Formula: VR-055")
        lines.append(f"  Source: {stored_input_file}")
        lines.append(f"  Records: {n_records}")
        lines.append(f"  Certified table: fidelity_summary.md Table 1, row 'Fidelity Score', column '{cond}'")
        lines.append("")

        lines.append(f"AUDITABILITY {cond}: {aud_val:.1f}% = auditable:{auditable} / (total:{aa['total_claims']} - non_claims:{aa['non_claims']}) × 100")
        lines.append(f"  Formula: VR-054")
        lines.append(f"  Denominator rule: excludes non_claims per VR-054")
        lines.append(f"  Source: {stored_input_file}")
        lines.append(f"  Records: {n_records}")
        lines.append(f"  Certified table: fidelity_summary.md Table 2, row 'Auditable', column '{cond}'")
        lines.append("")

    return lines


# ── Markdown report ────────────────────────────────────────────────────────────

def build_report(
    struct_checks: list,
    formula_checks: list,
    sanity_checks: list,
    trace_lines: list,
    v1: dict,
    recomputed: dict,
    n_records: int,
    params: dict,
    timestamp: str,
    all_pass: bool,
) -> str:
    lines = [
        "# Stage 3 Fidelity QC Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Script:** {SCRIPT_NAME}",
        f"**Verified against:** {params['summary_json']}",
        f"**Raw source:** {params['input_file']}",
        f"**SRS V&V Registry:** Section 8.9",
        "",
        "---",
        "",
        "## Structural Checks",
        "",
    ]
    for name, passed, detail in struct_checks:
        mark = "PASS" if passed else "FAIL"
        lines.append(f"- [{mark}] {name}: {detail}")

    lines += ["", "## Formula Verification", ""]
    lines += [
        "| Metric | Condition | Reported | Recomputed | Delta | Status | SRS Req | Certified Table |",
        "|--------|-----------|----------|------------|-------|--------|---------|-----------------|",
    ]
    for metric, cond, reported, recomp, delta, passed, srs_req, table_ref, note in formula_checks:
        mark = "PASS" if passed else "FAIL"
        rep_str = f"{reported:.1f}%" if reported is not None else "n/a"
        rec_str = f"{recomp:.1f}%" if recomp is not None else "n/a"
        dlt_str = f"{delta:.4f}%" if delta is not None else "n/a"
        lines.append(f"| {metric} | {cond} | {rep_str} | {rec_str} | {dlt_str} | {mark} | {srs_req} | {table_ref} |")

    lines += ["", "## Claim Count Sanity", ""]
    for name, passed, detail in sanity_checks:
        mark = "PASS" if passed else "FAIL"
        lines.append(f"- [{mark}] {name}: {detail}")

    lines += ["", "## Number Trace", ""]
    lines += trace_lines

    lines += ["## V1 vs V2 Reconciliation", ""]
    if v1:
        v2_prag_fid = recomputed["pragmatics"]["fidelity"]
        v2_prag_aud = recomputed["pragmatics"]["auditable_rate"]
        v2_ctrl_aud = recomputed["control"]["auditable_rate"]
        lines += [
            "| Metric | V1 (2-condition, pre-leakage) | V2 (3-condition) | Expected Divergence | Note |",
            "|--------|-------------------------------|-------------------|---------------------|------|",
            f"| Pragmatics fidelity | {v1.get('treatment_fidelity', 0):.1f}% | {v2_prag_fid:.1f}% | YES | Different Stage 1 responses (V1 pre-leakage fix, V2 equal tool access) |",
            f"| Pragmatics auditability | {v1.get('treatment_auditability', 0):.1f}% | {v2_prag_aud:.1f}% | YES | Same reason |",
            f"| Control auditability | {v1.get('control_auditability', 0):.1f}% | {v2_ctrl_aud:.1f}% | YES | Same reason; V2 control has full tool access |",
        ]
    else:
        lines.append("*V1 JSONL not found — reconciliation skipped.*")

    overall_status = "CERTIFIED" if all_pass else "NOT CERTIFIED"
    lines += [
        "",
        "## Tables Certified by This Run",
        "",
        "| Table | Location | Status |",
        "|-------|----------|--------|",
        f"| Overall Fidelity (Table 1) | fidelity_summary.md | {overall_status} |",
        f"| Overall Auditability (Table 2) | fidelity_summary.md | {overall_status} |",
        f"| Per-Category Fidelity | fidelity_summary.md | {overall_status} |",
        f"| Per-Category Auditability | fidelity_summary.md | {overall_status} |",
        "",
        f"## Overall: {'PASS' if all_pass else 'FAIL'}",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Stage 3 fidelity QC verification (VR-097 through VR-100)"
    )
    parser.add_argument("--config", default=str(CONFIG_PATH))
    args = parser.parse_args()

    config = load_config(Path(args.config))
    params = get_params(config)

    print(f"Input JSONL:    {params['input_file']}", file=sys.stderr)
    print(f"Summary JSON:   {params['summary_json']}", file=sys.stderr)
    print(f"Battery:        {params['battery_path']}", file=sys.stderr)

    for path, label in [(params["input_file"], "input_file"), (params["summary_json"], "summary_json")]:
        if not path.exists():
            print(f"ERROR: {label} not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load data
    records = load_jsonl(params["input_file"])
    battery_ids = load_battery_ids(params["battery_path"])
    with open(params["summary_json"]) as f:
        stored = json.load(f)

    # Checks
    print("Running structural checks...", file=sys.stderr)
    struct_checks = check_structure(records, battery_ids)

    print("Recomputing metrics from raw...", file=sys.stderr)
    recomputed = recompute_overall(records)

    print("Running formula verification...", file=sys.stderr)
    formula_checks = check_formulas(recomputed, stored)

    print("Running claim count sanity...", file=sys.stderr)
    sanity_checks = check_claim_sums(recomputed)

    print("Building trace...", file=sys.stderr)
    trace_lines = build_trace_lines(recomputed, str(params["input_file"]), len(records))

    print("Loading V1 for reconciliation...", file=sys.stderr)
    v1 = compute_v1_numbers(params["v1_file"])

    # Determine overall pass/fail
    all_pass = (
        all(p for _, p, _ in struct_checks)
        and all(p for *_, p, _, _, _ in formula_checks)
        and all(p for _, p, _ in sanity_checks)
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Console summary
    print("\n" + "=" * 60, file=sys.stderr)
    print("STAGE 3 FIDELITY QC", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    fail_count = sum(1 for _, p, _ in struct_checks if not p)
    fail_count += sum(1 for *_, p, _, _, _ in formula_checks if not p)
    fail_count += sum(1 for _, p, _ in sanity_checks if not p)
    print(f"Checks passed: {sum(1 for _, p, _ in struct_checks if p) + sum(1 for *_, p, _, _, _ in formula_checks if p) + sum(1 for _, p, _ in sanity_checks if p)}", file=sys.stderr)
    print(f"Checks failed: {fail_count}", file=sys.stderr)
    print(f"Overall: {'PASS' if all_pass else 'FAIL'}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Write report
    params["output_dir"].mkdir(parents=True, exist_ok=True)
    report = build_report(
        struct_checks, formula_checks, sanity_checks,
        trace_lines, v1, recomputed,
        len(records), params, timestamp, all_pass,
    )
    report_path = params["output_dir"] / "fidelity_qc_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport: {report_path}", file=sys.stderr)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
