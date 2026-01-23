#!/usr/bin/env python3
"""
Comprehensive validation of SNCF data and graph structure.

This script performs extensive validation checks on the processed data:
- Data completeness (coordinates, weights, orphaned nodes)
- Data consistency (station names, bidirectional connections, coordinates)
- Graph connectivity (connected components, isolated stations)
- Sample queries (Paris-Lyon, Toulouse-Marseille, Paris stations)

Ticket: KAN-30 - Validate processed data and graph
"""

import sys
import os
import pandas as pd
import networkx as nx
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pathfinding.graph_loader import (
    build_railway_graph,
    validate_graph,
    find_path,
    get_station_info
)


class NetworkValidator:
    """Comprehensive validation of SNCF railway network data."""

    def __init__(
        self,
        stations_file="data/processed/sncf/stations_clean.csv",
        connections_file="data/processed/sncf/connections_bidirectional.csv"
    ):
        self.stations_file = stations_file
        self.connections_file = connections_file
        self.stations_df = None
        self.connections_df = None
        self.graph = None
        self.validation_results = {}

    def load_data(self):
        """Load stations and connections data."""
        print("Loading data...")
        self.stations_df = pd.read_csv(self.stations_file, encoding='utf-8')
        self.connections_df = pd.read_csv(self.connections_file, encoding='utf-8')
        self.graph = build_railway_graph(self.stations_file, self.connections_file)
        print(f"  Loaded {len(self.stations_df)} stations")
        print(f"  Loaded {len(self.connections_df)} connections")
        print(f"  Built graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        print()

    def validate_data_completeness(self):
        """Validate data completeness."""
        print("=" * 70)
        print("1. DATA COMPLETENESS VALIDATION")
        print("=" * 70)
        print()

        results = {}

        # Check stations have coordinates
        missing_coords = self.stations_df[
            self.stations_df['latitude'].isna() | self.stations_df['longitude'].isna()
        ]
        results['stations_without_coords'] = len(missing_coords)
        results['stations_with_coords'] = len(self.stations_df) - len(missing_coords)
        results['coords_coverage'] = (len(self.stations_df) - len(missing_coords)) / len(self.stations_df) * 100

        print(f"Stations with coordinates: {results['stations_with_coords']}/{len(self.stations_df)} "
              f"({results['coords_coverage']:.1f}%)")
        if len(missing_coords) > 0:
            print(f"  [WARNING] {len(missing_coords)} stations without coordinates")
            for _, station in missing_coords.head(5).iterrows():
                print(f"    - {station['station_name']} ({station['uic_code']})")
        print()

        # Check connections have weights (duration)
        missing_weights = self.connections_df[
            self.connections_df['duration_minutes'].isna() |
            (self.connections_df['duration_minutes'] <= 0)
        ]
        results['connections_without_weights'] = len(missing_weights)
        results['connections_with_weights'] = len(self.connections_df) - len(missing_weights)
        results['weights_coverage'] = (len(self.connections_df) - len(missing_weights)) / len(self.connections_df) * 100

        print(f"Connections with valid weights: {results['connections_with_weights']}/{len(self.connections_df)} "
              f"({results['weights_coverage']:.1f}%)")
        if len(missing_weights) > 0:
            print(f"  [WARNING] {len(missing_weights)} connections without valid weights")
        print()

        # Check orphaned nodes
        graph_results = validate_graph(self.graph)
        results['orphaned_nodes'] = len(graph_results['orphaned_nodes'])
        results['connected_nodes'] = graph_results['num_nodes'] - len(graph_results['orphaned_nodes'])

        print(f"Connected nodes: {results['connected_nodes']}/{graph_results['num_nodes']}")
        print(f"Orphaned nodes: {results['orphaned_nodes']}")
        if results['orphaned_nodes'] > 0:
            print(f"  [INFO] {results['orphaned_nodes']} stations without connections (expected for remote stations)")
            for uic in list(graph_results['orphaned_nodes'])[:5]:
                station = get_station_info(self.graph, uic)
                print(f"    - {station['station_name']} ({station['city_name']})")
        print()

        self.validation_results['completeness'] = results
        return results

    def validate_data_consistency(self):
        """Validate data consistency."""
        print("=" * 70)
        print("2. DATA CONSISTENCY VALIDATION")
        print("=" * 70)
        print()

        results = {}

        # Check bidirectional connections
        forward_connections = set(
            (str(row['origin_uic']), str(row['destination_uic']))
            for _, row in self.connections_df.iterrows()
        )
        bidirectional_count = 0
        unidirectional_count = 0

        for origin, dest in forward_connections:
            if (dest, origin) in forward_connections:
                bidirectional_count += 1
            else:
                unidirectional_count += 1

        # Divide by 2 because we count each bidirectional pair twice
        bidirectional_count //= 2

        results['bidirectional_connections'] = bidirectional_count
        results['unidirectional_connections'] = unidirectional_count
        results['total_unique_connections'] = bidirectional_count + unidirectional_count
        results['bidirectional_ratio'] = bidirectional_count / (bidirectional_count + unidirectional_count) * 100

        print(f"Bidirectional connections: {bidirectional_count}")
        print(f"Unidirectional connections: {unidirectional_count}")
        print(f"Bidirectional ratio: {results['bidirectional_ratio']:.1f}%")
        print()

        # Check coordinates are in France (roughly -5 to 10 longitude, 41 to 51 latitude)
        france_bounds = {
            'lon_min': -5.5, 'lon_max': 10.0,
            'lat_min': 41.0, 'lat_max': 51.5
        }

        outside_france = self.stations_df[
            (self.stations_df['longitude'] < france_bounds['lon_min']) |
            (self.stations_df['longitude'] > france_bounds['lon_max']) |
            (self.stations_df['latitude'] < france_bounds['lat_min']) |
            (self.stations_df['latitude'] > france_bounds['lat_max'])
        ]
        outside_france = outside_france[outside_france['longitude'].notna()]

        results['stations_in_france'] = len(self.stations_df) - len(outside_france)
        results['stations_outside_france'] = len(outside_france)

        print(f"Stations within France bounds: {results['stations_in_france']}/{len(self.stations_df)}")
        if len(outside_france) > 0:
            print(f"  [INFO] {len(outside_france)} stations outside France (border regions, international)")
            for _, station in outside_france.head(5).iterrows():
                print(f"    - {station['station_name']}: ({station['latitude']:.2f}, {station['longitude']:.2f})")
        print()

        # Check distance consistency (no impossible distances)
        impossible_distances = self.connections_df[self.connections_df['distance_km'] > 1000]
        results['impossible_distances'] = len(impossible_distances)

        print(f"Connections with reasonable distances (<1000 km): {len(self.connections_df) - len(impossible_distances)}/{len(self.connections_df)}")
        if len(impossible_distances) > 0:
            print(f"  [WARNING] {len(impossible_distances)} connections with distances >1000 km")
            for _, conn in impossible_distances.head(3).iterrows():
                print(f"    - {conn['origin_uic']} -> {conn['destination_uic']}: {conn['distance_km']} km")
        print()

        self.validation_results['consistency'] = results
        return results

    def validate_graph_connectivity(self):
        """Validate graph connectivity."""
        print("=" * 70)
        print("3. GRAPH CONNECTIVITY VALIDATION")
        print("=" * 70)
        print()

        results = {}

        # Get connected components
        components = list(nx.connected_components(self.graph))
        components_sorted = sorted(components, key=len, reverse=True)

        results['num_components'] = len(components)
        results['largest_component_size'] = len(components_sorted[0]) if components else 0
        results['connectivity_ratio'] = results['largest_component_size'] / self.graph.number_of_nodes() * 100

        print(f"Connected components: {results['num_components']}")
        print(f"Largest component: {results['largest_component_size']} stations ({results['connectivity_ratio']:.1f}%)")
        print()

        # Show component breakdown
        if len(components) > 1:
            print("Component size distribution:")
            component_sizes = [len(c) for c in components_sorted]
            for i, size in enumerate(component_sizes[:10]):
                print(f"  Component {i+1}: {size} stations")
            if len(components) > 10:
                print(f"  ... and {len(components) - 10} more components")
            print()

        # Check major cities are in largest component
        # NOTE: Use first UIC code for stations with multiple codes
        major_cities = {
            '87686006': 'Paris Gare de Lyon',
            '87271023': 'Paris Gare du Nord',  # First code from 87271023;87271007;87271031
            '87723197': 'Lyon Part Dieu',
            '87751008': 'Marseille Saint-Charles',
            '87286005': 'Lille Flandres',
            '87581009': 'Bordeaux Saint-Jean',
            '87611004': 'Toulouse Matabiau',
            '87212027': 'Strasbourg'
        }

        largest_component = components_sorted[0]
        results['major_cities_connected'] = 0
        results['major_cities_total'] = len(major_cities)

        print("Major cities connectivity:")
        for uic, name in major_cities.items():
            in_graph = uic in self.graph.nodes()
            in_largest = uic in largest_component if in_graph else False

            if in_largest:
                status = "[OK] Connected"
                results['major_cities_connected'] += 1
            elif in_graph:
                status = "[WARNING] In graph but isolated"
            else:
                status = "[ERROR] Not in graph"

            print(f"  {name}: {status}")

        print()

        self.validation_results['connectivity'] = results
        return results

    def run_sample_queries(self):
        """Run sample pathfinding queries."""
        print("=" * 70)
        print("4. SAMPLE QUERIES")
        print("=" * 70)
        print()

        results = {}

        # Query 1: Paris Gare de Lyon -> Lyon Part Dieu
        print("Query 1: Paris Gare de Lyon -> Lyon Part Dieu")
        result = find_path(self.graph, '87686006', '87723197')
        if result:
            path, duration = result
            print(f"  [OK] Path found: {len(path)} stations, {duration:.0f} minutes ({duration/60:.1f} hours)")
            results['paris_lyon'] = {'found': True, 'duration': duration, 'stops': len(path)}
        else:
            print(f"  [ERROR] No path found")
            results['paris_lyon'] = {'found': False}
        print()

        # Query 2: Toulouse -> Marseille
        print("Query 2: Toulouse Matabiau -> Marseille Saint-Charles")
        result = find_path(self.graph, '87611004', '87751008')
        if result:
            path, duration = result
            print(f"  [OK] Path found: {len(path)} stations, {duration:.0f} minutes ({duration/60:.1f} hours)")
            results['toulouse_marseille'] = {'found': True, 'duration': duration, 'stops': len(path)}
        else:
            print(f"  [ERROR] No path found")
            results['toulouse_marseille'] = {'found': False}
        print()

        # Query 3: List stations in Paris
        print("Query 3: All stations in Paris")
        paris_stations = self.stations_df[
            self.stations_df['city_name'].str.contains('Paris', case=False, na=False)
        ]
        results['paris_stations_count'] = len(paris_stations)

        print(f"  Found {len(paris_stations)} stations in Paris:")
        for _, station in paris_stations.head(10).iterrows():
            in_graph = str(station['uic_code']).split(';')[0] in self.graph.nodes()
            status = "connected" if in_graph else "not in graph"
            print(f"    - {station['station_name']} ({status})")
        if len(paris_stations) > 10:
            print(f"    ... and {len(paris_stations) - 10} more stations")
        print()

        self.validation_results['queries'] = results
        return results

    def generate_report(self):
        """Generate comprehensive validation report."""
        print("=" * 70)
        print("VALIDATION SUMMARY REPORT")
        print("=" * 70)
        print()

        # Overall status
        issues = []

        # Completeness checks
        comp = self.validation_results['completeness']
        if comp['coords_coverage'] < 95:
            issues.append(f"Only {comp['coords_coverage']:.1f}% stations have coordinates")
        if comp['weights_coverage'] < 95:
            issues.append(f"Only {comp['weights_coverage']:.1f}% connections have valid weights")

        # Consistency checks
        cons = self.validation_results['consistency']
        if cons['bidirectional_ratio'] < 50:
            issues.append(f"Only {cons['bidirectional_ratio']:.1f}% connections are bidirectional")
        if cons['impossible_distances'] > 0:
            issues.append(f"{cons['impossible_distances']} connections have impossible distances")

        # Connectivity checks
        conn = self.validation_results['connectivity']
        if conn['num_components'] > 100:
            issues.append(f"Network highly fragmented: {conn['num_components']} components")
        if conn['major_cities_connected'] < conn['major_cities_total']:
            issues.append(f"Only {conn['major_cities_connected']}/{conn['major_cities_total']} major cities connected")

        # Query checks
        queries = self.validation_results['queries']
        if not queries['paris_lyon']['found']:
            issues.append("Cannot find path Paris-Lyon")
        if not queries['toulouse_marseille']['found']:
            issues.append("Cannot find path Toulouse-Marseille")

        # Print report
        if len(issues) == 0:
            print("[SUCCESS] All validation checks passed!")
        else:
            print(f"[WARNING] Found {len(issues)} issues:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

        print()
        print("Key Metrics:")
        print(f"  - Stations: {len(self.stations_df)} total, {comp['connected_nodes']} connected")
        print(f"  - Connections: {len(self.connections_df)} total")
        print(f"  - Coverage: {comp['coords_coverage']:.1f}% coordinates, {comp['weights_coverage']:.1f}% weights")
        print(f"  - Connectivity: {conn['connectivity_ratio']:.1f}% in largest component")
        print(f"  - Major cities: {conn['major_cities_connected']}/{conn['major_cities_total']} connected")
        print()

        return len(issues) == 0

    def run_all_validations(self):
        """Run all validation checks."""
        print()
        print("=" * 70)
        print("SNCF RAILWAY NETWORK VALIDATION")
        print("=" * 70)
        print()

        self.load_data()
        self.validate_data_completeness()
        self.validate_data_consistency()
        self.validate_graph_connectivity()
        self.run_sample_queries()

        success = self.generate_report()

        print("=" * 70)
        print("VALIDATION COMPLETED")
        print("=" * 70)

        return success


if __name__ == "__main__":
    validator = NetworkValidator()
    success = validator.run_all_validations()

    sys.exit(0 if success else 1)
