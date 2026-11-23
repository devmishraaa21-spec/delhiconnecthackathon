"""
Map visualization components for the Delhi Bus Traffic Model.
Uses Folium for high-resolution interactive 2D GIS rendering within Streamlit.
"""

from __future__ import annotations

import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen, MiniMap
from typing import Optional, List, Dict
import pandas as pd


# Delhi center coordinates
DELHI_CENTER = [28.6139, 77.2090]
DEFAULT_ZOOM = 12

# Congestion color palette
CONGESTION_COLORS = {
    "free_flow": "#2ecc71",    # emerald green
    "moderate": "#f1c40f",     # amber yellow
    "heavy": "#e67e22",        # orange
    "gridlock": "#e74c3c",     # red
    "severe": "#e74c3c",       # red fallback
}

# Free-flow speeds benchmark (km/h)
FREE_FLOW_BENCHMARKS = {
    "expressway": 60.0,
    "arterial": 40.0,
    "local": 30.0,
    "congested_zone": 15.0,
}

# Supported tile definitions
TILE_CONFIGS = {
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
        "name": "🗺️ OpenStreetMap Standard",
    },
    "Esri Street Map": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom",
        "name": "🏛️ Esri Street Map",
    },
    "Satellite Aerial (Esri)": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
        "name": "🛰️ Satellite Aerial (Esri)",
    },
    "Clean Light": {
        "tiles": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "name": "☀️ Clean Light",
    },
}
DEFAULT_THEME = "OpenStreetMap"


def _get_congestion_color(level: str) -> str:
    """Map a congestion level string to a hex color."""
    level_lower = level.lower().replace(" ", "_") if level else "free_flow"
    return CONGESTION_COLORS.get(level_lower, CONGESTION_COLORS["free_flow"])


