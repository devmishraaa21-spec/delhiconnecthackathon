"""
Data ingestion module for Delhi bus telemetry.

Provides loading from CSV, simulated real-time streaming via batched yields,
and live real-time ingestion from the official Delhi Open Transit Data (OTD) GTFS-RT feed.
"""

from __future__ import annotations

import time
from typing import Generator, Optional
import pandas as pd

# Optional dependencies for live GTFS-RT ingestion
try:
    import requests
except ImportError:
    requests = None

try:
    from google.transit import gtfs_realtime_pb2
except ImportError:
    gtfs_realtime_pb2 = None


# Official Delhi Open Transit Data API base endpoint
DELHI_OTD_BASE_URL = "https://otd.delhi.gov.in/api/realtime/VehiclePositions.pb"


def load_telemetry(filepath: str) -> pd.DataFrame:
    """Load a GPS telemetry CSV into a DataFrame.

    Parameters
    ----------
    filepath : str
        Path to the CSV file with columns
        [bus_id, route_id, timestamp, lat, lon, speed, heading].

    Returns
    -------
    pd.DataFrame
        Parsed DataFrame with ``timestamp`` as a datetime column, sorted
        chronologically.
    """
    df = pd.read_csv(filepath)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def stream_telemetry(
    df: pd.DataFrame,
    batch_size: int = 64,
) -> Generator[pd.DataFrame, None, None]:
    """Simulate real-time streaming by yielding fixed-size batches.

    Parameters
    ----------
    df : pd.DataFrame
        Full telemetry DataFrame (should be sorted by timestamp).
    batch_size : int
        Number of rows per batch.

    Yields
    ------
    pd.DataFrame
        A slice of ``df`` with at most ``batch_size`` rows.
    """
    for start in range(0, len(df), batch_size):
        yield df.iloc[start : start + batch_size].copy()


def parse_gtfs_rt_feed(content: bytes) -> pd.DataFrame:
    """Parse raw GTFS-RT Protocol Buffer bytes into a standardized DataFrame.

    Parameters
    ----------
    content : bytes
        Raw binary payload from the Delhi OTD VehiclePositions.pb endpoint.

    Returns
    -------
    pd.DataFrame
        Standardized DataFrame with columns:
        [bus_id, route_id, timestamp, lat, lon, speed, heading]
    """
    if gtfs_realtime_pb2 is None:
        raise ImportError(
            "The `gtfs-realtime-bindings` package is required to parse GTFS-RT feeds. "
            "Please install it with: pip install gtfs-realtime-bindings protobuf"
        )

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(content)

    records = []
    current_ts = pd.Timestamp.now()

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue

        veh = entity.vehicle
        pos = veh.position

        # Vehicle & Trip identifiers
        bus_id = veh.vehicle.id if veh.HasField("vehicle") and veh.vehicle.id else entity.id
        route_id = veh.trip.route_id if veh.HasField("trip") and veh.trip.route_id else "DTC_ROUTE"

        # Timestamp (convert POSIX epoch to UTC or local datetime)
        if veh.HasField("timestamp") and veh.timestamp > 0:
            ts = pd.to_datetime(veh.timestamp, unit="s")
        else:
            ts = current_ts

        # Speed in GTFS-RT is in meters per second; convert to km/h
        speed_kmh = (pos.speed * 3.6) if (pos.HasField("speed") and pos.speed >= 0) else 0.0

        # Bearing / heading in degrees (0..360)
        heading = pos.bearing if pos.HasField("bearing") else 0.0

        records.append({
            "bus_id": str(bus_id),
            "route_id": str(route_id),
            "timestamp": ts,
            "lat": float(pos.latitude),
            "lon": float(pos.longitude),
            "speed": float(speed_kmh),
            "heading": float(heading),
        })

    if not records:
        return pd.DataFrame(columns=["bus_id", "route_id", "timestamp", "lat", "lon", "speed", "heading"])

    df = pd.DataFrame(records)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def fetch_live_delhi_otd(
    api_key: str,
    base_url: str = DELHI_OTD_BASE_URL,
    timeout: int = 15,
) -> pd.DataFrame:
    """Fetch live real-time vehicle positions from Delhi Open Transit Data (OTD).

    Parameters
    ----------
    api_key : str
        Private API authorization key obtained from https://otd.delhi.gov.in/
    base_url : str
        URL to the GTFS-RT VehiclePositions.pb endpoint.
    timeout : int
        HTTP request timeout in seconds.

    Returns
    -------
    pd.DataFrame
        Standardized DataFrame with columns:
        [bus_id, route_id, timestamp, lat, lon, speed, heading]
    """
    if requests is None:
        raise ImportError(
            "The `requests` package is required to fetch live HTTP data. "
            "Please install it with: pip install requests"
        )

    if not api_key or not api_key.strip():
        raise ValueError("An API key is required to query the Delhi Open Transit Data (OTD) API.")

    url = f"{base_url}?key={api_key.strip()}"
    headers = {
        "User-Agent": "Delhi-Bus-Traffic-Journey-Planner/1.0 (Hackathon Project)"
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch live Delhi bus telemetry. HTTP status code {response.status_code}: {response.text[:200]}"
        )

    return parse_gtfs_rt_feed(response.content)
