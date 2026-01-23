#!/usr/bin/env python3
"""
Clean and normalize SNCF station names.

This script processes raw SNCF station data and creates a cleaned version
with normalized names suitable for NLP matching.

Ticket: KAN-26 - Clean and normalize SNCF station names
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.nlp.preprocessing import remove_accents, normalize_hyphens


def clean_station_names(input_file: str, output_file: str):
    """
    Clean and normalize SNCF station names.

    Args:
        input_file: Path to raw gares-sncf.csv
        output_file: Path to output stations_clean.csv
    """

    print("=" * 70)
    print("SNCF STATION NAME CLEANING")
    print("=" * 70)
    print()

    # Load raw data
    print(f"Loading data from: {input_file}")
    df = pd.read_csv(
        input_file,
        sep=';',  # CSV uses semicolon separator
        encoding='utf-8-sig',  # Handle BOM
        dtype=str  # Read all as strings to avoid issues
    )

    print(f"Total stations loaded: {len(df)}")
    print()
    print("Columns:", df.columns.tolist())
    print()

    # Rename columns for clarity
    df = df.rename(columns={
        'Nom': 'station_name',
        'Trigramme': 'trigramme',
        'Segment(s) DRG': 'segment_drg',
        'Position géographique': 'position',
        'Code commune': 'insee_code',
        'Code(s) UIC': 'uic_code'
    })

    # Extract latitude and longitude from position field
    print("Extracting GPS coordinates...")
    df[['latitude', 'longitude']] = df['position'].str.split(',', expand=True)
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    # Clean station names
    print("Cleaning station names...")

    # 1. Remove leading/trailing whitespace
    df['station_name_clean'] = df['station_name'].str.strip()

    # 2. Normalize hyphens (convert various dash types to standard hyphen)
    df['station_name_clean'] = df['station_name_clean'].apply(normalize_hyphens)

    # 3. Create normalized version (no accents, lowercase)
    df['station_name_normalized'] = df['station_name_clean'].apply(
        lambda x: remove_accents(x).lower()
    )

    # 4. Remove special characters (keep only alphanumeric, spaces, hyphens, apostrophes)
    df['station_name_normalized'] = df['station_name_normalized'].str.replace(
        r'[^a-z0-9\s\-\']', '', regex=True
    )

    # 5. Collapse multiple spaces
    df['station_name_normalized'] = df['station_name_normalized'].str.replace(
        r'\s+', ' ', regex=True
    ).str.strip()

    # 6. Create search-friendly version (no spaces, no hyphens)
    df['station_name_searchable'] = df['station_name_normalized'].str.replace(
        r'[\s\-\']', '', regex=True
    )

    # Extract city name from station name
    print("Extracting city names...")

    # List of major cities to detect at the beginning of station names
    major_cities = [
        'Paris', 'Lyon', 'Marseille', 'Lille', 'Bordeaux', 'Toulouse', 'Nice',
        'Nantes', 'Strasbourg', 'Montpellier', 'Rennes', 'Reims', 'Le Havre',
        'Saint-Étienne', 'Toulon', 'Grenoble', 'Dijon', 'Angers', 'Nîmes',
        'Villeurbanne', 'Le Mans', 'Aix-en-Provence', 'Clermont-Ferrand',
        'Brest', 'Tours', 'Amiens', 'Limoges', 'Annecy', 'Perpignan',
        'Boulogne-Billancourt', 'Metz', 'Besançon', 'Orléans', 'Saint-Denis',
        'Argenteuil', 'Rouen', 'Mulhouse', 'Montreuil', 'Caen', 'Nancy'
    ]

    def extract_city_name(station_name):
        """Extract city name from station name."""
        if pd.isna(station_name):
            return None

        # Check if station name starts with a major city
        for city in major_cities:
            if station_name.startswith(city + ' ') or station_name == city:
                return city

        # Fallback: split on " - " (space-dash-space separator)
        if ' - ' in station_name:
            return station_name.split(' - ')[0].strip()

        # Fallback: split on first dash (for compound names like Port-Boulet)
        if '-' in station_name:
            return station_name.split('-')[0].strip()

        # Fallback: return the full station name (single-word stations)
        return station_name

    df['city_name'] = df['station_name_clean'].apply(extract_city_name)
    df['city_name_normalized'] = df['city_name'].apply(
        lambda x: remove_accents(x).lower() if pd.notna(x) else None
    )

    # Quality checks
    print()
    print("=" * 70)
    print("QUALITY CHECKS")
    print("=" * 70)
    print()

    # Check for missing coordinates
    missing_coords = df[df['latitude'].isna() | df['longitude'].isna()]
    print(f"Stations with missing coordinates: {len(missing_coords)}")
    if len(missing_coords) > 0:
        print("Examples:")
        print(missing_coords[['station_name', 'position']].head())
        print()

    # Check for duplicates
    duplicates = df[df.duplicated(subset=['station_name_normalized'], keep=False)]
    print(f"Duplicate station names (normalized): {len(duplicates)}")
    if len(duplicates) > 0:
        print("Examples:")
        print(duplicates[['station_name', 'station_name_normalized']].head(10))
        print()

    # Statistics
    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print()
    print(f"Total stations processed: {len(df)}")
    print(f"Stations with GPS coordinates: {len(df[df['latitude'].notna()])}")
    print(f"Unique station names (original): {df['station_name'].nunique()}")
    print(f"Unique station names (normalized): {df['station_name_normalized'].nunique()}")
    print()

    # Example transformations
    print("=" * 70)
    print("EXAMPLE TRANSFORMATIONS")
    print("=" * 70)
    print()
    sample = df[['station_name', 'station_name_clean', 'station_name_normalized', 'city_name']].head(10)
    for idx, row in sample.iterrows():
        print(f"Original:   {row['station_name']}")
        print(f"Clean:      {row['station_name_clean']}")
        print(f"Normalized: {row['station_name_normalized']}")
        print(f"City:       {row['city_name']}")
        print()

    # Select columns for output
    output_df = df[[
        'station_name',           # Original name
        'station_name_clean',     # Cleaned (hyphens normalized, trimmed)
        'station_name_normalized', # No accents, lowercase
        'station_name_searchable', # No spaces/hyphens (for fuzzy matching)
        'city_name',              # Extracted city name
        'city_name_normalized',   # Normalized city name
        'trigramme',              # 3-letter code
        'uic_code',               # Unique identifier
        'insee_code',             # City code
        'latitude',               # GPS
        'longitude',              # GPS
        'segment_drg',            # DRG segment
        'position'                # Original position field
    ]].copy()

    # Save to CSV
    print("=" * 70)
    print("SAVING OUTPUT")
    print("=" * 70)
    print()

    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Cleaned data saved to: {output_file}")
    print(f"Total rows: {len(output_df)}")
    print()

    # Generate name mapping file (for quick lookups)
    name_mapping = df[['station_name_normalized', 'station_name', 'uic_code']].copy()
    name_mapping = name_mapping.drop_duplicates(subset=['station_name_normalized'])

    mapping_file = output_path.parent / 'station_name_mapping.csv'
    name_mapping.to_csv(mapping_file, index=False, encoding='utf-8')
    print(f"Name mapping saved to: {mapping_file}")
    print(f"Total mappings: {len(name_mapping)}")
    print()

    # Generate city mapping (city → list of stations)
    city_stations = df.groupby('city_name_normalized')['station_name'].apply(list).reset_index()
    city_stations.columns = ['city_normalized', 'stations']
    city_stations['station_count'] = city_stations['stations'].apply(len)
    city_stations = city_stations.sort_values('station_count', ascending=False)

    city_mapping_file = output_path.parent / 'city_station_mapping.csv'

    # Explode list for CSV format
    city_stations_exploded = df[['city_name_normalized', 'station_name', 'uic_code']].copy()
    city_stations_exploded = city_stations_exploded.drop_duplicates()
    city_stations_exploded = city_stations_exploded.sort_values(['city_name_normalized', 'station_name'])
    city_stations_exploded.to_csv(city_mapping_file, index=False, encoding='utf-8')

    print(f"City-station mapping saved to: {city_mapping_file}")
    print()

    # Show cities with multiple stations
    multi_station_cities = city_stations[city_stations['station_count'] > 1]
    print(f"Cities with multiple stations: {len(multi_station_cities)}")
    if len(multi_station_cities) > 0:
        print("\nTop 10 cities by station count:")
        for idx, row in multi_station_cities.head(10).iterrows():
            print(f"  {row['city_normalized']}: {row['station_count']} stations")
            for station in row['stations'][:3]:  # Show first 3
                print(f"    - {station}")
            if row['station_count'] > 3:
                print(f"    ... and {row['station_count'] - 3} more")

    print()
    print("=" * 70)
    print("CLEANING COMPLETED SUCCESSFULLY")
    print("=" * 70)

    return output_df


if __name__ == "__main__":
    # Paths
    input_file = "data/raw/sncf/gares-sncf.csv"
    output_file = "data/processed/sncf/stations_clean.csv"

    # Run cleaning
    clean_station_names(input_file, output_file)
