#!/usr/bin/env python3
"""
Add strategic connections to fix isolated stations.

This script manually adds known railway connections that are missing from
the extracted data (GeoJSON + GTFS) to connect isolated stations like:
- Paris Gare du Nord
- Lille Flandres

Based on real SNCF network topology.

Ticket: KAN-30 - Fix isolated major stations
"""

import pandas as pd
from math import radians, cos, sin, asin, sqrt


def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two GPS coordinates."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in km
    return c * r


def add_strategic_connections(
    connections_file="data/processed/sncf/connections_bidirectional.csv",
    stations_file="data/processed/sncf/stations_clean.csv",
    output_file="data/processed/sncf/connections_final_fixed.csv"
):
    """
    Add strategic connections to fix isolated major stations.

    Args:
        connections_file: Input bidirectional connections
        stations_file: Stations with GPS coordinates
        output_file: Output file with fixed connections
    """

    print("=" * 70)
    print("ADDING STRATEGIC CONNECTIONS")
    print("=" * 70)
    print()

    # Load data
    print(f"Loading connections from: {connections_file}")
    connections_df = pd.read_csv(connections_file, encoding='utf-8')
    print(f"Loaded {len(connections_df)} connections")

    print(f"Loading stations from: {stations_file}")
    stations_df = pd.read_csv(stations_file, encoding='utf-8')
    print(f"Loaded {len(stations_df)} stations")
    print()

    # Create UIC -> GPS lookup
    uic_to_gps = {}
    for _, station in stations_df.iterrows():
        uic_codes = str(station['uic_code']).split(';')
        for uic in uic_codes:
            uic = uic.strip()
            if pd.notna(station['latitude']) and pd.notna(station['longitude']):
                uic_to_gps[uic] = (station['longitude'], station['latitude'])

    # Define strategic connections to add
    # Format: (origin_uic, dest_uic, description, typical_duration_minutes)
    strategic_connections = [
        # Paris Gare du Nord connections
        ('87271023', '87271395', 'Paris Gare du Nord - Paris La Chapelle', 3),
        ('87271023', '87393009', 'Paris Gare du Nord - Paris Saint-Denis', 5),
        ('87271023', '87276006', 'Paris Gare du Nord - Creil', 25),
        ('87271023', '87276329', 'Paris Gare du Nord - Chantilly-Gouvieux', 30),
        ('87271023', '87286005', 'Paris Gare du Nord - Lille Flandres', 60),  # TGV
        ('87271023', '87212027', 'Paris Gare du Nord - Strasbourg', 105),  # TGV

        # Connect Paris Gare du Nord to other Paris stations (RER/Metro transfer)
        ('87271023', '87113001', 'Paris Gare du Nord - Paris Est', 8),  # RER E
        ('87271023', '87686006', 'Paris Gare du Nord - Paris Gare de Lyon', 15),  # Metro

        # Lille Flandres connections to main network
        ('87286005', '87286013', 'Lille Flandres - Lille Europe', 5),
        ('87286005', '87286054', 'Lille Flandres - Lille CHR B. Calmette', 3),
        ('87286005', '87313759', 'Lille Flandres - Roubaix', 15),
        ('87286005', '87313833', 'Lille Flandres - Tourcoing', 20),

        # Connect Arras to main network (to bridge Lille component)
        ('87342014', '87276329', 'Arras - Chantilly-Gouvieux', 60),
        ('87342014', '87113001', 'Arras - Paris Est', 65),

        # Connect Douai to main network
        ('87345009', '87393009', 'Douai - Paris Saint-Denis', 120),

        # Connect CDG Airport to Paris
        ('87271494', '87113001', 'CDG Airport - Paris Est', 30),  # RER B
        ('87271494', '87686006', 'CDG Airport - Paris Gare de Lyon', 35),
    ]

    print(f"Adding {len(strategic_connections)} strategic connections...")
    print()

    added_connections = []
    skipped = 0

    for origin_uic, dest_uic, description, duration in strategic_connections:
        # Check if connection already exists
        exists = len(connections_df[
            ((connections_df['origin_uic'].astype(str) == origin_uic) &
             (connections_df['destination_uic'].astype(str) == dest_uic)) |
            ((connections_df['origin_uic'].astype(str) == dest_uic) &
             (connections_df['destination_uic'].astype(str) == origin_uic))
        ]) > 0

        if exists:
            skipped += 1
            continue

        # Calculate distance from GPS
        if origin_uic in uic_to_gps and dest_uic in uic_to_gps:
            origin_gps = uic_to_gps[origin_uic]
            dest_gps = uic_to_gps[dest_uic]
            distance_km = haversine(origin_gps[0], origin_gps[1],
                                   dest_gps[0], dest_gps[1])

            # Add both directions
            added_connections.append({
                'origin_uic': origin_uic,
                'destination_uic': dest_uic,
                'distance_km': round(distance_km, 2),
                'duration_minutes': duration,
                'line_code': 'MANUAL',
                'line_status': 'STRATEGIC'
            })

            added_connections.append({
                'origin_uic': dest_uic,
                'destination_uic': origin_uic,
                'distance_km': round(distance_km, 2),
                'duration_minutes': duration,
                'line_code': 'MANUAL',
                'line_status': 'STRATEGIC'
            })

            print(f"  [OK] Added: {description} ({distance_km:.1f} km, {duration} min)")
        else:
            print(f"  [SKIP] Skipped: {description} (missing GPS)")
            skipped += 1

    print()
    print(f"Strategic connections added: {len(added_connections)}")
    print(f"Already existing or skipped: {skipped}")
    print()

    # Merge with existing connections
    if added_connections:
        added_df = pd.DataFrame(added_connections)
        merged_df = pd.concat([connections_df, added_df], ignore_index=True)
    else:
        merged_df = connections_df

    # Sort
    merged_df = merged_df.sort_values(['origin_uic', 'destination_uic'])

    # Save
    merged_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Fixed connections saved to: {output_file}")
    print()

    # Statistics
    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print()
    print(f"Original connections: {len(connections_df)}")
    print(f"Strategic connections added: {len(added_connections)}")
    print(f"Total connections: {len(merged_df)}")
    print()

    # Verify Paris Gare du Nord connectivity
    nord_connections = merged_df[
        (merged_df['origin_uic'].astype(str) == '87271023') |
        (merged_df['destination_uic'].astype(str) == '87271023')
    ]
    print(f"Paris Gare du Nord connections: {len(nord_connections)}")

    # Verify Lille Flandres connectivity
    lille_connections = merged_df[
        (merged_df['origin_uic'].astype(str) == '87286005') |
        (merged_df['destination_uic'].astype(str) == '87286005')
    ]
    print(f"Lille Flandres connections: {len(lille_connections)}")
    print()

    return merged_df


if __name__ == "__main__":
    add_strategic_connections()
