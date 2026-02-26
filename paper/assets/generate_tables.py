#!/usr/bin/env python3
"""Generate publication-ready markdown tables for the pragmatics paper.

Reads certified analysis JSONs and produces markdown tables that replace
[INSERT TABLE] placeholders in paper/sections/05_results.md.

Source data:
  - results/v2_redo/stage2/analysis/aggregate_statistics.json (T1-T3)
  - results/v2_redo/stage2/analysis/stratum_analysis.json (T4)
  - results/v2_redo/stage3/analysis/fidelity_summary.json (T5)
  - results/v2_redo/stage1/analysis/cost_analysis.json (T6)

Usage:
  python paper/assets/generate_tables.py --preview     # print all tables to stdout
  python paper/assets/generate_tables.py --apply       # replace placeholders in 05_results.md
  python paper/assets/generate_tables.py --table T3    # preview single table

Traceability: Each table function documents which numbers_registry.md IDs it consumes.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_PATHS = {
    "agg": REPO_ROOT / "results/v2_redo/stage2/analysis/aggregate_statistics.json",
    "stratum": REPO_ROOT / "results/v2_redo/stage2/analysis/stratum_analysis.json",
    "fidelity": REPO_ROOT / "results/v2_redo/stage3/analysis/fidelity_summary.json",
    "cost": REPO_ROOT / "results/v2_redo/stage1/analysis/cost_analysis.json",
}

SECTION_PATH = REPO_ROOT / "paper/sections/05_results.md"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def fmt_p(p_value: float) -> str:
    """Format p-value in APA style: '< .001' or '.xyz' without leading zero."""
    if p_value < 0.001:
        return "< .001"
    return f"{p_value:.3f}"[1:]  # ".002" from "0.002"


def fmt_d(d_value: float, bold: bool = False) -> str:
    """Format Cohen's d to 3 decimal places, optionally bold."""
    s = f"{d_value:.3f}"
    return f"**{s}**" if bold else s


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Format as percentage with given decimal places."""
    return f"{value:.{decimals}f}%"


def fmt_dollar(value: float) -> str:
    """Format as dollar amount with 3 decimal places."""
    return f"${value:.3f}"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data() -> dict:
    """Read all 4 source JSONs. Exits with error if any file is missing."""
    data = {}
    for key, path in DATA_PATHS.items():
        if not path.exists():
            print(f"ERROR: Data file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with path.open(encoding="utf-8") as f:
            data[key] = json.load(f)
    return data


# ---------------------------------------------------------------------------
# Table generators
# ---------------------------------------------------------------------------


def generate_T1(data: dict) -> str:
    """T1: CQS composite scores by condition (condition means only).

    Registry IDs consumed: S2-040, S2-041, S2-042
    """
    cm = data["agg"]["cqs_friedman"]["condition_means"]
    n = data["agg"]["cqs_friedman"]["n"]

    lines = [
        "| Condition | Mean CQS | *n* |",
        "|-----------|----------|-----|",
        f"| Pragmatics | {cm['pragmatics']:.3f} | {n} |",
        f"| RAG | {cm['rag']:.3f} | {n} |",
        f"| Control | {cm['control']:.3f} | {n} |",
        "",
        ": CQS composite scores by condition (D1\u2013D5 mean of per-query medians). {#tbl-cqs-means}",
    ]
    return "\n".join(lines)


def generate_T2(data: dict) -> str:
    """T2: Friedman omnibus + Wilcoxon pairwise with Holm-Bonferroni correction.

    Registry IDs consumed: S2-001, S2-002, S2-010, S2-011, S2-012
    """
    fr = data["agg"]["cqs_friedman"]
    pw = data["agg"]["cqs_pairwise"]

    panel_a = [
        "**Panel A: Omnibus**",
        "",
        "| Test | Statistic | *p* | *n* |",
        "|------|-----------|-----|-----|",
        f"| Friedman \u03c7\u00b2(2) | {fr['stat']:.2f} | {fmt_p(fr['p'])} | {fr['n']} |",
    ]

    panel_b_header = [
        "",
        "**Panel B: Pairwise (Holm-corrected)**",
        "",
        "| Comparison | \u0394 CQS | Cohen\u2019s *d* | 95% CI | *p* (Holm) | Eff. *n* |",
        "|------------|-------|-------------|--------|------------|----------|",
    ]

    comparisons = [
        ("Pragmatics vs Control", pw["pragmatics_vs_control"]),
        ("Pragmatics vs RAG", pw["pragmatics_vs_rag"]),
        ("RAG vs Control", pw["rag_vs_control"]),
    ]

    panel_b_rows = []
    for label, comp in comparisons:
        row = (
            f"| {label}"
            f" | +{comp['delta']:.3f}"
            f" | {comp['cohens_d']:.3f}"
            f" | [{comp['ci_lo']:.3f}, {comp['ci_hi']:.3f}]"
            f" | {fmt_p(comp['p_holm'])}"
            f" | {comp['effective_n']} |"
        )
        panel_b_rows.append(row)

    caption = [
        "",
        ": Friedman omnibus and Wilcoxon signed-rank pairwise comparisons with"
        " Holm\u2013Bonferroni correction. Bootstrap 95% CIs (10,000 iterations)"
        " on CQS deltas. {#tbl-pairwise}",
    ]

    return "\n".join(panel_a + panel_b_header + panel_b_rows + caption)


def generate_T3(data: dict) -> str:
    """T3: Per-dimension effect sizes (Cohen's d) for all 3 comparisons × 5 dimensions.

    Registry IDs consumed: S2-030 through S2-034
    Bold any d >= 0.800.
    """
    pd_ = data["agg"]["per_dimension"]

    dim_labels = [
        ("D1", "D1 (Accuracy)"),
        ("D2", "D2 (Completeness)"),
        ("D3", "D3 (Uncertainty Communication)"),
        ("D4", "D4 (Contextual Clarity)"),
        ("D5", "D5 (Fitness-for-Use Assessment)"),
    ]

    lines = [
        "| Dimension | Prag vs Ctrl *d* | Prag vs RAG *d* | RAG vs Ctrl *d* |",
        "|-----------|-----------------|-----------------|-----------------|",
    ]

    for dim, label in dim_labels:
        pw = pd_[dim]["pairwise"]
        pc = pw["pragmatics_vs_control"]["cohens_d"]
        pr = pw["pragmatics_vs_rag"]["cohens_d"]
        rc = pw["rag_vs_control"]["cohens_d"]
        lines.append(
            f"| {label}"
            f" | {fmt_d(pc, pc >= 0.800)}"
            f" | {fmt_d(pr, pr >= 0.800)}"
            f" | {fmt_d(rc, rc >= 0.800)} |"
        )

    lines.extend([
        "",
        ": Per-dimension Cohen\u2019s *d* effect sizes. Bold indicates *d* > 0.8 (large)."
        " {#tbl-dimension-effects}",
    ])
    return "\n".join(lines)


def generate_T4(data: dict) -> str:
    """T4: Stratum analysis comparing normal vs edge-case queries.

    Registry IDs consumed: SA-001 through SA-022
    Bold Normal d for pragmatics comparisons (key finding: normal > edge, no overfit).
    """
    sr = data["stratum"]["stratum_results"]
    bs = data["stratum"]["between_stratum"]
    n_normal = data["stratum"]["stratum_composition"]["normal"]["n"]
    n_edge = data["stratum"]["stratum_composition"]["edge"]["n"]

    comparisons = [
        ("Prag vs Ctrl", "pragmatics_vs_control", True),
        ("Prag vs RAG", "pragmatics_vs_rag", True),
        ("RAG vs Ctrl", "rag_vs_control", False),
    ]

    lines = [
        f"| Comparison | Normal *d* (*n*={n_normal}) | Edge *d* (*n*={n_edge})"
        f" | \u0394*d* (Edge\u2212Normal) | *p* (Edge > Normal) |",
        "|------------|--------------------|--------------------|---------------------|---------------------|",
    ]

    for label, key, is_prag in comparisons:
        nd = sr["normal"]["pairwise"][key]["cohens_d"]
        ed = sr["edge"]["pairwise"][key]["cohens_d"]
        dod = bs[key]["delta_of_deltas"]
        p = bs[key]["mann_whitney"]["p_greater"]

        nd_fmt = fmt_d(nd, bold=is_prag)
        ed_fmt = fmt_d(ed, bold=False)
        dod_str = f"+{dod:.3f}" if dod >= 0 else f"{dod:.3f}"

        lines.append(f"| {label} | {nd_fmt} | {ed_fmt} | {dod_str} | {fmt_p(p)} |")

    caption = (
        f": Stratum analysis comparing normal (*n*={n_normal}) and edge-case"
        f" (*n*={n_edge}) queries. \u0394*d* is the delta-of-deltas (edge minus normal"
        f" mean CQS delta). Mann-Whitney *p* tests whether edge deltas exceed normal"
        f" deltas. {{#tbl-stratum}}"
    )
    lines.extend(["", caption])
    return "\n".join(lines)


def generate_T5(data: dict) -> str:
    """T5: Pipeline fidelity by condition.

    Registry IDs consumed: S3-001 through S3-003, S3-010 through S3-012

    NOTE: Reads from JSON ground truth. The registry had S3-010/S3-011 swapped
    (Control/RAG auditability). That swap was corrected in numbers_registry.md
    on 2026-02-26. JSON ground truth: Control auditable=21.8%, RAG auditable=6.2%.
    """
    fid = data["fidelity"]["overall"]["fidelity"]
    aud = data["fidelity"]["overall"]["auditability"]

    conditions = [
        ("Pragmatics", "pragmatics"),
        ("RAG", "rag"),
        ("Control", "control"),
    ]

    lines = [
        "| Condition | Claims | Fidelity | Subst. Fidelity | Error Rate | Auditable |",
        "|-----------|--------|----------|-----------------|------------|-----------|",
    ]

    for label, key in conditions:
        f = fid[key]
        a = aud[key]
        row = (
            f"| {label}"
            f" | {f['total_claims']}"
            f" | {fmt_pct(f['fidelity'])}"
            f" | {fmt_pct(f['substantive_fidelity'])}"
            f" | {fmt_pct(f['error_rate'])}"
            f" | {fmt_pct(a['auditable_rate'])} |"
        )
        lines.append(row)

    lines.extend([
        "",
        ": Stage 3 fidelity verification. Fidelity = (matched + calculation_correct)"
        " / total_claims. Substantive fidelity excludes no_source claims. Error rate ="
        " (mismatched + calculation_incorrect) / total_claims. Auditable = fully"
        " auditable claims / substantive claims. {#tbl-fidelity}",
    ])
    return "\n".join(lines)


def generate_T6(data: dict) -> str:
    """T6: Cost analysis at two pricing tiers.

    Registry IDs consumed: COST-001 through COST-005, COST-010 through COST-013
    Bold 6.28 (Sonnet CQS/marginal$ for pragmatics) and 2.2× ratio (key findings).
    """
    pricing = data["cost"]["pricing"]
    costs = data["cost"]["costs"]

    sonnet_key = "claude-sonnet-4-5"
    opus_key = "claude-opus-4-6"

    s_inp = pricing[sonnet_key]["input_per_mtok"]
    s_out = pricing[sonnet_key]["output_per_mtok"]
    o_inp = pricing[opus_key]["input_per_mtok"]
    o_out = pricing[opus_key]["output_per_mtok"]

    sc = costs[sonnet_key]["per_condition"]
    oc = costs[opus_key]["per_condition"]
    ratio = costs[sonnet_key]["pragmatics_vs_rag_effectiveness_ratio"]

    s_rag_eff = sc["rag"]["cqs_per_marginal_dollar"]
    s_prag_eff = sc["pragmatics"]["cqs_per_marginal_dollar"]
    o_rag_eff = oc["rag"]["cqs_per_marginal_dollar"]
    o_prag_eff = oc["pragmatics"]["cqs_per_marginal_dollar"]

    lines = [
        "| Metric | Control | RAG | Pragmatics |",
        "|--------|---------|-----|------------|",
        f"| **Sonnet 4.5** (${s_inp:.0f}/${s_out:.0f} per MTok) | | | |",
        f"| Cost per query"
        f" | {fmt_dollar(sc['control']['cost_per_query'])}"
        f" | {fmt_dollar(sc['rag']['cost_per_query'])}"
        f" | {fmt_dollar(sc['pragmatics']['cost_per_query'])} |",
        f"| Marginal cost vs control"
        f" | \u2014"
        f" | {fmt_dollar(sc['rag']['marginal_cost_per_query'])}"
        f" | {fmt_dollar(sc['pragmatics']['marginal_cost_per_query'])} |",
        f"| CQS per marginal $ | \u2014 | {s_rag_eff:.2f} | **{s_prag_eff:.2f}** |",
        f"| **Opus 4.6** (${o_inp:.0f}/${o_out:.0f} per MTok) | | | |",
        f"| Cost per query"
        f" | {fmt_dollar(oc['control']['cost_per_query'])}"
        f" | {fmt_dollar(oc['rag']['cost_per_query'])}"
        f" | {fmt_dollar(oc['pragmatics']['cost_per_query'])} |",
        f"| Marginal cost vs control"
        f" | \u2014"
        f" | {fmt_dollar(oc['rag']['marginal_cost_per_query'])}"
        f" | {fmt_dollar(oc['pragmatics']['marginal_cost_per_query'])} |",
        f"| CQS per marginal $ | \u2014 | {o_rag_eff:.2f} | {o_prag_eff:.2f} |",
        "| | | | |",
        f"| Cost-effectiveness ratio (Prag/RAG) | \u2014 | \u2014 | **{ratio:.1f}\u00d7** |",
        "",
        ": Cost analysis at two pricing tiers. Marginal cost = condition cost minus"
        " control baseline. CQS per marginal dollar = CQS improvement over control /"
        " marginal cost per query. Cost-effectiveness ratio is constant across pricing"
        " tiers. {#tbl-cost}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

GENERATORS: dict = {
    "T1": generate_T1,
    "T2": generate_T2,
    "T3": generate_T3,
    "T4": generate_T4,
    "T5": generate_T5,
    "T6": generate_T6,
}


# ---------------------------------------------------------------------------
# Apply to section file
# ---------------------------------------------------------------------------


def apply_tables(section_path: Path, data: dict) -> None:
    """Replace [INSERT TABLE Tn: ...] placeholders in the section file."""
    content = section_path.read_text(encoding="utf-8")
    original = content

    for key, generator in GENERATORS.items():
        n = key[1]  # "1" from "T1"
        pattern = re.compile(rf"> \*\*\[INSERT TABLE T{n}: [^\]]+\]\*\*")
        if not pattern.search(content):
            print(f"  WARNING: Placeholder for {key} not found; skipping.", file=sys.stderr)
            continue
        table_md = generator(data)
        # Use lambda to avoid re.sub backslash processing in replacement string
        content = pattern.sub(lambda m, t=table_md: t, content)
        print(f"  Applied {key}")

    if content == original:
        print("No changes made (no placeholders matched).", file=sys.stderr)
        return

    section_path.write_text(content, encoding="utf-8")
    print(f"Wrote {section_path}")

    # Verify no placeholders remain
    remaining = re.findall(r"\[INSERT TABLE T\d:", content)
    if remaining:
        print(
            f"WARNING: {len(remaining)} placeholder(s) still remain: {remaining}",
            file=sys.stderr,
        )
    else:
        print("Verification: 0 [INSERT TABLE] placeholders remain. \u2713")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate publication-ready markdown tables for the pragmatics paper.",
        epilog="Source data: results/v2_redo/ analysis JSONs. Target: paper/sections/05_results.md",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--preview",
        action="store_true",
        help="Print all 6 tables to stdout",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Replace [INSERT TABLE] placeholders in paper/sections/05_results.md",
    )
    group.add_argument(
        "--table",
        metavar="Tn",
        help="Preview a single table by ID (e.g. T3)",
    )
    args = parser.parse_args()

    data = load_data()

    if args.preview:
        for key, generator in GENERATORS.items():
            print(f"\n{'=' * 60}")
            print(f"TABLE {key}")
            print("=" * 60)
            print(generator(data))

    elif args.table:
        key = args.table.upper()
        if key not in GENERATORS:
            print(
                f"ERROR: Unknown table '{args.table}'. Choose from: {', '.join(GENERATORS)}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(GENERATORS[key](data))

    elif args.apply:
        print(f"Applying tables to {SECTION_PATH} ...")
        apply_tables(SECTION_PATH, data)


if __name__ == "__main__":
    main()
