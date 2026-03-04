#!/usr/bin/env python3
"""Supplementary analysis: inter-judge agreement (Kendall's W) and rank-biserial r.

Loads Stage 2 pairwise comparison JSONL files and computes:

  1. Kendall's W (coefficient of concordance) across 3 judge vendors
     - Per condition (do vendors agree on which queries score high/low?)
     - Per pairwise delta (do vendors agree on treatment effect per query?)

  2. Rank-biserial correlation (r) from Wilcoxon signed-rank tests
     - Nonparametric effect size appropriate for ordinal/bounded data
     - Complements Cohen's d (which assumes interval scale)
     - r = 1 - (2W / (n * (n + 1) / 2)) where W = Wilcoxon statistic,
       n = number of non-zero differences

Reuses data loading and aggregation from aggregate_analysis.py.

SRS: VR-110, VR-111, VR-112

Usage:
    cd /path/to/census-mcp-server
    python src/eval/judge_agreement_analysis.py

Output:
    results/v2_redo/stage2/analysis/judge_agreement.json
    results/v2_redo/stage2/analysis/judge_agreement.md
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import __version__ as scipy_version
from scipy.stats import rankdata
from scipy.stats import chi2 as chi2_dist

# Reuse loading infrastructure
from aggregate_analysis import (
    CONDITIONS,
    COMPARISON_NAMES,
    PAIRS,
    CONFIG_PATH,
    DEFAULT_STAGE2_DIR,
    discover_stage2_files,
    load_config,
    load_records,
    get_analysis_params,
    _json_default,
)

VENDORS = ["anthropic", "openai", "google"]


# ── Data extraction by vendor ──────────────────────────────────────────────────

def extract_vendor_medians(files: dict, dimensions: list) -> tuple:
    """Extract per-vendor, per-query, per-condition median scores.

    For each vendor, across all passes and presentation orders for that vendor,
    compute the median score per (query, condition, dimension).

    Returns:
        vendor_scores[vendor][condition][query_id][dimension] = median_score
        vendor_cqs[vendor][condition][query_id] = mean of dimension medians
    """
    # Collect raw scores: raw[vendor][qid][condition][dim] = [scores]
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for comparison, path in files.items():
        records = load_records(path)
        for r in records:
            if not r.get("parse_success", False):
                continue
            vendor = r["judge_vendor"]
            qid = r["query_id"]
            for label_key, scores_key in [
                ("response_a_label", "scores_response_a"),
                ("response_b_label", "scores_response_b"),
            ]:
                cond = r[label_key]
                for dim, entry in r[scores_key].items():
                    if dim in dimensions:
                        raw[vendor][qid][cond][dim].append(entry["score"])

    # Aggregate to medians
    vendor_scores = {}
    vendor_cqs = {}
    for vendor in VENDORS:
        vendor_scores[vendor] = defaultdict(lambda: defaultdict(dict))
        vendor_cqs[vendor] = defaultdict(dict)
        for qid in raw[vendor]:
            for cond in CONDITIONS:
                dim_meds = {}
                for dim in dimensions:
                    vals = raw[vendor][qid][cond].get(dim, [])
                    dim_meds[dim] = float(np.median(vals)) if vals else float("nan")
                vendor_scores[vendor][cond][qid] = dim_meds
                valid = [v for v in dim_meds.values() if not np.isnan(v)]
                vendor_cqs[vendor][cond][qid] = float(np.mean(valid)) if valid else float("nan")

    return vendor_scores, vendor_cqs


# ── Kendall's W ────────────────────────────────────────────────────────────────

def kendalls_w(ratings_matrix: np.ndarray) -> tuple:
    """Compute Kendall's W (coefficient of concordance).

    Args:
        ratings_matrix: shape (k_judges, n_items). Each row is one judge's
                        ratings/rankings of n items.

    Returns:
        (W, chi2, p, k, n)
        W: Kendall's W [0, 1]
        chi2: Friedman chi-squared statistic
        p: p-value from chi-squared approximation with (n-1) df
        k: number of judges
        n: number of items
    """
    k, n = ratings_matrix.shape
    if k < 2 or n < 2:
        return float("nan"), float("nan"), float("nan"), k, n

    # Rank each judge's ratings
    ranked = np.array([rankdata(row) for row in ratings_matrix])

    # Sum of ranks per item
    R = ranked.sum(axis=0)
    R_mean = R.mean()

    # SS_between = sum of squared deviations of rank sums
    SS = np.sum((R - R_mean) ** 2)

    # W = 12 * SS / (k^2 * (n^3 - n))
    denom = k ** 2 * (n ** 3 - n)
    if denom == 0:
        return float("nan"), float("nan"), float("nan"), k, n
    W = (12.0 * SS) / denom

    # Chi-squared approximation: chi2 = k * (n - 1) * W
    chi2_val = k * (n - 1) * W

    # p-value from chi-squared distribution with (n-1) df
    p = 1.0 - chi2_dist.cdf(chi2_val, df=n - 1)

    return float(W), float(chi2_val), float(p), int(k), int(n)


def compute_agreement(vendor_cqs: dict, vendor_scores: dict,
                      dimensions: list) -> dict:
    """Compute Kendall's W for CQS and each dimension."""
    results = {}

    # Get common query IDs across all vendors and conditions
    all_qids = set()
    for vendor in VENDORS:
        for cond in CONDITIONS:
            all_qids.update(vendor_cqs[vendor][cond].keys())

    valid_qids = sorted([
        qid for qid in all_qids
        if all(
            not np.isnan(vendor_cqs[vendor].get(cond, {}).get(qid, float("nan")))
            for vendor in VENDORS
            for cond in CONDITIONS
        )
    ])

    n_queries = len(valid_qids)
    results["n_queries"] = n_queries
    results["n_vendors"] = len(VENDORS)
    results["vendors"] = VENDORS

    # Agreement on CQS per condition
    results["cqs_per_condition"] = {}
    for cond in CONDITIONS:
        matrix = np.array([
            [vendor_cqs[v][cond][qid] for qid in valid_qids]
            for v in VENDORS
        ])
        W, chi2_val, p, k, n = kendalls_w(matrix)
        results["cqs_per_condition"][cond] = {
            "W": W, "chi2": chi2_val, "p": p, "k": k, "n": n
        }

    # Agreement on pairwise CQS differences
    results["cqs_pairwise_deltas"] = {}
    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        matrix = np.array([
            [vendor_cqs[v][cond_a][qid] - vendor_cqs[v][cond_b][qid]
             for qid in valid_qids]
            for v in VENDORS
        ])
        W, chi2_val, p, k, n = kendalls_w(matrix)
        results["cqs_pairwise_deltas"][key] = {
            "W": W, "chi2": chi2_val, "p": p, "k": k, "n": n
        }

    # Per-dimension agreement
    results["per_dimension"] = {}
    for dim in dimensions:
        dim_results = {}
        for cond in CONDITIONS:
            matrix = np.array([
                [vendor_scores[v][cond][qid].get(dim, float("nan"))
                 for qid in valid_qids]
                for v in VENDORS
            ])
            col_mask = ~np.any(np.isnan(matrix), axis=0)
            matrix = matrix[:, col_mask]
            if matrix.shape[1] < 2:
                dim_results[cond] = {"W": float("nan"), "note": "insufficient data"}
                continue
            W, chi2_val, p, k, n = kendalls_w(matrix)
            dim_results[cond] = {"W": W, "chi2": chi2_val, "p": p, "k": k, "n": n}
        results["per_dimension"][dim] = dim_results

    return results


