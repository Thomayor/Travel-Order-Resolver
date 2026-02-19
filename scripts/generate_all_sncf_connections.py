#!/usr/bin/env python3
"""
Generate SNCF connections from real GTFS data

Parses data/raw/sncf/gtfs/stop_times.txt to extract actual segment durations
between consecutive stops on each trip.  This replaces the previous approach
of generating synthetic connections from geographical proximity.

Output: data/processed/sncf/connections_final_fixed.csv
  columns: origin_uic, destination_uic, distance_km, duration_minutes,
           line_code, line_status, origin_name, destination_name,
           trip_count, source

Usage:
    python scripts/generate_all_sncf_connections.py
"""

import sys
import re
import pandas as pd
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

GTFS_DIR   = Path("data/raw/sncf/gtfs")
OUT_FILE   = Path("data/processed/sncf/connections_final_fixed.csv")
CACHE_FILE = Path("models/train_network.pkl")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_gtfs_time(t: str) -> int:
    """Convert HH:MM:SS (can exceed 24h) to total seconds."""
    h, m, s = t.strip().split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def extract_uic(stop_id: str) -> str | None:
    """
    Extract 8-digit UIC code from GTFS stop_id.

    Examples:
        'StopPoint:OCENavette-87571240'  -> '87571240'
        'StopPoint:OCETGV INOUI-87756056' -> '87756056'
        'StopArea:OCE87571240'           -> '87571240'
    """
    m = re.search(r"(\d{8})$", stop_id)
    return m.group(1) if m else None


def load_route_types(gtfs_dir: Path) -> dict[str, str]:
    """
    Return {route_id: line_code} mapping.

    GTFS route_type: 2 = Rail.  We classify by combining route_short_name
    AND route_long_name, since TGV lines often have numeric short names
    (e.g. "001G") but "TGV" appears in route_long_name.
    """
    routes = pd.read_csv(gtfs_dir / "routes.txt")
    trips  = pd.read_csv(gtfs_dir / "trips.txt")[["trip_id", "route_id"]]

    def classify(row) -> str:
        short = str(row.get("route_short_name", "")).upper() if pd.notna(row.get("route_short_name")) else ""
        long_name = str(row.get("route_long_name", "")).upper() if pd.notna(row.get("route_long_name")) else ""
        combined = short + " " + long_name
        if any(k in combined for k in ("TGV", "INOUI", "OUIGO", "EUROSTAR", "THALYS")):
            return "TGV"
        if any(k in combined for k in ("IC", "INTERCIT", "INTERCITES")):
            return "IC"
        if "TER" in combined:
            return "TER"
        return "TRAIN"

    routes["line_code"] = routes.apply(classify, axis=1)
    route_map = dict(zip(routes["route_id"], routes["line_code"]))
    trip_map  = dict(zip(trips["trip_id"], trips["route_id"]))
    return route_map, trip_map


def build_connections_from_gtfs(gtfs_dir: Path) -> pd.DataFrame:
    """
    Parse stop_times.txt and extract one row per consecutive (A, B) segment.

    For each trip, for each pair of consecutive stops:
        duration_minutes = departure_time[n+1] - departure_time[n]

    Returns DataFrame with columns:
        origin_uic, destination_uic, duration_minutes, line_code, trip_count
    """
    print("  Loading stop_times.txt ...")
    st = pd.read_csv(
        gtfs_dir / "stop_times.txt",
        usecols=["trip_id", "departure_time", "stop_id", "stop_sequence"],
        dtype={"stop_sequence": int},
    )

    # Extract UIC from stop_id
    st["uic"] = st["stop_id"].apply(extract_uic)
    st = st[st["uic"].notna()].copy()

    # Parse departure time to seconds
    st["dep_sec"] = st["departure_time"].apply(parse_gtfs_time)

    # Sort
    st.sort_values(["trip_id", "stop_sequence"], inplace=True)

    print(f"  {len(st):,} stop_times rows after UIC filtering")

    # Route type lookup
    print("  Loading route types ...")
    route_map, trip_map = load_route_types(gtfs_dir)

    def get_line_code(trip_id: str) -> str:
        return route_map.get(trip_map.get(trip_id, ""), "TRAIN")

    # Build segment list
    print("  Extracting segments ...")
    records = []

    # Group by trip — vectorised shift is much faster than iterrows
    grp = st.groupby("trip_id", sort=False)

    for trip_id, group in grp:
        group = group.reset_index(drop=True)
        line_code = get_line_code(trip_id)

        for i in range(len(group) - 1):
            orig_uic = group.at[i,   "uic"]
            dest_uic = group.at[i+1, "uic"]
            if orig_uic == dest_uic:
                continue
            dur_sec = group.at[i+1, "dep_sec"] - group.at[i, "dep_sec"]
            if dur_sec <= 0 or dur_sec > 14400:  # ignore 0 or >4h single segments (allow long TGV)
                continue
            records.append((orig_uic, dest_uic, round(dur_sec / 60, 1), line_code))

    print(f"  {len(records):,} raw segments extracted")

    df = pd.DataFrame(records, columns=["origin_uic", "destination_uic", "duration_minutes", "line_code"])

    # Aggregate: keep median duration per (A, B) pair, count trips
    agg = (
        df.groupby(["origin_uic", "destination_uic", "line_code"])
          .agg(duration_minutes=("duration_minutes", "median"),
               trip_count=("duration_minutes", "count"))
          .reset_index()
    )

    # If multiple line_codes for same (A, B), keep the FASTEST connection
    # This ensures TGV (2h Paris-Lyon) wins over TER (5h) for the same pair
    agg = (
        agg.sort_values("duration_minutes", ascending=True)
           .drop_duplicates(subset=["origin_uic", "destination_uic"])
           .reset_index(drop=True)
    )

    agg["duration_minutes"] = agg["duration_minutes"].round().astype(int)

    # Minimal filter: remove single-trip anomalies (keep trip_count >= 2)
    # No aggressive filtering needed — routing_cost hop penalties prevent
    # zigzags on long routes while keeping small rural TER stops accessible
    filtered = agg[agg["trip_count"] >= 2].copy()

    print(f"  Filtered: {len(agg):,} -> {len(filtered):,} connections (removed single-trip anomalies)")

    return filtered


