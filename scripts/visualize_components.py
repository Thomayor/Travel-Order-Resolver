#!/usr/bin/env python3
"""
Visualize connected components of the railway network.

This script creates a PNG map showing each connected component in a different color.
Useful for understanding network fragmentation.

Output: railway_network_components.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def visualize_components(
    stations_file="data/processed/sncf/stations_clean.csv",
    connections_file="data/processed/sncf/connections_bidirectional.csv",
    output_file="railway_network_components.png"
):
    """
    Visualize connected components of the railway network.

    Args:
        stations_file: Path to stations CSV
        connections_file: Path to connections CSV
        output_file: Path to output PNG file
    """

    print("=" * 70)
    print("VISUALIZING CONNECTED COMPONENTS")
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

    # Build graph
    print("Building NetworkX graph...")
    G = nx.Graph()

    # Add nodes
    for _, station in stations_df.iterrows():
        uic = str(station['uic_code']).split(';')[0]
        G.add_node(uic,
                  lon=station['longitude'],
                  lat=station['latitude'],
                  name=station['station_name'])

    # Add edges
    for _, conn in connections_df.iterrows():
        origin_uic = str(conn['origin_uic']).split(';')[0]
        dest_uic = str(conn['destination_uic']).split(';')[0]

        if origin_uic in G.nodes() and dest_uic in G.nodes():
            G.add_edge(origin_uic, dest_uic)

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print()

    # Find connected components
    print("Finding connected components...")
    components = list(nx.connected_components(G))
    components_sorted = sorted(components, key=len, reverse=True)

    print(f"Number of components: {len(components)}")
    print(f"Largest component: {len(components_sorted[0])} stations ({len(components_sorted[0])/G.number_of_nodes()*100:.1f}%)")
    print()

    # Show component sizes
    print("Top 10 components by size:")
    for i, comp in enumerate(components_sorted[:10]):
        print(f"  {i+1}. {len(comp)} stations")
    print()

    # Assign colors to components
    print("Assigning colors...")
    node_to_component = {}
    for i, comp in enumerate(components_sorted):
        for node in comp:
            node_to_component[node] = i

    # Create color map (highlight largest, gray for small)
    def get_component_color(comp_index, total_components):
        if comp_index == 0:
            return 'red'  # Largest component in red
        elif comp_index < 10:
            # Top 10 components in distinct colors
            colors = ['blue', 'green', 'orange', 'purple', 'brown',
                     'pink', 'cyan', 'olive', 'navy']
            return colors[comp_index - 1]
        else:
            return 'gray'  # Small components in gray

    # Create figure
    print("Creating visualization...")
    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)

    # Draw connections grouped by component
    print("Drawing connections by component...")
    for i, comp in enumerate(components_sorted):
        if i >= 10:
            # Don't draw small components to avoid clutter
            break

        subgraph = G.subgraph(comp)
        color = get_component_color(i, len(components_sorted))

        for u, v in subgraph.edges():
            u_data = G.nodes[u]
            v_data = G.nodes[v]

            ax.plot([u_data['lon'], v_data['lon']],
                   [u_data['lat'], v_data['lat']],
                   color=color, linewidth=0.3, alpha=0.5, zorder=1)

    # Draw stations grouped by component
    print("Drawing stations by component...")
    for i, comp in enumerate(components_sorted[:10]):
        color = get_component_color(i, len(components_sorted))

        lons = [G.nodes[node]['lon'] for node in comp]
        lats = [G.nodes[node]['lat'] for node in comp]

        size = 10 if i == 0 else 3  # Larger dots for main component
        ax.scatter(lons, lats, c=color, s=size, alpha=0.8, zorder=2,
                  label=f"Composante {i+1}: {len(comp)} gares")

    # Draw small components in gray (no lines, just dots)
    print("Drawing small components...")
    small_comp_nodes = [node for i, comp in enumerate(components_sorted[10:], 10)
                       for node in comp]
    if small_comp_nodes:
        lons = [G.nodes[node]['lon'] for node in small_comp_nodes]
        lats = [G.nodes[node]['lat'] for node in small_comp_nodes]
        ax.scatter(lons, lats, c='gray', s=1, alpha=0.3, zorder=1,
                  label=f"Autres ({len(components_sorted)-10} composantes)")

    # Label major cities in main component
    print("Adding labels for major cities...")
    major_cities = {
        '87686006': 'Paris',
        '87723197': 'Lyon',
        '87751008': 'Marseille',
        '87611004': 'Toulouse',
        '87581009': 'Bordeaux',
        '87212027': 'Strasbourg'
    }

    main_component = components_sorted[0]
    for uic, name in major_cities.items():
        if uic in main_component:
            node_data = G.nodes[uic]
            ax.annotate(name, (node_data['lon'], node_data['lat']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3',
                               facecolor='white', alpha=0.9),
                       zorder=5)

    # Set bounds (France metropolitan)
    ax.set_xlim(-5.5, 10)
    ax.set_ylim(41, 51.5)

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title(f'Composantes Connexes du Réseau Ferroviaire SNCF\n' +
                f'{len(components)} composantes • Principale: {len(components_sorted[0])} gares ({len(components_sorted[0])/G.number_of_nodes()*100:.1f}%)',
                fontsize=14, fontweight='bold', pad=20)

    # Add legend
    ax.legend(loc='lower left', fontsize=8, ncol=2)

    # Add statistics box
    stats_text = (
        f"Fragmentation du réseau:\n"
        f"• Total gares: {G.number_of_nodes()}\n"
        f"• Composante principale: {len(components_sorted[0])} ({len(components_sorted[0])/G.number_of_nodes()*100:.1f}%)\n"
        f"• Composantes isolées: {len(components_sorted)-1}\n"
        f"• Gares orphelines: {sum(1 for c in components if len(c) == 1)}"
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
    print(f"Saving visualization to: {output_file}")
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Visualization saved successfully!")
    print()

    # Show file size
    import os
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"File size: {file_size:.2f} MB")
    print()

    print("=" * 70)
    print("COMPONENT VISUALIZATION COMPLETED")
    print("=" * 70)

    plt.close()


if __name__ == "__main__":
    visualize_components()
