#!/usr/bin/env python3
"""V2 aggregate statistical analysis: Friedman omnibus + Wilcoxon post-hoc (Holm-corrected).

Loads all three Stage 2 pairwise comparison JSONL files, aggregates judge scores
to per-query medians per condition (control/RAG/pragmatics), then runs:

  - Friedman omnibus test across 3 conditions (CQS + per-dimension D1-D5)
  - Pairwise Wilcoxon signed-rank tests with Holm-Bonferroni correction
  - Paired Cohen's d and bootstrap 95% CIs on CQS deltas

SRS: VR-048

Scipy API notes (verified against scipy 1.13.1):
  - scipy.stats.wilcoxon: zero_method='pratt' for Pratt zero-difference handling
    (NOT method='pratt' — that parameter controls the p-value computation method)
  - scipy.stats.friedmanchisquare: applies tie correction automatically via the
    standard Friedman procedure (divides by 1 - SS_tie / normalization factor)
  - statsmodels.stats.multitest.multipletests: method='holm' for Holm-Bonferroni

D6 is excluded from CQS composite per cqs_rubric_specification.md (empirically
found to reward vagueness and penalize specificity in V2 production evaluation).
CQS = mean of D1-D5 median scores per query per condition.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml
from scipy import __version__ as scipy_version
from scipy.stats import friedmanchisquare, wilcoxon
from statsmodels.stats.multitest import multipletests

# ── Constants ──────────────────────────────────────────────────────────────────

CONFIG_PATH = Path("src/eval/judge_config.yaml")
DEFAULT_STAGE2_DIR = Path("results/v2_redo/stage2")

CONDITIONS = ["control", "rag", "pragmatics"]

# Pairwise comparisons: (condition_a, condition_b); delta = a - b
# Positive delta means condition_a outperformed condition_b.
PAIRS = [
    ("pragmatics", "control"),
    ("pragmatics", "rag"),
    ("rag", "control"),
]

COMPARISON_NAMES = [
    "rag_vs_pragmatics",
    "control_vs_rag",
    "control_vs_pragmatics",
]


# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_analysis_params(config: dict) -> dict:
    """Extract analysis section from config with safe defaults."""
    a = config.get("analysis", {})
    return {
        "alpha": a.get("alpha", 0.05),
        "bootstrap_iterations": a.get("bootstrap_iterations", 10_000),
        "correction_method": a.get("correction_method", "holm"),
        "dimensions": a.get("dimensions", ["D1", "D2", "D3", "D4", "D5"]),
        "output_dir": a.get("output_dir", str(DEFAULT_STAGE2_DIR / "analysis")),
    }


# ── File discovery ─────────────────────────────────────────────────────────────

def discover_stage2_files(stage2_dir: Path) -> dict:
    """Auto-discover one JSONL file per comparison (latest non-backup timestamp)."""
    files = {}
    for comparison in COMPARISON_NAMES:
        candidates = [
            p for p in sorted(stage2_dir.glob(f"{comparison}_*.jsonl"))
            if "_backup" not in p.name
        ]
        if not candidates:
            raise FileNotFoundError(
                f"No JSONL found for '{comparison}' in {stage2_dir}"
            )
        files[comparison] = candidates[-1]  # lexicographic sort → latest timestamp
    return files


# ── Data loading ───────────────────────────────────────────────────────────────

def load_records(path: Path) -> list:
    """Load JSONL, deduplicate on (query_id, judge_vendor, pass_number, presentation_order)."""
    raw = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                raw.append(json.loads(line))

    seen = {}
    for r in raw:
        key = (
            r["query_id"],
            r["judge_vendor"],
            r["pass_number"],
            r["presentation_order"],
        )
        seen[key] = r

    n_dupes = len(raw) - len(seen)
    if n_dupes:
        print(
            f"  {path.name}: {len(raw)} records → {len(seen)} after dedup "
            f"({n_dupes} removed)",
            file=sys.stderr,
        )
    return list(seen.values())


def extract_condition_scores(records: list) -> dict:
    """Extract raw scores by (query_id, condition, dimension).

    Skips records with parse_success=False.
    Returns: scores[qid][condition][dim] = [score, ...]
    """
    scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in records:
        if not r.get("parse_success", False):
            continue
        qid = r["query_id"]
        for label_key, scores_key in [
            ("response_a_label", "scores_response_a"),
            ("response_b_label", "scores_response_b"),
        ]:
            cond = r[label_key]
            for dim, entry in r[scores_key].items():
                scores[qid][cond][dim].append(entry["score"])
    return scores


# ── Aggregation ────────────────────────────────────────────────────────────────

def aggregate_to_medians(all_scores: dict, dimensions: list) -> tuple:
    """Compute per-query median per condition per dimension, then CQS.

    Returns:
        medians: dict[condition][qid][dim] = float
        cqs:     dict[condition][qid]      = float (mean of dim medians; NaN if no data)
        query_ids: sorted list of all query IDs
    """
    query_ids = sorted(all_scores.keys())
    medians = defaultdict(lambda: defaultdict(dict))
    cqs = defaultdict(dict)

    for qid in query_ids:
        for cond in CONDITIONS:
            dim_medians = {}
            for dim in dimensions:
                raw = all_scores[qid][cond].get(dim, [])
                dim_medians[dim] = float(np.median(raw)) if raw else float("nan")
            medians[cond][qid] = dim_medians
            valid = [v for v in dim_medians.values() if not np.isnan(v)]
            cqs[cond][qid] = float(np.mean(valid)) if valid else float("nan")

    return dict(medians), dict(cqs), query_ids


# ── Statistical helpers ────────────────────────────────────────────────────────

def cohens_d_paired(a: np.ndarray, b: np.ndarray) -> float:
    """Paired Cohen's d = mean(a - b) / std(a - b, ddof=1)."""
    diff = a - b
    std = np.std(diff, ddof=1)
    if std == 0:
        return 0.0
    return float(np.mean(diff) / std)


