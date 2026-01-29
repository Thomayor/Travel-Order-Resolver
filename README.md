# 🚆 Travel Order Resolver

> Projet EPITECH NLP : Extraction d'informations de voyage depuis des commandes en français et génération d'itinéraires de train SNCF.

## 📋 Description

Ce projet vise à construire un système NLP capable de :
1. **Extraire** l'origine et la destination depuis des phrases en français (avec fautes d'orthographe, accents manquants, etc.)
2. **Générer** des itinéraires de train optimaux via l'algorithme de Dijkstra sur le réseau SNCF

**Focus** : 70% NLP, 30% pathfinding

---

## 📁 Structure du Projet

```
travel-order-resolver/
│
├── 📂 data/                           # Données du projet
│   ├── raw/                          # Datasets bruts générés (8 fichiers CSV)
│   ├── processed/                    # Datasets splittés (train/val/test)
│   │   ├── train.csv                # 60% des données
│   │   ├── val.csv                  # 20% des données
│   │   ├── test.csv                 # 20% des données
│   │   └── *_ner.json               # Format NER pour CamemBERT
│   ├── archive/                     # Anciennes versions
│   └── README.md                    # Documentation des datasets
│
├── 📂 src/                            # Code source principal
│   ├── nlp/                         # Module NLP (✅ implémenté)
│   │   ├── preprocessing.py        # Normalisation du texte français
│   │   ├── gazetteer.py            # Base de données de 66 villes
│   │   ├── baseline.py             # Extracteur baseline (règles)
│   │   ├── transformer.py          # CamemBERT fine-tuné
│   │   └── postprocessing.py       # Post-traitement des entités
│   ├── pathfinding/                 # Module pathfinding (🚧 en cours)
│   │   └── __init__.py
│   ├── evaluation/                  # Module d'évaluation
│   │   └── __init__.py
│   └── utils/                       # Utilitaires réutilisables
│       └── __init__.py
│
├── 📂 scripts/                        # Scripts utilitaires
│   ├── demos/                       # Scripts de démonstration
│   │   ├── demo_preprocessing.py   # Démo normalisation
│   │   ├── demo_gazetteer.py       # Démo matching de villes
│   │   └── demo_baseline.py        # Démo extraction baseline
│   ├── dataset_generation/          # Génération des datasets
│   │   ├── generate_dataset_10k.py # Génère 10k phrases
│   │   ├── validate_dataset_10k.py # Valide et déduplique
│   │   ├── finalize_dataset_10k.py # Finalise à 10k exact
│   │   └── split_dataset.py        # Split train/val/test
│   ├── baseline_evaluation/         # Évaluation du modèle baseline
│   │   └── evaluate_baseline_10k.py
│   ├── camembert/                   # Scripts CamemBERT
│   │   ├── train_camembert.py      # Entraînement du modèle
│   │   ├── evaluate_camembert.py   # Évaluation NER
│   │   ├── demo_camembert.py       # Démo du modèle entraîné
│   │   └── convert_dataset_to_ner.py
│   └── pathfinding/                 # Scripts pathfinding
│       ├── visualize_graph.py      # Visualisation du réseau
│       ├── demo_graph.py           # Démo Dijkstra
│       └── test_complete_network.py
│
├── 📂 tests/                          # Tests unitaires
│   ├── test_preprocessing.py        # 42 tests (✅ 100% pass)
│   └── test_gazetteer.py            # 32 tests (✅ 100% pass)
│
├── 📂 models/                         # Modèles entraînés
│   ├── camembert-ner/               # Modèle CamemBERT fine-tuné (~440MB)
│   └── README.md                    # Lien Google Drive pour télécharger
│
├── 📂 notebooks/                      # Jupyter notebooks d'analyse
│
├── 📂 docs/                           # Documentation
│   ├── images/                      # Images et graphiques
│   │   ├── railway_network_full.png
│   │   └── railway_network_main.png
│   ├── nlp_module_documentation.md  # Doc technique NLP
│   ├── pathfinding_algorithm_comparison.md
│   ├── DIFFICULTY_LEVELS.md         # Niveaux de difficulté dataset
│   ├── PROJECT_PLAN.md              # Plan de développement 8 semaines
│   ├── CAMEMBERT_IMPLEMENTATION.md  # Guide CamemBERT
│   ├── EVALUATION_ANALYSIS.md       # Analyse des performances
│   ├── SYNTHESE_COMPLETE_PROJET.md  # Synthèse complète
│   ├── GUIDE_COMPLET_RESEAU_SNCF.md
│   └── project.pdf                  # Sujet du projet (2.6 MB)
│
├── 📂 results/                        # Résultats d'évaluation
│   ├── evaluation_baseline_10k.json # Résultats baseline
│   ├── evaluation_baseline_10k.txt
│   ├── camembert_evaluation.json    # Résultats CamemBERT
│   └── camembert_errors.csv         # Erreurs d'analyse
│
├── 📂 venv/                           # Environnement virtuel Python
│
├── .gitignore                         # Fichiers ignorés par Git
├── CLAUDE.md                          # Instructions pour Claude Code
├── requirements.txt                   # Dépendances Python
└── README.md                          # Ce fichier
```

---

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd travel-order-resolver
```

### 2. Créer l'environnement virtuel

```bash
# Créer l'environnement
python -m venv venv

