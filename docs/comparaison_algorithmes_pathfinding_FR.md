# Comparaison des Algorithmes de Pathfinding et Guide d'Implémentation

**Projet**: Travel Order Resolver - Projet NLP EPITECH
**Module**: Pathfinding pour le Réseau Ferroviaire SNCF
**Date**: Janvier 2026
**Statut**: Phase de Sélection d'Algorithme

---

## Table des Matières

1. [Résumé Exécutif](#résumé-exécutif)
2. [Modélisation du Problème](#modélisation-du-problème)
3. [Théorie de la Complexité Algorithmique](#théorie-de-la-complexité-algorithmique)
4. [Comparaison des Algorithmes](#comparaison-des-algorithmes)
5. [Algorithme de Dijkstra - Solution Retenue](#algorithme-de-dijkstra---solution-retenue)
6. [Évaluation des Bases de Données Graphe](#évaluation-des-bases-de-données-graphe)
7. [Feuille de Route d'Implémentation](#feuille-de-route-dimplémentation)
8. [Annexes](#annexes)

---

## 1. Résumé Exécutif

### Contexte
Le Travel Order Resolver extrait les gares de départ et d'arrivée à partir de commandes en langage naturel français (module NLP), puis calcule les itinéraires optimaux de train via le réseau ferroviaire SNCF (module pathfinding).

### Recommandation
**Algorithme**: **Dijkstra**
**Bibliothèque Graphe**: **NetworkX (Python)**

### Justification
- ✅ **Optimal pour poids non-négatifs** (les durées de train sont toujours positives)
- ✅ **Complexité efficace**: O((V+E) log V) avec file de priorité
- ✅ **Simple à implémenter** et à expliquer dans un contexte académique
- ✅ **Garantit le plus court chemin** pour les graphes pondérés
- ✅ **Adapté à l'échelle du réseau SNCF** (~3000 gares, ~10 000 connexions)

### Alternatives Considérées
- **A***: Nécessite des coordonnées GPS pour l'heuristique (amélioration future)
- **Bellman-Ford**: Trop lent (O(V·E)), gère les poids négatifs inutilement
- **Neo4j**: Sur-dimensionné pour l'échelle du projet ; NetworkX suffit

---

## 2. Modélisation du Problème

### 2.1 Réseau Ferroviaire comme Graphe

Le réseau ferroviaire SNCF se modélise naturellement comme un **graphe pondéré dirigé**:

```
Graphe G = (V, E)
├── V (Sommets) = Gares/villes ferroviaires
│   ├── Exemples: "Paris", "Lyon", "Bordeaux"
│   ├── Taille: ~3000 gares dans le réseau SNCF complet
│   └── Projet: ~66 grandes villes (Phase 7)
│
└── E (Arêtes) = Connexions directes de train
    ├── Poids = Durée du trajet (minutes) OU distance (km)
    ├── Toujours positif (pas de durées négatives!)
    └── Taille: ~10 000 connexions dans le réseau complet
```

### 2.2 Format Entrée/Sortie

**Entrée** (depuis le module NLP):
```csv
sentenceID,Departure,Destination
1,Bordeaux,Paris
2,Lyon,Marseille
```

**Sortie** (depuis le module Pathfinding):
```csv
sentenceID,Origin,Stop1,Stop2,...,Destination
1,Bordeaux,Tours,Paris
2,Lyon,Avignon,Marseille
```

**Cas Particuliers**:
- Aucun chemin n'existe → `sentenceID,Departure,INVALID,INVALID`
- Connexion directe → `sentenceID,Departure,Destination` (pas d'arrêts intermédiaires)

### 2.3 Contraintes du Monde Réel

| Contrainte | Valeur | Impact sur l'Algorithme |
|-----------|-------|-------------------------|
| Nombre de gares (V) | 66 (projet) / 3000 (complet) | Dijkstra scale bien |
| Nombre de connexions (E) | ~200 (projet) / 10 000 (complet) | O(E log V) acceptable |
| Type de poids | Entiers positifs (minutes) | Dijkstra optimal |
| Densité du graphe | Sparse (E ≈ 3V) | File de priorité efficace |
| Fréquence des requêtes | Traitement par lot (CSV) | Pas d'exigence temps réel |

---

## 3. Théorie de la Complexité Algorithmique

### 3.1 Notation Big-O Expliquée

**Définition**: O(f(n)) décrit comment le temps d'exécution croît lorsque la taille d'entrée n augmente.

```
Pour les algorithmes de graphe:
├── V = nombre de sommets (gares)
└── E = nombre d'arêtes (connexions)

Exemple:
├── V = 1000 gares
├── E = 5000 connexions
└── Si V double → V = 2000, E ≈ 10 000
```

### 3.2 Complexités Courantes

| Notation | Taux de Croissance | Exemple | Si V double... |
|----------|-------------------|---------|----------------|
| O(V) | Linéaire | Visiter chaque gare une fois | Temps ×2 |
| O(E) | Linéaire | Vérifier chaque connexion une fois | Temps ×2 |
| O(V²) | Quadratique | Comparer toutes les paires de gares | Temps ×4 |
| O(V·E) | Polynomiale | Bellman-Ford | Temps ×8+ |
| O((V+E) log V) | Quasi-linéaire | Dijkstra/A* | Temps ×2,3 |

### 3.3 Comparaison Pratique de Complexité

**Scénario**: Réseau SNCF avec V=1000 gares, E=5000 connexions

| Algorithme | Complexité | Opérations | Vitesse Relative |
|-----------|-----------|------------|------------------|
| Dijkstra | O((V+E) log V) | 6000 × 10 = 60 000 | **1x (référence)** |
| A* | O((V+E) log V) | ~40 000 (avec bonne heuristique) | **1,5x plus rapide** |
| Bellman-Ford | O(V·E) | 1000 × 5000 = 5 000 000 | **83x plus lent** |

**Pourquoi O((V+E) log V)?**
```
Dijkstra utilise un min-heap (file de priorité):
├── (V+E) = Total des gares + connexions à examiner
└── log V = Coût par opération d'insertion/extraction du tas

Détail:
├── Chaque sommet extrait une fois du tas: V × log V
└── Chaque arête relaxe un voisin: E × log V
└── Total: (V+E) × log V
```

---

## 4. Comparaison des Algorithmes

### 4.1 Tableau Récapitulatif

| Algorithme | Idée Principale | Poids Négatifs | Optimalité (poids positifs) | Complexité Temporelle |
|-----------|-----------------|----------------|----------------------------|----------------------|
| **Dijkstra** | Glouton: traite toujours le nœud le plus proche non visité | ❌ Non | ✅ Oui | **O((V+E) log V)** |
| **A*** | Dijkstra + heuristique de distance vers le but | ❌ Non | ✅ Oui (si heuristique admissible) | **O((V+E) log V)** |
| **Bellman-Ford** | Relaxe toutes les arêtes V-1 fois | ✅ Oui | ✅ Oui | **O(V·E)** |

### 4.2 Algorithme de Dijkstra

**Principe**: Étendre gloutonement le nœud non visité le plus proche, en maintenant la plus courte distance connue vers tous les nœuds.

**Comment ça marche**:
1. Commencer à la source S avec distance 0
2. Toujours traiter le nœud U avec la plus petite distance connue
3. Mettre à jour les distances vers tous les voisins V de U
4. Répéter jusqu'à atteindre la cible T

**Forces**:
- ✅ Optimal pour poids non-négatifs (prouvé mathématiquement)
- ✅ Efficace avec file de priorité: O((V+E) log V)
- ✅ Simple à implémenter et comprendre
- ✅ Bien testé en production (navigation GPS, routage réseau)

**Faiblesses**:
- ❌ Échoue avec poids négatifs (peut rester bloqué dans un mauvais optimum local)
- ❌ Pas de guidage heuristique vers le but (explore toutes les directions également)

**Meilleur pour**: Réseaux de trains (durées toujours positives), réseaux routiers, paquets réseau

### 4.3 Algorithme A*

**Principe**: Dijkstra + fonction heuristique h(n) estimant la distance restante vers le but.

**Fonction de priorité**: `f(n) = g(n) + h(n)`
- g(n) = distance réelle depuis le départ vers n
- h(n) = distance estimée de n vers le but

**Exemple d'heuristique pour les trains**:
```python
def heuristic(station_courante, station_but):
    """Estimer le temps de trajet restant via distance à vol d'oiseau"""
    distance_km = haversine_distance(
        lat_lon[station_courante],
        lat_lon[station_but]
    )
    vitesse_moy_kmh = 120  # Vitesse moyenne TGV
    return distance_km / vitesse_moy_kmh * 60  # Convertir en minutes
```

**Forces**:
- ✅ Plus rapide que Dijkstra (explore moins de nœuds)
- ✅ Toujours optimal si l'heuristique est **admissible** (ne surestime jamais)
- ✅ Idéal quand la position du but est connue (coordonnées GPS)

**Faiblesses**:
- ❌ Nécessite une bonne heuristique (besoin de données GPS pour les gares)
- ❌ Plus complexe à implémenter correctement
- ❌ Admissibilité difficile à garantir (mauvaise heuristique → mauvais résultats)

**Meilleur pour**: Navigation GPS, pathfinding dans les jeux (cartes), robotique

### 4.4 Algorithme de Bellman-Ford

**Principe**: Relaxer toutes les arêtes E de manière répétée V-1 fois pour trouver les plus courts chemins.

**Comment ça marche**:
```python
# Répéter V-1 fois:
for u, v, poids in toutes_les_aretes:
    if distance[u] + poids < distance[v]:
        distance[v] = distance[u] + poids
        predecesseur[v] = u
```

**Forces**:
- ✅ Gère les poids négatifs (prêts, réductions dans les graphes de coût)
- ✅ Détecte les cycles négatifs (boucles de réduction de coût infinies)
- ✅ Plus simple conceptuellement (pas de file de priorité)

**Faiblesses**:
- ❌ **Très lent**: O(V·E) = 83x plus lent que Dijkstra pour le réseau SNCF
- ❌ Surdimensionné pour poids positifs (Dijkstra toujours meilleur)

**Meilleur pour**: Réseaux financiers (dettes), problèmes de graphe théoriques

### 4.5 Pourquoi Dijkstra pour ce Projet?

| Critère | Dijkstra | A* | Bellman-Ford |
|---------|----------|-----|--------------|
| **Poids positifs uniquement** | ✅ Parfait | ✅ Oui | ❌ Surdimensionné |
| **Performance** | ⭐⭐⭐⭐⭐ Rapide | ⭐⭐⭐⭐⭐ Plus rapide | ⭐⭐ Lent |
| **Simplicité** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐ Moyen | ⭐⭐⭐⭐ Simple |
| **Besoins en données** | Noms de gares uniquement | Coordonnées GPS nécessaires | Noms de gares uniquement |
| **Valeur pédagogique** | ⭐⭐⭐⭐⭐ Algorithme classique | ⭐⭐⭐⭐ Sujet avancé | ⭐⭐⭐ Usage spécialisé |
| **Temps d'implémentation** | ~2-3 heures | ~4-6 heures | ~1-2 heures |

**Décision**: **Dijkstra** est le choix évident pour ce projet.

---

## 5. Algorithme de Dijkstra - Solution Retenue

### 5.1 Pseudocode Détaillé

```
╔════════════════════════════════════════════════════════════════════
║ ALGORITHME: DIJKSTRA(G, S, T)
║
║ ENTRÉES:
║   G : Graphe (gares comme nœuds, connexions de train comme arêtes)
║   S : Gare source (ex: "Bordeaux")
║   T : Gare cible (ex: "Paris")
║   poids : Fonction retournant le poids d'une arête (ex: durée en minutes)
║
║ SORTIES:
║   chemin : Liste de gares de S à T
║   distance_totale : Temps/distance total de trajet
╚════════════════════════════════════════════════════════════════════

PHASE 1: INITIALISATION
------------------------
POUR chaque gare v dans G.sommets:
    distance[v] ← ∞              // Distance inconnue depuis S
    predecesseur[v] ← NULL       // Pas encore de chemin
FIN POUR

distance[S] ← 0                  // Distance de S à elle-même est 0

Q ← FilePrioritéMin()            // Min-heap ordonné par distance
Q.inserer_tous(G.sommets)        // Ajouter toutes les gares à la file


PHASE 2: BOUCLE PRINCIPALE (EXPANSION GLOUTONNE)
-------------------------------------------------
TANT QUE Q n'est pas vide:

    u ← Q.extraire_min()         // Obtenir la gare avec la plus petite distance

    // Optimisation de terminaison anticipée
    SI u == T:
        SORTIR                   // Plus court chemin vers la cible trouvé!
    FIN SI

    // Explorer tous les voisins de u
    POUR chaque voisin v de u:
        poids_arete ← poids(u, v)            // ex: 120 minutes
        distance_alternative ← distance[u] + poids_arete

        // ÉTAPE DE RELAXATION
        SI distance_alternative < distance[v]:
            distance[v] ← distance_alternative
            predecesseur[v] ← u
            Q.diminuer_priorite(v, distance_alternative)
        FIN SI
    FIN POUR
FIN TANT QUE


PHASE 3: RECONSTRUCTION DU CHEMIN
----------------------------------
SI distance[T] == ∞:
    RETOURNER "Aucun chemin n'existe", ∞
FIN SI

chemin ← liste vide
courant ← T

TANT QUE courant ≠ NULL:
    chemin.inserer_au_debut(courant)     // Construire le chemin en arrière
    courant ← predecesseur[courant]
FIN TANT QUE

RETOURNER chemin, distance[T]
```

### 5.2 Exemple Pas à Pas

**Réseau**:
```
Bordeaux --300min--> Tours --120min--> Paris
Bordeaux --480min--> Lyon --200min--> Paris
```

**Exécution** de `DIJKSTRA(G, "Bordeaux", "Paris")`:

| Itération | Nœud Courant | Distance vers Paris | Prédécesseur | File de Priorité |
|-----------|--------------|---------------------|--------------|------------------|
| **Init** | - | {Bordeaux:0, Tours:∞, Lyon:∞, Paris:∞} | {tous NULL} | [Bordeaux(0), Tours(∞), Lyon(∞), Paris(∞)] |
| **1** | Bordeaux | {Bordeaux:0, Tours:300, Lyon:480, Paris:∞} | {Tours←Bordeaux, Lyon←Bordeaux} | [Tours(300), Lyon(480), Paris(∞)] |
| **2** | Tours | {Bordeaux:0, Tours:300, Lyon:480, Paris:420} | {Paris←Tours} | [Paris(420), Lyon(480)] |
| **3** | Paris | **Cible atteinte!** | - | [Lyon(480)] |

**Résultat**:
- Chemin: `["Bordeaux", "Tours", "Paris"]`
- Durée totale: `420 minutes`

**Pourquoi pas Bordeaux → Lyon → Paris (680 min)?**
Dijkstra garantit le chemin optimal en traitant toujours le nœud non visité le plus proche en premier.

### 5.3 Preuve de Complexité Temporelle

**Opérations**:
1. **Initialisation**: O(V) - Mettre toutes les distances à ∞
2. **Construction du tas**: O(V) - Ajouter tous les sommets à la file de priorité
3. **Boucle principale**:
   - Chaque sommet extrait une fois: **V × log V** (extraction min du tas)
   - Chaque arête relaxée une fois: **E × log V** (diminution de priorité du tas)
4. **Reconstruction du chemin**: O(V) - Suivre les liens de prédécesseur

**Total**: O(V + V + V log V + E log V + V) = **O((V+E) log V)**

**Avec Tas de Fibonacci** (avancé): O(V log V + E) - mais complexe à implémenter.

### 5.4 Preuve de Correction (Esquisse)

**Affirmation**: Quand Dijkstra finalise le nœud u, `distance[u]` est le vrai plus court chemin de S à u.

**Preuve par induction**:
1. **Cas de base**: `distance[S] = 0` est correct (distance vers soi-même)
2. **Étape inductive**: Supposer que tous les nœuds finalisés ont les bonnes distances
   - Soit u le prochain nœud extrait (plus petite distance tentative)
   - Tout autre chemin vers u doit passer par des nœuds non finalisés avec distance ≥ distance[u]
   - Puisque les poids sont non-négatifs, ces chemins ne peuvent pas être plus courts
   - Donc, `distance[u]` est optimal ✓

**Cette preuve ÉCHOUE avec des poids négatifs!** (contre-exemple: S→A=1, A→B=-5, S→B=0)

---

## 6. Évaluation des Bases de Données Graphe

### 6.1 Neo4j - Base de Données Graphe de Production

**Architecture**:
```cypher
// Définition de nœud
(gare:Gare {
    nom: "Paris",
    lat: 48.8566,
    lon: 2.3522,
    region: "Île-de-France"
})

// Définition de relation
(bordeaux:Gare {nom:"Bordeaux"})
    -[:TRAIN_VERS {
        duree: 300,
        ligne: "TGV",
        frequence: "horaire"
    }]->
(paris:Gare {nom:"Paris"})
```

**Requête Cypher** (plus court chemin):
```cypher
MATCH chemin = shortestPath(
  (depart:Gare {nom:"Bordeaux"})
      -[:TRAIN_VERS*]->
  (arrivee:Gare {nom:"Paris"})
)
RETURN [n in nodes(chemin) | n.nom] AS itineraire,
       reduce(total=0, r in relationships(chemin) | total + r.duree) AS duree
```

**Avantages**:
- ✅ Stockage graphe natif (optimisé pour les traversées)
- ✅ Algorithmes intégrés (Dijkstra, A*, PageRank)
- ✅ Stockage persistant (survit aux crashes)
- ✅ Support multi-utilisateurs (requêtes concurrentes)
- ✅ Langage de requête riche (Cypher)
- ✅ Outils de visualisation (Neo4j Browser)

**Inconvénients**:
- ❌ Configuration complexe (déploiement Docker/Cloud)
- ❌ Courbe d'apprentissage (syntaxe Cypher, modélisation graphe)
- ❌ Surdimensionné pour réseau de 66 gares
- ❌ Complexité de déploiement pour projet académique
- ❌ Coût (version desktop gratuite, cloud payant)

**Meilleur pour**: Systèmes de production avec >100k nœuds, requêtes temps réel, analyses complexes

### 6.2 NetworkX - Graphes Python En Mémoire

**Configuration**:
```python
import networkx as nx

# Créer le graphe
G = nx.Graph()

# Ajouter des arêtes avec poids
G.add_edge("Bordeaux", "Paris", duree=300, ligne="TGV")
G.add_edge("Paris", "Lyon", duree=120, ligne="TGV")

# Calculer le plus court chemin
chemin = nx.shortest_path(G, "Bordeaux", "Lyon", weight="duree")
longueur = nx.shortest_path_length(G, "Bordeaux", "Lyon", weight="duree")

print(chemin)     # ['Bordeaux', 'Paris', 'Lyon']
print(longueur)   # 420
```

**Avantages**:
- ✅ Installation simple: `pip install networkx`
- ✅ Python pur (intégration facile avec le module NLP)
- ✅ Pas de serveur requis (s'exécute dans le même processus)
- ✅ Rapide pour graphes petits/moyens (<10k nœuds)
- ✅ Bibliothèque d'algorithmes riche (Dijkstra, A*, centralité, etc.)
- ✅ Tests et débogage faciles

**Inconvénients**:
- ❌ En mémoire uniquement (données perdues à la sortie)
- ❌ Pas d'accès concurrent (processus unique)
- ❌ Limité à l'écosystème Python

**Meilleur pour**: Projets de recherche, prototypes, traitement par lots, travail académique

### 6.3 Comparaison de Performance

**Benchmark**: Trouver le plus court chemin dans le réseau SNCF (1000 gares, 5000 connexions)

| Opération | Neo4j (cache froid) | Neo4j (cache chaud) | NetworkX |
|-----------|---------------------|---------------------|----------|
| **Charger graphe** | ~2000ms | ~50ms | ~100ms |
| **Plus court chemin unique** | ~10ms | ~1ms | ~5ms |
| **100 requêtes de chemin** | ~1000ms | ~100ms | ~500ms |
| **Usage mémoire** | ~200MB (serveur) | ~200MB | ~50MB |

**Verdict**: NetworkX est **suffisant** pour l'échelle du projet (66 gares, traitement par lots).

### 6.4 Recommandation: NetworkX

| Critère | Neo4j | NetworkX | Gagnant |
|---------|-------|----------|---------|
| **Portée du projet** | Surdimensionné | Parfait | ✅ NetworkX |
| **Complexité de configuration** | Élevée | Faible | ✅ NetworkX |
| **Courbe d'apprentissage** | Abrupte | Douce | ✅ NetworkX |
| **Performance (66 gares)** | Surdimensionné | Excellente | ✅ NetworkX |
| **Intégration avec NLP Python** | Moyenne | Native | ✅ NetworkX |
| **Déploiement** | Complexe | Simple | ✅ NetworkX |
| **Coût** | Payant (cloud) | Gratuit | ✅ NetworkX |

**Décision**: Utiliser **NetworkX** pour la Phase 7.
**Future**: Considérer Neo4j si le projet scale vers:
- >10 000 gares (réseau ferroviaire européen complet)
- Requêtes passagers temps réel
- Analyses complexes (routes les plus fréquentées, mesures de centralité)

---

## 7. Feuille de Route d'Implémentation

### 7.1 Phase 7 - Module Pathfinding (4 semaines)

#### Semaine 1: Collection de Données et Construction du Graphe
**Objectif**: Charger les données SNCF dans un graphe NetworkX

**Tâches**:
1. **Trouver les données ouvertes SNCF** (sources):
   - [SNCF Open Data](https://data.sncf.com/) - API officielle
   - [Format GTFS](https://developers.google.com/transit/gtfs) - données de transport standardisées
   - Solution de secours: CSV manuel avec 66 gares du projet

2. **Format CSV** (`data/sncf_connections.csv`):
   ```csv
   origin,destination,duration_minutes,line_type,frequency
   Paris,Lyon,120,TGV,horaire
   Lyon,Marseille,90,TGV,horaire
   Paris,Bordeaux,180,TGV,toutes_les_2h
   ```

3. **Chargeur de graphe** (`src/pathfinding/graph_loader.py`):
   ```python
   def load_sncf_graph(csv_path: str) -> nx.Graph:
       """Charger le réseau SNCF depuis CSV dans un graphe NetworkX"""
       G = nx.Graph()
       with open(csv_path, 'r', encoding='utf-8') as f:
           reader = csv.DictReader(f)
           for row in reader:
               G.add_edge(
                   row['origin'],
                   row['destination'],
                   duration=int(row['duration_minutes']),
                   line=row['line_type']
               )
       return G
   ```

**Livrable**: `graph_loader.py` fonctionnel avec tests unitaires

#### Semaine 2: Implémentation de Dijkstra
**Objectif**: Implémenter Dijkstra from scratch (exigence pédagogique)

**Implémentation** (`src/pathfinding/dijkstra.py`):
```python
import heapq
from typing import List, Tuple, Optional

def dijkstra(
    graph: nx.Graph,
    source: str,
    target: str,
    weight: str = 'duration'
) -> Tuple[Optional[List[str]], float]:
    """
    Calculer le plus court chemin avec l'algorithme de Dijkstra

    Args:
        graph: Graphe NetworkX avec arêtes pondérées
        source: Nom de la gare de départ
        target: Nom de la gare de destination
        weight: Attribut d'arête à utiliser comme poids

    Returns:
        (chemin, distance_totale) ou (None, inf) si aucun chemin n'existe

    Complexité Temporelle: O((V+E) log V)
    Complexité Spatiale: O(V)
    """
    # Initialisation
    distance = {node: float('inf') for node in graph.nodes}
    predecessor = {node: None for node in graph.nodes}
    distance[source] = 0

    # File de priorité: (distance, nœud)
    pq = [(0, source)]
    visited = set()

    # Boucle principale
    while pq:
        current_dist, current_node = heapq.heappop(pq)

        # Ignorer si déjà traité
        if current_node in visited:
            continue
        visited.add(current_node)

        # Terminaison anticipée
        if current_node == target:
            break

        # Explorer les voisins
        for neighbor in graph.neighbors(current_node):
            edge_data = graph[current_node][neighbor]
            edge_weight = edge_data.get(weight, 1)

            alternative_dist = current_dist + edge_weight

            # Relaxation
            if alternative_dist < distance[neighbor]:
                distance[neighbor] = alternative_dist
                predecessor[neighbor] = current_node
                heapq.heappush(pq, (alternative_dist, neighbor))

    # Reconstruction du chemin
    if distance[target] == float('inf'):
        return None, float('inf')

    path = []
    current = target
    while current is not None:
        path.append(current)
        current = predecessor[current]
    path.reverse()

    return path, distance[target]
```

**Validation**: Comparer avec `nx.shortest_path()` pour la correction

**Livrable**: Implémentation Dijkstra fonctionnelle + tests unitaires

#### Semaine 3: Intégration du Pipeline
**Objectif**: Connecter la sortie du module NLP à l'entrée du pathfinding

**Pipeline** (`src/main.py`):
```python
def process_csv(input_path: str, output_path: str):
    """
    Pipeline complet: Extraction NLP + Pathfinding

    Entrée:  sentenceID,sentence
    Sortie: sentenceID,Origin,Stop1,...,Destination
    """
    # Charger le graphe SNCF une fois
    graph = load_sncf_graph('data/sncf_connections.csv')

    # Extraction NLP
    nlp_results = extract_orders(input_path)  # Depuis Phase 5

    # Pathfinding pour chaque ordre
    with open(output_path, 'w', encoding='utf-8') as out:
        writer = csv.writer(out)

        for sentence_id, origin, dest in nlp_results:
            if origin == "INVALID" or dest == "INVALID":
                writer.writerow([sentence_id, "INVALID", "INVALID"])
                continue

            path, duration = dijkstra(graph, origin, dest)

            if path is None:
                writer.writerow([sentence_id, origin, "INVALID", dest])
            else:
                writer.writerow([sentence_id] + path)
```

**Livrable**: Traitement CSV de bout en bout

#### Semaine 4: Tests et Optimisation
**Tâches**:
1. **Profilage de performance**:
   ```python
   import time

   start = time.time()
   path, dist = dijkstra(G, "Bordeaux", "Paris")
   elapsed = time.time() - start

   print(f"Chemin trouvé en {elapsed*1000:.2f}ms")
   ```

2. **Optimisation par lots** (si nécessaire):
   - Utiliser `nx.all_pairs_dijkstra()` pour précalculer tous les chemins
   - Stocker dans un cache pour recherche instantanée

3. **Cas particuliers**:
   - Source == cible → retourner `[source]`
   - Gares pas dans le graphe → retourner INVALID
   - Composantes déconnectées → détecter et signaler

**Livrable**: Module de pathfinding prêt pour la production

---

## 8. Annexes

### Annexe A: Aide-Mémoire Complexité des Algorithmes

| Algorithme | Meilleur Cas | Cas Moyen | Pire Cas | Espace |
|-----------|--------------|-----------|----------|--------|
| Dijkstra | O(V log V) | O((V+E) log V) | O((V+E) log V) | O(V) |
| A* | O(E) | O((V+E) log V) | O((V+E) log V) | O(V) |
| Bellman-Ford | O(V·E) | O(V·E) | O(V·E) | O(V) |
| BFS (non pondéré) | O(V+E) | O(V+E) | O(V+E) | O(V) |

### Annexe B: Référence Rapide NetworkX

```python
# Création de graphe
G = nx.Graph()                    # Non dirigé
G = nx.DiGraph()                  # Dirigé

# Ajouter nœuds/arêtes
G.add_node("Paris", population=2_200_000)
G.add_edge("Paris", "Lyon", duree=120)

# Algorithmes
nx.shortest_path(G, "A", "B", weight="duree")
nx.shortest_path_length(G, "A", "B", weight="duree")
nx.all_shortest_paths(G, "A", "B")  # Tous les chemins de longueur égale

# Analyse
nx.is_connected(G)                # Vérifier connectivité
nx.number_of_nodes(G)
nx.number_of_edges(G)
nx.degree(G, "Paris")             # Nombre de connexions
```

### Annexe C: Alternative - Esquisse d'Implémentation A*

**Pour amélioration future si données GPS disponibles**:

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculer la distance du grand cercle en km"""
    R = 6371  # Rayon de la Terre
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def a_star(graph, source, target, coords):
    """
    A* avec heuristique géographique

    coords = {gare: (lat, lon)}
    heuristique(n) = haversine(n, target) / vitesse_moy
    """
    def h(node):
        distance_km = haversine(*coords[node], *coords[target])
        vitesse_moy = 120  # km/h
        return distance_km / vitesse_moy * 60  # minutes

    # Priorité: f(n) = g(n) + h(n)
    pq = [(h(source), 0, source)]  # (f_score, g_score, nœud)

    # ... similaire à Dijkstra mais avec priorité heuristique ...
```

### Annexe D: Stratégie de Tests

```python
# Tests unitaires (pytest)
def test_dijkstra_simple_path():
    G = nx.Graph()
    G.add_edge("A", "B", duree=10)
    G.add_edge("B", "C", duree=20)

    path, dist = dijkstra(G, "A", "C")
    assert path == ["A", "B", "C"]
    assert dist == 30

def test_dijkstra_no_path():
    G = nx.Graph()
    G.add_edge("A", "B", duree=10)
    G.add_node("C")  # Déconnecté

    path, dist = dijkstra(G, "A", "C")
    assert path is None
    assert dist == float('inf')

def test_dijkstra_vs_networkx():
    """Correction: comparer avec référence NetworkX"""
    G = load_sncf_graph('data/sncf_connections.csv')

    for source, target in [("Paris", "Lyon"), ("Bordeaux", "Marseille")]:
        notre_chemin, notre_dist = dijkstra(G, source, target)
        nx_chemin = nx.shortest_path(G, source, target, weight='duree')
        nx_dist = nx.shortest_path_length(G, source, target, weight='duree')

        assert notre_chemin == nx_chemin
        assert notre_dist == nx_dist
```

---

## Conclusion

Ce document fournit une justification complète pour le choix de **l'algorithme de Dijkstra avec NetworkX** pour le module de pathfinding du Travel Order Resolver. La décision privilégie:

1. **Correction**: Dijkstra garantit les chemins optimaux pour poids positifs
2. **Simplicité**: Implémentation straightforward pour contexte académique
3. **Performance**: O((V+E) log V) scale bien à la taille du réseau SNCF
4. **Praticité**: NetworkX s'intègre parfaitement avec le module NLP Python

Le pseudocode et le guide d'implémentation fournis permettent un développement immédiat en Phase 7.

**Prochaines Étapes**:
- [x] Sélection d'algorithme documentée
- [ ] Collecter données des gares SNCF
- [ ] Implémenter `graph_loader.py`
- [ ] Implémenter `dijkstra.py`
- [ ] Intégrer avec le pipeline NLP
- [ ] Valider sur le jeu de données de test

**Améliorations Futures**:
- Algorithme A* avec heuristique GPS (accélération de 10-50%)
- Optimisation multi-critères (durée + coût + correspondances)
- Intégration API SNCF temps réel
- Migration Neo4j pour réseau >10k gares
