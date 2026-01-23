# Railway Network Graph Schema

## Overview

This document defines the NetworkX graph schema for the Travel Order Resolver pathfinding module.

**Date**: 2026-01-23
**Ticket**: KAN-28 - Build graph database schema

---

## Graph Type

**Weighted, Undirected Graph** using NetworkX

### Rationale
- **Weighted**: Edge weights represent travel time/distance between stations
- **Undirected**: Train connections work in both directions (Paris → Lyon = Lyon → Paris)
- **NetworkX**: Simple, sufficient for project scale (~66-2,782 stations)

---

## Node Schema

### Node ID
**UIC Code** (8-digit unique station identifier)

Example: `87686006` (Paris Gare du Nord)

### Node Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `uic_code` | str | Unique identifier (8 digits) | `"87686006"` |
| `station_name` | str | Official station name | `"Paris Gare du Nord"` |
| `station_name_normalized` | str | Normalized for matching | `"paris gare du nord"` |
| `city_name` | str | Associated city | `"Paris"` |
| `city_name_normalized` | str | Normalized city name | `"paris"` |
| `latitude` | float | GPS latitude | `48.8799` |
| `longitude` | float | GPS longitude | `2.3553` |
| `segment_drg` | str | Station category (A/B/C) | `"A"` |

**Example Node**:
```python
G.nodes['87686006'] = {
    'uic_code': '87686006',
    'station_name': 'Paris Gare du Nord',
    'station_name_normalized': 'paris gare du nord',
    'city_name': 'Paris',
    'city_name_normalized': 'paris',
    'latitude': 48.8799,
    'longitude': 2.3553,
    'segment_drg': 'A'
}
```

---

## Edge Schema

### Edge Definition
Represents a direct railway connection between two stations.

**Format**: `(node1_uic, node2_uic, edge_attributes)`

### Edge Attributes

| Attribute | Type | Description | Example | Required |
|-----------|------|-------------|---------|----------|
| `weight` | float | Travel time (minutes) or distance (km) | `120.5` | Yes |
| `distance_km` | float | Geographic distance (Haversine) | `392.5` | Optional |
| `line_code` | str | Railway line identifier | `"033000"` | Optional |
| `connection_type` | str | Type of connection | `"direct"` / `"transfer"` | Optional |

**Example Edge**:
```python
G.add_edge('87686006', '87722025', weight=120, distance_km=392, line_code='033000')
# Paris Gare du Nord → Lyon Part Dieu: 120 minutes, 392 km
```

---

## Data Sources

### Phase 1: Simplified Network (KAN-28, KAN-29)
For initial implementation and testing:

**Input Files**:
1. **Nodes**: `data/processed/sncf/stations_clean.csv`
   - Contains: 2,782 stations with all node attributes
   - Used: Subset of major cities (~50-100 stations)

2. **Edges**: `data/processed/sncf/connections.csv` (to be created)
   - Format: `origin_uic,destination_uic,duration_minutes,distance_km`
   - Example:
     ```csv
     87686006,87722025,120,392
     87686006,87271007,135,505
     ```

### Phase 2: Full Network (Future - KAN-29+)
For complete SNCF network:

**Input Files**:
1. **GeoJSON Extraction**: `data/raw/sncf/formes-des-lignes-du-rfn.geojson`
   - Parse LineString geometries
   - Match stations to line endpoints
   - Calculate distances using Haversine formula
   - Estimate travel times (distance / avg speed)

2. **Timetable Data** (Optional): Real SNCF schedules if available

---

## Graph Construction Algorithm

### Step 1: Load Stations (Nodes)
```python
import pandas as pd
import networkx as nx

def load_stations(graph: nx.Graph, stations_file: str, subset: list = None):
    """
    Load stations as graph nodes.

    Args:
        graph: NetworkX graph object
        stations_file: Path to stations_clean.csv
        subset: Optional list of UIC codes to load (for testing)
    """
    df = pd.read_csv(stations_file, encoding='utf-8')

    # Filter to subset if provided
    if subset:
        df = df[df['uic_code'].isin(subset)]

    # Add each station as a node
    for _, station in df.iterrows():
        graph.add_node(
            station['uic_code'],
            uic_code=station['uic_code'],
            station_name=station['station_name'],
            station_name_normalized=station['station_name_normalized'],
            city_name=station['city_name'],
            city_name_normalized=station['city_name_normalized'],
            latitude=station['latitude'],
            longitude=station['longitude'],
            segment_drg=station['segment_drg']
        )
```

