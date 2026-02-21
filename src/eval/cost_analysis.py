#!/usr/bin/env python3
"""Token cost analysis: per-query and battery-level dollar costs per condition.

Uses actual token counts from overhead_analysis.json and hardcoded pricing
from the Anthropic model overview (retrieved 2026-02-21).

Pricing source (APA):
  Anthropic. (2026). Claude model pricing and API overview. Retrieved
  February 21, 2026, from
  https://platform.claude.com/docs/en/about-claude/models/overview

Pricing as of 2026-02-21 (per million tokens / MTok):
  claude-sonnet-4-5-20250929  input $3.00  output $15.00
  claude-sonnet-4-6            input $3.00  output $15.00
  claude-opus-4-6              input $5.00  output $25.00

Methodology:
  cost_per_query = (mean_input_tokens × input_rate) + (mean_output_tokens × output_rate)
  where rates are in $/token (i.e., $/MTok ÷ 1,000,000)

Inputs:
  results/v2_redo/stage1/analysis/overhead_analysis.json
  results/v2_redo/stage2/analysis/aggregate_statistics.json

Output:
  results/v2_redo/stage1/analysis/cost_analysis.md
  results/v2_redo/stage1/analysis/cost_analysis.json

Usage: python -m src.eval.cost_analysis
"""

import json
from datetime import datetime, timezone
from pathlib import Path


# ── Pricing (hardcoded, cited above) ─────────────────────────────────────────

# Rates in $/token (= $/MTok ÷ 1_000_000)
PRICING = {
    "claude-sonnet-4-5": {
        "label": "Claude Sonnet 4.5 (used in experiment)",
        "model_id": "claude-sonnet-4-5-20250929",
        "input_per_token": 3.00 / 1_000_000,
        "output_per_token": 15.00 / 1_000_000,
        "input_per_mtok": 3.00,
        "output_per_mtok": 15.00,
    },
    "claude-opus-4-6": {
        "label": "Claude Opus 4.6 (premium reference)",
        "model_id": "claude-opus-4-6",
        "input_per_token": 5.00 / 1_000_000,
        "output_per_token": 25.00 / 1_000_000,
        "input_per_mtok": 5.00,
        "output_per_mtok": 25.00,
    },
}

PRICING_SOURCE = (
    "Anthropic. (2026). Claude model pricing and API overview. "
    "Retrieved February 21, 2026, from "
    "https://platform.claude.com/docs/en/about-claude/models/overview"
)

PRICING_URL = "https://platform.claude.com/docs/en/about-claude/models/overview"
PRICING_RETRIEVED = "2026-02-21"

# ── Data loading ──────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ── Cost computation ──────────────────────────────────────────────────────────

def compute_costs(overhead: dict, cqs_means: dict, n_queries: int = 39) -> dict:
    """Compute per-condition, per-model costs and cost-effectiveness metrics."""
    conditions = ["control", "rag", "pragmatics"]
    results = {}

    for model_key, pricing in PRICING.items():
        model_results = {}

        for cond in conditions:
            cond_data = overhead["per_condition"][cond]
            mean_input = cond_data["input_tokens"]["mean"]
            mean_output = cond_data["output_tokens"]["mean"]

            cost_per_query = (
                mean_input * pricing["input_per_token"]
                + mean_output * pricing["output_per_token"]
            )
            total_battery_cost = cost_per_query * n_queries

            model_results[cond] = {
                "mean_input_tokens": mean_input,
                "mean_output_tokens": mean_output,
                "input_cost_per_query": mean_input * pricing["input_per_token"],
                "output_cost_per_query": mean_output * pricing["output_per_token"],
                "cost_per_query": cost_per_query,
                "total_battery_cost": total_battery_cost,
                "mean_cqs": cqs_means.get(cond, float("nan")),
            }

        # Marginal costs vs control
        ctrl = model_results["control"]
        for cond in ["rag", "pragmatics"]:
            c = model_results[cond]
            marginal_cost = c["cost_per_query"] - ctrl["cost_per_query"]
            cqs_improvement = c["mean_cqs"] - ctrl["mean_cqs"]

            c["marginal_cost_per_query"] = marginal_cost
            c["marginal_battery_cost"] = marginal_cost * n_queries
            c["cqs_improvement_over_control"] = cqs_improvement
            # CQS points per marginal dollar (higher = more cost-effective)
            if marginal_cost > 0:
                c["cqs_per_marginal_dollar"] = cqs_improvement / marginal_cost
            else:
                c["cqs_per_marginal_dollar"] = float("nan")

        # Cross-condition cost-effectiveness comparison
        prag = model_results["pragmatics"]
        rag = model_results["rag"]
        if rag.get("cqs_per_marginal_dollar") and prag.get("cqs_per_marginal_dollar"):
            ratio = prag["cqs_per_marginal_dollar"] / rag["cqs_per_marginal_dollar"]
        else:
            ratio = float("nan")

        results[model_key] = {
            "pricing": pricing,
            "per_condition": model_results,
            "pragmatics_vs_rag_effectiveness_ratio": ratio,
        }

    return results


