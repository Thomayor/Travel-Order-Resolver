# Pathfinding Algorithm Comparison and Implementation Guide

**Project**: Travel Order Resolver - EPITECH NLP Project
**Module**: Graph Pathfinding for SNCF Railway Network
**Date**: January 2026
**Status**: Algorithm Selection Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Modeling](#problem-modeling)
3. [Algorithm Complexity Theory](#algorithm-complexity-theory)
4. [Algorithm Comparison](#algorithm-comparison)
5. [Dijkstra's Algorithm - Selected Solution](#dijkstras-algorithm---selected-solution)
6. [Graph Database Evaluation](#graph-database-evaluation)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Appendices](#appendices)

---

## 1. Executive Summary

### Context
The Travel Order Resolver extracts departure and destination stations from French natural language commands (NLP module), then computes optimal train routes through the SNCF railway network (pathfinding module).

### Recommendation
**Algorithm**: **Dijkstra's Algorithm**
**Graph Library**: **NetworkX (Python)**

### Justification
- ✅ **Optimal for non-negative weights** (train durations/distances are always positive)
- ✅ **Efficient complexity**: O((V+E) log V) with priority queue
- ✅ **Simple to implement** and explain in academic context
- ✅ **Guarantees shortest path** for weighted graphs
- ✅ **Well-suited for SNCF network scale** (~3000 stations, ~10,000 connections)

### Alternatives Considered
- **A***: Requires GPS coordinates for heuristic (future enhancement)
- **Bellman-Ford**: Too slow (O(V·E)), unnecessary for positive weights
- **Neo4j**: Over-engineered for project scope; NetworkX sufficient

---

## 2. Problem Modeling

### 2.1 Railway Network as a Graph

The SNCF railway network naturally maps to a **weighted directed graph**:

```
Graph G = (V, E)
├── V (Vertices) = Railway stations/cities
│   ├── Examples: "Paris", "Lyon", "Bordeaux"
│   ├── Size: ~3000 stations in full SNCF network
│   └── Project: ~66 major cities (Phase 7)
│
└── E (Edges) = Direct train connections
    ├── Weight = Travel duration (minutes) OR distance (km)
    ├── Always positive (no negative durations!)
    └── Size: ~10,000 connections in full network
```

### 2.2 Input/Output Format

**Input** (from NLP module):
```csv
sentenceID,Departure,Destination
1,Bordeaux,Paris
2,Lyon,Marseille
```

**Output** (from Pathfinding module):
```csv
sentenceID,Origin,Stop1,Stop2,...,Destination
1,Bordeaux,Tours,Paris
2,Lyon,Avignon,Marseille
```

**Edge Cases**:
- No path exists → `sentenceID,Departure,INVALID,INVALID`
- Direct connection → `sentenceID,Departure,Destination` (no intermediate stops)

### 2.3 Real-World Constraints

| Constraint | Value | Impact on Algorithm |
|-----------|-------|---------------------|
| Station count (V) | 66 (project) / 3000 (full) | Dijkstra scales well |
| Connection count (E) | ~200 (project) / 10,000 (full) | O(E log V) acceptable |
| Weight type | Positive integers (minutes) | Dijkstra optimal |
| Graph density | Sparse (E ≈ 3V) | Priority queue efficient |
| Query frequency | Batch processing (CSV) | No real-time requirement |

---

## 3. Algorithm Complexity Theory

### 3.1 Big-O Notation Explained

**Definition**: O(f(n)) describes how runtime grows as input size n increases.

```
For graph algorithms:
├── V = number of vertices (stations)
└── E = number of edges (connections)

Example:
├── V = 1000 stations
├── E = 5000 connections
└── If V doubles → V = 2000, E ≈ 10,000
```

### 3.2 Common Complexities

| Notation | Growth Rate | Example | If V doubles... |
|----------|-------------|---------|-----------------|
| O(V) | Linear | Visiting each station once | Runtime ×2 |
| O(E) | Linear | Checking each connection once | Runtime ×2 |
| O(V²) | Quadratic | Comparing all station pairs | Runtime ×4 |
| O(V·E) | Polynomial | Bellman-Ford | Runtime ×8+ |
| O((V+E) log V) | Quasi-linear | Dijkstra/A* | Runtime ×2.3 |

### 3.3 Practical Complexity Comparison

**Scenario**: SNCF network with V=1000 stations, E=5000 connections

| Algorithm | Complexity | Operations | Relative Speed |
|-----------|-----------|------------|----------------|
| Dijkstra | O((V+E) log V) | 6000 × 10 = 60,000 | **1x (baseline)** |
| A* | O((V+E) log V) | ~40,000 (with good heuristic) | **1.5x faster** |
| Bellman-Ford | O(V·E) | 1000 × 5000 = 5,000,000 | **83x slower** |

**Why O((V+E) log V)?**
```
Dijkstra uses a min-heap (priority queue):
├── (V+E) = Total stations + connections to examine
└── log V = Cost per heap insert/extract operation

Breakdown:
├── Each vertex extracted once from heap: V × log V
└── Each edge relaxes neighbor: E × log V
└── Total: (V+E) × log V
```

---

## 4. Algorithm Comparison

### 4.1 Summary Table

| Algorithm | Core Idea | Negative Weights | Optimality (positive weights) | Time Complexity |
|-----------|-----------|------------------|-------------------------------|-----------------|
| **Dijkstra** | Greedy: always process nearest unvisited node | ❌ No | ✅ Yes | **O((V+E) log V)** |
| **A*** | Dijkstra + distance heuristic to goal | ❌ No | ✅ Yes (if heuristic admissible) | **O((V+E) log V)** |
| **Bellman-Ford** | Relax all edges V-1 times | ✅ Yes | ✅ Yes | **O(V·E)** |

### 4.2 Dijkstra's Algorithm

**Principle**: Greedily expand the closest unvisited node, maintaining the shortest known distance to all nodes.

**How it works**:
1. Start at source S with distance 0
2. Always process the node U with smallest known distance
3. Update distances to all neighbors V of U
4. Repeat until target T is reached

**Strengths**:
- ✅ Optimal for non-negative weights (proven mathematically)
- ✅ Efficient with priority queue: O((V+E) log V)
- ✅ Simple to implement and understand
- ✅ Well-tested in production (GPS navigation, network routing)

**Weaknesses**:
- ❌ Fails with negative weights (can get stuck in wrong local optimum)
- ❌ No heuristic guidance toward goal (explores all directions equally)

**Best for**: Train networks (durations always positive), road networks, network packets

### 4.3 A* Algorithm

**Principle**: Dijkstra + heuristic function h(n) estimating remaining distance to goal.

**Priority function**: `f(n) = g(n) + h(n)`
- g(n) = actual distance from start to n
- h(n) = estimated distance from n to goal

**Example heuristic for trains**:
```python
def heuristic(station_current, station_goal):
    """Estimate remaining travel time using straight-line distance"""
    distance_km = haversine_distance(
        lat_lon[station_current],
        lat_lon[station_goal]
    )
    avg_speed_kmh = 120  # TGV average speed
    return distance_km / avg_speed_kmh * 60  # Convert to minutes
```

**Strengths**:
- ✅ Faster than Dijkstra (explores fewer nodes)
- ✅ Still optimal if heuristic is **admissible** (never overestimates)
- ✅ Ideal when goal location known (GPS coordinates)

**Weaknesses**:
- ❌ Requires good heuristic (needs GPS data for stations)
- ❌ More complex to implement correctly
- ❌ Admissibility hard to guarantee (bad heuristic → wrong results)

**Best for**: GPS navigation, game pathfinding (maps), robotics

### 4.4 Bellman-Ford Algorithm

**Principle**: Relax all edges E repeatedly V-1 times to find shortest paths.

**How it works**:
```python
# Repeat V-1 times:
for u, v, weight in all_edges:
    if distance[u] + weight < distance[v]:
        distance[v] = distance[u] + weight
        predecessor[v] = u
```

**Strengths**:
- ✅ Handles negative weights (loans, discounts in cost graphs)
- ✅ Detects negative cycles (infinite cost reduction loops)
- ✅ Simpler conceptually (no priority queue)

**Weaknesses**:
- ❌ **Very slow**: O(V·E) = 83x slower than Dijkstra for SNCF network
- ❌ Overkill for positive weights (Dijkstra always better)

**Best for**: Financial networks (debts), theoretical graph problems

### 4.5 Why Dijkstra for This Project?

| Criterion | Dijkstra | A* | Bellman-Ford |
|-----------|----------|-----|--------------|
| **Positive weights only** | ✅ Perfect fit | ✅ Yes | ❌ Overkill |
| **Performance** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Faster | ⭐⭐ Slow |
| **Simplicity** | ⭐⭐⭐⭐⭐ Simple | ⭐⭐⭐ Moderate | ⭐⭐⭐⭐ Simple |
| **Data requirements** | Station names only | GPS coordinates needed | Station names only |
| **Pedagogical value** | ⭐⭐⭐⭐⭐ Classic algorithm | ⭐⭐⭐⭐ Advanced topic | ⭐⭐⭐ Specialized use |
| **Implementation time** | ~2-3 hours | ~4-6 hours | ~1-2 hours |

**Decision**: **Dijkstra** is the clear winner for this project.

---

## 5. Dijkstra's Algorithm - Selected Solution

### 5.1 Detailed Pseudocode

```
╔════════════════════════════════════════════════════════════════════
║ ALGORITHM: DIJKSTRA(G, S, T)
║
║ INPUTS:
║   G : Graph (stations as nodes, train connections as edges)
║   S : Source station (e.g., "Bordeaux")
║   T : Target station (e.g., "Paris")
║   weight : Function returning edge weight (e.g., duration in minutes)
║
║ OUTPUTS:
║   path : List of stations from S to T
║   total_distance : Total travel time/distance
╚════════════════════════════════════════════════════════════════════

PHASE 1: INITIALIZATION
------------------------
FOR each station v in G.vertices:
    distance[v] ← ∞              // Unknown distance from S
    predecessor[v] ← NULL         // No path yet
END FOR

distance[S] ← 0                   // Distance from S to itself is 0

Q ← MinPriorityQueue()            // Min-heap ordered by distance
Q.insert_all(G.vertices)          // Add all stations to queue


PHASE 2: MAIN LOOP (GREEDY EXPANSION)
--------------------------------------
WHILE Q is not empty:

    u ← Q.extract_min()           // Get station with smallest distance

    // Early termination optimization
    IF u == T:
        BREAK                      // Found shortest path to target!
    END IF

    // Explore all neighbors of u
    FOR each neighbor v of u:
        edge_weight ← weight(u, v)           // e.g., 120 minutes
        alternative_distance ← distance[u] + edge_weight

        // RELAXATION STEP
        IF alternative_distance < distance[v]:
            distance[v] ← alternative_distance
            predecessor[v] ← u
            Q.decrease_priority(v, alternative_distance)
        END IF
    END FOR
END WHILE


PHASE 3: PATH RECONSTRUCTION
-----------------------------
IF distance[T] == ∞:
    RETURN "No path exists", ∞
END IF

path ← empty list
current ← T

WHILE current ≠ NULL:
    path.insert_at_beginning(current)     // Build path backward
    current ← predecessor[current]
END WHILE

RETURN path, distance[T]
```

### 5.2 Step-by-Step Example

**Network**:
```
Bordeaux --300min--> Tours --120min--> Paris
Bordeaux --480min--> Lyon --200min--> Paris
```

**Execution** of `DIJKSTRA(G, "Bordeaux", "Paris")`:

| Iteration | Current Node | Distance to Paris | Predecessor | Priority Queue |
|-----------|--------------|-------------------|-------------|----------------|
| **Init** | - | {Bordeaux:0, Tours:∞, Lyon:∞, Paris:∞} | {all NULL} | [Bordeaux(0), Tours(∞), Lyon(∞), Paris(∞)] |
| **1** | Bordeaux | {Bordeaux:0, Tours:300, Lyon:480, Paris:∞} | {Tours←Bordeaux, Lyon←Bordeaux} | [Tours(300), Lyon(480), Paris(∞)] |
| **2** | Tours | {Bordeaux:0, Tours:300, Lyon:480, Paris:420} | {Paris←Tours} | [Paris(420), Lyon(480)] |
| **3** | Paris | **Target reached!** | - | [Lyon(480)] |

**Result**:
- Path: `["Bordeaux", "Tours", "Paris"]`
- Total duration: `420 minutes`

**Why not Bordeaux → Lyon → Paris (680 min)?**
Dijkstra guarantees optimal path by always processing the closest unvisited node first.

### 5.3 Time Complexity Proof

**Operations**:
1. **Initialization**: O(V) - Set all distances to ∞
2. **Heap construction**: O(V) - Add all vertices to priority queue
3. **Main loop**:
   - Each vertex extracted once: **V × log V** (heap extract-min)
   - Each edge relaxed once: **E × log V** (heap decrease-priority)
4. **Path reconstruction**: O(V) - Follow predecessor links

**Total**: O(V + V + V log V + E log V + V) = **O((V+E) log V)**

**With Fibonacci Heap** (advanced): O(V log V + E) - but complex to implement.

### 5.4 Correctness Proof (Sketch)

**Claim**: When Dijkstra finalizes node u, `distance[u]` is the true shortest path from S to u.

**Proof by induction**:
1. **Base case**: `distance[S] = 0` is correct (distance to itself)
2. **Inductive step**: Assume all finalized nodes have correct distances
   - Let u be the next node extracted (smallest tentative distance)
   - Any other path to u must go through unfinalized nodes with ≥ distance[u]
   - Since weights are non-negative, those paths can't be shorter
   - Therefore, `distance[u]` is optimal ✓

**This proof FAILS with negative weights!** (counterexample: S→A=1, A→B=-5, S→B=0)

---

## 6. Graph Database Evaluation

### 6.1 Neo4j - Production Graph Database

**Architecture**:
```cypher
// Node definition
(station:Gare {
    name: "Paris",
    lat: 48.8566,
    lon: 2.3522,
    region: "Île-de-France"
})

// Relationship definition
(bordeaux:Gare {name:"Bordeaux"})
    -[:TRAIN_TO {
        duration: 300,
        line: "TGV",
        frequency: "hourly"
    }]->
(paris:Gare {name:"Paris"})
```

**Cypher Query** (shortest path):
```cypher
MATCH path = shortestPath(
  (depart:Gare {name:"Bordeaux"})
      -[:TRAIN_TO*]->
  (arrivee:Gare {name:"Paris"})
)
RETURN [n in nodes(path) | n.name] AS itinerary,
       reduce(total=0, r in relationships(path) | total + r.duration) AS duration
```

**Pros**:
- ✅ Native graph storage (optimized for traversals)
- ✅ Built-in algorithms (Dijkstra, A*, PageRank)
- ✅ Persistent storage (survives crashes)
- ✅ Multi-user support (concurrent queries)
- ✅ Rich query language (Cypher)
- ✅ Visualization tools (Neo4j Browser)

**Cons**:
- ❌ Complex setup (Docker/Cloud deployment)
- ❌ Learning curve (Cypher syntax, graph modeling)
- ❌ Overkill for 66-station network
- ❌ Deployment complexity for academic project
- ❌ Cost (free desktop version, paid cloud)

**Best for**: Production systems with >100k nodes, real-time queries, complex analytics

### 6.2 NetworkX - Python In-Memory Graphs

**Setup**:
```python
import networkx as nx

# Create graph
G = nx.Graph()

# Add edges with weights
G.add_edge("Bordeaux", "Paris", duration=300, line="TGV")
G.add_edge("Paris", "Lyon", duration=120, line="TGV")

# Compute shortest path
path = nx.shortest_path(G, "Bordeaux", "Lyon", weight="duration")
length = nx.shortest_path_length(G, "Bordeaux", "Lyon", weight="duration")

print(path)    # ['Bordeaux', 'Paris', 'Lyon']
print(length)  # 420
```

**Pros**:
- ✅ Simple installation: `pip install networkx`
- ✅ Pure Python (easy integration with NLP module)
- ✅ No server required (runs in same process)
- ✅ Fast for small/medium graphs (<10k nodes)
- ✅ Rich algorithm library (Dijkstra, A*, centrality, etc.)
- ✅ Easy testing and debugging

**Cons**:
- ❌ In-memory only (data lost on exit)
- ❌ No concurrent access (single process)
- ❌ Limited to Python ecosystem

**Best for**: Research projects, prototypes, batch processing, academic work

### 6.3 Performance Comparison

**Benchmark**: Find shortest path in SNCF network (1000 stations, 5000 connections)

| Operation | Neo4j (cold cache) | Neo4j (warm cache) | NetworkX |
|-----------|-------------------|-------------------|----------|
| **Load graph** | ~2000ms | ~50ms | ~100ms |
| **Single shortest path** | ~10ms | ~1ms | ~5ms |
| **100 path queries** | ~1000ms | ~100ms | ~500ms |
| **Memory usage** | ~200MB (server) | ~200MB | ~50MB |

**Verdict**: NetworkX is **sufficient** for project scale (66 stations, batch processing).

### 6.4 Recommendation: NetworkX

| Criterion | Neo4j | NetworkX | Winner |
|-----------|-------|----------|--------|
| **Project scope** | Overkill | Perfect fit | ✅ NetworkX |
| **Setup complexity** | High | Low | ✅ NetworkX |
| **Learning curve** | Steep | Gentle | ✅ NetworkX |
| **Performance (66 stations)** | Overkill | Excellent | ✅ NetworkX |
| **Integration with Python NLP** | Moderate | Native | ✅ NetworkX |
| **Deployment** | Complex | Simple | ✅ NetworkX |
| **Cost** | Paid (cloud) | Free | ✅ NetworkX |

**Decision**: Use **NetworkX** for Phase 7.
**Future**: Consider Neo4j if project scales to:
- >10,000 stations (full European rail network)
- Real-time passenger queries
- Complex analytics (busiest routes, centrality measures)

---

## 7. Implementation Roadmap

### 7.1 Phase 7 - Pathfinding Module (4 weeks)

#### Week 1: Data Collection and Graph Construction
**Goal**: Load SNCF data into NetworkX graph

**Tasks**:
1. **Find SNCF open data** (sources):
   - [SNCF Open Data](https://data.sncf.com/) - official API
   - [GTFS format](https://developers.google.com/transit/gtfs) - standardized transit data
   - Fallback: Manual CSV with 66 project stations

2. **CSV format** (`data/sncf_connections.csv`):
   ```csv
   origin,destination,duration_minutes,line_type,frequency
   Paris,Lyon,120,TGV,hourly
   Lyon,Marseille,90,TGV,hourly
   Paris,Bordeaux,180,TGV,every_2h
   ```

3. **Graph loader** (`src/pathfinding/graph_loader.py`):
   ```python
   def load_sncf_graph(csv_path: str) -> nx.Graph:
       """Load SNCF network from CSV into NetworkX graph"""
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

**Deliverable**: Working `graph_loader.py` with unit tests

#### Week 2: Dijkstra Implementation
**Goal**: Implement Dijkstra from scratch (educational requirement)

**Implementation** (`src/pathfinding/dijkstra.py`):
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
    Compute shortest path using Dijkstra's algorithm

    Args:
        graph: NetworkX graph with weighted edges
        source: Starting station name
        target: Destination station name
        weight: Edge attribute to use as weight

    Returns:
        (path, total_distance) or (None, inf) if no path exists

    Time Complexity: O((V+E) log V)
    Space Complexity: O(V)
    """
    # Initialization
    distance = {node: float('inf') for node in graph.nodes}
    predecessor = {node: None for node in graph.nodes}
    distance[source] = 0

    # Priority queue: (distance, node)
    pq = [(0, source)]
    visited = set()

    # Main loop
    while pq:
        current_dist, current_node = heapq.heappop(pq)

        # Skip if already processed
        if current_node in visited:
            continue
        visited.add(current_node)

        # Early termination
        if current_node == target:
            break

        # Explore neighbors
        for neighbor in graph.neighbors(current_node):
            edge_data = graph[current_node][neighbor]
            edge_weight = edge_data.get(weight, 1)

            alternative_dist = current_dist + edge_weight

            # Relaxation
            if alternative_dist < distance[neighbor]:
                distance[neighbor] = alternative_dist
                predecessor[neighbor] = current_node
                heapq.heappush(pq, (alternative_dist, neighbor))

    # Path reconstruction
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

**Validation**: Compare against `nx.shortest_path()` for correctness

**Deliverable**: Working Dijkstra implementation + unit tests

#### Week 3: Pipeline Integration
**Goal**: Connect NLP module output to pathfinding input

**Pipeline** (`src/main.py`):
```python
def process_csv(input_path: str, output_path: str):
    """
    Full pipeline: NLP extraction + Pathfinding

    Input:  sentenceID,sentence
    Output: sentenceID,Origin,Stop1,...,Destination
    """
    # Load SNCF graph once
    graph = load_sncf_graph('data/sncf_connections.csv')

    # NLP extraction
    nlp_results = extract_orders(input_path)  # From Phase 5

    # Pathfinding for each order
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

**Deliverable**: End-to-end CSV processing

#### Week 4: Testing and Optimization
**Tasks**:
1. **Performance profiling**:
   ```python
   import time

   start = time.time()
   path, dist = dijkstra(G, "Bordeaux", "Paris")
   elapsed = time.time() - start

   print(f"Path found in {elapsed*1000:.2f}ms")
   ```

2. **Batch optimization** (if needed):
   - Use `nx.all_pairs_dijkstra()` to precompute all paths
   - Store in cache for instant lookup

3. **Edge cases**:
   - Source == target → return `[source]`
   - Stations not in graph → return INVALID
   - Disconnected components → detect and report

**Deliverable**: Production-ready pathfinding module

---

## 8. Appendices

### Appendix A: Algorithm Complexity Cheat Sheet

| Algorithm | Best Case | Average Case | Worst Case | Space |
|-----------|-----------|--------------|------------|-------|
| Dijkstra | O(V log V) | O((V+E) log V) | O((V+E) log V) | O(V) |
| A* | O(E) | O((V+E) log V) | O((V+E) log V) | O(V) |
| Bellman-Ford | O(V·E) | O(V·E) | O(V·E) | O(V) |
| BFS (unweighted) | O(V+E) | O(V+E) | O(V+E) | O(V) |

### Appendix B: NetworkX Quick Reference

```python
# Graph creation
G = nx.Graph()                    # Undirected
G = nx.DiGraph()                  # Directed

# Add nodes/edges
G.add_node("Paris", population=2_200_000)
G.add_edge("Paris", "Lyon", duration=120)

# Algorithms
nx.shortest_path(G, "A", "B", weight="duration")
nx.shortest_path_length(G, "A", "B", weight="duration")
nx.all_shortest_paths(G, "A", "B")  # All equal-length paths

# Analysis
nx.is_connected(G)                # Check connectivity
nx.number_of_nodes(G)
nx.number_of_edges(G)
nx.degree(G, "Paris")             # Number of connections
```

### Appendix C: Alternative: A* Implementation Outline

**For future enhancement if GPS data available**:

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in km"""
    R = 6371  # Earth radius
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def a_star(graph, source, target, coords):
    """
    A* with geographic heuristic

    coords = {station: (lat, lon)}
    heuristic(n) = haversine(n, target) / avg_speed
    """
    def h(node):
        distance_km = haversine(*coords[node], *coords[target])
        avg_speed = 120  # km/h
        return distance_km / avg_speed * 60  # minutes

    # Priority: f(n) = g(n) + h(n)
    pq = [(h(source), 0, source)]  # (f_score, g_score, node)

    # ... similar to Dijkstra but with heuristic priority ...
```

### Appendix D: Testing Strategy

```python
# Unit tests (pytest)
def test_dijkstra_simple_path():
    G = nx.Graph()
    G.add_edge("A", "B", duration=10)
    G.add_edge("B", "C", duration=20)

    path, dist = dijkstra(G, "A", "C")
    assert path == ["A", "B", "C"]
    assert dist == 30

def test_dijkstra_no_path():
    G = nx.Graph()
    G.add_edge("A", "B", duration=10)
    G.add_node("C")  # Disconnected

    path, dist = dijkstra(G, "A", "C")
    assert path is None
    assert dist == float('inf')

def test_dijkstra_vs_networkx():
    """Correctness: compare against NetworkX reference"""
    G = load_sncf_graph('data/sncf_connections.csv')

    for source, target in [("Paris", "Lyon"), ("Bordeaux", "Marseille")]:
        our_path, our_dist = dijkstra(G, source, target)
        nx_path = nx.shortest_path(G, source, target, weight='duration')
        nx_dist = nx.shortest_path_length(G, source, target, weight='duration')

        assert our_path == nx_path
        assert our_dist == nx_dist
```

---

## Conclusion

This document provides a complete justification for choosing **Dijkstra's algorithm with NetworkX** for the Travel Order Resolver pathfinding module. The decision prioritizes:

1. **Correctness**: Dijkstra guarantees optimal paths for positive weights
2. **Simplicity**: Straightforward implementation for academic context
3. **Performance**: O((V+E) log V) scales well to SNCF network size
4. **Practicality**: NetworkX integrates seamlessly with Python NLP module

The provided pseudocode and implementation guide enable immediate development in Phase 7.

**Next Steps**:
- [x] Algorithm selection documented
- [ ] Collect SNCF station data
- [ ] Implement `graph_loader.py`
- [ ] Implement `dijkstra.py`
- [ ] Integrate with NLP pipeline
- [ ] Validate on test dataset

**Future Enhancements**:
- A* algorithm with GPS heuristic (10-50% speedup)
- Multi-criteria optimization (duration + cost + transfers)
- Real-time SNCF API integration
- Neo4j migration for >10k station network
