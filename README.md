# Travel Order Resolver

> Projet EPITECH T-AIA-911 -- Extraction d'ordres de voyage en francais avec NLP + calcul d'itineraires sur le reseau SNCF.

---

## Resultats cles

| Modele | Exact match | Origine | Destination |
|---|---|---|---|
| Baseline (regles) | 60.1% | 74.9% | 71.8% |
| **CamemBERT fine-tune** | **96.76%** | **98.1%** | **97.5%** |

Dataset : 10 000 phrases francaises (train / val / test) -- 15 categories de difficulte.

---

## Prerequis

- Python 3.9+
- pip

---

## Installation

```bash
git clone <url>
cd T-AIA-911-TRAVEL-ORDER-RESOLVER

python -m venv .venv

# Windows PowerShell
.venv\Scripts\activate

# Windows Git Bash
source .venv/Scripts/activate

# Linux / Mac
source .venv/bin/activate

pip install -r requirements.txt
```

Le modele CamemBERT (~440 MB) n'est pas inclus dans le depot Git.
Voir [models/README.md](models/README.md) pour les instructions de telechargement.

---

## Demarrage rapide

### Interface graphique (recommande)

```bash
streamlit run app.py
```

Ouvre **http://localhost:8501** avec 6 onglets :

| Onglet | Contenu |
|---|---|
| Projet | Architecture, resultats cles, exemples |
| Donnees | Exploration du dataset par categorie / difficulte |
| Extraction NLP | Tester une phrase -- Baseline vs CamemBERT cote a cote |
| Itineraire | Route optimale avec carte interactive et badges TGV/TER/IC/CORRESP |
| Evaluation | Metriques completes + graphiques (live ou pre-calcules) |
| Pipeline CSV | Uploader un CSV, traiter, telecharger les resultats |

### CLI

```bash
# Mode interactif (phrase + itineraire en direct)
python main.py --interactive
python main.py -I --model camembert

# Traitement d'un fichier CSV
python main.py -i data/demo/input_demo.csv -o out.csv
python main.py -i data/demo/input_demo.csv -o out.csv --model camembert
python main.py -i data/demo/input_demo.csv -o out.csv -m full-pipeline --model camembert

# Evaluation sur le dataset
python main.py --evaluate --split val
python main.py --evaluate --split test --model camembert
```

---

## Formats d'entree / sortie

**Entree** : `sentenceID,sentence` (UTF-8)

```csv
sentenceID,sentence
1,Je veux aller de Paris a Lyon
2,j'veu ale de roquefort-les-pins @ niiice
3,Bonjour comment allez-vous
```

**Sortie `--mode nlp-only`** (defaut) :

```csv
sentenceID,Departure,Destination
1,Paris,Lyon
2,roquefort-les-pins,nice
3,INVALID,INVALID
```

**Sortie `--mode full-pipeline`** (avec itineraire complet) :

```csv
sentenceID,Departure,Step1,...,Destination
1,Paris,Lyon
2,roquefort-les-pins,Cannes,...,Nice
```

---

## Architecture

```
Phrase
  |
  v
Pretraitement (normalisation accents, casse, caracteres speciaux)
  |
  v
Extraction NLP -----> Baseline (regles, 60%)
  |                    ou CamemBERT (NER fine-tune, 96.76%)
  v
Postprocessing (reconstruction noms composes, validation gazetteer, suggestions)
  |
  v
Mapping ville -> code UIC (city_station_mapping.csv)
  |
  v
Dijkstra (routing_cost = duree x multiplicateur + penalite hop)
  |
  v
Itineraire (gares, durees, types de ligne TGV/TER/IC/CORRESP)
```

### Modules principaux (`src/`)

| Module | Role |
|---|---|
| `nlp/preprocessing.py` | Normalisation : accents, tirets, casse, caracteres speciaux |
| `nlp/gazetteer.py` | Base de 2 782 gares SNCF + fuzzy matching (Levenshtein) |
| `nlp/baseline.py` | Extracteur par mots-cles francais (de/depuis, a/vers/pour) |
| `nlp/transformer.py` | CamemBERT fine-tune sur 7 000 phrases (BIO tagging) |
| `nlp/postprocessing.py` | Reconstruction noms composes, validation gazetteer, prefixe/fuzzy |
| `nlp/data_preparation.py` | Conversion BIO word-level vers subwords pour Trainer HuggingFace |
| `pathfinding/graph_loader.py` | Graphe NetworkX depuis GTFS SNCF, correspondances intra-ville, routing_cost |
| `pathfinding/algorithms.py` | Dijkstra avec cout de routage, retourne le temps reel |
| `utils/pipeline.py` | Orchestration bout-en-bout, mapping UIC, detection villes etrangeres |
| `utils/io_handler.py` | Lecture/ecriture CSV (UTF-8) |
| `evaluation/metrics.py` | Precision / Recall / F1 / exact match par categorie |

### Reseau ferroviaire

- **Source** : GTFS SNCF officiel (`data/raw/sncf/gtfs/`)
- **Gares** : 2 782 stations avec coordonnees GPS
- **Connexions** : 10 320 segments bidirectionnels avec durees reelles (stop_times.txt)
- **Types de ligne** : TGV (492), IC (406), TER (190), TRAIN (~9 200)
- **Correspondances intra-ville** : 22 aretes (Paris 7 gares, Lyon, Lille, Marseille)
- **Algorithme** : Dijkstra avec `routing_cost` (penalise les hops inutiles, favorise TGV)

### Pathfinding intelligent

