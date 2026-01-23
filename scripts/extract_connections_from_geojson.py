#!/usr/bin/env python3
"""
Extract railway connections from SNCF GeoJSON data.

This script processes the formes-des-lignes-du-rfn.geojson file to extract
real railway connections between stations.

Ticket: KAN-28 - Build graph database schema
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from math import radians, cos, sin, asin, sqrt


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


def find_nearest_station(lon, lat, stations_df, max_distance_km=2.0):
    """
    Find the nearest station to given coordinates.

    Args:
        lon, lat: GPS coordinates
        stations_df: DataFrame with station data
        max_distance_km: Maximum distance to consider (km)

    Returns:
        UIC code of nearest station, or None if no station within max_distance
    """
    min_distance = float('inf')
    nearest_uic = None

    for _, station in stations_df.iterrows():
        if pd.notna(station['latitude']) and pd.notna(station['longitude']):
            distance = haversine(lon, lat, station['longitude'], station['latitude'])

            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest_uic = station['uic_code']

    return nearest_uic, min_distance if nearest_uic else None


def extract_connections(
    geojson_file: str = "data/raw/sncf/formes-des-lignes-du-rfn.geojson",
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    output_file: str = "data/processed/sncf/connections.csv",
    max_distance_km: float = 2.0
):
    """
    Extract railway connections from GeoJSON LineString geometries.

    Args:
        geojson_file: Path to GeoJSON file
        stations_file: Path to cleaned stations CSV
        output_file: Path to output connections CSV
        max_distance_km: Max distance to match station to line endpoint (km)
    """

    print("=" * 70)
    print("EXTRACTING RAILWAY CONNECTIONS FROM GEOJSON")
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
    print("Extracting connections from LineString geometries...")
    print(f"Max distance for station matching: {max_distance_km} km")
    print()

    connections = []
    lines_processed = 0
    connections_found = 0

    for idx, feature in enumerate(geojson['features']):
        if idx % 100 == 0:
            print(f"Processing feature {idx + 1}/{total_features}...", end='\r')

        geometry = feature['geometry']
        properties = feature.get('properties', {})

        # Only process LineString geometries
        if geometry['type'] != 'LineString':
            continue

        lines_processed += 1

        # Get line properties
        line_code = properties.get('code_ligne', 'unknown')
        line_status = properties.get('mnemo', 'unknown')

        # Skip closed lines if desired
        if line_status in ['FERME D', 'FERME']:
            continue

        # Get coordinates (lon, lat pairs)
        coordinates = geometry['coordinates']

        if len(coordinates) < 2:
            continue

        # Get start and end points
        start_lon, start_lat = coordinates[0]
        end_lon, end_lat = coordinates[-1]

        # Find nearest stations to start and end points
        start_station, start_dist = find_nearest_station(start_lon, start_lat, stations_df, max_distance_km)
        end_station, end_dist = find_nearest_station(end_lon, end_lat, stations_df, max_distance_km)

        # If both endpoints match stations, create connection
        if start_station and end_station and start_station != end_station:
            # Calculate distance along the line
            total_distance = 0
            for i in range(len(coordinates) - 1):
                lon1, lat1 = coordinates[i]
                lon2, lat2 = coordinates[i + 1]
                total_distance += haversine(lon1, lat1, lon2, lat2)

            # Estimate travel time (assuming avg speed of 100 km/h)
            duration_minutes = int((total_distance / 100) * 60)

            connections.append({
                'origin_uic': start_station,
                'destination_uic': end_station,
                'distance_km': round(total_distance, 2),
                'duration_minutes': duration_minutes,
                'line_code': line_code,
                'line_status': line_status
            })

            connections_found += 1

    print()
    print()
    print("=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print()
    print(f"Total features processed: {total_features}")
    print(f"LineString features: {lines_processed}")
    print(f"Connections found: {connections_found}")
    print()

    # Create DataFrame
    connections_df = pd.DataFrame(connections)

    # Remove duplicates (same connection from different lines)
    print("Removing duplicate connections...")
    before_dedup = len(connections_df)
    connections_df = connections_df.drop_duplicates(subset=['origin_uic', 'destination_uic'])
    after_dedup = len(connections_df)
    print(f"Removed {before_dedup - after_dedup} duplicates")
    print(f"Unique connections: {after_dedup}")
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
    print(f"Connections saved to: {output_file}")
    print(f"Total connections: {len(connections_df)}")
    print()

    # Statistics
    print("=" * 70)
    print("CONNECTION STATISTICS")
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

    # Show sample connections
    print("Sample connections:")
    for _, conn in connections_df.head(10).iterrows():
        origin = stations_df[stations_df['uic_code'] == conn['origin_uic']]['station_name'].iloc[0]
        dest = stations_df[stations_df['uic_code'] == conn['destination_uic']]['station_name'].iloc[0]
        print(f"  {origin} -> {dest}: {conn['distance_km']} km, {conn['duration_minutes']} min")

    print()
    print("=" * 70)
    print("CONNECTION EXTRACTION COMPLETED")
    print("=" * 70)

    return connections_df


if __name__ == "__main__":
    extract_connections()
