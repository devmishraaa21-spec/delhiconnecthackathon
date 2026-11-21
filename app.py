"""
Delhi Bus Traffic Model & Journey Planner
==========================================
Main Streamlit application entry point.

Run with:  streamlit run app.py
"""

import sys
import os
import time
from datetime import datetime

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
from pipeline.ingestion import (
    load_telemetry,
    stream_telemetry,
    fetch_live_delhi_otd,
    derive_delta_speeds,
    DEFAULT_OTD_API_KEY,
)
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

# Optional: streamlit-autorefresh for smooth 15s live polling
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


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
    model = TrafficModel()
    model.update(df, segments)
    return model, df


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
def main():
    # --- Auto-refresh hook (configurable non-blocking live poll) ---
    auto_refresh_enabled = st.session_state.get("auto_refresh", True)
    refresh_sec = st.session_state.get("refresh_interval", 25)
    if auto_refresh_enabled and st_autorefresh is not None:
        st_autorefresh(interval=refresh_sec * 1000, key="delhi_live_autorefresh_ticker")

    # --- Hero section ---
    render_hero()

    # --- Sidebar (controls inputs and data source) ---
    start_coords, end_coords = render_sidebar(BUS_STOPS)

    # --- Ensure fallback data exists ---
    ensure_synthetic_data()

    # --- Load road network segments ---
    segments = get_road_segments()

    # --- Data Source Handling (Live vs Synthetic) ---
    data_source = st.session_state.get("data_source", "🟢 Live Delhi OTD Feed")
    raw_df = None
    is_live_data = False
    last_fetch_str = st.session_state.get("last_fetch_time_str", "Just now")

    if data_source == "🟢 Live Delhi OTD Feed":
        api_key = st.session_state.get("otd_api_key", DEFAULT_OTD_API_KEY).strip()
        fetch_requested = st.session_state.pop("fetch_live_requested", False)
        now_ts = time.time()
        last_ts = st.session_state.get("last_fetch_timestamp", 0)

        # Has cached live data?
        has_cached_live = "live_df" in st.session_state

        # Auto-refresh cooldown: matched to chosen refresh interval
        time_elapsed = (now_ts - last_ts) >= max(10.0, float(refresh_sec) - 2.0)
        # Only fetch when:
        # 1. User clicked "Force Live Telemetry Refresh"
        # 2. First boot and no cached data
        # 3. Auto-refresh is on AND at least 15s have passed since last attempt
        needs_fetch = fetch_requested or (not has_cached_live) or (auto_refresh_enabled and time_elapsed)

        if api_key and needs_fetch:
            # Stamp timestamp immediately so clicks on map/tabs don't trigger simultaneous/rapid requests
            st.session_state["last_fetch_timestamp"] = now_ts
            with st.spinner("📡 Streaming real-time telemetry from Delhi Open Transit Data API (otd.delhi.gov.in) …"):
                try:
                    new_raw_df = fetch_live_delhi_otd(api_key=api_key)
                    if len(new_raw_df) > 0:
                        prev_raw_df = st.session_state.get("prev_otd_raw_df", None)
                        # Compute real-time delta speeds from actual GPS displacement
                        live_df_with_speeds = derive_delta_speeds(new_raw_df, prev_raw_df)

                        st.session_state["prev_otd_raw_df"] = new_raw_df.copy()
                        st.session_state["live_df"] = live_df_with_speeds
                        st.session_state["last_fetch_time_str"] = datetime.now().strftime("%I:%M:%S %p")
                        st.session_state["refresh_requested"] = True
                        last_fetch_str = st.session_state["last_fetch_time_str"]
                    else:
                        st.warning("Connected to Delhi OTD API, but feed returned 0 active vehicle positions right now.")
                except Exception as exc:
                    # Cooldown on network / socket error: back off by 25s to avoid spamming the port
                    st.session_state["last_fetch_timestamp"] = now_ts + 25.0
                    if has_cached_live:
                        # Retain existing live fleet without interruption or alarming error banner!
                        st.caption(
                            f"ℹ️ Delhi OTD live sync throttled: {exc}. Retaining current live snapshot ({len(st.session_state['live_df']):,} buses)."
                        )
                    else:
                        st.error(f"❌ Failed to query Delhi OTD API: {exc}")
                        st.info("Falling back to synthetic simulation baseline.")

        if "live_df" in st.session_state:
            raw_df = st.session_state["live_df"]
            is_live_data = True
            last_fetch_str = st.session_state.get("last_fetch_time_str", datetime.now().strftime("%I:%M:%S %p"))

    if raw_df is None:
        raw_df = get_telemetry(TELEMETRY_PATH)

    # --- Live Stream Status Banner ---
    if is_live_data:
        st.markdown(
            f"""
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 12px; padding: 10px 18px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-block; width: 10px; height: 10px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></span>
                    <span style="color: #34d399; font-weight: 700; font-size: 0.95rem;">LIVE OTD STREAMING</span>
                    <span style="color: #94a3b8; font-size: 0.88rem;">• Ingested <b>{len(raw_df):,}</b> active Delhi buses • Speeds calculated via live GPS displacement</span>
                </div>
                <div style="color: #38bdf8; font-size: 0.85rem; font-weight: 600;">
                    ⏱️ Last sync: {last_fetch_str} {'(Next in ~' + str(refresh_sec) + 's)' if auto_refresh_enabled else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 12px; padding: 10px 18px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-block; width: 10px; height: 10px; background-color: #f59e0b; border-radius: 50%;"></span>
                    <span style="color: #fbbf24; font-weight: 700; font-size: 0.95rem;">SYNTHETIC SIMULATION BASELINE</span>
                    <span style="color: #94a3b8; font-size: 0.88rem;">• Modeling 100 buses across Delhi's primary transit corridors</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.85rem;">
                    💡 Switch to <b>🟢 Live Delhi OTD Feed</b> in the sidebar to stream real-time DTC/DIMTS fleet
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
        map_tab_2d, map_tab_3d, map_tab_arcs, fleet_tab_main = st.tabs([
            "🗺️ 2D Live Map",
            "🏙️ 3D Congestion View",
            "🌐 Bus Route Arcs",
            "🚌 Active Bus Fleet Explorer",
        ])
    else:
        map_tab_2d, fleet_tab_main = st.tabs([
            "🗺️ 2D Live Map",
            "🚌 Active Bus Fleet Explorer",
        ])
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
                        st.session_state.pop("_last_handled_click", None)
                        st.rerun()

        # Corridor focal coordinates and zoom levels
        corridor = st.session_state.get("corridor_focus", "All Delhi (Metropolitan Overview)")
        corridor_coords = {
            "All Delhi (Metropolitan Overview)": ([28.6139, 77.2090], 12),
            "Central Delhi (Connaught Place / India Gate)": ([28.6200, 77.2180], 13),
            "North Delhi (ISBT Kashmere Gate / Red Fort)": ([28.6672, 77.2284], 14),
            "South Delhi (AIIMS / Ring Road / Saket)": ([28.5672, 77.2100], 13),
            "East Delhi (Vikas Marg / Anand Vihar)": ([28.6364, 77.2956], 13),
            "West Delhi (Dwarka / Janakpuri / IGI)": ([28.5950, 77.0700], 13),
        }
        map_center, map_zoom = corridor_coords.get(corridor, ([28.6139, 77.2090], 12))

        show_walkshed = st.session_state.get("show_walkshed", False)
        show_segments = st.session_state.get("show_segments", True)
        show_heatmap = st.session_state.get("show_heatmap", True)
        show_stops = st.session_state.get("show_stops", False)
        keep_layers_open = st.session_state.get("keep_layers_open", False)

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
            show_segments=show_segments,
            show_heatmap=show_heatmap,
            show_stops=show_stops,
            show_walkshed=show_walkshed,
            collapsed_layers=(not keep_layers_open),
            center=map_center,
            zoom=map_zoom,
        )

        if st_folium is not None:
            map_result = st_folium(
                combined_map,
                use_container_width=True,
                height=580,
                returned_objects=["last_clicked"],
            )

            # Handle click-to-route without redundant reruns
            if map_result and map_result.get("last_clicked"):
                clicked_lat = map_result["last_clicked"]["lat"]
                clicked_lon = map_result["last_clicked"]["lng"]
                click_tuple = (round(clicked_lat, 5), round(clicked_lon, 5))
                last_handled = st.session_state.get("_last_handled_click")
                if click_tuple != last_handled:
                    st.session_state["_last_handled_click"] = click_tuple
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
                segments=segments,
                traffic_model=traffic_model,
                route_geojson=route_geojson,
                dark_mode=is_dark,
                center=map_center,
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

    # --- Active Bus Fleet Explorer (Main Tab) ---
    with fleet_tab_main:
        render_bus_tracker(processed_df, key_prefix="top_fleet")

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
        render_bus_tracker(processed_df, key_prefix="sub_fleet")

    with table_tab3:
        _render_predictions(processed_df, segments)


def _render_predictions(processed_df: pd.DataFrame, segments):
    """Render ML traffic speed predictions 30 and 60 minutes ahead with trend indicators."""
    st.markdown("### 🔮 Machine Learning Traffic Forecasting")
    st.caption(
        "Gradient Boosting Regressor forecasting segment velocity 30 & 60 minutes into the future based on temporal cyclicality and bus velocity trends."
    )

    # Build predictor
    if "predictor" not in st.session_state:
        predictor = TrafficPredictor()
        # Prepare training data: attach segment_id via snap_to_segment
        if processed_df is not None and not processed_df.empty:
            from traffic.segments import snap_to_segment
            train_rows = []
            for _, row in processed_df.head(300).iterrows():
                if pd.notna(row.get("lat")) and pd.notna(row.get("lon")) and pd.notna(row.get("speed")):
                    seg = snap_to_segment(float(row["lat"]), float(row["lon"]), segments)
                    train_rows.append({
                        "segment_id": seg.segment_id,
                        "speed": float(row["speed"]),
                        "timestamp": row.get("timestamp", "2026-11-21 09:00:00"),
                    })
            if train_rows:
                predictor.train(pd.DataFrame(train_rows))

        st.session_state["predictor"] = predictor

    predictor = st.session_state["predictor"]
    current_model = st.session_state.get("traffic_model", TrafficModel())

    # Build forecast rows
    pred_rows = []
    bottlenecks_30m = []

    for seg in segments[:30]:  # Top 30 Delhi segments
        cur_spd = current_model.get_segment_speed(seg.segment_id)
        try:
            speed_30 = predictor.predict(seg.segment_id, future_minutes=30)
            speed_60 = predictor.predict(seg.segment_id, future_minutes=60)
        except Exception:
            speed_30 = speed_60 = cur_spd

        diff_30 = speed_30 - cur_spd
        if diff_30 >= 1.5:
            trend_icon = "🟢 Speeding Up ↗"
        elif diff_30 <= -1.5:
            trend_icon = "🔴 Slowing Down ↘"
            if speed_30 < 15.0:
                bottlenecks_30m.append(f"{seg.road_name} ({speed_30:.1f} km/h)")
        else:
            trend_icon = "⚪ Steady ➔"

        pred_rows.append({
            "Road Corridor": seg.road_name,
            "Type": seg.road_type.title(),
            "Current (km/h)": round(cur_spd, 1),
            "⏱️ +30 min (km/h)": round(speed_30, 1),
            "⏱️ +60 min (km/h)": round(speed_60, 1),
            "Expected Trend": trend_icon,
        })

    # Alert Banner if anticipated bottlenecks
    if bottlenecks_30m:
        st.warning(
            f"⚠️ **Anticipated Slowdowns (+30m):** {', '.join(bottlenecks_30m[:3])}"
            + (f" and {len(bottlenecks_30m)-3} more" if len(bottlenecks_30m) > 3 else "")
            + " — Dynamic journey planner will proactively route buses around these corridors."
        )

    if pred_rows:
        pred_df = pd.DataFrame(pred_rows)
        st.dataframe(
            pred_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Current (km/h)": st.column_config.ProgressColumn(
                    "Current Speed",
                    format="%.1f km/h",
                    min_value=0,
                    max_value=60,
                ),
                "⏱️ +30 min (km/h)": st.column_config.ProgressColumn(
                    "+30m Forecast",
                    format="%.1f km/h",
                    min_value=0,
                    max_value=60,
                ),
                "⏱️ +60 min (km/h)": st.column_config.ProgressColumn(
                    "+60m Forecast",
                    format="%.1f km/h",
                    min_value=0,
                    max_value=60,
                ),
            },
        )
    else:
        st.info("Not enough data to generate predictions yet.")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