Le calcul d'itineraire utilise un **cout de routage** distinct de la duree reelle pour produire des trajets realistes :

| Type de ligne | Multiplicateur | Penalite par hop |
|---|---|---|
| TGV | x1.0 | +5 min |
| IC | x1.05 | +8 min |
| TER / TRAIN | x1.15 | +8 min |
| CORRESP | x1.0 | +15 min |

Cela evite les zigzags (ex : Nice -> Antibes -> Juan-les-Pins -> Cannes au lieu d'un TGV direct).
Les correspondances intra-ville permettent les changements de gare (ex : Paris Gare de Lyon -> Paris Saint-Lazare en 30 min).

Voir [docs/PATHFINDING_IMPROVEMENTS.md](docs/PATHFINDING_IMPROVEMENTS.md) pour le detail complet.

---

## Dataset

10 000 phrases generees avec 15 categories :

| Categorie | Description |
|---|---|
| `standard` | Phrases bien formees avec mots-cles |
| `misspelling` | Fautes d'orthographe (le plus difficile -- 10.9% baseline) |
| `no_capitals` | Sans majuscules |
| `inverted_order` | Destination avant origine |
| `compound_name` | Villes composees (Aix-en-Provence, Port-Boulet) |
| `complex_question` | Structures grammaticales complexes |
| `name_ambiguity` | Noms ambigus (Paris comme prenom, etc.) |
| `garbage` / `no_intent` | Phrases sans ordre de voyage (invalides) |

Split : **7 000 train / 1 500 val / 1 500 test** (seed=42)

---

## Entrainement CamemBERT

```bash
# 1. Convertir le dataset en format NER (BIO)
python scripts/camembert/convert_dataset_to_ner.py

# 2. Tokeniser pour le Trainer HuggingFace
python main.py --prepare-data

# 3. Entrainer (20 epochs, lr=2e-5, batch=16)
python scripts/camembert/train_camembert.py

# 4. Evaluer
python scripts/camembert/evaluate_camembert.py
```

Parametres : `camembert-base`, 20 epochs, lr=2e-5, batch_size=16/32, max_length=128.

---

## Tests

216 tests unitaires couvrant preprocessing, postprocessing, gazetteer, baseline, pipeline, et pathfinding.

```bash
# Tous les tests
python -m pytest tests/ -v

# Un module specifique
python -m pytest tests/test_postprocessing.py -v

# Avec couverture
python -m pytest tests/ --cov=src --cov-report=html
```

---

## Structure du projet

```
T-AIA-911-TRAVEL-ORDER-RESOLVER/
|-- app.py                          # Interface Streamlit (streamlit run app.py)
|-- main.py                         # CLI principal
|-- requirements.txt
|
|-- src/
|   |-- nlp/                        # Extraction NLP
|   |   |-- preprocessing.py        # Normalisation du texte
|   |   |-- gazetteer.py            # 2 782 gares + fuzzy matching
|   |   |-- baseline.py             # Modele a regles (60%)
|   |   |-- transformer.py          # CamemBERT NER (96.76%)
|   |   |-- postprocessing.py       # Reconstruction, validation, suggestions
|   |   +-- data_preparation.py     # Tokenisation pour HuggingFace
|   |-- pathfinding/
|   |   |-- graph_loader.py         # Graphe NetworkX, correspondances, routing_cost
|   |   +-- algorithms.py           # Dijkstra avec cout de routage
|   |-- utils/
|   |   |-- pipeline.py             # Orchestration bout-en-bout
|   |   +-- io_handler.py           # Lecture/ecriture CSV
|   +-- evaluation/
|       +-- metrics.py              # Precision / Recall / F1
|
|-- data/
|   |-- raw/sncf/gtfs/              # Donnees GTFS SNCF officielles
|   +-- processed/
|       |-- train.csv / val.csv / test.csv
|       |-- *_ner.json              # Labels BIO word-level
|       +-- sncf/                   # Gares, connexions, mapping UIC
|
|-- models/                         # Modeles (non inclus dans Git)
|   |-- camembert-ner/              # CamemBERT fine-tune (~440 MB)
|   +-- train_network.pkl           # Cache du graphe NetworkX
|
|-- tests/                          # 216 tests unitaires
|-- scripts/                        # Scripts dataset, entrainement, evaluation
|-- results/                        # Resultats d'evaluation JSON/CSV
+-- docs/                           # Documentation technique
```

---

## Documentation technique

| Document | Contenu |
|---|---|
| [docs/PATHFINDING_IMPROVEMENTS.md](docs/PATHFINDING_IMPROVEMENTS.md) | Ameliorations du pathfinding (correspondances, routing_cost, alias UIC) |
| [docs/GUIDE_COMPLET_RESEAU_SNCF.md](docs/GUIDE_COMPLET_RESEAU_SNCF.md) | Construction du reseau ferroviaire depuis GTFS |
| [docs/CAMEMBERT_IMPLEMENTATION.md](docs/CAMEMBERT_IMPLEMENTATION.md) | Implementation et entrainement de CamemBERT |
| [docs/PIPELINE_INTEGRATION.md](docs/PIPELINE_INTEGRATION.md) | Integration du pipeline NLP + pathfinding |
| [models/README.md](models/README.md) | Telechargement des modeles depuis Google Drive |

---

## Liens

- Modele CamemBERT : voir [models/README.md](models/README.md)
- Sujet du projet : [docs/project.pdf](docs/project.pdf)

---

**Projet EPITECH T-AIA-911 -- Travel Order Resolver**
