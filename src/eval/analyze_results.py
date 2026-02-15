"""Aggregate Analysis Script - Phase 4B CQS Evaluation Results.

Computes all statistics for FCSM paper from Stage 2 (judge scores) and
Stage 3 (pipeline fidelity) outputs.

Usage:
    python -m eval.analyze_results [--config PATH] [--stage2-dir PATH] [--stage3-file PATH]
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
from scipy.stats import bootstrap


# =============================================================================
# DATA LOADING & VALIDATION
# =============================================================================

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_stage2_records(stage2_dir: Path) -> List[Dict[str, Any]]:
    """Load and parse all Stage 2 judge score files.

    Returns:
        List of JudgeRecord dicts with parse_success=True only
    """
    records = []
    files = sorted(stage2_dir.glob("judge_scores_*.jsonl"))

    total_lines = 0
    parse_failures = 0

    for file_path in files:
        with open(file_path) as f:
            for line in f:
                total_lines += 1
                record = json.loads(line)

                if not record.get('parse_success', False):
                    parse_failures += 1
                    continue

                records.append(record)

    print(f"\n📊 Stage 2 Data Loaded:")
    print(f"  Total records: {total_lines}")
    print(f"  Parse failures: {parse_failures} ({parse_failures/total_lines*100:.1f}%)")
    print(f"  Valid records: {len(records)}")

    # Per-vendor counts
    vendor_counts = defaultdict(int)
    for r in records:
        vendor_counts[r['judge_vendor']] += 1

    print(f"\n  Per-vendor:")
    for vendor in sorted(vendor_counts.keys()):
        print(f"    {vendor}: {vendor_counts[vendor]}")

    return records


def load_stage3_fidelity(stage3_file: Path) -> List[Dict[str, Any]]:
    """Load Stage 3 fidelity verification results."""
    records = []
    with open(stage3_file) as f:
        for line in f:
            records.append(json.loads(line))

    print(f"\n📊 Stage 3 Fidelity Loaded: {len(records)} queries")
    return records


def load_stage1_metadata(stage1_file: Path) -> Dict[str, Dict[str, str]]:
    """Load Stage 1 metadata for stratification.

    Returns:
        Dict mapping query_id -> {category, difficulty}
    """
    metadata = {}
    with open(stage1_file) as f:
        for line in f:
            record = json.loads(line)
            metadata[record['query_id']] = {
                'category': record.get('category', 'unknown'),
                'difficulty': record.get('difficulty', 'unknown')
            }

    print(f"\n📊 Stage 1 Metadata Loaded: {len(metadata)} queries")

    # Category distribution
    categories = defaultdict(int)
    for meta in metadata.values():
        categories[meta['category']] += 1

    print(f"  Categories:")
    for cat in sorted(categories.keys()):
        print(f"    {cat}: {categories[cat]}")

    return metadata


def map_scores_to_conditions(record: Dict[str, Any]) -> Tuple[Dict, Dict]:
    """Map response A/B scores back to control/treatment.

    Args:
        record: JudgeRecord dict with response_a_label/response_b_label

    Returns:
        (control_scores, treatment_scores) - each is dict[dimension -> DimensionScore]
    """
    a_label = record['response_a_label']
    b_label = record['response_b_label']

    scores_a = record['scores_response_a']
    scores_b = record['scores_response_b']

    if a_label == 'control':
        return scores_a, scores_b
    else:
        return scores_b, scores_a


# =============================================================================
# PER-DIMENSION EFFECT SIZES
# =============================================================================

def compute_cohens_d(treatment_scores: List[float], control_scores: List[float]) -> float:
    """Compute Cohen's d effect size (independent samples formula)."""
    mean_t = np.mean(treatment_scores)
    mean_c = np.mean(control_scores)

    # Pooled standard deviation
    n_t = len(treatment_scores)
    n_c = len(control_scores)
    var_t = np.var(treatment_scores, ddof=1)
    var_c = np.var(control_scores, ddof=1)

    pooled_sd = np.sqrt(((n_t - 1) * var_t + (n_c - 1) * var_c) / (n_t + n_c - 2))

    if pooled_sd == 0:
        return 0.0

    return (mean_t - mean_c) / pooled_sd


def compute_paired_cohens_d(treatment_scores: List[float], control_scores: List[float]) -> float:
    """Compute Cohen's d for paired/repeated-measures design.

    Uses within-pair differences, appropriate for paired data where each
    query has both treatment and control conditions.
    """
    diffs = np.array(treatment_scores) - np.array(control_scores)
    if np.std(diffs, ddof=1) == 0:
        return 0.0
    return np.mean(diffs) / np.std(diffs, ddof=1)


