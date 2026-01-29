#!/usr/bin/env python3
"""Analyze connected components in the network."""

import sys
import os
import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.pathfinding.graph_loader import build_railway_graph, get_station_info

# Load graph
G = build_railway_graph(
    stations_file="data/processed/sncf/stations_clean.csv",
    connections_file="data/processed/sncf/connections_complete.csv"
)

# Get connected components
components = list(nx.connected_components(G))
components_sorted = sorted(components, key=len, reverse=True)

print(f"Total components: {len(components)}")
print()

# Show top 10 largest components
print("Top 10 largest components:")
for i, component in enumerate(components_sorted[:10]):
    print(f"\n{i+1}. Component with {len(component)} stations:")

    # Show first 20 stations
    for j, uic in enumerate(list(component)[:20]):
        station = get_station_info(G, uic)
        print(f"   - {station['station_name']} ({station['city_name']})")

    if len(component) > 20:
        print(f"   ... and {len(component) - 20} more stations")

# Check which component contains major cities
print()
print("=" * 70)
print("MAJOR CITIES LOCATIONS")
print("=" * 70)
print()

major_cities = [
    ('87686006', 'Paris Gare de Lyon'),
    ('87271007', 'Paris Gare du Nord'),
    ('87723197', 'Lyon Part Dieu'),
    ('87751008', 'Marseille Saint-Charles'),
    ('87756056', 'Nice'),
    ('87286005', 'Lille Flandres'),
    ('87611004', 'Toulouse Matabiau'),
    ('87581009', 'Bordeaux Saint-Jean'),
]

for uic, name in major_cities:
    # Find which component contains this station
    for i, component in enumerate(components_sorted):
        if uic in component:
            print(f"{name}: Component #{i+1} ({len(component)} stations)")
            break
    else:
        print(f"{name}: NOT CONNECTED (orphan)")
