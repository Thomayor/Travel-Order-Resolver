"""
NLP Evaluation Metrics

This module provides comprehensive metrics for evaluating NLP model performance
on the Travel Order Resolver task (origin-destination extraction from French text).

Core Metrics:
- Accuracy: % of correctly identified origin-destination pairs
- Precision/Recall/F1: For valid order detection and entity extraction
- Confusion Matrix: Visualize error patterns
- Robustness: Performance on challenging cases (misspellings, no capitals, ambiguous names)

Usage:
    from src.evaluation.metrics import calculate_accuracy, EvaluationResult

    result = calculate_accuracy(predictions, ground_truth)
    print(f"Exact match accuracy: {result.exact_match_accuracy}")
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class EvaluationResult:
    """Container for evaluation results."""

    # Validity detection metrics
    validity_accuracy: float = 0.0
    validity_precision: float = 0.0
    validity_recall: float = 0.0
    validity_f1: float = 0.0

    # Confusion matrix (validity)
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # Extraction metrics (valid orders only)
    origin_accuracy: float = 0.0
    destination_accuracy: float = 0.0
    exact_match_accuracy: float = 0.0

    origin_correct: int = 0
    destination_correct: int = 0
    exact_match: int = 0
    total_valid_orders: int = 0

    # Robustness metrics
    robustness_scores: Dict[str, float] = field(default_factory=dict)

    # Detailed breakdown
    by_difficulty: Dict[str, Dict] = field(default_factory=dict)
    by_category: Dict[str, Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'validity_detection': {
                'accuracy': self.validity_accuracy,
                'precision': self.validity_precision,
                'recall': self.validity_recall,
                'f1': self.validity_f1,
                'confusion_matrix': {
                    'tp': self.true_positives,
                    'tn': self.true_negatives,
                    'fp': self.false_positives,
                    'fn': self.false_negatives
                }
            },
            'extraction_accuracy': {
                'origin': self.origin_accuracy,
                'destination': self.destination_accuracy,
                'exact_match': self.exact_match_accuracy,
                'counts': {
                    'origin_correct': self.origin_correct,
                    'destination_correct': self.destination_correct,
                    'exact_match': self.exact_match,
                    'total_valid_orders': self.total_valid_orders
                }
            },
            'robustness': self.robustness_scores,
            'by_difficulty': self.by_difficulty,
            'by_category': self.by_category
        }


def normalize_city_name(name: str) -> str:
    """
    Normalize city name for comparison.

    Applies:
    - Lowercase
    - Strip whitespace
    - Remove French accents (à→a, é→e, etc.)
    - Handle INVALID marker

    Args:
        name: City name to normalize

    Returns:
        Normalized city name (lowercase, no accents)

    Examples:
        >>> normalize_city_name("Paris")
        'paris'
        >>> normalize_city_name("Aix-en-Provence")
        'aix-en-provence'
        >>> normalize_city_name("INVALID")
        'INVALID'
    """
    if pd.isna(name) or name == '':
        return ''

    # Handle INVALID marker (keep uppercase)
    if str(name).upper() == 'INVALID':
        return 'INVALID'

    # Lowercase and strip
    name = str(name).lower().strip()

    # Remove French accents
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


def calculate_accuracy(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    id_column: str = 'sentenceID',
    origin_col_pred: str = 'origin',
    dest_col_pred: str = 'destination',
    origin_col_gt: str = 'origin',
    dest_col_gt: str = 'destination',
    validity_col_gt: str = 'is_valid'
) -> EvaluationResult:
    """
    Calculate comprehensive accuracy metrics.

    Computes:
    - Origin accuracy: % of correct origin extractions
    - Destination accuracy: % of correct destination extractions
    - Exact match accuracy: % where both origin AND destination are correct

    Args:
        predictions: DataFrame with model predictions (columns: sentenceID, origin, destination)
        ground_truth: DataFrame with ground truth labels (columns: sentenceID, origin, destination, is_valid)
        id_column: Name of sentence ID column
        origin_col_pred: Prediction origin column name
        dest_col_pred: Prediction destination column name
        origin_col_gt: Ground truth origin column name
        dest_col_gt: Ground truth destination column name
        validity_col_gt: Ground truth validity column name (1=valid, 0=invalid)

    Returns:
        EvaluationResult with accuracy metrics

    Example:
        >>> predictions = pd.DataFrame({
        ...     'sentenceID': [1, 2],
        ...     'origin': ['Paris', 'Lyon'],
        ...     'destination': ['Lyon', 'Marseille']
        ... })
        >>> ground_truth = pd.DataFrame({
        ...     'sentenceID': [1, 2],
        ...     'origin': ['Paris', 'Lyon'],
        ...     'destination': ['Lyon', 'Nice'],
        ...     'is_valid': [1, 1]
        ... })
        >>> result = calculate_accuracy(predictions, ground_truth)
        >>> result.origin_accuracy
        1.0
        >>> result.exact_match_accuracy
        0.5
    """
    result = EvaluationResult()

    # Merge predictions with ground truth
    merged = ground_truth.merge(
        predictions[[id_column, origin_col_pred, dest_col_pred]],
        on=id_column,
        how='left',
        suffixes=('_gt', '_pred')
    )

    # After merge, columns get suffixes: origin -> origin_gt, origin_pred
    origin_gt_col = f"{origin_col_gt}_gt" if origin_col_gt == origin_col_pred else origin_col_gt
    dest_gt_col = f"{dest_col_gt}_gt" if dest_col_gt == dest_col_pred else dest_col_gt
    origin_pred_col = f"{origin_col_pred}_pred" if origin_col_pred == origin_col_gt else origin_col_pred
    dest_pred_col = f"{dest_col_pred}_pred" if dest_col_pred == dest_col_gt else dest_col_pred

    # Normalize city names
    merged['origin_gt_norm'] = merged[origin_gt_col].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged[dest_gt_col].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged[origin_pred_col].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged[dest_pred_col].apply(normalize_city_name)

    # Filter to valid orders only (for extraction metrics)
    valid_orders = merged[merged[validity_col_gt] == 1].copy()

    if len(valid_orders) == 0:
        return result

    # Calculate extraction accuracy
    valid_orders['origin_correct'] = valid_orders['origin_gt_norm'] == valid_orders['origin_pred_norm']
    valid_orders['dest_correct'] = valid_orders['dest_gt_norm'] == valid_orders['dest_pred_norm']
    valid_orders['exact_match'] = valid_orders['origin_correct'] & valid_orders['dest_correct']

    result.total_valid_orders = len(valid_orders)
    result.origin_correct = int(valid_orders['origin_correct'].sum())
    result.destination_correct = int(valid_orders['dest_correct'].sum())
    result.exact_match = int(valid_orders['exact_match'].sum())

    result.origin_accuracy = result.origin_correct / result.total_valid_orders
    result.destination_accuracy = result.destination_correct / result.total_valid_orders
    result.exact_match_accuracy = result.exact_match / result.total_valid_orders

    return result


def calculate_precision_recall_f1(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    id_column: str = 'sentenceID',
    origin_col_pred: str = 'origin',
    dest_col_pred: str = 'destination',
    origin_col_gt: str = 'origin',
    dest_col_gt: str = 'destination',
    validity_col_gt: str = 'is_valid'
) -> EvaluationResult:
    """
    Calculate precision, recall, and F1 score for valid order detection.

    Metrics:
    - Precision: Of sentences predicted as valid, % that are actually valid
    - Recall: Of actual valid sentences, % that were detected as valid
    - F1: Harmonic mean of precision and recall

    Also computes confusion matrix:
    - True Positive (TP): Valid order correctly detected as valid
    - True Negative (TN): Invalid order correctly detected as invalid
    - False Positive (FP): Invalid order incorrectly detected as valid
    - False Negative (FN): Valid order incorrectly detected as invalid

    Args:
        predictions: DataFrame with model predictions
        ground_truth: DataFrame with ground truth labels
        id_column: Name of sentence ID column
        origin_col_pred: Prediction origin column name
        dest_col_pred: Prediction destination column name
        origin_col_gt: Ground truth origin column name
        dest_col_gt: Ground truth destination column name
        validity_col_gt: Ground truth validity column (1=valid, 0=invalid)

    Returns:
        EvaluationResult with precision, recall, F1, and confusion matrix

    Example:
        >>> result = calculate_precision_recall_f1(predictions, ground_truth)
        >>> print(f"Precision: {result.validity_precision:.2f}")
        >>> print(f"Recall: {result.validity_recall:.2f}")
        >>> print(f"F1: {result.validity_f1:.2f}")
    """
    result = EvaluationResult()

    # Merge predictions with ground truth
    merged = ground_truth.merge(
        predictions[[id_column, origin_col_pred, dest_col_pred]],
        on=id_column,
        how='left',
        suffixes=('_gt', '_pred')
    )

    # After merge, columns get suffixes if names conflict
    origin_pred_col = f"{origin_col_pred}_pred" if origin_col_pred == origin_col_gt else origin_col_pred
    dest_pred_col = f"{dest_col_pred}_pred" if dest_col_pred == dest_col_gt else dest_col_pred

    # Normalize
    merged['origin_pred_norm'] = merged[origin_pred_col].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged[dest_pred_col].apply(normalize_city_name)

    # Determine prediction validity (is predicted as valid if both origin and dest are not INVALID)
    merged['pred_is_valid'] = (merged['origin_pred_norm'] != 'INVALID') & (merged['dest_pred_norm'] != 'INVALID')
    merged['gt_is_valid'] = merged[validity_col_gt] == 1

    # Calculate confusion matrix
    tp = ((merged['gt_is_valid']) & (merged['pred_is_valid'])).sum()
    tn = ((~merged['gt_is_valid']) & (~merged['pred_is_valid'])).sum()
    fp = ((~merged['gt_is_valid']) & (merged['pred_is_valid'])).sum()
    fn = ((merged['gt_is_valid']) & (~merged['pred_is_valid'])).sum()

    result.true_positives = int(tp)
    result.true_negatives = int(tn)
    result.false_positives = int(fp)
    result.false_negatives = int(fn)

    # Calculate metrics
    total = len(merged)
    result.validity_accuracy = (tp + tn) / total if total > 0 else 0
    result.validity_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    result.validity_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    result.validity_f1 = (2 * result.validity_precision * result.validity_recall /
                          (result.validity_precision + result.validity_recall)
                          if (result.validity_precision + result.validity_recall) > 0 else 0)

    return result


def generate_confusion_matrix(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    id_column: str = 'sentenceID',
    origin_col_pred: str = 'origin',
    dest_col_pred: str = 'destination',
    validity_col_gt: str = 'is_valid'
) -> np.ndarray:
    """
    Generate confusion matrix for valid order detection.

    Returns 2x2 matrix:
        [[TN, FP],
         [FN, TP]]

    Where:
    - TN (top-left): Invalid correctly detected as invalid
    - FP (top-right): Invalid incorrectly detected as valid
    - FN (bottom-left): Valid incorrectly detected as invalid
    - TP (bottom-right): Valid correctly detected as valid

    Args:
        predictions: DataFrame with model predictions
        ground_truth: DataFrame with ground truth labels
        id_column: Name of sentence ID column
        origin_col_pred: Prediction origin column name
        dest_col_pred: Prediction destination column name
        validity_col_gt: Ground truth validity column

    Returns:
        2x2 numpy array confusion matrix

    Example:
        >>> cm = generate_confusion_matrix(predictions, ground_truth)
        >>> print(cm)
        [[  0 450]
         [  0 1050]]
        >>> # Interpretation: 450 false positives, 1050 true positives
    """
    # Calculate precision/recall to get confusion matrix
    result = calculate_precision_recall_f1(
        predictions, ground_truth, id_column,
        origin_col_pred, dest_col_pred, validity_col_gt=validity_col_gt
    )

    # Create 2x2 confusion matrix
    # Row 0: Ground truth negative (invalid)
    # Row 1: Ground truth positive (valid)
    # Col 0: Predicted negative (invalid)
    # Col 1: Predicted positive (valid)
    confusion_matrix = np.array([
        [result.true_negatives, result.false_positives],
        [result.false_negatives, result.true_positives]
    ])

    return confusion_matrix


def evaluate_robustness(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    test_categories: Optional[List[str]] = None,
    id_column: str = 'sentenceID',
    category_column: str = 'category',
    difficulty_column: str = 'difficulty',
    origin_col_pred: str = 'origin',
    dest_col_pred: str = 'destination',
    origin_col_gt: str = 'origin',
    dest_col_gt: str = 'destination',
    validity_col_gt: str = 'is_valid'
) -> Dict[str, float]:
    """
    Evaluate model robustness on challenging test cases.

    Measures performance on:
    - no_capitals: Sentences without capital letters
    - misspelling: Sentences with spelling errors
    - name_ambiguity: Ambiguous city names (e.g., Paris as person vs city)
    - compound_name: Multi-word city names (e.g., Aix-en-Provence)
    - complex_question: Complex grammatical structures
    - inverted_order: Destination mentioned before origin

    Args:
        predictions: DataFrame with model predictions
        ground_truth: DataFrame with ground truth (must have 'category' column)
        test_categories: List of categories to evaluate (default: all robustness categories)
        id_column: Name of sentence ID column
        category_column: Name of category column in ground truth
        difficulty_column: Name of difficulty column in ground truth
        origin_col_pred: Prediction origin column name
        dest_col_pred: Prediction destination column name
        origin_col_gt: Ground truth origin column name
        dest_col_gt: Ground truth destination column name
        validity_col_gt: Ground truth validity column

    Returns:
        Dictionary mapping category name to accuracy score

    Example:
        >>> robustness = evaluate_robustness(predictions, ground_truth)
        >>> print(f"Misspelling accuracy: {robustness['misspelling']:.2%}")
        >>> print(f"No capitals accuracy: {robustness['no_capitals']:.2%}")
    """
    # Default robustness categories
    if test_categories is None:
        test_categories = [
            'no_capitals',
            'misspelling',
            'name_ambiguity',
            'compound_name',
            'complex_question',
            'inverted_order'
        ]

    # Merge predictions with ground truth
    merged = ground_truth.merge(
        predictions[[id_column, origin_col_pred, dest_col_pred]],
        on=id_column,
        how='left',
        suffixes=('_gt', '_pred')
    )

    # After merge, columns get suffixes if names conflict
    origin_gt_col = f"{origin_col_gt}_gt" if origin_col_gt == origin_col_pred else origin_col_gt
    dest_gt_col = f"{dest_col_gt}_gt" if dest_col_gt == dest_col_pred else dest_col_gt
    origin_pred_col = f"{origin_col_pred}_pred" if origin_col_pred == origin_col_gt else origin_col_pred
    dest_pred_col = f"{dest_col_pred}_pred" if dest_col_pred == dest_col_gt else dest_col_pred

    # Normalize
    merged['origin_gt_norm'] = merged[origin_gt_col].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged[dest_gt_col].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged[origin_pred_col].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged[dest_pred_col].apply(normalize_city_name)

    # Filter to valid orders only
    valid_orders = merged[merged[validity_col_gt] == 1].copy()

    # Calculate exact match
    valid_orders['exact_match'] = (
        (valid_orders['origin_gt_norm'] == valid_orders['origin_pred_norm']) &
        (valid_orders['dest_gt_norm'] == valid_orders['dest_pred_norm'])
    )

    # Calculate accuracy per category
    robustness_scores = {}

    for category in test_categories:
        subset = valid_orders[valid_orders[category_column] == category]

        if len(subset) > 0:
            accuracy = subset['exact_match'].sum() / len(subset)
            robustness_scores[category] = accuracy
        else:
            robustness_scores[category] = None  # Category not present in dataset

    # Also evaluate by difficulty level
    for difficulty in ['easy', 'medium', 'hard']:
        subset = valid_orders[valid_orders[difficulty_column] == difficulty]

        if len(subset) > 0:
            accuracy = subset['exact_match'].sum() / len(subset)
            robustness_scores[f'difficulty_{difficulty}'] = accuracy

    return robustness_scores


def evaluate_model(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    id_column: str = 'sentenceID',
    origin_col_pred: str = 'origin',
    dest_col_pred: str = 'destination',
    origin_col_gt: str = 'origin',
    dest_col_gt: str = 'destination',
    validity_col_gt: str = 'is_valid',
    category_column: str = 'category',
    difficulty_column: str = 'difficulty'
) -> EvaluationResult:
    """
    Comprehensive model evaluation with all metrics.

    Combines:
    - Accuracy metrics (origin, destination, exact match)
    - Precision/Recall/F1 for validity detection
    - Confusion matrix
    - Robustness scores by category and difficulty

    This is the main entry point for complete model evaluation.

    Args:
        predictions: DataFrame with model predictions (sentenceID, origin, destination)
        ground_truth: DataFrame with ground truth (sentenceID, origin, destination, is_valid, category, difficulty)
        id_column: Name of sentence ID column
        origin_col_pred: Prediction origin column name
        dest_col_pred: Prediction destination column name
        origin_col_gt: Ground truth origin column name
        dest_col_gt: Ground truth destination column name
        validity_col_gt: Ground truth validity column
        category_column: Name of category column
        difficulty_column: Name of difficulty column

    Returns:
        EvaluationResult with complete metrics

    Example:
        >>> result = evaluate_model(predictions, ground_truth)
        >>> print(f"Exact match accuracy: {result.exact_match_accuracy:.2%}")
        >>> print(f"Validity F1: {result.validity_f1:.2%}")
        >>> print(f"Misspelling robustness: {result.robustness_scores['misspelling']:.2%}")
    """
    # Calculate accuracy metrics
    accuracy_result = calculate_accuracy(
        predictions, ground_truth, id_column,
        origin_col_pred, dest_col_pred,
        origin_col_gt, dest_col_gt, validity_col_gt
    )

    # Calculate precision/recall/F1
    pr_result = calculate_precision_recall_f1(
        predictions, ground_truth, id_column,
        origin_col_pred, dest_col_pred,
        origin_col_gt, dest_col_gt, validity_col_gt
    )

    # Calculate robustness
    robustness_scores = evaluate_robustness(
        predictions, ground_truth, None, id_column,
        category_column, difficulty_column,
        origin_col_pred, dest_col_pred,
        origin_col_gt, dest_col_gt, validity_col_gt
    )

    # Merge results
    result = EvaluationResult(
        # Validity detection
        validity_accuracy=pr_result.validity_accuracy,
        validity_precision=pr_result.validity_precision,
        validity_recall=pr_result.validity_recall,
        validity_f1=pr_result.validity_f1,
        true_positives=pr_result.true_positives,
        true_negatives=pr_result.true_negatives,
        false_positives=pr_result.false_positives,
        false_negatives=pr_result.false_negatives,

        # Extraction accuracy
        origin_accuracy=accuracy_result.origin_accuracy,
        destination_accuracy=accuracy_result.destination_accuracy,
        exact_match_accuracy=accuracy_result.exact_match_accuracy,
        origin_correct=accuracy_result.origin_correct,
        destination_correct=accuracy_result.destination_correct,
        exact_match=accuracy_result.exact_match,
        total_valid_orders=accuracy_result.total_valid_orders,

        # Robustness
        robustness_scores=robustness_scores
    )

    # Calculate detailed breakdown by category and difficulty
    merged = ground_truth.merge(
        predictions[[id_column, origin_col_pred, dest_col_pred]],
        on=id_column,
        how='left',
        suffixes=('_gt', '_pred')
    )

    # After merge, columns get suffixes if names conflict
    origin_gt_col = f"{origin_col_gt}_gt" if origin_col_gt == origin_col_pred else origin_col_gt
    dest_gt_col = f"{dest_col_gt}_gt" if dest_col_gt == dest_col_pred else dest_col_gt
    origin_pred_col = f"{origin_col_pred}_pred" if origin_col_pred == origin_col_gt else origin_col_pred
    dest_pred_col = f"{dest_col_pred}_pred" if dest_col_pred == dest_col_gt else dest_col_pred

    merged['origin_gt_norm'] = merged[origin_gt_col].apply(normalize_city_name)
    merged['dest_gt_norm'] = merged[dest_gt_col].apply(normalize_city_name)
    merged['origin_pred_norm'] = merged[origin_pred_col].apply(normalize_city_name)
    merged['dest_pred_norm'] = merged[dest_pred_col].apply(normalize_city_name)

    valid_orders = merged[merged[validity_col_gt] == 1].copy()
    valid_orders['exact_match'] = (
        (valid_orders['origin_gt_norm'] == valid_orders['origin_pred_norm']) &
        (valid_orders['dest_gt_norm'] == valid_orders['dest_pred_norm'])
    )

    # By difficulty
    for difficulty in ['easy', 'medium', 'hard']:
        subset = valid_orders[valid_orders[difficulty_column] == difficulty]
        if len(subset) > 0:
            result.by_difficulty[difficulty] = {
                'total': int(len(subset)),
                'correct': int(subset['exact_match'].sum()),
                'accuracy': float(subset['exact_match'].sum() / len(subset))
            }

    # By category
    category_stats = valid_orders.groupby(category_column).agg({
        'exact_match': ['sum', 'count', 'mean']
    })

    for category, row in category_stats.iterrows():
        result.by_category[category] = {
            'total': int(row[('exact_match', 'count')]),
            'correct': int(row[('exact_match', 'sum')]),
            'accuracy': float(row[('exact_match', 'mean')])
        }

    return result
