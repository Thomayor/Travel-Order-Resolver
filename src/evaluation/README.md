# Evaluation Module

Comprehensive metrics for evaluating NLP model performance on the Travel Order Resolver task (origin-destination extraction from French text).

## Features

✅ **Accuracy Metrics**: Origin, destination, and exact match accuracy
✅ **Precision/Recall/F1**: For valid order detection
✅ **Confusion Matrix**: Visualize error patterns
✅ **Robustness Metrics**: Performance on challenging cases (misspellings, no capitals, ambiguous names)
✅ **Report Generation**: Text, JSON, and Markdown formats

---

## Quick Start

### Basic Usage

```python
from src.evaluation.metrics import evaluate_model
from src.evaluation.report_template import save_report
import pandas as pd

# Load your predictions and ground truth
predictions = pd.read_csv("results/predictions.csv")  # sentenceID, origin, destination
ground_truth = pd.read_csv("data/ground_truth.csv")  # sentenceID, origin, destination, is_valid, difficulty, category

# Evaluate
result = evaluate_model(predictions, ground_truth)

# Print key metrics
print(f"Exact match accuracy: {result.exact_match_accuracy:.2%}")
print(f"Validity F1 score: {result.validity_f1:.2%}")

# Save reports
save_report(result, "results", model_name="Baseline", dataset_name="Validation")
```

---

## API Reference

### Core Functions

#### `calculate_accuracy(predictions, ground_truth)`

Calculate origin, destination, and exact match accuracy.

**Returns**: `EvaluationResult` with:
- `origin_accuracy`: % of correct origin extractions
- `destination_accuracy`: % of correct destination extractions
- `exact_match_accuracy`: % where both origin AND destination are correct

**Example**:
```python
from src.evaluation.metrics import calculate_accuracy

result = calculate_accuracy(predictions, ground_truth)
print(f"Origin accuracy: {result.origin_accuracy:.2%}")
print(f"Destination accuracy: {result.destination_accuracy:.2%}")
print(f"Exact match: {result.exact_match_accuracy:.2%}")
```

#### `calculate_precision_recall_f1(predictions, ground_truth)`

Calculate precision, recall, and F1 score for valid order detection.

**Returns**: `EvaluationResult` with:
- `validity_precision`: Of predicted valid, % actually valid
- `validity_recall`: Of actually valid, % detected as valid
- `validity_f1`: Harmonic mean of precision and recall
- Confusion matrix: `true_positives`, `true_negatives`, `false_positives`, `false_negatives`

**Example**:
```python
from src.evaluation.metrics import calculate_precision_recall_f1

result = calculate_precision_recall_f1(predictions, ground_truth)
print(f"Precision: {result.validity_precision:.2%}")
print(f"Recall: {result.validity_recall:.2%}")
print(f"F1: {result.validity_f1:.2%}")
print(f"Confusion matrix: TP={result.true_positives}, TN={result.true_negatives}")
```

#### `generate_confusion_matrix(predictions, ground_truth)`

Generate 2x2 confusion matrix for valid order detection.

**Returns**: `np.ndarray` with shape (2, 2):
```
[[TN, FP],
 [FN, TP]]
```

**Example**:
```python
from src.evaluation.metrics import generate_confusion_matrix

cm = generate_confusion_matrix(predictions, ground_truth)
print(f"True Negatives: {cm[0,0]}")
print(f"False Positives: {cm[0,1]}")
print(f"False Negatives: {cm[1,0]}")
print(f"True Positives: {cm[1,1]}")
```

#### `evaluate_robustness(predictions, ground_truth)`

Evaluate model performance on challenging test cases.

**Returns**: `Dict[str, float]` mapping category to accuracy:
- `no_capitals`: Sentences without capital letters
- `misspelling`: Sentences with spelling errors
- `name_ambiguity`: Ambiguous city names (Paris as person vs city)
- `compound_name`: Multi-word city names (Aix-en-Provence)
- `complex_question`: Complex grammatical structures
- `inverted_order`: Destination mentioned before origin
- `difficulty_easy`, `difficulty_medium`, `difficulty_hard`: By difficulty level

**Example**:
```python
from src.evaluation.metrics import evaluate_robustness

robustness = evaluate_robustness(predictions, ground_truth)
print(f"Misspelling accuracy: {robustness['misspelling']:.2%}")
print(f"No capitals accuracy: {robustness['no_capitals']:.2%}")
print(f"Hard difficulty: {robustness['difficulty_hard']:.2%}")
```

#### `evaluate_model(predictions, ground_truth)`

**[MAIN ENTRY POINT]** Comprehensive evaluation with all metrics.

Combines accuracy, precision/recall/F1, confusion matrix, and robustness in a single call.

**Returns**: `EvaluationResult` with complete metrics.

**Example**:
```python
from src.evaluation.metrics import evaluate_model

result = evaluate_model(predictions, ground_truth)

# Access all metrics
print(f"Exact match accuracy: {result.exact_match_accuracy:.2%}")
print(f"Validity F1: {result.validity_f1:.2%}")
print(f"Easy difficulty: {result.by_difficulty['easy']['accuracy']:.2%}")
print(f"Misspelling robustness: {result.robustness_scores['misspelling']:.2%}")

# Export to dict
metrics_dict = result.to_dict()
```

---

### Report Generation

#### `generate_text_report(result, model_name, dataset_name)`

Generate a plain text evaluation report.

**Example**:
```python
from src.evaluation.report_template import generate_text_report

report = generate_text_report(result, "Baseline", "Validation Set")
print(report)
```

