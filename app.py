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
from frontend.pydeck_view import pydeck_available, create_3d_congestion_view, create_bus_flow_arcs

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

    # --- Click-to-Route: check for map clicks ---
    click_start = st.session_state.get("click_start")
    click_end = st.session_state.get("click_end")
    if click_start and click_end:
        start_coords = click_start
        end_coords = click_end

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
    # Main layout
    # ===================================================================

    # --- Map Tabs: 2D Folium | 3D Pydeck ---
    heatmap_data = traffic_model.get_heatmap_data()
    map_theme = st.session_state.get("map_theme", "Dark Matter (Command Center)")
    show_bus_fleet = st.session_state.get("show_bus_fleet", True)

    # Choose tabs based on pydeck availability
    if pydeck_available():
        map_tab_2d, map_tab_3d, map_tab_arcs = st.tabs([
            "🗺️ 2D Live Map",
            "🏙️ 3D Congestion View",
            "🌐 Bus Route Arcs",
        ])
    else:
        map_tab_2d = st.container()
        map_tab_3d = None
        map_tab_arcs = None

    # --- 2D Folium Map ---
    with map_tab_2d:
        st.markdown("### 🗺️ Live Network & Route Map")

        # Click-to-route instructions
        if st_folium is not None:
            with st.expander("🖱️ Click-to-Route: Plan a journey by clicking on the map", expanded=False):
                st.markdown("""
                1. **Click once** on the map to set your **🟢 Origin**.
                2. **Click again** to set your **🔴 Destination**.
                3. The route will be calculated automatically!
                4. Click **Reset Click Points** to start over.
                """)
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if click_start:
                        st.success(f"🟢 Origin: {click_start[0]:.4f}, {click_start[1]:.4f}")
                    else:
                        st.info("🟢 Click to set origin")
                with col_b:
                    if click_end:
                        st.success(f"🔴 Destination: {click_end[0]:.4f}, {click_end[1]:.4f}")
                    else:
                        st.info("🔴 Click to set destination")
                with col_c:
                    if st.button("🗑️ Reset Click Points", use_container_width=True):
                        st.session_state.pop("click_start", None)
                        st.session_state.pop("click_end", None)
                        st.rerun()

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
            map_result = st_folium(
                combined_map,
                use_container_width=True,
                height=580,
                returned_objects=["last_clicked"],
            )

            # Handle click-to-route
            if map_result and map_result.get("last_clicked"):
                clicked_lat = map_result["last_clicked"]["lat"]
                clicked_lon = map_result["last_clicked"]["lng"]
                if "click_start" not in st.session_state or (
                    "click_start" in st.session_state and "click_end" in st.session_state
                ):
                    # First click or reset
                    st.session_state["click_start"] = (clicked_lat, clicked_lon)
                    st.session_state.pop("click_end", None)
                    st.rerun()
                elif "click_start" in st.session_state and "click_end" not in st.session_state:
                    st.session_state["click_end"] = (clicked_lat, clicked_lon)
                    st.rerun()
        else:
            # Fallback: render map as inline HTML
            from streamlit.components.v1 import html as st_html
            map_html = combined_map._repr_html_()
            st_html(map_html, height=580, scrolling=True)

    # --- 3D Pydeck Congestion View ---
    if map_tab_3d is not None:
        with map_tab_3d:
            st.markdown("### 🏙️ 3D Congestion Columns & Bus Scatter")
            st.caption("Height = congestion intensity. Taller / redder columns = heavier traffic. Live bus positions shown as dots.")
            is_dark = "dark" in map_theme.lower() if map_theme else True

            deck_3d = create_3d_congestion_view(
                heatmap_data=heatmap_data,
                bus_telemetry=processed_df,
                dark_mode=is_dark,
            )
            if deck_3d is not None:
                st.pydeck_chart(deck_3d, use_container_width=True, height=580)
            else:
                st.warning("Install `pydeck` to enable 3D visualization: `pip install pydeck`")

    # --- Bus Route Arcs ---
    if map_tab_arcs is not None:
        with map_tab_arcs:
            st.markdown("### 🌐 Delhi Bus Route Network (3D Arcs)")
            st.caption("Arc connections between consecutive bus stops on each route. Cyan → Orange gradient shows travel direction.")
            deck_arcs = create_bus_flow_arcs(BUS_ROUTES, BUS_STOPS)
            if deck_arcs is not None:
                st.pydeck_chart(deck_arcs, use_container_width=True, height=580)
            else:
                st.warning("Install `pydeck` to enable arc visualization.")

    st.markdown("---")

    # --- Metrics & Data Tables ---
    st.markdown("### 📊 Journey Metrics & Traffic Diagnostics")
    render_metrics(route)

    st.markdown("")  # spacer

    # --- Tabs: Traffic Table | Bus Tracker | Predictions ---
    table_tab1, table_tab2, table_tab3 = st.tabs([
        "🚦 Road Congestion Table",
        "🚌 Live Bus Tracker",
        "🔮 Traffic Predictions (ML)",
    ])

    with table_tab1:
        render_traffic_table(traffic_model, segments)

    with table_tab2:
        render_bus_tracker(processed_df)

    with table_tab3:
        _render_predictions(processed_df, segments)

    # --- Auto-refresh loop ---
    if st.session_state.get("auto_refresh"):
        placeholder = st.empty()
        with placeholder.container():
            st.caption("⏳ Auto-refreshing in 30 seconds …")
        time.sleep(30)
        st.rerun()


def _render_predictions(processed_df: pd.DataFrame, segments):
    """Render ML traffic speed predictions 30 and 60 minutes ahead."""
    st.markdown("### 🔮 Predictive Traffic Forecast")
    st.caption(
        "Uses a Gradient Boosting model trained on current session telemetry "
        "to forecast road segment speeds 30 and 60 minutes ahead."
    )

    # Build predictor
    if "predictor" not in st.session_state:
        predictor = TrafficPredictor()
        # Prepare training data: attach segment_id via snap_to_segment
        if processed_df is not None and not processed_df.empty:
            from traffic.segments import snap_to_segment
            train_rows = []
            for _, row in processed_df.head(2000).iterrows():
                if pd.notna(row.get("lat")) and pd.notna(row.get("lon")) and pd.notna(row.get("speed")):
                    seg = snap_to_segment(float(row["lat"]), float(row["lon"]), segments)
                    train_rows.append({
                        "segment_id": seg.segment_id,
                        "speed": float(row["speed"]),
                        "timestamp": row.get("timestamp", "2026-11-20 09:00:00"),
                    })
            if train_rows:
                predictor.train(pd.DataFrame(train_rows))

        st.session_state["predictor"] = predictor

    predictor = st.session_state["predictor"]

    # Show predictions for key segments
    pred_rows = []
    sample_segments = segments[:20]  # First 20 segments
    for seg in sample_segments:
        try:
            speed_30 = predictor.predict(seg.segment_id, future_minutes=30)
            speed_60 = predictor.predict(seg.segment_id, future_minutes=60)
        except Exception:
            speed_30 = speed_60 = None

        pred_rows.append({
            "Road": seg.road_name,
            "Type": seg.road_type.title(),
            "Current Speed (km/h)": f"{st.session_state.get('traffic_model', TrafficModel()).get_segment_speed(seg.segment_id):.1f}",
            "⏱️ +30 min Forecast": f"{speed_30:.1f} km/h" if speed_30 else "—",
            "⏱️ +60 min Forecast": f"{speed_60:.1f} km/h" if speed_60 else "—",
        })

    if pred_rows:
        st.dataframe(pd.DataFrame(pred_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Not enough data to generate predictions yet.")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
