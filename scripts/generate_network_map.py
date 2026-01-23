#!/usr/bin/env python3
"""
Generate a PNG map of the French railway network.

This script creates a static image showing:
- Railway connections (blue lines)
- Stations (red dots)
- Major cities (labeled)

Output: railway_network.png
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np


def generate_network_map(
    stations_file="data/processed/sncf/stations_clean.csv",
    connections_file="data/processed/sncf/connections_bidirectional.csv",
    output_file="railway_network.png",
    show_labels=True
):
    """
    Generate a PNG map of the railway network.

    Args:
        stations_file: Path to stations CSV
        connections_file: Path to connections CSV
        output_file: Path to output PNG file
        show_labels: Whether to show labels for major cities
    """

    print("=" * 70)
    print("GENERATING RAILWAY NETWORK MAP")
    print("=" * 70)
    print()

    # Load data
    print(f"Loading stations from: {stations_file}")
    stations_df = pd.read_csv(stations_file, encoding='utf-8')
    stations_df = stations_df[stations_df['latitude'].notna() & stations_df['longitude'].notna()]

    print(f"Loading connections from: {connections_file}")
    connections_df = pd.read_csv(connections_file, encoding='utf-8')

    print(f"Stations: {len(stations_df)}")
    print(f"Connections: {len(connections_df)}")
    print()

    # Create station lookup
    station_coords = {}
    for _, station in stations_df.iterrows():
        uic = str(station['uic_code']).split(';')[0]
        station_coords[uic] = (station['longitude'], station['latitude'])

    # Create figure
    print("Creating map...")
    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)

    # Draw connections (blue lines)
    print("Drawing connections...")
    connection_count = 0
    for _, conn in connections_df.iterrows():
        origin_uic = str(conn['origin_uic']).split(';')[0]
        dest_uic = str(conn['destination_uic']).split(';')[0]

        if origin_uic in station_coords and dest_uic in station_coords:
            lon1, lat1 = station_coords[origin_uic]
            lon2, lat2 = station_coords[dest_uic]

            ax.plot([lon1, lon2], [lat1, lat2],
                   color='blue', linewidth=0.3, alpha=0.4, zorder=1)
            connection_count += 1

    print(f"Drew {connection_count} connections")

    # Draw stations (red dots)
    print("Drawing stations...")
    lons = [coords[0] for coords in station_coords.values()]
    lats = [coords[1] for coords in station_coords.values()]
    ax.scatter(lons, lats, c='red', s=1, alpha=0.6, zorder=2)

    # Label major cities
    if show_labels:
        print("Adding labels for major cities...")
        major_cities = {
            '87686006': 'Paris Gare de Lyon',
            '87723197': 'Lyon',
            '87751008': 'Marseille',
            '87611004': 'Toulouse',
            '87581009': 'Bordeaux',
            '87212027': 'Strasbourg',
            '87391003': 'Paris Montparnasse',
            '87286005': 'Lille',
            '87481002': 'Nantes',
            '87481051': 'Rennes'
        }

        for uic, name in major_cities.items():
            if uic in station_coords:
                lon, lat = station_coords[uic]
                ax.scatter([lon], [lat], c='darkred', s=100, marker='o',
                          edgecolors='white', linewidth=2, zorder=3)
                ax.annotate(name, (lon, lat),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor='white', alpha=0.8),
                           zorder=4)

    # Set bounds (France metropolitan)
    ax.set_xlim(-5.5, 10)
    ax.set_ylim(41, 51.5)

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title('Réseau Ferroviaire SNCF\n' +
                f'{len(stations_df)} gares • {len(connections_df)} connexions',
                fontsize=16, fontweight='bold', pad=20)

    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='blue', linewidth=2, label='Connexions ferroviaires'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
               markersize=8, label='Gares'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='darkred',
               markeredgecolor='white', markeredgewidth=2,
               markersize=12, label='Grandes villes')
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=10)

    # Add statistics box
    stats_text = (
        f"Statistiques du réseau:\n"
        f"• Gares totales: {len(stations_df)}\n"
        f"• Connexions: {len(connections_df)} (bidirectionnelles)\n"
        f"• Paires uniques: {len(connections_df)//2}\n"
        f"• Distance moyenne: {connections_df['distance_km'].mean():.1f} km\n"
        f"• Durée moyenne: {connections_df['duration_minutes'].mean():.0f} min"
    )

    ax.text(0.98, 0.98, stats_text,
           transform=ax.transAxes,
           fontsize=9,
           verticalalignment='top',
           horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Save
    plt.tight_layout()
    print()
    print(f"Saving map to: {output_file}")
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Map saved successfully!")
    print()

    # Show file size
    import os
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"File size: {file_size:.2f} MB")
    print()

    print("=" * 70)
    print("MAP GENERATION COMPLETED")
    print("=" * 70)

    plt.close()


if __name__ == "__main__":
    generate_network_map()
