"""
Graph Loader for SNCF Railway Network

This module loads the railway network graph from CSV files into NetworkX.

Ticket: KAN-28 - Build graph database schema
"""

import pandas as pd
import networkx as nx
from typing import List, Optional, Tuple
from pathlib import Path


def load_stations(
    graph: nx.Graph,
    stations_file: str,
    subset: Optional[List[str]] = None
) -> int:
    """
    Load stations as graph nodes.

    Args:
        graph: NetworkX graph object
        stations_file: Path to stations_clean.csv
        subset: Optional list of UIC codes to load (for testing subset)

    Returns:
        Number of stations loaded

    Example:
        >>> G = nx.Graph()
        >>> load_stations(G, 'data/processed/sncf/stations_clean.csv')
        2782
    """
    # Load stations data
    df = pd.read_csv(stations_file, encoding='utf-8')

    # Filter to subset if provided
    if subset:
        df = df[df['uic_code'].isin(subset)]

    # Build alias map: alternative UIC codes -> primary UIC code
    uic_alias_map = {}

    # Add each station as a node
    for _, station in df.iterrows():
        # Handle multiple UIC codes (semicolon-separated)
        all_uics = [u.strip() for u in str(station['uic_code']).split(';')]
        uic_code = all_uics[0]

        graph.add_node(
            uic_code,
            uic_code=uic_code,
            station_name=station['station_name'],
            station_name_normalized=station['station_name_normalized'],
            city_name=station['city_name'],
            city_name_normalized=station['city_name_normalized'],
            latitude=station['latitude'] if pd.notna(station['latitude']) else None,
            longitude=station['longitude'] if pd.notna(station['longitude']) else None,
            segment_drg=station['segment_drg'] if pd.notna(station['segment_drg']) else None
        )

        # Map all alternative UICs to the primary
        for alt_uic in all_uics[1:]:
            uic_alias_map[alt_uic] = uic_code

    # Store alias map on graph for use by load_connections
    graph.graph['uic_alias_map'] = uic_alias_map

    return len(graph.nodes())


def load_connections(
    graph: nx.Graph,
    connections_file: str
) -> int:
    """
    Load connections as graph edges.

    Args:
        graph: NetworkX graph object
        connections_file: Path to connections.csv

    Returns:
        Number of connections loaded

    Example:
        >>> G = nx.Graph()
        >>> load_stations(G, 'data/processed/sncf/stations_clean.csv')
        >>> load_connections(G, 'data/processed/sncf/connections.csv')
        200
    """
    # Load connections data
    df = pd.read_csv(connections_file, encoding='utf-8')

    # Get UIC alias map (built by load_stations) for resolving alternative codes
    uic_alias_map = graph.graph.get('uic_alias_map', {})
    edges_added = 0

    for _, conn in df.iterrows():
        # Handle multiple UIC codes (semicolon-separated) - take first one
        origin_uic = str(conn['origin_uic']).split(';')[0].strip()
        dest_uic = str(conn['destination_uic']).split(';')[0].strip()

        # Resolve alternative UIC codes to primary node IDs
        origin_uic = uic_alias_map.get(origin_uic, origin_uic)
        dest_uic = uic_alias_map.get(dest_uic, dest_uic)

        # Only add edge if both nodes exist
        if origin_uic in graph.nodes() and dest_uic in graph.nodes():
            line_code = conn.get('line_code', 'TRAIN')
            duration = conn['duration_minutes']
            routing_cost = _compute_routing_cost(duration, line_code)
            graph.add_edge(
                origin_uic,
                dest_uic,
                weight=duration,
                routing_cost=routing_cost,
                distance_km=conn.get('distance_km', None),
                line_code=line_code
            )
            edges_added += 1

    return edges_added


# Routing cost penalties per line type
# multiplier: penalizes slower service types so Dijkstra prefers TGV
# hop_penalty: fixed cost per segment to discourage multi-hop detours
_ROUTING_PARAMS = {
    'TGV':     {'multiplier': 1.0, 'hop_penalty': 5},
    'IC':      {'multiplier': 1.05, 'hop_penalty': 8},
    'TER':     {'multiplier': 1.15, 'hop_penalty': 8},
    'TRAIN':   {'multiplier': 1.15, 'hop_penalty': 8},
    'CORRESP': {'multiplier': 1.0, 'hop_penalty': 15},
}


