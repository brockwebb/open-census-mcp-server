"""Three-Group Analysis - Control vs RAG vs Pragmatics.

Computes statistical comparisons across three conditions using repeated-measures
methods (Friedman test, Wilcoxon signed-rank post-hoc).

Usage:
    python -m eval.analyze_three_group [--config PATH]

Outputs to results/rag_ablation/analysis/:
- three_group_comparison.csv
- friedman_tests.csv
- posthoc_pairwise.csv
- rag_vs_control_effects.csv
- rag_fidelity.csv
- aggregate_report.md
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime
import yaml

import numpy as np
from scipy import stats


# =============================================================================
# DATA LOADING
# =============================================================================

def load_existing_analysis(analysis_dir: Path) -> Dict[str, Any]:
    """Load existing pragmatics vs control analysis."""
    # Load CSVs from results/stage2/analysis/
    effect_sizes = {}
    with open(analysis_dir / 'effect_sizes.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['vendor'] == 'pooled':
                effect_sizes[row['dimension']] = {
                    'cohens_d': float(row['cohens_d']),
                    'mean_treatment': float(row['mean_treatment']),
                    'mean_control': float(row['mean_control']),
                    'n': int(row['n'])
                }

    fidelity = {}
    with open(analysis_dir / 'fidelity_summary.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric = row['metric']
            if 'Auditable' in metric or 'Fidelity' in metric:
                fidelity[metric] = {
                    'treatment': row['treatment_value'],
                    'control': row['control_value']
                }

    return {
        'effect_sizes': effect_sizes,
        'fidelity': fidelity
    }


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


def load_rag_fidelity(rag_stage3: Path) -> Dict:
    """Load RAG fidelity results."""
    fidelity_file = rag_stage3 / 'fidelity_results.jsonl'
    if not fidelity_file.exists():
        return {}

    # Load fidelity records
    records = []
    with open(fidelity_file) as f:
        for line in f:
            records.append(json.loads(line))

    # Compute fidelity metrics (same logic as fidelity_check.py)
    # TODO: Implement fidelity aggregation
    return {}


# =============================================================================
# THREE-GROUP COMPARISONS
# =============================================================================

def compute_dimension_means(records: List[Dict], dimensions: List[str]) -> Dict:
    """Compute query-level means per dimension for each condition.

    Returns:
        {query_id: {dim: {condition: mean}}}
    """
    query_condition_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for record in records:
        query_id = record['query_id']
        # Determine which response is which condition
        # This depends on response_a_label and response_b_label
        # TODO: Implement score extraction per condition
        pass

    # TODO: Aggregate to query-level means
    return {}


def friedman_test_per_dimension(query_means: Dict, dimensions: List[str]) -> Dict:
    """Run Friedman test per dimension across 3 conditions.

    Args:
        query_means: {query_id: {dim: {condition: mean}}}
        dimensions: List of dimension IDs

    Returns:
        {dimension: {'chi2': ..., 'p_value': ..., 'df': ...}}
    """
    results = {}

    for dim in dimensions:
        # Extract scores for this dimension across all queries
        control_scores = []
        rag_scores = []
        prag_scores = []

        for qid in query_means:
            if dim in query_means[qid]:
                control_scores.append(query_means[qid][dim].get('control', np.nan))
                rag_scores.append(query_means[qid][dim].get('rag', np.nan))
                prag_scores.append(query_means[qid][dim].get('pragmatics', np.nan))

        # Run Friedman test (repeated-measures, ordinal)
        # Unit: query (n=39)
        data = np.array([control_scores, rag_scores, prag_scores]).T
        chi2, p = stats.friedmanchisquare(*data.T)

        results[dim] = {
            'chi2': chi2,
            'p_value': p,
            'df': 2,  # k-1 where k=3 conditions
            'n_queries': len([x for x in control_scores if not np.isnan(x)])
        }

    return results


def posthoc_pairwise_wilcoxon(query_means: Dict, dimensions: List[str]) -> List[Dict]:
    """Wilcoxon signed-rank post-hoc with Bonferroni correction.

    Three pairwise comparisons:
    - RAG vs Control
    - Pragmatics vs RAG
    - Pragmatics vs Control

    Returns list of comparison results.
    """
    comparisons = [
        ('rag', 'control', 'RAG vs Control'),
        ('pragmatics', 'rag', 'Pragmatics vs RAG'),
        ('pragmatics', 'control', 'Pragmatics vs Control')
    ]

    results = []

    for cond_a, cond_b, label in comparisons:
        for dim in dimensions:
            # Extract paired scores
            scores_a = []
            scores_b = []

            for qid in query_means:
                if dim in query_means[qid]:
                    a = query_means[qid][dim].get(cond_a)
                    b = query_means[qid][dim].get(cond_b)
                    if a is not None and b is not None:
                        scores_a.append(a)
                        scores_b.append(b)

            if len(scores_a) >= 10:
                # Wilcoxon signed-rank
                stat, p_raw = stats.wilcoxon(scores_a, scores_b)
                p_bonf = min(p_raw * 3, 1.0)  # Bonferroni correction for 3 comparisons

                # Cohen's d (paired)
                diffs = np.array(scores_a) - np.array(scores_b)
                d = np.mean(diffs) / np.std(diffs, ddof=1) if np.std(diffs, ddof=1) > 0 else 0

                results.append({
                    'comparison': label,
                    'dimension': dim,
                    'n': len(scores_a),
                    'wilcoxon_stat': stat,
                    'p_raw': p_raw,
                    'p_bonferroni': p_bonf,
                    'cohens_d': d,
                    'mean_a': np.mean(scores_a),
                    'mean_b': np.mean(scores_b)
                })

    return results


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def write_three_group_comparison(query_means: Dict, dimensions: List[str], output_dir: Path):
    """Write dimension means per condition."""
    csv_path = output_dir / 'three_group_comparison.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dimension', 'control_mean', 'rag_mean', 'pragmatics_mean', 'n_queries'])
        writer.writeheader()

        for dim in dimensions:
            # TODO: Compute means
            pass

    print(f"  ✅ {csv_path}")


def write_friedman_tests(friedman_results: Dict, output_dir: Path):
    """Write Friedman test results."""
    csv_path = output_dir / 'friedman_tests.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dimension', 'chi2', 'df', 'p_value', 'n_queries', 'interpretation'])
        writer.writeheader()

        for dim, stats in friedman_results.items():
            writer.writerow({
                'dimension': dim,
                'chi2': f"{stats['chi2']:.3f}",
                'df': stats['df'],
                'p_value': f"{stats['p_value']:.4f}",
                'n_queries': stats['n_queries'],
                'interpretation': 'Significant' if stats['p_value'] < 0.05 else 'Not significant'
            })

    print(f"  ✅ {csv_path}")


def write_posthoc_pairwise(pairwise_results: List[Dict], output_dir: Path):
    """Write pairwise post-hoc comparisons."""
    csv_path = output_dir / 'posthoc_pairwise.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'comparison', 'dimension', 'n', 'mean_a', 'mean_b',
            'cohens_d', 'wilcoxon_stat', 'p_raw', 'p_bonferroni', 'significant'
        ])
        writer.writeheader()

        for result in pairwise_results:
            writer.writerow({
                'comparison': result['comparison'],
                'dimension': result['dimension'],
                'n': result['n'],
                'mean_a': f"{result['mean_a']:.2f}",
                'mean_b': f"{result['mean_b']:.2f}",
                'cohens_d': f"{result['cohens_d']:.3f}",
                'wilcoxon_stat': f"{result['wilcoxon_stat']:.1f}",
                'p_raw': f"{result['p_raw']:.4f}",
                'p_bonferroni': f"{result['p_bonferroni']:.4f}",
                'significant': 'Yes' if result['p_bonferroni'] < 0.05 else 'No'
            })

    print(f"  ✅ {csv_path}")


def generate_aggregate_report(output_dir: Path):
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
        f.write("- Wilcoxon signed-rank post-hoc with Bonferroni correction\n")
        f.write("- Unit of analysis: query-level means (n=39)\n\n")
        f.write("## Results\n\n")
        f.write("TODO: Insert results tables\n\n")

    print(f"  ✅ {md_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Three-Group Analysis - RAG Ablation')
    parser.add_argument('--config', default='src/eval/judge_config.yaml',
                       help='Path to judge config YAML')

    args = parser.parse_args()

    print("="*70)
    print("THREE-GROUP ANALYSIS - RAG ABLATION")
    print("="*70)

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    dimensions = ['D1', 'D2', 'D3', 'D4', 'D5']  # Exclude D6 per DEC-4B-023

    # Load data
    print("\n📊 Loading data...")
    existing = load_existing_analysis(Path('results/stage2/analysis'))
    print(f"  ✅ Loaded existing pragmatics vs control analysis")

    rag_records = load_rag_judge_scores(Path('results/rag_ablation/stage2'))
    print(f"  ✅ Loaded {len(rag_records)} RAG judge records")

    rag_fidelity = load_rag_fidelity(Path('results/rag_ablation/stage3'))
    print(f"  ✅ Loaded RAG fidelity results")

    # Compute statistics
    print("\n📈 Computing statistics...")
    # TODO: Implement full analysis pipeline

    # Write outputs
    output_dir = Path('results/rag_ablation/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n💾 Writing outputs...")
    # TODO: Write all CSV files and report

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nOutputs in {output_dir}/")

    return 0


if __name__ == '__main__':
    exit(main())
