"""
Demo: Evaluation Metrics Module

This script demonstrates how to use the evaluation metrics module
to evaluate NLP model performance on the Travel Order Resolver task.

Usage:
    python scripts/demos/demo_evaluation_metrics.py
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.metrics import (
    calculate_accuracy,
    calculate_precision_recall_f1,
    generate_confusion_matrix,
    evaluate_robustness,
    evaluate_model
)
from src.evaluation.report_template import (
    generate_text_report,
    generate_json_report,
    generate_markdown_report,
    save_report
)


def create_sample_data():
    """Create sample predictions and ground truth for demo."""
    # Sample ground truth
    ground_truth = pd.DataFrame({
        'sentenceID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'sentence': [
            'Je veux aller de Paris à Lyon',
            'Billet Marseille Nice',
            'trajet tours reeims',  # Misspelling
            'Soit Toulouse soit Nice',  # Ambiguous
            'Comment aller à Bordeaux',  # Incomplete
            'Un train de Lille à Strasbourg',
            'Je pars de grenoble',  # Incomplete
            'Billet Aix-en-Provence Montpellier',  # Compound name
            'keneq gulyrosado',  # Garbage
            'De Nantes vers Rennes'
        ],
        'origin': ['Paris', 'Marseille', 'Tours', '', '', 'Lille', '', 'Aix-en-Provence', '', 'Nantes'],
        'destination': ['Lyon', 'Nice', 'Reims', '', '', 'Strasbourg', '', 'Montpellier', '', 'Rennes'],
        'is_valid': [1, 1, 1, 0, 0, 1, 0, 1, 0, 1],
        'difficulty': ['easy', 'medium', 'hard', 'medium', 'easy', 'easy', 'easy', 'hard', 'easy', 'medium'],
        'category': ['standard', 'no_markers', 'misspelling', 'ambiguous', 'incomplete_dest',
                    'standard', 'incomplete_dest', 'compound_name', 'garbage', 'standard']
    })

    # Sample predictions (baseline model)
    predictions = pd.DataFrame({
        'sentenceID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'origin': ['Paris', 'Marseille', 'INVALID', 'Nice', 'INVALID', 'Lille', 'INVALID', 'INVALID', 'INVALID', 'Nantes'],
        'destination': ['Lyon', 'Nice', 'Tours', 'Toulouse', 'Bordeaux', 'Strasbourg', 'Grenoble', 'Montpellier', 'INVALID', 'Rennes']
    })

    return predictions, ground_truth


def demo_individual_metrics():
    """Demonstrate individual metric calculations."""
    print("=" * 70)
    print("DEMO: INDIVIDUAL METRICS")
    print("=" * 70)
    print()

    predictions, ground_truth = create_sample_data()

    print("Sample Data:")
    print("-" * 70)
    print("\nGround Truth (first 5):")
    print(ground_truth[['sentenceID', 'sentence', 'origin', 'destination', 'is_valid']].head())
    print("\nPredictions (first 5):")
    print(predictions.head())
    print()

    # 1. Accuracy
    print("\n1. ACCURACY METRICS")
    print("-" * 70)
    accuracy_result = calculate_accuracy(predictions, ground_truth)
    print(f"Origin Accuracy:      {accuracy_result.origin_accuracy*100:.2f}%")
    print(f"Destination Accuracy: {accuracy_result.destination_accuracy*100:.2f}%")
    print(f"Exact Match Accuracy: {accuracy_result.exact_match_accuracy*100:.2f}%")
    print(f"  ({accuracy_result.exact_match}/{accuracy_result.total_valid_orders} correct)")

    # 2. Precision/Recall/F1
    print("\n2. PRECISION/RECALL/F1 (Validity Detection)")
    print("-" * 70)
    pr_result = calculate_precision_recall_f1(predictions, ground_truth)
    print(f"Precision: {pr_result.validity_precision*100:.2f}%")
    print(f"Recall:    {pr_result.validity_recall*100:.2f}%")
    print(f"F1 Score:  {pr_result.validity_f1*100:.2f}%")

    # 3. Confusion Matrix
    print("\n3. CONFUSION MATRIX")
    print("-" * 70)
    cm = generate_confusion_matrix(predictions, ground_truth)
    print("Confusion Matrix:")
    print(f"  [[TN={cm[0,0]:2d}, FP={cm[0,1]:2d}],")
    print(f"   [FN={cm[1,0]:2d}, TP={cm[1,1]:2d}]]")
    print("\nInterpretation:")
    print(f"  True Negatives:  {cm[0,0]:2d} (invalid correctly detected)")
    print(f"  False Positives: {cm[0,1]:2d} (invalid wrongly detected as valid)")
    print(f"  False Negatives: {cm[1,0]:2d} (valid wrongly detected as invalid)")
    print(f"  True Positives:  {cm[1,1]:2d} (valid correctly detected)")

    # 4. Robustness
    print("\n4. ROBUSTNESS METRICS")
    print("-" * 70)
    robustness = evaluate_robustness(predictions, ground_truth)
    for category, score in sorted(robustness.items()):
        if score is not None:
            print(f"  {category:25s}: {score*100:5.1f}%")


def demo_comprehensive_evaluation():
    """Demonstrate comprehensive model evaluation."""
    print("\n" + "=" * 70)
    print("DEMO: COMPREHENSIVE EVALUATION")
    print("=" * 70)
    print()

    predictions, ground_truth = create_sample_data()

    # Evaluate model
    result = evaluate_model(predictions, ground_truth)

    print("Complete Evaluation Result:")
    print("-" * 70)
    print(f"\nValidity Detection:")
    print(f"  Accuracy:  {result.validity_accuracy*100:.2f}%")
    print(f"  Precision: {result.validity_precision*100:.2f}%")
    print(f"  Recall:    {result.validity_recall*100:.2f}%")
    print(f"  F1:        {result.validity_f1*100:.2f}%")

    print(f"\nExtraction Accuracy:")
    print(f"  Origin:      {result.origin_accuracy*100:.2f}%")
    print(f"  Destination: {result.destination_accuracy*100:.2f}%")
    print(f"  Exact Match: {result.exact_match_accuracy*100:.2f}%")

    print(f"\nBy Difficulty:")
    for difficulty, stats in result.by_difficulty.items():
        print(f"  {difficulty.capitalize():6s}: {stats['accuracy']*100:.2f}% ({stats['correct']}/{stats['total']})")

    print(f"\nBy Category:")
    for category, stats in sorted(result.by_category.items(), key=lambda x: x[1]['accuracy']):
        print(f"  {category:20s}: {stats['accuracy']*100:.2f}% ({stats['correct']}/{stats['total']})")


def demo_report_generation():
    """Demonstrate report generation."""
    print("\n" + "=" * 70)
    print("DEMO: REPORT GENERATION")
    print("=" * 70)
    print()

    predictions, ground_truth = create_sample_data()

    # Evaluate
    result = evaluate_model(predictions, ground_truth)

    # Generate text report
    print("\n1. TEXT REPORT:")
    print("-" * 70)
    text_report = generate_text_report(
        result,
        model_name="Demo Baseline Model",
        dataset_name="Sample Dataset (10 sentences)",
        additional_info={'Note': 'This is a demo with synthetic data'}
    )
    print(text_report)

    # Show JSON snippet
    print("\n2. JSON REPORT (snippet):")
    print("-" * 70)
    json_report = generate_json_report(result, "Demo Model", "Sample")
    print(json_report[:500] + "...")

    # Show Markdown snippet
    print("\n3. MARKDOWN REPORT (first few lines):")
    print("-" * 70)
    md_report = generate_markdown_report(result, "Demo Model", "Sample")
    print("\n".join(md_report.split("\n")[:15]) + "\n...")


def main():
    """Run all demos."""
    print("\n")
    print("=" * 70)
    print("            EVALUATION METRICS MODULE DEMO")
    print("=" * 70)
    print()

    try:
        # Demo 1: Individual metrics
        demo_individual_metrics()

        # Demo 2: Comprehensive evaluation
        demo_comprehensive_evaluation()

        # Demo 3: Report generation
        demo_report_generation()

        print("\n" + "=" * 70)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  - Use evaluate_model() for comprehensive evaluation")
        print("  - Generate reports with save_report()")
        print("  - See src/evaluation/metrics.py for full API")
        print()

    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
