#!/usr/bin/env python3
"""Overhead and efficiency analysis: token and context costs per condition.

Compares resource overhead of control, RAG, and pragmatics conditions from
Stage 1 response records. Uses actual API token counts (input_tokens,
output_tokens) per record — not character estimates.

Inputs:
  results/v2_redo/stage1/control_responses_20260216_055354.jsonl
  results/v2_redo/stage1/rag_responses_20260216_055354.jsonl
  results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl

Output:
  results/v2_redo/stage1/analysis/overhead_analysis.md
  results/v2_redo/stage1/analysis/overhead_analysis.json

Usage: python -m src.eval.overhead_analysis
"""

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────

STAGE1_FILES = {
    "control":    "results/v2_redo/stage1/control_responses_20260216_055354.jsonl",
    "rag":        "results/v2_redo/stage1/rag_responses_20260216_055354.jsonl",
    "pragmatics": "results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl",
}

OUTPUT_DIR = "results/v2_redo/stage1/analysis"


# ── Statistics helpers ────────────────────────────────────────────────────────

def mean(vals):
    return sum(vals) / len(vals) if vals else float("nan")


def median(vals):
    if not vals:
        return float("nan")
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        return float(s[n // 2])
    return float((s[n // 2 - 1] + s[n // 2]) / 2)


def stddev(vals):
    if len(vals) < 2:
        return float("nan")
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def percentile(vals, p):
    if not vals:
        return float("nan")
    s = sorted(vals)
    idx = (len(s) - 1) * p / 100
    lo, hi = int(idx), math.ceil(idx)
    if lo == hi:
        return float(s[lo])
    return float(s[lo] * (hi - idx) + s[hi] * (idx - lo))


def summarize(vals, label=""):
    return {
        "n": len(vals),
        "mean": round(mean(vals), 1),
        "median": round(median(vals), 1),
        "sd": round(stddev(vals), 1),
        "min": round(min(vals), 1) if vals else float("nan"),
        "max": round(max(vals), 1) if vals else float("nan"),
        "p25": round(percentile(vals, 25), 1),
        "p75": round(percentile(vals, 75), 1),
    }


# ── Data loading ──────────────────────────────────────────────────────────────

def load_records(path: Path) -> list:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


# ── Per-condition extraction ──────────────────────────────────────────────────

def analyze_condition(records: list, cond: str) -> dict:
    """Extract overhead metrics from a condition's Stage 1 records."""
    input_tokens = []
    output_tokens = []
    total_tokens = []
    response_text_chars = []
    tool_call_counts = []

    # Condition-specific
    rag_retrieval_chars = []
    prag_guidance_chars = []
    prag_item_counts = []

    for rec in records:
        it = rec.get("input_tokens", 0) or 0
        ot = rec.get("output_tokens", 0) or 0
        input_tokens.append(it)
        output_tokens.append(ot)
        total_tokens.append(it + ot)

        rt = rec.get("response_text", "") or ""
        response_text_chars.append(len(rt))

        tcs = rec.get("tool_calls", []) or []
        tool_call_counts.append(len(tcs))

        if cond == "rag":
            rc = rec.get("retrieval_context_chars", 0) or 0
            rag_retrieval_chars.append(rc)

        if cond == "pragmatics":
            # Total chars in get_methodology_guidance results
            guidance_total = sum(
                len(str(tc.get("result", "")))
                for tc in tcs
                if tc.get("tool_name") == "get_methodology_guidance"
            )
            prag_guidance_chars.append(guidance_total)

            # Number of context IDs returned
            pr = rec.get("pragmatics_returned", []) or []
            prag_item_counts.append(len(pr))

    result = {
        "n_records": len(records),
        "total_file_bytes": None,  # filled below
        "input_tokens": summarize(input_tokens),
        "output_tokens": summarize(output_tokens),
        "total_tokens": summarize(total_tokens),
        "response_text_chars": summarize(response_text_chars),
        "tool_call_counts": summarize(tool_call_counts),
        "tool_call_distribution": {str(k): tool_call_counts.count(k) for k in sorted(set(tool_call_counts))},
    }

    if cond == "rag":
        result["retrieval_context_chars"] = summarize(rag_retrieval_chars)
        result["total_retrieval_chars"] = sum(rag_retrieval_chars)

    if cond == "pragmatics":
        result["guidance_response_chars"] = summarize(prag_guidance_chars)
        result["pragmatics_item_counts"] = summarize(prag_item_counts)
        result["total_guidance_chars"] = sum(prag_guidance_chars)

    return result


# ── Overhead ratios ───────────────────────────────────────────────────────────

def compute_overhead_ratios(stats: dict) -> dict:
    """Compute overhead ratios vs control baseline."""
    ctrl_input = stats["control"]["input_tokens"]["mean"]
    ctrl_total = stats["control"]["total_tokens"]["mean"]

    ratios = {}
    for cond in ["rag", "pragmatics"]:
        cond_input = stats[cond]["input_tokens"]["mean"]
        cond_total = stats[cond]["total_tokens"]["mean"]
        ratios[cond] = {
            "input_overhead_ratio": round((cond_input - ctrl_input) / ctrl_input, 3),
            "input_overhead_pct": round((cond_input - ctrl_input) / ctrl_input * 100, 1),
            "total_overhead_ratio": round((cond_total - ctrl_total) / ctrl_total, 3),
            "total_overhead_pct": round((cond_total - ctrl_total) / ctrl_total * 100, 1),
        }
    return ratios


# ── Markdown output ───────────────────────────────────────────────────────────

def fmt_n(v) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "N/A"
    return f"{v:,.0f}"


def fmt_f(v, dp=1) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "N/A"
    return f"{v:,.{dp}f}"


def build_markdown(stats: dict, ratios: dict, file_sizes: dict, timestamp: str) -> str:
    lines = []
    lines.append("# Overhead & Efficiency Analysis")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("**Script:** src/eval/overhead_analysis.py")
    lines.append("**Source:** results/v2_redo/stage1/*_responses_*.jsonl")
    lines.append("")

    # File sizes
    lines.append("## Stage 1 Response File Sizes")
    lines.append("")
    lines.append("| Condition | File | Size (bytes) | Records |")
    lines.append("|-----------|------|-------------|---------|")
    for cond in ["control", "rag", "pragmatics"]:
        sz = file_sizes.get(cond, {})
        lines.append(f"| {cond} | {sz.get('file', '?')} | {fmt_n(sz.get('bytes', 0))} | {stats[cond]['n_records']} |")
    lines.append("")

    # Token summary
    lines.append("## Token Usage Per Query")
    lines.append("")
    lines.append("*Input tokens include system prompt, tool results, and conversation history.*")
    lines.append("")
    lines.append("| Metric | Control | RAG | Pragmatics |")
    lines.append("|--------|---------|-----|------------|")

    for metric_key, label in [
        ("input_tokens", "Input tokens (mean)"),
        ("output_tokens", "Output tokens (mean)"),
        ("total_tokens", "Total tokens (mean)"),
    ]:
        row = [label]
        for cond in ["control", "rag", "pragmatics"]:
            row.append(fmt_n(stats[cond][metric_key]["mean"]))
        lines.append(f"| {' | '.join(row)} |")

    lines.append("")

    # Overhead vs control
    lines.append("## Overhead vs Control Baseline")
    lines.append("")
    lines.append("| Condition | Input Token Overhead | Total Token Overhead |")
    lines.append("|-----------|---------------------|---------------------|")
    for cond in ["rag", "pragmatics"]:
        r = ratios[cond]
        lines.append(
            f"| {cond} | +{r['input_overhead_pct']:.1f}% (+{r['input_overhead_ratio']:.2f}×) | "
            f"+{r['total_overhead_pct']:.1f}% (+{r['total_overhead_ratio']:.2f}×) |"
        )
    lines.append("")

    # Tool calls
    lines.append("## Tool Call Counts Per Query")
    lines.append("")
    lines.append("| Condition | Mean | Median | Min | Max | Distribution |")
    lines.append("|-----------|------|--------|-----|-----|-------------|")
    for cond in ["control", "rag", "pragmatics"]:
        tc = stats[cond]["tool_call_counts"]
        dist = stats[cond]["tool_call_distribution"]
        dist_str = ", ".join(f"{k} calls: {v}" for k, v in sorted(dist.items(), key=lambda x: int(x[0])))
        lines.append(
            f"| {cond} | {fmt_f(tc['mean'])} | {fmt_f(tc['median'])} | "
            f"{fmt_n(tc['min'])} | {fmt_n(tc['max'])} | {dist_str} |"
        )
    lines.append("")

    # RAG-specific
    rag = stats.get("rag", {})
    if "retrieval_context_chars" in rag:
        rc = rag["retrieval_context_chars"]
        total_rc = rag.get("total_retrieval_chars", 0)
        lines.append("## RAG: Retrieved Context Injected Into System Prompt")
        lines.append("")
        lines.append(
            f"| Mean chars/query | Median | Min | Max | Total across {rag['n_records']} queries |"
        )
        lines.append("|-----------------|--------|-----|-----|------------------------------------|")
        lines.append(
            f"| {fmt_n(rc['mean'])} | {fmt_n(rc['median'])} | {fmt_n(rc['min'])} | "
            f"{fmt_n(rc['max'])} | {fmt_n(total_rc)} |"
        )
        lines.append("")
        lines.append(
            "*RAG prepends retrieved chunks (top-5, all-MiniLM-L6-v2) directly into the system prompt — "
            "same context injected regardless of query specificity.*"
        )
        lines.append("")

    # Pragmatics-specific
    prag = stats.get("pragmatics", {})
    if "pragmatics_item_counts" in prag:
        pic = prag["pragmatics_item_counts"]
        gc = prag.get("guidance_response_chars", {})
        total_gc = prag.get("total_guidance_chars", 0)
        lines.append("## Pragmatics: Items Returned Per Query")
        lines.append("")
        lines.append(
            "| Mean items/query | Median | Min | Max | Pack size | Selectivity |"
        )
        lines.append("|-----------------|--------|-----|-----|-----------|------------|")
        pack_size = 36
        selectivity = round(pic["mean"] / pack_size * 100, 1) if pack_size else float("nan")
        lines.append(
            f"| {fmt_f(pic['mean'])} | {fmt_f(pic['median'])} | {fmt_n(pic['min'])} | "
            f"{fmt_n(pic['max'])} | {pack_size} | {selectivity:.1f}% of pack per query |"
        )
        lines.append("")
        lines.append(
            f"Mean `get_methodology_guidance` response: {fmt_n(gc.get('mean', 0))} chars "
            f"(total across {prag['n_records']} queries: {fmt_n(total_gc)} chars)"
        )
        lines.append("")
        lines.append(
            "*Pragmatics delivers only the relevant subset of expert knowledge per query — "
            "not a full index dump. Selectivity means lower noise at the point of decision.*"
        )
        lines.append("")

    # Response text comparison
    lines.append("## Response Text Length (chars)")
    lines.append("")
    lines.append("| Condition | Mean | Median | SD | Min | Max |")
    lines.append("|-----------|------|--------|-----|-----|-----|")
    for cond in ["control", "rag", "pragmatics"]:
        rt = stats[cond]["response_text_chars"]
        lines.append(
            f"| {cond} | {fmt_n(rt['mean'])} | {fmt_n(rt['median'])} | "
            f"{fmt_n(rt['sd'])} | {fmt_n(rt['min'])} | {fmt_n(rt['max'])} |"
        )
    lines.append("")

    # Architecture narrative
    lines.append("## Architecture Comparison")
    lines.append("")
    lines.append("| Property | RAG | Pragmatics |")
    lines.append("|----------|-----|------------|")

    rag_rc_mean = rag.get("retrieval_context_chars", {}).get("mean", 0)
    prag_gc_mean = prag.get("guidance_response_chars", {}).get("mean", 0)
    prag_items_mean = prag.get("pragmatics_item_counts", {}).get("mean", 0)

    lines.append(f"| Context delivery | Full top-5 chunks prepended to system prompt | Selective items via tool response |")
    lines.append(f"| Mean context size | {fmt_n(rag_rc_mean)} chars/query | {fmt_n(prag_gc_mean)} chars/query |")
    lines.append(f"| Items per query | 5 (fixed) | {fmt_f(prag_items_mean)} of 36 ({round(prag_items_mean/36*100,1) if prag_items_mean else '?'}% of pack) |")
    lines.append(f"| Client-side index | Required (FAISS + embeddings) | None (MCP API-served) |")
    lines.append(f"| Pack updates | Requires re-indexing | Replace pack via MCP |")
    lines.append("")

    lines.append(f"*Generated: {timestamp}*")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    base = Path(__file__).parent.parent.parent

    output_dir = base / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}
    file_sizes = {}

    for cond, rel_path in STAGE1_FILES.items():
        path = base / rel_path
        print(f"Loading {cond}: {path.name}")
        records = load_records(path)
        print(f"  {len(records)} records")
        stats[cond] = analyze_condition(records, cond)
        file_sz = os.path.getsize(path)
        stats[cond]["total_file_bytes"] = file_sz
        file_sizes[cond] = {"file": path.name, "bytes": file_sz}

    print("Computing overhead ratios vs control...")
    ratios = compute_overhead_ratios(stats)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Output JSON
    json_out = {
        "metadata": {
            "generated": timestamp,
            "script": "src/eval/overhead_analysis.py",
        },
        "per_condition": stats,
        "overhead_vs_control": ratios,
        "file_sizes": file_sizes,
    }

    json_path = output_dir / "overhead_analysis.json"
    with open(json_path, "w") as f:
        json.dump(json_out, f, indent=2, default=str)
    print(f"JSON written to: {json_path}")

    # Output Markdown
    md = build_markdown(stats, ratios, file_sizes, timestamp)
    md_path = output_dir / "overhead_analysis.md"
    with open(md_path, "w") as f:
        f.write(md)
    print(f"Markdown written to: {md_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("OVERHEAD SUMMARY")
    print("=" * 70)
    for cond in ["control", "rag", "pragmatics"]:
        s = stats[cond]
        print(f"\n[{cond.upper()}] n={s['n_records']}, "
              f"file={file_sizes[cond]['bytes']:,} bytes")
        print(f"  Input tokens:   mean={s['input_tokens']['mean']:,.0f}  "
              f"median={s['input_tokens']['median']:,.0f}")
        print(f"  Output tokens:  mean={s['output_tokens']['mean']:,.0f}")
        print(f"  Tool calls:     mean={s['tool_call_counts']['mean']:.1f}")
        if cond == "rag":
            print(f"  Retrieval chars mean={s['retrieval_context_chars']['mean']:,.0f}")
        if cond == "pragmatics":
            print(f"  Pragmatic items mean={s['pragmatics_item_counts']['mean']:.1f} "
                  f"(of 36 = {s['pragmatics_item_counts']['mean']/36*100:.0f}%)")
            print(f"  Guidance chars  mean={s['guidance_response_chars']['mean']:,.0f}")

    print()
    for cond in ["rag", "pragmatics"]:
        r = ratios[cond]
        print(f"[{cond.upper()} vs CONTROL]  "
              f"input +{r['input_overhead_pct']:.1f}%  "
              f"total +{r['total_overhead_pct']:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
