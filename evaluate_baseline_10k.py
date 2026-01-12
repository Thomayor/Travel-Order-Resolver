#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate baseline NLP model on 10K dataset

This script tests the rule-based baseline model on the complete 10,000-sentence
dataset and generates comprehensive performance metrics.
"""

import csv
import sys
import json
from collections import Counter, defaultdict

# Import NLP modules
from src.nlp.baseline import BaselineExtractor, load_extractor
from src.nlp.gazetteer import Gazetteer


def load_dataset(filename):
    """Load dataset from CSV"""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def evaluate_extraction(sentence, expected_origin, expected_dest, extractor):
    """
    Evaluate a single sentence extraction

    Returns:
        dict: {
            'predicted_origin': str,
            'predicted_dest': str,
            'origin_correct': bool,
            'dest_correct': bool,
            'both_correct': bool,
            'is_valid': bool
        }
    """

    # Extract using baseline model
    result = extractor.extract(sentence)

    predicted_origin = result.get('origin', '') or ''
    predicted_dest = result.get('destination', '') or ''

    # Normalize for comparison (handle None, empty strings)
    def normalize(val):
        if val is None or val == '':
            return ''
        return val.strip()

    pred_origin_norm = normalize(predicted_origin)
    pred_dest_norm = normalize(predicted_dest)
    exp_origin_norm = normalize(expected_origin)
    exp_dest_norm = normalize(expected_dest)

    # Check correctness
    origin_correct = pred_origin_norm == exp_origin_norm
    dest_correct = pred_dest_norm == exp_dest_norm
    both_correct = origin_correct and dest_correct

    # Check if model thinks it's valid (has both origin and dest)
    is_valid = bool(predicted_origin) and bool(predicted_dest)

    return {
        'predicted_origin': predicted_origin,
        'predicted_dest': predicted_dest,
        'origin_correct': origin_correct,
        'dest_correct': dest_correct,
        'both_correct': both_correct,
        'is_valid': is_valid
    }


def calculate_metrics(results, dataset):
    """Calculate comprehensive evaluation metrics"""

    metrics = {
        'total': len(results),
        'valid_orders': 0,
        'invalid_orders': 0,

        # Overall accuracy
        'correct_extractions': 0,
        'accuracy': 0.0,

        # Per-component accuracy
        'origin_correct_count': 0,
        'dest_correct_count': 0,
        'origin_accuracy': 0.0,
        'dest_accuracy': 0.0,

        # Classification metrics (valid vs invalid detection)
        'true_positive': 0,   # Correctly identified as valid
        'true_negative': 0,   # Correctly identified as invalid
        'false_positive': 0,  # Incorrectly identified as valid (should be invalid)
        'false_negative': 0,  # Incorrectly identified as invalid (should be valid)

        # Per-category performance
        'by_category': defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'accuracy': 0.0
        }),

        # Per-difficulty performance (valid orders only)
        'by_difficulty': defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'accuracy': 0.0
        }),

        # Error analysis
        'error_types': Counter(),
        'difficult_sentences': []
    }

    for i, (phrase, result) in enumerate(zip(dataset, results)):
        is_valid_expected = phrase['is_valid'] == '1'
        is_valid_predicted = result['is_valid']

        if is_valid_expected:
            metrics['valid_orders'] += 1
        else:
            metrics['invalid_orders'] += 1

        # Overall accuracy (both origin and dest correct)
        if result['both_correct']:
            metrics['correct_extractions'] += 1

        # Per-component accuracy
        if result['origin_correct']:
            metrics['origin_correct_count'] += 1
        if result['dest_correct']:
            metrics['dest_correct_count'] += 1

        # Classification metrics
        if is_valid_expected and is_valid_predicted:
            metrics['true_positive'] += 1
        elif not is_valid_expected and not is_valid_predicted:
            metrics['true_negative'] += 1
        elif not is_valid_expected and is_valid_predicted:
            metrics['false_positive'] += 1
        elif is_valid_expected and not is_valid_predicted:
            metrics['false_negative'] += 1

        # Per-category performance
        category = phrase['category']
        metrics['by_category'][category]['total'] += 1
        if result['both_correct']:
            metrics['by_category'][category]['correct'] += 1

        # Per-difficulty performance (valid orders only)
        if is_valid_expected:
            difficulty = phrase.get('difficulty', 'unknown')
            metrics['by_difficulty'][difficulty]['total'] += 1
            if result['both_correct']:
                metrics['by_difficulty'][difficulty]['correct'] += 1

        # Error analysis
        if not result['both_correct']:
            error_type = 'unknown'

            if not result['origin_correct'] and not result['dest_correct']:
                error_type = 'both_wrong'
            elif not result['origin_correct']:
                error_type = 'origin_wrong'
            elif not result['dest_correct']:
                error_type = 'dest_wrong'

            metrics['error_types'][error_type] += 1

            # Track difficult sentences
            if is_valid_expected and phrase.get('difficulty') == 'hard':
                metrics['difficult_sentences'].append({
                    'sentence': phrase['sentence'],
                    'expected_origin': phrase['origin'],
                    'expected_dest': phrase['destination'],
                    'predicted_origin': result['predicted_origin'],
                    'predicted_dest': result['predicted_dest'],
                    'category': category
                })

    # Calculate percentages
    if metrics['total'] > 0:
        metrics['accuracy'] = (metrics['correct_extractions'] / metrics['total']) * 100

    if metrics['valid_orders'] > 0:
        metrics['origin_accuracy'] = (metrics['origin_correct_count'] / metrics['valid_orders']) * 100
        metrics['dest_accuracy'] = (metrics['dest_correct_count'] / metrics['valid_orders']) * 100

    # Calculate per-category accuracies
    for category in metrics['by_category']:
        total = metrics['by_category'][category]['total']
        correct = metrics['by_category'][category]['correct']
        if total > 0:
            metrics['by_category'][category]['accuracy'] = (correct / total) * 100

    # Calculate per-difficulty accuracies
    for difficulty in metrics['by_difficulty']:
        total = metrics['by_difficulty'][difficulty]['total']
        correct = metrics['by_difficulty'][difficulty]['correct']
        if total > 0:
            metrics['by_difficulty'][difficulty]['accuracy'] = (correct / total) * 100

    # Calculate precision, recall, F1 for valid order detection
    if (metrics['true_positive'] + metrics['false_positive']) > 0:
        metrics['precision'] = metrics['true_positive'] / (metrics['true_positive'] + metrics['false_positive'])
    else:
        metrics['precision'] = 0.0

    if (metrics['true_positive'] + metrics['false_negative']) > 0:
        metrics['recall'] = metrics['true_positive'] / (metrics['true_positive'] + metrics['false_negative'])
    else:
        metrics['recall'] = 0.0

    if (metrics['precision'] + metrics['recall']) > 0:
        metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
    else:
        metrics['f1_score'] = 0.0

    return metrics


def print_evaluation_report(metrics):
    """Print comprehensive evaluation report"""

    report = []
    report.append("=" * 80)
    report.append("BASELINE MODEL EVALUATION - 10K DATASET")
    report.append("=" * 80)
    report.append("")

    # Overall metrics
    report.append("OVERALL PERFORMANCE")
    report.append("-" * 80)
    report.append(f"Total sentences evaluated: {metrics['total']:,}")
    report.append(f"  - Valid orders: {metrics['valid_orders']:,} ({metrics['valid_orders']/metrics['total']*100:.1f}%)")
    report.append(f"  - Invalid orders: {metrics['invalid_orders']:,} ({metrics['invalid_orders']/metrics['total']*100:.1f}%)")
    report.append("")
    report.append(f"Correct extractions (both origin & dest): {metrics['correct_extractions']:,} / {metrics['total']:,}")
    report.append(f"OVERALL ACCURACY: {metrics['accuracy']:.2f}%")
    report.append("")

    # Component-wise accuracy (valid orders only)
    report.append("COMPONENT-WISE ACCURACY (Valid Orders Only)")
    report.append("-" * 80)
    report.append(f"Origin correct: {metrics['origin_correct_count']:,} / {metrics['valid_orders']:,} ({metrics['origin_accuracy']:.2f}%)")
    report.append(f"Destination correct: {metrics['dest_correct_count']:,} / {metrics['valid_orders']:,} ({metrics['dest_accuracy']:.2f}%)")
    report.append("")

    # Classification metrics
    report.append("CLASSIFICATION METRICS (Valid vs Invalid Detection)")
    report.append("-" * 80)
    report.append(f"True Positives (correctly identified as valid):  {metrics['true_positive']:,}")
    report.append(f"True Negatives (correctly identified as invalid): {metrics['true_negative']:,}")
    report.append(f"False Positives (invalid marked as valid):        {metrics['false_positive']:,}")
    report.append(f"False Negatives (valid marked as invalid):        {metrics['false_negative']:,}")
    report.append("")
    report.append(f"Precision: {metrics['precision']:.4f}")
    report.append(f"Recall:    {metrics['recall']:.4f}")
    report.append(f"F1 Score:  {metrics['f1_score']:.4f}")
    report.append("")

    # Per-category performance
    report.append("PERFORMANCE BY CATEGORY")
    report.append("-" * 80)

    # Sort categories by type (valid vs invalid)
    valid_categories = ['standard', 'inverted_order', 'no_markers', 'name_ambiguity',
                       'compound_name', 'misspelling', 'no_capitals', 'additional_info',
                       'complex_question']
    invalid_categories = ['no_intent', 'incomplete_origin', 'incomplete_dest',
                         'incomplete_grammar', 'garbage', 'ambiguous']

    report.append("\nValid Order Categories:")
    for cat in valid_categories:
        if cat in metrics['by_category']:
            stats = metrics['by_category'][cat]
            report.append(f"  {cat:25s}: {stats['correct']:4d}/{stats['total']:4d} ({stats['accuracy']:6.2f}%)")

    report.append("\nInvalid Order Categories:")
    for cat in invalid_categories:
        if cat in metrics['by_category']:
            stats = metrics['by_category'][cat]
            report.append(f"  {cat:25s}: {stats['correct']:4d}/{stats['total']:4d} ({stats['accuracy']:6.2f}%)")
    report.append("")

    # Per-difficulty performance
    report.append("PERFORMANCE BY DIFFICULTY (Valid Orders Only)")
    report.append("-" * 80)
    for difficulty in ['easy', 'medium', 'hard']:
        if difficulty in metrics['by_difficulty']:
            stats = metrics['by_difficulty'][difficulty]
            report.append(f"  {difficulty:10s}: {stats['correct']:4d}/{stats['total']:4d} ({stats['accuracy']:6.2f}%)")
    report.append("")

    # Error analysis
    report.append("ERROR ANALYSIS")
    report.append("-" * 80)
    total_errors = sum(metrics['error_types'].values())
    for error_type, count in metrics['error_types'].most_common():
        pct = (count / total_errors) * 100 if total_errors > 0 else 0
        report.append(f"  {error_type:20s}: {count:5d} ({pct:5.1f}%)")
    report.append("")

    # Sample difficult sentences
    if metrics['difficult_sentences']:
        report.append("SAMPLE DIFFICULT SENTENCES (Hard Valid Orders with Errors)")
        report.append("-" * 80)
        for i, example in enumerate(metrics['difficult_sentences'][:10], 1):
            report.append(f"\n{i}. Sentence: {example['sentence']}")
            report.append(f"   Category: {example['category']}")
            report.append(f"   Expected: {example['expected_origin']} → {example['expected_dest']}")
            report.append(f"   Predicted: {example['predicted_origin']} → {example['predicted_dest']}")

        if len(metrics['difficult_sentences']) > 10:
            report.append(f"\n   ... and {len(metrics['difficult_sentences']) - 10} more difficult cases")
        report.append("")

    report.append("=" * 80)
    report.append("END OF EVALUATION REPORT")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main evaluation function"""

    print("\n" + "=" * 80)
    print("BASELINE MODEL EVALUATION ON 10K DATASET")
    print("=" * 80 + "\n")

    # Initialize baseline extractor
    print("Initializing baseline extractor...")
    extractor = load_extractor()
    print(f"  Loaded {len(extractor.gazetteer.cities)} cities")
    print(f"  Loaded {len(extractor.gazetteer.stations)} stations")

    # Load dataset
    print("\nLoading dataset...")
    dataset = load_dataset('data/dataset_final.csv')
    print(f"  Loaded {len(dataset)} sentences")

    # Evaluate each sentence
    print("\nEvaluating baseline model on all sentences...")
    results = []

    for i, phrase in enumerate(dataset, 1):
        if i % 1000 == 0:
            print(f"  Progress: {i}/{len(dataset)} ({i/len(dataset)*100:.1f}%)")

        sentence = phrase['sentence']
        expected_origin = phrase['origin']
        expected_dest = phrase['destination']

        result = evaluate_extraction(sentence, expected_origin, expected_dest, extractor)
        results.append(result)

    print(f"  Completed: {len(results)}/{len(dataset)} (100.0%)")

    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = calculate_metrics(results, dataset)

    # Generate report
    print("\nGenerating evaluation report...")
    report = print_evaluation_report(metrics)

    # Save text report
    with open('evaluation_baseline_10k.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("[OK] Text report saved to: evaluation_baseline_10k.txt")

    # Save JSON metrics
    json_metrics = {
        'dataset': 'dataset_final.csv',
        'total_sentences': metrics['total'],
        'accuracy': round(metrics['accuracy'], 2),
        'origin_accuracy': round(metrics['origin_accuracy'], 2),
        'dest_accuracy': round(metrics['dest_accuracy'], 2),
        'precision': round(metrics['precision'], 4),
        'recall': round(metrics['recall'], 4),
        'f1_score': round(metrics['f1_score'], 4),
        'classification': {
            'true_positive': metrics['true_positive'],
            'true_negative': metrics['true_negative'],
            'false_positive': metrics['false_positive'],
            'false_negative': metrics['false_negative']
        },
        'by_category': {k: {'total': v['total'], 'correct': v['correct'], 'accuracy': round(v['accuracy'], 2)}
                       for k, v in metrics['by_category'].items()},
        'by_difficulty': {k: {'total': v['total'], 'correct': v['correct'], 'accuracy': round(v['accuracy'], 2)}
                         for k, v in metrics['by_difficulty'].items()},
        'error_types': dict(metrics['error_types'])
    }

    with open('evaluation_baseline_10k.json', 'w', encoding='utf-8') as f:
        json.dump(json_metrics, f, indent=2, ensure_ascii=False)
    print("[OK] JSON metrics saved to: evaluation_baseline_10k.json")

    # Print report to console
    print("\n" + report)

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print("\nKey findings:")
    print(f"  - Overall accuracy: {metrics['accuracy']:.2f}%")
    print(f"  - Origin accuracy: {metrics['origin_accuracy']:.2f}%")
    print(f"  - Destination accuracy: {metrics['dest_accuracy']:.2f}%")
    print(f"  - F1 Score (valid detection): {metrics['f1_score']:.4f}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
