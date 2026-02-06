# Evaluation Report: Baseline

**Dataset**: Test Set  
**Date**: 2026-02-06 15:40:17  
**Total sentences**: 1500  

---

## Summary

- **Validity Detection Accuracy**: 83.47%
- **Extraction Accuracy (Valid Orders)**: 67.81%

## Validity Detection

| Metric | Value |
|--------|-------|
| Accuracy | 83.47% |
| Precision | 89.94% |
| Recall | 86.00% |
| F1 Score | 87.93% |

### Confusion Matrix

| | Predicted Invalid | Predicted Valid |
|---|---|---|
| **Actually Invalid** | 349 (TN) | 101 (FP) |
| **Actually Valid** | 147 (FN) | 903 (TP) |

## Extraction Accuracy (Valid Orders Only)

**Total valid orders**: 1050

| Entity | Correct | Total | Accuracy |
|--------|---------|-------|----------|
| Origin | 862 | 1050 | 82.10% |
| Destination | 821 | 1050 | 78.19% |
| Exact Match | 712 | 1050 | 67.81% |

## Performance by Difficulty

| Difficulty | Correct | Total | Accuracy |
|------------|---------|-------|----------|
| Easy | 186 | 213 | 87.32% |
| Medium | 468 | 655 | 71.45% |
| Hard | 58 | 182 | 31.87% |

## Performance by Category (Top 10 Weaknesses)

| Category | Correct | Total | Accuracy |
|----------|---------|-------|----------|
| misspelling | 1 | 84 | 1.19% |
| complex_question | 8 | 23 | 34.78% |
| compound_name | 38 | 92 | 41.30% |
| inverted_order | 86 | 132 | 65.15% |
| name_ambiguity | 119 | 179 | 66.48% |
| additional_info | 56 | 68 | 82.35% |
| standard | 237 | 286 | 82.87% |
| no_capitals | 67 | 77 | 87.01% |
| no_markers | 100 | 109 | 91.74% |

## Robustness Metrics

| Metric | Accuracy |
|--------|----------|
| complex_question | 34.78% |
| compound_name | 41.30% |
| difficulty_easy | 87.32% |
| difficulty_hard | 31.87% |
| difficulty_medium | 71.45% |
| inverted_order | 65.15% |
| misspelling | 1.19% |
| name_ambiguity | 66.48% |
| no_capitals | 87.01% |