#### `generate_json_report(result, model_name, dataset_name)`

Generate a JSON evaluation report (machine-readable).

**Example**:
```python
from src.evaluation.report_template import generate_json_report

json_report = generate_json_report(result, "Baseline", "Validation")
with open("report.json", "w") as f:
    f.write(json_report)
```

#### `generate_markdown_report(result, model_name, dataset_name)`

Generate a Markdown evaluation report (GitHub/docs friendly).

**Example**:
```python
from src.evaluation.report_template import generate_markdown_report

md_report = generate_markdown_report(result, "Baseline", "Validation")
with open("report.md", "w") as f:
    f.write(md_report)
```

#### `save_report(result, output_dir, model_name, dataset_name, formats=None)`

Save evaluation report in multiple formats (text, JSON, markdown).

**Example**:
```python
from src.evaluation.report_template import save_report

save_report(
    result,
    output_dir="results",
    model_name="Baseline",
    dataset_name="Validation",
    formats=['text', 'json', 'markdown']  # Optional, defaults to all
)
```

---

## Data Format Requirements

### Predictions DataFrame

Must contain:
- `sentenceID`: Unique sentence identifier (int)
- `origin`: Extracted origin city (str) or `"INVALID"`
- `destination`: Extracted destination city (str) or `"INVALID"`

### Ground Truth DataFrame

Must contain:
- `sentenceID`: Unique sentence identifier (int)
- `origin`: True origin city (str) or empty for invalid orders
- `destination`: True destination city (str) or empty for invalid orders
- `is_valid`: 1 for valid travel orders, 0 for invalid
- `difficulty`: `"easy"`, `"medium"`, or `"hard"` (optional, for robustness metrics)
- `category`: Category label like `"misspelling"`, `"no_capitals"`, etc. (optional, for robustness metrics)

### Example CSV Format

**Predictions** (`predictions.csv`):
```csv
sentenceID,origin,destination
1,Paris,Lyon
2,INVALID,INVALID
3,Marseille,Nice
```

**Ground Truth** (`ground_truth.csv`):
```csv
sentenceID,origin,destination,is_valid,difficulty,category
1,Paris,Lyon,1,easy,standard
2,,,0,easy,garbage
3,Marseille,Nice,1,medium,no_capitals
```

---

## Utility Functions

### `normalize_city_name(name)`

Normalize city name for comparison (lowercase, no accents).

**Example**:
```python
from src.evaluation.metrics import normalize_city_name

print(normalize_city_name("Paris"))           # 'paris'
print(normalize_city_name("Aix-en-Provence")) # 'aix-en-provence'
print(normalize_city_name("Nîmes"))           # 'nimes'
print(normalize_city_name("INVALID"))         # 'INVALID'
```

---

## Demo Script

Run the interactive demo to see all features:

```bash
python scripts/demos/demo_evaluation_metrics.py
```

This demonstrates:
- Individual metric calculations
- Comprehensive evaluation
- Report generation in all formats

---

## Integration Example

### Evaluating Baseline Model on Validation Set

```python
import pandas as pd
from src.evaluation.metrics import evaluate_model
from src.evaluation.report_template import save_report

# Load data
predictions = pd.read_csv("results/baseline_validation_output.csv")
ground_truth = pd.read_csv("data/val.csv")

# Rename columns if needed (predictions use "Departure"/"Destination")
predictions = predictions.rename(columns={
    'Departure': 'origin',
    'Destination': 'destination'
})

# Evaluate
result = evaluate_model(predictions, ground_truth)

# Print summary
print(f"Exact match accuracy: {result.exact_match_accuracy:.2%}")
print(f"Validity F1: {result.validity_f1:.2%}")
print(f"\nBy difficulty:")
for difficulty in ['easy', 'medium', 'hard']:
    if difficulty in result.by_difficulty:
        stats = result.by_difficulty[difficulty]
        print(f"  {difficulty.capitalize()}: {stats['accuracy']:.2%}")

# Save reports
save_report(
    result,
    output_dir="results",
    model_name="Baseline",
    dataset_name="Validation",
    additional_info={'Total sentences': 1500}
)
```

---

## Module Structure

```
src/evaluation/
├── __init__.py           # Module exports
├── metrics.py            # Core evaluation metrics (620 lines)
├── report_template.py    # Report generation utilities (370 lines)
└── README.md             # This file
```

---

## Design Principles

1. **Flexibility**: Works with any model (baseline, CamemBERT, future models)
2. **Reproducibility**: All metrics clearly defined and documented
3. **Completeness**: Covers all aspects (accuracy, validity, robustness)
4. **Usability**: Simple API with sensible defaults
5. **Extensibility**: Easy to add new metrics or report formats

---

## Related Documentation

- [BASELINE_VALIDATION_RESULTS.md](../../docs/BASELINE_VALIDATION_RESULTS.md) - Baseline validation results using this module
- [TESTING_GUIDE.md](../../docs/TESTING_GUIDE.md) - Testing guidelines
- [DIFFICULTY_LEVELS.md](../../docs/DIFFICULTY_LEVELS.md) - Dataset difficulty definitions

---

## Version History

- **v1.0.0** (2026-02-06): Initial release
  - Core metrics (accuracy, precision/recall/F1, confusion matrix)
  - Robustness evaluation
  - Report generation (text, JSON, markdown)
  - Demo script

---

**Module Created**: 2026-02-06
**Last Updated**: 2026-02-06
**Status**: ✅ Complete and tested
