#!/usr/bin/env python3
"""
Extract TGV connections from SNCF GTFS data.

This script processes the GTFS files (routes, trips, stop_times) to extract
connections between stations for TGV lines.

Ticket: KAN-29 - Complete railway network with TGV connections
"""

import pandas as pd
from collections import defaultdict
from pathlib import Path


def extract_tgv_connections(
    gtfs_dir: str = "data/raw/sncf/gtfs",
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    output_file: str = "data/processed/sncf/connections_tgv.csv"
):
    """
    Extract TGV connections from GTFS data.

    Args:
        gtfs_dir: Directory containing GTFS files
        stations_file: Path to cleaned stations CSV
        output_file: Path to output TGV connections CSV
    """

    print("=" * 70)
    print("EXTRACTING TGV CONNECTIONS FROM GTFS")
    print("=" * 70)
    print()

    # Load stations to get UIC codes
    print(f"Loading stations from: {stations_file}")
    stations_df = pd.read_csv(stations_file, encoding='utf-8')

    # Create mapping from GTFS stop_id to UIC code
    # GTFS stop_id format: StopPoint:OCETGV INOUI-87xxxxxx or StopArea:OCE87xxxxxx
    # We need to extract the UIC code from the stop_id
    def extract_uic_from_stop_id(stop_id):
        """Extract UIC code from GTFS stop_id."""
        # Format: StopPoint:OCETGV INOUI-87271007 or StopArea:OCE87271007
        if '-' in stop_id:
            # StopPoint format with service type
            uic = stop_id.split('-')[-1]
        elif 'OCE' in stop_id:
            # StopArea format
            uic = stop_id.split('OCE')[-1]
        else:
            return None

        # Take only first UIC if multiple (semicolon-separated)
        return uic.strip()

    # No pre-mapping needed, we'll extract UIC on the fly

    print(f"Loaded {len(stations_df)} stations")
    print()

    # Load GTFS routes
    print("Loading GTFS routes...")
    routes_file = Path(gtfs_dir) / "routes.txt"
    routes = pd.read_csv(routes_file, encoding='utf-8')

    # Filter TGV routes (containing "TGV" in name)
    tgv_routes = routes[routes['route_long_name'].str.contains('TGV', case=False, na=False)]
    tgv_route_ids = set(tgv_routes['route_id'])

    print(f"Total routes: {len(routes)}")
    print(f"TGV routes: {len(tgv_routes)}")
    print()

    # Load GTFS trips
    print("Loading GTFS trips...")
    trips_file = Path(gtfs_dir) / "trips.txt"
    trips = pd.read_csv(trips_file, encoding='utf-8')

    # Filter trips for TGV routes
    tgv_trips = trips[trips['route_id'].isin(tgv_route_ids)]
    tgv_trip_ids = set(tgv_trips['trip_id'])

    print(f"Total trips: {len(trips)}")
    print(f"TGV trips: {len(tgv_trips)}")
    print()

    # Load GTFS stop_times
    print("Loading GTFS stop_times (this may take a while, 56 MB file)...")
    stop_times_file = Path(gtfs_dir) / "stop_times.txt"

    # Read in chunks to handle large file
    # Store durations for each connection (to calculate average)
    connections_dict = defaultdict(lambda: {'count': 0, 'trips': [], 'durations': []})

    chunk_size = 100000
    chunks_processed = 0

    def parse_gtfs_time(time_str):
        """Parse GTFS time format (HH:MM:SS, can exceed 24h)."""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 60 + minutes + seconds / 60.0  # Convert to minutes

    for chunk in pd.read_csv(stop_times_file, encoding='utf-8', chunksize=chunk_size):
        chunks_processed += 1

        # Filter for TGV trips
        tgv_stop_times = chunk[chunk['trip_id'].isin(tgv_trip_ids)]

        if len(tgv_stop_times) == 0:
            continue

        # Group by trip to get station sequences with times
        for trip_id, group in tgv_stop_times.groupby('trip_id'):
            # Sort by stop_sequence
            group = group.sort_values('stop_sequence')

            # Extract consecutive station pairs WITH times
            stops = group['stop_id'].tolist()
            departure_times = group['departure_time'].tolist()
            arrival_times = group['arrival_time'].tolist()

            for i in range(len(stops) - 1):
                origin_stop = stops[i]
                dest_stop = stops[i + 1]

                # Extract UIC codes
                origin_uic = extract_uic_from_stop_id(origin_stop)
                dest_uic = extract_uic_from_stop_id(dest_stop)

                if origin_uic and dest_uic and origin_uic != dest_uic:
                    # Take first UIC code if multiple (semicolon-separated)
                    origin_uic = origin_uic.split(';')[0].strip()
                    dest_uic = dest_uic.split(';')[0].strip()

                    # Calculate duration from GTFS times
                    try:
                        depart_time = parse_gtfs_time(departure_times[i])
                        arrive_time = parse_gtfs_time(arrival_times[i + 1])
                        duration_minutes = arrive_time - depart_time

                        if duration_minutes > 0:  # Sanity check
                            connection_key = (origin_uic, dest_uic)
                            connections_dict[connection_key]['count'] += 1
                            connections_dict[connection_key]['trips'].append(trip_id)
                            connections_dict[connection_key]['durations'].append(duration_minutes)
                    except (ValueError, IndexError):
                        # Skip if time parsing fails
                        pass

        if chunks_processed % 5 == 0:
            print(f"  Processed {chunks_processed * chunk_size:,} rows, "
                  f"found {len(connections_dict)} unique connections...", end='\r')

    print()
    print()
    print(f"Total unique TGV connections found: {len(connections_dict)}")
    print()

    # Convert to DataFrame
    connections = []
    for (origin_uic, dest_uic), data in connections_dict.items():
        # Get station names
        origin_station = stations_df[stations_df['uic_code'].str.contains(origin_uic, na=False)]
        dest_station = stations_df[stations_df['uic_code'].str.contains(dest_uic, na=False)]

        if len(origin_station) > 0 and len(dest_station) > 0:
            origin_name = origin_station.iloc[0]['station_name']
            dest_name = dest_station.iloc[0]['station_name']

            # Calculate average duration from all trips for this connection
            if len(data['durations']) > 0:
                avg_duration = sum(data['durations']) / len(data['durations'])
                duration_minutes = int(round(avg_duration))
            else:
                duration_minutes = None

            connections.append({
                'origin_uic': origin_uic,
                'destination_uic': dest_uic,
                'origin_name': origin_name,
                'destination_name': dest_name,
                'trip_count': data['count'],
                'duration_minutes': duration_minutes,
                'source': 'GTFS_TGV'
            })

    connections_df = pd.DataFrame(connections)

    if len(connections_df) == 0:
        print("[WARNING] No TGV connections found!")
        return None

    # Sort by trip count (most frequent first)
    connections_df = connections_df.sort_values('trip_count', ascending=False)

    print("=" * 70)
    print("TGV CONNECTIONS SUMMARY")
    print("=" * 70)
    print()
    print(f"Total TGV connections: {len(connections_df)}")
    print()

    # Show top 20 most frequent connections
    print("Top 20 most frequent TGV connections:")
    for _, conn in connections_df.head(20).iterrows():
        duration_str = f", {conn['duration_minutes']} min" if pd.notna(conn.get('duration_minutes')) else ""
        print(f"  {conn['origin_name']} -> {conn['destination_name']}: "
              f"{conn['trip_count']} trips{duration_str}")

    print()

    # Save to CSV
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    connections_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"TGV connections saved to: {output_file}")
    print()

    return connections_df


if __name__ == "__main__":
    extract_tgv_connections()
