"""
3D Pydeck visualization for the Delhi Bus Traffic Model.
Provides 3D extruded congestion columns, dynamic 3D road segment paths,
live bus fleet scatter, and origin-destination arc flows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

try:
    import pydeck as pdk
except ImportError:
    pdk = None

DELHI_CENTER = [28.6139, 77.2090]

# Congestion RGB colors for Pydeck [R, G, B, Alpha]
CONGESTION_PDK_COLORS = {
    "free_flow": [46, 204, 113, 220],    # Emerald Green
    "moderate": [241, 196, 15, 220],     # Amber Gold
    "heavy": [230, 126, 34, 230],        # Orange
    "gridlock": [231, 76, 60, 240],      # Crimson Red
    "severe": [231, 76, 60, 240],
}


def pydeck_available() -> bool:
    """Check whether pydeck is installed."""
    return pdk is not None


def create_3d_congestion_view(
    heatmap_data: list[dict],
    bus_telemetry: Optional[pd.DataFrame] = None,
    segments: Optional[list] = None,
    traffic_model: Optional[Any] = None,
    route_geojson: Optional[dict] = None,
    dark_mode: bool = True,
    center: Optional[list] = None,
) -> "pdk.Deck | None":
    """
    Create a high-impact 3D Pydeck map with:
      - 3D HexagonLayer showing congestion intensity as extruded columns
      - 3D PathLayer rendering Delhi's road network colored by real-time speed
      - 3D PathLayer for the planned optimal route (glowing neon ribbon)
      - ScatterplotLayer showing live bus fleet positions with real-time speed color
      - ArcLayer showing major bus corridor flows across Delhi

    Parameters
    ----------
    heatmap_data : list[dict]
        Each dict has keys: lat, lon, intensity (0-1 float).
    bus_telemetry : pd.DataFrame, optional
        Live bus telemetry with columns: bus_id, lat, lon, speed, route_id.
    segments : list, optional
        List of RoadSegment objects.
    traffic_model : TrafficModel, optional
        Current traffic speed and congestion model.
    route_geojson : dict, optional
        GeoJSON dict of the calculated A* route.
    dark_mode : bool
        Whether to use dark map style.

    Returns
    -------
    pdk.Deck or None if pydeck is not available.
    """
    if pdk is None:
        return None

    layers = []
    map_style = "dark" if dark_mode else "light"

    # --- 1. 3D Road Network (PathLayer) ---
    if segments:
        segment_paths = []
        for seg in segments:
            level = "free_flow"
            speed_val = 30.0
            if traffic_model:
                try:
                    level = traffic_model.get_congestion_level(seg.segment_id)
                    speed_val = traffic_model.get_segment_speed(seg.segment_id)
                except Exception:
                    pass

            color = CONGESTION_PDK_COLORS.get(level.lower().replace(" ", "_"), [46, 204, 113, 200])
            segment_paths.append({
                "road_name": seg.road_name,
                "speed": f"{speed_val:.1f} km/h",
                "congestion": level.replace("_", " ").title(),
                "path": [
                    [seg.start_lon, seg.start_lat],
                    [seg.end_lon, seg.end_lat],
                ],
                "color": color,
                "width": 5 if level in ["heavy", "gridlock", "severe"] else 3,
            })

        if segment_paths:
            road_df = pd.DataFrame(segment_paths)
            road_df["tooltip_title"] = "🛣️ " + road_df["road_name"]
            road_df["tooltip_details"] = "Speed: " + road_df["speed"] + " • State: " + road_df["congestion"]
            road_layer = pdk.Layer(
                "PathLayer",
                data=road_df,
                get_path="path",
                get_color="color",
                get_width="width",
                width_min_pixels=3,
                width_max_pixels=8,
                pickable=True,
                auto_highlight=True,
            )
            layers.append(road_layer)

    # --- 2. 3D Planned Route Ribbon (PathLayer) ---
    if route_geojson and "features" in route_geojson and route_geojson["features"]:
        feature = route_geojson["features"][0]
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])
        if coords and len(coords) >= 2:
            eta_val = feature.get("properties", {}).get("eta_minutes", 0.0)
            dist_val = feature.get("properties", {}).get("distance_km", 0.0)
            route_df = pd.DataFrame([{
                "path": coords,
                "name": "⚡ Planned Optimal Route",
                "tooltip_title": "⚡ Planned Optimal Route",
                "tooltip_details": f"Distance: {dist_val:.1f} km • Dynamic ETA: {eta_val:.0f} min",
            }])
            route_layer = pdk.Layer(
                "PathLayer",
                data=route_df,
                get_path="path",
                get_color=[0, 240, 255, 255],
                width_min_pixels=7,
                width_max_pixels=14,
                pickable=True,
                auto_highlight=True,
            )
            layers.append(route_layer)

    # --- 3. 3D Extruded Hexagon Congestion Columns ---
    if heatmap_data:
        congestion_df = pd.DataFrame(heatmap_data)
        rows = []
        for _, row in congestion_df.iterrows():
            intensity = row.get("intensity", 0.5)
            # Repeat points proportional to congestion intensity to form taller pillars
            repeat = max(1, int(intensity * 10))
            for _ in range(repeat):
                rows.append({"lat": row["lat"], "lon": row["lon"]})
        hex_df = pd.DataFrame(rows)

        if not hex_df.empty:
            hex_layer = pdk.Layer(
                "HexagonLayer",
                data=hex_df,
                get_position=["lon", "lat"],
                radius=320,
                elevation_scale=70,
                elevation_range=[0, 1600],
                extruded=True,
                coverage=0.88,
                auto_highlight=True,
                color_range=[
                    [44, 186, 112, 190],   # Emerald Green
                    [241, 196, 15, 200],   # Yellow
                    [230, 126, 34, 210],   # Amber Orange
                    [231, 76, 60, 220],    # Red
                    [192, 57, 43, 235],    # Crimson
                    [130, 15, 15, 245],    # Deep Gridlock
                ],
                pickable=True,
            )
            layers.append(hex_layer)

    # --- 4. Live Bus Fleet (ScatterplotLayer) ---
    if bus_telemetry is not None and len(bus_telemetry) > 0:
        bus_df = bus_telemetry.copy()
        lat_col = "lat" if "lat" in bus_df.columns else "latitude"
        lon_col = "lon" if "lon" in bus_df.columns else "longitude"

        if lat_col in bus_df.columns and lon_col in bus_df.columns:
            bus_df = bus_df.dropna(subset=[lat_col, lon_col])

            # Deduplicate to latest ping per vehicle
            if "bus_id" in bus_df.columns:
                if "timestamp" in bus_df.columns:
                    bus_df = bus_df.sort_values("timestamp").groupby("bus_id").last().reset_index()
                else:
                    bus_df = bus_df.groupby("bus_id").last().reset_index()

            if len(bus_df) > 550:
                bus_df = bus_df.tail(550)

            def speed_to_rgba(spd):
                if spd >= 22.0:
                    return [34, 197, 94, 230]    # Green
                elif spd >= 10.0:
                    return [234, 179, 8, 230]    # Amber
                else:
                    return [239, 68, 68, 240]    # Red (slow/idle)

            bus_df["_color"] = bus_df.get("speed", pd.Series([0.0]*len(bus_df))).apply(speed_to_rgba)
            bus_df["speed_str"] = bus_df.get("speed", pd.Series([0.0]*len(bus_df))).apply(lambda s: f"{s:.1f} km/h")
            bus_df["tooltip_title"] = "🚌 Bus #" + bus_df["bus_id"].astype(str) + " (Route " + bus_df["route_id"].astype(str) + ")"
            bus_df["tooltip_details"] = "Live Speed: " + bus_df["speed_str"]

            scatter = pdk.Layer(
                "ScatterplotLayer",
                data=bus_df,
                get_position=[lon_col, lat_col],
                get_color="_color",
                get_radius=130,
                radius_min_pixels=4,
                radius_max_pixels=14,
                pickable=True,
                auto_highlight=True,
            )
            layers.append(scatter)

    # --- 5. Major Transit Corridor Flows (ArcLayer) ---
    arc_data = pd.DataFrame([
        {"name": "Rohini ↔ Connaught Place", "src_lat": 28.715, "src_lon": 77.118, "dst_lat": 28.631, "dst_lon": 77.217, "count": 85},
        {"name": "Dwarka ↔ Connaught Place", "src_lat": 28.552, "src_lon": 77.058, "dst_lat": 28.631, "dst_lon": 77.217, "count": 72},
        {"name": "Anand Vihar ↔ AIIMS", "src_lat": 28.647, "src_lon": 77.316, "dst_lat": 28.567, "dst_lon": 77.210, "count": 68},
        {"name": "ISBT Kashmere Gate ↔ Sarai Kale Khan", "src_lat": 28.667, "src_lon": 77.228, "dst_lat": 28.589, "dst_lon": 77.257, "count": 55},
        {"name": "Nehru Place ↔ ISBT Kashmere Gate", "src_lat": 28.549, "src_lon": 77.253, "dst_lat": 28.667, "dst_lon": 77.228, "count": 48},
        {"name": "Janakpuri ↔ ITO", "src_lat": 28.622, "src_lon": 77.086, "dst_lat": 28.629, "dst_lon": 77.241, "count": 42},
        {"name": "Model Town ↔ AIIMS", "src_lat": 28.715, "src_lon": 77.193, "dst_lat": 28.567, "dst_lon": 77.210, "count": 38},
    ])
    arc_data["tooltip_title"] = "🌐 " + arc_data["name"]
    arc_data["tooltip_details"] = "Corridor Flow: " + arc_data["count"].astype(str) + " buses/hour"

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=arc_data,
        get_source_position=["src_lon", "src_lat"],
        get_target_position=["dst_lon", "dst_lat"],
        get_source_color=[0, 240, 255, 180],
        get_target_color=[255, 0, 128, 180],
        get_width="count / 10",
        pickable=True,
        auto_highlight=True,
    )
    layers.append(arc_layer)

    target_lat = center[0] if center else DELHI_CENTER[0]
    target_lon = center[1] if center else DELHI_CENTER[1]
    view_state = pdk.ViewState(
        latitude=target_lat,
        longitude=target_lon,
        zoom=11.5,
        pitch=58,
        bearing=-18,
    )

    tooltip = {
        "html": """
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size:12px; line-height:1.4;">
            <div style="font-weight:700; color:#38bdf8; font-size:13px;">{tooltip_title}</div>
            <div style="color:#e2e8f0; font-size:11px; margin-top:3px;">{tooltip_details}</div>
        </div>
        """,
        "style": {
            "backgroundColor": "rgba(15, 23, 42, 0.92)",
            "color": "#f8fafc",
            "fontSize": "12px",
            "padding": "8px 12px",
            "borderRadius": "8px",
            "border": "1px solid rgba(255, 107, 53, 0.4)",
            "boxShadow": "0 8px 24px rgba(0,0,0,0.6)",
        },
    }

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=map_style,
    )


def create_bus_flow_arcs(
    bus_routes: list[dict],
    bus_stops: list[dict],
) -> "pdk.Deck | None":
    """
    Create a 3D arc visualization of bus routes connecting their stop sequences.
    """
    if pdk is None:
        return None

    stop_lookup = {s["stop_id"]: s for s in bus_stops}
    arc_rows = []

    for route in bus_routes:
        stop_ids = route.get("stop_ids", [])
        for i in range(len(stop_ids) - 1):
            src = stop_lookup.get(stop_ids[i])
            dst = stop_lookup.get(stop_ids[i + 1])
            if src and dst:
                arc_rows.append({
                    "route": route.get("name", route.get("route_id", "")),
                    "src_lat": src["lat"],
                    "src_lon": src["lon"],
                    "dst_lat": dst["lat"],
                    "dst_lon": dst["lon"],
                })

    if not arc_rows:
        return None

    arc_df = pd.DataFrame(arc_rows)

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=arc_df,
        get_source_position=["src_lon", "src_lat"],
        get_target_position=["dst_lon", "dst_lat"],
        get_source_color=[0, 240, 255, 170],
        get_target_color=[255, 107, 53, 170],
        get_width=2.8,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=DELHI_CENTER[0],
        longitude=DELHI_CENTER[1],
        zoom=11.0,
        pitch=50,
        bearing=5,
    )

    return pdk.Deck(
        layers=[arc_layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip={"text": "{route}"},
    )
