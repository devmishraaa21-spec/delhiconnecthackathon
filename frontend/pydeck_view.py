"""
3D Pydeck visualization for the Delhi Bus Traffic Model.
Provides 3D congestion columns (HexagonLayer) and origin-destination arc flows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

try:
    import pydeck as pdk
except ImportError:
    pdk = None

DELHI_CENTER = [28.6139, 77.2090]


def pydeck_available() -> bool:
    """Check whether pydeck is installed."""
    return pdk is not None


def create_3d_congestion_view(
    heatmap_data: list[dict],
    bus_telemetry: Optional[pd.DataFrame] = None,
    dark_mode: bool = True,
) -> "pdk.Deck | None":
    """
    Create a 3D Pydeck map with:
      - HexagonLayer showing congestion intensity as 3D columns
      - ScatterplotLayer showing live bus positions
      - ArcLayer showing major bus corridor flows

    Parameters
    ----------
    heatmap_data : list[dict]
        Each dict has keys: lat, lon, intensity (0-1 float).
    bus_telemetry : pd.DataFrame, optional
        Live bus telemetry with columns: bus_id, lat, lon, speed, route_id.
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

    # --- 3D Hexagon Congestion Columns ---
    if heatmap_data:
        congestion_df = pd.DataFrame(heatmap_data)
        # Duplicate high-intensity points to amplify hex elevation
        rows = []
        for _, row in congestion_df.iterrows():
            intensity = row.get("intensity", 0.5)
            repeat = max(1, int(intensity * 8))
            for _ in range(repeat):
                rows.append({"lat": row["lat"], "lon": row["lon"]})
        hex_df = pd.DataFrame(rows)

        hex_layer = pdk.Layer(
            "HexagonLayer",
            data=hex_df,
            get_position=["lon", "lat"],
            radius=350,
            elevation_scale=60,
            elevation_range=[0, 1200],
            extruded=True,
            coverage=0.85,
            auto_highlight=True,
            color_range=[
                [44, 186, 112],   # green
                [241, 196, 15],   # yellow
                [230, 126, 34],   # orange
                [231, 76, 60],    # red
                [192, 57, 43],    # dark red
                [120, 20, 20],    # very dark
            ],
            pickable=True,
        )
        layers.append(hex_layer)

    # --- Scatterplot: Live Bus Positions ---
    if bus_telemetry is not None and len(bus_telemetry) > 0:
        bus_df = bus_telemetry.copy()
        lat_col = "lat" if "lat" in bus_df.columns else "latitude"
        lon_col = "lon" if "lon" in bus_df.columns else "longitude"

        if lat_col in bus_df.columns and lon_col in bus_df.columns:
            bus_df = bus_df.dropna(subset=[lat_col, lon_col])

            # Keep latest per bus
            if "bus_id" in bus_df.columns and "timestamp" in bus_df.columns:
                bus_df = bus_df.sort_values("timestamp").groupby("bus_id").last().reset_index()

            # Limit for performance
            if len(bus_df) > 400:
                bus_df = bus_df.tail(400)

            # Speed to color
            def speed_to_color(spd):
                if spd >= 22:
                    return [22, 163, 74, 200]   # green
                elif spd >= 10:
                    return [217, 119, 6, 200]   # orange
                else:
                    return [220, 38, 38, 200]   # red

            bus_df["_color"] = bus_df.get("speed", pd.Series([0]*len(bus_df))).apply(speed_to_color)

            scatter = pdk.Layer(
                "ScatterplotLayer",
                data=bus_df,
                get_position=[lon_col, lat_col],
                get_color="_color",
                get_radius=120,
                radius_min_pixels=3,
                radius_max_pixels=12,
                pickable=True,
                auto_highlight=True,
            )
            layers.append(scatter)

    # --- Arc Layer: Major OD Bus Corridor Flows ---
    # Static arcs representing the busiest corridors in Delhi
    arc_data = pd.DataFrame([
        {"name": "Rohini ↔ CP", "src_lat": 28.715, "src_lon": 77.118, "dst_lat": 28.631, "dst_lon": 77.217, "count": 85},
        {"name": "Dwarka ↔ CP", "src_lat": 28.552, "src_lon": 77.058, "dst_lat": 28.631, "dst_lon": 77.217, "count": 72},
        {"name": "Anand Vihar ↔ AIIMS", "src_lat": 28.647, "src_lon": 77.316, "dst_lat": 28.567, "dst_lon": 77.210, "count": 68},
        {"name": "ISBT KG ↔ Sarai Kale Khan", "src_lat": 28.667, "src_lon": 77.228, "dst_lat": 28.589, "dst_lon": 77.257, "count": 55},
        {"name": "Nehru Place ↔ ISBT KG", "src_lat": 28.549, "src_lon": 77.253, "dst_lat": 28.667, "dst_lon": 77.228, "count": 48},
        {"name": "Janakpuri ↔ ITO", "src_lat": 28.622, "src_lon": 77.086, "dst_lat": 28.629, "dst_lon": 77.241, "count": 42},
        {"name": "Model Town ↔ AIIMS", "src_lat": 28.715, "src_lon": 77.193, "dst_lat": 28.567, "dst_lon": 77.210, "count": 38},
    ])

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

    view_state = pdk.ViewState(
        latitude=DELHI_CENTER[0],
        longitude=DELHI_CENTER[1],
        zoom=11,
        pitch=55,
        bearing=-15,
    )

    tooltip = {
        "html": "<b>{name}</b><br/>Buses/hr: {count}" if "name" in (arc_data.columns if len(arc_data) > 0 else []) else "",
        "style": {
            "backgroundColor": "#1e293b",
            "color": "#f1f5f9",
            "fontSize": "12px",
            "padding": "4px 8px",
            "borderRadius": "4px",
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
        get_source_color=[0, 240, 255, 160],
        get_target_color=[255, 107, 53, 160],
        get_width=2.5,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=DELHI_CENTER[0],
        longitude=DELHI_CENTER[1],
        zoom=11,
        pitch=45,
        bearing=0,
    )

    return pdk.Deck(
        layers=[arc_layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip={"text": "{route}"},
    )
