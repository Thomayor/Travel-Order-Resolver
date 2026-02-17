"""
Prioritize Main TGV Stations in City Mapping

This script reorders city_station_mapping.csv to prioritize main TGV stations
over local stations, ensuring the pipeline uses the correct hubs for pathfinding.

Priority order:
1. TGV stations (contains "TGV" in name)
2. Main stations (Gare de Lyon, Part Dieu, Montparnasse, etc.)
3. Other stations (alphabetical)

Usage:
    python scripts/prioritize_main_stations.py
"""

import pandas as pd
from pathlib import Path


def get_station_priority(station_name: str, segment_drg: str = 'C') -> int:
    """
    Assign priority to station based on name and segment_drg.

    Lower number = higher priority (will appear first in mapping).

    Priority levels:
    - 0: TGV stations
    - 1: Segment A (national hubs) or known main stations
    - 2: Segment B (regional hubs)
    - 3: Segment C (local stations) / Other
    """
    name_lower = station_name.lower()
    drg = str(segment_drg).split(';')[0].strip() if pd.notna(segment_drg) else 'C'

    # Priority 0: TGV stations + major TGV hub stations (even without "TGV" in name)
    tgv_hubs = [
        'gare de lyon',         # Paris main TGV hub for south
        'part dieu',            # Lyon main TGV hub
        'saint-charles',        # Marseille main station
        'montparnasse',         # Paris TGV hub for west
        'gare du nord',         # Paris international hub (Eurostar, Thalys)
        'saint-jean',           # Bordeaux main station
        'matabiau',             # Toulouse main station
    ]

    if 'tgv' in name_lower:
        return 0

    for hub in tgv_hubs:
        if hub in name_lower:
            return 0

    # Priority 1: Segment A (national hubs) or known main stations
    main_stations = [
        'saint-laud',           # Angers main station
        'europe',               # Lille Europe (TGV/Eurostar)
        'saint-roch',           # Montpellier main station
        'chateaucreux',         # Saint-Étienne main station
    ]

    if drg == 'A':
        return 1

    for main in main_stations:
        if main in name_lower:
            return 1

    # Priority 2: Segment B (regional hubs)
    if drg == 'B':
        return 2

    # Priority 3: All other stations (segment C, local)
    return 3


def prioritize_stations(input_file: str, output_file: str,
                        stations_file: str = "data/processed/sncf/stations_clean.csv"):
    """Reorder stations by priority using station name and segment_drg."""
    print("=" * 70)
    print("PRIORITIZE MAIN TGV STATIONS IN CITY MAPPING")
    print("=" * 70)
    print()

    # Load mapping
    print(f"Loading: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"  Total rows: {len(df)}")

    # Load segment_drg from stations_clean.csv
    print(f"Loading station segments from: {stations_file}")
    stations = pd.read_csv(stations_file, encoding='utf-8', usecols=['uic_code', 'segment_drg'])
    # Handle multi-UIC codes (take first)
    stations['uic_code'] = stations['uic_code'].astype(str).str.split(';').str[0].str.strip()
    drg_map = dict(zip(stations['uic_code'], stations['segment_drg']))

    # Add segment_drg to mapping
    df['_segment_drg'] = df['uic_code'].astype(str).str.split(';').str[0].str.strip().map(drg_map).fillna('C')
    print()

    # Add priority column
    df['_priority'] = df.apply(
        lambda row: get_station_priority(row['station_name'], row['_segment_drg']),
        axis=1
    )
    df['_station_name_lower'] = df['station_name'].str.lower()

    # Sort by: city_name_normalized, priority (ascending), station_name (alphabetical)
    df_sorted = df.sort_values(
        ['city_name_normalized', '_priority', '_station_name_lower']
    ).reset_index(drop=True)

    # Drop temporary columns
    df_sorted = df_sorted.drop(columns=['_priority', '_station_name_lower', '_segment_drg'])

    # Show examples of reordering
    print("Examples of prioritized stations:")
    print()

    for city in ['paris', 'lyon', 'marseille', 'toulouse', 'bordeaux']:
        city_stations = df_sorted[df_sorted['city_name_normalized'] == city]
        if len(city_stations) > 0:
            print(f"{city.upper()}:")
            for _, row in city_stations.head(3).iterrows():
                drg = drg_map.get(str(row['uic_code']).split(';')[0].strip(), 'C')
                priority = get_station_priority(row['station_name'], drg)
                priority_label = {0: "[TGV]", 1: "[HUB-A]", 2: "[REG-B]", 3: "[LOCAL]"}.get(priority, "[?]")
                print(f"  {priority_label} {row['station_name']} ({row['uic_code']})")
            if len(city_stations) > 3:
                print(f"  ... and {len(city_stations) - 3} more stations")
            print()

    # Save reordered mapping
    print(f"Saving reordered mapping to: {output_file}")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df_sorted.to_csv(output_file, index=False, encoding='utf-8')
    print(f"  [OK] Saved {len(df_sorted)} rows")
    print()

    # Analyze changes
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    # Count by priority (re-compute using drg_map)
    priority_counts = df_sorted.groupby(
        df_sorted.apply(
            lambda row: get_station_priority(
                row['station_name'],
                drg_map.get(str(row['uic_code']).split(';')[0].strip(), 'C')
            ), axis=1
        )
    ).size()

    print("\nStation distribution:")
    priority_labels = {0: "TGV stations", 1: "Hub A / Main stations", 2: "Regional B", 3: "Local C"}
    for priority, count in priority_counts.items():
        print(f"  {priority_labels.get(priority, f'Priority {priority}')}: {count}")

    # Show what changed for Paris and Lyon
    print("\nKey changes:")
    paris_first = df_sorted[df_sorted['city_name_normalized'] == 'paris'].iloc[0]
    lyon_first = df_sorted[df_sorted['city_name_normalized'] == 'lyon'].iloc[0]

    print(f"  Paris first station: {paris_first['station_name']} ({paris_first['uic_code']})")
    print(f"  Lyon first station:  {lyon_first['station_name']} ({lyon_first['uic_code']})")

    print("\n[SUCCESS] Prioritization complete!")
    print("=" * 70)


def main():
    input_file = "data/processed/sncf/city_station_mapping.csv"
    output_file = "data/processed/sncf/city_station_mapping.csv"  # Overwrite

    prioritize_stations(input_file, output_file)

    print("\nNext steps:")
    print("  1. The city mapping has been updated in-place")
    print("  2. Test the pipeline: python demo_pipeline.py")
    print()


if __name__ == "__main__":
    main()
