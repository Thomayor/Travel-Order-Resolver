# Models Directory

This directory contains trained models for the Travel Order Resolver project.

## CamemBERT NER Model

The fine-tuned CamemBERT model for Named Entity Recognition is **not included in this repository** due to its large size (~440MB).

### 🎯 Latest Model: v1.0 (2026-01-22)

**Performance achieved:**
- **Overall Accuracy: 96.76%** (Target: 85%) ✅
- Easy sentences: **100.00%**
- Medium sentences: **96.21%**
- Hard sentences: **93.98%**
- Improvement vs Baseline: **+52.57%**

**Training details:**
- Dataset: 10,000 sentences (7,000 train + 1,500 val + 1,500 test)
- Templates: 600 templates (200 easy / 200 medium / 200 hard)
- Distribution: 33% easy / 33% medium / 34% hard
- Epochs: 20
- Model: camembert-base fine-tuned on NER task
- See full results: [results/camembert_evaluation.json](../results/camembert_evaluation.json)

### Option 1: Download Pre-trained Model (Recommended)

**For team members:** Download the pre-trained model to avoid re-training.

1. **Download link**:

   📦 **https://drive.google.com/drive/folders/165JA7C1AGRt203LoyilBYSSXYsXLRCWZ?usp=sharing**

   *(Upload camembert-ner.tar.gz or camembert-ner.zip to shared Google Drive)*

2. **Extract to this directory**:
   ```bash
   # Windows (with tar)
   tar -xzf camembert-ner.tar.gz -C models/

   # Or use 7-Zip / WinRAR to extract to models/camembert-ner/

   # Expected structure:
   models/
   └── camembert-ner/
       ├── config.json
       ├── pytorch_model.bin         (~440MB)
       ├── tokenizer_config.json
       ├── sentencepiece.bpe.model
       └── special_tokens_map.json
   ```

3. **Verify installation**:
   ```bash
   python scripts/evaluate_camembert.py
   ```

   Expected output: **96.76% accuracy** ✅

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

### Model Performance History

**v1.0 (2026-01-22) - Current Model ✅**
- Overall Accuracy: **96.76%** (Target: 85%)
- Easy: 100.00% | Medium: 96.21% | Hard: 93.98%
- Improvement vs Baseline: **+52.57%**
- Training: 20 epochs on 600-template dataset

See [docs/FIX_CONVERT_NER_SPLIT.md](../docs/FIX_CONVERT_NER_SPLIT.md) for implementation details.

---

## Model Sharing Instructions (For Trainer)

After training the model, the person who trained it should:

1. **Compress the model**:
   ```bash
   # Option A: Using tar (Git Bash / WSL)
   cd models/
   tar -czf camembert-ner-v1.0.tar.gz camembert-ner/

   # Option B: Using 7-Zip (Windows)
   # Right-click camembert-ner/ → 7-Zip → Add to archive
   # Format: .zip or .tar.gz
   ```

2. **Upload to Google Drive**:
   - Navigate to team's shared Google Drive folder
   - Create folder: `T-AIA-911-Models/`
   - Upload `camembert-ner-v1.0.tar.gz` (~440MB compressed)
   - Set sharing permissions: "Anyone with the link can view"
   - Copy the shareable link

3. **Update this README**:
   - Replace `[GOOGLE DRIVE LINK TO BE ADDED HERE]` with actual link
   - Format: `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`
   - Commit and push the updated README

4. **Share results with team**:
   ```bash
   git add results/camembert_evaluation.json
   git add results/camembert_errors.csv
   git add models/README.md
   git commit -m "feat(KAN-53): Add CamemBERT v1.0 model (96.76% accuracy)

   - Model uploaded to Google Drive
   - Overall accuracy: 96.76% (target: 85%)
   - Performance: easy 100%, medium 96.21%, hard 93.98%
   - See models/README.md for download instructions"
   git push
   ```

5. **Notify team** with performance summary:
   ```
   🎉 CamemBERT v1.0 trained successfully!

   📊 Performance:
   - Overall: 96.76% (target: 85%) ✅
   - Easy: 100.00%
   - Medium: 96.21%
   - Hard: 93.98%

   📦 Model available on Google Drive
   📖 See models/README.md for download instructions
   ```

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

**Last Updated**: 2026-01-22 (v1.0 model trained - 96.76% accuracy)
