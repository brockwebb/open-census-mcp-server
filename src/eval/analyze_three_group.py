"""Three-Group Analysis - Control vs RAG vs Pragmatics.

Computes statistical comparisons across three conditions using repeated-measures
methods (Friedman test, Wilcoxon signed-rank post-hoc).

Usage:
    python -m src.eval.analyze_three_group

Outputs to results/rag_ablation/analysis/:
- three_group_comparison.csv
- friedman_tests.csv
- posthoc_pairwise.csv
- rag_vs_control_effects.csv
- fidelity_comparison.csv
- aggregate_report.md
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from datetime import datetime
import yaml

import numpy as np
from scipy import stats


# =============================================================================
# DATA LOADING
# =============================================================================

def load_primary_judge_scores(stage2_dir: Path, valid_run_ids: List[str]) -> List[Dict]:
    """Load primary eval judge scores (control and pragmatics)."""
    records = []
    for jsonl_file in sorted(stage2_dir.glob('judge_scores_*.jsonl')):
        # Extract run_id from filename (e.g., judge_scores_20260208_155317.jsonl)
        run_id = jsonl_file.stem.replace('judge_scores_', '')

        if run_id not in valid_run_ids:
            continue

        with open(jsonl_file) as f:
            for line in f:
                record = json.loads(line)
                if record.get('parse_success', False):
                    records.append(record)

    return records


def load_rag_judge_scores(rag_dir: Path) -> List[Dict]:
    """Load RAG vs Control judge scores."""
    records = []
    for jsonl_file in sorted(rag_dir.glob('judge_scores_*.jsonl')):
        with open(jsonl_file) as f:
            for line in f:
                record = json.loads(line)
                if record.get('parse_success', False):
                    records.append(record)
    return records


def load_fidelity_results(stage3_dir: Path) -> Dict[str, Any]:
    """Load fidelity results from most recent file."""
    fidelity_files = sorted(stage3_dir.glob('fidelity_*.jsonl'))
    if not fidelity_files:
        return {'total_claims': 0, 'matched': 0, 'auditable': 0}

    # Load most recent
    records = []
    with open(fidelity_files[-1]) as f:
        for line in f:
            records.append(json.loads(line))

    # Aggregate treatment fidelity and control auditability
    total_claims = 0
    matched_claims = 0
    calc_correct = 0

    control_auditable = 0
    control_total = 0

    for rec in records:
        # Treatment fidelity
        tf_summary = rec.get('treatment_fidelity', {}).get('summary', {})
        total_claims += tf_summary.get('total_claims', 0)
        matched_claims += tf_summary.get('matched', 0)
        calc_correct += tf_summary.get('calculation_correct', 0)

        # Control auditability
        ca_summary = rec.get('control_auditability', {}).get('summary', {})
        control_total += ca_summary.get('total_claims', 0)
        control_auditable += ca_summary.get('auditable', 0)

    fidelity_pct = (matched_claims + calc_correct) / total_claims * 100 if total_claims > 0 else 0
    auditability_pct = control_auditable / control_total * 100 if control_total > 0 else 0

    return {
        'total_claims': total_claims,
        'matched': matched_claims,
        'calc_correct': calc_correct,
        'fidelity_pct': fidelity_pct,
        'control_total_claims': control_total,
        'control_auditable': control_auditable,
        'control_auditability_pct': auditability_pct
    }


# =============================================================================
# QUERY-LEVEL MEAN COMPUTATION
# =============================================================================

def extract_scores_from_record(record: Dict, dimensions: List[str]) -> Dict[str, Tuple[Dict[str, float], Dict[str, float]]]:
    """Extract dimension scores for both responses from a judge record.

    Returns:
        {dimension: (response_a_scores, response_b_scores)}
    """
    scores_a = {}
    scores_b = {}

    for dim in dimensions:
        # Get scores for response A
        if f'scores_response_a' in record and dim in record['scores_response_a']:
            scores_a[dim] = record['scores_response_a'][dim].get('score', np.nan)

        # Get scores for response B
        if f'scores_response_b' in record and dim in record['scores_response_b']:
            scores_b[dim] = record['scores_response_b'][dim].get('score', np.nan)

    return scores_a, scores_b


def compute_query_means_three_group(
    primary_records: List[Dict],
    rag_records: List[Dict],
    dimensions: List[str]
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Compute query-level means for all three conditions.

    Returns:
        {query_id: {dimension: {'control': mean, 'rag': mean, 'pragmatics': mean}}}
    """
    # Collect all scores per query/dimension/condition
    query_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # Process primary eval records (control and pragmatics)
    for rec in primary_records:
        query_id = rec['query_id']
        scores_a, scores_b = extract_scores_from_record(rec, dimensions)

        # Map A/B to control/treatment using labels
        label_a = rec['response_a_label']
        label_b = rec['response_b_label']

        for dim in dimensions:
            if dim in scores_a and not np.isnan(scores_a[dim]):
                cond = 'pragmatics' if label_a == 'treatment' else 'control'
                query_scores[query_id][dim][cond].append(scores_a[dim])

            if dim in scores_b and not np.isnan(scores_b[dim]):
                cond = 'pragmatics' if label_b == 'treatment' else 'control'
                query_scores[query_id][dim][cond].append(scores_b[dim])

    # Process RAG records (control and rag)
    for rec in rag_records:
        query_id = rec['query_id']
        scores_a, scores_b = extract_scores_from_record(rec, dimensions)

        label_a = rec['response_a_label']
        label_b = rec['response_b_label']

        for dim in dimensions:
            if dim in scores_a and not np.isnan(scores_a[dim]):
                cond = 'rag' if label_a == 'treatment' else 'control'
                query_scores[query_id][dim][cond].append(scores_a[dim])

            if dim in scores_b and not np.isnan(scores_b[dim]):
                cond = 'rag' if label_b == 'treatment' else 'control'
                query_scores[query_id][dim][cond].append(scores_b[dim])

    # Compute means
    query_means = {}
    for query_id in query_scores:
        query_means[query_id] = {}
        for dim in query_scores[query_id]:
            query_means[query_id][dim] = {}
            for cond in query_scores[query_id][dim]:
                scores = query_scores[query_id][dim][cond]
                query_means[query_id][dim][cond] = np.mean(scores) if scores else np.nan

    return query_means