### Step 2: Load Connections (Edges)
```python
def load_connections(graph: nx.Graph, connections_file: str):
    """
    Load connections as graph edges.

    Args:
        graph: NetworkX graph object
        connections_file: Path to connections.csv
    """
    df = pd.read_csv(connections_file, encoding='utf-8')

    for _, conn in df.iterrows():
        graph.add_edge(
            conn['origin_uic'],
            conn['destination_uic'],
            weight=conn['duration_minutes'],
            distance_km=conn.get('distance_km', None)
        )
```

### Step 3: Build Complete Graph
```python
def build_railway_graph(stations_file: str, connections_file: str) -> nx.Graph:
    """
    Build complete railway network graph.

    Returns:
        NetworkX Graph with stations and connections
    """
    G = nx.Graph()

    load_stations(G, stations_file)
    load_connections(G, connections_file)

    return G
```

---

## Graph Statistics & Validation

### Expected Statistics (Simplified Network)
- **Nodes**: 50-100 major stations
- **Edges**: 150-300 connections
- **Average Degree**: 3-6 (each station connects to 3-6 others)
- **Connected Components**: 1 (fully connected network)
- **Diameter**: ~8-12 hops (max path length)

### Validation Checks
```python
def validate_graph(G: nx.Graph):
    """Validate graph structure and connectivity."""

    # Basic checks
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")

    # Connectivity check
    if nx.is_connected(G):
        print("[OK] Graph is fully connected")
    else:
        components = list(nx.connected_components(G))
        print(f"[WARNING] Graph has {len(components)} disconnected components")

    # Orphaned nodes (no connections)
    orphans = [n for n in G.nodes() if G.degree(n) == 0]
    if orphans:
        print(f"[WARNING] {len(orphans)} orphaned nodes (no connections)")

    # Average degree
    avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
    print(f"Average degree: {avg_degree:.2f}")

    # Diameter (if connected)
    if nx.is_connected(G):
        diameter = nx.diameter(G)
        print(f"Graph diameter: {diameter} hops")
```

---

## Query Examples

### Find Shortest Path
```python
import networkx as nx

# Find shortest path (by weight)
path = nx.shortest_path(G, source='87686006', target='87722025', weight='weight')
print(f"Path: {[G.nodes[n]['station_name'] for n in path]}")

# Get total travel time
total_time = nx.shortest_path_length(G, source='87686006', target='87722025', weight='weight')
print(f"Total time: {total_time} minutes")
```

### Get Station Neighbors
```python
# Get all directly connected stations
neighbors = list(G.neighbors('87686006'))
for neighbor_uic in neighbors:
    station = G.nodes[neighbor_uic]
    edge_data = G.edges['87686006', neighbor_uic]
    print(f"{station['station_name']}: {edge_data['weight']} min")
```

### Calculate Distance
```python
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two GPS coordinates (in km)."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in km
    return c * r
```

---

## File Structure

```
data/
├── processed/
│   └── sncf/
│       ├── stations_clean.csv        # All stations (2,782)
│       ├── stations_subset.csv       # Major cities only (~66)
│       └── connections.csv           # Station-to-station connections
│
src/
└── pathfinding/
    ├── __init__.py
    ├── graph_loader.py               # Load graph from CSV files
    ├── dijkstra.py                   # Pathfinding algorithm
    └── utils.py                      # Helper functions (haversine, etc.)
```

---

## Next Steps

### KAN-28 (Current)
- [x] Define graph schema
- [ ] Create sample connections.csv
- [ ] Implement graph_loader.py
- [ ] Create demo script
- [ ] Validate graph structure

### KAN-29 (Next)
- [ ] Extract connections from GeoJSON
- [ ] Calculate real distances using Haversine
- [ ] Estimate travel times from distances
- [ ] Expand to full network (2,782 stations)

### KAN-30 (Testing)
- [ ] Validate pathfinding results
- [ ] Test sample queries (Paris → Lyon, etc.)
- [ ] Performance benchmarks

---

## References

- **NetworkX Documentation**: https://networkx.org/
- **SNCF Open Data**: https://data.sncf.com/
- **Dijkstra's Algorithm**: O((V + E) log V) complexity
- **Haversine Formula**: Calculate GPS distance

---

**Status**: KAN-28 ✅ Schema defined
**Next**: Implement graph_loader.py
