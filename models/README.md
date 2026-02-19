# Dossier Models

Ce dossier contient les modeles entraines pour le projet Travel Order Resolver.
Les modeles ne sont **pas inclus dans le depot Git** en raison de leur taille (~440 MB).

---

## Telechargement des modeles

### Lien Google Drive

https://drive.google.com/drive/folders/165JA7C1AGRt203LoyilBYSSXYsXLRCWZ?usp=sharing

### Instructions

Le Drive contient **3 fichiers .zip**. Il faut les telecharger et les decompresser un par un dans le dossier `models/`.

1. **Telecharger les 3 archives** depuis le lien ci-dessus

2. **Decompresser chaque archive** dans le dossier `models/` :
   - Clic droit sur chaque `.zip` -> "Extraire ici" (ou "Extract Here")
   - Ou via la ligne de commande :
     ```bash
     cd models/
     unzip camembert-ner-part1.zip
     unzip camembert-ner-part2.zip
     unzip camembert-ner-part3.zip
     ```

3. **Verifier la structure finale** :
   ```
   models/
   |-- README.md                    # Ce fichier
   |-- camembert-ner/               # Modele CamemBERT fine-tune
   |   |-- config.json
   |   |-- pytorch_model.bin        (~440 MB)
   |   |-- tokenizer_config.json
   |   |-- sentencepiece.bpe.model
   |   +-- special_tokens_map.json
   +-- train_network.pkl            # Cache du graphe NetworkX (genere automatiquement)
   ```

4. **Verifier l'installation** :
   ```bash
   python scripts/camembert/evaluate_camembert.py
   ```
   Resultat attendu : **96.76% accuracy**

---

## Modele CamemBERT NER v1.0

**Performance** :
- Precision globale : **96.76%** (objectif : 85%)
- Phrases faciles : 100.00%
- Phrases moyennes : 96.21%
- Phrases difficiles : 93.98%
- Amelioration vs Baseline : +52.57%

**Entrainement** :
- Base : `camembert-base`
- Dataset : 10 000 phrases (7 000 train + 1 500 val + 1 500 test)
- Templates : 600 (200 faciles / 200 moyens / 200 difficiles)
- Epochs : 20, lr=2e-5, batch_size=16/32, max_length=128

---

## Entrainer le modele soi-meme

Si vous souhaitez re-entrainer le modele :

### Prerequis

- GPU avec CUDA (recommande : RTX 3070 ou mieux)
- PyTorch avec CUDA installe
- 2-4 heures d'entrainement

### Etapes

```bash
# 1. Installer PyTorch avec CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Verifier le GPU
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 3. Convertir le dataset en format NER
python scripts/camembert/convert_dataset_to_ner.py

# 4. Entrainer
python scripts/camembert/train_camembert.py

# 5. Evaluer
python scripts/camembert/evaluate_camembert.py
```

---

## Cache du graphe NetworkX

Le fichier `train_network.pkl` est un cache du graphe du reseau SNCF. Il est genere automatiquement au premier lancement et accelere les demarrages suivants.

**Supprimer ce fichier** si vous modifiez :
- `src/pathfinding/graph_loader.py`
- `data/processed/sncf/connections_final_fixed.csv`
- `data/processed/sncf/stations_clean.csv`

```bash
rm -f models/train_network.pkl
```

---

## FAQ

### Pourquoi le modele n'est-il pas dans le depot ?

Le modele pese ~440 MB, trop lourd pour Git. On le partage via Google Drive.

### Erreur `OSError: models/camembert-ner/ not found`

Le modele n'a pas ete telecharge. Suivez les instructions de telechargement ci-dessus.

### CamemBERT tres lent

Verifiez que le GPU est detecte :
```bash
python -c "import torch; print('GPU:', torch.cuda.is_available())"
```
Sans GPU, utilisez le Baseline (`--model baseline`) qui est 100x plus rapide mais moins precis (60% vs 96%).