# ── Markdown output ───────────────────────────────────────────────────────────

def fmt_cents(v: float) -> str:
    """Format dollar amount — use cents if < $0.10, else dollars."""
    if v < 0.001:
        return f"${v:.5f}"
    if v < 0.10:
        return f"${v:.4f} ({v*100:.2f}¢)"
    return f"${v:.4f}"


def fmt_dollar(v: float, dp: int = 4) -> str:
    return f"${v:.{dp}f}"


def build_markdown(costs: dict, n_queries: int, timestamp: str) -> str:
    conditions = ["control", "rag", "pragmatics"]
    lines = []

    lines.append("# Token Cost Analysis: Pragmatics vs RAG vs Control")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("**Script:** src/eval/cost_analysis.py")
    lines.append("")
    lines.append("## Pricing Source")
    lines.append("")
    lines.append(f"> {PRICING_SOURCE}")
    lines.append("")
    lines.append("| Model | Input ($/MTok) | Output ($/MTok) |")
    lines.append("|-------|---------------|----------------|")
    for mk, p in PRICING.items():
        lines.append(
            f"| {p['label']} (`{p['model_id']}`) | ${p['input_per_mtok']:.2f} | ${p['output_per_mtok']:.2f} |"
        )
    lines.append("")
    lines.append("**Methodology:** `cost = (mean_input_tokens × input_rate) + (mean_output_tokens × output_rate)`")
    lines.append("")
    lines.append("---")
    lines.append("")

    for model_key, model_data in costs.items():
        p = model_data["pricing"]
        per_cond = model_data["per_condition"]

        lines.append(f"## {p['label']}")
        lines.append("")

        # Per-query cost table
        lines.append("### Cost Per Query")
        lines.append("")
        lines.append("| Condition | Input tokens | Output tokens | Input cost | Output cost | **Total/query** |")
        lines.append("|-----------|-------------|--------------|-----------|------------|----------------|")
        for cond in conditions:
            c = per_cond[cond]
            lines.append(
                f"| {cond} | {c['mean_input_tokens']:,.0f} | {c['mean_output_tokens']:,.0f} | "
                f"{fmt_cents(c['input_cost_per_query'])} | {fmt_cents(c['output_cost_per_query'])} | "
                f"**{fmt_cents(c['cost_per_query'])}** |"
            )
        lines.append("")

        # Battery cost table
        lines.append(f"### Total Battery Cost ({n_queries} queries)")
        lines.append("")
        lines.append("| Condition | Per-query | **Total (39 queries)** | Marginal vs Control |")
        lines.append("|-----------|-----------|----------------------|---------------------|")
        for cond in conditions:
            c = per_cond[cond]
            marginal = c.get("marginal_battery_cost")
            marginal_str = f"+{fmt_dollar(marginal, 2)}" if marginal is not None else "—"
            lines.append(
                f"| {cond} | {fmt_cents(c['cost_per_query'])} | "
                f"**{fmt_dollar(c['total_battery_cost'], 2)}** | {marginal_str} |"
            )
        lines.append("")

        # Cost-effectiveness
        lines.append("### Cost-Effectiveness vs Control")
        lines.append("")
        lines.append("| Condition | CQS improvement | Marginal cost/query | CQS per marginal dollar |")
        lines.append("|-----------|----------------|---------------------|------------------------|")
        for cond in ["rag", "pragmatics"]:
            c = per_cond[cond]
            cpmd = c.get("cqs_per_marginal_dollar", float("nan"))
            cpmd_str = f"{cpmd:.2f}" if cpmd == cpmd else "N/A"  # NaN check
            lines.append(
                f"| {cond} | +{c['cqs_improvement_over_control']:.4f} CQS | "
                f"{fmt_cents(c['marginal_cost_per_query'])} | **{cpmd_str}** |"
            )
        lines.append("")

        ratio = model_data["pragmatics_vs_rag_effectiveness_ratio"]
        if ratio == ratio:  # not NaN
            lines.append(
                f"**Pragmatics is {ratio:.1f}× more cost-effective than RAG** "
                f"(CQS improvement per marginal dollar spent over control)."
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    # Key findings
    lines.append("## Key Findings")
    lines.append("")

    # Use Sonnet 4.5 for summary numbers
    s45 = costs["claude-sonnet-4-5"]["per_condition"]
    s45_ratio = costs["claude-sonnet-4-5"]["pragmatics_vs_rag_effectiveness_ratio"]
    o46 = costs["claude-opus-4-6"]["per_condition"]

    lines.append(f"**1. Absolute cost is negligible (Sonnet 4.5 pricing):**")
    lines.append(
        f"- Control: {fmt_cents(s45['control']['cost_per_query'])} per query "
        f"({fmt_dollar(s45['control']['total_battery_cost'], 2)} total)"
    )
    lines.append(
        f"- RAG: {fmt_cents(s45['rag']['cost_per_query'])} per query "
        f"({fmt_dollar(s45['rag']['total_battery_cost'], 2)} total)"
    )
    lines.append(
        f"- Pragmatics: {fmt_cents(s45['pragmatics']['cost_per_query'])} per query "
        f"({fmt_dollar(s45['pragmatics']['total_battery_cost'], 2)} total)"
    )
    lines.append("")
    lines.append(f"**2. Marginal cost of adding pragmatics:**")
    lines.append(
        f"- Sonnet 4.5: {fmt_cents(s45['pragmatics']['marginal_cost_per_query'])} per query "
        f"above control ({fmt_dollar(s45['pragmatics']['marginal_battery_cost'], 2)} for full 39-query battery)"
    )
    lines.append(
        f"- Opus 4.6: {fmt_cents(o46['pragmatics']['marginal_cost_per_query'])} per query "
        f"above control ({fmt_dollar(o46['pragmatics']['marginal_battery_cost'], 2)} for full battery)"
    )
    lines.append("")
    lines.append(f"**3. Cost-effectiveness (Sonnet 4.5):**")
    lines.append(
        f"- Pragmatics delivers {s45['pragmatics']['cqs_per_marginal_dollar']:.2f} CQS points "
        f"per marginal dollar over control"
    )
    lines.append(
        f"- RAG delivers {s45['rag']['cqs_per_marginal_dollar']:.2f} CQS points "
        f"per marginal dollar over control"
    )
    if s45_ratio == s45_ratio:
        lines.append(
            f"- **Pragmatics is {s45_ratio:.1f}× more cost-effective than RAG** per marginal dollar spent"
        )
    lines.append("")
    lines.append(
        f"**4. Even at premium Opus 4.6 pricing**, the full 39-query battery costs "
        f"{fmt_dollar(o46['pragmatics']['total_battery_cost'], 2)} for pragmatics. "
        f"The marginal cost of expert statistical guidance is "
        f"{fmt_cents(o46['pragmatics']['marginal_cost_per_query'])} per query."
    )
    lines.append("")
    lines.append(f"*Pricing source: {PRICING_SOURCE}*")
    lines.append(f"*Generated: {timestamp}*")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    base = Path(__file__).parent.parent.parent

    overhead_path = base / "results/v2_redo/stage1/analysis/overhead_analysis.json"
    stats_path = base / "results/v2_redo/stage2/analysis/aggregate_statistics.json"
    output_dir = base / "results/v2_redo/stage1/analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading overhead analysis...")
    overhead = load_json(overhead_path)

    print("Loading aggregate statistics...")
    stats = load_json(stats_path)
    cqs_means = {
        cond: sum(scores.values()) / len(scores)
        for cond, scores in stats["per_query_cqs"].items()
    }
    print(f"  CQS means: {', '.join(f'{c}={v:.4f}' for c, v in cqs_means.items())}")

    print("Computing costs...")
    costs = compute_costs(overhead, cqs_means, n_queries=39)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # JSON output
    json_out = {
        "metadata": {
            "generated": timestamp,
            "script": "src/eval/cost_analysis.py",
            "pricing_source": PRICING_SOURCE,
            "pricing_url": PRICING_URL,
            "pricing_retrieved": PRICING_RETRIEVED,
            "methodology": "cost = (mean_input_tokens × input_rate) + (mean_output_tokens × output_rate)",
            "n_queries": 39,
        },
        "pricing": PRICING,
        "costs": {
            mk: {
                "per_condition": {
                    cond: {k: round(v, 8) if isinstance(v, float) else v
                           for k, v in cdata.items()
                           if k != "pricing"}
                    for cond, cdata in mdata["per_condition"].items()
                },
                "pragmatics_vs_rag_effectiveness_ratio": mdata["pragmatics_vs_rag_effectiveness_ratio"],
            }
            for mk, mdata in costs.items()
        },
        "cqs_means": cqs_means,
    }

    json_path = output_dir / "cost_analysis.json"
    with open(json_path, "w") as f:
        json.dump(json_out, f, indent=2, default=str)
    print(f"JSON written to: {json_path}")

    # Markdown output
    md = build_markdown(costs, n_queries=39, timestamp=timestamp)
    md_path = output_dir / "cost_analysis.md"
    with open(md_path, "w") as f:
        f.write(md)
    print(f"Markdown written to: {md_path}")

    # Console summary
    s45 = costs["claude-sonnet-4-5"]["per_condition"]
    ratio = costs["claude-sonnet-4-5"]["pragmatics_vs_rag_effectiveness_ratio"]

    print("\n" + "=" * 70)
    print("COST ANALYSIS SUMMARY (Sonnet 4.5 pricing: $3/$15 per MTok)")
    print("=" * 70)
    for cond in ["control", "rag", "pragmatics"]:
        c = s45[cond]
        print(f"  {cond:<12} ${c['cost_per_query']:.4f}/query  "
              f"${c['total_battery_cost']:.2f} total (39 queries)")
    print()
    print(f"  Marginal cost of pragmatics: ${s45['pragmatics']['marginal_cost_per_query']:.4f}/query")
    print(f"  Marginal cost of RAG:        ${s45['rag']['marginal_cost_per_query']:.4f}/query")
    print()
    print(f"  Cost-effectiveness (CQS per marginal $):")
    print(f"    Pragmatics: {s45['pragmatics']['cqs_per_marginal_dollar']:.2f}")
    print(f"    RAG:        {s45['rag']['cqs_per_marginal_dollar']:.2f}")
    if ratio == ratio:
        print(f"    Pragmatics is {ratio:.1f}x more cost-effective than RAG")
    print("=" * 70)


if __name__ == "__main__":
    main()
