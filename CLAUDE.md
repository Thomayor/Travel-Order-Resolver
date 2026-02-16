# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# 🚄 Travel Order Resolver - Guide de démarrage

## 📋 Vue d'ensemble

Ce projet extrait automatiquement l'origine et la destination à partir de phrases en français et calcule des itinéraires sur le réseau SNCF.

**Exemple** :
- Entrée : `"Je veux aller de Paris à Lyon"`
- Sortie : `Paris → Lyon` + itinéraire complet

**Performance** : 96.76% de précision avec CamemBERT (vs 60% avec le baseline)

---

## ⚙️ Installation (obligatoire pour tout)

```bash
# 1. Ouvrir un terminal dans le dossier du projet
cd T-AIA-911-TRAVEL-ORDER-RESOLVER

# 2. Créer un environnement virtuel (optionnel mais recommandé)
python -m venv .venv

# 3. Activer l'environnement

# Windows PowerShell
.venv\Scripts\activate

# Windows Git Bash / Linux / Mac
source .venv/Scripts/activate   # Git Bash sur Windows
# source .venv/bin/activate     # Linux/Mac

# Si vous êtes sur Windows avec Git Bash, utilisez:
# source .venv/Scripts/activate

# 4. Installer toutes les dépendances
pip install -r requirements.txt
```

**Temps d'installation** : ~5 minutes

**Dépendances principales installées** :
- `streamlit` : Interface web
- `transformers` + `torch` : Modèle CamemBERT
- `networkx` : Graphe du réseau SNCF
- `pandas`, `numpy` : Traitement des données

---

## 🎯 Option 1 : Interface Web Streamlit (RECOMMANDÉ pour débuter)

### Lancer l'application

```bash
# Depuis le terminal, dans le dossier du projet
streamlit run app.py
```

**Résultat** : Votre navigateur s'ouvre automatiquement sur `http://localhost:8501`

### Utilisation de l'interface

L'application contient **6 onglets** :

#### 🔍 Onglet "Extraction NLP" (le plus utilisé)

1. Entrer une phrase dans la zone de texte
2. Cliquer sur "Extraire"
3. Voir le résultat : origine et destination détectées

**Exemples à tester** :
```
Je veux aller de Paris à Lyon
Billet Marseille Nice
j'veu alé de parris @ lyyon
De Bordeaux vers Toulouse
```

#### 🗺️ Onglet "Itinéraire"

1. Entrer une phrase avec origine et destination
2. Voir l'itinéraire complet avec carte interactive
3. Durée du trajet + arrêts intermédiaires

#### 📁 Onglet "Pipeline CSV"

1. Uploader un fichier CSV au format :
   ```csv
   sentenceID,sentence
   1,Je veux aller de Paris à Lyon
   2,Billet Marseille Nice
   ```
2. Choisir le modèle (Baseline ou CamemBERT)
3. Cliquer sur "Traiter"
4. Télécharger les résultats

#### 📊 Onglet "Données"

Explorer les 10 000 phrases du dataset par catégorie et difficulté.

#### 📈 Onglet "Évaluation"

Voir les métriques de performance (précision, recall, F1).

#### 🏠 Onglet "Projet"

Présentation du projet et architecture.

### Arrêter l'application

Dans le terminal, appuyer sur `Ctrl + C`

---

## 💻 Option 2 : Ligne de commande Python (CLI)

### Usage basique : Traiter un fichier CSV

#### Étape 1 : Créer un fichier d'entrée

Créer un fichier `input.csv` avec ce format :

```csv
sentenceID,sentence
1,Je veux aller de Paris à Lyon
2,Billet Marseille Nice
3,Bonjour comment allez-vous
```

#### Étape 2 : Lancer le traitement

**Avec le modèle Baseline** (rapide, 60% de précision) :
```bash
python main.py --input input.csv --output resultats.csv
```

**Avec CamemBERT** (lent, 96% de précision - RECOMMANDÉ) :
```bash
python main.py --input input.csv --output resultats.csv --model camembert
```

**Avec itinéraire complet** :
```bash
python main.py --input input.csv --output resultats.csv --model camembert --mode full-pipeline
```