def enrich_with_station_names(df: pd.DataFrame, gtfs_dir: Path) -> pd.DataFrame:
    """Add origin_name / destination_name columns from stops.txt."""
    stops = pd.read_csv(gtfs_dir / "stops.txt", usecols=["stop_id", "stop_name"])
    stops["uic"] = stops["stop_id"].apply(extract_uic)
    stops = stops[stops["uic"].notna()].drop_duplicates("uic").set_index("uic")
    name_map = stops["stop_name"].to_dict()

    df["origin_name"]      = df["origin_uic"].map(name_map)
    df["destination_name"] = df["destination_uic"].map(name_map)
    return df


def make_bidirectional(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure every (A->B) has a matching (B->A) with the same duration."""
    reverse = df.rename(columns={
        "origin_uic": "destination_uic",
        "destination_uic": "origin_uic",
        "origin_name": "destination_name",
        "destination_name": "origin_name",
    })
    combined = pd.concat([df, reverse], ignore_index=True)
    combined = (
        combined.sort_values("duration_minutes", ascending=True)
                .drop_duplicates(subset=["origin_uic", "destination_uic"])
                .reset_index(drop=True)
    )
    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("SNCF CONNECTIONS — GTFS-based generator")
    print("=" * 70)
    print()

    # 1. Build from GTFS
    print("[1/4] Parsing GTFS stop_times ...")
    df = build_connections_from_gtfs(GTFS_DIR)
    print(f"  {len(df):,} unique directed segments")
    print()

    # 2. Make bidirectional
    print("[2/4] Making bidirectional ...")
    df = make_bidirectional(df)
    print(f"  {len(df):,} connections (bidirectional)")
    print()

    # 3. Enrich with names + add placeholder columns for compatibility
    print("[3/4] Enriching with station names ...")
    df = enrich_with_station_names(df, GTFS_DIR)
    df["distance_km"]  = None   # not in GTFS, left empty
    df["line_status"]  = "GTFS"
    df["source"]       = "gtfs_stop_times"
    print()

    # 4. Save
    print("[4/4] Saving ...")
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    col_order = [
        "origin_uic", "destination_uic", "distance_km", "duration_minutes",
        "line_code", "line_status", "origin_name", "destination_name",
        "trip_count", "source",
    ]
    df[col_order].to_csv(OUT_FILE, index=False, encoding="utf-8")
    print(f"  Saved {len(df):,} connections -> {OUT_FILE}")
    print()

    # Stats
    print("Duration statistics:")
    print(df["duration_minutes"].describe().to_string())
    print()
    print("By line_code:")
    print(df["line_code"].value_counts().to_string())
    print()

    # Rebuild graph cache
    print("=" * 70)
    print("Rebuilding graph cache ...")
    from src.pathfinding.graph_loader import get_or_build_graph
    graph = get_or_build_graph(
        cache_path=str(CACHE_FILE),
        connections_file=str(OUT_FILE),
        force_rebuild=True,
    )
    print(f"Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print()

    # Quick test
    print("Quick test — Nice -> Toulouse:")
    from src.pathfinding.algorithms import dijkstra
    from src.pathfinding.graph_loader import get_station_info
    from src.utils.pipeline import load_city_mapping, map_city_to_uic

    mapping = load_city_mapping()
    nice_uic     = map_city_to_uic("nice", mapping)
    toulouse_uic = map_city_to_uic("toulouse", mapping)

    try:
        path, total_time = dijkstra(graph, nice_uic, toulouse_uic)
        cities = []
        for uic in path:
            info = get_station_info(graph, uic)
            cities.append(info.get("city_name", uic) if info else uic)
        print(f"  {' -> '.join(cities)}")
        print(f"  Total: {total_time:.0f} min ({total_time/60:.1f}h)")
    except Exception as e:
        print(f"  [ERROR] {e}")

    print()
    print("=" * 70)
    print("Done.")
    print("=" * 70)


if __name__ == "__main__":
    main()
