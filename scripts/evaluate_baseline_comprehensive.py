"""
Comprehensive Baseline Evaluation

This script performs comprehensive evaluation of the baseline model including:
- All metrics from evaluation module
- Detailed error analysis
- Common failure pattern identification
- City/station misidentification analysis
- Performance graphs and visualizations

Usage:
    python scripts/evaluate_baseline_comprehensive.py
"""

import pandas as pd
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter, defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.metrics import evaluate_model, normalize_city_name
from src.evaluation.report_template import save_report


def load_data(test_file: str, predictions_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load test data and predictions."""
    print("=" * 70)
    print("LOADING DATA")
    print("=" * 70)
    print()

    # Load ground truth
    print(f"Loading ground truth: {test_file}")
    gt = pd.read_csv(test_file, encoding='utf-8')
    print(f"  [OK] Loaded {len(gt)} sentences")

    # Load predictions
    print(f"\nLoading predictions: {predictions_file}")
    pred = pd.read_csv(predictions_file, encoding='utf-8')

    # Rename columns to match ground truth
    pred = pred.rename(columns={'Departure': 'origin', 'Destination': 'destination'})
    print(f"  [OK] Loaded {len(pred)} predictions")

    return gt, pred


def analyze_error_patterns(gt: pd.DataFrame, pred: pd.DataFrame) -> Dict:
    """Analyze common error patterns."""
    print("\n" + "=" * 70)
    print("ERROR PATTERN ANALYSIS")
    print("=" * 70)
    print()

    # Merge data
    merged = gt.merge(pred, on='sentenceID', suffixes=('_gt', '_pred'))

    # Normalize
    merged['origin_gt_norm'] = merged['origin_gt'].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged['destination_gt'].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged['origin_pred'].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged['destination_pred'].apply(normalize_city_name)

    # Filter to valid orders only
    valid = merged[merged['is_valid'] == 1].copy()

    # Categorize errors
    valid['origin_correct'] = valid['origin_gt_norm'] == valid['origin_pred_norm']
    valid['dest_correct'] = valid['dest_gt_norm'] == valid['dest_pred_norm']

    error_patterns = {
        'both_wrong': ((~valid['origin_correct']) & (~valid['dest_correct'])).sum(),
        'origin_wrong_only': ((~valid['origin_correct']) & (valid['dest_correct'])).sum(),
        'dest_wrong_only': ((valid['origin_correct']) & (~valid['dest_correct'])).sum(),
        'both_correct': (valid['origin_correct'] & valid['dest_correct']).sum()
    }

    total_valid = len(valid)
    print("Error Distribution:")
    print(f"  Both correct:           {error_patterns['both_correct']:4d} ({error_patterns['both_correct']/total_valid*100:.1f}%)")
    print(f"  Origin wrong only:      {error_patterns['origin_wrong_only']:4d} ({error_patterns['origin_wrong_only']/total_valid*100:.1f}%)")
    print(f"  Destination wrong only: {error_patterns['dest_wrong_only']:4d} ({error_patterns['dest_wrong_only']/total_valid*100:.1f}%)")
    print(f"  Both wrong:             {error_patterns['both_wrong']:4d} ({error_patterns['both_wrong']/total_valid*100:.1f}%)")

    # Analyze specific error types
    errors = valid[~(valid['origin_correct'] & valid['dest_correct'])].copy()

    # Type 1: Swapped (origin and dest reversed)
    errors['swapped'] = (errors['origin_gt_norm'] == errors['dest_pred_norm']) & \
                        (errors['dest_gt_norm'] == errors['origin_pred_norm'])

    # Type 2: Duplicated (same city for both)
    errors['duplicated'] = errors['origin_pred_norm'] == errors['dest_pred_norm']

    # Type 3: One missing (INVALID)
    errors['origin_missing'] = errors['origin_pred_norm'] == 'INVALID'
    errors['dest_missing'] = errors['dest_pred_norm'] == 'INVALID'

    print("\nSpecific Error Types:")
    print(f"  Swapped (reversed):     {errors['swapped'].sum():4d} ({errors['swapped'].sum()/len(errors)*100:.1f}% of errors)")
    print(f"  Duplicated (same city): {errors['duplicated'].sum():4d} ({errors['duplicated'].sum()/len(errors)*100:.1f}% of errors)")
    print(f"  Origin missing:         {errors['origin_missing'].sum():4d} ({errors['origin_missing'].sum()/len(errors)*100:.1f}% of errors)")
    print(f"  Destination missing:    {errors['dest_missing'].sum():4d} ({errors['dest_missing'].sum()/len(errors)*100:.1f}% of errors)")

    return {
        'error_distribution': error_patterns,
        'error_types': {
            'swapped': int(errors['swapped'].sum()),
            'duplicated': int(errors['duplicated'].sum()),
            'origin_missing': int(errors['origin_missing'].sum()),
            'dest_missing': int(errors['dest_missing'].sum())
        }
    }


def analyze_misidentified_cities(gt: pd.DataFrame, pred: pd.DataFrame) -> Dict:
    """Analyze which cities are most frequently misidentified."""
    print("\n" + "=" * 70)
    print("MISIDENTIFIED CITIES ANALYSIS")
    print("=" * 70)
    print()

    # Merge data
    merged = gt.merge(pred, on='sentenceID', suffixes=('_gt', '_pred'))
    merged['origin_gt_norm'] = merged['origin_gt'].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged['destination_gt'].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged['origin_pred'].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged['destination_pred'].apply(normalize_city_name)

    # Filter to valid orders
    valid = merged[merged['is_valid'] == 1].copy()

    # Cities with most origin errors
    origin_errors = valid[valid['origin_gt_norm'] != valid['origin_pred_norm']]
    origin_error_counts = Counter(origin_errors['origin_gt'])

    # Cities with most destination errors
    dest_errors = valid[valid['dest_gt_norm'] != valid['dest_pred_norm']]
    dest_error_counts = Counter(dest_errors['destination_gt'])

    print("Most Frequently Misidentified Origins (Top 10):")
    for city, count in origin_error_counts.most_common(10):
        total_occurrences = len(valid[valid['origin_gt'] == city])
        error_rate = count / total_occurrences * 100 if total_occurrences > 0 else 0
        print(f"  {city:25s}: {count:3d} / {total_occurrences:3d} errors ({error_rate:5.1f}%)")

    print("\nMost Frequently Misidentified Destinations (Top 10):")
    for city, count in dest_error_counts.most_common(10):
        total_occurrences = len(valid[valid['destination_gt'] == city])
        error_rate = count / total_occurrences * 100 if total_occurrences > 0 else 0
        print(f"  {city:25s}: {count:3d} / {total_occurrences:3d} errors ({error_rate:5.1f}%)")

    return {
        'origin_errors': dict(origin_error_counts.most_common(20)),
        'dest_errors': dict(dest_error_counts.most_common(20))
    }


def analyze_sentence_structures(gt: pd.DataFrame, pred: pd.DataFrame) -> Dict:
    """Analyze which sentence structures fail most often."""
    print("\n" + "=" * 70)
    print("SENTENCE STRUCTURE ANALYSIS")
    print("=" * 70)
    print()

    # Merge data
    merged = gt.merge(pred, on='sentenceID', suffixes=('_gt', '_pred'))
    merged['origin_gt_norm'] = merged['origin_gt'].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged['destination_gt'].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged['origin_pred'].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged['destination_pred'].apply(normalize_city_name)

    # Filter to valid orders
    valid = merged[merged['is_valid'] == 1].copy()
    valid['correct'] = (valid['origin_gt_norm'] == valid['origin_pred_norm']) & \
                       (valid['dest_gt_norm'] == valid['dest_pred_norm'])

    # Analyze by category
    category_stats = valid.groupby('category').agg({
        'correct': ['sum', 'count', 'mean']
    }).round(4)

    # Sort by error rate (ascending accuracy)
    category_stats = category_stats.sort_values(('correct', 'mean'))

    print("Performance by Sentence Structure (worst to best):")
    structure_results = {}
    for category, row in category_stats.iterrows():
        count = int(row[('correct', 'count')])
        correct = int(row[('correct', 'sum')])
        accuracy = row[('correct', 'mean')]
        errors = count - correct

        print(f"  {category:25s}: {correct:3d} / {count:3d} correct ({accuracy*100:5.1f}%) - {errors:3d} errors")

        structure_results[category] = {
            'total': count,
            'correct': correct,
            'errors': errors,
            'accuracy': float(accuracy)
        }

    return structure_results


def collect_failure_examples(gt: pd.DataFrame, pred: pd.DataFrame, max_per_category: int = 5) -> Dict:
    """Collect specific failure examples by category."""
    print("\n" + "=" * 70)
    print("FAILURE EXAMPLES BY CATEGORY")
    print("=" * 70)
    print()

    # Merge data
    merged = gt.merge(pred, on='sentenceID', suffixes=('_gt', '_pred'))
    merged['origin_gt_norm'] = merged['origin_gt'].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged['destination_gt'].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged['origin_pred'].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged['destination_pred'].apply(normalize_city_name)

    # Filter to errors only
    valid = merged[merged['is_valid'] == 1].copy()
    errors = valid[~((valid['origin_gt_norm'] == valid['origin_pred_norm']) &
                     (valid['dest_gt_norm'] == valid['dest_pred_norm']))]

    examples = {}

    # Get examples by category
    for category in errors['category'].unique():
        category_errors = errors[errors['category'] == category]
        samples = []

        for _, row in category_errors.head(max_per_category).iterrows():
            samples.append({
                'sentenceID': int(row['sentenceID']),
                'sentence': row['sentence'],
                'expected_origin': row['origin_gt'] if pd.notna(row['origin_gt']) else '',
                'expected_dest': row['destination_gt'] if pd.notna(row['destination_gt']) else '',
                'predicted_origin': row['origin_pred'],
                'predicted_dest': row['destination_pred']
            })

        if samples:
            examples[category] = samples

    # Print top 5 categories with most errors
    error_counts = errors.groupby('category').size().sort_values(ascending=False)

    print(f"Categories with Most Errors (Top 5):")
    for category in error_counts.head(5).index:
        count = error_counts[category]
        print(f"\n{category.upper()} ({count} errors):")

        for i, example in enumerate(examples[category][:3], 1):
            print(f"\n  Example {i} (ID {example['sentenceID']}):")
            print(f"    Sentence: {example['sentence']}")
            print(f"    Expected: {example['expected_origin']} -> {example['expected_dest']}")
            print(f"    Predicted: {example['predicted_origin']} -> {example['predicted_dest']}")

    return examples


def generate_recommendations(result, error_analysis: Dict, city_analysis: Dict, structure_analysis: Dict) -> List[str]:
    """Generate recommendations based on analysis."""
    recommendations = []

    # Recommendation 1: Invalid detection
    if result.false_positives > 100:
        recommendations.append({
            'priority': 'CRITICAL',
            'issue': 'Invalid Order Detection',
            'finding': f'{result.false_positives} false positives (invalid orders predicted as valid)',
            'recommendation': 'Implement validation logic: require both origin AND destination, check for duplicates, add confidence thresholds',
            'expected_impact': '+20-30% validity detection accuracy'
        })

    # Recommendation 2: Misspellings
    if 'misspelling' in result.robustness_scores and result.robustness_scores['misspelling'] < 0.15:
        recommendations.append({
            'priority': 'CRITICAL',
            'issue': 'Misspelling Handling',
            'finding': f'Only {result.robustness_scores["misspelling"]*100:.1f}% accuracy on misspelled text',
            'recommendation': 'Enable fuzzy matching in gazetteer with max_distance=2 or 3',
            'expected_impact': '+40-50% on misspelling category, +10-15% overall'
        })

    # Recommendation 3: Compound names
    if 'compound_name' in result.robustness_scores and result.robustness_scores['compound_name'] < 0.50:
        recommendations.append({
            'priority': 'HIGH',
            'issue': 'Compound Name Matching',
            'finding': f'Only {result.robustness_scores["compound_name"]*100:.1f}% accuracy on compound names',
            'recommendation': 'Add space-to-hyphen normalization for patterns like "sur Mer", "en Provence"',
            'expected_impact': '+20-30% on compound names, +5% overall'
        })

    # Recommendation 4: Duplicated predictions
    if error_analysis['error_types']['duplicated'] > 50:
        recommendations.append({
            'priority': 'MEDIUM',
            'issue': 'Duplicated City Predictions',
            'finding': f'{error_analysis["error_types"]["duplicated"]} cases where same city predicted for both origin and dest',
            'recommendation': 'Add heuristic validation: if only one city found, mark as INVALID instead of duplicating',
            'expected_impact': '+5-10% on no_markers and inverted_order categories'
        })

    # Recommendation 5: Inverted order
    if 'inverted_order' in result.robustness_scores and result.robustness_scores['inverted_order'] < 0.75:
        recommendations.append({
            'priority': 'MEDIUM',
            'issue': 'Inverted Order Pattern',
            'finding': f'Only {result.robustness_scores["inverted_order"]*100:.1f}% accuracy on inverted order',
            'recommendation': 'Add patterns for "Cap sur X", "Vers X depuis Y", "à X en partance de Y"',
            'expected_impact': '+15-20% on inverted_order category'
        })

    # Recommendation 6: Transition to CamemBERT
    if result.exact_match_accuracy < 0.75:
        recommendations.append({
            'priority': 'STRATEGIC',
            'issue': 'Baseline Ceiling',
            'finding': f'Baseline plateaus at {result.exact_match_accuracy*100:.1f}% exact match accuracy',
            'recommendation': 'Transition to CamemBERT NER model for context-aware extraction',
            'expected_impact': 'Target 85%+ accuracy (vs current ~69%)'
        })

    return recommendations


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    import numpy as np

    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    else:
        return obj


def save_comprehensive_report(
    result,
    error_analysis: Dict,
    city_analysis: Dict,
    structure_analysis: Dict,
    failure_examples: Dict,
    recommendations: List[Dict],
    output_dir: str
):
    """Save comprehensive evaluation report."""
    print("\n" + "=" * 70)
    print("GENERATING COMPREHENSIVE REPORTS")
    print("=" * 70)
    print()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Save standard reports using evaluation module
    save_report(
        result,
        output_dir,
        model_name="Baseline",
        dataset_name="Test Set",
        additional_info={'Total sentences': 1500},
        formats=['text', 'json', 'markdown']
    )

    # 2. Save comprehensive analysis
    comprehensive_data = {
        'metrics': result.to_dict(),
        'error_analysis': convert_numpy_types(error_analysis),
        'city_analysis': convert_numpy_types(city_analysis),
        'structure_analysis': convert_numpy_types(structure_analysis),
        'failure_examples': failure_examples,
        'recommendations': recommendations
    }

    json_file = output_path / "baseline_test_comprehensive.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Comprehensive analysis saved to: {json_file}")

    # 3. Generate recommendations report
    rec_file = output_path / "baseline_recommendations.md"
    with open(rec_file, 'w', encoding='utf-8') as f:
        f.write("# Baseline Model - Improvement Recommendations\n\n")
        f.write(f"**Test Set Performance**: {result.exact_match_accuracy*100:.2f}% exact match accuracy\n\n")
        f.write("---\n\n")

        for i, rec in enumerate(recommendations, 1):
            f.write(f"## {i}. {rec['issue']} [{rec['priority']}]\n\n")
            f.write(f"**Finding**: {rec['finding']}\n\n")
            f.write(f"**Recommendation**: {rec['recommendation']}\n\n")
            f.write(f"**Expected Impact**: {rec['expected_impact']}\n\n")
            f.write("---\n\n")

    print(f"[OK] Recommendations saved to: {rec_file}")


def main():
    """Main evaluation function."""
    print("\n")
    print("=" * 70)
    print("       COMPREHENSIVE BASELINE EVALUATION - TEST SET")
    print("=" * 70)
    print()

    # File paths
    test_file = "data/test.csv"
    predictions_file = "results/baseline_test_output.csv"
    output_dir = "results"

    # Load data
    gt, pred = load_data(test_file, predictions_file)

    # Run comprehensive evaluation
    print("\n" + "=" * 70)
    print("RUNNING METRICS EVALUATION")
    print("=" * 70)
    result = evaluate_model(pred, gt)

    # Print summary
    print("\nKey Metrics:")
    print(f"  Exact Match Accuracy: {result.exact_match_accuracy*100:.2f}%")
    print(f"  Validity F1 Score:    {result.validity_f1*100:.2f}%")
    print(f"  Origin Accuracy:      {result.origin_accuracy*100:.2f}%")
    print(f"  Destination Accuracy: {result.destination_accuracy*100:.2f}%")

    # Error pattern analysis
    error_analysis = analyze_error_patterns(gt, pred)

    # City misidentification analysis
    city_analysis = analyze_misidentified_cities(gt, pred)

    # Sentence structure analysis
    structure_analysis = analyze_sentence_structures(gt, pred)

    # Collect failure examples
    failure_examples = collect_failure_examples(gt, pred, max_per_category=10)

    # Generate recommendations
    recommendations = generate_recommendations(result, error_analysis, city_analysis, structure_analysis)

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS SUMMARY")
    print("=" * 70)
    print()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['priority']}] {rec['issue']}")
        print(f"   Finding: {rec['finding']}")
        print(f"   Impact:  {rec['expected_impact']}")
        print()

    # Save comprehensive report
    save_comprehensive_report(
        result,
        error_analysis,
        city_analysis,
        structure_analysis,
        failure_examples,
        recommendations,
        output_dir
    )

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"\nReports saved to: {output_dir}/")
    print("  - baseline_test_set_report.txt")
    print("  - baseline_test_set_report.json")
    print("  - baseline_test_set_report.md")
    print("  - baseline_test_comprehensive.json")
    print("  - baseline_recommendations.md")
    print()


if __name__ == "__main__":
    main()
