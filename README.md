# 🚄 Travel Order Resolver

> Projet EPITECH T-AIA-911 — Extraction d'ordres de voyage en français avec NLP + calcul d'itinéraires sur le réseau SNCF.

---

## Résultats clés

| Modèle | Exact match | Origine | Destination |
|---|---|---|---|
| Baseline (règles) | 60.1% | 74.9% | 71.8% |
| **CamemBERT fine-tuné** | **96.76%** | **98.1%** | **97.5%** |

Dataset : 10 000 phrases françaises (train / val / test) — 15 catégories de difficulté.

---

## Installation

```powershell
git clone <url>
cd T-AIA-911-TRAVEL-ORDER-RESOLVER

python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate   # Linux / Mac

pip install -r requirements.txt
```

> Le modèle CamemBERT (~440 MB) doit être placé dans `models/camembert-ner/`.
> Voir [models/README.md](models/README.md) pour le lien de téléchargement.

---

## Démarrage rapide

### Interface graphique (recommandé)

```powershell
streamlit run app.py
```

Ouvre **http://localhost:8501** avec 6 onglets :

| Onglet | Contenu |
|---|---|
| 🏠 Projet | Architecture, résultats clés, exemples |
| 📊 Données | Exploration du dataset par catégorie / difficulté |
| 🔍 Extraction NLP | Tester une phrase — Baseline vs CamemBERT côte à côte |
| 🗺️ Itinéraire | Route optimale avec carte interactive du réseau SNCF |
| 📈 Évaluation | Métriques complètes + graphiques (live ou pré-calculés) |
| 📁 Pipeline CSV | Uploader un CSV, traiter, télécharger les résultats |

### CLI

```powershell
# Mode interactif (phrase + itinéraire en direct)
python main.py --interactive
python main.py -I --model camembert

# Traitement d'un fichier CSV
python main.py -i data/demo/input_demo.csv -o out.csv
python main.py -i data/demo/input_demo.csv -o out.csv --model camembert
python main.py -i data/demo/input_demo.csv -o out.csv -m full-pipeline --model camembert

# Évaluation sur le dataset
python main.py --evaluate --split val
python main.py --evaluate --split test --model camembert

# Préparer les données pour le fine-tuning CamemBERT
python main.py --prepare-data
```

---

## Formats I/O

**Entrée** : `sentenceID,sentence` (UTF-8)

```csv
sentenceID,sentence
1,Je veux aller de Paris à Lyon
2,j'veu alé de roquefort-les-pins @ niiice
3,Bonjour comment allez-vous
```

**Sortie `--mode nlp-only`** :
```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,roquefort-les-pins,nice
3,INVALID,INVALID
```

**Sortie `--mode full-pipeline`** :
```csv
sentenceID,Departure,Step1,...,Destination
1,Paris,Lyon
2,roquefort-les-pins,Cannes,...,Nice
```

---

## Architecture

```
Phrase → Prétraitement → Extraction NLP → Mapping UIC → Dijkstra → Itinéraire
                              ↑
                    Baseline (règles) ou CamemBERT (NER fine-tuné)
```

### Modules principaux (`src/`)

| Module | Rôle |
|---|---|
| `nlp/preprocessing.py` | Normalisation : accents, tirets, casse, caractères spéciaux |
| `nlp/gazetteer.py` | Base de 66 villes + fuzzy matching (Levenshtein ≤ 2) |
| `nlp/baseline.py` | Extracteur par mots-clés français (de/depuis, à/vers/pour) |
| `nlp/transformer.py` | CamemBERT fine-tuné sur 7 000 phrases (BIO tagging) |
| `nlp/postprocessing.py` | Reconstruction noms composés, validation gazetteer |
| `nlp/data_preparation.py` | Conversion BIO word-level → subwords pour Trainer HuggingFace |
| `pathfinding/graph_loader.py` | Graphe NetworkX depuis données GTFS SNCF (2 782 gares) |
| `pathfinding/algorithms.py` | Dijkstra sur codes UIC |
| `utils/pipeline.py` | Orchestration bout-en-bout |
| `utils/io_handler.py` | Lecture/écriture CSV (UTF-8) |
| `evaluation/metrics.py` | Precision / Recall / F1 / exact match par catégorie |