def add_composite_dimension(query_means: Dict) -> None:
    """Add composite score (mean of D1-D5) to query_means in-place."""
    for query_id in query_means:
        composite_scores = {}

        for cond in ['control', 'rag', 'pragmatics']:
            dim_scores = []
            for dim in ['D1', 'D2', 'D3', 'D4', 'D5']:
                if dim in query_means[query_id]:
                    score = query_means[query_id][dim].get(cond, np.nan)
                    if not np.isnan(score):
                        dim_scores.append(score)

            composite_scores[cond] = np.mean(dim_scores) if dim_scores else np.nan

        query_means[query_id]['composite'] = composite_scores


# =============================================================================
# STATISTICAL TESTS
# =============================================================================

def friedman_test_per_dimension(query_means: Dict, dimensions: List[str]) -> Dict:
    """Run Friedman test per dimension across 3 conditions."""
    results = {}

    for dim in dimensions:
        control_scores = []
        rag_scores = []
        prag_scores = []

        for qid in sorted(query_means.keys()):
            if dim in query_means[qid]:
                c = query_means[qid][dim].get('control', np.nan)
                r = query_means[qid][dim].get('rag', np.nan)
                p = query_means[qid][dim].get('pragmatics', np.nan)

                # Only include if all three conditions have data
                if not (np.isnan(c) or np.isnan(r) or np.isnan(p)):
                    control_scores.append(c)
                    rag_scores.append(r)
                    prag_scores.append(p)

        if len(control_scores) >= 10:
            # Friedman test
            chi2, p_value = stats.friedmanchisquare(control_scores, rag_scores, prag_scores)

            results[dim] = {
                'chi2': chi2,
                'p_value': p_value,
                'df': 2,
                'n_queries': len(control_scores),
                'control_mean': np.mean(control_scores),
                'control_sd': np.std(control_scores, ddof=1),
                'rag_mean': np.mean(rag_scores),
                'rag_sd': np.std(rag_scores, ddof=1),
                'pragmatics_mean': np.mean(prag_scores),
                'pragmatics_sd': np.std(prag_scores, ddof=1)
            }

    return results


