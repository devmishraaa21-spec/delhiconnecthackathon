"""Road network graph construction and traffic weight management."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import networkx as nx

# Free-flow speeds (km/h) by road type
FREE_FLOW_SPEEDS: dict[str, float] = {
    "expressway": 60.0,
    "arterial": 40.0,
    "local": 30.0,
    "congested_zone": 15.0,
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in metres between two lat/lon coordinates."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


def _find_or_add_node(
    lat: float,
    lon: float,
    nodes_list: list[tuple[int, float, float]],
    threshold_m: float = 50.0,
) -> int:
    """Find an existing node within threshold_m, or create a new node id."""
    for nid, nlat, nlon in nodes_list:
        if haversine_m(lat, lon, nlat, nlon) <= threshold_m:
            return nid

    new_id = len(nodes_list)
    nodes_list.append((new_id, lat, lon))
    return new_id


def build_graph(segments: list) -> nx.DiGraph:
    """Build a NetworkX directed graph from road segments.

    Nodes represent geographic endpoints (points within 50m are merged).
    Edges carry attributes:
        segment_id      : str
        distance        : float (metres)
        free_flow_speed : float (km/h)
        current_speed   : float (km/h)
        road_type       : str
        road_name       : str
        weight          : float (estimated travel time in hours)
    """
    G = nx.DiGraph()
    # List of (node_id, lat, lon)
    registered_nodes: list[tuple[int, float, float]] = []

    for seg in segments:
        u = _find_or_add_node(seg.start_lat, seg.start_lon, registered_nodes, threshold_m=50.0)
        v = _find_or_add_node(seg.end_lat, seg.end_lon, registered_nodes, threshold_m=50.0)

        # Ensure node attributes are set
        if u not in G.nodes:
            _, ulat, ulon = registered_nodes[u]
            G.add_node(u, lat=ulat, lon=ulon)
        if v not in G.nodes:
            _, vlat, vlon = registered_nodes[v]
            G.add_node(v, lat=vlat, lon=vlon)

        dist_m = float(seg.length_m)
        ff_speed = FREE_FLOW_SPEEDS.get(seg.road_type, 30.0)
        weight_hours = (dist_m / 1000.0) / max(ff_speed, 1.0)

        edge_attrs = {
            "segment_id": seg.segment_id,
            "distance": dist_m,
            "free_flow_speed": ff_speed,
            "current_speed": ff_speed,
            "road_type": seg.road_type,
            "road_name": seg.road_name,
            "weight": weight_hours,
        }

        # Delhi roads are bidirectional bus corridors
        G.add_edge(u, v, **edge_attrs)
        G.add_edge(v, u, **edge_attrs)

    return G


def update_weights(G: nx.DiGraph, traffic_model: Any) -> nx.DiGraph:
    """Update edge weights using real-time traffic speeds.

    Weight = travel_time = distance_km / current_speed_kmh (hours).
    """
    speeds = traffic_model.get_all_speeds() if hasattr(traffic_model, "get_all_speeds") else {}

    for u, v, data in G.edges(data=True):
        sid = data.get("segment_id", "")
        if sid in speeds:
            speed_kmh = float(speeds[sid])
        elif hasattr(traffic_model, "get_segment_speed"):
            speed_kmh = float(traffic_model.get_segment_speed(sid))
        else:
            speed_kmh = data.get("free_flow_speed", 30.0)

        # Clamp speed to avoid division by zero
        speed_kmh = max(2.0, speed_kmh)
        data["current_speed"] = speed_kmh

        dist_km = data.get("distance", 1000.0) / 1000.0
        data["weight"] = dist_km / speed_kmh

    return G
