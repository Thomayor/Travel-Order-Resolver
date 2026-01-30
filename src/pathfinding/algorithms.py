"""
Pathfinding Algorithms for SNCF Railway Network

This module implements shortest path algorithms for train route planning.
Uses NetworkX's optimized Dijkstra implementation for performance.

Ticket: KAN-35 - Implement Dijkstra's algorithm for pathfinding
"""

import networkx as nx
from typing import List, Dict, Optional, Tuple
from .graph_loader import build_railway_graph, get_station_info


class PathfindingError(Exception):
    """Base exception for pathfinding errors."""
    pass


class InvalidStationError(PathfindingError):
    """Raised when station code is invalid or not in graph."""
    pass


class NoPathError(PathfindingError):
    """Raised when no path exists between stations."""
    pass


def dijkstra(
    graph: nx.Graph,
    origin: str,
    destination: str,
    weight: str = 'weight'
) -> Tuple[List[str], float]:
    """
    Find shortest path using Dijkstra's algorithm.

    This function uses NetworkX's optimized Dijkstra implementation,
    which is based on priority queues for O((V+E) log V) complexity.

    Algorithm explanation:
    1. Start at origin with distance 0
    2. Maintain priority queue of (distance, station) pairs
    3. Always process closest unvisited station
    4. Update distances to neighbors if shorter path found
    5. Continue until destination reached or all nodes processed

    Args:
        graph: NetworkX graph with railway network
        origin: Origin station UIC code
        destination: Destination station UIC code
        weight: Edge attribute to use as weight (default: 'weight')

    Returns:
        Tuple of (path as list of UIC codes, total travel time in minutes)

    Raises:
        InvalidStationError: If origin or destination not in graph
        NoPathError: If no path exists between stations

    Example:
        >>> G = build_railway_graph()
        >>> path, time = dijkstra(G, '87686006', '87723197')
        >>> print(f"Path: {path}, Time: {time} minutes")
        Path: ['87686006', '87723197'], Time: 117 minutes
    """
    # Validate stations exist
    if origin not in graph.nodes():
        raise InvalidStationError(f"Origin station '{origin}' not found in graph")

    if destination not in graph.nodes():
        raise InvalidStationError(f"Destination station '{destination}' not found in graph")

    # Same station
    if origin == destination:
        return [origin], 0.0

    # Find shortest path using Dijkstra (NetworkX implementation)
    try:
        path = nx.shortest_path(graph, origin, destination, weight=weight)
        total_time = nx.shortest_path_length(graph, origin, destination, weight=weight)

        return path, total_time

    except nx.NetworkXNoPath:
        origin_info = get_station_info(graph, origin)
        dest_info = get_station_info(graph, destination)
        origin_name = origin_info['station_name'] if origin_info else origin
        dest_name = dest_info['station_name'] if dest_info else destination

        raise NoPathError(
            f"No path exists between {origin_name} ({origin}) "
            f"and {dest_name} ({destination}). "
            f"Stations may be in disconnected network components."
        )


def find_route(
    origin: str,
    destination: str,
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections_final_fixed.csv"
) -> Dict:
    """
    Find route between two stations with detailed information.

    This is a high-level wrapper around dijkstra() that returns
    a dictionary with all route information including station names.

    Args:
        origin: Origin station UIC code
        destination: Destination station UIC code
        stations_file: Path to stations CSV (optional)
        connections_file: Path to connections CSV (optional)

    Returns:
        Dictionary with route information:
        {
            'success': bool,              # True if route found
            'origin': str,                # Origin UIC code
            'destination': str,           # Destination UIC code
            'origin_name': str,           # Origin station name
            'destination_name': str,      # Destination station name
            'path': List[str],            # List of UIC codes
            'stations': List[str],        # List of station names
            'total_time': float,          # Total travel time (minutes)
            'num_stops': int,             # Number of intermediate stops
            'error': Optional[str]        # Error message if failed
        }

    Example:
        >>> result = find_route('87686006', '87723197')
        >>> if result['success']:
        ...     print(f"Route: {' → '.join(result['stations'])}")
        ...     print(f"Time: {result['total_time']} minutes")
    """
    result = {
        'success': False,
        'origin': origin,
        'destination': destination,
        'origin_name': None,
        'destination_name': None,
        'path': [],
        'stations': [],
        'total_time': 0.0,
        'num_stops': 0,
        'error': None
    }

    try:
        # Build graph (this is cached in practice)
        graph = build_railway_graph(stations_file, connections_file)

        # Get station names
        origin_info = get_station_info(graph, origin)
        dest_info = get_station_info(graph, destination)

        if origin_info:
            result['origin_name'] = origin_info['station_name']
        if dest_info:
            result['destination_name'] = dest_info['station_name']

        # Find path
        path, total_time = dijkstra(graph, origin, destination)

        # Get station names for path
        stations = []
        for uic in path:
            info = get_station_info(graph, uic)
            stations.append(info['station_name'] if info else uic)

        # Update result
        result['success'] = True
        result['path'] = path
        result['stations'] = stations
        result['total_time'] = total_time
        result['num_stops'] = len(path) - 2  # Exclude origin and destination

    except InvalidStationError as e:
        result['error'] = str(e)

    except NoPathError as e:
        result['error'] = str(e)

    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def calculate_total_time(
    route: List[str],
    graph: Optional[nx.Graph] = None,
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections_final_fixed.csv"
) -> int:
    """
    Calculate total travel time for a given route.

    Args:
        route: List of station UIC codes representing the route
        graph: Pre-built NetworkX graph (optional, will build if not provided)
        stations_file: Path to stations CSV (used if graph not provided)
        connections_file: Path to connections CSV (used if graph not provided)

    Returns:
        Total travel time in minutes (rounded to int)

    Raises:
        ValueError: If route has less than 2 stations
        InvalidStationError: If any station in route not found
        NoPathError: If consecutive stations are not connected

    Example:
        >>> route = ['87686006', '87723197']  # Paris -> Lyon
        >>> time = calculate_total_time(route)
        >>> print(f"Total time: {time} minutes")
        Total time: 117 minutes
    """
    if len(route) < 2:
        raise ValueError("Route must contain at least 2 stations")

    # Build graph if not provided
    if graph is None:
        graph = build_railway_graph(stations_file, connections_file)

    # Validate all stations exist
    for uic in route:
        if uic not in graph.nodes():
            raise InvalidStationError(f"Station '{uic}' not found in graph")

    # Calculate total time by summing edge weights
    total_time = 0.0

    for i in range(len(route) - 1):
        origin = route[i]
        destination = route[i + 1]

        # Check if edge exists
        if not graph.has_edge(origin, destination):
            origin_name = get_station_info(graph, origin)['station_name']
            dest_name = get_station_info(graph, destination)['station_name']

            raise NoPathError(
                f"No direct connection between {origin_name} ({origin}) "
                f"and {dest_name} ({destination})"
            )

        # Add edge weight (travel time)
        edge_data = graph[origin][destination]
        total_time += edge_data['weight']

    return int(total_time)


