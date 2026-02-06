"""
Evaluation Module

This module provides comprehensive metrics for evaluating NLP model performance
on the Travel Order Resolver task.

Metrics include:
- Accuracy (exact match, origin, destination)
- Precision, Recall, F1 scores
- Confusion matrices
- Robustness metrics (misspellings, no capitals, ambiguous names)
"""

from .metrics import (
    calculate_accuracy,
    calculate_precision_recall_f1,
    generate_confusion_matrix,
    evaluate_robustness,
    normalize_city_name,
    EvaluationResult
)

__all__ = [
    'calculate_accuracy',
    'calculate_precision_recall_f1',
    'generate_confusion_matrix',
    'evaluate_robustness',
    'normalize_city_name',
    'EvaluationResult'
]
