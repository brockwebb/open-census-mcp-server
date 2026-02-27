#!/usr/bin/env python3
"""Generate publication-ready figures for the pragmatics paper.

Reads certified analysis JSONs and produces PDF figures using plotnine.

Source data:
  - talks/fcsm_2026/analysis/results/similarity_results_*.json (F2a, F2b)
  - results/v2_redo/stage2/analysis/aggregate_statistics.json (F7)
  - results/v2_redo/stage3/analysis/fidelity_summary.json (F8)
  - results/v2_redo/stage1/analysis/cost_analysis.json (F9)

Usage:
  python paper/assets/generate_figures.py --all          # generate all figures
  python paper/assets/generate_figures.py --figure F7    # generate single figure
  python paper/assets/generate_figures.py --preview      # show in window, don't save

Output: paper/assets/figures/*.pdf

Note on F2: F2 is split into two PDFs (F2a_similarity, F2b_discrimination) because
plotnine does not natively support multi-panel composition. Both replace the single
F2 placeholder as paired subfigures.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from plotnine import (
    ggplot,
    aes,
    annotate,
    coord_cartesian,
    element_text,
    facet_wrap,
    geom_col,
    geom_hline,
    geom_point,
    geom_segment,
    geom_text,
    geom_vline,
    labs,
    position_dodge,
    scale_color_manual,
    scale_fill_manual,
    scale_shape_manual,
    scale_x_continuous,
    scale_y_continuous,
    scale_y_discrete,
    theme,
)
from census_plot_style import COLORS, COLORS_F2, COLORS_F7, paper_theme, save_figure

REPO_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = REPO_ROOT / "paper/assets/figures"

DATA_PATHS = {
    "minilm": REPO_ROOT / "talks/fcsm_2026/analysis/results/similarity_results_minilm.json",
    "roberta": REPO_ROOT / "talks/fcsm_2026/analysis/results/similarity_results_roberta.json",
    "agg": REPO_ROOT / "results/v2_redo/stage2/analysis/aggregate_statistics.json",
    "fidelity": REPO_ROOT / "results/v2_redo/stage3/analysis/fidelity_summary.json",
    "cost": REPO_ROOT / "results/v2_redo/stage1/analysis/cost_analysis.json",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data() -> dict:
    """Read all source JSONs. Exits with error if any file is missing."""
    data = {}
    for key, path in DATA_PATHS.items():
        if not path.exists():
            print(f"ERROR: Data file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with path.open(encoding="utf-8") as f:
            data[key] = json.load(f)
    return data


# ---------------------------------------------------------------------------
# Figure generators
# ---------------------------------------------------------------------------


def make_F2a(data: dict):
    """F2a: Mean pairwise similarity by representation (Panel A).

    Grouped bar chart: 3 representations × 2 models, faceted by model.
    Annotates % increase on Enriched bars.
    """
    ml = data["minilm"]["similarity"]
    rb = data["roberta"]["similarity"]

    # % increase from Raw to Enriched
    ml_inc = (ml["enriched"]["mean"] - ml["raw"]["mean"]) / ml["raw"]["mean"] * 100
    rb_inc = (rb["enriched"]["mean"] - rb["raw"]["mean"]) / rb["raw"]["mean"] * 100

    rows = []
    for rep_key, rep_label in [("labels", "Labels"), ("raw", "Raw"), ("enriched", "Enriched")]:
        rows.append({
            "Model": "MiniLM-384",
            "Representation": rep_label,
            "Similarity": ml[rep_key]["mean"],
        })
        rows.append({
            "Model": "RoBERTa-1024",
            "Representation": rep_label,
            "Similarity": rb[rep_key]["mean"],
        })
    df = pd.DataFrame(rows)
    df["Representation"] = pd.Categorical(
        df["Representation"], categories=["Labels", "Raw", "Enriched"], ordered=True
    )

    # Annotation rows for the Enriched bars
    ann_df = pd.DataFrame([
        {
            "Model": "MiniLM-384",
            "Representation": "Enriched",
            "Similarity": ml["enriched"]["mean"] + 0.03,
            "label": f"+{ml_inc:.1f}%",
        },
        {
            "Model": "RoBERTa-1024",
            "Representation": "Enriched",
            "Similarity": rb["enriched"]["mean"] + 0.03,
            "label": f"+{rb_inc:.1f}%",
        },
    ])

    p = (
        ggplot(df, aes("Representation", "Similarity", fill="Representation"))
        + geom_col(show_legend=False)
        + geom_text(
            aes(x="Representation", y="Similarity", label="label"),
            data=ann_df,
            size=9,
            va="bottom",
        )
        + facet_wrap("~Model")
        + scale_fill_manual(values=COLORS_F2)
        + scale_y_continuous(limits=[0, 1.1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
        + labs(
            x="",
            y="Mean Cosine Similarity",
            title="Panel A: Mean Pairwise Similarity by Representation",
        )
        + paper_theme(figure_size=(6.5, 3.5))
        + theme(legend_position="none")
    )
    return p


def make_F2b(data: dict):
    """F2b: Group discrimination collapse (Panel B).

    Within-group vs cross-group similarity for Raw and Enriched, faceted by model.
    Annotates discrimination gap (delta) above each condition pair.
    """
    ml_disc = data["minilm"]["discrimination"]
    rb_disc = data["roberta"]["discrimination"]

    rows = []
    for model_label, disc in [("MiniLM-384", ml_disc), ("RoBERTa-1024", rb_disc)]:
        for cond_key, cond_label in [("raw", "Raw"), ("enriched", "Enriched")]:
            d = disc[cond_key]
            rows.extend([
                {
                    "Model": model_label,
                    "Condition": cond_label,
                    "Type": "Within-Group",
                    "Similarity": d["within_mean"],
                },
                {
                    "Model": model_label,
                    "Condition": cond_label,
                    "Type": "Cross-Group",
                    "Similarity": d["cross_mean"],
                },
            ])
    df = pd.DataFrame(rows)
    df["Condition"] = pd.Categorical(df["Condition"], categories=["Raw", "Enriched"], ordered=True)
    df["Type"] = pd.Categorical(df["Type"], categories=["Within-Group", "Cross-Group"], ordered=True)

    # Discrimination gap annotations (above the within-group bar for each condition)
    ml_red = data["minilm"]["discrimination"]["reduction_pct"]
    rb_red = data["roberta"]["discrimination"]["reduction_pct"]

    ann_rows = []
    for model_label, disc, reduction in [
        ("MiniLM-384", ml_disc, ml_red),
        ("RoBERTa-1024", rb_disc, rb_red),
    ]:
        for cond_key, cond_label in [("raw", "Raw"), ("enriched", "Enriched")]:
            d = disc[cond_key]
            ann_rows.append({
                "Model": model_label,
                "Condition": cond_label,
                "Type": "Within-Group",  # anchor to within-group bar
                "Similarity": d["within_mean"] + 0.04,
                "label": f"\u0394={d['delta']:.3f}",
            })
        # Reduction annotation at midpoint
        ann_rows.append({
            "Model": model_label,
            "Condition": "Enriched",
            "Type": "Cross-Group",
            "Similarity": disc["enriched"]["within_mean"] + 0.10,
            "label": f"\u2212{reduction:.1f}% disc.",
        })
    ann_df = pd.DataFrame(ann_rows)

    disc_colors = {"Within-Group": "#4477AA", "Cross-Group": "#AABBCC"}

    p = (
        ggplot(df, aes("Condition", "Similarity", fill="Type"))
        + geom_col(position="dodge")
        + geom_text(
            aes(x="Condition", y="Similarity", label="label"),
            data=ann_df,
            size=8,
            va="bottom",
        )
        + facet_wrap("~Model")
        + scale_fill_manual(
            values=disc_colors,
            name="Similarity Type",
        )
        + scale_y_continuous(limits=[0, 1.05], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
        + labs(
            x="",
            y="Mean Cosine Similarity",
            title="Panel B: Discrimination Collapse — Within vs. Cross-Group Similarity",
        )
        + paper_theme(figure_size=(6.5, 3.5))
    )
    return p


def make_F7(data: dict):
    """F7: Forest plot of Cohen's d effect sizes by dimension.

    Horizontal point plot with 3 comparison series, 6 rows (CQS + 5 dimensions).
    Uses manual Y-position offsets for reliable dodging on a continuous Y axis.
    Reference lines at d = 0.2 (small), 0.5 (medium), 0.8 (large).
    """
    agg = data["agg"]
    pw = agg["cqs_pairwise"]
    pd_ = agg["per_dimension"]

    # Y positions: CQS Composite at top (6.5), D5 at bottom (1), with extra gap
    y_base = {
        "D5 (Fitness-for-Use)": 1,
        "D4 (Contextual Clarity)": 2,
        "D3 (Uncertainty)": 3,
        "D2 (Completeness)": 4,
        "D1 (Accuracy)": 5,
        "CQS Composite": 6.5,
    }
    y_offset = {
        "Prag vs Ctrl": 0.15,
        "Prag vs RAG": 0.0,
        "RAG vs Ctrl": -0.15,
    }

    comparisons = [
        ("Prag vs Ctrl", "pragmatics_vs_control"),
        ("Prag vs RAG", "pragmatics_vs_rag"),
        ("RAG vs Ctrl", "rag_vs_control"),
    ]

    dim_labels = [
        ("CQS Composite", "cqs"),
        ("D1 (Accuracy)", "D1"),
        ("D2 (Completeness)", "D2"),
        ("D3 (Uncertainty)", "D3"),
        ("D4 (Contextual Clarity)", "D4"),
        ("D5 (Fitness-for-Use)", "D5"),
    ]

    rows = []
    for dim_label, dim_key in dim_labels:
        for comp_label, comp_key in comparisons:
            d_val = (
                pw[comp_key]["cohens_d"]
                if dim_key == "cqs"
                else pd_[dim_key]["pairwise"][comp_key]["cohens_d"]
            )
            rows.append({
                "Dimension": dim_label,
                "Comparison": comp_label,
                "d": d_val,
                "y": y_base[dim_label] + y_offset[comp_label],
            })
    df = pd.DataFrame(rows)

    shapes = {
        "Prag vs Ctrl": "o",
        "Prag vs RAG": "s",
        "RAG vs Ctrl": "^",
    }

    y_breaks = list(y_base.values())
    y_labels = list(y_base.keys())

    p = (
        ggplot(df, aes(x="d", y="y", color="Comparison", shape="Comparison"))
        + geom_vline(xintercept=0.2, linetype="dashed", color="#cccccc", size=0.6)
        + geom_vline(xintercept=0.5, linetype="dashed", color="#cccccc", size=0.6)
        + geom_vline(xintercept=0.8, linetype="dashed", color="#bbbbbb", size=0.6)
        + geom_hline(yintercept=5.75, linetype="dotted", color="#bbbbbb", size=0.5)
        + geom_point(size=3)
        + scale_color_manual(values=COLORS_F7, name="Comparison")
        + scale_shape_manual(values=shapes, name="Comparison")
        + scale_x_continuous(limits=[0, 2.6], breaks=[0, 0.5, 1.0, 1.5, 2.0, 2.5])
        + scale_y_continuous(
            limits=[0.5, 7.0],
            breaks=y_breaks,
            labels=y_labels,
        )
        + labs(
            x="Cohen's \u03b4",
            y="",
            title="Effect Sizes by Dimension",
            caption=(
                "Vertical lines: \u03b4= 0.2 (small), 0.5 (medium), 0.8 (large). "
                "Dotted line separates composite from per-dimension. "
                "Points dodged \u00b10.15 units for clarity."
            ),
        )
        + paper_theme(figure_size=(6.5, 5.0))
        + theme(legend_position="right", plot_caption=element_text(size=8))
    )
    return p


def make_F8(data: dict):
    """F8: Fidelity bar chart — one bar per condition, fidelity %.

    Simple bar chart with annotated values. Substantive fidelity and error rate
    noted in caption (they are all 98.9–100.0% and 0–0.8%, too similar to plot).
    """
    fid = data["fidelity"]["overall"]["fidelity"]

    rows = [
        {
            "Condition": "Control",
            "Fidelity": fid["control"]["fidelity"],
            "label": f"{fid['control']['fidelity']:.1f}%",
        },
        {
            "Condition": "RAG",
            "Fidelity": fid["rag"]["fidelity"],
            "label": f"{fid['rag']['fidelity']:.1f}%",
        },
        {
            "Condition": "Pragmatics",
            "Fidelity": fid["pragmatics"]["fidelity"],
            "label": f"{fid['pragmatics']['fidelity']:.1f}%",
        },
    ]
    df = pd.DataFrame(rows)
    df["Condition"] = pd.Categorical(
        df["Condition"], categories=["Control", "RAG", "Pragmatics"], ordered=True
    )

    p = (
        ggplot(df, aes("Condition", "Fidelity", fill="Condition"))
        + geom_col(show_legend=False)
        + geom_text(aes(label="label"), va="bottom", nudge_y=0.8, size=10)
        + scale_fill_manual(values=COLORS)
        + scale_y_continuous(limits=[0, 105], breaks=[0, 20, 40, 60, 80, 100])
        + labs(
            x="",
            y="Fidelity (%)",
            title="Stage 3 Pipeline Fidelity by Condition",
            caption=(
                "Fidelity = (matched + calculation_correct) / total_claims. "
                "Substantive fidelity: Control 100.0%, RAG 98.9%, Pragmatics 99.7%. "
                "Error rates: Control 0.0%, RAG 0.8%, Pragmatics 0.3%."
            ),
        )
        + paper_theme(figure_size=(5.0, 4.0))
        + theme(legend_position="none", plot_caption=element_text(size=8))
    )
    return p


def make_F9(data: dict):
    """F9: Cost-effectiveness — CQS improvement per marginal dollar (Sonnet pricing).

    Simple bar chart for RAG and Pragmatics with 2.2× effectiveness ratio annotated.
    Sonnet 4.5 pricing only (Opus is secondary; ratio is constant across tiers).
    """
    sonnet = data["cost"]["costs"]["claude-sonnet-4-5"]["per_condition"]
    ratio = data["cost"]["costs"]["claude-sonnet-4-5"]["pragmatics_vs_rag_effectiveness_ratio"]

    rag_eff = sonnet["rag"]["cqs_per_marginal_dollar"]
    prag_eff = sonnet["pragmatics"]["cqs_per_marginal_dollar"]

    rows = [
        {
            "Condition": "RAG",
            "CQS_per_dollar": rag_eff,
            "label": f"{rag_eff:.2f}",
        },
        {
            "Condition": "Pragmatics",
            "CQS_per_dollar": prag_eff,
            "label": f"{prag_eff:.2f}",
        },
    ]
    df = pd.DataFrame(rows)
    df["Condition"] = pd.Categorical(
        df["Condition"], categories=["RAG", "Pragmatics"], ordered=True
    )

    y_bracket = prag_eff + 0.7  # above the taller bar
    y_text = y_bracket + 0.5

    p = (
        ggplot(df, aes("Condition", "CQS_per_dollar", fill="Condition"))
        + geom_col(show_legend=False)
        + geom_text(aes(label="label"), va="bottom", nudge_y=0.15, size=11)
        # Horizontal bracket
        + annotate("segment", x=1, xend=2, y=y_bracket, yend=y_bracket, color="black", size=0.6)
        + annotate("segment", x=1, xend=1, y=y_bracket - 0.15, yend=y_bracket, color="black", size=0.6)
        + annotate("segment", x=2, xend=2, y=y_bracket - 0.15, yend=y_bracket, color="black", size=0.6)
        + annotate(
            "text",
            x=1.5,
            y=y_text,
            label=f"{ratio:.1f}\u00d7 more cost-effective",
            size=10,
            ha="center",
        )
        + scale_fill_manual(
            values={"RAG": COLORS["RAG"], "Pragmatics": COLORS["Pragmatics"]},
        )
        + scale_y_continuous(
            limits=[0, y_text + 1],
            breaks=[0, 1, 2, 3, 4, 5, 6, 7],
        )
        + labs(
            x="",
            y="CQS Improvement per Marginal Dollar",
            title="Cost-Effectiveness: CQS per Marginal Dollar",
            caption="Claude Sonnet 4.5 pricing ($3/$15 per MTok). Marginal cost vs control baseline.",
        )
        + paper_theme(figure_size=(4.5, 4.5))
        + theme(legend_position="none", plot_caption=element_text(size=8))
    )
    return p


# ---------------------------------------------------------------------------
# Save and apply
# ---------------------------------------------------------------------------


FIGURES: dict = {
    "F2a": {
        "fn": make_F2a,
        "filename": "F2a_semantic_smearing_similarity.pdf",
        "width": 6.5,
        "height": 3.5,
        "placeholder_section": "02_semantic_smearing.md",
        "placeholder_key": "F2",
    },
    "F2b": {
        "fn": make_F2b,
        "filename": "F2b_semantic_smearing_discrimination.pdf",
        "width": 6.5,
        "height": 3.5,
        "placeholder_section": None,  # replaced together with F2a
        "placeholder_key": None,
    },
    "F7": {
        "fn": make_F7,
        "filename": "F7_effect_sizes_forest.pdf",
        "width": 6.5,
        "height": 5.0,
        "placeholder_section": "05_results.md",
        "placeholder_key": "F7",
    },
    "F8": {
        "fn": make_F8,
        "filename": "F8_fidelity_bars.pdf",
        "width": 5.0,
        "height": 4.0,
        "placeholder_section": "05_results.md",
        "placeholder_key": "F8",
    },
    "F9": {
        "fn": make_F9,
        "filename": "F9_cost_effectiveness.pdf",
        "width": 4.5,
        "height": 4.5,
        "placeholder_section": "05_results.md",
        "placeholder_key": "F9",
    },
}


def apply_figures() -> None:
    """Replace [INSERT FIGURE Fn] placeholders with Quarto image references.

    F2: replaced with TWO figure references (F2a and F2b subfigures).
    F7, F8, F9: each replaced with one figure reference.
    """
    import re

    sections_dir = REPO_ROOT / "paper/sections"

    replacements = {
        "F2": (
            "![Semantic smearing: mean pairwise similarity by representation.]"
            "(assets/figures/F2a_semantic_smearing_similarity.pdf)"
            "{#fig-smearing-similarity width=6.5in}\n\n"
            "![Semantic smearing: group discrimination collapse.]"
            "(assets/figures/F2b_semantic_smearing_discrimination.pdf)"
            "{#fig-smearing-discrimination width=6.5in}"
        ),
        "F7": (
            "![Cohen's *d* effect sizes by dimension. Vertical lines: "
            "*d* = 0.2 (small), 0.5 (medium), 0.8 (large).]"
            "(assets/figures/F7_effect_sizes_forest.pdf)"
            "{#fig-effect-sizes width=6.5in}"
        ),
        "F8": (
            "![Stage 3 pipeline fidelity by condition. Substantive fidelity "
            "(98.9–100.0%) and error rates (0.0–0.8%) annotated in caption.]"
            "(assets/figures/F8_fidelity_bars.pdf)"
            "{#fig-fidelity width=5.0in}"
        ),
        "F9": (
            "![Cost-effectiveness: CQS improvement per marginal dollar. "
            "Pragmatics is 2.2\u00d7 more cost-effective than RAG.]"
            "(assets/figures/F9_cost_effectiveness.pdf)"
            "{#fig-cost-effectiveness width=4.5in}"
        ),
    }

    pattern = re.compile(r"> \*\*\[INSERT FIGURE F(\w+): [^\]]+\]\*\*")

    files_to_update = {
        "02_semantic_smearing.md",
        "05_results.md",
    }

    for fname in files_to_update:
        path = sections_dir / fname
        if not path.exists():
            print(f"  WARNING: {fname} not found; skipping.", file=sys.stderr)
            continue
        content = path.read_text(encoding="utf-8")
        original = content

        for m in pattern.finditer(original):
            fig_key = f"F{m.group(1)}"
            if fig_key in replacements:
                replacement = replacements[fig_key]
                content = content.replace(m.group(0), replacement)
                print(f"  Applied {fig_key} in {fname}")

        if content != original:
            path.write_text(content, encoding="utf-8")
            print(f"  Wrote {path}")

    # Verify no placeholders remain
    for fname in files_to_update:
        path = sections_dir / fname
        if not path.exists():
            continue
        remaining = re.findall(r"\[INSERT FIGURE F\w+:", path.read_text())
        if remaining:
            print(f"  WARNING: {len(remaining)} placeholder(s) remain in {fname}: {remaining}", file=sys.stderr)
        else:
            print(f"  Verification: 0 [INSERT FIGURE] placeholders in {fname}. \u2713")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate publication-ready PDF figures for the pragmatics paper.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Generate all figures and save to paper/assets/figures/",
    )
    group.add_argument(
        "--figure",
        metavar="FN",
        help="Generate a single figure by ID (e.g. F7, F2a, F2b)",
    )
    group.add_argument(
        "--preview",
        action="store_true",
        help="Generate all figures and display in window (do not save)",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Replace [INSERT FIGURE] placeholders in section files (run after --all)",
    )
    args = parser.parse_args()

    data = load_data()

    if args.all:
        print("Generating all figures...")
        for key, cfg in FIGURES.items():
            p = cfg["fn"](data)
            save_figure(p, cfg["filename"], output_dir=FIGURES_DIR, width=cfg["width"], height=cfg["height"])

    elif args.figure:
        key = args.figure.upper()
        if key not in FIGURES:
            print(
                f"ERROR: Unknown figure '{args.figure}'. "
                f"Choose from: {', '.join(FIGURES)}",
                file=sys.stderr,
            )
            sys.exit(1)
        cfg = FIGURES[key]
        p = cfg["fn"](data)
        save_figure(p, cfg["filename"], output_dir=FIGURES_DIR, width=cfg["width"], height=cfg["height"])

    elif args.preview:
        import matplotlib.pyplot as plt
        print("Rendering all figures (preview mode, not saving)...")
        for key, cfg in FIGURES.items():
            print(f"  {key}: {cfg['filename']}")
            p = cfg["fn"](data)
            p.draw()
        plt.show()

    elif args.apply:
        print("Replacing [INSERT FIGURE] placeholders in section files...")
        apply_figures()


if __name__ == "__main__":
    main()