def _compute_routing_cost(duration: float, line_code: str) -> float:
    """Compute routing cost with penalties to prefer TGV and fewer hops."""
    params = _ROUTING_PARAMS.get(line_code, _ROUTING_PARAMS['TRAIN'])
    return duration * params['multiplier'] + params['hop_penalty']


# Intra-city transfer connections (metro/walk between stations)
CITY_TRANSFERS = {
    "paris": {
        "stations": [
            "87686006",   # Paris Gare de Lyon
            "87391003",   # Paris Montparnasse
            "87113001",   # Paris Est
            "87384008",   # Paris Saint-Lazare
            "87271023",   # Paris Gare du Nord
            "87547026",   # Paris Austerlitz
            "87686667",   # Paris Bercy
        ],
        "duration": 30,
    },
    "lyon": {
        "stations": ["87723197", "87722025"],  # Part Dieu ↔ Perrache
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


def add_transfer_edges(graph: nx.Graph) -> int:
    """
    Add intra-city transfer edges between major stations in the same city.

    These represent metro/taxi transfers (e.g., Paris Gare de Lyon ↔ Paris Saint-Lazare).

    Returns:
        Number of transfer edges added
    """
    transfers_added = 0
    for city, config in CITY_TRANSFERS.items():
        stations = [s for s in config["stations"] if s in graph.nodes()]
        duration = config["duration"]
        routing_cost = _compute_routing_cost(duration, "CORRESP")

        for i in range(len(stations)):
            for j in range(i + 1, len(stations)):
                if not graph.has_edge(stations[i], stations[j]):
                    graph.add_edge(
                        stations[i], stations[j],
                        weight=duration,
                        routing_cost=routing_cost,
                        line_code="CORRESP",
                        distance_km=None,
                    )
                    transfers_added += 1

    return transfers_added


def build_railway_graph(
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections_final_fixed.csv",
    subset: Optional[List[str]] = None
) -> nx.Graph:
    """
    Build complete railway network graph.

    Args:
        stations_file: Path to cleaned stations CSV
        connections_file: Path to connections CSV
        subset: Optional list of UIC codes for testing subset

    Returns:
        NetworkX Graph with stations and connections

    Example:
        >>> G = build_railway_graph()
        >>> print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    """
    G = nx.Graph()

    # Load stations (nodes)
    num_stations = load_stations(G, stations_file, subset)
    print(f"Loaded {num_stations} stations")

    # Load connections (edges)
    num_connections = load_connections(G, connections_file)
    print(f"Loaded {num_connections} connections")

    # Add intra-city transfer edges (metro between Paris stations, etc.)
    num_transfers = add_transfer_edges(G)
    print(f"Added {num_transfers} transfer edges")

    return G


def validate_graph(graph: nx.Graph) -> dict:
    """
    Validate graph structure and connectivity.

    Args:
        graph: NetworkX graph to validate

    Returns:
        Dictionary with validation results

    Example:
        >>> G = build_railway_graph()
        >>> results = validate_graph(G)
        >>> print(results['is_connected'])
        True
    """
    results = {
        'num_nodes': graph.number_of_nodes(),
        'num_edges': graph.number_of_edges(),
        'is_connected': nx.is_connected(graph) if graph.number_of_nodes() > 0 else False,
        'num_components': nx.number_connected_components(graph),
        'orphaned_nodes': [],
        'avg_degree': 0,
        'diameter': None
    }

    # Find orphaned nodes (no connections)
    results['orphaned_nodes'] = [n for n in graph.nodes() if graph.degree(n) == 0]

    # Calculate average degree
    if graph.number_of_nodes() > 0:
        results['avg_degree'] = sum(dict(graph.degree()).values()) / graph.number_of_nodes()

    # Calculate diameter (if connected)
    if results['is_connected']:
        results['diameter'] = nx.diameter(graph)

    return results


def print_validation_results(results: dict):
    """
    Print validation results in readable format.

    Args:
        results: Validation results dictionary from validate_graph()
    """
    print("=" * 70)
    print("GRAPH VALIDATION RESULTS")
    print("=" * 70)
    print()

    print(f"Nodes: {results['num_nodes']}")
    print(f"Edges: {results['num_edges']}")
    print()

    # Connectivity
    if results['is_connected']:
        print("[OK] Graph is fully connected")
        print(f"Diameter: {results['diameter']} hops (max path length)")
    else:
        print(f"[WARNING] Graph has {results['num_components']} disconnected components")

    print()

    # Orphaned nodes
    if results['orphaned_nodes']:
        print(f"[WARNING] {len(results['orphaned_nodes'])} orphaned nodes (no connections)")
        if len(results['orphaned_nodes']) <= 10:
            print("Orphaned nodes:", results['orphaned_nodes'])
    else:
        print("[OK] No orphaned nodes")

    print()

    # Average degree
    print(f"Average degree: {results['avg_degree']:.2f} connections per station")
    print()


def get_station_info(graph: nx.Graph, uic_code: str) -> Optional[dict]:
    """
    Get information about a specific station.

    Args:
        graph: NetworkX graph
        uic_code: UIC code of station

    Returns:
        Dictionary with station info, or None if not found

    Example:
        >>> G = build_railway_graph()
        >>> info = get_station_info(G, '87686006')
        >>> print(info['station_name'])
        'Paris Gare de Lyon'
    """
    if uic_code not in graph.nodes():
        return None

    return dict(graph.nodes[uic_code])


def find_path(
    graph: nx.Graph,
    origin_uic: str,
    destination_uic: str
) -> Optional[Tuple[List[str], float]]:
    """
    Find shortest path between two stations.

    Args:
        graph: NetworkX graph
        origin_uic: Origin station UIC code
        destination_uic: Destination station UIC code

    Returns:
        Tuple of (path as list of UIC codes, total travel time in minutes)
        or None if no path exists

    Example:
        >>> G = build_railway_graph()
        >>> path, time = find_path(G, '87686006', '87722025')
        >>> print(f"Travel time: {time} minutes")
    """
    if origin_uic not in graph.nodes() or destination_uic not in graph.nodes():
        return None

    try:
        # Use routing_cost for pathfinding (includes hop penalties)
        path = nx.shortest_path(graph, origin_uic, destination_uic, weight='routing_cost')
        # Return real travel time (not routing cost)
        total_time = sum(
            graph[path[i]][path[i + 1]]['weight']
            for i in range(len(path) - 1)
        )

        return path, total_time
    except nx.NetworkXNoPath:
        return None


def get_station_neighbors(
    graph: nx.Graph,
    uic_code: str
) -> List[Tuple[str, str, float]]:
    """
    Get all directly connected stations (neighbors).

    Args:
        graph: NetworkX graph
        uic_code: UIC code of station

    Returns:
        List of tuples: (neighbor_uic, station_name, travel_time_minutes)

    Example:
        >>> G = build_railway_graph()
        >>> neighbors = get_station_neighbors(G, '87686006')
        >>> for uic, name, time in neighbors:
        ...     print(f"{name}: {time} min")
    """
    if uic_code not in graph.nodes():
        return []

    neighbors = []
    for neighbor_uic in graph.neighbors(uic_code):
        station_name = graph.nodes[neighbor_uic]['station_name']
        edge_data = graph.edges[uic_code, neighbor_uic]
        travel_time = edge_data['weight']

        neighbors.append((neighbor_uic, station_name, travel_time))

    # Sort by travel time
    neighbors.sort(key=lambda x: x[2])

    return neighbors


def export_graph_stats(graph: nx.Graph, output_file: str):
    """
    Export detailed graph statistics to text file.

    Args:
        graph: NetworkX graph
        output_file: Path to output statistics file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("RAILWAY NETWORK GRAPH STATISTICS\n")
        f.write("=" * 70 + "\n\n")

        # Basic stats
        f.write(f"Total stations (nodes): {graph.number_of_nodes()}\n")
        f.write(f"Total connections (edges): {graph.number_of_edges()}\n\n")

        # Connectivity
        if nx.is_connected(graph):
            f.write("[OK] Graph is fully connected\n")
            f.write(f"Diameter: {nx.diameter(graph)} hops\n")
        else:
            components = list(nx.connected_components(graph))
            f.write(f"[WARNING] {len(components)} disconnected components\n")
            f.write(f"Largest component: {len(max(components, key=len))} nodes\n")

        f.write("\n")

        # Degree distribution
        degrees = dict(graph.degree())
        avg_degree = sum(degrees.values()) / len(degrees)
        f.write(f"Average degree: {avg_degree:.2f}\n")
        f.write(f"Min degree: {min(degrees.values())}\n")
        f.write(f"Max degree: {max(degrees.values())}\n\n")

        # Top 10 most connected stations
        f.write("Top 10 most connected stations:\n")
        sorted_stations = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        for uic, degree in sorted_stations:
            station_name = graph.nodes[uic]['station_name']
            f.write(f"  {station_name}: {degree} connections\n")

        f.write("\n")
        f.write("=" * 70 + "\n")

    print(f"Statistics saved to: {output_file}")


def save_graph(
    graph: nx.Graph,
    path: str = "models/train_network.pkl"
) -> bool:
    """
    Save graph to disk using pickle for fast loading.

    This allows caching the built graph to avoid rebuilding from CSV files
    every time. Useful for production deployments and testing.

    Args:
        graph: NetworkX graph to save
        path: Path where to save the pickled graph (default: models/train_network.pkl)

    Returns:
        True if successful, False otherwise

    Example:
        >>> G = build_railway_graph()
        >>> save_graph(G, "models/train_network.pkl")
        Graph saved to: models/train_network.pkl (size: 2.5 MB)
        True

    Ticket: KAN-36 - Graph loader optimization
    """
    import pickle
    from pathlib import Path

    try:
        # Create parent directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save graph using pickle
        with open(path, 'wb') as f:
            pickle.dump(graph, f, protocol=pickle.HIGHEST_PROTOCOL)

        # Get file size for logging
        import os
        file_size = os.path.getsize(path) / (1024 * 1024)  # Convert to MB

        print(f"Graph saved to: {path} (size: {file_size:.1f} MB)")
        return True

    except Exception as e:
        print(f"Error saving graph: {e}")
        return False


def load_graph(path: str = "models/train_network.pkl") -> Optional[nx.Graph]:
    """
    Load graph from disk.

    Much faster than rebuilding from CSV files. Use this in production
    to avoid the ~2-3 second loading time from CSV.

    Args:
        path: Path to pickled graph file (default: models/train_network.pkl)

    Returns:
        NetworkX Graph if successful, None if file not found or error

    Example:
        >>> G = load_graph("models/train_network.pkl")
        >>> if G:
        ...     print(f"Graph loaded: {G.number_of_nodes()} stations")
        ... else:
        ...     print("Graph file not found, building from CSV...")
        ...     G = build_railway_graph()

    Ticket: KAN-36 - Graph loader optimization
    """
    import pickle
    from pathlib import Path

    if not Path(path).exists():
        print(f"Graph file not found: {path}")
        return None

    try:
        with open(path, 'rb') as f:
            graph = pickle.load(f)

        print(f"Graph loaded from: {path}")
        print(f"  Stations: {graph.number_of_nodes()}")
        print(f"  Connections: {graph.number_of_edges()}")

        return graph

    except Exception as e:
        print(f"Error loading graph: {e}")
        return None


def get_or_build_graph(
    cache_path: str = "models/train_network.pkl",
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections_final_fixed.csv",
    force_rebuild: bool = False
) -> nx.Graph:
    """
    Get cached graph or build from CSV if not available.

    This is the recommended way to get the graph in production.
    It will use the cached version if available, otherwise build
    from CSV and cache it for next time.

    Args:
        cache_path: Path to cached graph file
        stations_file: Path to stations CSV (used if rebuilding)
        connections_file: Path to connections CSV (used if rebuilding)
        force_rebuild: If True, ignore cache and rebuild from CSV

    Returns:
        NetworkX Graph

    Example:
        >>> # First call: builds from CSV and caches (~2-3 seconds)
        >>> G = get_or_build_graph()

        >>> # Subsequent calls: loads from cache (~0.1 seconds)
        >>> G = get_or_build_graph()

    Ticket: KAN-36 - Graph loader optimization
    """
    if not force_rebuild:
        # Try to load from cache
        graph = load_graph(cache_path)
        if graph is not None:
            return graph

        print("Cache miss, building graph from CSV files...")

    # Build from CSV
    print("Building graph from CSV files...")
    graph = build_railway_graph(stations_file, connections_file)

    # Save to cache
    print("Saving graph to cache...")
    save_graph(graph, cache_path)

    return graph


if __name__ == "__main__":
    # Example usage
    print("Loading railway network graph...")
    G = build_railway_graph()

    print()
    results = validate_graph(G)
    print_validation_results(results)
