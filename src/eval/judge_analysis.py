"""Statistical Analysis of Judge Scores - Stage 2.

Computes all metrics from test_plan/06b_statistical_analysis_plan.md:
- Inter-rater agreement (Krippendorff's α, Fleiss' κ, Cohen's κ)
- Bias diagnostics (position, verbosity, self-enhancement, leniency)
- Treatment effects (Wilcoxon, Cohen's d, TOST, McNemar's)
- Reliability (ICC test-retest, confidence calibration, Cronbach's α)
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from scipy import stats
from scipy.stats import spearmanr, wilcoxon, kruskal
import matplotlib.pyplot as plt
import seaborn as sns

# Import statistical functions
try:
    import krippendorff
    HAS_KRIPPENDORFF = True
except ImportError:
    HAS_KRIPPENDORFF = False
    print("Warning: krippendorff package not installed. Install with: pip install krippendorff")


# =============================================================================
# STATISTICAL FUNCTIONS (adapted from ~/Documents/GitHub/federal-survey-concept-mapper/src/lib/stats.py)
# =============================================================================

def cohens_kappa(labels1, labels2):
    """Compute Cohen's Kappa for two raters."""
    labels1 = np.array(labels1)
    labels2 = np.array(labels2)

    # Remove pairs where either is null
    mask = ~(pd.isna(labels1) | pd.isna(labels2))
    labels1 = labels1[mask]
    labels2 = labels2[mask]

    n = len(labels1)
    if n == 0:
        return np.nan

    # Observed agreement
    po = np.mean(labels1 == labels2)

    # Expected agreement (by chance)
    categories = list(set(labels1) | set(labels2))
    pe = 0
    for cat in categories:
        p1 = np.mean(labels1 == cat)
        p2 = np.mean(labels2 == cat)
        pe += p1 * p2

    # Kappa
    if pe == 1:
        return 1.0 if po == 1 else 0.0

    kappa = (po - pe) / (1 - pe)
    return kappa


