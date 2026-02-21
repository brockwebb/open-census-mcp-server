#!/usr/bin/env python3
"""Stratum-level treatment effect analysis: normal vs edge case queries.

Answers whether pragmatics treatment effect differs between normal and edge
case query types — specifically whether we overfitted for edge cases.

Inputs:
  - src/eval/battery/queries.yaml         — category labels per query_id
  - results/v2_redo/stage2/analysis/aggregate_statistics.json
                                          — per-query CQS scores per condition

Outputs:
  - results/v2_redo/stage2/analysis/stratum_analysis.md
  - results/v2_redo/stage2/analysis/stratum_analysis.json

SRS: VR-101 (stratum classification), VR-102 (per-stratum pairwise analysis),
     VR-103 (between-stratum treatment effect comparison)

Usage: python -m src.eval.stratum_analysis
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import mannwhitneyu, wilcoxon


# ── Constants ─────────────────────────────────────────────────────────────────

PAIRS = [
    ("pragmatics", "control"),
    ("pragmatics", "rag"),
    ("rag", "control"),
]

PAIR_LABELS = {
    ("pragmatics", "control"): "pragmatics vs control",
    ("pragmatics", "rag"):     "pragmatics vs rag",
    ("rag", "control"):        "rag vs control",
}

# Power notes per task spec (VR-102)
POWER_NOTES = {
    "normal": "n=15: Wilcoxon power ~0.56 at d=0.5, ~0.94 at d=1.0 (underpowered for small effects)",
    "edge":   "n=24: Wilcoxon power ~0.80 at d=0.5, ~0.99 at d=1.0",
}


# ── Data loading ──────────────────────────────────────────────────────────────

def load_battery_categories(battery_path: Path) -> dict:
    """Return {query_id: category} for all battery entries."""
    with open(battery_path) as f:
        data = yaml.safe_load(f)
    queries = data.get("queries", data) if isinstance(data, dict) else data
    return {q["id"]: q.get("category", "unknown") for q in queries}


def load_per_query_cqs(stats_path: Path) -> dict:
    """Return per_query_cqs dict: {condition: {query_id: float}}."""
    with open(stats_path) as f:
        data = json.load(f)
    return data["per_query_cqs"]


# ── Stratum classification ────────────────────────────────────────────────────

def classify_queries(categories: dict) -> dict:
    """Return {stratum: [query_id, ...]} for normal/edge split (VR-101)."""
    strata = {"normal": [], "edge": []}
    for qid, cat in sorted(categories.items()):
        if cat == "normal":
            strata["normal"].append(qid)
        else:
            strata["edge"].append(qid)
    return strata


# ── Statistical helpers ───────────────────────────────────────────────────────

def cohens_d_paired(a: np.ndarray, b: np.ndarray) -> float:
    """Paired Cohen's d = mean(a - b) / std(a - b, ddof=1)."""
    diff = a - b
    std = np.std(diff, ddof=1)
    return float(np.mean(diff) / std) if std > 0 else 0.0


def aligned_pair(cqs: dict, query_ids: list, cond_a: str, cond_b: str):
    """Build aligned arrays (a, b, included_ids), dropping NaN queries."""
    a_vals, b_vals, included = [], [], []
    for qid in query_ids:
        a = cqs[cond_a].get(qid, float("nan"))
        b = cqs[cond_b].get(qid, float("nan"))
        if not (np.isnan(a) or np.isnan(b)):
            a_vals.append(a)
            b_vals.append(b)
            included.append(qid)
    return np.array(a_vals), np.array(b_vals), included


# ── Per-stratum analysis ──────────────────────────────────────────────────────

def analyze_stratum(stratum_ids: list, cqs: dict, alpha: float = 0.05) -> dict:
    """Compute condition means, pairwise stats within a stratum (VR-102)."""
    conditions = ["control", "rag", "pragmatics"]

    # Condition means within stratum
    means = {}
    for cond in conditions:
        vals = [cqs[cond][qid] for qid in stratum_ids if qid in cqs[cond]]
        means[cond] = float(np.mean(vals)) if vals else float("nan")

    # Pairwise statistics
    pairwise = {}
    for cond_a, cond_b in PAIRS:
        a, b, included = aligned_pair(cqs, stratum_ids, cond_a, cond_b)
        n = len(included)
        if n < 2:
            pairwise[(cond_a, cond_b)] = {"n": n, "error": "insufficient data"}
            continue

        delta = float(np.mean(a - b))
        d = cohens_d_paired(a, b)

        # Wilcoxon signed-rank (paired within stratum)
        try:
            stat, p = wilcoxon(a, b, zero_method="pratt", alternative="two-sided")
            wilcoxon_result = {"statistic": float(stat), "p": float(p)}
        except ValueError as e:
            wilcoxon_result = {"error": str(e)}

        pairwise[(cond_a, cond_b)] = {
            "n": n,
            "delta": delta,
            "cohens_d": d,
            "wilcoxon": wilcoxon_result,
            "significant": wilcoxon_result.get("p", 1.0) < alpha,
            "query_ids": included,
        }

    return {"means": means, "pairwise": pairwise}


