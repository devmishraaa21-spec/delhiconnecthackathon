"""
Dashboard UI components for the Delhi Bus Traffic Model.
Renders sidebar controls, metric cards, traffic tables, and bus tracker.
"""

import streamlit as st
import pandas as pd
from typing import Tuple, Optional


def _inject_custom_css():
    """Inject Delhi-themed custom CSS."""
    st.markdown(
        """
        <style>
        /* Delhi tricolor accent bar */
        .stApp > header {
            background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
            height: 4px;
        }

        /* Metric card styling */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #FF6B35;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.15);
        }
        div[data-testid="stMetric"] label {
            color: #FF9933 !important;
            font-weight: 600;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 1.8rem !important;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a1a 0%, #16213e 100%);
            border-right: 2px solid #FF6B35;
        }
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stSlider label {
            color: #FF9933 !important;
        }

        /* Hero section */
        .hero-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #FF9933, #FF6B35);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0;
        }
        .hero-subtitle {
            color: #94a3b8;
            font-size: 1.1rem;
            margin-top: 4px;
        }
        .hero-divider {
            height: 3px;
            background: linear-gradient(90deg, #FF9933 0%, #138808 50%, transparent 100%);
            border: none;
            margin: 12px 0 24px 0;
        }

        /* Table styling */
        .dataframe th {
            background-color: #16213e !important;
            color: #FF9933 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    """Render the hero / title section of the dashboard."""
    st.markdown(
        """
        <div>
            <div class="hero-title">🚌 Delhi Bus Traffic Model & Journey Planner</div>
            <div class="hero-subtitle">
                Real-time traffic analysis, congestion heatmaps & intelligent route planning
                for Delhi's bus network — powered by live GPS telemetry.
            </div>
            <hr class="hero-divider">
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(bus_stops: Optional[list] = None) -> Tuple[Optional[tuple], Optional[tuple]]:
    """
    Streamlit sidebar with source / destination selection and controls.

    Parameters
    ----------
    bus_stops : list[dict], optional
        List of bus-stop dicts with keys name, lat, lon. If omitted,
        attempts to load from data.delhi_bus_stops.BUS_STOPS.

    Returns
    -------
    tuple
        (start_coords, end_coords) where each is (lat, lon) or None.
    """
    if bus_stops is None:
        try:
            from data.delhi_bus_stops import BUS_STOPS
            bus_stops = BUS_STOPS
        except Exception:
            bus_stops = []

    with st.sidebar:
        st.markdown("## 📡 Telemetry Source")
        data_source = st.radio(
            "Select Telemetry Feed",
            ["🟡 Synthetic Simulation", "🟢 Live Delhi OTD Feed"],
            index=0,
            horizontal=False,
            help="Switch between realistic simulation and official Delhi Open Transit Data API",
        )
        st.session_state["data_source"] = data_source

        if data_source == "🟢 Live Delhi OTD Feed":
            api_key = st.text_input(
                "Delhi OTD API Key",
                value=st.session_state.get("otd_api_key", ""),
                type="password",
                help="Obtain your free API key at https://otd.delhi.gov.in/",
            )
            st.session_state["otd_api_key"] = api_key
            st.caption("🔑 Request a key at [otd.delhi.gov.in](https://otd.delhi.gov.in/)")
            if st.button("📡 Fetch Live Delhi Buses", use_container_width=True):
                st.session_state["fetch_live_requested"] = True

        st.markdown("---")
        st.markdown("## 🗺️ Journey Planner")
        st.markdown("---")

        # --- Input mode ---
        input_mode = st.radio(
            "Select input mode",
            ["Bus Stop Dropdown", "Manual Coordinates"],
            horizontal=True,
        )

        start_coords: Optional[tuple] = None
        end_coords: Optional[tuple] = None

        if input_mode == "Bus Stop Dropdown":
            stop_names = [s["name"] for s in bus_stops]

            src_name = st.selectbox("🟢 Source Stop", stop_names, index=0)
            dst_name = st.selectbox(
                "🔴 Destination Stop",
                stop_names,
                index=min(5, len(stop_names) - 1),
            )

            src_stop = next((s for s in bus_stops if s["name"] == src_name), None)
            dst_stop = next((s for s in bus_stops if s["name"] == dst_name), None)

            if src_stop:
                start_coords = (src_stop["lat"], src_stop["lon"])
            if dst_stop:
                end_coords = (dst_stop["lat"], dst_stop["lon"])
        else:
            st.markdown("**🟢 Start Coordinates**")
            s_lat = st.number_input("Start Latitude", value=28.6328, format="%.4f", key="slat")
            s_lon = st.number_input("Start Longitude", value=77.2197, format="%.4f", key="slon")
            start_coords = (s_lat, s_lon)

            st.markdown("**🔴 End Coordinates**")
            e_lat = st.number_input("End Latitude", value=28.5733, format="%.4f", key="elat")
            e_lon = st.number_input("End Longitude", value=77.2109, format="%.4f", key="elon")
            end_coords = (e_lat, e_lon)

        st.markdown("---")
        st.markdown("### 🗺️ Map Display")
        map_theme = st.selectbox(
            "Base Map Style",
            ["Dark Matter (Command Center)", "Clean Light", "OpenStreetMap"],
            index=0,
            help="Choose the visual styling of Delhi's road base map",
        )
        st.session_state["map_theme"] = map_theme

        show_fleet = st.checkbox("Show Live Bus Fleet (Clusters)", value=True)
        st.session_state["show_bus_fleet"] = show_fleet

        st.markdown("---")

        # --- Time-of-day selector ---
        st.markdown("### ⏰ Time of Day")
        time_of_day = st.slider(
            "Hour (24h format)",
            min_value=0,
            max_value=23,
            value=9,
            format="%d:00",
        )
        st.session_state["time_of_day"] = time_of_day

        st.markdown("---")

        # --- Refresh & auto-refresh ---
        st.markdown("### 🔄 Data Controls")
        refresh = st.button("🔃 Refresh Traffic Data", use_container_width=True)
        st.session_state["refresh_requested"] = refresh

        auto_refresh = st.toggle("Auto-refresh (30s)", value=False)
        st.session_state["auto_refresh"] = auto_refresh

        st.markdown("---")
        st.caption("Delhi Bus Traffic Model — Hackathon 2026")

    return start_coords, end_coords


def render_metrics(route: dict):
    """
    Display key journey metrics as st.metric cards.

    Parameters
    ----------
    route : dict
        Route dict with keys: distance_km, eta_minutes, congestion_summary.
    """
    if not route:
        st.info("Plan a route to see journey metrics.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🛣️ Distance",
            value=f"{route.get('distance_km', 0):.1f} km",
        )

    with col2:
        eta = route.get("eta_minutes", 0)
        hours, mins = divmod(int(eta), 60)
        eta_str = f"{hours}h {mins}m" if hours else f"{int(eta)} min"
        st.metric(label="⏱️ ETA", value=eta_str)

    with col3:
        congestion = route.get("congestion_summary", {})
        if isinstance(congestion, dict):
            dominant = max(congestion, key=congestion.get) if congestion else "N/A"
        else:
            dominant = str(congestion)
        st.metric(label="🚦 Congestion", value=dominant.replace("_", " ").title())

    with col4:
        num_segments = len(route.get("segments", []))
        st.metric(label="📍 Segments", value=str(num_segments))


def render_traffic_table(traffic_model, segments: list):
    """
    Table showing road segment speeds and congestion levels.

    Parameters
    ----------
    traffic_model : TrafficModel
        Traffic model instance.
    segments : list
        List of RoadSegment objects.
    """
    st.markdown("### 🚗 Road Segment Traffic")

    rows = []
    for seg in segments:
        try:
            speed = traffic_model.get_segment_speed(seg.segment_id)
            level = traffic_model.get_congestion_level(seg.segment_id)
        except Exception:
            speed = None
            level = "unknown"

        rows.append(
            {
                "Road": seg.road_name,
                "Type": seg.road_type,
                "Length (m)": f"{seg.length_m:.0f}",
                "Speed (km/h)": f"{speed:.1f}" if speed else "—",
                "Congestion": level.replace("_", " ").title() if level else "—",
            }
        )

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Congestion": st.column_config.TextColumn(
                    "Congestion",
                    help="Current congestion level for this segment",
                ),
            },
        )
    else:
        st.info("No segment data available yet.")


