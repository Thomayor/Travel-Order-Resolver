#!/usr/bin/env python3
"""
Demo: Visualize railway route with matplotlib

Shows the found route on a map of France with stations and connections.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pathfinding.algorithms import dijkstra, find_route
from src.pathfinding.graph_loader import get_or_build_graph, get_station_info


def visualize_route(
    origin_uic: str,
    destination_uic: str,
    show_all_network: bool = True
):
    """
    Visualize a route on a map using matplotlib.

    Args:
        origin_uic: Origin station UIC code
        destination_uic: Destination station UIC code
        show_all_network: If True, show all stations and connections
    """
    # Load graph
    print("Loading railway network...")
    graph = get_or_build_graph()
    print()

    # Find route
    print(f"Finding route from {origin_uic} to {destination_uic}...")
    try:
        path, total_time = dijkstra(graph, origin_uic, destination_uic)
        print(f"[OK] Route found: {len(path)} stations, {total_time} minutes ({total_time/60:.1f}h)")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return

    # Get station info for path
    route_stations = []
    for uic in path:
        info = get_station_info(graph, uic)
        if info and info['latitude'] and info['longitude']:
            route_stations.append({
                'uic': uic,
                'name': info['station_name'],
                'lat': info['latitude'],
                'lon': info['longitude']
            })

    print()
    print("Route:")
    for i, station in enumerate(route_stations):
        print(f"  {i+1}. {station['name']}")

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))

    # Draw all network if requested
    if show_all_network:
        print("\nDrawing network...")

        # Draw all connections (light gray lines)
        for edge in graph.edges():
            origin_info = get_station_info(graph, edge[0])
            dest_info = get_station_info(graph, edge[1])

            if (origin_info and dest_info and
                origin_info['latitude'] and origin_info['longitude'] and
                dest_info['latitude'] and dest_info['longitude']):

                ax.plot(
                    [origin_info['longitude'], dest_info['longitude']],
                    [origin_info['latitude'], dest_info['latitude']],
                    color='lightgray',
                    linewidth=0.3,
                    alpha=0.3,
                    zorder=1
                )

        # Draw all stations (small gray dots)
        all_stations = []
        for node in graph.nodes():
            info = get_station_info(graph, node)
            if info and info['latitude'] and info['longitude']:
                all_stations.append((info['longitude'], info['latitude']))

        if all_stations:
            lons, lats = zip(*all_stations)
            ax.scatter(lons, lats, c='lightgray', s=1, alpha=0.5, zorder=2)

    # Draw route connections (thick blue lines)
    print("Drawing route...")
    for i in range(len(route_stations) - 1):
        origin = route_stations[i]
        dest = route_stations[i + 1]

        ax.plot(
            [origin['lon'], dest['lon']],
            [origin['lat'], dest['lat']],
            color='blue',
            linewidth=3,
            alpha=0.8,
            zorder=4
        )

    # Draw route stations
    route_lons = [s['lon'] for s in route_stations]
    route_lats = [s['lat'] for s in route_stations]

    # Origin (green)
    ax.scatter(
        route_lons[0], route_lats[0],
        color='green',
        s=200,
        marker='o',
        edgecolors='white',
        linewidth=2,
        zorder=5,
        label='Départ'
    )

    # Destination (red)
    ax.scatter(
        route_lons[-1], route_lats[-1],
        color='red',
        s=200,
        marker='o',
        edgecolors='white',
        linewidth=2,
        zorder=5,
        label='Arrivée'
    )

    # Intermediate stops (orange)
    if len(route_stations) > 2:
        ax.scatter(
            route_lons[1:-1], route_lats[1:-1],
            color='orange',
            s=100,
            marker='o',
            edgecolors='white',
            linewidth=1.5,
            zorder=5,
            label='Arrêts'
        )

    # Add labels for route stations
    for station in route_stations:
        ax.annotate(
            station['name'],
            (station['lon'], station['lat']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=9,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
            zorder=6
        )

    # Set bounds (France)
    ax.set_xlim(-5.5, 10)
    ax.set_ylim(41, 51.5)

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)

    origin_name = route_stations[0]['name']
    dest_name = route_stations[-1]['name']
    ax.set_title(
        f'Itineraire : {origin_name} -> {dest_name}\n'
        f'{len(path)} gares - {total_time} minutes ({total_time/60:.1f}h)',
        fontsize=14,
        fontweight='bold',
        pad=20
    )

    # Legend
    ax.legend(loc='lower left', fontsize=10)

    # Stats box
    stats_text = (
        f"Itineraire calcule:\n"
        f"- Depart: {origin_name}\n"
        f"- Arrivee: {dest_name}\n"
        f"- Gares: {len(path)}\n"
        f"- Arrets: {len(path) - 2}\n"
        f"- Duree: {total_time} min ({total_time/60:.1f}h)"
    )

    ax.text(
        0.98, 0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
        zorder=7
    )

    plt.tight_layout()

    # Save
    output_file = f"route_{origin_uic}_{destination_uic}.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Carte sauvegardee : {output_file}")

    # Show
    plt.show()


if __name__ == "__main__":
    print("=" * 70)
    print("VISUALISATION D'ITINERAIRE FERROVIAIRE")
    print("=" * 70)
    print()

    # Exemples de trajets
    routes = [
        ('87686006', '87723197', 'Paris Gare de Lyon -> Lyon Part Dieu'),
        ('87611004', '87751008', 'Toulouse -> Marseille'),
        ('87271023', '87723197', 'Paris Gare du Nord -> Lyon'),
    ]

    print("Trajets disponibles :")
    for i, (origin, dest, desc) in enumerate(routes, 1):
        print(f"  {i}. {desc}")
    print()

    # Choix utilisateur
    try:
        choice = input("Choisissez un trajet (1-3) ou appuyez sur Entrée pour trajet 1 : ").strip()
        if not choice:
            choice = "1"
        idx = int(choice) - 1

        if idx < 0 or idx >= len(routes):
            print("Choix invalide, utilisation du trajet 1")
            idx = 0

        origin, dest, desc = routes[idx]
        print(f"\n> Trajet selectionne : {desc}")
        print()

        # Afficher le reseau complet ?
        show_network = input("Afficher tout le reseau en arriere-plan ? (o/N) : ").strip().lower()
        show_all = show_network == 'o'

        print()
        print("=" * 70)
        print()

        # Visualiser
        visualize_route(origin, dest, show_all_network=show_all)

    except KeyboardInterrupt:
        print("\n\nAnnule par l'utilisateur")
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