# ── Rank-biserial r ────────────────────────────────────────────────────────────

def rank_biserial_from_wilcoxon(wilcoxon_stat: float, n_nonzero: int) -> float:
    """Compute rank-biserial correlation from Wilcoxon signed-rank statistic.

    r = 1 - (2W / (n(n+1)/2))

    W is the Wilcoxon T statistic (smaller rank sum), n is non-zero differences.
    r in [-1, +1]. Positive = condition A systematically higher.
    """
    if n_nonzero < 1 or np.isnan(wilcoxon_stat):
        return float("nan")
    T_max = n_nonzero * (n_nonzero + 1) / 2.0
    r = 1.0 - (2.0 * wilcoxon_stat / T_max)
    return float(r)


def compute_rank_biserial(aggregate_json_path: Path) -> dict:
    """Read aggregate_statistics.json and compute rank-biserial r for all
    pairwise comparisons (CQS and per-dimension)."""
    with open(aggregate_json_path) as f:
        agg = json.load(f)

    results = {}

    # CQS pairwise
    results["cqs_pairwise"] = {}
    for key, pw in agg["cqs_pairwise"].items():
        W = pw.get("wilcoxon_stat")
        n_eff = pw.get("effective_n")
        r = rank_biserial_from_wilcoxon(W, n_eff) if W is not None and n_eff is not None else float("nan")
        results["cqs_pairwise"][key] = {
            "rank_biserial_r": r,
            "wilcoxon_stat": W,
            "effective_n": n_eff,
            "cohens_d": pw.get("cohens_d"),
            "interpretation": _interpret_r(r),
        }

    # Per-dimension
    results["per_dimension"] = {}
    for dim, dim_data in agg.get("per_dimension", {}).items():
        results["per_dimension"][dim] = {}
        for key, pw in dim_data.get("pairwise", {}).items():
            W = pw.get("wilcoxon_stat")
            n_eff = pw.get("effective_n")
            r = rank_biserial_from_wilcoxon(W, n_eff) if W is not None and n_eff is not None else float("nan")
            results["per_dimension"][dim][key] = {
                "rank_biserial_r": r,
                "wilcoxon_stat": W,
                "effective_n": n_eff,
                "cohens_d": pw.get("cohens_d"),
            }

    return results