#### Étape 3 : Voir les résultats

Ouvrir le fichier `resultats.csv` :

**Mode normal (NLP-only)** :
```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,Marseille,Nice
3,INVALID,INVALID
```

**Mode full-pipeline** :
```csv
sentenceID,Departure,Step1,Step2,Destination
1,Paris,Lyon
2,Marseille,Cannes,Grasse,Nice
3,INVALID,INVALID
```

### Mode interactif : Tester des phrases en direct

```bash
# Lancer le mode interactif
python main.py --interactive

# Ou version courte
python main.py -I

# Avec CamemBERT (recommandé)
python main.py -I --model camembert
```

**Exemple d'utilisation** :
```
$ python main.py -I --model camembert

=== Mode interactif ===
Entrez une phrase (ou 'quit' pour quitter) :

> Je veux aller de Paris à Lyon
✓ Origine: Paris
✓ Destination: Lyon

> j'veu alé de parris @ lyyon
✓ Origine: Paris
✓ Destination: Lyon

> Bonjour comment allez-vous
✗ INVALID,INVALID (pas d'ordre de voyage)

> quit
Au revoir !
```

### Évaluer les modèles

**Évaluer le Baseline sur la validation** :
```bash
python main.py --evaluate --split val
```

**Évaluer CamemBERT sur le test** :
```bash
python main.py --evaluate --split test --model camembert
```

**Résultat affiché** :
```
=== Résultats d'évaluation ===
Exact match: 96.76%
Origin accuracy: 98.1%
Destination accuracy: 97.5%
```

---

## 📖 Résumé des commandes principales

### Streamlit (Interface Web)

```bash
# Lancer l'interface web
streamlit run app.py

# Avec un port personnalisé
streamlit run app.py --server.port 8502
```

### Python CLI

```bash
# Traiter un fichier CSV (baseline)
python main.py -i input.csv -o output.csv

# Traiter avec CamemBERT (précis)
python main.py -i input.csv -o output.csv --model camembert

# Traiter avec itinéraire complet
python main.py -i input.csv -o output.csv --model camembert --mode full-pipeline

# Mode interactif
python main.py -I
python main.py -I --model camembert

# Évaluer les modèles
python main.py --evaluate --split val
python main.py --evaluate --split test --model camembert

# Afficher l'aide
python main.py --help
```

---

## 🔧 Tests et développement

### Lancer les tests unitaires

```bash
# Tous les tests (103 tests)
python -m pytest tests/ -v

# Un module spécifique
python -m pytest tests/test_baseline.py -v

# Avec rapport de couverture
python -m pytest tests/ --cov=src --cov-report=html
```

### Scripts de démonstration

```bash
# Démo du preprocessing (normalisation du texte)
python scripts/demos/demo_preprocessing.py

# Démo du gazetteer (matching de villes)
python scripts/demos/demo_gazetteer.py

# Démo du baseline (extraction)
python scripts/demos/demo_baseline.py

# Démo du pipeline complet
python scripts/demos/demo_pipeline.py

# Démo de l'évaluation
python scripts/demos/demo_evaluation_metrics.py

# Démo de visualisation d'itinéraire
python scripts/demos/demo_visualize_route.py
```

### Entraîner CamemBERT (avancé)

```bash
# 1. Convertir le dataset en format NER
python scripts/camembert/convert_dataset_to_ner.py

# 2. Préparer les données tokenisées
python main.py --prepare-data

# 3. Entraîner le modèle (~2h sur GPU, ~12h sur CPU)
python scripts/camembert/train_camembert.py

# 4. Évaluer le modèle entraîné
python scripts/camembert/evaluate_camembert.py

# 5. Tester le modèle
python scripts/camembert/demo_camembert.py
```

---

## 🛠️ Dépannage

### Erreur : `ModuleNotFoundError: No module named 'streamlit'`

**Solution** :
```bash
pip install -r requirements.txt
```

### Erreur : `OSError: models/camembert-ner/ not found`

**Cause** : Le modèle CamemBERT n'est pas téléchargé.

**Solution** : Voir `models/README.md` pour le lien de téléchargement.

