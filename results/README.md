# Results Directory

This directory contains evaluation results for the CamemBERT NER model.

## Files

### Committed to Git (Important Results)

- **`camembert_evaluation.json`**: Detailed evaluation metrics
  - Overall accuracy
  - Performance by difficulty (easy/medium/hard)
  - Performance by category (standard, name_ambiguity, misspelling, etc.)
  - Comparison with baseline

- **`camembert_errors.csv`**: Error analysis
  - Sentences where model prediction was incorrect
  - Expected vs predicted origin/destination
  - Categorized by difficulty and type

### Not Committed (Regenerated)

- `checkpoint-*/`: Training checkpoints (ignored by Git)
- `tmp_*`: Temporary files (ignored by Git)

## How to Generate Results

After training the model, run evaluation:

```bash
python scripts/evaluate_camembert.py
```

This will generate:
- `results/camembert_evaluation.json`
- `results/camembert_errors.csv`

## Example: camembert_evaluation.json

```json
{
  "accuracy": 0.8750,
  "correct": 918,
  "total": 1050,
  "by_difficulty": {
    "easy": {"correct": 195, "total": 205},
    "medium": {"correct": 556, "total": 628},
    "hard": {"correct": 167, "total": 217}
  },
  "by_category": {
    "standard": {"correct": 285, "total": 290},
    "name_ambiguity": {"correct": 82, "total": 100},
    "misspelling": {"correct": 47, "total": 72}
  }
}
```

## Example: camembert_errors.csv

```csv
sentenceID,sentence,expected_origin,expected_dest,predicted_origin,predicted_dest,category,difficulty
42,avec mon ami paris de lyon a florence,Lyon,Florence,Paris,Florence,name_ambiguity,hard
156,billet bordeau limogees,Bordeaux,Limoges,,,misspelling,hard
```

---

**Note for Team**: Only the final evaluation results are committed to Git. Training logs and intermediate checkpoints are ignored.
