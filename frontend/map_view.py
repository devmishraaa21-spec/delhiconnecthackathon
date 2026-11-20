"""
Map visualization components for the Delhi Bus Traffic Model.
Uses Folium for interactive map rendering within Streamlit.
"""

import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
from typing import Optional, List, Dict
import pandas as pd


# Delhi center coordinates
DELHI_CENTER = [28.6139, 77.2090]
DEFAULT_ZOOM = 12

# Congestion color palette
CONGESTION_COLORS = {
    "free_flow": "#2ecc71",    # green
    "moderate": "#f1c40f",     # yellow
    "heavy": "#e67e22",        # orange
    "severe": "#e74c3c",       # red
}

# Supported tile definitions (free public CDN endpoints with explicit attribution)
TILE_CONFIGS = {
    "Dark Matter (Command Center)": {
        "tiles": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "name": "🌙 Dark Mode (Command Center)",
    },
    "Clean Light": {
        "tiles": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "name": "☀️ Clean Light",
    },
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "attr": "&copy; OpenStreetMap contributors",
        "name": "🗺️ OpenStreetMap",
    },
}
DEFAULT_THEME = "Dark Matter (Command Center)"


def _get_congestion_color(level: str) -> str:
    """Map a congestion level string to a hex color."""
    level_lower = level.lower().replace(" ", "_") if level else "free_flow"
    return CONGESTION_COLORS.get(level_lower, CONGESTION_COLORS["free_flow"])


def _add_tile_layers(m: folium.Map, active_theme: str = DEFAULT_THEME):
    """Add switchable base tile layers to the map."""
    for theme_name, conf in TILE_CONFIGS.items():
        if theme_name != active_theme:
            folium.TileLayer(
                tiles=conf["tiles"],
                attr=conf["attr"],
                name=conf["name"],
                control=True,
            ).add_to(m)


def _add_bus_fleet_cluster(
    m: folium.Map,
    telemetry_df: pd.DataFrame,
    max_buses: int = 400,
    show_by_default: bool = True,
):
    """
    Cluster and plot active live buses on the map with real-time speed color coding.
    """
    if telemetry_df is None or len(telemetry_df) == 0:
        return

    df = telemetry_df.copy()

    # Normalize coordinate column names
    lat_col = "lat" if "lat" in df.columns else ("latitude" if "latitude" in df.columns else None)
    lon_col = "lon" if "lon" in df.columns else ("longitude" if "longitude" in df.columns else None)
    if not lat_col or not lon_col:
        return

    # Drop null coordinates
    df = df.dropna(subset=[lat_col, lon_col])
    if len(df) == 0:
        return

    # Keep only the latest ping per bus
    if "bus_id" in df.columns:
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").groupby("bus_id").last().reset_index()
        else:
            df = df.groupby("bus_id").last().reset_index()

    # Limit to top N for smooth browser rendering
    if len(df) > max_buses:
        df = df.tail(max_buses)

    cluster = MarkerCluster(
        name="🚌 Live Bus Fleet (Clusters)",
        overlay=True,
        control=True,
        show=show_by_default,
        options={"maxClusterRadius": 40, "disableClusteringAtZoom": 15},
    )

    for _, row in df.iterrows():
        lat = float(row[lat_col])
        lon = float(row[lon_col])
        bus_id = str(row.get("bus_id", "Bus"))
        route_id = str(row.get("route_id", "Route"))
        speed = float(row.get("speed", 0.0))
        ts = str(row.get("timestamp", ""))

        # Speed category & color
        if speed >= 22.0:
            icon_color = "green"
            status_text = "🟢 Fast / Free Flow"
        elif speed >= 10.0:
            icon_color = "orange"
            status_text = "🟡 Moderate Speed"
        else:
            icon_color = "red"
            status_text = "🔴 Slow / Heavy Delay"

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size:12px; min-width:160px; line-height:1.5;">
            <div style="background:#1e293b; color:#fff; padding:4px 8px; border-radius:4px 4px 0 0; font-weight:bold;">
                🚌 Bus #{bus_id}
            </div>
            <div style="padding:6px 8px; border:1px solid #e2e8f0; border-top:none; border-radius:0 0 4px 4px; background:#fff;">
                <b>Route:</b> {route_id}<br/>
                <b>Live Speed:</b> <span style="font-weight:bold; color:{'#16a34a' if speed>=22 else ('#d97706' if speed>=10 else '#dc2626')};">{speed:.1f} km/h</span><br/>
                <b>Status:</b> {status_text}<br/>
                {f'<small style="color:#64748b;">Ping: {ts[:19]}</small>' if ts else ''}
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"Bus #{bus_id} | {speed:.0f} km/h",
            icon=folium.Icon(color=icon_color, icon="bus", prefix="fa"),
        ).add_to(cluster)

    cluster.add_to(m)


