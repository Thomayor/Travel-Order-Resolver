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


def get_station_priority(station_name: str) -> int:
    """
    Assign priority to station based on name.

    Lower number = higher priority (will appear first in mapping).

    Priority levels:
    - 0: TGV stations
    - 1: Main intercity stations (Gare de Lyon, Part Dieu, etc.)
    - 2: Regular stations
    """
    name_lower = station_name.lower()

    # Priority 0: TGV stations
    if 'tgv' in name_lower:
        return 0

    # Priority 1: Main intercity hubs
    main_stations = [
        'gare de lyon',         # Paris main TGV hub
        'part dieu',            # Lyon main TGV hub
        'saint-charles',        # Marseille main station
        'montparnasse',         # Paris TGV hub
        'gare du nord',         # Paris international hub
        'saint-jean',           # Bordeaux main station
        'matabiau',             # Toulouse main station
        'saint-laud',           # Angers main station
        'europe',               # Lille Europe (TGV/Eurostar)
    ]

    for main in main_stations:
        if main in name_lower:
            return 1

    # Priority 2: All other stations
    return 2


def prioritize_stations(input_file: str, output_file: str):
    """Reorder stations by priority."""
    print("=" * 70)
    print("PRIORITIZE MAIN TGV STATIONS IN CITY MAPPING")
    print("=" * 70)
    print()

    # Load mapping
    print(f"Loading: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"  Total rows: {len(df)}")
    print()

    # Add priority column
    df['_priority'] = df['station_name'].apply(get_station_priority)
    df['_station_name_lower'] = df['station_name'].str.lower()

    # Sort by: city_name_normalized, priority (ascending), station_name (alphabetical)
    df_sorted = df.sort_values(
        ['city_name_normalized', '_priority', '_station_name_lower']
    ).reset_index(drop=True)

    # Drop temporary columns
    df_sorted = df_sorted.drop(columns=['_priority', '_station_name_lower'])

    # Show examples of reordering
    print("Examples of prioritized stations:")
    print()

    for city in ['paris', 'lyon', 'marseille', 'toulouse', 'bordeaux']:
        city_stations = df_sorted[df_sorted['city_name_normalized'] == city]
        if len(city_stations) > 0:
            print(f"{city.upper()}:")
            for _, row in city_stations.head(3).iterrows():
                priority = get_station_priority(row['station_name'])
                priority_label = ["[TGV]", "[MAIN]", "[OTHER]"][priority]
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

    # Count by priority
    priority_counts = df_sorted.groupby(
        df_sorted['station_name'].apply(get_station_priority)
    ).size()

    print("\nStation distribution:")
    priority_labels = {0: "TGV stations", 1: "Main stations", 2: "Other stations"}
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
