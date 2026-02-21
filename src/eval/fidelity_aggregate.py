#!/usr/bin/env python3
"""Stage 3 fidelity aggregate analysis.

Loads the V2 FidelityRecord JSONL produced by fidelity_check.py and computes
per-condition fidelity scores, substantive fidelity, error rates, and
auditability — overall and by query category.

Outputs:
  results/{run}/stage3/analysis/fidelity_summary.md
  results/{run}/stage3/analysis/fidelity_summary.json

SRS: VR-091 through VR-096
Config: judge_config.yaml fidelity.aggregate section
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
SCRIPT_NAME = "src/eval/fidelity_aggregate.py"
SRS_REFS = "VR-091 through VR-096"


# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_aggregate_params(config: dict) -> dict:
    """Extract fidelity.aggregate section from config."""
    agg = config.get("fidelity", {}).get("aggregate", {})
    if not agg.get("input_file"):
        raise ValueError(
            "fidelity.aggregate.input_file not found in config. "
            "Add it to judge_config.yaml under fidelity: aggregate:"
        )
    return {
        "input_file": Path(agg["input_file"]),
        "output_dir": Path(agg.get("output_dir", "results/v2_redo/stage3/analysis")),
        "battery_path": Path(agg.get("battery_path", "src/eval/battery/queries.yaml")),
    }


# ── Data loading ───────────────────────────────────────────────────────────────

def load_records(path: Path) -> list:
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_battery(path: Path) -> dict:
    """Load battery YAML → {query_id: {text, category}}."""
    if not path.exists():
        print(f"  Warning: battery not found at {path}", file=sys.stderr)
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    result = {}
    for q in data.get("queries", []):
        qid = q.get("id") or q.get("query_id")
        if qid:
            result[qid] = {
                "text": q.get("text") or q.get("query_text", ""),
                "category": q.get("category", "unknown"),
            }
    return result


# ── Accumulator helpers ────────────────────────────────────────────────────────

def _empty_fidelity_acc() -> dict:
    return {
        "total_claims": 0,
        "matched": 0,
        "mismatched": 0,
        "no_source": 0,
        "calculation_correct": 0,
        "calculation_incorrect": 0,
    }


def _empty_auditability_acc() -> dict:
    return {
        "total_claims": 0,
        "auditable": 0,
        "partially_auditable": 0,
        "unauditable": 0,
        "non_claims": 0,
    }


def _add_counts(acc: dict, summary: dict) -> None:
    for k in acc:
        acc[k] += summary.get(k, 0)


# ── Computations (VR-070, VR-071, VR-072) ─────────────────────────────────────

def compute_fidelity_stats(acc: dict) -> dict:
    """VR-055, VR-070, VR-072."""
    total = acc["total_claims"]
    matched = acc["matched"]
    calc_correct = acc["calculation_correct"]
    mismatched = acc["mismatched"]
    calc_incorrect = acc["calculation_incorrect"]
    no_source = acc["no_source"]

    fidelity = (matched + calc_correct) / total * 100 if total > 0 else None
    substantive_denom = total - no_source
    substantive_fidelity = (
        (matched + calc_correct) / substantive_denom * 100
        if substantive_denom > 0 else None
    )
    error_rate = (mismatched + calc_incorrect) / total * 100 if total > 0 else None

    return {
        "total_claims": total,
        "matched": matched,
        "calculation_correct": calc_correct,
        "mismatched": mismatched,
        "calculation_incorrect": calc_incorrect,
        "no_source": no_source,
        "fidelity": fidelity,
        "substantive_fidelity": substantive_fidelity,
        "error_rate": error_rate,
    }


def compute_auditability_stats(acc: dict) -> dict:
    """VR-054, VR-071."""
    total = acc["total_claims"]
    auditable = acc["auditable"]
    partially = acc["partially_auditable"]
    unauditable = acc["unauditable"]
    non_claims = acc["non_claims"]

    # VR-054: exclude non_claims from denominator
    substantive = total - non_claims
    auditable_rate = auditable / substantive * 100 if substantive > 0 else None
    partially_rate = partially / substantive * 100 if substantive > 0 else None
    unauditable_rate = unauditable / substantive * 100 if substantive > 0 else None

    return {
        "total_claims": total,
        "substantive_claims": substantive,
        "auditable": auditable,
        "auditable_rate": auditable_rate,
        "partially_auditable": partially,
        "partially_auditable_rate": partially_rate,
        "unauditable": unauditable,
        "unauditable_rate": unauditable_rate,
        "non_claims": non_claims,
    }


# ── Aggregation ────────────────────────────────────────────────────────────────

def aggregate_records(records: list, battery: dict) -> tuple:
    """Aggregate FidelityRecords into overall and per-category accumulators.

    Returns:
        overall:   {condition: {fidelity: acc, auditability: acc}}
        by_cat:    {category: {condition: {fidelity: acc, auditability: acc}}}
        n_records: int
    """
    overall = {
        cond: {
            "fidelity": _empty_fidelity_acc(),
            "auditability": _empty_auditability_acc(),
        }
        for cond in CONDITIONS
    }
    by_cat: dict = {}

    for rec in records:
        qid = rec["query_id"]
        category = rec.get("category") or battery.get(qid, {}).get("category", "unknown")
        if not category:
            category = "unknown"

        if category not in by_cat:
            by_cat[category] = {
                cond: {
                    "fidelity": _empty_fidelity_acc(),
                    "auditability": _empty_auditability_acc(),
                }
                for cond in CONDITIONS
            }

        conditions_data = rec.get("conditions", {})
        for cond in CONDITIONS:
            cond_data = conditions_data.get(cond, {})
            fid_summary = cond_data.get("fidelity", {}).get("summary", {})
            aud_summary = cond_data.get("auditability", {}).get("summary", {})
            _add_counts(overall[cond]["fidelity"], fid_summary)
            _add_counts(overall[cond]["auditability"], aud_summary)
            _add_counts(by_cat[category][cond]["fidelity"], fid_summary)
            _add_counts(by_cat[category][cond]["auditability"], aud_summary)

    return overall, by_cat, len(records)


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _pct(v) -> str:
    return "n/a" if v is None else f"{v:.1f}%"


def _fidelity_table(stats: dict) -> list:
    c, r, p = stats["control"], stats["rag"], stats["pragmatics"]
    return [
        "| Metric               | Control | RAG     | Pragmatics |",
        "|----------------------|---------|---------|------------|",
        f"| Total Claims         | {c['total_claims']:>7} | {r['total_claims']:>7} | {p['total_claims']:>10} |",
        f"| Matched              | {c['matched']:>7} | {r['matched']:>7} | {p['matched']:>10} |",
        f"| Calc Correct         | {c['calculation_correct']:>7} | {r['calculation_correct']:>7} | {p['calculation_correct']:>10} |",
        f"| Mismatched           | {c['mismatched']:>7} | {r['mismatched']:>7} | {p['mismatched']:>10} |",
        f"| Calc Incorrect       | {c['calculation_incorrect']:>7} | {r['calculation_incorrect']:>7} | {p['calculation_incorrect']:>10} |",
        f"| No Source            | {c['no_source']:>7} | {r['no_source']:>7} | {p['no_source']:>10} |",
        f"| **Fidelity Score**   | {_pct(c['fidelity']):>7} | {_pct(r['fidelity']):>7} | {_pct(p['fidelity']):>10} |",
        f"| Substantive Fidelity | {_pct(c['substantive_fidelity']):>7} | {_pct(r['substantive_fidelity']):>7} | {_pct(p['substantive_fidelity']):>10} |",
        f"| Error Rate           | {_pct(c['error_rate']):>7} | {_pct(r['error_rate']):>7} | {_pct(p['error_rate']):>10} |",
    ]


def _auditability_table(stats: dict) -> list:
    c, r, p = stats["control"], stats["rag"], stats["pragmatics"]
    return [
        "| Metric               | Control | RAG     | Pragmatics |",
        "|----------------------|---------|---------|------------|",
        f"| Substantive Claims   | {c['substantive_claims']:>7} | {r['substantive_claims']:>7} | {p['substantive_claims']:>10} |",
        f"| Auditable            | {_pct(c['auditable_rate']):>7} | {_pct(r['auditable_rate']):>7} | {_pct(p['auditable_rate']):>10} |",
        f"| Partially Auditable  | {_pct(c['partially_auditable_rate']):>7} | {_pct(r['partially_auditable_rate']):>7} | {_pct(p['partially_auditable_rate']):>10} |",
        f"| Unauditable          | {_pct(c['unauditable_rate']):>7} | {_pct(r['unauditable_rate']):>7} | {_pct(p['unauditable_rate']):>10} |",
        f"| Non-Claims (excl.)   | {c['non_claims']:>7} | {r['non_claims']:>7} | {p['non_claims']:>10} |",
    ]


# ── Markdown output ────────────────────────────────────────────────────────────

def build_markdown(
    overall_fid: dict,
    overall_aud: dict,
    cat_fid: dict,
    cat_aud: dict,
    n_records: int,
    input_file: Path,
    timestamp: str,
) -> str:
    lines = [
        "# Stage 3 Fidelity Aggregate Analysis",
        "",
        f"**Input:** {input_file}",
        f"**Records:** {n_records} queries",
        f"**Generated:** {timestamp}",
        f"**Script:** {SCRIPT_NAME}",
        f"**Governing SRS:** {SRS_REFS}",
        "",
        "---",
        "",
        "## Overall Fidelity",
        "",
    ]
    lines += _fidelity_table(overall_fid)
    lines += ["", "## Overall Auditability", ""]
    lines += _auditability_table(overall_aud)
    lines += [""]

    for cat in sorted(cat_fid.keys()):
        lines += [
            "---",
            "",
            f"## Category: {cat}",
            "",
            "### Fidelity",
            "",
        ]
        lines += _fidelity_table(cat_fid[cat])
        lines += ["", "### Auditability", ""]
        lines += _auditability_table(cat_aud[cat])
        lines += [""]

    lines += [
        "---",
        f"*Generated: {timestamp}*",
        f"*Script: {SCRIPT_NAME}*",
        f"*SRS: {SRS_REFS}*",
    ]
    return "\n".join(lines)


# ── JSON output ────────────────────────────────────────────────────────────────

def build_json_output(
    overall_fid: dict,
    overall_aud: dict,
    cat_fid: dict,
    cat_aud: dict,
    n_records: int,
    input_file: Path,
    timestamp: str,
) -> dict:
    return {
        "metadata": {
            "input_file": str(input_file),
            "n_records": n_records,
            "generated": timestamp,
            "script": SCRIPT_NAME,
            "srs_references": ["VR-070", "VR-071", "VR-072", "VR-073", "VR-074", "VR-075"],
        },
        "overall": {
            "fidelity": overall_fid,
            "auditability": overall_aud,
        },
        "by_category": {
            cat: {
                "fidelity": cat_fid[cat],
                "auditability": cat_aud[cat],
            }
            for cat in sorted(cat_fid.keys())
        },
    }


# ── Console summary ────────────────────────────────────────────────────────────

def print_summary(overall_fid: dict, overall_aud: dict) -> None:
    print("\n" + "=" * 66)
    print("STAGE 3 FIDELITY AGGREGATE ANALYSIS")
    print("=" * 66)

    hdr = f"  {'Metric':<22} {'Control':>9} {'RAG':>9} {'Pragmatics':>12}"
    sep = "  " + "-" * (len(hdr) - 2)

    c, r, p = overall_fid["control"], overall_fid["rag"], overall_fid["pragmatics"]
    print("\n[FIDELITY]")
    print(hdr)
    print(sep)
    print(f"  {'Total Claims':<22} {c['total_claims']:>9} {r['total_claims']:>9} {p['total_claims']:>12}")
    print(f"  {'Matched':<22} {c['matched']:>9} {r['matched']:>9} {p['matched']:>12}")
    print(f"  {'Calc Correct':<22} {c['calculation_correct']:>9} {r['calculation_correct']:>9} {p['calculation_correct']:>12}")
    print(f"  {'Mismatched':<22} {c['mismatched']:>9} {r['mismatched']:>9} {p['mismatched']:>12}")
    print(f"  {'Calc Incorrect':<22} {c['calculation_incorrect']:>9} {r['calculation_incorrect']:>9} {p['calculation_incorrect']:>12}")
    print(f"  {'No Source':<22} {c['no_source']:>9} {r['no_source']:>9} {p['no_source']:>12}")
    print(sep)
    print(f"  {'Fidelity Score':<22} {_pct(c['fidelity']):>9} {_pct(r['fidelity']):>9} {_pct(p['fidelity']):>12}")
    print(f"  {'Substantive Fidelity':<22} {_pct(c['substantive_fidelity']):>9} {_pct(r['substantive_fidelity']):>9} {_pct(p['substantive_fidelity']):>12}")
    print(f"  {'Error Rate':<22} {_pct(c['error_rate']):>9} {_pct(r['error_rate']):>9} {_pct(p['error_rate']):>12}")

    ca, ra, pa = overall_aud["control"], overall_aud["rag"], overall_aud["pragmatics"]
    print("\n[AUDITABILITY]")
    print(hdr)
    print(sep)
    print(f"  {'Substantive Claims':<22} {ca['substantive_claims']:>9} {ra['substantive_claims']:>9} {pa['substantive_claims']:>12}")
    print(f"  {'Auditable':<22} {_pct(ca['auditable_rate']):>9} {_pct(ra['auditable_rate']):>9} {_pct(pa['auditable_rate']):>12}")
    print(f"  {'Partially Auditable':<22} {_pct(ca['partially_auditable_rate']):>9} {_pct(ra['partially_auditable_rate']):>9} {_pct(pa['partially_auditable_rate']):>12}")
    print(f"  {'Unauditable':<22} {_pct(ca['unauditable_rate']):>9} {_pct(ra['unauditable_rate']):>9} {_pct(pa['unauditable_rate']):>12}")
    print(f"  {'Non-Claims (excl.)':<22} {ca['non_claims']:>9} {ra['non_claims']:>9} {pa['non_claims']:>12}")
    print("=" * 66)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Stage 3 fidelity aggregate analysis (VR-070 through VR-075)"
    )
    parser.add_argument(
        "--config", default=str(CONFIG_PATH),
        help="Path to judge_config.yaml",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))
    params = get_aggregate_params(config)

    input_file = params["input_file"]
    output_dir = params["output_dir"]
    battery_path = params["battery_path"]

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Input:   {input_file}", file=sys.stderr)
    print(f"Output:  {output_dir}", file=sys.stderr)
    print(f"Battery: {battery_path}", file=sys.stderr)

    print("\nLoading battery...", file=sys.stderr)
    battery = load_battery(battery_path)
    print(f"  {len(battery)} queries in battery", file=sys.stderr)

    print("Loading fidelity records...", file=sys.stderr)
    records = load_records(input_file)
    print(f"  {len(records)} records loaded", file=sys.stderr)

    # Validate V2 format
    if records and "conditions" not in records[0]:
        print(
            "ERROR: Records appear to be V1 format (no 'conditions' field). "
            "fidelity_aggregate.py requires V2 FidelityRecord format.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Aggregating...", file=sys.stderr)
    overall_acc, by_cat_acc, n_records = aggregate_records(records, battery)

    categories = sorted(by_cat_acc.keys())
    print(f"  Categories: {categories}", file=sys.stderr)

    # Compute stats
    overall_fid = {cond: compute_fidelity_stats(overall_acc[cond]["fidelity"]) for cond in CONDITIONS}
    overall_aud = {cond: compute_auditability_stats(overall_acc[cond]["auditability"]) for cond in CONDITIONS}

    cat_fid = {
        cat: {cond: compute_fidelity_stats(by_cat_acc[cat][cond]["fidelity"]) for cond in CONDITIONS}
        for cat in categories
    }
    cat_aud = {
        cat: {cond: compute_auditability_stats(by_cat_acc[cat][cond]["auditability"]) for cond in CONDITIONS}
        for cat in categories
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Console summary
    print_summary(overall_fid, overall_aud)

    # Write outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    md_content = build_markdown(
        overall_fid, overall_aud, cat_fid, cat_aud,
        n_records, input_file, timestamp,
    )
    md_path = output_dir / "fidelity_summary.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"\nMarkdown: {md_path}", file=sys.stderr)

    json_data = build_json_output(
        overall_fid, overall_aud, cat_fid, cat_aud,
        n_records, input_file, timestamp,
    )
    json_path = output_dir / "fidelity_summary.json"
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"JSON:     {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
