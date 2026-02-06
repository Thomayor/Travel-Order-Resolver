"""
Evaluation Script for CamemBERT NER Model

Evaluates the fine-tuned CamemBERT model and compares with baseline.

Usage:
    python scripts/evaluate_camembert.py

Output:
    - results/camembert_evaluation.json: Detailed metrics
    - results/camembert_errors.csv: Error analysis
    - Console: Comparison with baseline performance
"""

import sys
import json
import csv
from pathlib import Path
from collections import defaultdict

# Add src to path (3 levels up: evaluate_camembert.py -> camembert -> scripts -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nlp.transformer import load_pretrained_model
from nlp.baseline import BaselineExtractor
from nlp.gazetteer import load_gazetteer
from nlp.postprocessing import extract_entities


def fuzzy_match_cities(predicted: str, expected: str, gazetteer) -> bool:
    """
    Check if predicted city matches expected city using fuzzy matching.

    Args:
        predicted: City name predicted by model (may be misspelled)
        expected: Expected city name from ground truth
        gazetteer: Gazetteer instance for fuzzy matching

    Returns:
        True if cities match (exact or fuzzy), False otherwise
    """
    if not predicted or not expected:
        return predicted == expected

    # Exact match (case-insensitive)
    if predicted.lower().strip() == expected.lower().strip():
        return True

    # Try fuzzy match: check if predicted resolves to expected
    matches = gazetteer.fuzzy_match(predicted, max_distance=3)
    if matches:
        for match_city, _ in matches:
            if match_city.lower().strip() == expected.lower().strip():
                return True

    return False