def _get_map_with_theme(tile_theme: str) -> tuple[folium.Map, str]:
    conf = TILE_CONFIGS.get(tile_theme, TILE_CONFIGS[DEFAULT_THEME])
    m = folium.Map(
        location=DELHI_CENTER,
        zoom_start=DEFAULT_ZOOM,
        tiles=conf["tiles"],
        attr=conf["attr"],
        control_scale=True,
    )
    _add_tile_layers(m, active_theme=tile_theme)
    Fullscreen(position="topleft").add_to(m)
    return m, conf["tiles"]


def create_route_map(
    route_geojson: dict,
    start_coords: tuple,
    end_coords: tuple,
    bus_stops: list,
    tile_theme: str = DEFAULT_THEME,
) -> folium.Map:
    """
    Create a Folium map centered on Delhi showing the route as a colored
    polyline, start/end markers, and bus-stop markers along the route.
    """
    m, tiles = _get_map_with_theme(tile_theme)

    # --- Route polyline ---
    if route_geojson:
        folium.GeoJson(
            route_geojson,
            name="Planned Route",
            style_function=lambda _: {
                "color": "#FF6B35",
                "weight": 5,
                "opacity": 0.85,
            },
        ).add_to(m)

    # --- Start marker ---
    if start_coords:
        folium.Marker(
            location=start_coords,
            popup="<b>Start Location</b>",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(m)

    # --- End marker ---
    if end_coords:
        folium.Marker(
            location=end_coords,
            popup="<b>Destination</b>",
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(m)

    # --- Bus stop markers ---
    if bus_stops:
        bus_stop_group = folium.FeatureGroup(name="🚏 Bus Stops")
        for stop in bus_stops:
            folium.CircleMarker(
                location=(stop["lat"], stop["lon"]),
                radius=6,
                color="#0284c7",
                fill=True,
                fill_color="#38bdf8",
                fill_opacity=0.85,
                popup=f"<b>🚏 {stop['name']}</b>",
                tooltip=stop["name"],
            ).add_to(bus_stop_group)
        bus_stop_group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def create_heatmap(heatmap_data: list, tile_theme: str = DEFAULT_THEME) -> folium.Map:
    """Create a congestion heatmap overlay using folium HeatMap plugin."""
    m, tiles = _get_map_with_theme(tile_theme)

    if heatmap_data:
        heat_points = [
            [d["lat"], d["lon"], d.get("intensity", 0.5)]
            for d in heatmap_data
        ]
        HeatMap(
            heat_points,
            name="🔥 Congestion Heatmap",
            radius=18,
            blur=22,
            max_zoom=15,
            gradient={
                0.2: "#2ecc71",
                0.4: "#f1c40f",
                0.6: "#e67e22",
                0.8: "#e74c3c",
                1.0: "#c0392b",
            },
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def create_combined_map(
    route_geojson: dict,
    heatmap_data: list,
    start_coords: tuple,
    end_coords: tuple,
    bus_stops: list,
    segments: list,
    traffic_model=None,
    bus_telemetry=None,
    tile_theme: str = DEFAULT_THEME,
    show_bus_fleet: bool = True,
) -> folium.Map:
    """
    Combined map with route + heatmap + segment coloring by congestion level
    + live bus fleet clustering + switchable basemaps.
    """
    m, tiles = _get_map_with_theme(tile_theme)

    # --- Heatmap layer ---
    if heatmap_data:
        heat_points = [
            [d["lat"], d["lon"], d.get("intensity", 0.5)]
            for d in heatmap_data
        ]
        HeatMap(
            heat_points,
            name="🔥 Congestion Heatmap",
            radius=18,
            blur=22,
            max_zoom=15,
            gradient={
                0.2: "#2ecc71",
                0.4: "#f1c40f",
                0.6: "#e67e22",
                0.8: "#e74c3c",
                1.0: "#c0392b",
            },
        ).add_to(m)

    # --- Segment lines colored by congestion ---
    if segments:
        segment_group = folium.FeatureGroup(name="🛣️ Road Segments (Congestion)")
        for seg in segments:
            level = "free_flow"
            speed_str = "N/A"
            if traffic_model:
                try:
                    level = traffic_model.get_congestion_level(seg.segment_id)
                    speed_val = traffic_model.get_segment_speed(seg.segment_id)
                    speed_str = f"{speed_val:.1f} km/h" if speed_val else "N/A"
                except Exception:
                    pass

            color = _get_congestion_color(level)
            folium.PolyLine(
                locations=[
                    (seg.start_lat, seg.start_lon),
                    (seg.end_lat, seg.end_lon),
                ],
                color=color,
                weight=5,
                opacity=0.8,
                tooltip=f"{seg.road_name}: {level.upper()} ({speed_str})",
            ).add_to(segment_group)
        segment_group.add_to(m)

    # --- Live Bus Fleet (Clusters) ---
    if show_bus_fleet and bus_telemetry is not None:
        _add_bus_fleet_cluster(m, bus_telemetry, max_buses=350, show_by_default=True)

    # --- Route polyline ---
    if route_geojson:
        folium.GeoJson(
            route_geojson,
            name="⚡ Optimized Route",
            style_function=lambda _: {
                "color": "#00f0ff" if "dark" in tiles else "#ff007f",
                "weight": 6,
                "opacity": 0.95,
                "dashArray": "8 4",
            },
        ).add_to(m)

    # --- Start / End markers ---
    if start_coords:
        folium.Marker(
            location=start_coords,
            popup="<b>🟢 Start Origin</b>",
            tooltip="Origin",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(m)
    if end_coords:
        folium.Marker(
            location=end_coords,
            popup="<b>🔴 Journey Destination</b>",
            tooltip="Destination",
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(m)

    # --- Bus stop markers with enhanced popups ---
    if bus_stops:
        bus_stop_group = folium.FeatureGroup(name="🚏 Bus Stops", show=False)
        walkshed_group = folium.FeatureGroup(name="🚶 500m Walkshed Radius", show=False)

        # Pre-compute route counts per stop
        try:
            from data.delhi_bus_stops import BUS_ROUTES
            stop_route_map = {}
            for route in BUS_ROUTES:
                for sid in route.get("stop_ids", []):
                    if sid not in stop_route_map:
                        stop_route_map[sid] = []
                    stop_route_map[sid].append(route.get("name", route.get("route_id", "?")))
        except Exception:
            stop_route_map = {}

        for stop in bus_stops:
            stop_id = stop.get("stop_id", "")
            routes_here = stop_route_map.get(stop_id, [])
            routes_count = len(routes_here)
            route_names_html = "".join(f"<li style='font-size:11px;'>{r}</li>" for r in routes_here[:5])
            if routes_count > 5:
                route_names_html += f"<li style='font-size:11px; color:#94a3b8;'>…and {routes_count - 5} more</li>"

            popup_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; min-width:180px; line-height:1.4;">
                <div style="background:#0284c7; color:#fff; padding:5px 10px; border-radius:6px 6px 0 0; font-weight:bold; font-size:13px;">
                    🚏 {stop['name']}
                </div>
                <div style="padding:8px 10px; border:1px solid #e2e8f0; border-top:none; border-radius:0 0 6px 6px; background:#fff; font-size:12px;">
                    <b>Stop ID:</b> {stop_id}<br/>
                    <b>Coordinates:</b> {stop['lat']:.4f}, {stop['lon']:.4f}<br/>
                    <b>Routes Served:</b> <span style="color:#0284c7; font-weight:bold;">{routes_count}</span><br/>
                    {'<b>Bus Lines:</b><ul style="margin:2px 0 0 16px; padding:0;">' + route_names_html + '</ul>' if routes_here else '<span style="color:#94a3b8;">No route data</span>'}
                </div>
            </div>
            """

            folium.CircleMarker(
                location=(stop["lat"], stop["lon"]),
                radius=7,
                color="#0284c7",
                fill=True,
                fill_color="#38bdf8",
                fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"🚏 {stop['name']} ({routes_count} routes)",
            ).add_to(bus_stop_group)

            # 500m walkshed circle (~0.0045 degrees)
            folium.Circle(
                location=(stop["lat"], stop["lon"]),
                radius=500,
                color="#0ea5e9",
                fill=True,
                fill_color="#0ea5e9",
                fill_opacity=0.08,
                weight=1,
                dash_array="4 4",
            ).add_to(walkshed_group)

        bus_stop_group.add_to(m)
        walkshed_group.add_to(m)

    # Auto-fit bounds if journey planned
    if start_coords and end_coords:
        try:
            m.fit_bounds([
                [min(start_coords[0], end_coords[0]) - 0.01, min(start_coords[1], end_coords[1]) - 0.01],
                [max(start_coords[0], end_coords[0]) + 0.01, max(start_coords[1], end_coords[1]) + 0.01],
            ])
        except Exception:
            pass

    folium.LayerControl(collapsed=False).add_to(m)
    return m

