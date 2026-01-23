#!/usr/bin/env python3
"""
Merge railway network from multiple sources.

Combines:
1. GeoJSON regional network (connections_complete.csv) - 1960 connections
2. GTFS TGV connections (connections_tgv.csv) - 627 connections

Output: Complete unified network for pathfinding

Ticket: KAN-29 - Complete railway network
"""

import pandas as pd
from math import radians, cos, sin, asin, sqrt


def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two GPS coordinates using Haversine formula."""
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


def merge_network_sources(
    geojson_file: str = "data/processed/sncf/connections_complete.csv",
    tgv_file: str = "data/processed/sncf/connections_tgv.csv",
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    output_file: str = "data/processed/sncf/connections_final.csv"
):
    """
    Merge network sources into a single connections file.

    Args:
        geojson_file: GeoJSON-extracted regional connections
        tgv_file: GTFS-extracted TGV connections
        stations_file: Cleaned stations with GPS coordinates
        output_file: Output unified connections file
    """

    print("=" * 70)
    print("MERGING RAILWAY NETWORK SOURCES")
    print("=" * 70)
    print()

    # Load stations (for GPS coordinates and distance calculation)
    print(f"Loading stations from: {stations_file}")
    stations_df = pd.read_csv(stations_file, encoding='utf-8')
    print(f"Loaded {len(stations_df)} stations")
    print()

    # Create UIC -> GPS mapping
    uic_to_gps = {}
    for _, station in stations_df.iterrows():
        uic_codes = str(station['uic_code']).split(';')
        for uic in uic_codes:
            uic = uic.strip()
            if pd.notna(station['latitude']) and pd.notna(station['longitude']):
                uic_to_gps[uic] = (station['longitude'], station['latitude'])

    # Load GeoJSON regional network
    print(f"Loading GeoJSON regional network from: {geojson_file}")
    geojson_connections = pd.read_csv(geojson_file, encoding='utf-8')
    print(f"Loaded {len(geojson_connections)} regional connections")
    print()

    # Load GTFS TGV connections
    print(f"Loading GTFS TGV connections from: {tgv_file}")
    tgv_connections = pd.read_csv(tgv_file, encoding='utf-8')
    print(f"Loaded {len(tgv_connections)} TGV connections")
    print()

    # Standardize TGV connections format to match GeoJSON
    print("Processing TGV connections with real GTFS durations...")

    tgv_standardized = []
    for _, conn in tgv_connections.iterrows():
        origin_uic = str(conn['origin_uic']).strip()
        dest_uic = str(conn['destination_uic']).strip()

        # Use real duration from GTFS if available, otherwise calculate from GPS
        if pd.notna(conn.get('duration_minutes')):
            duration_minutes = int(conn['duration_minutes'])
        else:
            # Fallback: estimate from GPS distance
            if origin_uic in uic_to_gps and dest_uic in uic_to_gps:
                origin_gps = uic_to_gps[origin_uic]
                dest_gps = uic_to_gps[dest_uic]
                distance_km = haversine(origin_gps[0], origin_gps[1], dest_gps[0], dest_gps[1])
                duration_minutes = int((distance_km / 150) * 60)  # 150 km/h average
            else:
                continue  # Skip if no GPS and no duration

        # Calculate distance using GPS coordinates
        if origin_uic in uic_to_gps and dest_uic in uic_to_gps:
            origin_gps = uic_to_gps[origin_uic]
            dest_gps = uic_to_gps[dest_uic]
            distance_km = haversine(origin_gps[0], origin_gps[1], dest_gps[0], dest_gps[1])

            tgv_standardized.append({
                'origin_uic': origin_uic,
                'destination_uic': dest_uic,
                'distance_km': round(distance_km, 2),
                'duration_minutes': max(1, duration_minutes),  # At least 1 minute
                'line_code': 'TGV',
                'line_status': 'TGV'
            })

    tgv_standardized_df = pd.DataFrame(tgv_standardized)
    print(f"Standardized {len(tgv_standardized_df)} TGV connections")
    print()

    # Merge both sources
    print("Merging connections...")
    merged = pd.concat([geojson_connections, tgv_standardized_df], ignore_index=True)
    print(f"Total before deduplication: {len(merged)} connections")
    print()

    # Remove duplicates - keep the one with shortest distance
    print("Removing duplicates (keeping shortest path)...")
    merged['connection_key'] = merged['origin_uic'].astype(str) + '->' + merged['destination_uic'].astype(str)
    merged_sorted = merged.sort_values('distance_km')
    merged_deduplicated = merged_sorted.drop_duplicates(subset='connection_key', keep='first')
    merged_deduplicated = merged_deduplicated.drop('connection_key', axis=1)

    print(f"Total after deduplication: {len(merged_deduplicated)} connections")
    print()

    # Save result
    merged_deduplicated.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Final network saved to: {output_file}")
    print()

    # Statistics
    print("=" * 70)
    print("FINAL NETWORK STATISTICS")
    print("=" * 70)
    print()
    print(f"Total connections: {len(merged_deduplicated)}")
    print(f"  - Regional (GeoJSON): {len(geojson_connections)}")
    print(f"  - TGV (GTFS): {len(tgv_standardized_df)}")
    print(f"  - Duplicates removed: {len(merged) - len(merged_deduplicated)}")
    print()
    print(f"Average distance: {merged_deduplicated['distance_km'].mean():.2f} km")
    print(f"Min distance: {merged_deduplicated['distance_km'].min():.2f} km")
    print(f"Max distance: {merged_deduplicated['distance_km'].max():.2f} km")
    print()
    print(f"Average duration: {merged_deduplicated['duration_minutes'].mean():.1f} minutes")
    print(f"Min duration: {merged_deduplicated['duration_minutes'].min()} minutes")
    print(f"Max duration: {merged_deduplicated['duration_minutes'].max()} minutes")
    print()

    # Show sample TGV connections
    print("Sample TGV long-distance connections:")
    tgv_only = merged_deduplicated[merged_deduplicated['line_code'] == 'TGV']
    tgv_sorted = tgv_only.sort_values('distance_km', ascending=False)

    for _, conn in tgv_sorted.head(10).iterrows():
        origin = stations_df[stations_df['uic_code'].str.contains(conn['origin_uic'], na=False)]
        dest = stations_df[stations_df['uic_code'].str.contains(conn['destination_uic'], na=False)]

        if len(origin) > 0 and len(dest) > 0:
            print(f"  {origin.iloc[0]['station_name']} -> {dest.iloc[0]['station_name']}: "
                  f"{conn['distance_km']} km, {conn['duration_minutes']} min")

    print()
    print("=" * 70)
    print("NETWORK MERGE COMPLETED")
    print("=" * 70)

    return merged_deduplicated


if __name__ == "__main__":
    merge_network_sources()
