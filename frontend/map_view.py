"""
Map visualization components for the Delhi Bus Traffic Model.
Uses Folium for interactive map rendering within Streamlit.
"""

import folium
from folium.plugins import HeatMap
from typing import Optional


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

# Delhi-themed tile options
TILE_STYLE = "cartodbpositron"


def _get_congestion_color(level: str) -> str:
    """Map a congestion level string to a hex color."""
    level_lower = level.lower().replace(" ", "_") if level else "free_flow"
    return CONGESTION_COLORS.get(level_lower, CONGESTION_COLORS["free_flow"])


def create_route_map(
    route_geojson: dict,
    start_coords: tuple,
    end_coords: tuple,
    bus_stops: list,
) -> folium.Map:
    """
    Create a Folium map centered on Delhi showing the route as a colored
    polyline, start/end markers, and bus-stop markers along the route.

    Parameters
    ----------
    route_geojson : dict
        GeoJSON dict with the route geometry (FeatureCollection or Feature).
    start_coords : tuple
        (lat, lon) of the journey origin.
    end_coords : tuple
        (lat, lon) of the journey destination.
    bus_stops : list[dict]
        Bus stops to display; each dict has keys name, lat, lon.

    Returns
    -------
    folium.Map
    """
    m = folium.Map(location=DELHI_CENTER, zoom_start=DEFAULT_ZOOM, tiles=TILE_STYLE)

    # --- Route polyline ---
    if route_geojson:
        folium.GeoJson(
            route_geojson,
            name="Route",
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
            popup="<b>Start</b>",
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
        bus_stop_group = folium.FeatureGroup(name="Bus Stops")
        for stop in bus_stops:
            folium.CircleMarker(
                location=(stop["lat"], stop["lon"]),
                radius=5,
                color="#2c3e50",
                fill=True,
                fill_color="#3498db",
                fill_opacity=0.7,
                popup=f"<b>{stop['name']}</b>",
                tooltip=stop["name"],
            ).add_to(bus_stop_group)
        bus_stop_group.add_to(m)

    folium.LayerControl().add_to(m)
    return m


def create_heatmap(heatmap_data: list[dict]) -> folium.Map:
    """
    Create a congestion heatmap overlay using folium HeatMap plugin.

    Parameters
    ----------
    heatmap_data : list[dict]
        Each dict should have keys: lat, lon, intensity (0-1 float).

    Returns
    -------
    folium.Map
    """
    m = folium.Map(location=DELHI_CENTER, zoom_start=DEFAULT_ZOOM, tiles=TILE_STYLE)

    if heatmap_data:
        heat_points = [
            [d["lat"], d["lon"], d.get("intensity", 0.5)]
            for d in heatmap_data
        ]
        HeatMap(
            heat_points,
            name="Congestion Heatmap",
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

    folium.LayerControl().add_to(m)
    return m


def create_combined_map(
    route_geojson: dict,
    heatmap_data: list[dict],
    start_coords: tuple,
    end_coords: tuple,
    bus_stops: list,
    segments: list,
    traffic_model=None,
) -> folium.Map:
    """
    Combined map with route + heatmap + segment coloring by congestion level.

    Parameters
    ----------
    route_geojson : dict
        GeoJSON dict with the route geometry.
    heatmap_data : list[dict]
        Heat-map point data with lat, lon, intensity.
    start_coords : tuple
        (lat, lon) of the journey origin.
    end_coords : tuple
        (lat, lon) of the journey destination.
    bus_stops : list[dict]
        Bus stops to display.
    segments : list
        List of RoadSegment objects.
    traffic_model : TrafficModel, optional
        If provided, used to color segments by congestion level.

    Returns
    -------
    folium.Map
    """
    m = folium.Map(location=DELHI_CENTER, zoom_start=DEFAULT_ZOOM, tiles=TILE_STYLE)

    # --- Heatmap layer ---
    if heatmap_data:
        heat_points = [
            [d["lat"], d["lon"], d.get("intensity", 0.5)]
            for d in heatmap_data
        ]
        HeatMap(
            heat_points,
            name="Congestion Heatmap",
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
        segment_group = folium.FeatureGroup(name="Road Segments")
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
                weight=4,
                opacity=0.75,
                tooltip=f"{seg.road_name} — {level} ({speed_str})",
            ).add_to(segment_group)
        segment_group.add_to(m)

    # --- Route polyline ---
    if route_geojson:
        folium.GeoJson(
            route_geojson,
            name="Planned Route",
            style_function=lambda _: {
                "color": "#FF6B35",
                "weight": 6,
                "opacity": 0.9,
                "dashArray": "10 6",
            },
        ).add_to(m)

    # --- Start / End markers ---
    if start_coords:
        folium.Marker(
            location=start_coords,
            popup="<b>Start</b>",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(m)
    if end_coords:
        folium.Marker(
            location=end_coords,
            popup="<b>Destination</b>",
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(m)

    # --- Bus stop markers ---
    if bus_stops:
        bus_stop_group = folium.FeatureGroup(name="Bus Stops")
        for stop in bus_stops:
            folium.CircleMarker(
                location=(stop["lat"], stop["lon"]),
                radius=5,
                color="#2c3e50",
                fill=True,
                fill_color="#3498db",
                fill_opacity=0.7,
                popup=f"<b>{stop['name']}</b>",
                tooltip=stop["name"],
            ).add_to(bus_stop_group)
        bus_stop_group.add_to(m)

    folium.LayerControl().add_to(m)
    return m

