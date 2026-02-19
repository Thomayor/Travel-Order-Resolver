#!/usr/bin/env python3
"""
Generate stations_clean.csv from GTFS stops.txt

Extracts French railway stations (UIC codes starting with 87) from GTFS data
and creates the stations_clean.csv file with all necessary columns.

Output: data/processed/sncf/stations_clean.csv
  columns: uic_code, station_name, station_name_normalized, city_name,
           city_name_normalized, latitude, longitude, segment_drg

Usage:
    python scripts/generate_stations_from_gtfs.py
"""

import pandas as pd
import re
from pathlib import Path
import unicodedata

GTFS_DIR = Path("data/raw/sncf/gtfs")
OUT_FILE = Path("data/processed/sncf/stations_clean.csv")


def extract_uic(stop_id: str) -> str | None:
    """
    Extract 8-digit UIC code from GTFS stop_id.

    Examples:
        'StopPoint:OCENavette-87571240'  -> '87571240'
        'StopPoint:OCETGV INOUI-87756056' -> '87756056'
        'StopArea:OCE87571240'           -> '87571240'
    """
    m = re.search(r'(\d{8})$', stop_id)
    return m.group(1) if m else None


def normalize_name(name: str) -> str:
    """Normalize station/city name (lowercase, no accents)."""
    if pd.isna(name):
        return ''

    # Lowercase
    name = str(name).lower()

    # Remove accents
    nfkd_form = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

    # Remove special characters, keep letters, numbers, spaces, hyphens
    name = re.sub(r'[^\w\s-]', '', name)

    # Normalize spaces
    name = ' '.join(name.split())

    return name


def extract_city_from_station(station_name: str) -> str:
    """
    Extract city name from station name.

    Examples:
        'Paris Gare de Lyon' -> 'Paris'
        'Lyon Part Dieu' -> 'Lyon'
        'Avignon TGV' -> 'Avignon'
        'Aix-en-Provence' -> 'Aix-en-Provence'
    """
    if pd.isna(station_name):
        return ''

    station_name = str(station_name).strip()

    # Remove common station suffixes
    patterns = [
        r'\s+Gare de .*$',      # Paris Gare de Lyon -> Paris
        r'\s+Part Dieu$',       # Lyon Part Dieu -> Lyon
        r'\s+TGV$',             # Avignon TGV -> Avignon
        r'\s+Centre$',          # Toulouse Centre -> Toulouse
        r'\s+Saint[-\s].*$',    # Keep if city starts with Saint
    ]

    city = station_name
    for pattern in patterns:
        # Don't apply if city name itself starts with the pattern
        if not re.match(r'^(Saint|Sainte)', city, re.IGNORECASE):
            city = re.sub(pattern, '', city, flags=re.IGNORECASE)

    # Take first part before space (for multi-word stations)
    # BUT keep compound names with hyphens
    if '-' not in city:
        city = city.split()[0] if city.split() else city

    return city.strip()


def load_stops_from_gtfs(gtfs_dir: Path) -> pd.DataFrame:
    """
    Load and process stops.txt from GTFS.

    Returns DataFrame with French railway stations only.
    """
    print("Loading stops.txt...")
    stops = pd.read_csv(gtfs_dir / "stops.txt")

    print(f"  Total stops in GTFS: {len(stops):,}")

    # Extract UIC codes
    stops['uic_code'] = stops['stop_id'].apply(extract_uic)

    # Filter to French stations (UIC starting with 87)
    stops = stops[
        stops['uic_code'].notna() &
        stops['uic_code'].str.startswith('87')
    ].copy()

    print(f"  French stations (87xxxxxx): {len(stops):,}")

    # Remove duplicates (keep first occurrence)
    stops = stops.drop_duplicates(subset=['uic_code'])

    print(f"  After deduplication: {len(stops):,}")

    return stops


def build_stations_csv(stops: pd.DataFrame) -> pd.DataFrame:
    """
    Build stations_clean.csv format from GTFS stops.

    Columns:
    - uic_code: 8-digit UIC code
    - station_name: Original station name
    - station_name_normalized: Normalized for matching
    - city_name: Extracted city name
    - city_name_normalized: Normalized city name
    - latitude: GPS latitude
    - longitude: GPS longitude
    - segment_drg: Placeholder (not in GTFS)
    """
    print("\nBuilding stations DataFrame...")

    df = pd.DataFrame()

    # UIC code
    df['uic_code'] = stops['uic_code']

    # Station name
    df['station_name'] = stops['stop_name']
    df['station_name_normalized'] = df['station_name'].apply(normalize_name)

    # City name (extract from station name)
    df['city_name'] = df['station_name'].apply(extract_city_from_station)
    df['city_name_normalized'] = df['city_name'].apply(normalize_name)

    # GPS coordinates
    df['latitude'] = stops['stop_lat']
    df['longitude'] = stops['stop_lon']

    # Segment DRG (not available in GTFS, leave empty)
    df['segment_drg'] = None

    # Sort by UIC code
    df = df.sort_values('uic_code').reset_index(drop=True)

    print(f"  Built {len(df):,} station records")

    return df


def print_sample_stations(df: pd.DataFrame, n: int = 10):
    """Print sample stations for verification."""
    print(f"\nSample stations (first {n}):")
    print("-" * 80)
    for _, row in df.head(n).iterrows():
        print(f"  {row['uic_code']}: {row['station_name']:40s} | City: {row['city_name']}")


def main():
    print("=" * 70)
    print("GENERATE stations_clean.csv FROM GTFS")
    print("=" * 70)
    print()

    # Load stops from GTFS
    stops = load_stops_from_gtfs(GTFS_DIR)

    # Build stations CSV
    stations = build_stations_csv(stops)

    # Print samples
    print_sample_stations(stations, n=15)

    # Save
    print(f"\nSaving to: {OUT_FILE}")
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    stations.to_csv(OUT_FILE, index=False, encoding='utf-8')
    print(f"  [OK] Saved {len(stations):,} stations")

    # Stats
    print("\nStatistics:")
    print(f"  Total stations: {len(stations):,}")
    print(f"  With GPS coords: {stations['latitude'].notna().sum():,}")
    print(f"  Unique cities: {stations['city_name'].nunique():,}")

    print("\nTop 10 cities by station count:")
    city_counts = stations['city_name'].value_counts().head(10)
    for city, count in city_counts.items():
        print(f"  {city:30s}: {count:3d} stations")

    print()
    print("=" * 70)
    print("Done.")
    print("=" * 70)


if __name__ == "__main__":
    main()
