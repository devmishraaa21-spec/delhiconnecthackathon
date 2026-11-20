"""Journey planner with A* routing over the Delhi road network graph."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx


# ---------------------------------------------------------------------------
# Haversine utility
# ---------------------------------------------------------------------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in **metres** between two points."""
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Nearest-node lookup
# ---------------------------------------------------------------------------

def find_nearest_node(G: nx.DiGraph, lat: float, lon: float) -> Any:
    """Return the node id in *G* closest to the given coordinate."""
    best_node = None
    best_dist = float("inf")
    for node, data in G.nodes(data=True):
        nlat = data.get("lat", 0.0)
        nlon = data.get("lon", 0.0)
        d = haversine(lat, lon, nlat, nlon)
        if d < best_dist:
            best_dist = d
            best_node = node
    return best_node


# ---------------------------------------------------------------------------
# A* heuristic
# ---------------------------------------------------------------------------

def _astar_heuristic(G: nx.DiGraph, target_node: Any):
    """Return a heuristic function for A* that estimates travel time (hours)
    from any node to *target_node* using haversine distance and an optimistic
    speed of 60 km/h (expressway speed)."""
    target_data = G.nodes[target_node]
    tlat = target_data.get("lat", 0.0)
    tlon = target_data.get("lon", 0.0)

    def heuristic(u: Any, v: Any) -> float:  # noqa: ARG001 – NetworkX passes (u, target)
        nd = G.nodes[u]
        dist_m = haversine(nd.get("lat", 0.0), nd.get("lon", 0.0), tlat, tlon)
        # Optimistic travel time in hours (60 km/h)
        return (dist_m / 1000.0) / 60.0

    return heuristic


# ---------------------------------------------------------------------------
# Route planning
# ---------------------------------------------------------------------------

def plan_route(
    G: nx.DiGraph,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> Dict[str, Any]:
    """Plan a route using A* with a haversine heuristic.

    Returns
    -------
    dict with keys:
        path          – list of (lat, lon) tuples along the route
        distance_km   – total route distance in kilometres
        eta_minutes   – estimated travel time in minutes
        segments      – list of segment_id strings traversed
        congestion_summary – human-readable congestion description
    """
    src = find_nearest_node(G, start_lat, start_lon)
    dst = find_nearest_node(G, end_lat, end_lon)

    if src is None or dst is None:
        return {
            "path": [],
            "distance_km": 0.0,
            "eta_minutes": 0.0,
            "segments": [],
            "congestion_summary": "No route found — graph has no nodes.",
        }

    if src == dst:
        nd = G.nodes[src]
        return {
            "path": [(nd.get("lat", 0.0), nd.get("lon", 0.0))],
            "distance_km": 0.0,
            "eta_minutes": 0.0,
            "segments": [],
            "congestion_summary": "Origin and destination are the same node.",
        }

    heuristic = _astar_heuristic(G, dst)

    try:
        node_path = nx.astar_path(G, src, dst, heuristic=heuristic, weight="weight")
    except nx.NetworkXNoPath:
        return {
            "path": [],
            "distance_km": 0.0,
            "eta_minutes": 0.0,
            "segments": [],
            "congestion_summary": "No path found between the given coordinates.",
        }

    # Extract route details
    path_coords: list[tuple[float, float]] = []
    total_distance_m = 0.0
    total_time_h = 0.0
    segment_ids: list[str] = []
    congestion_counts: dict[str, int] = {
        "free_flow": 0,
        "moderate": 0,
        "heavy": 0,
        "gridlock": 0,
    }

    for node in node_path:
        nd = G.nodes[node]
        path_coords.append((nd.get("lat", 0.0), nd.get("lon", 0.0)))

    for i in range(len(node_path) - 1):
        u, v = node_path[i], node_path[i + 1]
        edge_data = G.edges[u, v]
        total_distance_m += edge_data.get("distance", 0.0)
        total_time_h += edge_data.get("weight", 0.0)
        seg_id = edge_data.get("segment_id", "")
        if seg_id:
            segment_ids.append(seg_id)

        # Classify congestion on this edge
        speed = edge_data.get("current_speed", 30.0)
        ff = edge_data.get("free_flow_speed", 40.0)
        if ff > 0:
            ratio = speed / ff
            if ratio >= 0.75:
                congestion_counts["free_flow"] += 1
            elif ratio >= 0.50:
                congestion_counts["moderate"] += 1
            elif ratio >= 0.25:
                congestion_counts["heavy"] += 1
            else:
                congestion_counts["gridlock"] += 1

    total_edges = max(sum(congestion_counts.values()), 1)
    summary_parts: list[str] = []
    for level in ("gridlock", "heavy", "moderate", "free_flow"):
        cnt = congestion_counts[level]
        if cnt > 0:
            pct = round(100 * cnt / total_edges)
            summary_parts.append(f"{pct}% {level.replace('_', ' ')}")
    congestion_summary = ", ".join(summary_parts) if summary_parts else "No data"

    return {
        "path": path_coords,
        "distance_km": round(total_distance_m / 1000.0, 2),
        "eta_minutes": round(total_time_h * 60.0, 1),
        "segments": segment_ids,
        "congestion_summary": congestion_summary,
    }


# ---------------------------------------------------------------------------
# GeoJSON export
# ---------------------------------------------------------------------------

def get_route_geojson(route: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a route dict (from plan_route) to a GeoJSON FeatureCollection.

    The route is represented as a LineString geometry with properties for
    distance, ETA, and congestion summary.
    """
    coords = route.get("path", [])
    # GeoJSON uses [lon, lat] order
    geojson_coords = [[lon, lat] for lat, lon in coords]

    feature: dict[str, Any] = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": geojson_coords,
        },
        "properties": {
            "distance_km": route.get("distance_km", 0.0),
            "eta_minutes": route.get("eta_minutes", 0.0),
            "segments": route.get("segments", []),
            "congestion_summary": route.get("congestion_summary", ""),
        },
    }

    return {
        "type": "FeatureCollection",
        "features": [feature],
    }
