# CLAUDE.md

Instructions pour Claude Code travaillant sur ce depot.

## Vue d'ensemble

Extraction d'ordres de voyage en francais (NLP) + calcul d'itineraires sur le reseau SNCF.

- Entree : `"Je veux aller de Paris a Lyon"`
- Sortie : `Paris -> Lyon` + itineraire complet avec gares intermediaires

## Commandes principales

```bash
# Installation
python -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt

# Tests (216 tests)
python -m pytest tests/ -v

# Interface web
streamlit run app.py

# CLI
python main.py -I --model camembert          # Mode interactif
python main.py -i input.csv -o out.csv       # Traitement CSV
python main.py --evaluate --split test --model camembert  # Evaluation
```

## Architecture du code

```
src/
  nlp/
    preprocessing.py      # Normalisation texte (accents, casse, caracteres speciaux)
    gazetteer.py          # 2 782 gares SNCF + fuzzy matching (Levenshtein)
    baseline.py           # Extracteur a regles (60% precision)
    transformer.py        # CamemBERT fine-tune NER (96.76% precision)
    postprocessing.py     # Reconstruction noms composes, validation gazetteer, suggestions
    data_preparation.py   # Conversion BIO word-level -> subwords HuggingFace
  pathfinding/
    graph_loader.py       # Graphe NetworkX depuis GTFS SNCF
    algorithms.py         # Dijkstra avec cout de routage
  utils/
    pipeline.py           # Orchestration bout-en-bout (NLP -> UIC -> Dijkstra)
    io_handler.py         # Lecture/ecriture CSV
  evaluation/
    metrics.py            # Precision / Recall / F1 / exact match
```

## Pipeline de traitement

```
Phrase -> preprocessing -> CamemBERT NER (BIO tagging) -> postprocessing
  -> validate_against_gazetteer (prefixe/fuzzy) -> map_city_to_uic
  -> dijkstra(routing_cost) -> itineraire avec durees reelles
```

## Pathfinding : concepts cles

- **routing_cost** : Dijkstra utilise `routing_cost` (duree x multiplicateur + penalite hop) pour le routage, mais retourne le temps reel via `weight`. Cela favorise les TGV sur les longs trajets.
- **Correspondances intra-ville** : Paris (7 gares, 30min), Lyon (2, 15min), Lille (2, 5min), Marseille (2, 10min). Type `CORRESP`.
- **Alias UIC** : `stations_clean.csv` a des codes UIC separes par `;`. Le premier est le principal, les suivants sont des alias resolus dans `load_connections()`.
- **Cache** : `models/train_network.pkl`. Supprimer ce fichier apres toute modification de `graph_loader.py` ou des CSV de connexions.

## Fichiers de donnees importants

- `data/processed/sncf/stations_clean.csv` : 2 782 gares (UIC, nom, coordonnees GPS)
- `data/processed/sncf/connections_final_fixed.csv` : 10 320 connexions (origin, dest, duree, type)
- `data/processed/sncf/city_station_mapping.csv` : mapping ville normalisee -> UIC
- `data/raw/sncf/gtfs/` : donnees GTFS SNCF brutes (stop_times.txt, routes.txt, etc.)

## Resolution des noms de villes

`validate_against_gazetteer()` dans `postprocessing.py` :
1. Match exact normalise
2. Match prefixe (si diff <= 2 chars : faute de frappe, sinon : ambigu -> suggestions)
3. Fuzzy match (Levenshtein distance <= 2)

`map_city_to_uic()` dans `pipeline.py` :
1. Match exact dans city_station_mapping.csv
2. Match prefixe si pas de match exact (ex: "aix" -> "aix-en-provence")

## Conventions

- Tous les fichiers CSV sont en UTF-8
- Les codes UIC sont des strings (ex: "87686006")
- Le graphe NetworkX est non-dirige (bidirectionnel)
- Les labels NER suivent le schema BIO : B-ORIGIN, I-ORIGIN, B-DEST, I-DEST, O
- `find_route()` dans `app.py` retourne 5 valeurs : `(cities, total_time, segments, err, err_type)`

## Points d'attention

- Toujours supprimer `models/train_network.pkl` apres modification du graphe
- Streamlit utilise `@st.cache_resource` : redemarrer l'app apres modifications du graphe
- Le fichier de connexions par defaut est `connections_final_fixed.csv` (pas `connections_final.csv`)
- Les multiplicateurs routing_cost sont calibres : TGV=1.0, IC=1.05, TER/TRAIN=1.15
