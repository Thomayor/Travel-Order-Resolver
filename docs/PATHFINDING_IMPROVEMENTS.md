# Améliorations du Pathfinding SNCF

**Date** : Février 2026
**Statut** : Terminé

---

## Contexte

Le moteur de pathfinding initial (Dijkstra sur graphe NetworkX) produisait des itinéraires incohérents pour les trajets complexes :

- **Nice → Rouen** : 7h36, 12 gares, zigzag sur la Côte d'Azur (Nice → Antibes → Juan-les-Pins → Cannes → St-Raphaël...) puis passage par Pont de Rungis et Versailles au lieu de traverser Paris proprement.
- **Paris → Marseille** : 6h12 via 40+ arrêts TER au lieu d'un TGV direct en 3h.
- **Marseille → Lille** : 7h02, 14 arrêts, pas de traversée de Paris.

**Causes racines identifiées** :

1. Les arêtes TGV n'étaient pas chargées (mauvais fichier CSV par défaut)
2. Aucune correspondance inter-gares dans une même ville (ex : Paris Gare de Lyon ↔ Paris Saint-Lazare)
3. Dijkstra minimisait la durée pure : 3 hops TER de 5 min = 15 min battait un TGV direct de 34 min
4. Paris Nord et Paris Austerlitz avaient 0 connexion (codes UIC alternatifs non résolus)
5. Le filtre `trip_count >= 10` supprimait les gares rurales

---

## Amélioration 1 : Chargement correct des connexions TGV

### Problème

`get_or_build_graph()` et `build_railway_graph()` pointaient vers `connections_final.csv` (ancien fichier sans TGV) au lieu de `connections_final_fixed.csv`.

### Solution

- Changement du fichier par défaut dans `graph_loader.py` vers `connections_final_fixed.csv`
- Suppression du cache stale `models/train_network.pkl`

### Fichier modifié

- `src/pathfinding/graph_loader.py` : paramètre `connections_file` par défaut

### Impact

Paris → Marseille : 372 min (40+ arrêts TER) → **184 min TGV direct**

---

## Amélioration 2 : Classification TGV depuis GTFS

### Problème

Le script de génération de connexions ne classifiait les lignes TGV qu'en lisant `route_short_name`. Or dans les données GTFS SNCF, de nombreux TGV n'ont pas de `route_short_name` mais sont identifiables via `route_long_name` (ex : "TGV INOUI PARIS MARSEILLE").

### Solution

La fonction `classify()` dans `generate_all_sncf_connections.py` combine désormais les deux colonnes :

```python
def classify(row) -> str:
    short = str(row.get("route_short_name", "")).upper()
    long_name = str(row.get("route_long_name", "")).upper()
    combined = short + " " + long_name
    if any(k in combined for k in ("TGV", "INOUI", "OUIGO", "EUROSTAR", "THALYS")):
        return "TGV"
    if any(k in combined for k in ("INTERCIT", "IC ")):
        return "IC"
    if any(k in combined for k in ("TER",)):
        return "TER"
    return "TRAIN"
```

### Fichier modifié

- `scripts/generate_all_sncf_connections.py`

### Impact

492 connexions TGV identifiées (contre ~50 auparavant).

---

## Amélioration 3 : Correspondances intra-ville (CORRESP)

### Problème

Paris possède 7 gares principales, mais aucune arête ne les reliait entre elles. Un trajet Nice → Rouen (qui passe par Paris Gare de Lyon puis Paris Saint-Lazare en réalité) était impossible car le graphe ne savait pas qu'on peut changer de gare dans une même ville.

Même situation à Lyon (Part-Dieu ↔ Perrache), Lille (Flandres ↔ Europe) et Marseille (Saint-Charles ↔ Blancarde).

### Solution

Ajout d'un dictionnaire `CITY_TRANSFERS` et d'une fonction `add_transfer_edges()` dans `graph_loader.py` :

```python
CITY_TRANSFERS = {
    "paris": {
        "stations": [
            "87686006",   # Gare de Lyon
            "87391003",   # Montparnasse
            "87113001",   # Est
            "87384008",   # Bercy
            "87271023",   # Nord
            "87547026",   # Austerlitz
            "87686667",   # Saint-Lazare
        ],
        "duration": 30,  # minutes (metro/taxi)
    },
    "lyon": {
        "stations": ["87723197", "87722025"],  # Part-Dieu ↔ Perrache
        "duration": 15,
    },
    "lille": {
        "stations": ["87286005", "87223263"],  # Flandres ↔ Europe
        "duration": 5,
    },
    "marseille": {
        "stations": ["87751008", "87751602"],  # Saint-Charles ↔ Blancarde
        "duration": 10,
    },
}
```