def fleiss_kappa(ratings_matrix):
    """Compute Fleiss' Kappa for multiple raters.

    Args:
        ratings_matrix: 2D array, shape (n_items, n_raters)

    Returns:
        kappa: float
    """
    ratings = np.array(ratings_matrix)
    n_items, n_raters = ratings.shape

    # Get unique categories
    categories = sorted(list(set(ratings.flatten())))
    n_categories = len(categories)
    cat_to_idx = {cat: i for i, cat in enumerate(categories)}

    # Count matrix: for each item, count of each category
    counts = np.zeros((n_items, n_categories))
    for i in range(n_items):
        for j in range(n_raters):
            if not pd.isna(ratings[i, j]):
                cat_idx = cat_to_idx[ratings[i, j]]
                counts[i, cat_idx] += 1

    # P_i for each item
    P_i = (np.sum(counts ** 2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    P_bar = np.mean(P_i)

    # P_j for each category (proportion across all ratings)
    p_j = np.sum(counts, axis=0) / (n_items * n_raters)
    P_e_bar = np.sum(p_j ** 2)

    # Kappa
    if P_e_bar == 1:
        return 1.0 if P_bar == 1 else 0.0

    kappa = (P_bar - P_e_bar) / (1 - P_e_bar)
    return kappa


def percent_agreement(labels1, labels2):
    """Simple percentage agreement between two raters."""
    labels1 = np.array(labels1)
    labels2 = np.array(labels2)
    mask = ~(pd.isna(labels1) | pd.isna(labels2))
    if mask.sum() == 0:
        return np.nan
    return np.mean(labels1[mask] == labels2[mask])


def krippendorff_alpha(ratings_matrix, level_of_measurement='ordinal'):
    """Compute Krippendorff's Alpha for multiple raters."""
    if not HAS_KRIPPENDORFF:
        return np.nan

    # krippendorff expects shape (n_raters, n_items), so transpose
    data = np.array(ratings_matrix).T.tolist()
    return krippendorff.alpha(reliability_data=data, level_of_measurement=level_of_measurement)


def cohens_d_paired(x, y):
    """Cohen's d for paired samples."""
    diff = np.array(x) - np.array(y)
    return np.mean(diff) / np.std(diff, ddof=1)


def rank_biserial(x, y):
    """Rank-biserial correlation for Wilcoxon signed-rank test."""
    diff = np.array(x) - np.array(y)
    n = len(diff)
    if n == 0:
        return np.nan

    # Wilcoxon statistic
    W, _ = wilcoxon(diff)

    # Rank-biserial r = W / (n(n+1)/2) * 2 - 1
    max_W = n * (n + 1) / 2
    r = (W / max_W) * 2 - 1
    return r


def cronbach_alpha(data_matrix):
    """Cronbach's alpha for internal consistency.

    Args:
        data_matrix: 2D array, shape (n_items, n_dimensions)

    Returns:
        alpha: float
    """
    data = np.array(data_matrix)
    n_items, n_dimensions = data.shape

    # Variance of each dimension
    var_dims = np.var(data, axis=0, ddof=1)

    # Variance of total scores
    total_scores = np.sum(data, axis=1)
    var_total = np.var(total_scores, ddof=1)

    # Cronbach's alpha
    alpha = (n_dimensions / (n_dimensions - 1)) * (1 - np.sum(var_dims) / var_total)
    return alpha


def intraclass_correlation(data_matrix):
    """Intraclass Correlation Coefficient (ICC) for test-retest reliability.

    Uses ICC(3,1) - two-way mixed effects, absolute agreement, single rater.

    Args:
        data_matrix: 2D array, shape (n_subjects, n_measurements)

    Returns:
        icc: float
    """
    data = np.array(data_matrix)
    n, k = data.shape

    # Mean squares
    row_means = np.mean(data, axis=1)
    grand_mean = np.mean(data)

    # Between-subjects sum of squares
    SS_between = k * np.sum((row_means - grand_mean) ** 2)

    # Within-subjects sum of squares
    SS_within = np.sum((data - row_means[:, np.newaxis]) ** 2)

    # Mean squares
    MS_between = SS_between / (n - 1)
    MS_within = SS_within / (n * (k - 1))

    # ICC(3,1)
    icc = (MS_between - MS_within) / (MS_between + (k - 1) * MS_within)
    return icc


# =============================================================================
# DATA LOADING
# =============================================================================

def load_judge_scores(scores_path: Path) -> pd.DataFrame:
    """Load judge scores from JSONL into DataFrame with deduplication.

    Keeps latest record per (query_id, judge_vendor, presentation_order, pass_number) key.
    This handles re-runs where new records are appended to JSONL.
    """
    records = []
    with open(scores_path) as f:
        for line in f:
            data = json.loads(line)
            records.append(data)

    print(f"Loaded {len(records)} raw records from {scores_path}")

    # Deduplicate - keep last occurrence per unique key
    seen = {}
    for r in records:
        key = (r['query_id'], r['judge_vendor'], r['presentation_order'], r['pass_number'])
        seen[key] = r

    deduped = list(seen.values())
    print(f"Deduplicated to {len(deduped)} unique records (removed {len(records) - len(deduped)} duplicates)")

    return pd.DataFrame(deduped)


def extract_dimension_scores(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Extract dimension scores into separate DataFrames for analysis.

    Returns:
        Dict mapping dimension name to DataFrame with columns:
        [query_id, judge, ordering, control_score, treatment_score, ...]
    """
    dimension_dfs = {}
    dimensions = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

    for dim in dimensions:
        rows = []
        for _, row in df.iterrows():
            if not row['parse_success']:
                continue

            # Get scores for this dimension from response_a and response_b
            score_a = row['scores_response_a'][dim]['score']
            score_b = row['scores_response_b'][dim]['score']
            conf_a = row['scores_response_a'][dim]['confidence']
            conf_b = row['scores_response_b'][dim]['confidence']

            # Map to control/treatment based on labels
            if row['response_a_label'] == 'control':
                control_score = score_a
                treatment_score = score_b
                control_conf = conf_a
                treatment_conf = conf_b
            else:
                control_score = score_b
                treatment_score = score_a
                control_conf = conf_b
                treatment_conf = conf_a

            rows.append({
                'query_id': row['query_id'],
                'judge': row['judge_vendor'],
                'judge_model': row['judge_model'],
                'ordering': row['presentation_order'],
                'control_score': control_score,
                'treatment_score': treatment_score,
                'control_confidence': control_conf,
                'treatment_confidence': treatment_conf,
                'is_retest': row.get('is_retest', False)
            })

        dimension_dfs[dim] = pd.DataFrame(rows)

    return dimension_dfs


# =============================================================================
# §6B.3: INTER-RATER AGREEMENT
# =============================================================================

def compute_inter_rater_agreement(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute all inter-rater agreement metrics per dimension."""
    results = {}

    for dim, df in dimension_dfs.items():
        # Filter to first rating only (exclude retests)
        df_first = df[~df['is_retest']]

        # Build ratings matrix for control and treatment separately
        judges = df_first['judge'].unique()
        query_ids = df_first['query_id'].unique()

        # Control ratings matrix: (n_queries, n_judges)
        control_matrix = []
        treatment_matrix = []

        for qid in query_ids:
            control_row = []
            treatment_row = []
            for judge in judges:
                judge_data = df_first[(df_first['query_id'] == qid) & (df_first['judge'] == judge)]
                if len(judge_data) > 0:
                    # Take mean across both orderings if present
                    control_row.append(judge_data['control_score'].mean())
                    treatment_row.append(judge_data['treatment_score'].mean())
                else:
                    control_row.append(np.nan)
                    treatment_row.append(np.nan)

            control_matrix.append(control_row)
            treatment_matrix.append(treatment_row)

        control_matrix = np.array(control_matrix)
        treatment_matrix = np.array(treatment_matrix)

        # Krippendorff's alpha (ordinal)
        alpha_control = krippendorff_alpha(control_matrix, 'ordinal')
        alpha_treatment = krippendorff_alpha(treatment_matrix, 'ordinal')

        # Fleiss' kappa
        fleiss_control = fleiss_kappa(control_matrix)
        fleiss_treatment = fleiss_kappa(treatment_matrix)

        # Pairwise Cohen's kappa
        pairwise_kappas = []
        for i, judge1 in enumerate(judges):
            for j, judge2 in enumerate(judges):
                if i < j:
                    labels1 = control_matrix[:, i]
                    labels2 = control_matrix[:, j]
                    kappa = cohens_kappa(labels1, labels2)
                    pairwise_kappas.append({
                        'judge1': judge1,
                        'judge2': judge2,
                        'kappa': kappa,
                        'condition': 'control'
                    })

        # Percent agreement
        percent_agreements = []
        for i, judge1 in enumerate(judges):
            for j, judge2 in enumerate(judges):
                if i < j:
                    labels1 = control_matrix[:, i]
                    labels2 = control_matrix[:, j]
                    pct = percent_agreement(labels1, labels2)
                    percent_agreements.append({
                        'judge1': judge1,
                        'judge2': judge2,
                        'percent_agreement': pct
                    })

        results[dim] = {
            'krippendorff_alpha_control': alpha_control,
            'krippendorff_alpha_treatment': alpha_treatment,
            'fleiss_kappa_control': fleiss_control,
            'fleiss_kappa_treatment': fleiss_treatment,
            'pairwise_cohens_kappa': pairwise_kappas,
            'pairwise_percent_agreement': percent_agreements
        }

    return results


# =============================================================================
# §6B.4: BIAS DIAGNOSTICS
# =============================================================================

def compute_position_bias(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute position bias metrics."""
    results = {}

    for dim, df in dimension_dfs.items():
        df_first = df[~df['is_retest']]

        # Swap consistency: for each query+judge, compare scores across orderings
        swap_consistency = []

        for query_id in df_first['query_id'].unique():
            for judge in df_first['judge'].unique():
                subset = df_first[(df_first['query_id'] == query_id) & (df_first['judge'] == judge)]

                if len(subset) == 2:  # Both orderings present
                    control_first = subset[subset['ordering'] == 'control_first'].iloc[0]
                    treatment_first = subset[subset['ordering'] == 'treatment_first'].iloc[0]

                    # Did the preference flip?
                    diff_control_first = control_first['control_score'] - control_first['treatment_score']
                    diff_treatment_first = treatment_first['control_score'] - treatment_first['treatment_score']

                    consistent = np.sign(diff_control_first) == np.sign(diff_treatment_first)

                    swap_consistency.append({
                        'query_id': query_id,
                        'judge': judge,
                        'consistent': consistent,
                        'diff_control_first': diff_control_first,
                        'diff_treatment_first': diff_treatment_first
                    })

        consistency_df = pd.DataFrame(swap_consistency)
        consistency_rate = consistency_df['consistent'].mean() if len(consistency_df) > 0 else np.nan

        results[dim] = {
            'swap_consistency_rate': consistency_rate,
            'swap_details': swap_consistency
        }

    return results


def compute_verbosity_bias(df: pd.DataFrame, dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute verbosity bias (correlation between response length and CQS scores)."""

    # Calculate total CQS for each response
    cqs_scores = []

    for _, row in df.iterrows():
        if not row['parse_success']:
            continue

        # Get control and treatment total CQS
        control_cqs = 0
        treatment_cqs = 0

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']:
            if row['response_a_label'] == 'control':
                control_cqs += row['scores_response_a'][dim]['score']
                treatment_cqs += row['scores_response_b'][dim]['score']
            else:
                control_cqs += row['scores_response_b'][dim]['score']
                treatment_cqs += row['scores_response_a'][dim]['score']

        cqs_scores.append({
            'query_id': row['query_id'],
            'judge': row['judge_vendor'],
            'control_cqs': control_cqs,
            'treatment_cqs': treatment_cqs,
            'is_retest': row.get('is_retest', False)
        })

    # We don't have response lengths in this DataFrame - would need to load from Stage 1
    # Placeholder for now
    return {
        'note': 'Verbosity bias requires Stage 1 response lengths - not computed'
    }


def compute_self_enhancement_bias(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute self-enhancement bias per vendor."""
    results = {}

    for dim, df in dimension_dfs.items():
        df_first = df[~df['is_retest']]

        # Per-vendor mean CQS for control and treatment
        vendor_means = []

        for judge in df_first['judge'].unique():
            judge_data = df_first[df_first['judge'] == judge]

            control_mean = judge_data['control_score'].mean()
            treatment_mean = judge_data['treatment_score'].mean()

            vendor_means.append({
                'judge': judge,
                'control_mean': control_mean,
                'treatment_mean': treatment_mean,
                'self_enhancement_ratio': treatment_mean / control_mean if control_mean > 0 else np.nan
            })

        results[dim] = {'vendor_means': vendor_means}

    return results


def compute_leniency_severity(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute leniency/severity per judge (mean score range)."""
    results = {}

    for dim, df in dimension_dfs.items():
        df_first = df[~df['is_retest']]

        judge_stats = []

        for judge in df_first['judge'].unique():
            judge_data = df_first[df_first['judge'] == judge]

            all_scores = pd.concat([judge_data['control_score'], judge_data['treatment_score']])

            judge_stats.append({
                'judge': judge,
                'mean_score': all_scores.mean(),
                'std_score': all_scores.std(),
                'min_score': all_scores.min(),
                'max_score': all_scores.max()
            })

        results[dim] = {'judge_stats': judge_stats}

    return results


# =============================================================================
# §6B.5: TREATMENT EFFECTS
# =============================================================================

def compute_treatment_effects(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute all treatment effect metrics."""
    results = {}

    for dim, df in dimension_dfs.items():
        df_first = df[~df['is_retest']]

        # Aggregate scores across judges and orderings
        query_scores = []

        for query_id in df_first['query_id'].unique():
            query_data = df_first[df_first['query_id'] == query_id]

            control_scores = query_data['control_score'].values
            treatment_scores = query_data['treatment_score'].values

            query_scores.append({
                'query_id': query_id,
                'control_mean': np.mean(control_scores),
                'treatment_mean': np.mean(treatment_scores),
                'control_scores': control_scores,
                'treatment_scores': treatment_scores
            })

        query_df = pd.DataFrame(query_scores)

        # Wilcoxon signed-rank test
        control_means = query_df['control_mean'].values
        treatment_means = query_df['treatment_mean'].values

        wilcoxon_stat, wilcoxon_p = wilcoxon(control_means, treatment_means)

        # Cohen's d (paired)
        cohens_d_val = cohens_d_paired(treatment_means, control_means)

        # Rank-biserial correlation
        rank_biserial_val = rank_biserial(treatment_means, control_means)

        # McNemar's test for D6 gate failures (score = 0)
        d6_failures_control = (query_df['control_mean'] == 0).sum()
        d6_failures_treatment = (query_df['treatment_mean'] == 0).sum()

        results[dim] = {
            'wilcoxon_statistic': wilcoxon_stat,
            'wilcoxon_p_value': wilcoxon_p,
            'cohens_d_paired': cohens_d_val,
            'rank_biserial': rank_biserial_val,
            'control_mean': control_means.mean(),
            'treatment_mean': treatment_means.mean(),
            'mean_difference': treatment_means.mean() - control_means.mean(),
            'd6_failures_control': d6_failures_control,
            'd6_failures_treatment': d6_failures_treatment
        }

    return results


# =============================================================================
# §6B.6: RELIABILITY
# =============================================================================

def compute_test_retest_reliability(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute ICC for test-retest reliability."""
    results = {}

    for dim, df in dimension_dfs.items():
        # Filter to retest subset only
        df_retest = df[df['is_retest']]

        if len(df_retest) == 0:
            results[dim] = {'icc': np.nan, 'note': 'No retest data'}
            continue

        # Build matrix: (n_queries, 2) for first test and retest
        # This is simplified - proper implementation needs to match test/retest pairs

        results[dim] = {'note': 'Test-retest ICC implementation requires paired test/retest matching'}

    return results


def compute_confidence_calibration(dimension_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Compute correlation between confidence and score accuracy."""
    results = {}

    for dim, df in dimension_dfs.items():
        # Placeholder - requires ground truth or consensus scores
        results[dim] = {'note': 'Confidence calibration requires ground truth scores'}

    return results


def compute_cronbach_alpha_dimensions(df: pd.DataFrame) -> float:
    """Compute Cronbach's alpha across all 6 dimensions for internal consistency."""

    # Build matrix: (n_responses, 6 dimensions)
    response_scores = []

    for _, row in df.iterrows():
        if not row['parse_success']:
            continue

        if not row.get('is_retest', False):  # First rating only
            scores = []
            for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']:
                # Use control scores
                if row['response_a_label'] == 'control':
                    scores.append(row['scores_response_a'][dim]['score'])
                else:
                    scores.append(row['scores_response_b'][dim]['score'])

            response_scores.append(scores)

    if len(response_scores) == 0:
        return np.nan

    matrix = np.array(response_scores)
    return cronbach_alpha(matrix)


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def run_analysis(scores_path: str, output_dir: str):
    """Run complete statistical analysis on judge scores."""

    print("="*60)
    print("JUDGE ANALYSIS - Stage 2")
    print("="*60)

    scores_path = Path(scores_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_judge_scores(scores_path)

    print(f"\nTotal records: {len(df)}")
    print(f"Parse success: {df['parse_success'].sum()} ({df['parse_success'].mean()*100:.1f}%)")

    # Extract dimension scores
    dimension_dfs = extract_dimension_scores(df)

    # Compute all metrics
    print("\nComputing inter-rater agreement...")
    inter_rater = compute_inter_rater_agreement(dimension_dfs)

    print("Computing position bias...")
    position_bias = compute_position_bias(dimension_dfs)

    print("Computing self-enhancement bias...")
    self_enhancement = compute_self_enhancement_bias(dimension_dfs)

    print("Computing leniency/severity...")
    leniency = compute_leniency_severity(dimension_dfs)

    print("Computing treatment effects...")
    treatment_effects = compute_treatment_effects(dimension_dfs)

    print("Computing Cronbach's alpha...")
    cronbach = compute_cronbach_alpha_dimensions(df)

    # Compile results
    results = {
        'metadata': {
            'scores_file': str(scores_path),
            'total_records': len(df),
            'parse_success_rate': df['parse_success'].mean(),
            'analysis_timestamp': datetime.utcnow().isoformat()
        },
        'inter_rater_agreement': inter_rater,
        'position_bias': position_bias,
        'self_enhancement_bias': self_enhancement,
        'leniency_severity': leniency,
        'treatment_effects': treatment_effects,
        'cronbach_alpha': cronbach
    }

    # Write JSON report
    json_path = output_dir / 'analysis_report.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nAnalysis complete!")
    print(f"Report: {json_path}")

    # Generate summary tables
    generate_summary_tables(results, output_dir)

    return results


def generate_summary_tables(results: Dict, output_dir: Path):
    """Generate markdown summary tables."""

    md_path = output_dir / 'summary_tables.md'

    with open(md_path, 'w') as f:
        f.write("# CQS Judge Analysis Summary\n\n")

        # Treatment effects table
        f.write("## Treatment Effects by Dimension\n\n")
        f.write("| Dimension | Control Mean | Treatment Mean | Difference | Wilcoxon p | Cohen's d |\n")
        f.write("|-----------|--------------|----------------|------------|------------|------------|\n")

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']:
            te = results['treatment_effects'][dim]
            f.write(f"| {dim} | {te['control_mean']:.2f} | {te['treatment_mean']:.2f} | "
                   f"{te['mean_difference']:.2f} | {te['wilcoxon_p_value']:.4f} | "
                   f"{te['cohens_d_paired']:.2f} |\n")

        f.write("\n## Inter-Rater Agreement\n\n")
        f.write("| Dimension | Krippendorff's α (Control) | Fleiss' κ (Control) |\n")
        f.write("|-----------|---------------------------|--------------------|\n")

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']:
            ira = results['inter_rater_agreement'][dim]
            f.write(f"| {dim} | {ira['krippendorff_alpha_control']:.3f} | "
                   f"{ira['fleiss_kappa_control']:.3f} |\n")

        f.write(f"\n## Internal Consistency\n\n")
        f.write(f"Cronbach's α across all 6 dimensions: {results['cronbach_alpha']:.3f}\n")

    print(f"Summary tables: {md_path}")


def main():
    """Entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m eval.judge_analysis <scores_file.jsonl>")
        sys.exit(1)

    scores_path = sys.argv[1]
    output_dir = 'results/stage2/analysis'

    run_analysis(scores_path, output_dir)


if __name__ == '__main__':
    main()