def _interpret_r(r: float) -> str:
    """Kerby 2014 guidelines for rank-biserial r magnitude."""
    if np.isnan(r):
        return "n/a"
    ar = abs(r)
    if ar >= 0.5:
        return "large"
    elif ar >= 0.3:
        return "medium"
    elif ar >= 0.1:
        return "small"
    else:
        return "negligible"


# ── Output ─────────────────────────────────────────────────────────────────────

def build_markdown(agreement: dict, rank_biserial: dict) -> str:
    lines = []

    lines += [
        "# Supplementary Analysis: Judge Agreement & Nonparametric Effect Sizes",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"scipy {scipy_version}",
        "",
        "---",
        "",
        "## Inter-Judge Agreement (Kendall's W)",
        "",
        f"Vendors: {', '.join(agreement['vendors'])} | "
        f"Queries: {agreement['n_queries']}",
        "",
        "### CQS Agreement per Condition",
        "",
        f"| Condition | Kendall's W | chi2(df={agreement['n_queries'] - 1}) | p |",
        "|-----------|-------------|-----------|---|",
    ]

    for cond in CONDITIONS:
        r = agreement["cqs_per_condition"][cond]
        p_str = "< .001" if r["p"] < 0.001 else f"{r['p']:.4f}"
        lines.append(f"| {cond} | {r['W']:.3f} | {r['chi2']:.2f} | {p_str} |")

    lines += [
        "",
        "### CQS Agreement on Pairwise Deltas",
        "",
        "| Comparison | Kendall's W | chi2 | p |",
        "|------------|-------------|------|---|",
    ]

    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        r = agreement["cqs_pairwise_deltas"][key]
        p_str = "< .001" if r["p"] < 0.001 else f"{r['p']:.4f}"
        lines.append(f"| {cond_a} vs {cond_b} | {r['W']:.3f} | {r['chi2']:.2f} | {p_str} |")

    lines += [
        "",
        "### Per-Dimension Agreement (CQS per condition)",
        "",
        "| Dimension | Control W | RAG W | Pragmatics W |",
        "|-----------|-----------|-------|-------------|",
    ]

    for dim in sorted(agreement.get("per_dimension", {}).keys()):
        vals = []
        for cond in CONDITIONS:
            d = agreement["per_dimension"][dim].get(cond, {})
            w = d.get("W", float("nan"))
            vals.append(f"{w:.3f}" if not np.isnan(w) else "n/a")
        lines.append(f"| {dim} | {vals[0]} | {vals[1]} | {vals[2]} |")

    lines += [
        "",
        "---",
        "",
        "## Rank-Biserial Correlation (r)",
        "",
        "Nonparametric effect size from Wilcoxon signed-rank test. "
        "Appropriate for bounded ordinal composite scores. "
        "Interpretation: |r| >= 0.5 large, >= 0.3 medium, >= 0.1 small (Kerby 2014).",
        "",
        "### CQS Pairwise",
        "",
        "| Comparison | r | Cohen's d | Eff. n | Interpretation |",
        "|------------|---|-----------|--------|----------------|",
    ]

    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        r = rank_biserial["cqs_pairwise"][key]
        r_val = r["rank_biserial_r"]
        d_val = r["cohens_d"]
        r_str = f"{r_val:.3f}" if r_val is not None and not np.isnan(r_val) else "n/a"
        d_str = f"{d_val:.3f}" if d_val is not None else "n/a"
        lines.append(
            f"| {cond_a} vs {cond_b} | {r_str} | {d_str} | "
            f"{r['effective_n']} | {r['interpretation']} |"
        )

    lines += [
        "",
        "### Per-Dimension Rank-Biserial r",
        "",
        "| Dimension | Prag vs Ctrl r | Prag vs RAG r | RAG vs Ctrl r |",
        "|-----------|---------------|---------------|---------------|",
    ]

    for dim in sorted(rank_biserial["per_dimension"].keys()):
        dim_data = rank_biserial["per_dimension"][dim]
        vals = []
        for cond_a, cond_b in PAIRS:
            key = f"{cond_a}_vs_{cond_b}"
            r_val = dim_data.get(key, {}).get("rank_biserial_r", float("nan"))
            vals.append(f"{r_val:.3f}" if not np.isnan(r_val) else "n/a")
        lines.append(f"| {dim} | {vals[0]} | {vals[1]} | {vals[2]} |")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"scipy {scipy_version}", file=sys.stderr)

    config = load_config(CONFIG_PATH)
    params = get_analysis_params(config)
    dimensions = params["dimensions"]

    print("Discovering Stage 2 files...", file=sys.stderr)
    files = discover_stage2_files(DEFAULT_STAGE2_DIR)
    for comp, path in files.items():
        print(f"  {comp}: {path}", file=sys.stderr)

    # Kendall's W
    print("\nExtracting vendor-level scores...", file=sys.stderr)
    vendor_scores, vendor_cqs = extract_vendor_medians(files, dimensions)

    print("Computing Kendall's W...", file=sys.stderr)
    agreement = compute_agreement(vendor_cqs, vendor_scores, dimensions)

    print("\n" + "=" * 60, file=sys.stderr)
    print("INTER-JUDGE AGREEMENT (Kendall's W)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for cond in CONDITIONS:
        r = agreement["cqs_per_condition"][cond]
        print(f"  {cond:<12} W = {r['W']:.3f}  (p = {r['p']:.4f})", file=sys.stderr)
    print("", file=sys.stderr)
    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        r = agreement["cqs_pairwise_deltas"][key]
        print(f"  delta {key:<30} W = {r['W']:.3f}  (p = {r['p']:.4f})", file=sys.stderr)

    # Rank-biserial r
    agg_json = DEFAULT_STAGE2_DIR / "analysis" / "aggregate_statistics.json"
    if not agg_json.exists():
        print(f"\nERROR: {agg_json} not found. Run aggregate_analysis.py first.",
              file=sys.stderr)
        sys.exit(1)

    print("\nComputing rank-biserial r from existing Wilcoxon statistics...",
          file=sys.stderr)
    rank_biserial = compute_rank_biserial(agg_json)

    print("\n" + "=" * 60, file=sys.stderr)
    print("RANK-BISERIAL r (CQS)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        r = rank_biserial["cqs_pairwise"][key]
        r_val = r["rank_biserial_r"]
        print(f"  {key:<30} r = {r_val:.3f}  (d = {r['cohens_d']:.3f})  [{r['interpretation']}]",
              file=sys.stderr)

    # Write outputs
    output_dir = DEFAULT_STAGE2_DIR / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    combined = {
        "metadata": {
            "scipy_version": scipy_version,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "description": "Inter-judge agreement (Kendall's W) and rank-biserial r effect sizes",
            "srs_requirements": ["VR-110", "VR-111", "VR-112"],
        },
        "judge_agreement": agreement,
        "rank_biserial": rank_biserial,
    }

    json_path = output_dir / "judge_agreement.json"
    with open(json_path, "w") as f:
        json.dump(combined, f, indent=2, default=_json_default)
    print(f"\nJSON:     {json_path}", file=sys.stderr)

    md_content = build_markdown(agreement, rank_biserial)
    md_path = output_dir / "judge_agreement.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Markdown: {md_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