Pour chaque ville, une arête bidirectionnelle `CORRESP` est créée entre chaque paire de gares. Cela génère **22 arêtes de transfert** (21 pour les 7 gares de Paris + 1 pour Lyon + 1 pour Lille + 1 pour Marseille, mais les gares manquantes dans le graphe sont ignorées).

### Fichier modifié

- `src/pathfinding/graph_loader.py` : `CITY_TRANSFERS`, `add_transfer_edges()`

### Impact

Nice → Rouen passe désormais par Paris GDL → (CORRESP 30min) → Paris St-Lazare → Rouen.

---

## Amélioration 4 : Coût de routage (routing_cost)

### Problème

Même avec les correspondances, Dijkstra préférait les chemins avec beaucoup de petits hops TER (3+7+4 = 14 min) plutôt qu'un TGV direct (34 min) car il minimise la durée pure.

### Solution

Ajout d'un attribut `routing_cost` sur chaque arête, distinct du `weight` (durée réelle). Dijkstra utilise `routing_cost` pour le pathfinding, mais le temps total affiché est toujours calculé avec `weight`.

**Formule** : `routing_cost = duration_minutes × type_multiplier + hop_penalty`

| Type | `type_multiplier` | `hop_penalty` |
|------|-------------------|---------------|
| TGV | 1.0 | 5 min |
| IC | 1.05 | 8 min |
| TER | 1.15 | 8 min |
| TRAIN | 1.15 | 8 min |
| CORRESP | 1.0 | 15 min |

**Exemple** :
- Nice → Cannes direct TGV (34 min) : cost = 34 × 1.0 + 5 = **39**
- Nice → Antibes → Cannes TER (16+10 = 26 min) : cost = (16 × 1.15 + 8) + (10 × 1.15 + 8) = **45.9** → TGV gagne

Les multiplicateurs ont été calibrés pour ne pas être trop agressifs (1.15 au lieu de 1.3 initialement) afin de ne pas forcer des détours irréalistes.

### Fichiers modifiés

- `src/pathfinding/graph_loader.py` : `_ROUTING_PARAMS`, `_compute_routing_cost()`
- `src/pathfinding/algorithms.py` : `dijkstra(weight='routing_cost')`, retourne le temps réel via `weight`

### Impact

Les longs trajets empruntent désormais les lignes TGV/IC au lieu de zigzaguer sur les TER.

---

## Amélioration 5 : Résolution des alias UIC

### Problème

Paris Gare du Nord avait **0 connexion** dans le graphe, alors que c'est une gare majeure (Eurostar, Thalys, trains vers Lille). Cause : le fichier `stations_clean.csv` liste le code UIC principal `87271023` mais le GTFS utilise un code alternatif `87271007`. Le format est `87271023;87271007;87271031` (séparés par des points-virgules).

### Solution

Construction d'une table d'alias UIC dans `load_stations()` :

```python
uic_alias_map = {}
for _, station in df.iterrows():
    all_uics = [u.strip() for u in str(station['uic_code']).split(';')]
    uic_code = all_uics[0]  # Code principal
    for alt_uic in all_uics[1:]:
        uic_alias_map[alt_uic] = uic_code  # Alias → principal
graph.graph['uic_alias_map'] = uic_alias_map
```

Dans `load_connections()`, chaque code UIC source/destination est résolu via l'alias map avant de créer l'arête.

### Fichier modifié

- `src/pathfinding/graph_loader.py` : `load_stations()`, `load_connections()`

### Impact

- Paris Nord : 0 → **20 connexions**
- ~84 autres connexions récupérées via les alias
- Marseille → Lille : 7h02 / 14 arrêts → **3h56 / 3 arrêts** (via Paris)

---

## Amélioration 6 : Filtre dynamique des connexions

### Problème

Un filtre `trip_count >= 10` dans le script de génération supprimait les petites gares rurales. Les trajets comme Limoges → Brive ne fonctionnaient plus.

### Solution

Remplacement par `trip_count >= 2`. Le `routing_cost` (amélioration 4) empêche déjà les zigzags sur les longs trajets, donc le filtre agressif n'est plus nécessaire.