Le modèle doit être placé dans `models/camembert-ner/` avec ces fichiers :
- `config.json`
- `pytorch_model.bin`
- `tokenizer_config.json`
- etc.

### Erreur : `Address already in use` (Streamlit)

**Cause** : Le port 8501 est déjà occupé.

**Solution** :
```bash
# Utiliser un autre port
streamlit run app.py --server.port 8502

# Ou arrêter le processus existant
# Windows
taskkill /F /IM streamlit.exe

# Linux/Mac
killall streamlit
```

### Erreur : `UnicodeDecodeError` sur les fichiers CSV

**Cause** : Le fichier n'est pas en UTF-8.

**Solution** : Sauvegarder le fichier CSV en UTF-8 (dans Excel : "Enregistrer sous" → "CSV UTF-8")

### CamemBERT très lent

**Cause** : Pas de GPU disponible (utilise le CPU).

**Vérifier** :
```bash
python -c "import torch; print('GPU disponible:', torch.cuda.is_available())"
```

**Astuce** : Le Baseline est 100x plus rapide mais moins précis (60% vs 96%)

---

## 📊 Structure du projet

```
T-AIA-911-TRAVEL-ORDER-RESOLVER/
├── app.py                          # Interface Streamlit (streamlit run app.py)
├── main.py                         # CLI principal (python main.py)
├── requirements.txt                # Dépendances Python
│
├── src/                            # Code source
│   ├── nlp/                        # Extraction NLP
│   │   ├── preprocessing.py        # Normalisation du texte
│   │   ├── gazetteer.py            # Base de villes + fuzzy matching
│   │   ├── baseline.py             # Modèle à règles (60%)
│   │   ├── transformer.py          # CamemBERT (96%)
│   │   ├── postprocessing.py       # Extraction entités BIO
│   │   └── data_preparation.py     # Tokenisation
│   ├── pathfinding/
│   │   ├── graph_loader.py         # Chargement réseau SNCF
│   │   └── algorithms.py           # Dijkstra
│   ├── utils/
│   │   ├── pipeline.py             # Orchestration
│   │   └── io_handler.py           # Lecture/écriture CSV
│   └── evaluation/
│       └── metrics.py              # Métriques de performance
│
├── data/
│   ├── processed/                  # Données prétraitées
│   │   ├── train.csv               # 7000 phrases
│   │   ├── val.csv                 # 1500 phrases
│   │   ├── test.csv                # 1500 phrases
│   │   └── sncf/                   # Réseau SNCF (2782 gares)
│   └── demo/
│       └── input_demo.csv          # Fichier d'exemple
│
├── models/
│   └── camembert-ner/              # Modèle CamemBERT fine-tuné (~440 MB)
│
├── scripts/
│   ├── demos/                      # Scripts de démonstration
│   ├── camembert/                  # Entraînement CamemBERT
│   ├── dataset_generation/         # Génération dataset
│   └── baseline_evaluation/        # Évaluation baseline
│
└── tests/                          # Tests unitaires (103 tests)
```

---

## 🎯 Pour aller plus loin

### Format des données

**CSV d'entrée** :
```csv
sentenceID,sentence
1,Je veux aller de Paris à Lyon
2,Billet Marseille Nice
```

**CSV de sortie (NLP-only)** :
```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,Marseille,Nice
```

**CSV de sortie (full-pipeline)** :
```csv
sentenceID,Departure,Step1,Step2,Destination
1,Paris,Lyon
2,Marseille,Cannes,Grasse,Nice
```

### Performance des modèles

| Modèle | Précision | Vitesse |
|--------|-----------|---------|
| **Baseline** | 60.1% | ⚡ Très rapide |
| **CamemBERT** | 96.76% | 🐢 Lent (GPU recommandé) |

**Catégories difficiles pour le Baseline** :
- Fautes d'orthographe : 9.3% (❌)
- Noms ambigus : 1.0% (❌)
- Questions complexes : 43.2% (⚠️)

**CamemBERT** : Résout tous ces problèmes → ~95-99% sur toutes les catégories

### Options de main.py

