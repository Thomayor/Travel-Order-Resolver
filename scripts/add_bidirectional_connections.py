#!/usr/bin/env python3
"""
Add bidirectional connections to the railway network.

Most railway connections are bidirectional, but the GeoJSON extraction only creates
unidirectional connections (start -> end of LineString). This script adds the reverse
connections where they don't already exist.

Ticket: KAN-30 - Fix network connectivity
"""

import pandas as pd


def add_bidirectional_connections(
    input_file: str = "data/processed/sncf/connections_final.csv",
    output_file: str = "data/processed/sncf/connections_bidirectional.csv"
):
    """
    Add reverse connections for all unidirectional connections.

    Args:
        input_file: Input connections file
        output_file: Output file with bidirectional connections
    """

    print("=" * 70)
    print("ADDING BIDIRECTIONAL CONNECTIONS")
    print("=" * 70)
    print()

    # Load connections
    print(f"Loading connections from: {input_file}")
    connections_df = pd.read_csv(input_file, encoding='utf-8')
    print(f"Loaded {len(connections_df)} connections")
    print()

    # Check current bidirectionality
    forward = set(zip(connections_df['origin_uic'].astype(str),
                       connections_df['destination_uic'].astype(str)))
    backward = set(zip(connections_df['destination_uic'].astype(str),
                        connections_df['origin_uic'].astype(str)))
    bidirectional = forward & backward

    print(f"Current bidirectional connections: {len(bidirectional)}/{len(forward)} ({len(bidirectional)/len(forward)*100:.1f}%)")
    print()

    # Find connections that need reverse
    needs_reverse = forward - backward
    print(f"Connections needing reverse: {len(needs_reverse)}")
    print()

    # Create reverse connections
    print("Creating reverse connections...")
    reverse_connections = []

    for origin, dest in needs_reverse:
        # Find the original connection
        original = connections_df[
            (connections_df['origin_uic'].astype(str) == origin) &
            (connections_df['destination_uic'].astype(str) == dest)
        ].iloc[0]

        # Create reverse
        reverse_connections.append({
            'origin_uic': dest,
            'destination_uic': origin,
            'distance_km': original['distance_km'],
            'duration_minutes': original['duration_minutes'],
            'line_code': original['line_code'],
            'line_status': original['line_status']
        })

    reverse_df = pd.DataFrame(reverse_connections)
    print(f"Created {len(reverse_df)} reverse connections")
    print()

    # Merge with original
    print("Merging with original connections...")
    merged_df = pd.concat([connections_df, reverse_df], ignore_index=True)

    # Sort by origin
    merged_df = merged_df.sort_values(['origin_uic', 'destination_uic'])

    print(f"Total connections: {len(merged_df)}")
    print()

    # Verify bidirectionality
    forward_new = set(zip(merged_df['origin_uic'].astype(str),
                           merged_df['destination_uic'].astype(str)))
    backward_new = set(zip(merged_df['destination_uic'].astype(str),
                            merged_df['origin_uic'].astype(str)))
    bidirectional_new = forward_new & backward_new

    print(f"New bidirectional connections: {len(bidirectional_new)}/{len(forward_new)} ({len(bidirectional_new)/len(forward_new)*100:.1f}%)")
    print()

    # Save
    merged_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Saved bidirectional network to: {output_file}")
    print()

    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)
    print()
    print(f"Original connections: {len(connections_df)}")
    print(f"Reverse connections added: {len(reverse_df)}")
    print(f"Total connections: {len(merged_df)}")
    print(f"Bidirectional ratio: {len(bidirectional_new)/len(forward_new)*100:.1f}%")
    print()


if __name__ == "__main__":
    add_bidirectional_connections()
