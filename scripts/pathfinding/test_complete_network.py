#!/usr/bin/env python3
"""
Test complete railway network with path finding.

This script tests the complete network extracted from GeoJSON to verify
that major cities are connected through multi-hop paths.

Ticket: KAN-29 - Build complete network
"""

import sys
import os
from pathlib import Path

# Add project root to path (2 levels up: pathfinding -> scripts -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pathfinding.graph_loader import (
    build_railway_graph,
    validate_graph,
    print_validation_results,
    find_path,
    get_station_info
)


def test_network():
    print("=" * 70)
    print("TESTING COMPLETE RAILWAY NETWORK")
    print("=" * 70)
    print()

    # Build graph with final merged network (regional + TGV)
    print("Loading complete railway network (regional + TGV)...")
    G = build_railway_graph(
        stations_file="data/processed/sncf/stations_clean.csv",
        connections_file="data/processed/sncf/connections_final.csv"
    )
    print()

    # Validate
    print("=" * 70)
    print("VALIDATION")
    print("=" * 70)
    print()
    results = validate_graph(G)
    print_validation_results(results)

    # Test key paths
    print("=" * 70)
    print("TESTING KEY PATHS")
    print("=" * 70)
    print()

    test_paths = [
        ('87686006', '87723197', 'Paris Gare de Lyon', 'Lyon Part Dieu'),
        ('87723197', '87751008', 'Lyon Part Dieu', 'Marseille Saint-Charles'),
        ('87751008', '87756056', 'Marseille Saint-Charles', 'Nice'),
        ('87686006', '87751008', 'Paris Gare de Lyon', 'Marseille Saint-Charles'),
        ('87686006', '87756056', 'Paris Gare de Lyon', 'Nice'),
        ('87271007', '87286005', 'Paris Gare du Nord', 'Lille Flandres'),
        ('87686006', '87611004', 'Paris Gare de Lyon', 'Toulouse Matabiau'),
        ('87686006', '87581009', 'Paris Gare de Lyon', 'Bordeaux Saint-Jean'),
    ]

    for origin_uic, dest_uic, origin_name, dest_name in test_paths:
        print(f"\n{origin_name} -> {dest_name}:")

        result = find_path(G, origin_uic, dest_uic)

        if result:
            path, total_time = result
            print(f"  [OK] Path found!")
            print(f"  Travel time: {total_time:.0f} minutes ({total_time/60:.1f} hours)")
            print(f"  Number of transfers: {len(path) - 1}")

            # Show full route (only if less than 20 stops)
            if len(path) <= 20:
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
                print(f"  Route (showing first 5 and last 5 of {len(path)} stops):")
                for i in range(min(5, len(path))):
                    station = get_station_info(G, path[i])
                    print(f"    {i+1}. {station['station_name']}")
                print(f"    ... ({len(path) - 10} intermediate stops)")
                for i in range(max(len(path) - 5, 5), len(path)):
                    station = get_station_info(G, path[i])
                    print(f"    {i+1}. {station['station_name']}")
        else:
            print(f"  [ERROR] No path found (stations not connected)")

    print()
    print("=" * 70)
    print("TESTING COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    test_network()
