"""
Evaluate Baseline System on Validation Dataset

This script compares the baseline system's predictions on the validation dataset
against ground truth labels to measure performance metrics.

Usage:
    python scripts/evaluate_baseline_validation.py
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def normalize_city_name(name: str) -> str:
    """Normalize city name for comparison (lowercase, no accents)."""
    if pd.isna(name) or name == '':
        return ''

    # Handle INVALID marker
    if name.upper() == 'INVALID':
        return 'INVALID'

    # Lowercase and strip
    name = str(name).lower().strip()

    # Remove accents
    accent_map = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n'
    }

    for accented, plain in accent_map.items():
        name = name.replace(accented, plain)

    return name


def load_ground_truth(file_path: str) -> pd.DataFrame:
    """Load validation dataset with ground truth labels."""
    print(f"Loading ground truth from: {file_path}")
    df = pd.read_csv(file_path, encoding='utf-8')

    # Normalize ground truth
    df['gt_origin_norm'] = df['origin'].apply(normalize_city_name)
    df['gt_destination_norm'] = df['destination'].apply(normalize_city_name)

    # Create ground truth validity flag
    df['gt_is_valid'] = df['is_valid'] == 1

    print(f"  Loaded {len(df)} sentences")
    print(f"  Valid orders: {df['gt_is_valid'].sum()}")
    print(f"  Invalid orders: {(~df['gt_is_valid']).sum()}")

    return df


def load_predictions(file_path: str) -> pd.DataFrame:
    """Load baseline system predictions."""
    print(f"\nLoading predictions from: {file_path}")
    df = pd.read_csv(file_path, encoding='utf-8')

    # Rename columns to match ground truth format
    df = df.rename(columns={'Departure': 'origin', 'Destination': 'destination'})

    # Normalize predictions
    df['pred_origin_norm'] = df['origin'].apply(normalize_city_name)
    df['pred_destination_norm'] = df['destination'].apply(normalize_city_name)

    # Create prediction validity flag
    df['pred_is_valid'] = (df['pred_origin_norm'] != 'invalid') & (df['pred_destination_norm'] != 'invalid')

    print(f"  Loaded {len(df)} predictions")
    print(f"  Valid orders predicted: {df['pred_is_valid'].sum()}")
    print(f"  Invalid orders predicted: {(~df['pred_is_valid']).sum()}")

    return df


def merge_data(gt_df: pd.DataFrame, pred_df: pd.DataFrame) -> pd.DataFrame:
    """Merge ground truth and predictions."""
    # Merge on sentenceID
    merged = gt_df.merge(
        pred_df[['sentenceID', 'pred_origin_norm', 'pred_destination_norm', 'pred_is_valid']],
        on='sentenceID',
        how='left'
    )

    return merged


def evaluate_validity_detection(df: pd.DataFrame) -> Dict:
    """Evaluate ability to detect valid vs invalid orders."""
    print("\n" + "=" * 70)
    print("VALIDITY DETECTION METRICS")
    print("=" * 70)

    # Calculate confusion matrix
    tp = ((df['gt_is_valid']) & (df['pred_is_valid'])).sum()  # True Positive: valid detected as valid
    tn = ((~df['gt_is_valid']) & (~df['pred_is_valid'])).sum()  # True Negative: invalid detected as invalid
    fp = ((~df['gt_is_valid']) & (df['pred_is_valid'])).sum()  # False Positive: invalid detected as valid
    fn = ((df['gt_is_valid']) & (~df['pred_is_valid'])).sum()  # False Negative: valid detected as invalid

    total = len(df)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nConfusion Matrix:")
    print(f"  True Positives (valid->valid):     {tp:4d}")
    print(f"  True Negatives (invalid->invalid): {tn:4d}")
    print(f"  False Positives (invalid->valid):  {fp:4d}")
    print(f"  False Negatives (valid->invalid):  {fn:4d}")

    print(f"\nMetrics:")
    print(f"  Accuracy:  {accuracy*100:.2f}%")
    print(f"  Precision: {precision*100:.2f}%")
    print(f"  Recall:    {recall*100:.2f}%")
    print(f"  F1 Score:  {f1*100:.2f}%")

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': int(tp),
        'tn': int(tn),
        'fp': int(fp),
        'fn': int(fn)
    }


def evaluate_extraction_accuracy(df: pd.DataFrame) -> Dict:
    """Evaluate origin and destination extraction accuracy (for valid orders only)."""
    print("\n" + "=" * 70)
    print("EXTRACTION ACCURACY (Valid Orders Only)")
    print("=" * 70)

    # Filter to only valid orders (ground truth)
    valid_df = df[df['gt_is_valid']].copy()

    # Check if origin matches
    valid_df['origin_correct'] = valid_df['gt_origin_norm'] == valid_df['pred_origin_norm']

    # Check if destination matches
    valid_df['destination_correct'] = valid_df['gt_destination_norm'] == valid_df['pred_destination_norm']

    # Check if both match (exact match)
    valid_df['exact_match'] = valid_df['origin_correct'] & valid_df['destination_correct']

    # Calculate metrics
    total_valid = len(valid_df)
    origin_accuracy = valid_df['origin_correct'].sum() / total_valid if total_valid > 0 else 0
    destination_accuracy = valid_df['destination_correct'].sum() / total_valid if total_valid > 0 else 0
    exact_match_accuracy = valid_df['exact_match'].sum() / total_valid if total_valid > 0 else 0

    print(f"\nTotal valid orders: {total_valid}")
    print(f"\nAccuracy:")
    print(f"  Origin correct:      {valid_df['origin_correct'].sum():4d} / {total_valid} ({origin_accuracy*100:.2f}%)")
    print(f"  Destination correct: {valid_df['destination_correct'].sum():4d} / {total_valid} ({destination_accuracy*100:.2f}%)")
    print(f"  Exact match (both):  {valid_df['exact_match'].sum():4d} / {total_valid} ({exact_match_accuracy*100:.2f}%)")

    return {
        'total_valid_orders': int(total_valid),
        'origin_accuracy': origin_accuracy,
        'destination_accuracy': destination_accuracy,
        'exact_match_accuracy': exact_match_accuracy,
        'origin_correct': int(valid_df['origin_correct'].sum()),
        'destination_correct': int(valid_df['destination_correct'].sum()),
        'exact_match': int(valid_df['exact_match'].sum())
    }


def analyze_by_difficulty(df: pd.DataFrame) -> Dict:
    """Analyze performance by difficulty level."""
    print("\n" + "=" * 70)
    print("PERFORMANCE BY DIFFICULTY LEVEL")
    print("=" * 70)

    # Filter to valid orders only
    valid_df = df[df['gt_is_valid']].copy()
    valid_df['exact_match'] = (valid_df['gt_origin_norm'] == valid_df['pred_origin_norm']) & \
                               (valid_df['gt_destination_norm'] == valid_df['pred_destination_norm'])

    results = {}

    for difficulty in ['easy', 'medium', 'hard']:
        subset = valid_df[valid_df['difficulty'] == difficulty]
        if len(subset) == 0:
            continue

        accuracy = subset['exact_match'].sum() / len(subset)

        print(f"\n{difficulty.upper()}:")
        print(f"  Total: {len(subset):4d} sentences")
        print(f"  Correct: {subset['exact_match'].sum():4d} ({accuracy*100:.2f}%)")

        results[difficulty] = {
            'total': int(len(subset)),
            'correct': int(subset['exact_match'].sum()),
            'accuracy': accuracy
        }

    return results


def analyze_by_category(df: pd.DataFrame) -> Dict:
    """Analyze performance by category."""
    print("\n" + "=" * 70)
    print("PERFORMANCE BY CATEGORY")
    print("=" * 70)

    # Filter to valid orders only
    valid_df = df[df['gt_is_valid']].copy()
    valid_df['exact_match'] = (valid_df['gt_origin_norm'] == valid_df['pred_origin_norm']) & \
                               (valid_df['gt_destination_norm'] == valid_df['pred_destination_norm'])

    # Group by category
    category_stats = valid_df.groupby('category').agg({
        'exact_match': ['sum', 'count', 'mean']
    }).round(4)

    # Sort by accuracy (ascending to show weaknesses first)
    category_stats = category_stats.sort_values(('exact_match', 'mean'))

    results = {}

    print("\nSorted by accuracy (lowest to highest):")
    for category, row in category_stats.iterrows():
        count = int(row[('exact_match', 'count')])
        correct = int(row[('exact_match', 'sum')])
        accuracy = row[('exact_match', 'mean')]

        print(f"  {category:25s}: {correct:3d} / {count:3d} ({accuracy*100:5.1f}%)")

        results[category] = {
            'total': count,
            'correct': correct,
            'accuracy': accuracy
        }

    return results


def collect_error_samples(df: pd.DataFrame, max_per_category: int = 5) -> Dict:
    """Collect sample errors by category."""
    print("\n" + "=" * 70)
    print("ERROR SAMPLES BY CATEGORY")
    print("=" * 70)

    # Filter to errors only (valid orders that were incorrectly extracted)
    valid_df = df[df['gt_is_valid']].copy()
    valid_df['is_error'] = (valid_df['gt_origin_norm'] != valid_df['pred_origin_norm']) | \
                            (valid_df['gt_destination_norm'] != valid_df['pred_destination_norm'])

    errors_df = valid_df[valid_df['is_error']]

    error_samples = {}

    # Get samples by category
    for category in errors_df['category'].unique():
        category_errors = errors_df[errors_df['category'] == category]
        samples = []

        for _, row in category_errors.head(max_per_category).iterrows():
            samples.append({
                'sentenceID': int(row['sentenceID']),
                'sentence': row['sentence'],
                'gt_origin': row['origin'] if pd.notna(row['origin']) else '',
                'gt_destination': row['destination'] if pd.notna(row['destination']) else '',
                'pred_origin': row['pred_origin_norm'].title() if row['pred_origin_norm'] != 'invalid' else 'INVALID',
                'pred_destination': row['pred_destination_norm'].title() if row['pred_destination_norm'] != 'invalid' else 'INVALID'
            })

        if samples:
            error_samples[category] = samples

    # Print samples
    for category, samples in sorted(error_samples.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{category.upper()} ({len(samples)} samples shown):")
        for sample in samples[:3]:  # Show max 3 in console
            print(f"  ID {sample['sentenceID']}: {sample['sentence']}")
            print(f"    Expected: {sample['gt_origin']} -> {sample['gt_destination']}")
            print(f"    Predicted: {sample['pred_origin']} -> {sample['pred_destination']}")

    return error_samples


def generate_report(metrics: Dict, output_dir: str):
    """Generate JSON and text reports."""
    print("\n" + "=" * 70)
    print("GENERATING REPORTS")
    print("=" * 70)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save JSON report
    json_file = output_path / "baseline_validation_metrics.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] JSON report saved to: {json_file}")

    # Save text report
    text_file = output_path / "baseline_validation_report.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("BASELINE VALIDATION REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total sentences: {metrics['validity_detection']['tp'] + metrics['validity_detection']['tn'] + metrics['validity_detection']['fp'] + metrics['validity_detection']['fn']}\n")
        f.write(f"Validity detection accuracy: {metrics['validity_detection']['accuracy']*100:.2f}%\n")
        f.write(f"Extraction accuracy (valid orders): {metrics['extraction_accuracy']['exact_match_accuracy']*100:.2f}%\n\n")

        f.write("VALIDITY DETECTION\n")
        f.write("-" * 70 + "\n")
        f.write(f"Accuracy:  {metrics['validity_detection']['accuracy']*100:.2f}%\n")
        f.write(f"Precision: {metrics['validity_detection']['precision']*100:.2f}%\n")
        f.write(f"Recall:    {metrics['validity_detection']['recall']*100:.2f}%\n")
        f.write(f"F1 Score:  {metrics['validity_detection']['f1']*100:.2f}%\n\n")

        f.write("EXTRACTION ACCURACY (Valid Orders Only)\n")
        f.write("-" * 70 + "\n")
        f.write(f"Origin accuracy:      {metrics['extraction_accuracy']['origin_accuracy']*100:.2f}%\n")
        f.write(f"Destination accuracy: {metrics['extraction_accuracy']['destination_accuracy']*100:.2f}%\n")
        f.write(f"Exact match accuracy: {metrics['extraction_accuracy']['exact_match_accuracy']*100:.2f}%\n\n")

        f.write("BY DIFFICULTY LEVEL\n")
        f.write("-" * 70 + "\n")
        for difficulty, stats in metrics['by_difficulty'].items():
            f.write(f"{difficulty.upper()}: {stats['accuracy']*100:.2f}% ({stats['correct']}/{stats['total']})\n")

        f.write("\nBY CATEGORY (Top 10 Weaknesses)\n")
        f.write("-" * 70 + "\n")
        sorted_categories = sorted(metrics['by_category'].items(), key=lambda x: x[1]['accuracy'])
        for category, stats in sorted_categories[:10]:
            f.write(f"{category:30s}: {stats['accuracy']*100:5.1f}% ({stats['correct']}/{stats['total']})\n")

    print(f"[OK] Text report saved to: {text_file}")

    # Save error samples
    errors_file = output_path / "baseline_validation_errors.json"
    with open(errors_file, 'w', encoding='utf-8') as f:
        json.dump(metrics['error_samples'], f, indent=2, ensure_ascii=False)
    print(f"[OK] Error samples saved to: {errors_file}")


def main():
    """Main evaluation function."""
    print("=" * 70)
    print("BASELINE VALIDATION EVALUATION")
    print("=" * 70)
    print()

    # File paths
    gt_file = "data/val.csv"
    pred_file = "results/baseline_validation_output.csv"
    output_dir = "results"

    # Load data
    gt_df = load_ground_truth(gt_file)
    pred_df = load_predictions(pred_file)

    # Merge
    merged_df = merge_data(gt_df, pred_df)

    # Evaluate
    metrics = {}
    metrics['validity_detection'] = evaluate_validity_detection(merged_df)
    metrics['extraction_accuracy'] = evaluate_extraction_accuracy(merged_df)
    metrics['by_difficulty'] = analyze_by_difficulty(merged_df)
    metrics['by_category'] = analyze_by_category(merged_df)
    metrics['error_samples'] = collect_error_samples(merged_df, max_per_category=10)

    # Generate reports
    generate_report(metrics, output_dir)

    # Summary
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"\nKey Metrics:")
    print(f"  Validity Detection: {metrics['validity_detection']['accuracy']*100:.2f}%")
    print(f"  Extraction Accuracy: {metrics['extraction_accuracy']['exact_match_accuracy']*100:.2f}%")
    print(f"  Easy:   {metrics['by_difficulty']['easy']['accuracy']*100:.2f}%")
    print(f"  Medium: {metrics['by_difficulty']['medium']['accuracy']*100:.2f}%")
    print(f"  Hard:   {metrics['by_difficulty']['hard']['accuracy']*100:.2f}%")
    print()


if __name__ == "__main__":
    main()
