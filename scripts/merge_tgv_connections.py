"""
Merge TGV Connections from Archive

This script merges archived TGV connections (especially Paris-Lyon direct routes)
into the current connections file to fix the pathfinding issue.

Issue: Paris-Lyon returns 47-stop TER route instead of direct TGV
Cause: connections_final.csv missing TGV connections for Paris stations
Solution: Merge connections_tgv.csv into connections_final.csv

Usage:
    python scripts/merge_tgv_connections.py
"""

import pandas as pd
from pathlib import Path


def load_current_connections(file_path: str) -> pd.DataFrame:
    """Load current connections file."""
    print(f"Loading current connections from: {file_path}")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"  Current connections: {len(df)}")
    return df


def load_archived_tgv_connections(file_path: str) -> pd.DataFrame:
    """Load archived TGV connections."""
    print(f"\nLoading archived TGV connections from: {file_path}")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"  Archived TGV connections: {len(df)}")
    return df


def merge_connections(current_df: pd.DataFrame, tgv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge TGV connections into current connections.

    Strategy:
    1. Remove any existing connections between the same origin-destination pairs
    2. Add TGV connections (which are faster and more direct)
    3. Sort by origin_uic, destination_uic
    """
    print("\nMerging connections...")

    # Create a key for deduplication (origin_uic, destination_uic)
    current_df['_key'] = current_df['origin_uic'].astype(str) + '_' + current_df['destination_uic'].astype(str)
    tgv_df['_key'] = tgv_df['origin_uic'].astype(str) + '_' + tgv_df['destination_uic'].astype(str)

    # Get keys from TGV connections
    tgv_keys = set(tgv_df['_key'])

    # Remove from current any connections that will be replaced by TGV
    print(f"  Removing {len(current_df[current_df['_key'].isin(tgv_keys)])} existing connections that will be replaced by TGV...")
    current_df_filtered = current_df[~current_df['_key'].isin(tgv_keys)].copy()

    # Drop temporary key column
    current_df_filtered = current_df_filtered.drop(columns=['_key'])
    tgv_df = tgv_df.drop(columns=['_key'])

    # Concatenate
    merged_df = pd.concat([current_df_filtered, tgv_df], ignore_index=True)

    # Sort by origin_uic, destination_uic
    merged_df = merged_df.sort_values(['origin_uic', 'destination_uic']).reset_index(drop=True)

    print(f"  Final connection count: {len(merged_df)}")
    print(f"  Added {len(tgv_df)} TGV connections")

    return merged_df


def analyze_paris_lyon_connections(df: pd.DataFrame):
    """Analyze connections between Paris and Lyon stations."""
    print("\n" + "=" * 70)
    print("PARIS-LYON CONNECTION ANALYSIS")
    print("=" * 70)

    # Paris Gare de Lyon
    paris_gare_lyon = '87686006'

    # Lyon stations
    lyon_part_dieu = '87723197'
    lyon_st_exupery = '87762906'
    lyon_perrache = '87722025'

    # Find connections from Paris to Lyon
    paris_to_lyon = df[
        (df['origin_uic'] == paris_gare_lyon) &
        (df['destination_uic'].isin([lyon_part_dieu, lyon_st_exupery, lyon_perrache]))
    ]

    print(f"\nConnections from Paris Gare de Lyon ({paris_gare_lyon}) to Lyon:")
    if len(paris_to_lyon) > 0:
        for _, row in paris_to_lyon.iterrows():
            print(f"  → {row['destination_station_name']} ({row['destination_uic']})")
            print(f"     Duration: {row['duration_minutes']} min | Source: {row['source']}")
    else:
        print("  [X] NO CONNECTIONS FOUND")

    # Find connections from Lyon to Paris
    lyon_to_paris = df[
        (df['origin_uic'].isin([lyon_part_dieu, lyon_st_exupery, lyon_perrache])) &
        (df['destination_uic'] == paris_gare_lyon)
    ]

    print(f"\nConnections from Lyon to Paris Gare de Lyon ({paris_gare_lyon}):")
    if len(lyon_to_paris) > 0:
        for _, row in lyon_to_paris.iterrows():
            print(f"  → From {row['origin_station_name']} ({row['origin_uic']})")
            print(f"     Duration: {row['duration_minutes']} min | Source: {row['source']}")
    else:
        print("  [X] NO CONNECTIONS FOUND")

    print("\n" + "=" * 70)


def save_merged_connections(df: pd.DataFrame, output_path: str):
    """Save merged connections to file."""
    print(f"\nSaving merged connections to: {output_path}")

    # Create parent directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"  [OK] Saved {len(df)} connections")


def main():
    """Main function to merge TGV connections."""
    print("=" * 70)
    print("MERGE TGV CONNECTIONS INTO CURRENT DATABASE")
    print("=" * 70)

    # File paths
    current_file = "data/processed/sncf/connections_final.csv"
    tgv_archive = "data/archive/old_connections/connections_tgv.csv"
    output_file = "data/processed/sncf/connections_final_fixed.csv"

    # Load data
    current_df = load_current_connections(current_file)
    tgv_df = load_archived_tgv_connections(tgv_archive)

    # Analyze BEFORE merge
    print("\n" + "=" * 70)
    print("BEFORE MERGE - Current connections:")
    analyze_paris_lyon_connections(current_df)

    # Merge
    merged_df = merge_connections(current_df, tgv_df)

    # Analyze AFTER merge
    print("\n" + "=" * 70)
    print("AFTER MERGE - With TGV connections:")
    analyze_paris_lyon_connections(merged_df)

    # Save
    save_merged_connections(merged_df, output_file)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Original connections:  {len(current_df)}")
    print(f"TGV connections added: {len(tgv_df)}")
    print(f"Final connections:     {len(merged_df)}")
    print(f"\nOutput file: {output_file}")
    print("\nNext steps:")
    print("  1. Rebuild graph cache: python -c \"from src.pathfinding.graph_loader import get_or_build_graph; get_or_build_graph(force_rebuild=True)\"")
    print("  2. Test Paris-Lyon route: python demo_pipeline.py")
    print("\n[SUCCESS] MERGE COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