def posthoc_pairwise_wilcoxon(query_means: Dict, dimensions: List[str]) -> List[Dict]:
    """Wilcoxon signed-rank post-hoc with Bonferroni correction."""
    comparisons = [
        ('rag', 'control', 'RAG vs Control'),
        ('pragmatics', 'rag', 'Pragmatics vs RAG'),
        ('pragmatics', 'control', 'Pragmatics vs Control')
    ]

    BONFERRONI_ALPHA = 0.05 / 3  # 0.0167
    results = []

    for cond_a, cond_b, label in comparisons:
        for dim in dimensions:
            scores_a = []
            scores_b = []

            for qid in sorted(query_means.keys()):
                if dim in query_means[qid]:
                    a = query_means[qid][dim].get(cond_a, np.nan)
                    b = query_means[qid][dim].get(cond_b, np.nan)

                    if not (np.isnan(a) or np.isnan(b)):
                        scores_a.append(a)
                        scores_b.append(b)

            if len(scores_a) >= 10:
                # Wilcoxon signed-rank
                stat, p_value = stats.wilcoxon(scores_a, scores_b)

                # Cohen's d (paired)
                diffs = np.array(scores_a) - np.array(scores_b)
                cohens_d = np.mean(diffs) / np.std(diffs, ddof=1) if np.std(diffs, ddof=1) > 0 else 0

                # Bootstrap CI on effect size
                ci_lower, ci_upper = bootstrap_cohens_d_ci(scores_a, scores_b, n_bootstrap=1000, seed=42)

                results.append({
                    'dimension': dim,
                    'comparison': label,
                    'n': len(scores_a),
                    'mean_a': np.mean(scores_a),
                    'mean_b': np.mean(scores_b),
                    'cohens_d': cohens_d,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'wilcoxon_stat': stat,
                    'wilcoxon_p': p_value,
                    'significant': 'Yes' if p_value < BONFERRONI_ALPHA else 'No'
                })

    return results


def bootstrap_cohens_d_ci(x: np.ndarray, y: np.ndarray, n_bootstrap: int = 1000, seed: int = 42, alpha: float = 0.05) -> Tuple[float, float]:
    """Bootstrap confidence interval for paired Cohen's d."""
    np.random.seed(seed)
    x = np.array(x)
    y = np.array(y)
    n = len(x)

    bootstrap_d = []
    for _ in range(n_bootstrap):
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        diffs = x_boot - y_boot
        d = np.mean(diffs) / np.std(diffs, ddof=1) if np.std(diffs, ddof=1) > 0 else 0
        bootstrap_d.append(d)

    ci_lower = np.percentile(bootstrap_d, alpha/2 * 100)
    ci_upper = np.percentile(bootstrap_d, (1 - alpha/2) * 100)

    return ci_lower, ci_upper


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def write_three_group_comparison(friedman_results: Dict, output_dir: Path):
    """Write dimension means and SDs per condition."""
    csv_path = output_dir / 'three_group_comparison.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'dimension', 'control_mean', 'control_sd', 'rag_mean', 'rag_sd',
            'pragmatics_mean', 'pragmatics_sd', 'friedman_chi2', 'friedman_p', 'n_queries'
        ])
        writer.writeheader()

        for dim in sorted(friedman_results.keys()):
            stats_dict = friedman_results[dim]
            writer.writerow({
                'dimension': dim,
                'control_mean': f"{stats_dict['control_mean']:.2f}",
                'control_sd': f"{stats_dict['control_sd']:.2f}",
                'rag_mean': f"{stats_dict['rag_mean']:.2f}",
                'rag_sd': f"{stats_dict['rag_sd']:.2f}",
                'pragmatics_mean': f"{stats_dict['pragmatics_mean']:.2f}",
                'pragmatics_sd': f"{stats_dict['pragmatics_sd']:.2f}",
                'friedman_chi2': f"{stats_dict['chi2']:.3f}",
                'friedman_p': f"{stats_dict['p_value']:.4f}",
                'n_queries': stats_dict['n_queries']
            })

    print(f"  ✅ {csv_path}")


def write_posthoc_pairwise(pairwise_results: List[Dict], output_dir: Path):
    """Write pairwise post-hoc comparisons."""
    csv_path = output_dir / 'posthoc_pairwise.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'dimension', 'comparison', 'cohens_d', 'ci_lower', 'ci_upper',
            'wilcoxon_stat', 'wilcoxon_p', 'significant', 'n'
        ])
        writer.writeheader()

        for result in pairwise_results:
            writer.writerow({
                'dimension': result['dimension'],
                'comparison': result['comparison'],
                'cohens_d': f"{result['cohens_d']:.3f}",
                'ci_lower': f"{result['ci_lower']:.3f}",
                'ci_upper': f"{result['ci_upper']:.3f}",
                'wilcoxon_stat': f"{result['wilcoxon_stat']:.1f}",
                'wilcoxon_p': f"{result['wilcoxon_p']:.4f}",
                'significant': result['significant'],
                'n': result['n']
            })

    print(f"  ✅ {csv_path}")