### Réseau ferroviaire

- **Source** : GTFS SNCF officiel (`data/raw/sncf/gtfs/`)
- **Gares** : 2 782 stations avec coordonnées GPS
- **Connexions** : 11 230 segments bidirectionnels avec durées réelles (stop_times.txt)
- **Algorithme** : Dijkstra — poids = durée en minutes

---

## Dataset

10 000 phrases générées avec 15 catégories :

| Catégorie | Description |
|---|---|
| `standard` | Phrases bien formées avec mots-clés |
| `misspelling` | Fautes d'orthographe (le plus difficile — 10.9% baseline) |
| `no_capitals` | Sans majuscules |
| `inverted_order` | Destination avant origine |
| `compound_name` | Villes composées (Aix-en-Provence, Port-Boulet) |
| `complex_question` | Structures grammaticales complexes |
| `name_ambiguity` | Noms ambigus (Paris comme prénom, etc.) |
| `garbage` / `no_intent` | Phrases sans ordre de voyage (invalides) |

Split : **7 000 train / 1 500 val / 1 500 test** (seed=42)

---

## Entraînement CamemBERT

```powershell
# 1. Convertir le dataset en format NER (BIO)
python scripts/camembert/convert_dataset_to_ner.py

# 2. Tokeniser pour le Trainer HuggingFace
python main.py --prepare-data

# 3. Entraîner (20 epochs, lr=2e-5, batch=16)
python scripts/camembert/train_camembert.py

# 4. Évaluer
python scripts/camembert/evaluate_camembert.py
```

Paramètres du modèle : `camembert-base`, 20 epochs, lr=2e-5, batch_size=16/32, max_length=128.

---

## Tests

```powershell
# Tous les tests
python -m pytest tests/ -v

# Un module spécifique
python -m pytest tests/test_postprocessing.py -v

# Avec couverture
python -m pytest tests/ --cov=src --cov-report=html
```

---

## Structure du projet

```
├── app.py                          # Interface Streamlit (streamlit run app.py)
├── main.py                         # CLI principal
├── requirements.txt
│
├── src/
│   ├── nlp/                        # Extraction NLP
│   │   ├── preprocessing.py
│   │   ├── gazetteer.py
│   │   ├── baseline.py
│   │   ├── transformer.py          # CamemBERT
│   │   ├── postprocessing.py
│   │   └── data_preparation.py     # Tokenisation GTFS -> HuggingFace
│   ├── pathfinding/
│   │   ├── graph_loader.py         # NetworkX depuis GTFS
│   │   └── algorithms.py           # Dijkstra
│   ├── utils/
│   │   ├── pipeline.py             # Orchestration
│   │   └── io_handler.py
│   └── evaluation/
│       └── metrics.py              # Precision / Recall / F1
│
├── data/
│   ├── raw/sncf/gtfs/              # Données GTFS SNCF officielles
│   └── processed/
│       ├── train.csv / val.csv / test.csv
│       ├── *_ner.json              # Labels BIO word-level
│       └── sncf/                   # Gares, connexions, mapping UIC
│
├── models/
│   └── camembert-ner/              # Modèle fine-tuné (~440 MB)
│
├── tests/                          # Tests unitaires
├── scripts/                        # Scripts dataset, entraînement, évaluation
└── results/                        # Résultats d'évaluation JSON/CSV
```

---

## Liens

- Modèle CamemBERT : voir [models/README.md](models/README.md)
- Sujet du projet : [docs/project.pdf](docs/project.pdf)
- Jira : `travel-order-resolver.atlassian.net` (projet `KAN`)