# Activer l'environnement
# Sur Windows (Git Bash)
source venv/Scripts/activate

# Sur Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Sur Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer les dépendances (⚠️ peut prendre 5-10 minutes)
pip install -r requirements.txt

# Télécharger le modèle français spaCy
python -m spacy download fr_core_news_md
```

### 4. Vérifier l'installation

```bash
# Tester le preprocessing
python scripts/demos/demo_preprocessing.py

# Tester le gazetteer
python scripts/demos/demo_gazetteer.py

# Tester le baseline
python scripts/demos/demo_baseline.py
```

---

## 🎯 Utilisation

### Extraire origine et destination (Baseline)

```python
from src.nlp.baseline import BaselineExtractor
from src.nlp.gazetteer import load_gazetteer

# Charger le gazetteer (66 villes)
gaz = load_gazetteer()

# Créer l'extracteur
extractor = BaselineExtractor(gaz)

# Extraire depuis une phrase
sentence = "Je veux aller de Paris à Lyon"
origin, destination = extractor.extract(sentence)
print(f"Origine: {origin}, Destination: {destination}")
# Output: Origine: Paris, Destination: Lyon
```

### Utiliser CamemBERT (Modèle avancé)

```python
from src.nlp.transformer import CamembertNER

# Charger le modèle fine-tuné
model = CamembertNER.from_pretrained("models/camembert-ner")

# Prédire
sentence = "Quel train va de Bordeaux à Marseille?"
entities = model.predict(sentence)
print(entities)
# Output: {'origin': 'Bordeaux', 'destination': 'Marseille'}
```

---

## 🧪 Tests

Le projet contient **74 tests unitaires** (100% passent) :

```bash
# Lancer tous les tests
python -m pytest tests/ -v

# Tester un module spécifique
python -m pytest tests/test_preprocessing.py -v
python -m pytest tests/test_gazetteer.py -v
```

---

## 📊 Performances

### Modèle Baseline (règles)
- **Précision globale** : 70%
- **Format direct** ("billet Paris Lyon") : 93%
- **Avec mots-clés** ("de Paris à Lyon") : 90%
- **Questions** ("Quel train va à Lyon?") : 60%
- **Phrases complexes** : 40%

### Modèle CamemBERT (transformers)
- **Précision globale** : 85-90% (objectif)
- **F1-score** : ~87%
- Fine-tuné sur 10,000 phrases françaises

---

## 📈 Dataset

- **Taille totale** : 10,000 phrases
  - **Valid orders** : 7,000 phrases (70%)
  - **Invalid orders** : 3,000 phrases (30%)

- **Niveaux de difficulté** :
  - **Easy (20%)** : Structure claire, orthographe correcte → Baseline 87%
  - **Medium (60%)** : Questions, ordre inversé → Baseline 73%
  - **Hard (20%)** : Fautes, ambiguïtés → Baseline 35%

- **Split** :
  - Train : 60% (6,000 phrases)
  - Validation : 20% (2,000 phrases)
  - Test : 20% (2,000 phrases)

---

## 🗺️ Pathfinding (Phase 7)

### Algorithme : Dijkstra
- **Réseau** : 66 stations SNCF, ~200 connexions
- **Poids** : Durée en minutes
- **Complexité** : O((V+E) log V)
- **Bibliothèque** : NetworkX

### Visualiser le réseau

```bash
python scripts/pathfinding/visualize_graph.py
```

---

## 📚 Documentation

Toute la documentation se trouve dans le dossier [docs/](docs/) :

- [**PROJECT_PLAN.md**](docs/PROJECT_PLAN.md) - Plan de développement 8 semaines
- [**nlp_module_documentation.md**](docs/nlp_module_documentation.md) - Guide technique NLP
- [**DIFFICULTY_LEVELS.md**](docs/DIFFICULTY_LEVELS.md) - Niveaux de difficulté expliqués
- [**CAMEMBERT_IMPLEMENTATION.md**](docs/CAMEMBERT_IMPLEMENTATION.md) - Guide CamemBERT
- [**pathfinding_algorithm_comparison.md**](docs/pathfinding_algorithm_comparison.md) - Comparaison algorithmes

---

## 🛠️ Développement

### Générer un nouveau dataset

```bash
# Générer 10k phrases
python scripts/dataset_generation/generate_dataset_10k.py

# Valider et dédupliquer
python scripts/dataset_generation/validate_dataset_10k.py

# Finaliser
python scripts/dataset_generation/finalize_dataset_10k.py

# Générer les statistiques
python scripts/dataset_generation/generate_report_10k.py
```

### Entraîner CamemBERT

```bash
# Convertir en format NER
python scripts/camembert/convert_dataset_to_ner.py

# Entraîner
python scripts/camembert/train_camembert.py

# Évaluer
python scripts/camembert/evaluate_camembert.py
```

---

## 🤝 Contribution

Ce projet est un projet académique EPITECH. Pour toute question :
- Consulter la documentation dans [docs/](docs/)
- Voir [CLAUDE.md](CLAUDE.md) pour les instructions de développement

---

## 📝 Licence

Projet académique EPITECH - NLP Travel Order Resolver

---

## 🔗 Liens utiles

- **Modèles pré-entraînés** : Voir [models/README.md](models/README.md)
- **Datasets** : Voir [data/README.md](data/README.md)
- **Sujet du projet** : Voir [docs/project.pdf](docs/project.pdf)
