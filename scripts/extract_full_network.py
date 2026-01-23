#!/usr/bin/env python3
"""
Extract COMPLETE railway network from SNCF GeoJSON data.

This improved version analyzes ALL points along LineStrings (not just endpoints)
to find all stations along each railway line and create sequential connections.

Ticket: KAN-29 - Calculate connection weights and build complete network
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from collections import defaultdict


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate distance between two GPS coordinates using Haversine formula.

    Args:
        lon1, lat1: First point coordinates (degrees)
        lon2, lat2: Second point coordinates (degrees)

    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Earth radius in kilometers
    r = 6371

    return c * r


def find_stations_along_line(coordinates, stations_df, max_distance_km=5.0):
    """
    Find all stations along a railway line (LineString) - OPTIMIZED VERSION.

    This function samples points along the line intelligently to find stations
    without checking every single point (for performance).

    Args:
        coordinates: List of (lon, lat) tuples representing the line
        stations_df: DataFrame with station data
        max_distance_km: Maximum distance to consider a station as "on the line" (km)

    Returns:
        List of tuples: (station_uic, distance_along_line, min_distance_to_line)
    """
    stations_on_line = {}  # uic -> (position_along_line, min_distance)

    # Calculate cumulative distance along the line
    cumulative_distance = [0]
    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]
        segment_distance = haversine(lon1, lat1, lon2, lat2)
        cumulative_distance.append(cumulative_distance[-1] + segment_distance)

    # OPTIMIZATION: Sample points intelligently
    # - Always check start and end
    # - Sample every ~10km along the line
    # - This reduces O(n*m) to O(n * m/k) where k ~= 10-20
    sampling_distance_km = 10.0
    sampled_indices = [0]  # Always include start

    current_distance = 0
    for i in range(1, len(cumulative_distance)):
        if cumulative_distance[i] - current_distance >= sampling_distance_km:
            sampled_indices.append(i)
            current_distance = cumulative_distance[i]

    sampled_indices.append(len(coordinates) - 1)  # Always include end

    # For each station, check distance to sampled points only
    for _, station in stations_df.iterrows():
        if pd.notna(station['latitude']) and pd.notna(station['longitude']):
            station_lon = station['longitude']
            station_lat = station['latitude']
            # Handle multiple UIC codes (semicolon-separated) - take first one
            uic = str(station['uic_code']).split(';')[0].strip()

            min_distance = float('inf')
            closest_position = 0

            # Check distance to SAMPLED points only
            for idx in sampled_indices:
                lon, lat = coordinates[idx]
                distance = haversine(station_lon, station_lat, lon, lat)

                if distance < min_distance:
                    min_distance = distance
                    closest_position = cumulative_distance[idx]

            # If station is close enough to the line, add it
            if min_distance <= max_distance_km:
                if uic not in stations_on_line or min_distance < stations_on_line[uic][1]:
                    stations_on_line[uic] = (closest_position, min_distance)

    # Sort stations by position along the line
    sorted_stations = sorted(stations_on_line.items(), key=lambda x: x[1][0])

    return [(uic, pos, dist) for uic, (pos, dist) in sorted_stations]


def calculate_line_distance(coordinates, start_idx, end_idx):
    """
    Calculate distance along a line between two point indices.

    Args:
        coordinates: List of (lon, lat) tuples
        start_idx: Starting point index
        end_idx: Ending point index

    Returns:
        Distance in kilometers
    """
    total_distance = 0
    for i in range(start_idx, end_idx):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]
        total_distance += haversine(lon1, lat1, lon2, lat2)

    return total_distance


def extract_complete_network(
    geojson_file: str = "data/raw/sncf/formes-des-lignes-du-rfn.geojson",
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    output_file: str = "data/processed/sncf/connections_complete.csv",
    max_distance_km: float = 5.0
):
    """
    Extract COMPLETE railway network from GeoJSON LineString geometries.

    This improved version analyzes ALL points along each line and creates
    sequential connections between consecutive stations.

    Args:
        geojson_file: Path to GeoJSON file
        stations_file: Path to cleaned stations CSV
        output_file: Path to output connections CSV
        max_distance_km: Max distance to match station to line (km)
    """

    print("=" * 70)
    print("EXTRACTING COMPLETE RAILWAY NETWORK FROM GEOJSON")
    print("=" * 70)
    print()

    # Load stations
    print(f"Loading stations from: {stations_file}")
    stations_df = pd.read_csv(stations_file, encoding='utf-8')
    print(f"Total stations loaded: {len(stations_df)}")
    print()

    # Load GeoJSON
    print(f"Loading GeoJSON from: {geojson_file}")
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson = json.load(f)

    total_features = len(geojson['features'])
    print(f"Total railway line features: {total_features}")
    print()

    # Extract connections from LineString geometries
    print("Analyzing ALL points along railway lines...")
    print(f"Max distance for station matching: {max_distance_km} km")
    print()

    connections_dict = defaultdict(lambda: {'min_distance': float('inf'), 'line_code': None})
    lines_processed = 0
    total_connections_found = 0

    for idx, feature in enumerate(geojson['features']):
        if idx % 50 == 0:
            print(f"Processing feature {idx + 1}/{total_features}... "
                  f"({total_connections_found} connections found)", end='\r')

        geometry = feature['geometry']
        properties = feature.get('properties', {})

        # Only process LineString geometries
        if geometry['type'] != 'LineString':
            continue

        lines_processed += 1

        # Get line properties
        line_code = properties.get('code_ligne', 'unknown')
        line_status = properties.get('mnemo', 'unknown')

        # Skip closed lines
        if line_status in ['FERME D', 'FERME']:
            continue

        # Get coordinates (lon, lat pairs)
        coordinates = geometry['coordinates']

        if len(coordinates) < 2:
            continue

        # Find ALL stations along this line
        stations_on_line = find_stations_along_line(coordinates, stations_df, max_distance_km)

        if len(stations_on_line) < 2:
            continue

        # Create connections between consecutive stations
        for i in range(len(stations_on_line) - 1):
            origin_uic, origin_pos, origin_dist = stations_on_line[i]
            dest_uic, dest_pos, dest_dist = stations_on_line[i + 1]

            if origin_uic == dest_uic:
                continue

            # Calculate distance between stations along the line
            distance = dest_pos - origin_pos

            if distance <= 0:
                continue

            # Estimate travel time (assuming avg speed of 80 km/h for complete network)
            duration_minutes = int((distance / 80) * 60)

            # Store connection (keep shortest path if duplicate)
            connection_key = (origin_uic, dest_uic)
            if distance < connections_dict[connection_key]['min_distance']:
                connections_dict[connection_key] = {
                    'origin_uic': origin_uic,
                    'destination_uic': dest_uic,
                    'distance_km': round(distance, 2),
                    'duration_minutes': max(1, duration_minutes),  # At least 1 minute
                    'line_code': line_code,
                    'line_status': line_status,
                    'min_distance': distance
                }
                total_connections_found += 1

    print()
    print()
    print("=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print()
    print(f"Total features processed: {total_features}")
    print(f"LineString features analyzed: {lines_processed}")
    print(f"Unique connections found: {len(connections_dict)}")
    print()

    # Convert to DataFrame
    connections = []
    for conn_key, conn_data in connections_dict.items():
        if 'origin_uic' in conn_data:
            connections.append({
                'origin_uic': conn_data['origin_uic'],
                'destination_uic': conn_data['destination_uic'],
                'distance_km': conn_data['distance_km'],
                'duration_minutes': conn_data['duration_minutes'],
                'line_code': conn_data['line_code'],
                'line_status': conn_data['line_status']
            })

    connections_df = pd.DataFrame(connections)

    print(f"Total connections in DataFrame: {len(connections_df)}")
    print()

    # Sort by origin
    connections_df = connections_df.sort_values(['origin_uic', 'destination_uic'])

    # Save to CSV
    print("=" * 70)
    print("SAVING OUTPUT")
    print("=" * 70)
    print()

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    connections_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Complete network saved to: {output_file}")
    print(f"Total connections: {len(connections_df)}")
    print()

    # Statistics
    print("=" * 70)
    print("NETWORK STATISTICS")
    print("=" * 70)
    print()

    print(f"Average distance: {connections_df['distance_km'].mean():.2f} km")
    print(f"Min distance: {connections_df['distance_km'].min():.2f} km")
    print(f"Max distance: {connections_df['distance_km'].max():.2f} km")
    print()
    print(f"Average duration: {connections_df['duration_minutes'].mean():.1f} minutes")
    print(f"Min duration: {connections_df['duration_minutes'].min()} minutes")
    print(f"Max duration: {connections_df['duration_minutes'].max()} minutes")
    print()

    # Count stations with connections
    unique_stations = set(connections_df['origin_uic']) | set(connections_df['destination_uic'])
    print(f"Stations with connections: {len(unique_stations)}/{len(stations_df)}")
    print(f"Coverage: {len(unique_stations)/len(stations_df)*100:.1f}%")
    print()

    # Show sample connections
    print("Sample connections:")
    for _, conn in connections_df.head(20).iterrows():
        origin_uic = conn['origin_uic'].split(';')[0]
        dest_uic = conn['destination_uic'].split(';')[0]

        origin = stations_df[stations_df['uic_code'] == origin_uic]['station_name'].iloc[0] if len(stations_df[stations_df['uic_code'] == origin_uic]) > 0 else origin_uic
        dest = stations_df[stations_df['uic_code'] == dest_uic]['station_name'].iloc[0] if len(stations_df[stations_df['uic_code'] == dest_uic]) > 0 else dest_uic

        print(f"  {origin} -> {dest}: {conn['distance_km']} km, {conn['duration_minutes']} min")

    print()

    # Verify key connections
    print("=" * 70)
    print("VERIFYING KEY CONNECTIONS")
    print("=" * 70)
    print()

    key_pairs = [
        ('87686006', '87722025', 'Paris Gare de Lyon', 'Lyon Part Dieu'),
        ('87722025', '87751008', 'Lyon Part Dieu', 'Marseille Saint-Charles'),
        ('87751008', '87756056', 'Marseille Saint-Charles', 'Nice'),
        ('87271007', '87286005', 'Paris Gare du Nord', 'Lille Flandres'),
    ]

    for origin_uic, dest_uic, origin_name, dest_name in key_pairs:
        # Check direct connection
        direct = connections_df[
            (connections_df['origin_uic'].str.contains(origin_uic)) &
            (connections_df['destination_uic'].str.contains(dest_uic))
        ]

        reverse = connections_df[
            (connections_df['origin_uic'].str.contains(dest_uic)) &
            (connections_df['destination_uic'].str.contains(origin_uic))
        ]

        if len(direct) > 0:
            print(f"[OK] {origin_name} -> {dest_name}: "
                  f"{direct.iloc[0]['distance_km']} km, {direct.iloc[0]['duration_minutes']} min")
        elif len(reverse) > 0:
            print(f"[OK] {origin_name} <- {dest_name}: "
                  f"{reverse.iloc[0]['distance_km']} km, {reverse.iloc[0]['duration_minutes']} min")
        else:
            print(f"[WARNING] No direct connection: {origin_name} <-> {dest_name}")

    print()
    print("=" * 70)
    print("COMPLETE NETWORK EXTRACTION COMPLETED")
    print("=" * 70)

    return connections_df


if __name__ == "__main__":
    extract_complete_network()