# ── Between-stratum comparison ────────────────────────────────────────────────

def between_stratum_comparison(
    normal_ids: list,
    edge_ids: list,
    cqs: dict,
    alpha: float = 0.05,
) -> dict:
    """Compare treatment effect magnitude between strata using Mann-Whitney U (VR-103).

    For each pair, computes per-query deltas in each stratum, then tests
    whether edge deltas are larger than normal deltas (one-sided: edge > normal).
    """
    results = {}
    for cond_a, cond_b in PAIRS:
        a_n, b_n, _ = aligned_pair(cqs, normal_ids, cond_a, cond_b)
        a_e, b_e, _ = aligned_pair(cqs, edge_ids, cond_a, cond_b)

        deltas_normal = a_n - b_n
        deltas_edge = a_e - b_e

        mean_delta_normal = float(np.mean(deltas_normal)) if len(deltas_normal) else float("nan")
        mean_delta_edge = float(np.mean(deltas_edge)) if len(deltas_edge) else float("nan")
        delta_of_deltas = mean_delta_edge - mean_delta_normal  # positive = edge > normal

        # Mann-Whitney U: one-sided, edge > normal
        mw_result = {}
        if len(deltas_normal) >= 2 and len(deltas_edge) >= 2:
            try:
                stat, p_greater = mannwhitneyu(
                    deltas_edge, deltas_normal, alternative="greater"
                )
                mw_result = {
                    "statistic": float(stat),
                    "p_greater": float(p_greater),
                    "significant": float(p_greater) < alpha,
                }
            except Exception as e:
                mw_result = {"error": str(e)}

        results[(cond_a, cond_b)] = {
            "mean_delta_normal": mean_delta_normal,
            "mean_delta_edge": mean_delta_edge,
            "delta_of_deltas": delta_of_deltas,
            "n_normal": len(deltas_normal),
            "n_edge": len(deltas_edge),
            "mann_whitney": mw_result,
        }

    return results


# ── Markdown output ───────────────────────────────────────────────────────────

def fmt_p(p) -> str:
    if p is None:
        return "N/A"
    if p < 0.001:
        return "< 0.001"
    return f"{p:.4f}"


def sig_marker(p, alpha=0.05) -> str:
    if p is None:
        return ""
    return " *" if p < alpha else ""