def _inject_map_control_styles(m: folium.Map):
    """Inject executive glassmorphic styling into Leaflet map controls."""
    css = """
    <style>
    /* Executive Glassmorphic Leaflet Layer Control */
    .leaflet-control-layers {
        background: rgba(15, 23, 42, 0.94) !important;
        border: 1px solid rgba(255, 107, 53, 0.45) !important;
        border-radius: 14px !important;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65), 0 0 16px rgba(255, 107, 53, 0.15) !important;
        backdrop-filter: blur(16px) !important;
        color: #f1f5f9 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 12px !important;
        padding: 10px 14px !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    .leaflet-control-layers-toggle {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(255, 107, 53, 0.5) !important;
        border-radius: 10px !important;
        width: 38px !important;
        height: 38px !important;
        background-size: 20px 20px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }

    .leaflet-control-layers-toggle:hover {
        transform: scale(1.06) !important;
        border-color: #ff9933 !important;
        box-shadow: 0 0 14px rgba(255, 153, 51, 0.5) !important;
    }

    .leaflet-control-layers-expanded {
        padding: 12px 16px !important;
        min-width: 220px !important;
        max-width: 280px !important;
    }

    .leaflet-control-layers-base label,
    .leaflet-control-layers-overlays label {
        margin-bottom: 6px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        cursor: pointer !important;
        color: #cbd5e1 !important;
        font-size: 11.5px !important;
        font-weight: 500 !important;
        transition: color 0.15s ease !important;
    }

    .leaflet-control-layers label:hover {
        color: #ff9933 !important;
    }

    .leaflet-control-layers input[type="radio"],
    .leaflet-control-layers input[type="checkbox"] {
        accent-color: #ff6b35 !important;
        cursor: pointer !important;
        width: 15px !important;
        height: 15px !important;
        margin: 0 !important;
    }

    .leaflet-control-layers-separator {
        border-top: 1px solid rgba(255, 107, 53, 0.3) !important;
        margin: 10px 0 !important;
    }

    /* Glassmorphic Zoom Controls (+ / -) */
    .leaflet-control-zoom {
        border: 1px solid rgba(255, 107, 53, 0.35) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5) !important;
    }

    .leaflet-control-zoom a {
        background: rgba(15, 23, 42, 0.92) !important;
        color: #ff9933 !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        width: 32px !important;
        height: 32px !important;
        line-height: 32px !important;
        font-size: 16px !important;
        transition: background 0.2s ease, color 0.2s ease !important;
    }

    .leaflet-control-zoom a:hover {
        background: rgba(255, 107, 53, 0.25) !important;
        color: #ffffff !important;
    }

    /* Fullscreen Button */
    .leaflet-control-fullscreen a {
        background: rgba(15, 23, 42, 0.92) !important;
        border: 1px solid rgba(255, 107, 53, 0.35) !important;
        border-radius: 10px !important;
        color: #ff9933 !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5) !important;
    }

    /* MiniMap */
    .leaflet-control-minimap {
        border: 1px solid rgba(255, 107, 53, 0.4) !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
        overflow: hidden !important;
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(css))


def _add_tile_layers(m: folium.Map, active_theme: str = DEFAULT_THEME):
    """Add switchable base tile layers to the map."""
    pass  # Handled cleanly inside _get_map_with_theme to prevent raw URL name leakage


def _add_legend(m: folium.Map):
    """Add a glassmorphic floating legend control to the map."""
    legend_html = """
    <div style="
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 175px;
        background: rgba(15, 23, 42, 0.88);
        border: 1px solid rgba(255, 107, 53, 0.4);
        border-radius: 12px;
        padding: 10px 14px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11px;
        color: #f1f5f9;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        z-index: 9999;
        line-height: 1.5;
    ">
        <b style="color: #ff9933; font-size: 12px; display: block; margin-bottom: 6px; letter-spacing: 0.04em;">
            🚦 TRAFFIC VELOCITY
        </b>
        <div style="display:flex; align-items:center; margin-bottom:3px;">
            <span style="display:inline-block; width:14px; height:4px; background:#2ecc71; margin-right:8px; border-radius:2px;"></span>
            <span>Free Flow (&gt;28 km/h)</span>
        </div>
        <div style="display:flex; align-items:center; margin-bottom:3px;">
            <span style="display:inline-block; width:14px; height:4px; background:#f1c40f; margin-right:8px; border-radius:2px;"></span>
            <span>Moderate (18-28)</span>
        </div>
        <div style="display:flex; align-items:center; margin-bottom:3px;">
            <span style="display:inline-block; width:14px; height:4px; background:#e67e22; margin-right:8px; border-radius:2px;"></span>
            <span>Heavy (10-18)</span>
        </div>
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <span style="display:inline-block; width:14px; height:4px; background:#e74c3c; margin-right:8px; border-radius:2px;"></span>
            <span>Gridlock (&lt;10 km/h)</span>
        </div>
        <hr style="border:none; border-top:1px solid rgba(255,255,255,0.12); margin:4px 0 6px 0;">
        <div style="display:flex; align-items:center;">
            <span style="display:inline-block; width:10px; height:10px; background:#00f0ff; margin-right:8px; border-radius:50%; box-shadow:0 0 6px #00f0ff;"></span>
            <span>Planned Route</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def _add_bus_fleet_cluster(
    m: folium.Map,
    telemetry_df: pd.DataFrame,
    max_buses: int = 550,
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

    # Limit for smooth performance
    if len(df) > max_buses:
        df = df.tail(max_buses)

    cluster = MarkerCluster(
        name="🚌 Live Bus Fleet (Clusters)",
        overlay=True,
        control=True,
        show=show_by_default,
        options={
            "maxClusterRadius": 45,
            "disableClusteringAtZoom": 15,
            "spiderfyOnMaxZoom": True,
        },
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
            spd_color = "#16a34a"
        elif speed >= 10.0:
            icon_color = "orange"
            status_text = "🟡 Moderate Speed"
            spd_color = "#d97706"
        else:
            icon_color = "red"
            status_text = "🔴 Slow / Heavy Delay"
            spd_color = "#dc2626"

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size:12px; min-width:170px; line-height:1.5;">
            <div style="background:#0f172a; color:#fff; padding:6px 10px; border-radius:6px 6px 0 0; font-weight:bold; display:flex; justify-content:space-between; align-items:center;">
                <span>🚌 Bus #{bus_id}</span>
                <span style="font-size:10px; background:#334155; padding:2px 6px; border-radius:4px;">R-{route_id}</span>
            </div>
            <div style="padding:8px 10px; border:1px solid #e2e8f0; border-top:none; border-radius:0 0 6px 6px; background:#fff;">
                <b>Live Velocity:</b> <span style="font-weight:bold; font-size:13px; color:{spd_color};">{speed:.1f} km/h</span><br/>
                <b>Traffic State:</b> {status_text}<br/>
                {f'<small style="color:#64748b;">GPS Ping: {ts[:19]}</small>' if ts else ''}
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=230),
            tooltip=f"Bus #{bus_id} | {speed:.1f} km/h",
            icon=folium.Icon(color=icon_color, icon="bus", prefix="fa"),
        ).add_to(cluster)

    cluster.add_to(m)