def bootstrap_ci(
    a: np.ndarray,
    b: np.ndarray,
    n_iter: int,
    rng: np.random.Generator,
    alpha: float = 0.05,
) -> tuple:
    """Bootstrap CI on mean(a - b) by resampling query pairs with replacement."""
    n = len(a)
    deltas = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        deltas[i] = np.mean(a[idx] - b[idx])
    lo = float(np.percentile(deltas, 100 * alpha / 2))
    hi = float(np.percentile(deltas, 100 * (1 - alpha / 2)))
    return lo, hi


def aligned_arrays(score_dict: dict, query_ids: list, cond_a: str, cond_b: str) -> tuple:
    """Build aligned arrays for two conditions, excluding queries with NaN in either.

    score_dict: dict[condition][qid] = float
    Returns: (arr_a, arr_b, included_query_ids)
    """
    rows_a, rows_b, included = [], [], []
    for qid in query_ids:
        a = score_dict[cond_a].get(qid, float("nan"))
        b = score_dict[cond_b].get(qid, float("nan"))
        if not (np.isnan(a) or np.isnan(b)):
            rows_a.append(a)
            rows_b.append(b)
            included.append(qid)
    return np.array(rows_a), np.array(rows_b), included


# ── Friedman ───────────────────────────────────────────────────────────────────

def run_friedman(score_dict: dict, query_ids: list) -> dict:
    """Friedman test across 3 conditions. score_dict[condition][qid] = float."""
    valid_qids = [
        qid for qid in query_ids
        if not any(
            np.isnan(score_dict[c].get(qid, float("nan"))) for c in CONDITIONS
        )
    ]
    n = len(valid_qids)
    if n < 3:
        return {"stat": float("nan"), "p": float("nan"), "n": n,
                "error": "Insufficient complete cases"}

    ctrl  = np.array([score_dict["control"][qid]    for qid in valid_qids])
    rag   = np.array([score_dict["rag"][qid]         for qid in valid_qids])
    prag  = np.array([score_dict["pragmatics"][qid]  for qid in valid_qids])

    stat, p = friedmanchisquare(ctrl, rag, prag)
    return {
        "stat": float(stat),
        "p": float(p),
        "n": n,
        "condition_means": {
            "control":    float(np.mean(ctrl)),
            "rag":        float(np.mean(rag)),
            "pragmatics": float(np.mean(prag)),
        },
    }


