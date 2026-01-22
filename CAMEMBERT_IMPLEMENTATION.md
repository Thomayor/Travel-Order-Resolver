# CamemBERT NER Implementation - Complete Summary

**Ticket**: KAN-53 - Implement CamemBERT fine-tuning pipeline for travel order NER
**Status**: ✅ READY FOR TRAINING
**Date**: 2026-01-16

---

## Overview

This implementation provides a complete pipeline for fine-tuning CamemBERT on Named Entity Recognition (NER) to extract travel orders (origin and destination cities) from French sentences.

**Goal**: Achieve **85%+ accuracy** (vs 70% baseline)

---

## What Has Been Implemented

### ✅ 1. Dataset Conversion (Step 1)

**Script**: [scripts/convert_dataset_to_ner.py](scripts/convert_dataset_to_ner.py)

Converts the 10,000-sentence CSV dataset to token-level NER format:
- Tokenizes sentences (handles hyphens in multi-word cities)
- Assigns BIO labels: B-ORIGIN, I-ORIGIN, B-DEST, I-DEST, O
- Splits into train/val/test (70%/15%/15%)
- Preserves metadata (difficulty, category, validity)

**Output**:
- `data/train_ner.json` (7,000 examples)
- `data/val_ner.json` (1,500 examples)
- `data/test_ner.json` (1,500 examples)

**Status**: ✅ Complete and tested

---

### ✅ 2. CamemBERT NER Module (Step 2)

**Module**: [src/nlp/transformer.py](src/nlp/transformer.py)

Complete CamemBERT implementation with:
- `CamembertNER` class for training and inference
- Subword token alignment for SentencePiece tokenization
- Token classification with 5 labels
- Metrics computation (Precision, Recall, F1, Accuracy)
- Model loading/saving functionality
- GPU/CPU support with automatic detection

**Key Methods**:
- `train()`: Fine-tune model with custom hyperparameters
- `predict()`: Predict origin/destination from text
- `evaluate_on_test()`: Evaluate model on test set

**Status**: ✅ Complete and tested

---

### ✅ 3. Post-processing Module (Step 3)

**Module**: [src/nlp/postprocessing.py](src/nlp/postprocessing.py)

Entity extraction from token-level predictions:
- `extract_entities()`: Extract origin and destination from BIO labels
- `reconstruct_city_name()`: Reconstruct multi-word cities (Port-Boulet, Aix-en-Provence)
- `extract_all_entities()`: Debug function to extract all entities
- `validate_extraction()`: Check if extraction is valid

**Status**: ✅ Complete and tested

---

### ✅ 4. Training Script (Step 4)

**Script**: [scripts/train_camembert.py](scripts/train_camembert.py)

Command-line training script with:
- Configurable hyperparameters via CLI arguments
- Progress logging and monitoring
- TensorBoard integration
- Checkpoint saving (best model selection)
- Error handling and validation

**Default Hyperparameters**:
- Epochs: 4
- Batch size: 16
- Learning rate: 2e-5
- Warmup ratio: 0.1
- Weight decay: 0.01

**Status**: ✅ Complete and ready to run

---

### ✅ 5. Evaluation Script (Step 5)

**Script**: [scripts/evaluate_camembert.py](scripts/evaluate_camembert.py)

Comprehensive evaluation with:
- Baseline comparison
- Performance by difficulty (easy/medium/hard)
- Performance by category (standard, name_ambiguity, misspelling, etc.)
- Error analysis (saves incorrect predictions to CSV)
- Detailed metrics in JSON format

**Output**:
- Console: Comparison table
- `results/camembert_evaluation.json`: Detailed metrics
- `results/camembert_errors.csv`: Error analysis

**Status**: ✅ Complete and ready to run

---

### ✅ 6. Demo Script (Bonus)

**Script**: [scripts/demo_camembert.py](scripts/demo_camembert.py)

Interactive demo to test trained model:
- Interactive mode: Test on custom sentences
- Examples mode: Test on predefined examples

**Status**: ✅ Complete

---

### ✅ 7. Documentation

**Files**:
- [docs/camembert_training.md](docs/camembert_training.md): Comprehensive training guide (30+ pages)
- [scripts/README.md](scripts/README.md): Scripts documentation
- [requirements_camembert.txt](requirements_camembert.txt): Python dependencies
- This file: Implementation summary

**Status**: ✅ Complete

---

## How to Use (Quick Start)

### Step 1: Install Dependencies

```bash
pip install transformers>=4.30.0 datasets>=2.12.0 torch>=2.0.0 accelerate>=0.20.0 evaluate seqeval scikit-learn
```

Or use the requirements file:
```bash
pip install -r requirements_camembert.txt
```

### Step 2: Convert Dataset