def _get_map_with_theme(
    tile_theme: str = DEFAULT_THEME,
    center: Optional[list] = None,
    zoom: int = DEFAULT_ZOOM,
) -> tuple[folium.Map, str]:
    target_center = center if center else DELHI_CENTER
    # Guard against stale session state referencing removed themes
    if tile_theme not in TILE_CONFIGS:
        tile_theme = DEFAULT_THEME
    conf = TILE_CONFIGS.get(tile_theme, TILE_CONFIGS[DEFAULT_THEME])

    # Initialize Folium Map with tiles=None to eliminate raw-URL name leakage in LayerControl
    m = folium.Map(
        location=target_center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    # Register each base map with its clean name and icon
    for theme_name, tconf in TILE_CONFIGS.items():
        is_active = (theme_name == tile_theme)
        folium.TileLayer(
            tiles=tconf["tiles"],
            attr=tconf["attr"],
            name=tconf["name"],
            control=True,
            show=is_active,
        ).add_to(m)

    Fullscreen(position="topleft").add_to(m)
    MiniMap(toggle_display=True, position="bottomleft", width=130, height=90).add_to(m)
    _add_legend(m)
    _inject_map_control_styles(m)
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
            name="⚡ Optimized Route",
            style_function=lambda _: {
                "color": "#00f0ff" if "dark" in tiles or "Satellite" in tiles else "#ff007f",
                "weight": 6,
                "opacity": 0.9,
                "dashArray": "8 4",
            },
        ).add_to(m)

    # --- Start marker ---
    if start_coords:
        folium.Marker(
            location=start_coords,
            popup="<b>🟢 Start Origin</b>",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(m)

    # --- End marker ---
    if end_coords:
        folium.Marker(
            location=end_coords,
            popup="<b>🔴 Destination</b>",
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

    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    return m


def create_heatmap(heatmap_data: list, tile_theme: str = DEFAULT_THEME) -> folium.Map:
    """Create a congestion heatmap overlay using folium HeatMap plugin."""
    m, tiles = _get_map_with_theme(tile_theme)

    if heatmap_data:
        heat_points = [
            [d["lat"], d["lon"], d.get("intensity", 0.5)]
            for d in heatmap_data
        ]
        heat_group = folium.FeatureGroup(name="🔥 Congestion Heatmap", show=True)
        HeatMap(
            heat_points,
            radius=22,
            blur=26,
            max_zoom=15,
            gradient={
                0.2: "#2ecc71",
                0.4: "#f1c40f",
                0.6: "#e67e22",
                0.8: "#e74c3c",
                1.0: "#c0392b",
            },
        ).add_to(heat_group)
        heat_group.add_to(m)

    folium.LayerControl(collapsed=True, position="topright").add_to(m)
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
    show_segments: bool = True,
    show_heatmap: bool = True,
    show_stops: bool = False,
    show_walkshed: bool = False,
    collapsed_layers: bool = True,
    center: Optional[list] = None,
    zoom: int = DEFAULT_ZOOM,
) -> folium.Map:
    """
    Combined map with route + heatmap + segment coloring by congestion level
    + live bus fleet clustering + switchable basemaps + walkshed circles.
    """
    m, tiles = _get_map_with_theme(tile_theme, center=center, zoom=zoom)

    # --- Heatmap layer ---
    if heatmap_data:
        heat_points = [
            [d["lat"], d["lon"], d.get("intensity", 0.5)]
            for d in heatmap_data
        ]
        heat_group = folium.FeatureGroup(name="🔥 Congestion Heatmap", show=show_heatmap)
        HeatMap(
            heat_points,
            radius=22,
            blur=26,
            max_zoom=15,
            gradient={
                0.2: "#2ecc71",
                0.4: "#f1c40f",
                0.6: "#e67e22",
                0.8: "#e74c3c",
                1.0: "#c0392b",
            },
        ).add_to(heat_group)
        heat_group.add_to(m)

    # --- Segment lines colored by congestion with interactive detail popup ---
    if segments:
        segment_group = folium.FeatureGroup(name="🛣️ Road Segments (Congestion)", show=show_segments)
        for seg in segments:
            level = "free_flow"
            speed_val = 30.0
            if traffic_model:
                try:
                    level = traffic_model.get_congestion_level(seg.segment_id)
                    speed_val = traffic_model.get_segment_speed(seg.segment_id)
                except Exception:
                    pass

            color = _get_congestion_color(level)
            ff_speed = FREE_FLOW_BENCHMARKS.get(seg.road_type, 35.0)
            weight = 6 if level in ["heavy", "gridlock", "severe"] else 4

            seg_popup = f"""
            <div style="font-family:-apple-system, BlinkMacSystemFont, sans-serif; font-size:12px; min-width:180px; line-height:1.4;">
                <div style="background:{color}; color:#fff; padding:5px 8px; border-radius:4px 4px 0 0; font-weight:bold;">
                    🛣️ {seg.road_name}
                </div>
                <div style="padding:6px 8px; border:1px solid #cbd5e1; border-top:none; border-radius:0 0 4px 4px; background:#fff;">
                    <b>Current Velocity:</b> <span style="font-weight:bold; color:{color};">{speed_val:.1f} km/h</span><br/>
                    <b>Congestion State:</b> {level.replace('_', ' ').title()}<br/>
                    <b>Road Category:</b> {seg.road_type.title()}<br/>
                    <b>Length:</b> {seg.length_m:.0f}m (Free-flow: {ff_speed:.0f} km/h)
                </div>
            </div>
            """

            folium.PolyLine(
                locations=[
                    (seg.start_lat, seg.start_lon),
                    (seg.end_lat, seg.end_lon),
                ],
                color=color,
                weight=weight,
                opacity=0.85,
                popup=folium.Popup(seg_popup, max_width=240),
                tooltip=f"{seg.road_name}: {level.upper()} ({speed_val:.1f} km/h)",
            ).add_to(segment_group)
        segment_group.add_to(m)

    # --- Live Bus Fleet (Clusters) ---
    if bus_telemetry is not None:
        _add_bus_fleet_cluster(m, bus_telemetry, max_buses=550, show_by_default=show_bus_fleet)

    # --- Route polyline ---
    if route_geojson:
        folium.GeoJson(
            route_geojson,
            name="⚡ Optimized Route",
            style_function=lambda _: {
                "color": "#00f0ff" if "dark" in tiles.lower() or "arcgis" in tiles.lower() else "#ff007f",
                "weight": 7,
                "opacity": 0.95,
                "dashArray": "10 5",
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
        bus_stop_group = folium.FeatureGroup(name="🚏 Bus Stops", show=show_stops)
        walkshed_group = folium.FeatureGroup(name="🚶 500m Walkshed Radius", show=show_walkshed)

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
                radius=6,
                color="#0284c7",
                fill=True,
                fill_color="#38bdf8",
                fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"🚏 {stop['name']} ({routes_count} routes)",
            ).add_to(bus_stop_group)

            # 500m walkshed circle
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
                [min(start_coords[0], end_coords[0]) - 0.015, min(start_coords[1], end_coords[1]) - 0.015],
                [max(start_coords[0], end_coords[0]) + 0.015, max(start_coords[1], end_coords[1]) + 0.015],
            ])
        except Exception:
            pass

    folium.LayerControl(collapsed=collapsed_layers, position="topright").add_to(m)
    return m
