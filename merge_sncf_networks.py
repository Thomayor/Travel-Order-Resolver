#!/usr/bin/env python3
"""
Merge SNCF networks: original connections.csv + GeoJSON extracted network.

This combines:
1. connections.csv: TGV longue distance (312 connections)
2. connections_complete.csv: Regional network from GeoJSON (1960 connections)
"""

import pandas as pd

print("=" * 70)
print("MERGING SNCF NETWORK SOURCES")
print("=" * 70)
print()

# Load both files
original = pd.read_csv('data/processed/sncf/connections.csv', encoding='utf-8')
geojson = pd.read_csv('data/processed/sncf/connections_complete.csv', encoding='utf-8')

print(f"Original connections.csv: {len(original)} connections")
print(f"GeoJSON extracted (connections_complete.csv): {len(geojson)} connections")
print()

# Combine both sources
merged = pd.concat([original, geojson], ignore_index=True)
print(f"Total before deduplication: {len(merged)} connections")

# Remove duplicates (keep the one with shortest distance/duration)
# Group by origin-destination pair and keep the best one
merged['connection_key'] = merged['origin_uic'] + '->' + merged['destination_uic']

# Sort by distance (shortest first) then drop duplicates keeping first
merged_sorted = merged.sort_values('distance_km')
merged_deduplicated = merged_sorted.drop_duplicates(subset='connection_key', keep='first')

# Drop the temporary column
merged_deduplicated = merged_deduplicated.drop('connection_key', axis=1)

print(f"Total after deduplication: {len(merged_deduplicated)} connections")
print()

# Save result
output_file = 'data/processed/sncf/connections_final.csv'
merged_deduplicated.to_csv(output_file, index=False, encoding='utf-8')

print(f"Final network saved to: {output_file}")
print()

# Statistics
print("=" * 70)
print("FINAL NETWORK STATISTICS")
print("=" * 70)
print()
print(f"Total connections: {len(merged_deduplicated)}")
print(f"Average distance: {merged_deduplicated['distance_km'].mean():.2f} km")
print(f"Min distance: {merged_deduplicated['distance_km'].min():.2f} km")
print(f"Max distance: {merged_deduplicated['distance_km'].max():.2f} km")
print()
print(f"Average duration: {merged_deduplicated['duration_minutes'].mean():.1f} minutes")
print(f"Min duration: {merged_deduplicated['duration_minutes'].min()} minutes")
print(f"Max duration: {merged_deduplicated['duration_minutes'].max()} minutes")
print()

# Unique stations
unique_origins = set(merged_deduplicated['origin_uic'])
unique_dests = set(merged_deduplicated['destination_uic'])
unique_stations = unique_origins | unique_dests
print(f"Stations with connections: {len(unique_stations)}")
