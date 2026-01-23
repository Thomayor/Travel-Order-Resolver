#!/usr/bin/env python3
"""
Build comprehensive city-to-station mapping for NLP and pathfinding.

This script processes cleaned SNCF station data and creates:
1. JSON mapping: city → list of stations
2. Cities CSV: city metadata (coordinates, primary station, etc.)

Ticket: KAN-27 - Create station-to-city mapping
"""

import pandas as pd
import json
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def build_city_mapping(
    input_file: str = "data/processed/sncf/stations_clean.csv",
    output_json: str = "data/processed/city_station_mapping.json",
    output_csv: str = "data/processed/cities.csv"
):
    """
    Build city-to-station mapping with metadata.

    Args:
        input_file: Path to cleaned stations CSV
        output_json: Path to output JSON mapping
        output_csv: Path to output cities CSV
    """

    print("=" * 70)
    print("BUILDING CITY-TO-STATION MAPPING")
    print("=" * 70)
    print()

    # Load cleaned station data
    print(f"Loading data from: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"Total stations loaded: {len(df)}")
    print()

    # ===================================================================
    # 1. BUILD JSON MAPPING: city → [stations]
    # ===================================================================

    print("Building city -> stations mapping...")

    # Group by normalized city name
    city_groups = df.groupby('city_name_normalized')

    # Create mapping dictionary
    city_mapping = {}
    for city_normalized, group in city_groups:
        if pd.notna(city_normalized):
            # Get list of station names (official names, not normalized)
            stations = group['station_name'].tolist()
            city_mapping[city_normalized] = stations

    print(f"Total cities mapped: {len(city_mapping)}")
    print()

    # Show examples
    print("Example mappings:")
    for i, (city, stations) in enumerate(list(city_mapping.items())[:5]):
        print(f"  {city}: {len(stations)} station(s)")
        if len(stations) <= 3:
            for station in stations:
                print(f"    - {station}")
        else:
            for station in stations[:2]:
                print(f"    - {station}")
            print(f"    ... and {len(stations) - 2} more")
    print()

    # ===================================================================
    # 2. BUILD CITIES CSV WITH METADATA
    # ===================================================================

    print("Building cities metadata...")

    cities_data = []

    for city_normalized, group in city_groups:
        if pd.notna(city_normalized):
            # Get original city name (first occurrence, should be consistent)
            city_name_original = group['city_name'].iloc[0]

            # Calculate centroid (average of all station coordinates)
            stations_with_coords = group.dropna(subset=['latitude', 'longitude'])

            if len(stations_with_coords) > 0:
                centroid_lat = stations_with_coords['latitude'].mean()
                centroid_lon = stations_with_coords['longitude'].mean()
            else:
                centroid_lat = None
                centroid_lon = None

            # Determine primary station
            # Strategy: use the first station alphabetically (or could use segment_drg = A)
            # Alternative: prefer stations with "Gare" in name or segment A
            primary_candidates = group[group['segment_drg'] == 'A']

            if len(primary_candidates) > 0:
                # Use first segment A station
                primary_station = primary_candidates.iloc[0]['station_name']
                primary_uic = primary_candidates.iloc[0]['uic_code']
            else:
                # Fallback: use first station alphabetically
                primary_station = group.sort_values('station_name').iloc[0]['station_name']
                primary_uic = group.sort_values('station_name').iloc[0]['uic_code']

            # Count stations
            station_count = len(group)

            # Get all station names (for reference)
            all_stations = group['station_name'].tolist()

            cities_data.append({
                'city_name': city_name_original,
                'city_name_normalized': city_normalized,
                'station_count': station_count,
                'primary_station': primary_station,
                'primary_uic_code': primary_uic,
                'centroid_latitude': centroid_lat,
                'centroid_longitude': centroid_lon,
                'all_stations': '; '.join(all_stations)  # Semicolon-separated list
            })

    cities_df = pd.DataFrame(cities_data)

    # Sort by station count (descending) then by city name
    cities_df = cities_df.sort_values(['station_count', 'city_name'], ascending=[False, True])

    print(f"Total cities with metadata: {len(cities_df)}")
    print()

    # ===================================================================
    # 3. SAVE OUTPUTS
    # ===================================================================

    print("=" * 70)
    print("SAVING OUTPUTS")
    print("=" * 70)
    print()

    # Save JSON mapping
    output_json_path = Path(output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(city_mapping, f, ensure_ascii=False, indent=2)

    print(f"JSON mapping saved to: {output_json}")
    print(f"Total cities: {len(city_mapping)}")
    print()

    # Save cities CSV
    output_csv_path = Path(output_csv)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    cities_df.to_csv(output_csv, index=False, encoding='utf-8')

    print(f"Cities CSV saved to: {output_csv}")
    print(f"Total cities: {len(cities_df)}")
    print()

    # ===================================================================
    # 4. STATISTICS
    # ===================================================================

    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print()

    # Multi-station cities
    multi_station_cities = cities_df[cities_df['station_count'] > 1]
    print(f"Cities with multiple stations: {len(multi_station_cities)}")
    print()

    # Top 10 cities by station count
    print("Top 10 cities by station count:")
    for idx, row in cities_df.head(10).iterrows():
        print(f"  {row['city_name']}: {row['station_count']} stations")
        print(f"    Primary: {row['primary_station']}")
        if row['centroid_latitude']:
            print(f"    Centroid: ({row['centroid_latitude']:.4f}, {row['centroid_longitude']:.4f})")
    print()

    # Cities without GPS coordinates
    cities_no_gps = cities_df[cities_df['centroid_latitude'].isna()]
    print(f"Cities without GPS coordinates: {len(cities_no_gps)}")
    if len(cities_no_gps) > 0:
        print("Examples:")
        for idx, row in cities_no_gps.head(5).iterrows():
            print(f"  {row['city_name']} ({row['station_count']} stations)")
    print()

    # ===================================================================
    # 5. VALIDATION
    # ===================================================================

    print("=" * 70)
    print("VALIDATION")
    print("=" * 70)
    print()

    # Check Paris
    if 'paris' in city_mapping:
        paris_stations = city_mapping['paris']
        print(f"[OK] Paris found: {len(paris_stations)} stations")
        for station in paris_stations:
            print(f"    - {station}")
    else:
        print("[ERROR] Paris not found in mapping!")
    print()

    # Check Lyon
    if 'lyon' in city_mapping:
        lyon_stations = city_mapping['lyon']
        print(f"[OK] Lyon found: {len(lyon_stations)} stations")
        for station in lyon_stations:
            print(f"    - {station}")
    else:
        print("[ERROR] Lyon not found in mapping!")
    print()

    print("=" * 70)
    print("CITY MAPPING COMPLETED SUCCESSFULLY")
    print("=" * 70)

    return city_mapping, cities_df


if __name__ == "__main__":
    build_city_mapping()
