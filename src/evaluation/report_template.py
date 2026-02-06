"""
Evaluation Report Template

This module provides templates for generating evaluation reports in various formats
(text, JSON, HTML, markdown).

Usage:
    from src.evaluation.report_template import generate_text_report
    from src.evaluation.metrics import evaluate_model

    result = evaluate_model(predictions, ground_truth)
    report = generate_text_report(result, model_name="Baseline")
    print(report)
"""

import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
from .metrics import EvaluationResult


def generate_text_report(
    result: EvaluationResult,
    model_name: str = "Model",
    dataset_name: str = "Dataset",
    additional_info: Optional[Dict] = None
) -> str:
    """
    Generate a text evaluation report.

    Args:
        result: EvaluationResult from metrics evaluation
        model_name: Name of the model being evaluated
        dataset_name: Name of the dataset used
        additional_info: Optional dictionary with extra information

    Returns:
        Formatted text report as string

    Example:
        >>> report = generate_text_report(result, "Baseline", "Validation")
        >>> print(report)
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append(f"EVALUATION REPORT: {model_name}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Dataset: {dataset_name}")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if additional_info:
        for key, value in additional_info.items():
            lines.append(f"{key}: {value}")

    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"Validity Detection Accuracy: {result.validity_accuracy*100:.2f}%")
    lines.append(f"Extraction Accuracy (Valid Orders): {result.exact_match_accuracy*100:.2f}%")
    lines.append("")

    # Validity Detection
    lines.append("VALIDITY DETECTION")
    lines.append("-" * 70)
    lines.append(f"Accuracy:  {result.validity_accuracy*100:.2f}%")
    lines.append(f"Precision: {result.validity_precision*100:.2f}%")
    lines.append(f"Recall:    {result.validity_recall*100:.2f}%")
    lines.append(f"F1 Score:  {result.validity_f1*100:.2f}%")
    lines.append("")
    lines.append("Confusion Matrix:")
    lines.append(f"  True Positives (valid->valid):     {result.true_positives:4d}")
    lines.append(f"  True Negatives (invalid->invalid): {result.true_negatives:4d}")
    lines.append(f"  False Positives (invalid->valid):  {result.false_positives:4d}")
    lines.append(f"  False Negatives (valid->invalid):  {result.false_negatives:4d}")
    lines.append("")

    # Extraction Accuracy
    lines.append("EXTRACTION ACCURACY (Valid Orders Only)")
    lines.append("-" * 70)
    lines.append(f"Total valid orders: {result.total_valid_orders}")
    lines.append("")
    lines.append(f"Origin accuracy:      {result.origin_correct:4d} / {result.total_valid_orders} ({result.origin_accuracy*100:.2f}%)")
    lines.append(f"Destination accuracy: {result.destination_correct:4d} / {result.total_valid_orders} ({result.destination_accuracy*100:.2f}%)")
    lines.append(f"Exact match accuracy: {result.exact_match:4d} / {result.total_valid_orders} ({result.exact_match_accuracy*100:.2f}%)")
    lines.append("")

    # By Difficulty
    if result.by_difficulty:
        lines.append("PERFORMANCE BY DIFFICULTY")
        lines.append("-" * 70)
        for difficulty in ['easy', 'medium', 'hard']:
            if difficulty in result.by_difficulty:
                stats = result.by_difficulty[difficulty]
                lines.append(f"{difficulty.upper()}: {stats['accuracy']*100:.2f}% ({stats['correct']}/{stats['total']})")
        lines.append("")

    # By Category
    if result.by_category:
        lines.append("PERFORMANCE BY CATEGORY (Top 10 Weaknesses)")
        lines.append("-" * 70)
        # Sort by accuracy (ascending)
        sorted_categories = sorted(result.by_category.items(), key=lambda x: x[1]['accuracy'])
        for category, stats in sorted_categories[:10]:
            lines.append(f"{category:30s}: {stats['accuracy']*100:5.1f}% ({stats['correct']}/{stats['total']})")
        lines.append("")

    # Robustness
    if result.robustness_scores:
        lines.append("ROBUSTNESS METRICS")
        lines.append("-" * 70)
        for metric, score in sorted(result.robustness_scores.items()):
            if score is not None:
                lines.append(f"{metric:30s}: {score*100:5.1f}%")
        lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)


def generate_json_report(
    result: EvaluationResult,
    model_name: str = "Model",
    dataset_name: str = "Dataset",
    additional_info: Optional[Dict] = None
) -> str:
    """
    Generate a JSON evaluation report.

    Args:
        result: EvaluationResult from metrics evaluation
        model_name: Name of the model being evaluated
        dataset_name: Name of the dataset used
        additional_info: Optional dictionary with extra information

    Returns:
        JSON string

    Example:
        >>> json_report = generate_json_report(result, "Baseline", "Validation")
        >>> with open("report.json", "w") as f:
        ...     f.write(json_report)
    """
    report_dict = {
        'metadata': {
            'model_name': model_name,
            'dataset_name': dataset_name,
            'timestamp': datetime.now().isoformat(),
            'additional_info': additional_info or {}
        },
        'metrics': result.to_dict()
    }

    return json.dumps(report_dict, indent=2, ensure_ascii=False)


def generate_markdown_report(
    result: EvaluationResult,
    model_name: str = "Model",
    dataset_name: str = "Dataset",
    additional_info: Optional[Dict] = None
) -> str:
    """
    Generate a Markdown evaluation report.

    Args:
        result: EvaluationResult from metrics evaluation
        model_name: Name of the model being evaluated
        dataset_name: Name of the dataset used
        additional_info: Optional dictionary with extra information

    Returns:
        Markdown formatted report as string

    Example:
        >>> md_report = generate_markdown_report(result, "Baseline", "Validation")
        >>> with open("report.md", "w") as f:
        ...     f.write(md_report)
    """
    lines = []

    # Header
    lines.append(f"# Evaluation Report: {model_name}")
    lines.append("")
    lines.append(f"**Dataset**: {dataset_name}  ")
    lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")

    if additional_info:
        for key, value in additional_info.items():
            lines.append(f"**{key}**: {value}  ")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Validity Detection Accuracy**: {result.validity_accuracy*100:.2f}%")
    lines.append(f"- **Extraction Accuracy (Valid Orders)**: {result.exact_match_accuracy*100:.2f}%")
    lines.append("")

    # Validity Detection
    lines.append("## Validity Detection")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Accuracy | {result.validity_accuracy*100:.2f}% |")
    lines.append(f"| Precision | {result.validity_precision*100:.2f}% |")
    lines.append(f"| Recall | {result.validity_recall*100:.2f}% |")
    lines.append(f"| F1 Score | {result.validity_f1*100:.2f}% |")
    lines.append("")

    lines.append("### Confusion Matrix")
    lines.append("")
    lines.append("| | Predicted Invalid | Predicted Valid |")
    lines.append("|---|---|---|")
    lines.append(f"| **Actually Invalid** | {result.true_negatives} (TN) | {result.false_positives} (FP) |")
    lines.append(f"| **Actually Valid** | {result.false_negatives} (FN) | {result.true_positives} (TP) |")
    lines.append("")

    # Extraction Accuracy
    lines.append("## Extraction Accuracy (Valid Orders Only)")
    lines.append("")
    lines.append(f"**Total valid orders**: {result.total_valid_orders}")
    lines.append("")
    lines.append("| Entity | Correct | Total | Accuracy |")
    lines.append("|--------|---------|-------|----------|")
    lines.append(f"| Origin | {result.origin_correct} | {result.total_valid_orders} | {result.origin_accuracy*100:.2f}% |")
    lines.append(f"| Destination | {result.destination_correct} | {result.total_valid_orders} | {result.destination_accuracy*100:.2f}% |")
    lines.append(f"| Exact Match | {result.exact_match} | {result.total_valid_orders} | {result.exact_match_accuracy*100:.2f}% |")
    lines.append("")

    # By Difficulty
    if result.by_difficulty:
        lines.append("## Performance by Difficulty")
        lines.append("")
        lines.append("| Difficulty | Correct | Total | Accuracy |")
        lines.append("|------------|---------|-------|----------|")
        for difficulty in ['easy', 'medium', 'hard']:
            if difficulty in result.by_difficulty:
                stats = result.by_difficulty[difficulty]
                lines.append(f"| {difficulty.capitalize()} | {stats['correct']} | {stats['total']} | {stats['accuracy']*100:.2f}% |")
        lines.append("")

    # By Category
    if result.by_category:
        lines.append("## Performance by Category (Top 10 Weaknesses)")
        lines.append("")
        lines.append("| Category | Correct | Total | Accuracy |")
        lines.append("|----------|---------|-------|----------|")
        sorted_categories = sorted(result.by_category.items(), key=lambda x: x[1]['accuracy'])
        for category, stats in sorted_categories[:10]:
            lines.append(f"| {category} | {stats['correct']} | {stats['total']} | {stats['accuracy']*100:.2f}% |")
        lines.append("")

    # Robustness
    if result.robustness_scores:
        lines.append("## Robustness Metrics")
        lines.append("")
        lines.append("| Metric | Accuracy |")
        lines.append("|--------|----------|")
        for metric, score in sorted(result.robustness_scores.items()):
            if score is not None:
                lines.append(f"| {metric} | {score*100:.2f}% |")
        lines.append("")

    return "\n".join(lines)


def save_report(
    result: EvaluationResult,
    output_dir: str,
    model_name: str = "Model",
    dataset_name: str = "Dataset",
    additional_info: Optional[Dict] = None,
    formats: Optional[list] = None
):
    """
    Save evaluation report in multiple formats.

    Args:
        result: EvaluationResult from metrics evaluation
        output_dir: Directory to save reports
        model_name: Name of the model being evaluated
        dataset_name: Name of the dataset used
        additional_info: Optional dictionary with extra information
        formats: List of formats to generate ['text', 'json', 'markdown']
                 Default: all formats

    Example:
        >>> save_report(result, "results", "Baseline", "Validation")
        # Saves: results/baseline_validation_report.txt
        #        results/baseline_validation_report.json
        #        results/baseline_validation_report.md
    """
    if formats is None:
        formats = ['text', 'json', 'markdown']

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename base
    model_slug = model_name.lower().replace(' ', '_')
    dataset_slug = dataset_name.lower().replace(' ', '_')
    base_filename = f"{model_slug}_{dataset_slug}_report"

    # Generate and save reports
    if 'text' in formats:
        text_report = generate_text_report(result, model_name, dataset_name, additional_info)
        text_file = output_path / f"{base_filename}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        print(f"[OK] Text report saved to: {text_file}")

    if 'json' in formats:
        json_report = generate_json_report(result, model_name, dataset_name, additional_info)
        json_file = output_path / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_report)
        print(f"[OK] JSON report saved to: {json_file}")

    if 'markdown' in formats:
        md_report = generate_markdown_report(result, model_name, dataset_name, additional_info)
        md_file = output_path / f"{base_filename}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"[OK] Markdown report saved to: {md_file}")