def write_fidelity_comparison(
    primary_fidelity: Dict,
    rag_fidelity: Dict,
    output_dir: Path
):
    """Write fidelity/auditability comparison across all 3 conditions."""
    csv_path = output_dir / 'fidelity_comparison.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'metric', 'control', 'rag', 'pragmatics'
        ])
        writer.writeheader()

        # Auditability (control has same value for all conditions in this metric)
        writer.writerow({
            'metric': 'control_auditability_pct',
            'control': f"{primary_fidelity.get('control_auditability_pct', 0):.1f}%",
            'rag': f"{rag_fidelity.get('control_auditability_pct', 0):.1f}%",
            'pragmatics': f"{primary_fidelity.get('control_auditability_pct', 0):.1f}%"
        })

        # Fidelity (treatment fidelity for RAG and pragmatics)
        writer.writerow({
            'metric': 'treatment_fidelity_pct',
            'control': 'N/A',
            'rag': f"{rag_fidelity.get('fidelity_pct', 0):.1f}%",
            'pragmatics': f"{primary_fidelity.get('fidelity_pct', 0):.1f}%"
        })

        # Total claims
        writer.writerow({
            'metric': 'total_claims',
            'control': f"{primary_fidelity.get('control_total_claims', 0)}",
            'rag': f"{rag_fidelity.get('total_claims', 0)}",
            'pragmatics': f"{primary_fidelity.get('total_claims', 0)}"
        })

    print(f"  ✅ {csv_path}")


