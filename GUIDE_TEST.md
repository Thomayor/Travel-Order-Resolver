# Guide de Test - Travel Order Resolver

Ce guide permet de tester facilement toutes les fonctionnalités du projet.

## Prérequis

**Installation des dépendances:**
```bash
pip install pandas numpy networkx pytest
```

## Tests Rapides (5 minutes)

### 1. Module NLP - Preprocessing

```bash
python scripts/demos/demo_preprocessing.py
```

**Résultat attendu:** Affiche la normalisation de texte français (accents, casse, etc.)

---

### 2. Module NLP - Gazetteer

```bash
python scripts/demos/demo_gazetteer.py
```

**Résultat attendu:**
- 66 locations chargées (50 villes + 18 gares)
- Extraction de "Paris" et "Lyon" depuis "Je veux aller de Paris à Lyon"

---

### 3. Module NLP - Baseline Extractor

```bash
python scripts/demos/demo_baseline.py
```

**Résultat attendu:**
- Extraction correcte de l'origine et destination
- Exemple: "Je veux aller de Paris à Lyon" → Origin: Paris, Destination: Lyon

---

### 4. Module Pathfinding - Graph & Dijkstra

```bash
python scripts/test_kan35_kan36.py
```

**Résultat attendu:**
- Graph chargé: 2782 stations, 13098 connexions
- Paris → Lyon: ~290 minutes
- Toulouse → Marseille: ~95 minutes (trajet direct)

---

### 5. Visualisation de Route

```bash
python scripts/demo_visualize_route.py
```

**Instructions:**
1. Choisir un trajet (1, 2 ou 3)
2. Afficher le réseau complet ? (o/N)

**Résultat attendu:**
- Génération d'une image PNG avec la route visualisée
- Fichier sauvegardé: `route_[ORIGIN]_[DEST].png`

---

## Tests Complets (15 minutes)

### 1. Tests Unitaires (103 tests)

```bash
# Tous les tests
pytest tests/ -v

# Tests par module
pytest tests/test_preprocessing.py -v  # 42 tests
pytest tests/test_gazetteer.py -v      # 32 tests
pytest tests/test_baseline.py -v       # 29 tests
```

**Résultat attendu:** 103/103 tests passés ✓

---

### 2. Évaluation du Baseline (Dataset 10K)

```bash
python scripts/baseline_evaluation/evaluate_baseline_10k.py
```

**Résultats attendus:**
- **Accuracy globale:** ~55-60%
- **F1 Score:** ~85%
- **Précision:** ~90%
- **Rappel:** ~81%

**Performance par difficulté:**
- Easy: ~80%
- Medium: ~63%
- Hard: ~37%

---

### 3. Génération Complète des Connexions

**Note:** Cette étape prend ~2-3 minutes

```bash
python scripts/generate_all_sncf_connections.py
```

**Résultat attendu:**
- 26,196 connexions générées
- Graph reconstruit: 2782 stations, 13098 edges
- Fichier créé: `data/processed/sncf/connections_final.csv`
- Cache graph: `models/train_network.pkl` (~1 MB)

---

## Structure du Projet

```
T-AIA-911-TRAVEL-ORDER-RESOLVER/
├── src/
│   ├── nlp/                          # Modules NLP
│   │   ├── preprocessing.py          # Normalisation texte
│   │   ├── gazetteer.py              # Base de données villes
│   │   ├── baseline.py               # Extracteur règles
│   │   └── transformer.py            # CamemBERT (optionnel)
│   └── pathfinding/                  # Modules Pathfinding
│       ├── graph_loader.py           # Chargement graph NetworkX
│       └── algorithms.py             # Dijkstra
│
├── data/
│   ├── train.csv, val.csv, test.csv  # Datasets (10K total)
│   └── processed/sncf/
│       ├── stations_clean.csv        # 2782 stations
│       └── connections_final.csv     # 26K connexions
│
├── scripts/
│   ├── demos/                        # Scripts de démonstration
│   ├── baseline_evaluation/          # Évaluation baseline
│   ├── camembert/                    # Training CamemBERT (optionnel)
│   ├── generate_all_sncf_connections.py  # Génération connexions
│   ├── test_kan35_kan36.py           # Tests pathfinding
│   └── demo_visualize_route.py       # Visualisation routes
│
└── tests/                            # Tests unitaires (103 tests)
```

---

## Points Clés à Vérifier

### ✅ Module NLP
- [x] Preprocessing normalise correctement le texte français
- [x] Gazetteer charge 66 locations (50 villes + 18 gares)
- [x] Baseline extrait origin/destination avec ~60% accuracy

### ✅ Module Pathfinding
- [x] Graph NetworkX: 2782 stations, 13098 connexions
- [x] Dijkstra trouve le chemin le plus court
- [x] Cache pickle pour chargement rapide (~0.01s vs 0.16s)

### ✅ Données
- [x] Dataset 10K: train (7K) + val (1.5K) + test (1.5K)
- [x] Connexions SNCF complètes (26K connexions bidirectionnelles)
- [x] Pas de détour absurde (ex: Toulouse → Marseille direct, pas via Paris)

---

## Résolution de Problèmes

### Erreur: "ModuleNotFoundError"

```bash
# Vérifier que vous êtes à la racine du projet
pwd  # Devrait afficher: .../T-AIA-911-TRAVEL-ORDER-RESOLVER

# Installer les dépendances manquantes
pip install pandas numpy networkx pytest
```

### Erreur: "FileNotFoundError: connections_final.csv"

```bash
# Régénérer les connexions
python scripts/generate_all_sncf_connections.py
```

### Erreur: "Graph file not found"

```bash
# Le cache sera reconstruit automatiquement
# Ou forcer la reconstruction:
python -c "from src.pathfinding.graph_loader import get_or_build_graph; get_or_build_graph(force_rebuild=True)"
```

---

## Contacts & Support

- **Documentation complète:** Voir `CLAUDE.md`
- **Architecture NLP:** Voir `docs/nlp_module_documentation.md`
- **Pathfinding:** Voir `docs/pathfinding_algorithm_comparison.md`

---

## Résumé - Tests à Exécuter

**Minimum (5 min):**
1. `python scripts/demos/demo_baseline.py` - Test extraction NLP
2. `python scripts/test_kan35_kan36.py` - Test pathfinding

**Recommandé (15 min):**
1. Minimum +
2. `pytest tests/ -v` - Tests unitaires complets
3. `python scripts/baseline_evaluation/evaluate_baseline_10k.py` - Évaluation

**Complet (30 min):**
1. Recommandé +
2. `python scripts/generate_all_sncf_connections.py` - Régénération connexions
3. `python scripts/demo_visualize_route.py` - Visualisation

---

**✅ Le projet est prêt pour la présentation !**