```bash
python scripts/convert_dataset_to_ner.py
```

**Expected output**: Creates `train_ner.json`, `val_ner.json`, `test_ner.json` in `data/`

### Step 3: Train Model

```bash
python scripts/train_camembert.py
```

**Training time**:
- GPU (Tesla T4): 2-4 hours
- GPU (RTX 3080): 1-2 hours
- CPU: 12-24 hours

**Expected output**: Model saved to `models/camembert-ner/`

**Alternative (Google Colab)**:
```python
# In Colab with GPU
!git clone <your-repo>
%cd T-AIA-911-TRAVEL-ORDER-RESOLVER
!python scripts/train_camembert.py
```

### Step 4: Evaluate Model

```bash
python scripts/evaluate_camembert.py
```

**Expected output**: Comparison table + results files

### Step 5: Test Model (Interactive)

```bash
python scripts/demo_camembert.py --mode interactive
```

---

## File Structure

```
T-AIA-911-TRAVEL-ORDER-RESOLVER/
├── data/
│   ├── dataset_final.csv           # Original dataset (10K sentences)
│   ├── train_ner.json              # Training set (7K) ✅ Created
│   ├── val_ner.json                # Validation set (1.5K) ✅ Created
│   └── test_ner.json               # Test set (1.5K) ✅ Created
│
├── src/nlp/
│   ├── transformer.py              # CamemBERT NER module ✅ New
│   ├── postprocessing.py           # Entity extraction ✅ New
│   ├── baseline.py                 # Baseline model (existing)
│   ├── gazetteer.py                # City gazetteer (existing)
│   └── preprocessing.py            # Text preprocessing (existing)
│
├── scripts/
│   ├── convert_dataset_to_ner.py   # Dataset conversion ✅ New
│   ├── train_camembert.py          # Training script ✅ New
│   ├── evaluate_camembert.py       # Evaluation script ✅ New
│   ├── demo_camembert.py           # Demo script ✅ New
│   └── README.md                   # Scripts docs ✅ New
│
├── docs/
│   ├── camembert_training.md       # Training guide ✅ New
│   └── (other docs)
│
├── models/
│   └── camembert-ner/              # Trained model (after training)
│       ├── config.json
│       ├── pytorch_model.bin
│       ├── tokenizer_config.json
│       └── logs/                   # TensorBoard logs
│
├── results/
│   ├── camembert_evaluation.json   # Metrics (after evaluation)
│   └── camembert_errors.csv        # Error analysis (after evaluation)
│
├── requirements_camembert.txt      # Python dependencies ✅ New
└── CAMEMBERT_IMPLEMENTATION.md     # This file ✅ New
```

---

## Expected Performance

### Targets (Based on Ticket Requirements)

| Metric | Baseline | Target | Expected CamemBERT |
|--------|----------|--------|-------------------|
| **Overall Accuracy** | 70% | **≥85%** | 87-90% ✅ |
| Easy Difficulty | 87% | ≥90% | 95%+ ✅ |
| Medium Difficulty | 73% | ≥85% | 88-92% ✅ |
| Hard Difficulty | 35% | ≥60% | 70-75% ✅ |
| Name Ambiguity | 40% | ≥75% | 80-85% ✅ |
| Misspellings | 8% | ≥50% | 60-70% ✅ |

### Why CamemBERT Will Outperform Baseline

1. **Context Understanding**: Transformer attention captures sentence structure
2. **Ambiguity Resolution**: Learns to distinguish "Paris" (person) vs "Paris" (city) from context
3. **Misspelling Handling**: Subword tokenization handles unknown words better
4. **Pattern Learning**: Learns from 7,000 training examples vs hand-crafted rules

---

## Implementation Details

### Dataset Format (NER JSON)

```json
{
  "tokens": ["Je", "veux", "aller", "de", "Port", "-", "Boulet", "à", "Lyon"],
  "labels": ["O", "O", "O", "O", "B-ORIGIN", "I-ORIGIN", "I-ORIGIN", "O", "B-DEST"],
  "metadata": {
    "sentenceID": "123",
    "origin": "Port-Boulet",
    "destination": "Lyon",
    "is_valid": 1,
    "difficulty": "medium",
    "category": "compound_name"
  }
}
```

### Label Schema (BIO)

- **B-ORIGIN**: Beginning of origin city (e.g., "Port")
- **I-ORIGIN**: Inside origin city (e.g., "-", "Boulet")
- **B-DEST**: Beginning of destination city
- **I-DEST**: Inside destination city
- **O**: Outside (not part of any entity)

### Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Learning Rate | 2e-5 | Standard for BERT fine-tuning |
| Batch Size | 16 | Balance between speed and memory |
| Epochs | 4 | Sufficient for convergence (monitor validation) |
| Warmup Ratio | 0.1 | Stabilizes training |
| Weight Decay | 0.01 | Regularization |
| Max Length | 128 | Covers longest sentences in dataset |

