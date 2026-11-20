"""
Delhi Bus Traffic Model & Journey Planner
==========================================
Main Streamlit application entry point.

Run with:  streamlit run app.py
"""

import sys
import os
import time

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so all sub-packages are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Delhi Bus Traffic Model & Journey Planner",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from data.delhi_bus_stops import BUS_STOPS, BUS_ROUTES
from pipeline.ingestion import load_telemetry, stream_telemetry, fetch_live_delhi_otd
from pipeline.preprocessing import clean_gps, filter_dwell_times, compute_segment_speeds
from traffic.segments import create_delhi_road_network
from traffic.model import TrafficModel
from traffic.predictor import TrafficPredictor
from routing.graph import build_graph, update_weights
from routing.planner import plan_route, get_route_geojson

from frontend.dashboard import (
    _inject_custom_css,
    render_hero,
    render_sidebar,
    render_metrics,
    render_traffic_table,
    render_bus_tracker,
)
from frontend.map_view import create_combined_map

# Optional: streamlit-folium for rendering maps inline
try:
    from streamlit_folium import st_folium
except ImportError:
    st_folium = None


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
_inject_custom_css()


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
TELEMETRY_PATH = os.path.join(DATA_DIR, "synthetic_telemetry.csv")


@st.cache_resource(show_spinner="Building road network …")
def get_road_segments():
    """Create and cache the road-segment network."""
    return create_delhi_road_network()


@st.cache_resource(show_spinner="Building routing graph …")
def get_routing_graph(_segments, _traffic_model):
    """Build and weight the routing graph."""
    G = build_graph(_segments)
    G = update_weights(G, _traffic_model)
    return G


@st.cache_data(show_spinner="Loading telemetry …")
def get_telemetry(path: str) -> pd.DataFrame:
    """Load and return raw telemetry data."""
    return load_telemetry(path)


def ensure_synthetic_data():
    """Generate synthetic data if it does not exist yet."""
    if not os.path.exists(TELEMETRY_PATH):
        with st.spinner("Generating synthetic telemetry data — this may take a moment …"):
            gen_script = os.path.join(DATA_DIR, "generate_synthetic.py")
            if os.path.exists(gen_script):
                import subprocess
                subprocess.run(
                    [sys.executable, gen_script],
                    cwd=DATA_DIR,
                    check=True,
                )
            else:
                st.error(
                    "Synthetic data not found and `data/generate_synthetic.py` is missing. "
                    "Please generate telemetry data first."
                )
                st.stop()


def build_traffic_model(df: pd.DataFrame, segments):
    """Run the preprocessing pipeline and build the traffic model."""
    df = clean_gps(df)
    df = filter_dwell_times(df, BUS_STOPS)
    df = compute_segment_speeds(df)
    model = TrafficModel()
    model.update(df, segments)
    return model, df


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
def main():
    # --- Hero section ---
    render_hero()

    # --- Sidebar (controls inputs and data source) ---
    start_coords, end_coords = render_sidebar(BUS_STOPS)

    # --- Ensure fallback data exists ---
    ensure_synthetic_data()

    # --- Load road network segments ---
    segments = get_road_segments()

    # --- Data Source Handling (Live vs Synthetic) ---
    data_source = st.session_state.get("data_source", "🟡 Synthetic Simulation")
    raw_df = None
    is_live_data = False

    if data_source == "🟢 Live Delhi OTD Feed":
        api_key = st.session_state.get("otd_api_key", "").strip()
        fetch_requested = st.session_state.pop("fetch_live_requested", False)
        
        if api_key:
            if fetch_requested or "live_df" not in st.session_state:
                with st.spinner("📡 Fetching real-time telemetry from Delhi Open Transit Data API (otd.delhi.gov.in) …"):
                    try:
                        live_df = fetch_live_delhi_otd(api_key=api_key)
                        if len(live_df) > 0:
                            st.session_state["live_df"] = live_df
                            st.session_state["refresh_requested"] = True
                            st.success(f"🟢 Successfully connected to Delhi OTD API! Ingested {len(live_df):,} live vehicle positions.")
                        else:
                            st.warning("Connected to Delhi OTD API, but feed returned 0 active vehicle positions right now.")
                    except Exception as exc:
                        st.error(f"❌ Failed to query Delhi OTD API: {exc}")
                        st.info("Falling back to synthetic telemetry simulation baseline.")
            
            if "live_df" in st.session_state:
                raw_df = st.session_state["live_df"]
                is_live_data = True
        else:
            st.info("💡 **Live Mode Selected:** Please enter your Delhi Open Transit Data API key in the sidebar and click **'Fetch Live Delhi Buses'**. Currently showing synthetic baseline.")

    if raw_df is None:
        raw_df = get_telemetry(TELEMETRY_PATH)

    # Rebuild model when data changes or on refresh
    if "traffic_model" not in st.session_state or st.session_state.get("refresh_requested"):
        traffic_model, processed_df = build_traffic_model(raw_df.copy(), segments)
        st.session_state["traffic_model"] = traffic_model
        st.session_state["processed_df"] = processed_df
        st.session_state["refresh_requested"] = False
    else:
        traffic_model = st.session_state["traffic_model"]
        processed_df = st.session_state["processed_df"]

    # --- Routing graph ---
    G = get_routing_graph(segments, traffic_model)

    # --- Plan route ---
    route = None
    route_geojson = None
    if start_coords and end_coords:
        try:
            route = plan_route(
                G,
                start_coords[0], start_coords[1],
                end_coords[0], end_coords[1],
            )
            route_geojson = get_route_geojson(route)
        except Exception as e:
            st.warning(f"Could not plan route: {e}")

    # ===================================================================
    # Main layout: Map (top), Metrics and Tables (bottom)
    # ===================================================================

    # --- Top: Map View ---
    st.markdown("### 🗺️ Live Network & Route Map")
    heatmap_data = traffic_model.get_heatmap_data()
    map_theme = st.session_state.get("map_theme", "Dark Matter (Command Center)")
    show_bus_fleet = st.session_state.get("show_bus_fleet", True)

    combined_map = create_combined_map(
        route_geojson=route_geojson,
        heatmap_data=heatmap_data,
        start_coords=start_coords,
        end_coords=end_coords,
        bus_stops=BUS_STOPS,
        segments=segments,
        traffic_model=traffic_model,
        bus_telemetry=processed_df,
        tile_theme=map_theme,
        show_bus_fleet=show_bus_fleet,
    )

    if st_folium is not None:
        st_folium(combined_map, use_container_width=True, height=520)
    else:
        # Fallback: render map as inline HTML
        from streamlit.components.v1 import html as st_html
        map_html = combined_map._repr_html_()
        st_html(map_html, height=520, scrolling=True)

    st.markdown("---")

    # --- Bottom: Metrics & Data Tables ---
    st.markdown("### 📊 Journey Metrics & Traffic Diagnostics")
    render_metrics(route)

    st.markdown("")  # spacer

    table_tab1, table_tab2 = st.tabs(["🚦 Road Congestion Table", "🚌 Live Bus Tracker"])

    with table_tab1:
        render_traffic_table(traffic_model, segments)

    with table_tab2:
        render_bus_tracker(processed_df)

    # --- Auto-refresh loop ---
    if st.session_state.get("auto_refresh"):
        placeholder = st.empty()
        with placeholder.container():
            st.caption("⏳ Auto-refreshing in 30 seconds …")
        time.sleep(30)
        st.rerun()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()

