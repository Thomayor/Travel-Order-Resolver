#!/usr/bin/env python3
"""
Demo script for Railway Network Graph

This script demonstrates loading and querying the SNCF railway network graph.

Ticket: KAN-28 - Build graph database schema
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.pathfinding.graph_loader import (
    build_railway_graph,
    validate_graph,
    print_validation_results,
    get_station_info,
    find_path,
    get_station_neighbors
)


def main():
    print("=" * 70)
    print("SNCF RAILWAY NETWORK GRAPH - DEMO")
    print("=" * 70)
    print()

    # Build graph
    print("Loading railway network graph...")
    G = build_railway_graph()
    print()

    # Validate graph
    print("=" * 70)
    print("VALIDATION")
    print("=" * 70)
    print()
    results = validate_graph(G)
    print_validation_results(results)

    # Test queries
    print("=" * 70)
    print("SAMPLE QUERIES")
    print("=" * 70)
    print()

    # Query 1: Get station info
    print("Query 1: Station Information")
    print("-" * 70)
    test_uics = ['87686006', '87722025', '87751008']  # Paris Gare de Lyon, Lyon Part Dieu, Marseille

    for uic in test_uics:
        info = get_station_info(G, uic)
        if info:
            print(f"\nStation: {info['station_name']}")
            print(f"  City: {info['city_name']}")
            print(f"  UIC: {info['uic_code']}")
            if info['latitude']:
                print(f"  GPS: ({info['latitude']:.4f}, {info['longitude']:.4f})")
            print(f"  Segment: {info['segment_drg']}")
            print(f"  Connections: {G.degree(uic)}")
        else:
            print(f"\nStation {uic}: Not found in graph")

    # Query 2: Find neighbors
    print()
    print()
    print("Query 2: Direct Connections from Paris Gare de Lyon")
    print("-" * 70)
    neighbors = get_station_neighbors(G, '87686006')
    if neighbors:
        print(f"\nParis Gare de Lyon has {len(neighbors)} direct connections:")
        for uic, name, time in neighbors[:10]:  # Show first 10
            print(f"  -> {name}: {time} min")
        if len(neighbors) > 10:
            print(f"  ... and {len(neighbors) - 10} more")
    else:
        print("No connections found")

    # Query 3: Find path
    print()
    print()
    print("Query 3: Pathfinding Examples")
    print("-" * 70)

    # Test some paths
    test_paths = [
        ('87686006', '87722025', 'Paris Gare de Lyon', 'Lyon Part Dieu'),
        ('87271007', '87751008', 'Paris Gare du Nord', 'Marseille Saint-Charles'),
        ('87686006', '87751008', 'Paris Gare de Lyon', 'Marseille Saint-Charles')
    ]

    for origin_uic, dest_uic, origin_name, dest_name in test_paths:
        print(f"\n{origin_name} -> {dest_name}:")

        result = find_path(G, origin_uic, dest_uic)

        if result:
            path, total_time = result
            print(f"  Travel time: {total_time:.0f} minutes ({total_time/60:.1f} hours)")
            print(f"  Stops: {len(path) - 1} intermediate stations")
            print(f"  Route:")
            for i, uic in enumerate(path):
                station = get_station_info(G, uic)
                if i == 0:
                    print(f"    1. {station['station_name']} (departure)")
                elif i == len(path) - 1:
                    print(f"    {i+1}. {station['station_name']} (arrival)")
                else:
                    print(f"    {i+1}. {station['station_name']}")
        else:
            print("  No path found (stations not connected)")

    print()
    print("=" * 70)
    print("DEMO COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
