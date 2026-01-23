#!/usr/bin/env python3
"""
Visualize Railway Network Graph

This script creates a visual representation of the SNCF railway network graph
using matplotlib with GPS coordinates for positioning.

Ticket: KAN-28 - Build graph database schema
"""

import sys
import os
import matplotlib.pyplot as plt
import networkx as nx

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.pathfinding.graph_loader import (
    build_railway_graph,
    validate_graph
)


def visualize_network(graph, output_file='railway_network.png', show_labels=False):
    """
    Visualize railway network using GPS coordinates.

    Args:
        graph: NetworkX graph with station data
        output_file: Output image file path
        show_labels: Whether to show station names (can be cluttered)
    """
    print("Creating network visualization...")
    print()

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))

    # Extract GPS positions for nodes that have coordinates
    pos = {}
    nodes_with_coords = []

    for node in graph.nodes():
        data = graph.nodes[node]
        if data['latitude'] and data['longitude']:
            # Use (longitude, latitude) for (x, y) positioning
            pos[node] = (data['longitude'], data['latitude'])
            nodes_with_coords.append(node)

    print(f"Nodes with GPS coordinates: {len(nodes_with_coords)}/{graph.number_of_nodes()}")

    # Create subgraph with only nodes that have coordinates
    subgraph = graph.subgraph(nodes_with_coords)

    print(f"Visualizing {subgraph.number_of_nodes()} stations and {subgraph.number_of_edges()} connections")
    print()

    # Find connected components
    components = list(nx.connected_components(subgraph))
    print(f"Network has {len(components)} connected components")

    if len(components) > 0:
        largest_component = max(components, key=len)
        print(f"Largest component: {len(largest_component)} stations")
        print()

    # Draw network
    print("Drawing network...")

    # Draw edges (connections)
    nx.draw_networkx_edges(
        subgraph, pos,
        edge_color='steelblue',
        alpha=0.4,
        width=1,
        ax=ax
    )

    # Draw nodes
    # Color nodes by whether they're connected
    node_colors = []
    for node in subgraph.nodes():
        if subgraph.degree(node) > 0:
            node_colors.append('red')  # Connected stations
        else:
            node_colors.append('lightgray')  # Orphaned stations

    nx.draw_networkx_nodes(
        subgraph, pos,
        node_color=node_colors,
        node_size=20,
        alpha=0.7,
        ax=ax
    )

    # Optionally draw labels (warning: can be very cluttered)
    if show_labels:
        # Only label stations with connections
        labels = {}
        for node in subgraph.nodes():
            if subgraph.degree(node) > 0:
                labels[node] = subgraph.nodes[node]['city_name']

        nx.draw_networkx_labels(
            subgraph, pos,
            labels,
            font_size=6,
            font_color='black',
            ax=ax
        )

    # Set title and labels
    ax.set_title('SNCF Railway Network Graph\n(Red: Connected Stations, Gray: Orphaned Stations)',
                 fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)

    # Add grid
    ax.grid(True, alpha=0.3)

    # Add statistics as text
    stats_text = f"Stations: {subgraph.number_of_nodes()}\n"
    stats_text += f"Connections: {subgraph.number_of_edges()}\n"
    stats_text += f"Components: {len(components)}"

    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {output_file}")
    print()

    # Show interactive plot
    print("Displaying interactive plot (close window to continue)...")
    plt.show()


def visualize_largest_component(graph, output_file='railway_network_main.png'):
    """
    Visualize only the largest connected component of the network.

    Args:
        graph: NetworkX graph with station data
        output_file: Output image file path
    """
    print("=" * 70)
    print("VISUALIZING LARGEST CONNECTED COMPONENT")
    print("=" * 70)
    print()

    # Extract nodes with GPS
    nodes_with_coords = []
    pos = {}

    for node in graph.nodes():
        data = graph.nodes[node]
        if data['latitude'] and data['longitude']:
            pos[node] = (data['longitude'], data['latitude'])
            nodes_with_coords.append(node)

    subgraph = graph.subgraph(nodes_with_coords)

    # Get largest connected component
    components = list(nx.connected_components(subgraph))

    if len(components) == 0:
        print("No connected components found!")
        return

    largest_component = max(components, key=len)
    component_graph = subgraph.subgraph(largest_component)

    print(f"Largest component has {component_graph.number_of_nodes()} stations")
    print(f"and {component_graph.number_of_edges()} connections")
    print()

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))

    # Draw edges
    nx.draw_networkx_edges(
        component_graph, pos,
        edge_color='steelblue',
        alpha=0.5,
        width=1.5,
        ax=ax
    )

    # Color nodes by degree (number of connections)
    degrees = dict(component_graph.degree())
    node_colors = [degrees[node] for node in component_graph.nodes()]

    nx.draw_networkx_nodes(
        component_graph, pos,
        node_color=node_colors,
        node_size=50,
        cmap=plt.cm.Reds,
        alpha=0.8,
        ax=ax
    )

    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds,
                                norm=plt.Normalize(vmin=min(node_colors),
                                                   vmax=max(node_colors)))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Number of Connections', rotation=270, labelpad=20)

    # Labels for major hubs (stations with many connections)
    hub_threshold = sorted(degrees.values(), reverse=True)[min(10, len(degrees)-1)]
    labels = {}
    for node in component_graph.nodes():
        if degrees[node] >= hub_threshold:
            labels[node] = component_graph.nodes[node]['city_name']

    if labels:
        nx.draw_networkx_labels(
            component_graph, pos,
            labels,
            font_size=8,
            font_color='darkred',
            font_weight='bold',
            ax=ax
        )

    ax.set_title('SNCF Railway Network - Main Connected Component\n(Node color = number of connections)',
                 fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {output_file}")
    print()

    plt.show()


def main():
    print("=" * 70)
    print("SNCF RAILWAY NETWORK VISUALIZATION")
    print("=" * 70)
    print()

    # Load graph
    print("Loading railway network graph...")
    G = build_railway_graph()
    print()

    # Validate
    results = validate_graph(G)
    print(f"Network Statistics:")
    print(f"  Total stations: {results['num_nodes']}")
    print(f"  Total connections: {results['num_edges']}")
    print(f"  Connected components: {results['num_components']}")
    print(f"  Orphaned stations: {len(results['orphaned_nodes'])}")
    print()

    # Create visualizations
    print("=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    print()

    # Visualization 1: Full network
    print("1. Full network (all stations with GPS)...")
    visualize_network(G, 'railway_network_full.png', show_labels=False)

    # Visualization 2: Largest component only
    print("2. Largest connected component...")
    visualize_largest_component(G, 'railway_network_main.png')

    print("=" * 70)
    print("VISUALIZATION COMPLETED")
    print("=" * 70)
    print()
    print("Generated files:")
    print("  - railway_network_full.png (complete network)")
    print("  - railway_network_main.png (main component)")


if __name__ == "__main__":
    main()