# ── Pairwise Wilcoxon ──────────────────────────────────────────────────────────

def run_pairwise_wilcoxon(
    score_dict: dict,
    query_ids: list,
    params: dict,
    rng: np.random.Generator,
) -> dict:
    """Wilcoxon signed-rank for all 3 pairs with Holm correction.

    Uses zero_method='pratt' (Pratt method for zero-difference handling).
    delta = cond_a - cond_b; positive means cond_a > cond_b.

    Returns dict keyed by "{cond_a}_vs_{cond_b}".
    """
    raw_pvals = []
    pair_data = {}

    for cond_a, cond_b in PAIRS:
        arr_a, arr_b, included = aligned_arrays(score_dict, query_ids, cond_a, cond_b)
        n = len(included)
        diff = arr_a - arr_b
        effective_n = int(np.sum(diff != 0))
        delta = float(np.mean(arr_a) - np.mean(arr_b)) if n > 0 else float("nan")
        key = f"{cond_a}_vs_{cond_b}"

        if effective_n < 4:
            pair_data[key] = {
                "comparison": key,
                "delta": delta,
                "wilcoxon_stat": float("nan"),
                "p_raw": float("nan"),
                "p_holm": float("nan"),
                "cohens_d": cohens_d_paired(arr_a, arr_b) if n > 1 else float("nan"),
                "ci_lo": float("nan"),
                "ci_hi": float("nan"),
                "effective_n": effective_n,
                "total_n": n,
                "note": "Too few non-zero differences for Wilcoxon",
            }
            raw_pvals.append(float("nan"))
            continue

        # zero_method='pratt': includes zero-differences in ranking but drops
        # their signed ranks — more conservative than 'wilcox' (which discards them)
        stat, p_raw = wilcoxon(arr_a, arr_b, zero_method="pratt", alternative="two-sided")

        ci_lo, ci_hi = bootstrap_ci(
            arr_a, arr_b,
            n_iter=params["bootstrap_iterations"],
            rng=rng,
            alpha=1.0 - 0.95,
        )

        pair_data[key] = {
            "comparison": key,
            "delta": delta,
            "wilcoxon_stat": float(stat),
            "p_raw": float(p_raw),
            "p_holm": float("nan"),  # filled after Holm pass
            "cohens_d": cohens_d_paired(arr_a, arr_b),
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "effective_n": effective_n,
            "total_n": n,
        }
        raw_pvals.append(float(p_raw))

    # Holm correction over the valid p-values
    valid_keys = [f"{a}_vs_{b}" for a, b in PAIRS]
    valid_pvals = [
        p for p in raw_pvals if not np.isnan(p)
    ]
    valid_key_list = [
        k for k, p in zip(valid_keys, raw_pvals) if not np.isnan(p)
    ]

    if valid_pvals:
        _, corrected, _, _ = multipletests(
            valid_pvals,
            alpha=params["alpha"],
            method=params["correction_method"],
        )
        for k, p_holm in zip(valid_key_list, corrected):
            pair_data[k]["p_holm"] = float(p_holm)

    return pair_data


# ── Per-dimension analysis ─────────────────────────────────────────────────────

def run_dimension_analysis(
    medians: dict,
    query_ids: list,
    params: dict,
    rng: np.random.Generator,
) -> dict:
    """Friedman + Wilcoxon for each dimension in params['dimensions']."""
    results = {}
    for dim in params["dimensions"]:
        dim_scores = {
            cond: {qid: medians[cond][qid].get(dim, float("nan")) for qid in query_ids}
            for cond in CONDITIONS
        }
        results[dim] = {
            "friedman": run_friedman(dim_scores, query_ids),
            "pairwise": run_pairwise_wilcoxon(dim_scores, query_ids, params, rng),
        }
    return results


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _fmt_p(p: float) -> str:
    if np.isnan(p):
        return "n/a"
    if p < 0.001:
        return "< 0.001"
    return f"{p:.4f}"