def build_markdown(
    stratum_results: dict,
    between: dict,
    strata: dict,
    categories: dict,
    timestamp: str,
    alpha: float,
) -> str:
    lines = []
    lines.append("# Stratum-Level Treatment Effect Analysis")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("**Script:** src/eval/stratum_analysis.py")
    lines.append(f"**SRS:** VR-101, VR-102, VR-103")
    lines.append(f"**α = {alpha}**")
    lines.append("")

    # Stratum composition
    lines.append("## Stratum Composition (VR-101)")
    lines.append("")
    lines.append("| Stratum | N | Categories |")
    lines.append("|---------|---|-----------|")

    from collections import Counter
    normal_cats = Counter(categories[qid] for qid in strata["normal"])
    edge_cats = Counter(categories[qid] for qid in strata["edge"])
    lines.append(f"| Normal | {len(strata['normal'])} | {', '.join(f'{k}:{v}' for k, v in sorted(normal_cats.items()))} |")
    lines.append(f"| Edge | {len(strata['edge'])} | {', '.join(f'{k}:{v}' for k, v in sorted(edge_cats.items()))} |")
    lines.append("")

    # Per-stratum results
    for stratum_name in ["normal", "edge"]:
        sr = stratum_results[stratum_name]
        lines.append(f"## {stratum_name.title()} Queries (n={len(strata[stratum_name])}) (VR-102)")
        lines.append("")
        lines.append(f"*Power note: {POWER_NOTES[stratum_name]}*")
        lines.append("")

        # Condition means
        lines.append("### Condition Means (CQS)")
        lines.append("")
        lines.append("| Condition | Mean CQS |")
        lines.append("|-----------|----------|")
        for cond in ["control", "rag", "pragmatics"]:
            m = sr["means"].get(cond, float("nan"))
            lines.append(f"| {cond} | {m:.4f} |")
        lines.append("")

        # Pairwise comparisons
        lines.append("### Pairwise Comparisons")
        lines.append("")
        lines.append("| Comparison | Δ CQS | Cohen's d | Wilcoxon W | p | Sig | Eff. N |")
        lines.append("|------------|-------|-----------|-----------|---|-----|--------|")
        for pair in PAIRS:
            res = sr["pairwise"].get(pair, {})
            if "error" in res:
                lines.append(f"| {PAIR_LABELS[pair]} | — | — | — | — | — | {res.get('n', '?')} |")
                continue
            wil = res.get("wilcoxon", {})
            p_val = wil.get("p")
            w_stat = wil.get("statistic", "—")
            marker = sig_marker(p_val, alpha)
            lines.append(
                f"| {PAIR_LABELS[pair]} | {res['delta']:+.3f} | {res['cohens_d']:.3f} | "
                f"{w_stat:.1f} | {fmt_p(p_val)}{marker} | {'*' if res.get('significant') else ''} | "
                f"{res['n']}/{len(strata[stratum_name])} |"
            )
        lines.append("")

    # Between-stratum comparison
    lines.append("## Between-Stratum Comparison (VR-103)")
    lines.append("")
    lines.append("*Tests whether treatment effect is larger for edge queries.*")
    lines.append("*Mann-Whitney U: one-sided (edge > normal), unpaired, unequal n — interpret cautiously.*")
    lines.append("")
    lines.append("| Pair | Normal Δ | Edge Δ | ΔΔ (Edge−Normal) | MW U | p(Edge>Normal) | Sig |")
    lines.append("|------|---------|--------|------------------|------|----------------|-----|")
    for pair in PAIRS:
        res = between.get(pair, {})
        mw = res.get("mann_whitney", {})
        p_g = mw.get("p_greater")
        u = mw.get("statistic", "—")
        marker = sig_marker(p_g, alpha)
        dod = res.get("delta_of_deltas", float("nan"))
        lines.append(
            f"| {PAIR_LABELS[pair]} | {res.get('mean_delta_normal', float('nan')):+.3f} | "
            f"{res.get('mean_delta_edge', float('nan')):+.3f} | {dod:+.3f} | "
            f"{u if isinstance(u, str) else f'{u:.1f}'} | {fmt_p(p_g)}{marker} | "
            f"{'*' if mw.get('significant') else ''} |"
        )
    lines.append("")

    # Narrative summary
    lines.append("## Findings Summary")
    lines.append("")

    # Check for overfit: do pragmatics hurt on normal queries?
    norm_prag_ctrl = stratum_results["normal"]["pairwise"].get(("pragmatics", "control"), {})
    edge_prag_ctrl = stratum_results["edge"]["pairwise"].get(("pragmatics", "control"), {})
    norm_delta = norm_prag_ctrl.get("delta", float("nan"))
    edge_delta = edge_prag_ctrl.get("delta", float("nan"))
    between_prag_ctrl = between.get(("pragmatics", "control"), {})
    dod = between_prag_ctrl.get("delta_of_deltas", float("nan"))

    if not np.isnan(norm_delta):
        direction = "POSITIVE" if norm_delta > 0 else "NEGATIVE (RED FLAG — possible overfit)"
        lines.append(f"**Normal queries (pragmatics vs control):** Δ = {norm_delta:+.3f} — {direction}")
    if not np.isnan(edge_delta):
        lines.append(f"**Edge queries (pragmatics vs control):** Δ = {edge_delta:+.3f}")
    if not np.isnan(dod):
        lines.append(f"**Delta-of-deltas (edge − normal):** {dod:+.3f} — edge queries benefit {'more' if dod > 0 else 'less'} from pragmatics")

    mw_prag_ctrl = between_prag_ctrl.get("mann_whitney", {})
    p_between = mw_prag_ctrl.get("p_greater")
    if p_between is not None:
        sig_str = f"significant (p={fmt_p(p_between)})" if p_between < alpha else f"not significant (p={fmt_p(p_between)})"
        lines.append(f"**Between-stratum difference:** {sig_str}")
    lines.append("")
    lines.append(
        f"*Parameters: α={alpha}, Wilcoxon zero_method=pratt, Mann-Whitney alternative=greater*"
    )
    lines.append(f"*Generated: {timestamp}*")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Stratum-level treatment effect analysis")
    parser.add_argument(
        "--battery", default="src/eval/battery/queries.yaml",
        help="Path to battery queries.yaml"
    )
    parser.add_argument(
        "--stats", default="results/v2_redo/stage2/analysis/aggregate_statistics.json",
        help="Path to aggregate_statistics.json"
    )
    parser.add_argument(
        "--output-dir", default="results/v2_redo/stage2/analysis",
        help="Output directory"
    )
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    base = Path(__file__).parent.parent.parent

    battery_path = base / args.battery
    stats_path = base / args.stats
    output_dir = base / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading battery categories...")
    categories = load_battery_categories(battery_path)
    print(f"  {len(categories)} queries loaded")

    print("Loading per-query CQS scores...")
    cqs = load_per_query_cqs(stats_path)
    n_queries = len(next(iter(cqs.values())))
    print(f"  {n_queries} queries per condition")

    print("Classifying strata...")
    strata = classify_queries(categories)
    print(f"  Normal: {len(strata['normal'])} queries")
    print(f"  Edge:   {len(strata['edge'])} queries")

    # Filter to only queries present in CQS data
    conditions = list(cqs.keys())
    cqs_ids = set(cqs[conditions[0]].keys())
    for stratum_name in ["normal", "edge"]:
        before = len(strata[stratum_name])
        strata[stratum_name] = [q for q in strata[stratum_name] if q in cqs_ids]
        after = len(strata[stratum_name])
        if before != after:
            print(f"  Warning: {before - after} {stratum_name} queries missing from CQS data")

    print("Running per-stratum analysis (VR-102)...")
    stratum_results = {}
    for stratum_name, ids in strata.items():
        stratum_results[stratum_name] = analyze_stratum(ids, cqs, alpha=args.alpha)

    print("Running between-stratum comparison (VR-103)...")
    between = between_stratum_comparison(
        strata["normal"], strata["edge"], cqs, alpha=args.alpha
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Build JSON output ──
    def make_serializable(d):
        """Convert tuple keys to strings for JSON serialization."""
        if isinstance(d, dict):
            return {
                (f"{k[0]}_vs_{k[1]}" if isinstance(k, tuple) else k): make_serializable(v)
                for k, v in d.items()
            }
        elif isinstance(d, (list, tuple)):
            return [make_serializable(i) for i in d]
        elif isinstance(d, np.ndarray):
            return d.tolist()
        elif isinstance(d, (np.floating, np.integer)):
            return float(d)
        return d

    output_json = {
        "metadata": {
            "generated": timestamp,
            "script": "src/eval/stratum_analysis.py",
            "srs": ["VR-101", "VR-102", "VR-103"],
            "alpha": args.alpha,
        },
        "stratum_composition": {
            "normal": {
                "n": len(strata["normal"]),
                "query_ids": strata["normal"],
            },
            "edge": {
                "n": len(strata["edge"]),
                "query_ids": strata["edge"],
            },
        },
        "stratum_results": make_serializable(stratum_results),
        "between_stratum": make_serializable(between),
    }

    json_path = output_dir / "stratum_analysis.json"
    with open(json_path, "w") as f:
        json.dump(output_json, f, indent=2, default=str)
    print(f"JSON written to: {json_path}")

    # ── Build Markdown output ──
    md = build_markdown(
        stratum_results, between, strata, categories, timestamp, args.alpha
    )

    md_path = output_dir / "stratum_analysis.md"
    with open(md_path, "w") as f:
        f.write(md)
    print(f"Markdown written to: {md_path}")

    # Print summary to stdout
    print("\n" + "=" * 70)
    print("STRATUM ANALYSIS SUMMARY")
    print("=" * 70)
    for stratum_name in ["normal", "edge"]:
        sr = stratum_results[stratum_name]
        print(f"\n[{stratum_name.upper()}] n={len(strata[stratum_name])}")
        for pair in PAIRS:
            res = sr["pairwise"].get(pair, {})
            if "error" not in res:
                sig = "*" if res.get("significant") else " "
                print(
                    f"  {PAIR_LABELS[pair]:<30}  Δ={res.get('delta', float('nan')):+.3f}  "
                    f"d={res.get('cohens_d', float('nan')):.3f}  "
                    f"p={fmt_p(res.get('wilcoxon', {}).get('p'))}{sig}"
                )

    print("\n[BETWEEN-STRATUM]")
    for pair in PAIRS:
        res = between.get(pair, {})
        mw = res.get("mann_whitney", {})
        dod = res.get("delta_of_deltas", float("nan"))
        print(
            f"  {PAIR_LABELS[pair]:<30}  ΔΔ={dod:+.3f}  "
            f"p(edge>normal)={fmt_p(mw.get('p_greater'))}"
            f"{'*' if mw.get('significant') else ''}"
        )
    print("=" * 70)


if __name__ == "__main__":
    main()