def get_route_details(
    route: List[str],
    graph: Optional[nx.Graph] = None,
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections_final_fixed.csv"
) -> List[Dict]:
    """
    Get detailed information for each segment of a route.

    Args:
        route: List of station UIC codes
        graph: Pre-built NetworkX graph (optional)
        stations_file: Path to stations CSV
        connections_file: Path to connections CSV

    Returns:
        List of dictionaries, one per segment:
        [
            {
                'from_uic': str,
                'to_uic': str,
                'from_name': str,
                'to_name': str,
                'duration': int,
                'distance_km': float
            },
            ...
        ]

    Example:
        >>> route = ['87686006', '87723197']
        >>> details = get_route_details(route)
        >>> for seg in details:
        ...     print(f"{seg['from_name']} → {seg['to_name']}: {seg['duration']} min")
    """
    if len(route) < 2:
        return []

    # Build graph if not provided
    if graph is None:
        graph = build_railway_graph(stations_file, connections_file)

    segments = []

    for i in range(len(route) - 1):
        from_uic = route[i]
        to_uic = route[i + 1]

        from_info = get_station_info(graph, from_uic)
        to_info = get_station_info(graph, to_uic)

        edge_data = graph[from_uic][to_uic]

        segment = {
            'from_uic': from_uic,
            'to_uic': to_uic,
            'from_name': from_info['station_name'] if from_info else from_uic,
            'to_name': to_info['station_name'] if to_info else to_uic,
            'duration': int(edge_data['weight']),
            'distance_km': edge_data.get('distance_km', None)
        }

        segments.append(segment)

    return segments


# Convenience function for quick testing
def find_shortest_path(origin: str, destination: str) -> Optional[Tuple[List[str], float]]:
    """
    Quick shortcut to find path without error handling.

    Returns:
        (path, time) or None if failed

    Example:
        >>> result = find_shortest_path('87686006', '87723197')
        >>> if result:
        ...     path, time = result
        ...     print(f"Found path in {time} minutes")
    """
    try:
        graph = build_railway_graph()
        return dijkstra(graph, origin, destination)
    except (InvalidStationError, NoPathError):
        return None


if __name__ == "__main__":
    # Demo usage
    print("=" * 70)
    print("PATHFINDING ALGORITHMS DEMO")
    print("=" * 70)
    print()

    # Test 1: Paris -> Lyon
    print("Test 1: Paris Gare de Lyon → Lyon Part Dieu")
    result = find_route('87686006', '87723197')

    if result['success']:
        print(f"  ✓ Route found!")
        print(f"  Stations: {' → '.join(result['stations'])}")
        print(f"  Total time: {result['total_time']} minutes ({result['total_time']/60:.1f}h)")
        print(f"  Intermediate stops: {result['num_stops']}")
    else:
        print(f"  ✗ Error: {result['error']}")

    print()

    # Test 2: Invalid station
    print("Test 2: Invalid station code")
    result = find_route('99999999', '87723197')
    print(f"  Error (expected): {result['error']}")
    print()

    # Test 3: Route details
    print("Test 3: Route details Paris → Lyon")
    graph = build_railway_graph()
    path, _ = dijkstra(graph, '87686006', '87723197')
    details = get_route_details(path, graph)

    for i, seg in enumerate(details, 1):
        print(f"  Segment {i}: {seg['from_name']} → {seg['to_name']}")
        print(f"    Duration: {seg['duration']} min, Distance: {seg['distance_km']} km")

    print()
    print("=" * 70)