def bootstrap_cohens_d_ci(treatment_scores: np.ndarray, control_scores: np.ndarray,
                          n_bootstrap: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for Cohen's d."""
    def cohens_d_stat(treatment, control):
        return compute_cohens_d(treatment.tolist(), control.tolist())

    # Bootstrap both samples together
    rng = np.random.default_rng(seed=42)
    d_values = []

    for _ in range(n_bootstrap):
        t_resample = rng.choice(treatment_scores, size=len(treatment_scores), replace=True)
        c_resample = rng.choice(control_scores, size=len(control_scores), replace=True)
        d_values.append(compute_cohens_d(t_resample.tolist(), c_resample.tolist()))

    alpha = 1 - confidence
    ci_lower = np.percentile(d_values, alpha/2 * 100)
    ci_upper = np.percentile(d_values, (1 - alpha/2) * 100)

    return ci_lower, ci_upper


def analyze_effect_sizes(records: List[Dict[str, Any]], dimensions: List[str]) -> Dict[str, Any]:
    """Compute effect sizes for all dimensions (D1-D5, excluding D6 from composite).

    Returns:
        Dict with overall and per-vendor effect sizes
    """
    results = {
        'overall': {},
        'by_vendor': defaultdict(dict),
        'd6_separate': {}  # D6 reported separately per DEC-4B-023
    }

    # Collect scores by dimension
    for dim in dimensions:
        treatment_scores = []
        control_scores = []

        # Per-vendor collections
        vendor_treatment = defaultdict(list)
        vendor_control = defaultdict(list)

        for record in records:
            control, treatment = map_scores_to_conditions(record)
            vendor = record['judge_vendor']

            if dim in control and dim in treatment:
                c_score = control[dim]['score']
                t_score = treatment[dim]['score']

                control_scores.append(c_score)
                treatment_scores.append(t_score)

                vendor_control[vendor].append(c_score)
                vendor_treatment[vendor].append(t_score)

        # Overall effect size
        t_arr = np.array(treatment_scores)
        c_arr = np.array(control_scores)

        d = compute_cohens_d(treatment_scores, control_scores)
        ci_lower, ci_upper = bootstrap_cohens_d_ci(t_arr, c_arr)

        target = results['d6_separate'] if dim == 'D6' else results['overall']

        target[dim] = {
            'cohens_d': d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'mean_treatment': np.mean(treatment_scores),
            'mean_control': np.mean(control_scores),
            'n': len(treatment_scores)
        }

        # Per-vendor effect sizes
        for vendor in vendor_treatment.keys():
            vt = vendor_treatment[vendor]
            vc = vendor_control[vendor]

            if len(vt) > 0 and len(vc) > 0:
                d_vendor = compute_cohens_d(vt, vc)
                results['by_vendor'][vendor][dim] = {
                    'cohens_d': d_vendor,
                    'mean_treatment': np.mean(vt),
                    'mean_control': np.mean(vc),
                    'n': len(vt)
                }

    # Compute composite CQS (D1-D5 only, excluding D6)
    composite_treatment = []
    composite_control = []

    for record in records:
        control, treatment = map_scores_to_conditions(record)

        # Average D1-D5 only
        composite_dims = ['D1', 'D2', 'D3', 'D4', 'D5']
        c_scores = [control[d]['score'] for d in composite_dims if d in control]
        t_scores = [treatment[d]['score'] for d in composite_dims if d in treatment]

        if len(c_scores) == 5 and len(t_scores) == 5:
            composite_control.append(np.mean(c_scores))
            composite_treatment.append(np.mean(t_scores))

    ct_arr = np.array(composite_treatment)
    cc_arr = np.array(composite_control)

    d_composite = compute_cohens_d(composite_treatment, composite_control)
    ci_lower, ci_upper = bootstrap_cohens_d_ci(ct_arr, cc_arr)

    results['overall']['Composite'] = {
        'cohens_d': d_composite,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'mean_treatment': np.mean(composite_treatment),
        'mean_control': np.mean(composite_control),
        'n': len(composite_treatment)
    }

    return results


# =============================================================================
# INTER-RATER RELIABILITY
# =============================================================================

def compute_krippendorff_alpha(ratings_matrix: np.ndarray) -> float:
    """Compute Krippendorff's alpha for ordinal data.

    Args:
        ratings_matrix: (n_items, n_raters) with values 0, 1, 2 or NaN for missing

    Returns:
        Alpha coefficient
    """
    try:
        import krippendorff
        return krippendorff.alpha(reliability_data=ratings_matrix.T, level_of_measurement='ordinal')
    except ImportError:
        print("⚠️  krippendorff package not installed. Run: pip install krippendorff")
        return np.nan


def analyze_inter_rater_reliability(records: List[Dict[str, Any]],
                                    dimensions: List[str]) -> Dict[str, Any]:
    """Compute Krippendorff's alpha for each dimension across 3 vendors."""
    results = {}

    # Group records by query_id and pass_number to align ratings
    grouped = defaultdict(lambda: defaultdict(dict))

    for record in records:
        qid = record['query_id']
        vendor = record['judge_vendor']
        pass_num = record.get('pass_number', 1)
        # Bug 6 fix: presentation_order is deterministic from pass_num, redundant in key
        key = (qid, pass_num)

        _, treatment = map_scores_to_conditions(record)
        grouped[key][vendor] = treatment

    for dim in dimensions:
        # Build ratings matrix: rows = items (query+pass combos), cols = vendors
        vendors = ['anthropic', 'openai', 'google']
        ratings = []

        for key in sorted(grouped.keys()):
            row = []
            for vendor in vendors:
                if vendor in grouped[key] and dim in grouped[key][vendor]:
                    row.append(grouped[key][vendor][dim]['score'])
                else:
                    row.append(np.nan)
            ratings.append(row)

        ratings_matrix = np.array(ratings)
        alpha = compute_krippendorff_alpha(ratings_matrix)

        # Count valid ratings
        n_valid = np.sum(~np.isnan(ratings_matrix))
        n_total = ratings_matrix.size

        results[dim] = {
            'alpha': alpha,
            'interpretation': interpret_alpha(alpha),
            'n_ratings': n_valid,
            'n_possible': n_total,
            'coverage': n_valid / n_total if n_total > 0 else 0.0
        }

    return results


def interpret_alpha(alpha: float) -> str:
    """Interpret Krippendorff's alpha value."""
    if np.isnan(alpha):
        return 'Not computed'
    elif alpha > 0.8:
        return 'Good'
    elif alpha > 0.667:
        return 'Acceptable'
    elif alpha > 0.4:
        return 'Marginal'
    else:
        return 'Poor'


# =============================================================================
# BIAS DIAGNOSTICS
# =============================================================================

def analyze_position_bias(records: List[Dict[str, Any]], dimensions: List[str]) -> Dict[str, Any]:
    """Test whether scores differ based on presentation position (A vs B)."""
    results = {}

    for vendor in ['anthropic', 'openai', 'google']:
        vendor_records = [r for r in records if r['judge_vendor'] == vendor]

        vendor_results = {}
        for dim in dimensions:
            # Collect treatment scores when presented as A vs B
            scores_when_a = []
            scores_when_b = []

            for record in vendor_records:
                _, treatment = map_scores_to_conditions(record)

                if dim in treatment:
                    score = treatment[dim]['score']

                    # Check if treatment was response A or B
                    if record['response_a_label'] == 'treatment':
                        scores_when_a.append(score)
                    else:
                        scores_when_b.append(score)

            if len(scores_when_a) > 0 and len(scores_when_b) > 0:
                mean_a = np.mean(scores_when_a)
                mean_b = np.mean(scores_when_b)
                difference = mean_a - mean_b

                # Paired t-test (approximate - not truly paired at observation level)
                stat, p_value = stats.ttest_ind(scores_when_a, scores_when_b)

                vendor_results[dim] = {
                    'mean_when_a': mean_a,
                    'mean_when_b': mean_b,
                    'difference': difference,
                    'p_value': p_value,
                    'significant': abs(difference) > 0.2 and p_value < 0.05,
                    'n_a': len(scores_when_a),
                    'n_b': len(scores_when_b)
                }

        results[vendor] = vendor_results

    return results


def analyze_self_enhancement_bias(effect_sizes: Dict[str, Any]) -> Dict[str, Any]:
    """Test whether Anthropic shows inflated treatment scores (judging Claude)."""
    results = {}

    # Compare Anthropic's treatment-control delta to others
    by_vendor = effect_sizes['by_vendor']

    for dim in ['D1', 'D2', 'D3', 'D4', 'D5']:
        if dim in by_vendor['anthropic']:
            anthro_d = by_vendor['anthropic'][dim]['cohens_d']
            openai_d = by_vendor.get('openai', {}).get(dim, {}).get('cohens_d', 0)
            google_d = by_vendor.get('google', {}).get(dim, {}).get('cohens_d', 0)

            avg_others = (openai_d + google_d) / 2 if openai_d and google_d else openai_d or google_d

            delta = anthro_d - avg_others

            results[dim] = {
                'anthropic_d': anthro_d,
                'avg_others_d': avg_others,
                'delta': delta,
                'flagged': delta > 0.3  # Threshold from task spec
            }

    return results


def analyze_verbosity_bias(records: List[Dict[str, Any]],
                           stage1_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Correlate response length with composite score."""
    # Load response lengths from Stage 1
    response_lengths = {}
    for record in stage1_data:
        qid = record['query_id']
        response_lengths[qid] = {
            'control': len(record['control']['response_text']),
            'treatment': len(record['treatment']['response_text'])
        }

    results = {}

    for vendor in ['anthropic', 'openai', 'google']:
        vendor_records = [r for r in records if r['judge_vendor'] == vendor]

        treatment_lengths = []
        treatment_composites = []
        control_lengths = []
        control_composites = []

        for record in vendor_records:
            qid = record['query_id']
            if qid not in response_lengths:
                continue

            control, treatment = map_scores_to_conditions(record)

            # Compute composite (D1-D5)
            composite_dims = ['D1', 'D2', 'D3', 'D4', 'D5']

            # Treatment
            t_scores = [treatment[d]['score'] for d in composite_dims if d in treatment]
            if len(t_scores) == 5:
                treatment_lengths.append(response_lengths[qid]['treatment'])
                treatment_composites.append(np.mean(t_scores))

            # Bug 7 fix: Also analyze control
            c_scores = [control[d]['score'] for d in composite_dims if d in control]
            if len(c_scores) == 5:
                control_lengths.append(response_lengths[qid]['control'])
                control_composites.append(np.mean(c_scores))

        vendor_result = {}

        if len(treatment_lengths) > 5:
            rho_t, p_t = stats.spearmanr(treatment_lengths, treatment_composites)
            vendor_result['treatment'] = {
                'spearman_rho': rho_t,
                'p_value': p_t,
                'n': len(treatment_lengths)
            }

        if len(control_lengths) > 5:
            rho_c, p_c = stats.spearmanr(control_lengths, control_composites)
            vendor_result['control'] = {
                'spearman_rho': rho_c,
                'p_value': p_c,
                'n': len(control_lengths)
            }

        if vendor_result:
            results[vendor] = vendor_result

    return results


# =============================================================================
# TEST-RETEST RELIABILITY
# =============================================================================

def analyze_test_retest(records: List[Dict[str, Any]], dimensions: List[str]) -> Dict[str, Any]:
    """Compute test-retest reliability across 6 passes."""
    results = {}

    for vendor in ['anthropic', 'openai', 'google']:
        vendor_records = [r for r in records if r['judge_vendor'] == vendor]

        # Group by query and pass
        grouped = defaultdict(dict)
        for record in vendor_records:
            qid = record['query_id']
            pass_num = record.get('pass_number', 1)
            _, treatment = map_scores_to_conditions(record)
            grouped[qid][pass_num] = treatment

        vendor_results = {}
        for dim in dimensions:
            # Bug 1 fix: Collect all pass-pairs into single list
            # Each pass-pair is an independent measurement occasion, so combining
            # them increases statistical power without inflating correlation
            all_pairs = []

            for qid in grouped.keys():
                passes = grouped[qid]

                # Pair 1: passes 1 & 2
                if 1 in passes and 2 in passes and dim in passes[1] and dim in passes[2]:
                    all_pairs.append((passes[1][dim]['score'], passes[2][dim]['score']))

                # Pair 2: passes 3 & 4
                if 3 in passes and 4 in passes and dim in passes[3] and dim in passes[4]:
                    all_pairs.append((passes[3][dim]['score'], passes[4][dim]['score']))

                # Pair 3: passes 5 & 6
                if 5 in passes and 6 in passes and dim in passes[5] and dim in passes[6]:
                    all_pairs.append((passes[5][dim]['score'], passes[6][dim]['score']))

            if len(all_pairs) > 3:
                # Compute Pearson correlation between paired measurements
                scores_a = [p[0] for p in all_pairs]
                scores_b = [p[1] for p in all_pairs]

                r, p_value = stats.pearsonr(scores_a, scores_b)

                vendor_results[dim] = {
                    'pearson_r': r,
                    'p_value': p_value,
                    'n_pairs': len(all_pairs),  # Total across all pass-pairs
                    'interpretation': 'Good' if r > 0.7 else 'Moderate' if r > 0.5 else 'Poor'
                }

        results[vendor] = vendor_results

    return results


# =============================================================================
# STRATIFIED ANALYSIS
# =============================================================================

def analyze_stratified_effects(records: List[Dict[str, Any]],
                               metadata: Dict[str, Dict[str, str]],
                               dimensions: List[str]) -> Dict[str, Any]:
    """Compute effect sizes separately for normal vs edge case queries."""
    results = {}

    # Define strata
    strata = {
        'normal': [],
        'edge_cases': []
    }

    for record in records:
        qid = record['query_id']
        if qid in metadata:
            category = metadata[qid]['category']
            stratum = 'normal' if category == 'normal' else 'edge_cases'
            strata[stratum].append(record)

    for stratum, stratum_records in strata.items():
        stratum_results = {}

        for dim in dimensions:
            # Bug 4 fix: Aggregate to query level first to avoid inflated N
            # from repeated measures (vendors × passes)
            query_treatment = defaultdict(list)
            query_control = defaultdict(list)

            for record in stratum_records:
                control, treatment = map_scores_to_conditions(record)
                qid = record['query_id']

                if dim in control and dim in treatment:
                    query_control[qid].append(control[dim]['score'])
                    query_treatment[qid].append(treatment[dim]['score'])

            # Compute query-level means
            paired_queries = sorted(set(query_treatment.keys()) & set(query_control.keys()))
            query_t_means = [np.mean(query_treatment[qid]) for qid in paired_queries]
            query_c_means = [np.mean(query_control[qid]) for qid in paired_queries]

            # Also collect all record-level scores for backward compatibility
            all_treatment = [s for scores in query_treatment.values() for s in scores]
            all_control = [s for scores in query_control.values() for s in scores]

            if len(paired_queries) > 0:
                # Effect size on query-level means (paired design)
                d_paired = compute_paired_cohens_d(query_t_means, query_c_means)

                # Also compute independent d on all records
                t_arr = np.array(all_treatment)
                c_arr = np.array(all_control)
                d_independent = compute_cohens_d(all_treatment, all_control)
                ci_lower, ci_upper = bootstrap_cohens_d_ci(t_arr, c_arr)

                # Wilcoxon on query-level means (correct N)
                if len(paired_queries) >= 10:
                    stat, p_value = stats.wilcoxon(query_t_means, query_c_means)
                else:
                    p_value = np.nan  # Too few queries for meaningful test

                stratum_results[dim] = {
                    'cohens_d': d_independent,  # Conservative (independent formula)
                    'cohens_d_paired': d_paired,  # Primary (paired formula on query means)
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'mean_treatment': np.mean(query_t_means),
                    'mean_control': np.mean(query_c_means),
                    'p_value': p_value,
                    'n_queries': len(paired_queries),
                    'n_records': len(all_treatment)
                }

        results[stratum] = stratum_results

    return results


# =============================================================================
# PREFERENCE ANALYSIS
# =============================================================================

def analyze_preferences(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which response judges preferred (treatment vs control)."""
    results = {}

    for vendor in ['anthropic', 'openai', 'google']:
        vendor_records = [r for r in records if r['judge_vendor'] == vendor]

        treatment_preferred = 0
        control_preferred = 0
        ties = 0

        for record in vendor_records:
            pref = record.get('preference', 'parse_failed')

            if pref == 'parse_failed':
                continue

            # Map A/B preference to control/treatment
            if pref == 'A':
                if record['response_a_label'] == 'treatment':
                    treatment_preferred += 1
                else:
                    control_preferred += 1
            elif pref == 'B':
                if record['response_b_label'] == 'treatment':
                    treatment_preferred += 1
                else:
                    control_preferred += 1
            elif pref == 'tie':
                ties += 1

        total = treatment_preferred + control_preferred + ties

        if total > 0:
            results[vendor] = {
                'pct_treatment': treatment_preferred / total * 100,
                'pct_control': control_preferred / total * 100,
                'pct_tie': ties / total * 100,
                'n_treatment': treatment_preferred,
                'n_control': control_preferred,
                'n_tie': ties,
                'n_total': total
            }

    # Pooled preference
    all_treatment = sum(r['n_treatment'] for r in results.values())
    all_control = sum(r['n_control'] for r in results.values())
    all_tie = sum(r['n_tie'] for r in results.values())
    all_total = all_treatment + all_control + all_tie

    if all_total > 0:
        results['pooled'] = {
            'pct_treatment': all_treatment / all_total * 100,
            'pct_control': all_control / all_total * 100,
            'pct_tie': all_tie / all_total * 100,
            'n_treatment': all_treatment,
            'n_control': all_control,
            'n_tie': all_tie,
            'n_total': all_total
        }

    return results


# =============================================================================
# STAGE 3 FIDELITY SUMMARY
# =============================================================================

def analyze_fidelity(fidelity_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate Stage 3 pipeline fidelity results."""
    # Treatment fidelity aggregation
    total_claims = 0
    matched = 0
    mismatched = 0
    no_source = 0
    calc_correct = 0
    calc_incorrect = 0

    # Auditability aggregation
    treatment_aud = {'auditable': 0, 'partially_auditable': 0, 'unauditable': 0, 'non_claims': 0, 'total': 0}
    control_aud = {'auditable': 0, 'partially_auditable': 0, 'unauditable': 0, 'non_claims': 0, 'total': 0}

    for record in fidelity_records:
        # Treatment fidelity
        tf_summary = record.get('treatment_fidelity', {}).get('summary', {})
        total_claims += tf_summary.get('total_claims', 0)
        matched += tf_summary.get('matched', 0)
        mismatched += tf_summary.get('mismatched', 0)
        no_source += tf_summary.get('no_source', 0)
        calc_correct += tf_summary.get('calculation_correct', 0)
        calc_incorrect += tf_summary.get('calculation_incorrect', 0)

        # Treatment auditability
        ta_summary = record.get('treatment_auditability', {}).get('summary', {})
        for key in treatment_aud.keys():
            treatment_aud[key] += ta_summary.get(key, 0)

        # Control auditability
        ca_summary = record.get('control_auditability', {}).get('summary', {})
        for key in control_aud.keys():
            control_aud[key] += ca_summary.get(key, 0)

    # Bug 2 fix: Compute fidelity score using total_claims as denominator
    # no_source claims count against fidelity (unverifiable assertions)
    if total_claims > 0:
        fidelity_score = (matched + calc_correct) / total_claims * 100
    else:
        fidelity_score = 0.0

    # Also compute substantive fidelity (among verifiable claims only) for discussion
    substantive_claims = total_claims - no_source
    if substantive_claims > 0:
        substantive_fidelity = (matched + calc_correct) / substantive_claims * 100
    else:
        substantive_fidelity = 0.0

    # Bug 3 fix: Compute auditability percentages excluding non_claims
    # non_claims are methodological statements, not auditability candidates
    t_auditable_total = (treatment_aud['auditable'] + treatment_aud['partially_auditable'] +
                        treatment_aud['unauditable'])
    c_auditable_total = (control_aud['auditable'] + control_aud['partially_auditable'] +
                        control_aud['unauditable'])

    treatment_aud_pct = {
        'auditable': treatment_aud['auditable'] / t_auditable_total * 100 if t_auditable_total > 0 else 0,
        'partially_auditable': treatment_aud['partially_auditable'] / t_auditable_total * 100 if t_auditable_total > 0 else 0,
        'unauditable': treatment_aud['unauditable'] / t_auditable_total * 100 if t_auditable_total > 0 else 0,
    }

    control_aud_pct = {
        'auditable': control_aud['auditable'] / c_auditable_total * 100 if c_auditable_total > 0 else 0,
        'partially_auditable': control_aud['partially_auditable'] / c_auditable_total * 100 if c_auditable_total > 0 else 0,
        'unauditable': control_aud['unauditable'] / c_auditable_total * 100 if c_auditable_total > 0 else 0,
    }

    # Chi-square test on auditability distributions
    # Compare auditable vs (partially + unauditable) between conditions
    if t_auditable_total > 0 and c_auditable_total > 0:
        contingency = [
            [treatment_aud['auditable'], control_aud['auditable']],
            [treatment_aud['partially_auditable'] + treatment_aud['unauditable'],
             control_aud['partially_auditable'] + control_aud['unauditable']]
        ]
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    else:
        chi2, p_value = None, None

    return {
        'treatment_fidelity': {
            'total_claims': total_claims,
            'matched': matched,
            'mismatched': mismatched,
            'no_source': no_source,
            'calculation_correct': calc_correct,
            'calculation_incorrect': calc_incorrect,
            'fidelity_score': fidelity_score,
            'substantive_fidelity': substantive_fidelity,  # Among verifiable claims only
            'pct_matched': matched/total_claims*100 if total_claims > 0 else 0,
            'pct_calc_correct': calc_correct/total_claims*100 if total_claims > 0 else 0
        },
        'treatment_auditability': {
            'counts': treatment_aud,
            'percentages': treatment_aud_pct,
            'n_substantive': t_auditable_total,  # Excludes non_claims
            'n_non_claims': treatment_aud['non_claims']
        },
        'control_auditability': {
            'counts': control_aud,
            'percentages': control_aud_pct,
            'n_substantive': c_auditable_total,  # Excludes non_claims
            'n_non_claims': control_aud['non_claims']
        },
        'chi_square_test': {
            'chi2': chi2,
            'p_value': p_value
        }
    }


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def write_effect_sizes_csv(effect_sizes: Dict[str, Any], output_dir: Path):
    """Write effect sizes to CSV."""
    csv_path = output_dir / 'effect_sizes.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dimension', 'vendor', 'cohens_d', 'ci_lower', 'ci_upper', 'mean_treatment', 'mean_control', 'n'])
        writer.writeheader()

        # Overall results
        for dim, stats_dict in effect_sizes['overall'].items():
            writer.writerow({
                'dimension': dim,
                'vendor': 'pooled',
                'cohens_d': f"{stats_dict['cohens_d']:.2f}",
                'ci_lower': f"{stats_dict['ci_lower']:.2f}",
                'ci_upper': f"{stats_dict['ci_upper']:.2f}",
                'mean_treatment': f"{stats_dict['mean_treatment']:.2f}",
                'mean_control': f"{stats_dict['mean_control']:.2f}",
                'n': stats_dict['n']
            })

        # Per-vendor results
        for vendor, vendor_stats in effect_sizes['by_vendor'].items():
            for dim, stats_dict in vendor_stats.items():
                writer.writerow({
                    'dimension': dim,
                    'vendor': vendor,
                    'cohens_d': f"{stats_dict['cohens_d']:.2f}",
                    'ci_lower': 'N/A',
                    'ci_upper': 'N/A',
                    'mean_treatment': f"{stats_dict['mean_treatment']:.2f}",
                    'mean_control': f"{stats_dict['mean_control']:.2f}",
                    'n': stats_dict['n']
                })

        # D6 separate section
        if effect_sizes['d6_separate']:
            for dim, stats_dict in effect_sizes['d6_separate'].items():
                writer.writerow({
                    'dimension': f"{dim} (excluded)",
                    'vendor': 'pooled',
                    'cohens_d': f"{stats_dict['cohens_d']:.2f}",
                    'ci_lower': f"{stats_dict['ci_lower']:.2f}",
                    'ci_upper': f"{stats_dict['ci_upper']:.2f}",
                    'mean_treatment': f"{stats_dict['mean_treatment']:.2f}",
                    'mean_control': f"{stats_dict['mean_control']:.2f}",
                    'n': stats_dict['n']
                })

    print(f"  ✅ {csv_path}")


def write_irr_csv(irr_results: Dict[str, Any], output_dir: Path):
    """Write inter-rater reliability to CSV."""
    csv_path = output_dir / 'irr_scores.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dimension', 'alpha', 'interpretation', 'n_ratings', 'coverage'])
        writer.writeheader()

        for dim, stats in irr_results.items():
            writer.writerow({
                'dimension': dim,
                'alpha': f"{stats['alpha']:.3f}" if not np.isnan(stats['alpha']) else 'N/A',
                'interpretation': stats['interpretation'],
                'n_ratings': stats['n_ratings'],
                'coverage': f"{stats['coverage']*100:.1f}%"
            })

    print(f"  ✅ {csv_path}")


def write_bias_diagnostics_csv(position_bias: Dict, self_enhancement: Dict,
                               verbosity: Dict, output_dir: Path):
    """Write bias diagnostics to CSV."""
    csv_path = output_dir / 'bias_diagnostics.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['vendor', 'bias_type', 'dimension', 'metric', 'value', 'significant'])
        writer.writeheader()

        # Position bias
        for vendor, vendor_stats in position_bias.items():
            for dim, stats in vendor_stats.items():
                writer.writerow({
                    'vendor': vendor,
                    'bias_type': 'position',
                    'dimension': dim,
                    'metric': 'mean_difference',
                    'value': f"{stats['difference']:.3f}",
                    'significant': 'Yes' if stats['significant'] else 'No'
                })

        # Self-enhancement
        for dim, stats in self_enhancement.items():
            writer.writerow({
                'vendor': 'anthropic',
                'bias_type': 'self_enhancement',
                'dimension': dim,
                'metric': 'delta_vs_others',
                'value': f"{stats['delta']:.3f}",
                'significant': 'Yes' if stats['flagged'] else 'No'
            })

        # Verbosity (Bug 7 fix: now includes both treatment and control)
        for vendor, vendor_stats in verbosity.items():
            if 'treatment' in vendor_stats:
                stats = vendor_stats['treatment']
                writer.writerow({
                    'vendor': vendor,
                    'bias_type': 'verbosity_treatment',
                    'dimension': 'Composite',
                    'metric': 'spearman_rho',
                    'value': f"{stats['spearman_rho']:.3f}",
                    'significant': 'Yes' if stats['p_value'] < 0.05 else 'No'
                })

            if 'control' in vendor_stats:
                stats = vendor_stats['control']
                writer.writerow({
                    'vendor': vendor,
                    'bias_type': 'verbosity_control',
                    'dimension': 'Composite',
                    'metric': 'spearman_rho',
                    'value': f"{stats['spearman_rho']:.3f}",
                    'significant': 'Yes' if stats['p_value'] < 0.05 else 'No'
                })

    print(f"  ✅ {csv_path}")


def write_preference_csv(preferences: Dict[str, Any], output_dir: Path):
    """Write preference analysis to CSV."""
    csv_path = output_dir / 'preference_summary.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['vendor', 'pct_treatment', 'pct_control', 'pct_tie', 'n'])
        writer.writeheader()

        for vendor, stats in preferences.items():
            writer.writerow({
                'vendor': vendor,
                'pct_treatment': f"{stats['pct_treatment']:.1f}",
                'pct_control': f"{stats['pct_control']:.1f}",
                'pct_tie': f"{stats['pct_tie']:.1f}",
                'n': stats['n_total']
            })

    print(f"  ✅ {csv_path}")


def write_stratified_csv(stratified: Dict[str, Any], output_dir: Path):
    """Write stratified analysis to CSV."""
    csv_path = output_dir / 'stratified_effects.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['stratum', 'dimension', 'cohens_d_paired', 'cohens_d_independent',
                                               'ci_lower', 'ci_upper', 'p_value', 'n_queries', 'n_records'])
        writer.writeheader()

        for stratum, stratum_stats in stratified.items():
            for dim, stats in stratum_stats.items():
                p_val_str = f"{stats['p_value']:.4f}" if not np.isnan(stats['p_value']) else 'N/A'
                writer.writerow({
                    'stratum': stratum,
                    'dimension': dim,
                    'cohens_d_paired': f"{stats['cohens_d_paired']:.2f}",
                    'cohens_d_independent': f"{stats['cohens_d']:.2f}",
                    'ci_lower': f"{stats['ci_lower']:.2f}",
                    'ci_upper': f"{stats['ci_upper']:.2f}",
                    'p_value': p_val_str,
                    'n_queries': stats['n_queries'],
                    'n_records': stats['n_records']
                })

    print(f"  ✅ {csv_path}")


def write_fidelity_csv(fidelity: Dict[str, Any], output_dir: Path):
    """Write fidelity summary to CSV."""
    csv_path = output_dir / 'fidelity_summary.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'treatment_value', 'control_value'])
        writer.writeheader()

        # Fidelity scores
        writer.writerow({
            'metric': 'Fidelity Score (overall)',
            'treatment_value': f"{fidelity['treatment_fidelity']['fidelity_score']:.1f}%",
            'control_value': 'N/A'
        })

        writer.writerow({
            'metric': 'Substantive Fidelity (verifiable only)',
            'treatment_value': f"{fidelity['treatment_fidelity']['substantive_fidelity']:.1f}%",
            'control_value': 'N/A'
        })

        # Auditability (excludes non_claims)
        writer.writerow({
            'metric': 'Auditable Claims',
            'treatment_value': f"{fidelity['treatment_auditability']['percentages']['auditable']:.1f}%",
            'control_value': f"{fidelity['control_auditability']['percentages']['auditable']:.1f}%"
        })

        writer.writerow({
            'metric': 'Partially Auditable',
            'treatment_value': f"{fidelity['treatment_auditability']['percentages']['partially_auditable']:.1f}%",
            'control_value': f"{fidelity['control_auditability']['percentages']['partially_auditable']:.1f}%"
        })

        writer.writerow({
            'metric': 'Unauditable',
            'treatment_value': f"{fidelity['treatment_auditability']['percentages']['unauditable']:.1f}%",
            'control_value': f"{fidelity['control_auditability']['percentages']['unauditable']:.1f}%"
        })

        # Non-claims (descriptive)
        writer.writerow({
            'metric': 'Non-claims (excluded)',
            'treatment_value': fidelity['treatment_auditability']['n_non_claims'],
            'control_value': fidelity['control_auditability']['n_non_claims']
        })

    print(f"  ✅ {csv_path}")


def write_test_retest_csv(test_retest: Dict[str, Any], output_dir: Path):
    """Write test-retest reliability to CSV."""
    csv_path = output_dir / 'test_retest.csv'

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['vendor', 'dimension', 'pearson_r', 'p_value', 'interpretation', 'n_pairs'])
        writer.writeheader()

        for vendor, vendor_stats in test_retest.items():
            for dim, stats in vendor_stats.items():
                writer.writerow({
                    'vendor': vendor,
                    'dimension': dim,
                    'pearson_r': f"{stats['pearson_r']:.3f}",
                    'p_value': f"{stats['p_value']:.4f}",
                    'interpretation': stats['interpretation'],
                    'n_pairs': stats['n_pairs']
                })

    print(f"  ✅ {csv_path}")


def generate_markdown_report(all_results: Dict[str, Any], output_dir: Path):
    """Generate comprehensive markdown report."""
    md_path = output_dir / 'aggregate_report.md'

    with open(md_path, 'w') as f:
        f.write("# Phase 4B CQS Evaluation - Aggregate Results\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Effect sizes
        f.write("## Effect Sizes (Cohen's d)\n\n")
        f.write("### Overall (Pooled Across Vendors)\n\n")
        f.write("| Dimension | d | 95% CI | Interpretation | n |\n")
        f.write("|-----------|---|--------|----------------|---|\n")

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'Composite']:
            if dim in all_results['effect_sizes']['overall']:
                stats = all_results['effect_sizes']['overall'][dim]
                interp = interpret_d(stats['cohens_d'])
                f.write(f"| {dim} | {stats['cohens_d']:.2f} | [{stats['ci_lower']:.2f}, {stats['ci_upper']:.2f}] | {interp} | {stats['n']} |\n")

        # D6 note
        if all_results['effect_sizes']['d6_separate']:
            f.write("\n### D6 (Excluded from Composite per DEC-4B-023)\n\n")
            stats = all_results['effect_sizes']['d6_separate']['D6']
            f.write(f"- **Cohen's d:** {stats['cohens_d']:.2f} (negative)\n")
            f.write(f"- **Interpretation:** D6 rewarded vagueness, penalized specificity (rubric flaw)\n")
            f.write(f"- **Replaced by:** Automated Pipeline Fidelity metric (Stage 3)\n\n")

        # Preferences
        f.write("## Judge Preferences\n\n")
        f.write("| Vendor | Treatment | Control | Tie | n |\n")
        f.write("|--------|-----------|---------|-----|---|\n")

        for vendor in ['anthropic', 'openai', 'google', 'pooled']:
            if vendor in all_results['preferences']:
                p = all_results['preferences'][vendor]
                f.write(f"| {vendor} | {p['pct_treatment']:.1f}% | {p['pct_control']:.1f}% | {p['pct_tie']:.1f}% | {p['n_total']} |\n")

        # Fidelity
        f.write("\n## Pipeline Fidelity (Stage 3)\n\n")
        fid = all_results['fidelity']
        f.write(f"**Treatment Fidelity Score:** {fid['treatment_fidelity']['fidelity_score']:.1f}%\n\n")

        f.write("### Symmetric Auditability Comparison\n\n")
        f.write("| Metric | Treatment | Control |\n")
        f.write("|--------|-----------|----------|\n")

        t_aud = fid['treatment_auditability']['percentages']
        c_aud = fid['control_auditability']['percentages']

        f.write(f"| Auditable | {t_aud['auditable']:.1f}% | {c_aud['auditable']:.1f}% |\n")
        f.write(f"| Partially Auditable | {t_aud['partially_auditable']:.1f}% | {c_aud['partially_auditable']:.1f}% |\n")
        f.write(f"| Unauditable | {t_aud['unauditable']:.1f}% | {c_aud['unauditable']:.1f}% |\n")

        if fid['chi_square_test']['p_value']:
            f.write(f"\nχ² test: p = {fid['chi_square_test']['p_value']:.4f}\n")

        # IRR
        f.write("\n## Inter-Rater Reliability (Krippendorff's α)\n\n")
        f.write("| Dimension | α | Interpretation |\n")
        f.write("|-----------|---|----------------|\n")

        for dim in ['D1', 'D2', 'D3', 'D4', 'D5']:
            if dim in all_results['irr']:
                stats = all_results['irr'][dim]
                alpha_str = f"{stats['alpha']:.3f}" if not np.isnan(stats['alpha']) else 'N/A'
                f.write(f"| {dim} | {alpha_str} | {stats['interpretation']} |\n")

        f.write("\n---\n\n")
        f.write("**Note:** Full results available in CSV files in this directory.\n")

    print(f"  ✅ {md_path}")


def interpret_d(d: float) -> str:
    """Interpret Cohen's d effect size."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return 'Negligible'
    elif abs_d < 0.5:
        return 'Small'
    elif abs_d < 0.8:
        return 'Medium'
    else:
        return 'Large'


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Entry point with CLI arguments."""
    parser = argparse.ArgumentParser(description='Aggregate Analysis - Phase 4B CQS Evaluation')
    parser.add_argument('--config', default='src/eval/judge_config.yaml',
                       help='Path to judge config YAML')
    parser.add_argument('--stage2-dir', default='results/stage2',
                       help='Directory containing judge score JSONL files')
    parser.add_argument('--stage3-file', default='results/stage3/fidelity_20260213_195123.jsonl',
                       help='Stage 3 fidelity results file')

    args = parser.parse_args()

    print("="*70)
    print("PHASE 4B: AGGREGATE ANALYSIS")
    print("="*70)

    # Load config
    config = load_config(args.config)
    dimensions = config['scoring']['dimensions']  # ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

    # Load data
    stage2_records = load_stage2_records(Path(args.stage2_dir))
    fidelity_records = load_stage3_fidelity(Path(args.stage3_file))

    # Load Stage 1 for stratification
    stage1_path = Path(config['paths']['stage1_results'])
    metadata = load_stage1_metadata(stage1_path)

    # Also load full Stage 1 for verbosity analysis
    stage1_records = []
    with open(stage1_path) as f:
        for line in f:
            stage1_records.append(json.loads(line))

    # Run all analyses
    print("\n" + "="*70)
    print("RUNNING ANALYSES")
    print("="*70)

    print("\n1. Computing effect sizes...")
    effect_sizes = analyze_effect_sizes(stage2_records, dimensions)

    print("2. Computing inter-rater reliability...")
    irr = analyze_inter_rater_reliability(stage2_records, dimensions)

    print("3. Testing position bias...")
    position_bias = analyze_position_bias(stage2_records, dimensions)

    print("4. Testing self-enhancement bias...")
    self_enhancement = analyze_self_enhancement_bias(effect_sizes)

    print("5. Testing verbosity bias...")
    verbosity_bias = analyze_verbosity_bias(stage2_records, stage1_records)

    print("6. Computing test-retest reliability...")
    test_retest = analyze_test_retest(stage2_records, dimensions)

    print("7. Running stratified analysis...")
    stratified = analyze_stratified_effects(stage2_records, metadata, dimensions)

    print("8. Analyzing preferences...")
    preferences = analyze_preferences(stage2_records)

    print("9. Aggregating fidelity results...")
    fidelity = analyze_fidelity(fidelity_records)

    # Create output directory
    output_dir = Path(args.stage2_dir) / 'analysis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("WRITING OUTPUTS")
    print("="*70)
    print(f"\nOutput directory: {output_dir}\n")

    # Write CSVs
    write_effect_sizes_csv(effect_sizes, output_dir)
    write_irr_csv(irr, output_dir)
    write_bias_diagnostics_csv(position_bias, self_enhancement, verbosity_bias, output_dir)
    write_preference_csv(preferences, output_dir)
    write_stratified_csv(stratified, output_dir)
    write_fidelity_csv(fidelity, output_dir)
    write_test_retest_csv(test_retest, output_dir)

    # Generate markdown report
    all_results = {
        'effect_sizes': effect_sizes,
        'irr': irr,
        'position_bias': position_bias,
        'self_enhancement': self_enhancement,
        'verbosity_bias': verbosity_bias,
        'test_retest': test_retest,
        'stratified': stratified,
        'preferences': preferences,
        'fidelity': fidelity
    }

    generate_markdown_report(all_results, output_dir)

    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nResults written to: {output_dir}")
    print("\nNext steps:")
    print("  - Review aggregate_report.md for summary tables")
    print("  - Import CSVs into paper/presentation")
    print("  - Check bias_diagnostics.csv for methodological concerns")


if __name__ == '__main__':
    main()