def load_test_data(test_path: str):
    """Load test data from NER JSON."""
    with open(test_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def evaluate_baseline(test_data, gazetteer):
    """Evaluate baseline model on test data."""
    baseline = BaselineExtractor(gazetteer)

    correct = 0
    total = 0
    valid_examples = 0

    # Performance by category and difficulty
    by_category = defaultdict(lambda: {'correct': 0, 'total': 0})
    by_difficulty = defaultdict(lambda: {'correct': 0, 'total': 0})

    for example in test_data:
        metadata = example['metadata']

        # Skip invalid examples for accuracy calculation
        if metadata['is_valid'] == 0:
            continue

        valid_examples += 1
        total += 1

        # Reconstruct sentence from tokens
        sentence = ' '.join(example['tokens'])

        # Predict with baseline
        result = baseline.extract(sentence)

        # Check if correct (with fuzzy matching for misspellings)
        expected_origin = metadata['origin'].strip()
        expected_dest = metadata['destination'].strip()

        origin_match = fuzzy_match_cities(result['origin'], expected_origin, gazetteer)
        dest_match = fuzzy_match_cities(result['destination'], expected_dest, gazetteer)
        is_correct = origin_match and dest_match

        if is_correct:
            correct += 1

        # Track by category
        category = metadata.get('category', 'unknown')
        by_category[category]['total'] += 1
        if is_correct:
            by_category[category]['correct'] += 1

        # Track by difficulty
        difficulty = metadata.get('difficulty', 'unknown')
        by_difficulty[difficulty]['total'] += 1
        if is_correct:
            by_difficulty[difficulty]['correct'] += 1

    accuracy = correct / total if total > 0 else 0

    return {
        'accuracy': accuracy,
        'correct': correct,
        'total': total,
        'by_category': dict(by_category),
        'by_difficulty': dict(by_difficulty)
    }


def evaluate_camembert(model, test_data, gazetteer):
    """Evaluate CamemBERT model on test data."""
    correct = 0
    total = 0
    valid_examples = 0

    # Performance by category and difficulty
    by_category = defaultdict(lambda: {'correct': 0, 'total': 0})
    by_difficulty = defaultdict(lambda: {'correct': 0, 'total': 0})

    # Store errors for analysis
    errors = []

    for example in test_data:
        metadata = example['metadata']

        # Skip invalid examples for accuracy calculation
        if metadata['is_valid'] == 0:
            continue

        valid_examples += 1
        total += 1

        # Reconstruct sentence from tokens
        sentence = ' '.join(example['tokens'])

        # Predict with CamemBERT
        try:
            _, predicted_labels, pred_origin, pred_dest = model.predict(sentence)
        except Exception as e:
            print(f"Error predicting: {e}")
            pred_origin = None
            pred_dest = None

        # Check if correct (with fuzzy matching for misspellings)
        expected_origin = metadata['origin'].strip()
        expected_dest = metadata['destination'].strip()

        origin_match = fuzzy_match_cities(pred_origin, expected_origin, gazetteer)
        dest_match = fuzzy_match_cities(pred_dest, expected_dest, gazetteer)
        is_correct = origin_match and dest_match

        if is_correct:
            correct += 1
        else:
            # Store error
            errors.append({
                'sentenceID': metadata['sentenceID'],
                'sentence': sentence,
                'expected_origin': expected_origin,
                'expected_dest': expected_dest,
                'predicted_origin': pred_origin or '',
                'predicted_dest': pred_dest or '',
                'category': metadata.get('category', ''),
                'difficulty': metadata.get('difficulty', '')
            })

        # Track by category
        category = metadata.get('category', 'unknown')
        by_category[category]['total'] += 1
        if is_correct:
            by_category[category]['correct'] += 1

        # Track by difficulty
        difficulty = metadata.get('difficulty', 'unknown')
        by_difficulty[difficulty]['total'] += 1
        if is_correct:
            by_difficulty[difficulty]['correct'] += 1

    accuracy = correct / total if total > 0 else 0

    return {
        'accuracy': accuracy,
        'correct': correct,
        'total': total,
        'by_category': dict(by_category),
        'by_difficulty': dict(by_difficulty),
        'errors': errors
    }


def print_comparison(baseline_results, camembert_results):
    """Print comparison table between baseline and CamemBERT."""
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON: Baseline vs CamemBERT")
    print("=" * 80)

    # Overall accuracy
    print("\nOverall Accuracy:")
    print(f"  Baseline:   {baseline_results['accuracy']*100:.2f}%")
    print(f"  CamemBERT:  {camembert_results['accuracy']*100:.2f}%")
    print(f"  Improvement: {(camembert_results['accuracy'] - baseline_results['accuracy'])*100:+.2f}%")

    # By difficulty
    print("\nPerformance by Difficulty:")
    print(f"  {'Difficulty':<15} {'Baseline':<15} {'CamemBERT':<15} {'Improvement':<15}")
    print(f"  {'-'*15} {'-'*15} {'-'*15} {'-'*15}")

    for difficulty in ['easy', 'medium', 'hard']:
        base_stats = baseline_results['by_difficulty'].get(difficulty, {'correct': 0, 'total': 0})
        camem_stats = camembert_results['by_difficulty'].get(difficulty, {'correct': 0, 'total': 0})

        base_acc = base_stats['correct'] / base_stats['total'] if base_stats['total'] > 0 else 0
        camem_acc = camem_stats['correct'] / camem_stats['total'] if camem_stats['total'] > 0 else 0

        print(f"  {difficulty:<15} {base_acc*100:<14.2f}% {camem_acc*100:<14.2f}% {(camem_acc - base_acc)*100:+.2f}%")

    # By category (top categories)
    print("\nPerformance by Category (Top 5 by volume):")
    print(f"  {'Category':<20} {'Baseline':<15} {'CamemBERT':<15} {'Improvement':<15}")
    print(f"  {'-'*20} {'-'*15} {'-'*15} {'-'*15}")

    # Sort categories by total count
    categories = sorted(
        camembert_results['by_category'].items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )[:5]

    for category, camem_stats in categories:
        base_stats = baseline_results['by_category'].get(category, {'correct': 0, 'total': 0})

        base_acc = base_stats['correct'] / base_stats['total'] if base_stats['total'] > 0 else 0
        camem_acc = camem_stats['correct'] / camem_stats['total'] if camem_stats['total'] > 0 else 0

        print(f"  {category:<20} {base_acc*100:<14.2f}% {camem_acc*100:<14.2f}% {(camem_acc - base_acc)*100:+.2f}%")


def save_results(camembert_results, output_path):
    """Save detailed results to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(camembert_results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to: {output_path}")


def save_errors(errors, output_path):
    """Save error analysis to CSV."""
    if not errors:
        print("\nNo errors to save (100% accuracy!)")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['sentenceID', 'sentence', 'expected_origin', 'expected_dest',
                      'predicted_origin', 'predicted_dest', 'category', 'difficulty']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(errors)

    print(f"Error analysis saved to: {output_path}")


def main():
    print("=" * 80)
    print("CamemBERT NER Model Evaluation")
    print("=" * 80)

    # Paths
    test_path = project_root / 'data' / 'processed' / 'test_ner.json'
    model_path = project_root / 'models' / 'camembert-ner'
    results_dir = project_root / 'results'
    results_dir.mkdir(exist_ok=True)

    # Check if test data exists
    if not test_path.exists():
        print(f"\nError: Test data not found at {test_path}")
        print("\nPlease run the conversion script first:")
        print("  python scripts/convert_dataset_to_ner.py")
        sys.exit(1)

    # Check if model exists
    if not model_path.exists():
        print(f"\nError: Model not found at {model_path}")
        print("\nPlease train the model first:")
        print("  python scripts/train_camembert.py")
        sys.exit(1)

    print(f"\nLoading test data from: {test_path}")
    test_data = load_test_data(str(test_path))
    print(f"Test examples: {len(test_data)}")

    # Evaluate baseline
    print("\nEvaluating baseline model...")
    gazetteer = load_gazetteer()
    baseline_results = evaluate_baseline(test_data, gazetteer)
    print(f"Baseline accuracy: {baseline_results['accuracy']*100:.2f}%")

    # Load CamemBERT model
    print(f"\nLoading CamemBERT model from: {model_path}")
    camembert_model = load_pretrained_model(str(model_path))

    # Evaluate CamemBERT (with fuzzy matching)
    print("\nEvaluating CamemBERT model...")
    camembert_results = evaluate_camembert(camembert_model, test_data, gazetteer)
    print(f"CamemBERT accuracy: {camembert_results['accuracy']*100:.2f}%")

    # Print comparison
    print_comparison(baseline_results, camembert_results)

    # Save results
    results_path = results_dir / 'camembert_evaluation.json'
    save_results(camembert_results, str(results_path))

    # Save errors
    errors_path = results_dir / 'camembert_errors.csv'
    save_errors(camembert_results['errors'], str(errors_path))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nCamemBERT Model Performance:")
    print(f"  Accuracy: {camembert_results['accuracy']*100:.2f}%")
    print(f"  Correct: {camembert_results['correct']} / {camembert_results['total']}")
    print(f"  Errors: {len(camembert_results['errors'])}")

    improvement = (camembert_results['accuracy'] - baseline_results['accuracy']) * 100
    print(f"\nImprovement over Baseline: {improvement:+.2f}%")

    # Check if target achieved
    if camembert_results['accuracy'] >= 0.85:
        print("\nTarget achieved! (>= 85% accuracy)")
    else:
        print(f"\nTarget not yet achieved. Need {(0.85 - camembert_results['accuracy'])*100:.2f}% more.")


if __name__ == '__main__':
    main()