def _fmt(v: float, dec: int = 3) -> str:
    if np.isnan(v):
        return "n/a"
    return f"{v:.{dec}f}"


# ── Output builders ────────────────────────────────────────────────────────────

def build_markdown(
    cqs_friedman: dict,
    cqs_pairwise: dict,
    dim_results: dict,
    params: dict,
) -> str:
    alpha = params["alpha"]
    lines = []

    # Omnibus
    f = cqs_friedman
    sig = "**significant**" if (not np.isnan(f["p"]) and f["p"] < alpha) else "not significant"
    lines += [
        "## Omnibus Test",
        "",
        f"Friedman χ²(2, N={f['n']}) = {_fmt(f['stat'], 2)}, p = {_fmt_p(f['p'])} [{sig}]",
        "",
    ]

    if "condition_means" in f:
        lines += [
            "**Condition means (CQS):**",
            "",
            "| Condition | Mean CQS |",
            "|-----------|----------|",
        ]
        for cond in CONDITIONS:
            lines.append(f"| {cond} | {_fmt(f['condition_means'][cond], 4)} |")
        lines.append("")

    # Pairwise
    lines += [
        "## Pairwise Comparisons (Holm-corrected)",
        "",
        "| Comparison | CQS Delta | Wilcoxon W | p (raw) | p (Holm) | Cohen's d | 95% CI | Effective N |",
        "|------------|-----------|-----------|---------|----------|-----------|--------|-------------|",
    ]
    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        r = cqs_pairwise[key]
        ci = f"[{_fmt(r['ci_lo'], 3)}, {_fmt(r['ci_hi'], 3)}]"
        sig_mark = " \\*" if (not np.isnan(r["p_holm"]) and r["p_holm"] < alpha) else ""
        lines.append(
            f"| {cond_a} vs {cond_b} | {_fmt(r['delta'], 3)} | "
            f"{_fmt(r['wilcoxon_stat'], 1)} | {_fmt_p(r['p_raw'])} | "
            f"{_fmt_p(r['p_holm'])}{sig_mark} | {_fmt(r['cohens_d'], 3)} | "
            f"{ci} | {r['effective_n']}/{r['total_n']} |"
        )
    lines += [
        "",
        "*\\* p < α after Holm correction. Delta = row condition − column condition.*",
        "",
    ]

    # Per-dimension
    lines.append("## Per-Dimension Results")
    lines.append("")
    for dim, dr in dim_results.items():
        fd = dr["friedman"]
        sig_d = "**significant**" if (not np.isnan(fd["p"]) and fd["p"] < alpha) else "not significant"
        lines += [
            f"### {dim}",
            "",
            f"Friedman χ²(2, N={fd['n']}) = {_fmt(fd['stat'], 2)}, p = {_fmt_p(fd['p'])} [{sig_d}]",
            "",
            "| Comparison | Δ | W | p (raw) | p (Holm) | Cohen's d | 95% CI | Eff. N |",
            "|------------|---|---|---------|----------|-----------|--------|--------|",
        ]
        for cond_a, cond_b in PAIRS:
            key = f"{cond_a}_vs_{cond_b}"
            r = dr["pairwise"][key]
            ci = f"[{_fmt(r['ci_lo'], 3)}, {_fmt(r['ci_hi'], 3)}]"
            sig_mark = " \\*" if (not np.isnan(r["p_holm"]) and r["p_holm"] < alpha) else ""
            lines.append(
                f"| {cond_a} vs {cond_b} | {_fmt(r['delta'], 3)} | "
                f"{_fmt(r['wilcoxon_stat'], 1)} | {_fmt_p(r['p_raw'])} | "
                f"{_fmt_p(r['p_holm'])}{sig_mark} | {_fmt(r['cohens_d'], 3)} | "
                f"{ci} | {r['effective_n']}/{r['total_n']} |"
            )
        lines.append("")

    lines += [
        "---",
        f"*Parameters: α={alpha}, bootstrap_iterations={params['bootstrap_iterations']:,}, "
        f"correction={params['correction_method']}, CQS dimensions={params['dimensions']}*",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        f"*scipy {scipy_version}*",
    ]
    return "\n".join(lines)