### Fichier modifié

- `scripts/generate_all_sncf_connections.py`

### Impact

Connexions : 7 450 → **10 320** (gares rurales accessibles). Les longs trajets restent propres grâce au `routing_cost`.

---

## Amélioration 7 : Résolution de gares principales

### Problème

"Lyon" se résolvait vers "Lyon Gorge de Loup" au lieu de "Lyon Part-Dieu" (gare principale). Cause : une logique de préfixe pour les noms courts (≤ 4 caractères) prenait le premier match alphabétique au lieu de respecter le mapping exact.

### Solution

Suppression de la logique de préfixe pour les noms courts quand un match exact existe. Le CSV `city_station_mapping.csv` mappe déjà `lyon → Lyon Part-Dieu`. Un match exact n'est plus remplacé par un match préfixé.

### Fichier modifié

- `src/utils/pipeline.py` : `map_city_to_uic()`

### Impact

"Lyon" → Lyon Part-Dieu (au lieu de Lyon Gorge de Loup).

---

## Amélioration 8 : Matching intelligent des noms de villes

### Problème

- "saint-lau" (tapé par l'utilisateur) se résolvait en "Saint-Ay" via fuzzy matching (distance de Levenshtein faible) au lieu de proposer les villes commençant par "Saint-Laurent-*"
- "Pari" (faute de frappe) devait se résoudre à "Paris", pas être traité comme préfixe ambigu

### Solution

Dans `validate_against_gazetteer()` (postprocessing.py) :

1. Le matching par préfixe est exécuté **avant** le fuzzy matching
2. Si le match préfixe le plus proche diffère de **1-2 caractères** seulement → c'est une faute de frappe → résolution directe ("pari" → "paris")
3. Si les matches préfixes sont **significativement plus longs** → c'est un préfixe ambigu → retourne `None` → déclenche le système de suggestions ("saint-lau" → 7 résultats Saint-Laurent-*)

### Fichier modifié

- `src/nlp/postprocessing.py` : `validate_against_gazetteer()`

### Impact

- "Pari" → "Paris" (correction de faute)
- "saint-lau" → suggestions : Saint-Laurent-du-Var, Saint-Laurent-de-Mure, etc.

---

## Résumé du graphe final

| Métrique | Valeur |
|----------|--------|
| Gares | 2 782 |
| Connexions totales | 10 320 (CSV) / 3 779 (graphe dédupliqué) |
| Connexions TGV | 492 (CSV) / 224 (graphe) |
| Connexions IC | 406 (CSV) / 125 (graphe) |
| Connexions TER | 190 (CSV) / 114 (graphe) |
| Connexions TRAIN | ~9 200 (CSV) / 3 294 (graphe) |
| Transferts intra-ville | 22 |
| Villes avec correspondances | 4 (Paris, Lyon, Lille, Marseille) |

---

## Exemples de trajets corrigés

| Trajet | Avant | Après |
|--------|-------|-------|
| Paris → Marseille | 6h12, 40+ arrêts TER | **3h04, TGV direct** |
| Nice → Rouen | 7h36, 12 arrêts, zigzag Côte d'Azur | **~4h, via Paris (GDL → CORRESP → St-Lazare)** |
| Marseille → Lille | 7h02, 14 arrêts | **3h56, 3 arrêts via Paris** |
| Limoges → Brive | Route introuvable | **1h03, direct** |
| Saint-Laurent-du-Var → Lyon | Arrivée "Lyon Gorge de Loup" | **Arrivée "Lyon Part-Dieu"** |

---

## Fichiers modifiés (récapitulatif)

| Fichier | Modifications |
|---------|--------------|
| `src/pathfinding/graph_loader.py` | Alias UIC, correspondances intra-ville, routing_cost, fichier CSV par défaut |
| `src/pathfinding/algorithms.py` | Dijkstra utilise `routing_cost`, retourne le temps réel |
| `src/nlp/postprocessing.py` | Préfixe avant fuzzy, seuil de différence 1-2 chars |
| `src/nlp/gazetteer.py` | Villes étrangères, chargement depuis stations_clean.csv |
| `src/utils/pipeline.py` | Suppression du préfixe override pour noms courts, détection villes étrangères |
| `scripts/generate_all_sncf_connections.py` | classify() amélioré, filtre trip_count >= 2, cap durée 4h |
| `app.py` | Affichage badges TGV/TER/IC/CORRESP, suggestions de villes, station_name |