def render_bus_tracker(telemetry_df: pd.DataFrame):
    """
    Show active buses, their positions and speeds.

    Parameters
    ----------
    telemetry_df : pd.DataFrame
        GPS telemetry data with columns: bus_id, lat, lon, speed, timestamp.
    """
    st.markdown("### 🚌 Active Bus Tracker")

    if telemetry_df is None or telemetry_df.empty:
        st.info("No telemetry data available.")
        return

    # Get the latest position for each bus
    df = telemetry_df.copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        latest = df.sort_values("timestamp").groupby("bus_id").tail(1)
    else:
        latest = df.groupby("bus_id").tail(1)

    summary_rows = []
    for _, row in latest.iterrows():
        speed_val = row.get("speed", 0)
        if pd.notna(speed_val) and speed_val > 1:
            status = "🟢 Moving"
        else:
            status = "🔴 Stopped"

        summary_rows.append(
            {
                "Bus ID": row.get("bus_id", "—"),
                "Route": row.get("route_id", "—"),
                "Lat": f"{row.get('lat', 0):.4f}",
                "Lon": f"{row.get('lon', 0):.4f}",
                "Speed (km/h)": f"{speed_val:.1f}" if pd.notna(speed_val) else "—",
                "Status": status,
            }
        )

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Buses", len(summary_rows))
        with col2:
            moving = sum(1 for r in summary_rows if "Moving" in r["Status"])
            st.metric("Moving", moving)
        with col3:
            stopped = len(summary_rows) - moving
            st.metric("Stopped", stopped)

        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.info("No active buses found.")