def print_summary(
    cqs_friedman: dict,
    cqs_pairwise: dict,
    dim_results: dict,
    params: dict,
) -> None:
    """Formatted summary table to stdout."""
    alpha = params["alpha"]
    f = cqs_friedman
    sig = "SIGNIFICANT" if (not np.isnan(f["p"]) and f["p"] < alpha) else "NOT SIGNIFICANT"

    print("\n" + "=" * 72)
    print("V2 AGGREGATE STATISTICAL ANALYSIS")
    print("=" * 72)
    print(f"\nscipy {scipy_version}")

    print(f"\n[OMNIBUS — CQS, N={f['n']}]")
    print(f"Friedman χ²(2) = {_fmt(f['stat'], 4)},  p = {_fmt_p(f['p'])}  [{sig}]")
    if "condition_means" in f:
        print("  Condition means:")
        for cond in CONDITIONS:
            print(f"    {cond:<12} {f['condition_means'][cond]:.4f}")

    hdr = f"  {'Comparison':<25} {'Delta':>7} {'W':>8} {'p(raw)':>9} {'p(Holm)':>9} {'d':>7} {'95% CI':>23} {'Eff.N':>6}"
    sep = "  " + "-" * (len(hdr) - 2)
    print(f"\n[PAIRWISE — CQS (Holm-corrected)]")
    print(hdr)
    print(sep)
    for cond_a, cond_b in PAIRS:
        key = f"{cond_a}_vs_{cond_b}"
        r = cqs_pairwise[key]
        ci = f"[{_fmt(r['ci_lo'], 3)},{_fmt(r['ci_hi'], 3)}]"
        flag = " *" if (not np.isnan(r["p_holm"]) and r["p_holm"] < alpha) else "  "
        print(
            f"  {cond_a+' vs '+cond_b:<25} "
            f"{_fmt(r['delta'], 4):>7} "
            f"{_fmt(r['wilcoxon_stat'], 1):>8} "
            f"{_fmt_p(r['p_raw']):>9} "
            f"{_fmt_p(r['p_holm']):>8}{flag} "
            f"{_fmt(r['cohens_d'], 3):>7} "
            f"{ci:>23}  "
            f"{r['effective_n']:>2}/{r['total_n']}"
        )

    print(f"\n[PER-DIMENSION OMNIBUS]")
    print(f"  {'Dim':<4} {'χ²(2)':>10} {'p':>9} {'Sig':>6}")
    print("  " + "-" * 32)
    for dim, dr in dim_results.items():
        fd = dr["friedman"]
        sig_d = "YES" if (not np.isnan(fd["p"]) and fd["p"] < alpha) else "no"
        print(f"  {dim:<4} {_fmt(fd['stat'], 4):>10} {_fmt_p(fd['p']):>9} {sig_d:>6}")

    print(f"\n  α={alpha}, correction={params['correction_method']}, "
          f"bootstrap={params['bootstrap_iterations']:,}")
    print("=" * 72)


# ── JSON serialization ─────────────────────────────────────────────────────────

