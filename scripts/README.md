# Scripts Directory

This directory contains scripts for CamemBERT NER model training and evaluation.

## Quick Start

### 1. Convert Dataset

Convert the CSV dataset to NER token format:

```bash
python scripts/convert_dataset_to_ner.py
```

**Output:**
- `data/train_ner.json` (7,000 examples)
- `data/val_ner.json` (1,500 examples)
- `data/test_ner.json` (1,500 examples)

### 2. Train Model

Fine-tune CamemBERT on the NER task:

```bash
python scripts/train_camembert.py
```

**Training time:**
- GPU (T4): 2-4 hours
- CPU: 12-24 hours

**Output:**
- `models/camembert-ner/` (model checkpoint)
- `models/camembert-ner/logs/` (TensorBoard logs)

### 3. Evaluate Model

Evaluate trained model and compare with baseline:

```bash
python scripts/evaluate_camembert.py
```

**Output:**
- Console: Performance comparison table
- `results/camembert_evaluation.json` (detailed metrics)
- `results/camembert_errors.csv` (error analysis)

## Scripts

### convert_dataset_to_ner.py

Converts Travel Order dataset from CSV to NER token format.

**Features:**
- Tokenizes sentences
- Assigns BIO labels (B-ORIGIN, I-ORIGIN, B-DEST, I-DEST, O)
- Handles multi-word cities (Port-Boulet, Aix-en-Provence)
- Splits into train/val/test (70/15/15)
- Stratified split by validity

**Usage:**
```bash
python scripts/convert_dataset_to_ner.py
```

**Input:** `data/dataset_final.csv`
**Output:** `data/{train,val,test}_ner.json`

### train_camembert.py

Fine-tunes CamemBERT model for NER.

**Features:**
- Token classification with 5 labels
- Subword token alignment
- Mixed precision training (FP16)
- TensorBoard logging
- Early stopping (based on F1)

**Usage:**
```bash
# Basic training
python scripts/train_camembert.py

# Custom hyperparameters
python scripts/train_camembert.py --epochs 6 --batch-size 8 --learning-rate 3e-5

# Full options
python scripts/train_camembert.py \
  --train data/train_ner.json \
  --val data/val_ner.json \
  --output models/camembert-ner \
  --epochs 4 \
  --batch-size 16 \
  --learning-rate 2e-5 \
  --warmup-ratio 0.1 \
  --weight-decay 0.01
```

**Options:**
- `--train`: Training data path (default: data/train_ner.json)
- `--val`: Validation data path (default: data/val_ner.json)
- `--output`: Output directory (default: models/camembert-ner)
- `--epochs`: Number of epochs (default: 4)
- `--batch-size`: Batch size per device (default: 16)
- `--learning-rate`: Learning rate (default: 2e-5)
- `--warmup-ratio`: Warmup ratio (default: 0.1)
- `--weight-decay`: Weight decay (default: 0.01)

### evaluate_camembert.py

Evaluates trained model and compares with baseline.

**Features:**
- Sentence-level accuracy (origin AND destination must be correct)
- Performance by difficulty (easy/medium/hard)
- Performance by category (standard, name_ambiguity, misspelling, etc.)
- Error analysis (saves incorrect predictions to CSV)
- Baseline comparison

**Usage:**
```bash
python scripts/evaluate_camembert.py
```

**Input:**
- `models/camembert-ner/` (trained model)
- `data/test_ner.json` (test set)

**Output:**
- Console: Comparison table
- `results/camembert_evaluation.json`
- `results/camembert_errors.csv`

## Pipeline Overview

```
dataset_final.csv
    ↓
[convert_dataset_to_ner.py]
    ↓
train_ner.json, val_ner.json, test_ner.json
    ↓
[train_camembert.py]
    ↓
models/camembert-ner/
    ↓
[evaluate_camembert.py]
    ↓
results/camembert_evaluation.json
results/camembert_errors.csv
```

## Expected Results

### Conversion

```
Converting Travel Order Dataset to NER Format

Loading dataset from data/dataset_final.csv
Loaded 10000 sentences

Splitting dataset (70% train, 15% val, 15% test)

TRAIN Statistics:
  Total examples: 7000
  Valid orders: 4900 (70.0%)
  Label distribution:
    O: 38289 (74.9%)
    B-ORIGIN: 4495 (8.8%)
    I-ORIGIN: 1998 (3.9%)
    B-DEST: 4490 (8.8%)
    I-DEST: 1882 (3.7%)
```

### Training

```
Epoch 1/4
Step 100/437 | Loss: 0.125 | LR: 1.5e-5
Step 200/437 | Loss: 0.089 | LR: 2.0e-5
...
Validation F1: 0.8234

Epoch 2/4
...
Validation F1: 0.8567

...

Training completed!
Best model F1: 0.8723
```

### Evaluation

```
PERFORMANCE COMPARISON: Baseline vs CamemBERT

Overall Accuracy:
  Baseline:   70.00%
  CamemBERT:  87.50%
  Improvement: +17.50%

Performance by Difficulty:
  easy            87.14%          95.20%          +8.06%
  medium          73.39%          88.50%          +15.11%
  hard            34.84%          71.30%          +36.46%

Target achieved! (>= 85% accuracy)
```

## Troubleshooting

### CUDA Out of Memory

Reduce batch size:
```bash
python scripts/train_camembert.py --batch-size 8
```

### Slow Training

Use GPU or Google Colab with GPU runtime.

### Import Errors

Ensure you're in project root:
```bash
cd /path/to/T-AIA-911-TRAVEL-ORDER-RESOLVER
python scripts/train_camembert.py
```

### Low Accuracy

Try more epochs or different learning rate:
```bash
python scripts/train_camembert.py --epochs 6 --learning-rate 3e-5
```

## Requirements

```
transformers>=4.30.0
datasets>=2.12.0
torch>=2.0.0
accelerate>=0.20.0
evaluate
seqeval
scikit-learn
```

Install with:
```bash
pip install -r requirements.txt
```

## Documentation

See [docs/camembert_training.md](../docs/camembert_training.md) for comprehensive training guide.

---

**Last Updated**: 2026-01-16
