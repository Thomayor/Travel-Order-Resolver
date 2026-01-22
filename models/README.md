# Models Directory

This directory contains trained models for the Travel Order Resolver project.

## CamemBERT NER Model

The fine-tuned CamemBERT model for Named Entity Recognition is **not included in this repository** due to its large size (~440MB).

### Option 1: Download Pre-trained Model (Recommended)

**For team members:** Download the pre-trained model to avoid re-training.

1. **Download link**: [TO BE ADDED - Upload to Google Drive/HuggingFace after training]

2. **Extract to this directory**:
   ```bash
   # Expected structure:
   models/
   └── camembert-ner/
       ├── config.json
       ├── pytorch_model.bin
       ├── tokenizer_config.json
       ├── sentencepiece.bpe.model
       └── special_tokens_map.json
   ```

3. **Verify installation**:
   ```bash
   python scripts/demo_camembert.py
   ```

### Option 2: Train Model Yourself

If you want to train the model from scratch:

#### Prerequisites
- GPU with CUDA support (recommended: RTX 3070 or better)
- PyTorch with CUDA installed
- 2-4 hours training time

#### Steps

1. **Install PyTorch with CUDA**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

2. **Verify GPU**:
   ```bash
   python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
   ```

3. **Convert dataset** (if not already done):
   ```bash
   python scripts/convert_dataset_to_ner.py
   ```

4. **Train model**:
   ```bash
   python scripts/train_camembert.py
   ```

5. **Evaluate**:
   ```bash
   python scripts/evaluate_camembert.py
   ```

### Model Performance

**Target**: ≥85% accuracy (vs 70% baseline)

Expected results after training:
- Overall Accuracy: **87-90%**
- Easy sentences: **95%+**
- Medium sentences: **88-92%**
- Hard sentences: **70-75%**

See [docs/camembert_training.md](../docs/camembert_training.md) for detailed training guide.

---

## Model Sharing Instructions (For Trainer)

After training the model, the person who trained it should:

1. **Compress the model**:
   ```bash
   # Windows
   tar -czf camembert-ner.tar.gz camembert-ner/

   # Or use 7-Zip / WinRAR
   ```

2. **Upload to cloud storage**:
   - Google Drive (team shared folder)
   - HuggingFace Hub
   - OneDrive / Dropbox

3. **Update this README** with download link

4. **Share results**:
   - Commit `results/camembert_evaluation.json`
   - Commit `results/camembert_errors.csv`
   - Update team on performance metrics

---

## Directory Structure

```
models/
├── README.md                    # This file
├── camembert-ner/               # Fine-tuned model (not in Git)
│   ├── config.json
│   ├── pytorch_model.bin        (~440MB)
│   ├── tokenizer_config.json
│   ├── sentencepiece.bpe.model
│   ├── special_tokens_map.json
│   └── logs/                    # TensorBoard logs (not in Git)
└── checkpoint-*/                # Training checkpoints (not in Git)
```

---

## FAQ

### Q: Why is the model not in the repository?

The model is ~440MB, which is too large for Git. Using Git LFS would require all team members to install and configure it. Instead, we share via cloud storage.

### Q: Can I use the model without training?

Yes! Download the pre-trained model using Option 1 above. Only one team member needs to train.

### Q: What if I get CUDA out of memory?

Reduce batch size:
```bash
python scripts/train_camembert.py --batch-size 8
```

### Q: Training takes too long on my machine?

Use Google Colab with free GPU (Tesla T4, ~2-4 hours):
1. Upload project to Google Drive
2. Open Colab notebook with GPU runtime
3. Run training script

---

**Last Updated**: 2026-01-16