def _json_default(obj):
    if isinstance(obj, float) and np.isnan(obj):
        return None
    if isinstance(obj, (float, np.floating)):
        return float(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run_analysis(files: dict, params: dict) -> dict:
    """Load data, aggregate, run all tests, return results dict."""
    print(f"scipy {scipy_version}", file=sys.stderr)

    # Merge raw scores from all three files
    all_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    total_records = 0
    parse_failures = 0

    for comparison, path in files.items():
        print(f"Loading {comparison}: {path}", file=sys.stderr)
        records = load_records(path)
        total_records += len(records)
        parse_failures += sum(1 for r in records if not r.get("parse_success", False))
        for qid, cond_dict in extract_condition_scores(records).items():
            for cond, dim_dict in cond_dict.items():
                for dim, score_list in dim_dict.items():
                    all_scores[qid][cond][dim].extend(score_list)

    print(f"\nRecords loaded: {total_records}  |  parse failures: {parse_failures}",
          file=sys.stderr)

    # Aggregate to per-query medians and CQS
    medians, cqs, query_ids = aggregate_to_medians(all_scores, params["dimensions"])

    print(f"Queries with data: {len(query_ids)}", file=sys.stderr)
    for cond in CONDITIONS:
        n_valid = sum(1 for qid in query_ids if not np.isnan(cqs[cond].get(qid, float("nan"))))
        print(f"  {cond}: {n_valid}/{len(query_ids)} queries with valid CQS", file=sys.stderr)

    # Shared RNG for reproducible bootstrap (seed from config if present)
    rng = np.random.default_rng(42)

    # CQS omnibus
    print("\nRunning Friedman omnibus (CQS)...", file=sys.stderr)
    cqs_friedman = run_friedman(cqs, query_ids)

    # CQS pairwise
    print("Running pairwise Wilcoxon (CQS)...", file=sys.stderr)
    cqs_pairwise = run_pairwise_wilcoxon(cqs, query_ids, params, rng)

    # Per-dimension
    print("Running per-dimension analysis (D1-D5)...", file=sys.stderr)
    dim_results = run_dimension_analysis(medians, query_ids, params, rng)

    results = {
        "metadata": {
            "scipy_version": scipy_version,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_records_loaded": total_records,
            "parse_failures": parse_failures,
            "n_queries": len(query_ids),
            "alpha": params["alpha"],
            "bootstrap_iterations": params["bootstrap_iterations"],
            "correction_method": params["correction_method"],
            "dimensions_in_cqs": params["dimensions"],
            "d6_excluded": True,
            "input_files": {k: str(v) for k, v in files.items()},
        },
        "cqs_friedman": cqs_friedman,
        "cqs_pairwise": cqs_pairwise,
        "per_dimension": dim_results,
        "per_query_cqs": {
            cond: {qid: cqs[cond].get(qid, float("nan")) for qid in query_ids}
            for cond in CONDITIONS
        },
    }

    return results, cqs_pairwise, dim_results


def main():
    parser = argparse.ArgumentParser(
        description="V2 aggregate statistical analysis: Friedman + Wilcoxon + Holm"
    )
    parser.add_argument(
        "--rag-vs-pragmatics", dest="rag_vs_pragmatics",
        help="Path to rag_vs_pragmatics Stage 2 JSONL",
    )
    parser.add_argument(
        "--control-vs-rag", dest="control_vs_rag",
        help="Path to control_vs_rag Stage 2 JSONL",
    )
    parser.add_argument(
        "--control-vs-pragmatics", dest="control_vs_pragmatics",
        help="Path to control_vs_pragmatics Stage 2 JSONL",
    )
    parser.add_argument(
        "--stage2-dir", dest="stage2_dir",
        default=str(DEFAULT_STAGE2_DIR),
        help="Directory for auto-discovery of Stage 2 JSONL files",
    )
    parser.add_argument(
        "--config", default=str(CONFIG_PATH),
        help="Path to judge_config.yaml",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))
    params = get_analysis_params(config)

    if all([args.rag_vs_pragmatics, args.control_vs_rag, args.control_vs_pragmatics]):
        files = {
            "rag_vs_pragmatics":      Path(args.rag_vs_pragmatics),
            "control_vs_rag":         Path(args.control_vs_rag),
            "control_vs_pragmatics":  Path(args.control_vs_pragmatics),
        }
    else:
        print(f"Auto-discovering Stage 2 files in {args.stage2_dir}...", file=sys.stderr)
        files = discover_stage2_files(Path(args.stage2_dir))

    for comparison, path in files.items():
        print(f"  {comparison}: {path}", file=sys.stderr)
        if not path.exists():
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            sys.exit(1)

    results, cqs_pairwise, dim_results = run_analysis(files, params)

    # Stdout summary
    print_summary(results["cqs_friedman"], cqs_pairwise, dim_results, params)

    # Write outputs
    output_dir = Path(params["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "aggregate_statistics.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=_json_default)
    print(f"\nJSON:     {json_path}", file=sys.stderr)

    md_content = build_markdown(
        results["cqs_friedman"], cqs_pairwise, dim_results, params
    )
    md_path = output_dir / "aggregate_statistics.md"
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Markdown: {md_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