def generate_aggregate_report(
    friedman_results: Dict,
    pairwise_results: List[Dict],
    primary_fidelity: Dict,
    rag_fidelity: Dict,
    output_dir: Path
):
    """Generate markdown report with publication-ready tables."""
    md_path = output_dir / 'aggregate_report.md'

    with open(md_path, 'w') as f:
        f.write("# Three-Group Analysis - RAG Ablation\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Experimental Design\n\n")
        f.write("**Conditions:**\n")
        f.write("1. **Control** - Bare LLM (no tools, no retrieval)\n")
        f.write("2. **RAG** - Retrieval-augmented prompting from source documents\n")
        f.write("3. **Pragmatics** - Structured pragmatic context via MCP tools\n\n")

        f.write("**Statistical Methods:**\n")
        f.write("- Friedman test (repeated-measures, ordinal) per dimension\n")
        f.write("- Wilcoxon signed-rank post-hoc with Bonferroni correction (α = 0.0167)\n")
        f.write("- Unit of analysis: query-level means (n=39)\n")
        f.write("- Dimensions: D1-D5 + composite\n\n")

        f.write("---\n\n")
        f.write("## Table 1: Three-Group CQS Comparison\n\n")
        f.write("| Dimension | Control | RAG | Pragmatics | χ² | p |\n")
        f.write("|-----------|---------|-----|------------|-------|-------|\n")

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'composite']:
            if dim in friedman_results:
                r = friedman_results[dim]
                sig = "*" if r['p_value'] < 0.05 else ""
                f.write(f"| **{dim}** | {r['control_mean']:.2f} ± {r['control_sd']:.2f} | "
                       f"{r['rag_mean']:.2f} ± {r['rag_sd']:.2f} | "
                       f"{r['pragmatics_mean']:.2f} ± {r['pragmatics_sd']:.2f} | "
                       f"{r['chi2']:.2f} | {r['p_value']:.4f}{sig} |\n")

        f.write("\n*p < 0.05\n\n")

        f.write("---\n\n")
        f.write("## Table 2: Pairwise Effect Sizes (Cohen's d)\n\n")
        f.write("| Dimension | RAG vs Control | Pragmatics vs RAG | Pragmatics vs Control |\n")
        f.write("|-----------|----------------|-------------------|----------------------|\n")

        # Reorganize pairwise results by dimension
        by_dim = defaultdict(dict)
        for r in pairwise_results:
            by_dim[r['dimension']][r['comparison']] = r

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'composite']:
            if dim in by_dim:
                rc = by_dim[dim].get('RAG vs Control', {})
                pr = by_dim[dim].get('Pragmatics vs RAG', {})
                pc = by_dim[dim].get('Pragmatics vs Control', {})

                def format_effect(r):
                    if not r:
                        return "—"
                    sig = "**" if r.get('significant') == 'Yes' else ""
                    return f"{sig}{r['cohens_d']:.2f}{sig} ({r['ci_lower']:.2f}, {r['ci_upper']:.2f})"

                f.write(f"| **{dim}** | {format_effect(rc)} | {format_effect(pr)} | {format_effect(pc)} |\n")

        f.write("\n**Bold** = significant at Bonferroni-corrected α = 0.0167\n\n")

        f.write("---\n\n")
        f.write("## Table 3: Fidelity & Auditability\n\n")
        f.write("| Metric | Control | RAG | Pragmatics |\n")
        f.write("|--------|---------|-----|------------|\n")

        f.write(f"| Treatment Fidelity | N/A | "
               f"{rag_fidelity.get('fidelity_pct', 0):.1f}% | "
               f"{primary_fidelity.get('fidelity_pct', 0):.1f}% |\n")

        f.write(f"| Control Auditability | "
               f"{primary_fidelity.get('control_auditability_pct', 0):.1f}% | "
               f"{rag_fidelity.get('control_auditability_pct', 0):.1f}% | "
               f"{primary_fidelity.get('control_auditability_pct', 0):.1f}% |\n")

        f.write(f"| Total Claims | "
               f"{primary_fidelity.get('control_total_claims', 0)} | "
               f"{rag_fidelity.get('total_claims', 0)} | "
               f"{primary_fidelity.get('total_claims', 0)} |\n")

        f.write("\n---\n\n")
        f.write("## Interpretation Notes\n\n")
        f.write("- Fidelity measures whether treatment responses accurately reflect their source data\n")
        f.write("- Auditability measures whether control responses include specific enough claims for external verification\n")
        f.write("- Statistical significance does not imply practical significance\n")
        f.write("- Effect sizes should be interpreted with domain context\n\n")

    print(f"  ✅ {md_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Three-Group Analysis - RAG Ablation')
    args = parser.parse_args()

    print("="*70)
    print("THREE-GROUP ANALYSIS - RAG ABLATION")
    print("="*70)

    # Load configs
    with open('src/eval/judge_config.yaml') as f:
        primary_config = yaml.safe_load(f)

    dimensions = ['D1', 'D2', 'D3', 'D4', 'D5', 'composite']

    # Load data
    print("\n📊 Loading data...")

    # Primary eval (control and pragmatics) - use all available judge score files
    primary_records = []
    stage2_dir = Path('results/stage2')
    for jsonl_file in sorted(stage2_dir.glob('judge_scores_*.jsonl')):
        with open(jsonl_file) as f:
            for line in f:
                rec = json.loads(line)
                if rec.get('parse_success', False):
                    primary_records.append(rec)
    print(f"  ✅ Loaded {len(primary_records)} primary eval records (control & pragmatics)")

    # RAG ablation (control and RAG)
    rag_records = load_rag_judge_scores(Path('results/rag_ablation/stage2'))
    print(f"  ✅ Loaded {len(rag_records)} RAG ablation records")

    # Fidelity results
    primary_fidelity = load_fidelity_results(Path('results/stage3'))
    rag_fidelity = load_fidelity_results(Path('results/rag_ablation/stage3'))
    print(f"  ✅ Loaded fidelity results")

    # Compute query-level means
    print("\n📈 Computing query-level means...")
    query_means = compute_query_means_three_group(
        primary_records,
        rag_records,
        ['D1', 'D2', 'D3', 'D4', 'D5']
    )
    add_composite_dimension(query_means)
    print(f"  ✅ Computed means for {len(query_means)} queries")

    # Run Friedman tests
    print("\n📊 Running Friedman tests...")
    friedman_results = friedman_test_per_dimension(query_means, dimensions)
    print(f"  ✅ Completed Friedman tests for {len(friedman_results)} dimensions")

    # Run post-hoc pairwise comparisons
    print("\n📊 Running Wilcoxon post-hoc tests...")
    pairwise_results = posthoc_pairwise_wilcoxon(query_means, dimensions)
    print(f"  ✅ Completed {len(pairwise_results)} pairwise comparisons")

    # Write outputs
    output_dir = Path('results/rag_ablation/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n💾 Writing outputs...")
    write_three_group_comparison(friedman_results, output_dir)
    write_posthoc_pairwise(pairwise_results, output_dir)
    write_fidelity_comparison(primary_fidelity, rag_fidelity, output_dir)
    generate_aggregate_report(friedman_results, pairwise_results, primary_fidelity, rag_fidelity, output_dir)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nOutputs in {output_dir}/")

    # Print quick summary
    print("\nQuick Summary:")
    print(f"  Queries analyzed: {len(query_means)}")
    print(f"  Dimensions: {len(dimensions)}")
    print(f"  Friedman significant (p<0.05): {sum(1 for r in friedman_results.values() if r['p_value'] < 0.05)}/{len(friedman_results)}")
    print(f"  Post-hoc significant (Bonferroni): {sum(1 for r in pairwise_results if r['significant'] == 'Yes')}/{len(pairwise_results)}")

    return 0


if __name__ == '__main__':
    exit(main())