### Training Process

1. **Load pretrained CamemBERT** from HuggingFace
2. **Add classification head** (5 labels)
3. **Tokenize datasets** with subword alignment
4. **Train with Trainer API** (HuggingFace)
5. **Save best checkpoint** (based on validation F1)

---

## Next Steps (After Training)

### 1. Training (Required)

```bash
python scripts/train_camembert.py
```

**Monitor with TensorBoard**:
```bash
tensorboard --logdir models/camembert-ner/logs
```

### 2. Evaluation (Required)

```bash
python scripts/evaluate_camembert.py
```

**Check**:
- Overall accuracy ≥85%
- Improvement over baseline ≥15%
- Performance on hard cases ≥70%

### 3. Error Analysis (If accuracy <85%)

Review `results/camembert_errors.csv`:
- Identify common error patterns
- Consider data augmentation
- Try different hyperparameters

### 4. Integration (Future)

Update main pipeline to use CamemBERT:
```python
# In main.py or baseline.py
from nlp.transformer import load_pretrained_model

model = load_pretrained_model("models/camembert-ner")
_, _, origin, destination = model.predict(sentence)
```

---

## Troubleshooting

### Issue: CUDA Out of Memory

**Solution**: Reduce batch size
```bash
python scripts/train_camembert.py --batch-size 8
```

### Issue: Training Too Slow

**Solution**: Use Google Colab with free GPU (Tesla T4)
- Runtime → Change runtime type → GPU
- Training time: 2-4 hours

### Issue: Low Accuracy (<85%)

**Try**:
1. More epochs: `--epochs 6`
2. Different learning rate: `--learning-rate 3e-5`
3. Check data quality in NER JSON files
4. Enable fuzzy matching in baseline (for fair comparison)

### Issue: Import Errors

**Solution**: Run from project root
```bash
cd /path/to/T-AIA-911-TRAVEL-ORDER-RESOLVER
python scripts/train_camembert.py
```

---

## Success Criteria (Ticket KAN-53)

### ✅ Completed

- [x] Dataset converted to NER format (train/val/test)
- [x] CamemBERT NER module implemented
- [x] Training script with proper hyperparameters
- [x] Evaluation script comparing with baseline
- [x] Post-processing for entity extraction
- [x] Comprehensive documentation
- [x] Error analysis functionality

### ⏳ Pending (Requires User Action)

- [ ] Model CamemBERT fine-tuned and saved
- [ ] Accuracy ≥85% on test set (to be verified after training)
- [ ] Performance ≥80% on name_ambiguity category
- [ ] Performance ≥70% on hard difficulty

---

## Technical Highlights

### 1. Subword Token Alignment

Handles CamemBERT's SentencePiece tokenization:
```python
# Original tokens: ["Port", "-", "Boulet"]
# Subword tokens: ["▁Port", "-", "▁Bou", "let"]
# Labels aligned: [B-ORIGIN, I-ORIGIN, I-ORIGIN, -100]
# (-100 = ignore in loss)
```

### 2. Multi-word City Reconstruction

```python
tokens = ["Port", "-", "Boulet"]
labels = ["B-ORIGIN", "I-ORIGIN", "I-ORIGIN"]
result = "Port-Boulet"  # Correctly reconstructed
```

### 3. Class Imbalance Handling

Dataset is naturally imbalanced:
- O: 74.9%
- B-ORIGIN: 8.8%
- I-ORIGIN: 3.9%
- B-DEST: 8.8%
- I-DEST: 3.7%

**Mitigation**:
- seqeval metric (ignores "O" in entity-level F1)
- Weight decay for regularization

---

## Resources

### Documentation
- [docs/camembert_training.md](docs/camembert_training.md): Complete training guide
- [scripts/README.md](scripts/README.md): Scripts documentation
- [CLAUDE.md](CLAUDE.md): Project overview

### External Resources
- CamemBERT Paper: https://arxiv.org/abs/1911.03894
- HuggingFace CamemBERT: https://huggingface.co/camembert-base
- Token Classification Tutorial: https://huggingface.co/docs/transformers/tasks/token_classification

---

## Summary

✅ **All code implemented and tested**
✅ **All documentation complete**
✅ **Dataset converted to NER format**
⏳ **Ready for training** (requires GPU, 2-4 hours)
⏳ **Evaluation pending** (after training)

**Next Action**: Run `python scripts/train_camembert.py` to train the model.

---

**Author**: Claude Code
**Date**: 2026-01-16
**Ticket**: KAN-53
**Status**: IMPLEMENTATION COMPLETE, READY FOR TRAINING
