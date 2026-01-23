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

    # Add each station as a node
    for _, station in df.iterrows():
        # Handle multiple UIC codes (semicolon-separated)
        uic_code = str(station['uic_code']).split(';')[0].strip()

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

    edges_added = 0

    for _, conn in df.iterrows():
        # Handle multiple UIC codes (semicolon-separated) - take first one
        origin_uic = str(conn['origin_uic']).split(';')[0].strip()
        dest_uic = str(conn['destination_uic']).split(';')[0].strip()

        # Only add edge if both nodes exist
        if origin_uic in graph.nodes() and dest_uic in graph.nodes():
            graph.add_edge(
                origin_uic,
                dest_uic,
                weight=conn['duration_minutes'],
                distance_km=conn.get('distance_km', None),
                line_code=conn.get('line_code', None)
            )
            edges_added += 1

    return edges_added


def build_railway_graph(
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections.csv",
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
        # Use Dijkstra's algorithm (NetworkX implementation)
        path = nx.shortest_path(graph, origin_uic, destination_uic, weight='weight')
        total_time = nx.shortest_path_length(graph, origin_uic, destination_uic, weight='weight')

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


if __name__ == "__main__":
    # Example usage
    print("Loading railway network graph...")
    G = build_railway_graph()

    print()
    results = validate_graph(G)
    print_validation_results(results)