```bash
python main.py --help

Options:
  -i, --input FILE          Fichier CSV d'entrée
  -o, --output FILE         Fichier CSV de sortie
  -m, --mode MODE           nlp-only ou full-pipeline (défaut: nlp-only)
  --model MODEL             baseline ou camembert (défaut: baseline)
  --model-path PATH         Chemin du modèle CamemBERT
  -I, --interactive         Mode interactif
  -e, --evaluate            Évaluer sur un dataset
  --split SPLIT             val ou test (défaut: val)
  --prepare-data            Préparer données pour entraînement
  -v, --verbose             Logs détaillés
  -h, --help                Afficher l'aide
```

---

## 📝 Exemples d'utilisation

### Exemple 1 : Test rapide avec Streamlit

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer Streamlit
streamlit run app.py

# 3. Dans le navigateur, aller dans l'onglet "🔍 Extraction NLP"

# 4. Tester cette phrase :
"Je veux aller de Paris à Lyon"

# 5. Résultat : Paris → Lyon
```

### Exemple 2 : Traiter un fichier CSV

```bash
# 1. Créer input.csv :
echo "sentenceID,sentence" > input.csv
echo "1,Je veux aller de Paris à Lyon" >> input.csv
echo "2,Billet Marseille Nice" >> input.csv

# 2. Traiter avec CamemBERT
python main.py -i input.csv -o output.csv --model camembert

# 3. Voir le résultat
cat output.csv
# sentenceID,Departure,Destination
# 1,Paris,Lyon
# 2,Marseille,Nice
```

### Exemple 3 : Mode interactif

```bash
# Lancer le mode interactif avec CamemBERT
python main.py -I --model camembert

# Tester ces phrases :
"Je veux aller de Paris à Lyon"
"j'veu alé de parris @ lyyon"  # Avec fautes
"Billet Marseille Nice"
"Bonjour"  # Invalid
```

### Exemple 4 : Calculer un itinéraire complet

```bash
# Créer input.csv avec une phrase
echo "sentenceID,sentence" > input.csv
echo "1,Je veux aller de Paris à Marseille" >> input.csv

# Traiter en mode full-pipeline
python main.py -i input.csv -o itineraire.csv --model camembert --mode full-pipeline

# Voir l'itinéraire complet
cat itineraire.csv
# sentenceID,Departure,Step1,Step2,Step3,Destination
# 1,Paris,Lyon,Valence,Avignon,Marseille
```

---

## ✅ Checklist de démarrage

- [ ] Python 3.9+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Modèle CamemBERT téléchargé (si on veut 96% de précision)
- [ ] Terminal ouvert dans le dossier du projet

**Ensuite, au choix** :

**Option A : Interface Web (débutant)**
- [ ] Lancer `streamlit run app.py`
- [ ] Tester des phrases dans l'onglet "🔍 Extraction NLP"

**Option B : CLI (avancé)**
- [ ] Créer un fichier `input.csv`
- [ ] Lancer `python main.py -i input.csv -o output.csv --model camembert`
- [ ] Consulter `output.csv`

---

## 🔗 Ressources

- **README.md** : Présentation complète (français)
- **GUIDE_TEST.md** : Guide des tests unitaires
- **models/README.md** : Téléchargement du modèle CamemBERT
- **docs/** : Documentation technique détaillée

---

## 💡 Conseils

### Pour débuter
1. ✅ Utiliser Streamlit (`streamlit run app.py`)
2. ✅ Tester des phrases dans l'onglet "🔍 Extraction NLP"
3. ✅ Comparer Baseline vs CamemBERT sur les mêmes phrases

### Pour la production
1. ✅ Utiliser CamemBERT (96% de précision)
2. ✅ Mode CLI pour traiter de gros fichiers CSV
3. ✅ GPU recommandé pour la vitesse

### Pour le développement
1. ✅ Lancer les tests : `python -m pytest tests/ -v`
2. ✅ Utiliser les scripts de démo dans `scripts/demos/`
3. ✅ Mode interactif pour tester rapidement : `python main.py -I --model camembert`

---

**Projet EPITECH T-AIA-911 — Travel Order Resolver**

*Extraction d'ordres de voyage en français + calcul d'itinéraires SNCF*
