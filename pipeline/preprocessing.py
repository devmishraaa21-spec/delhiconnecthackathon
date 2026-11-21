"""
GPS cleaning and preprocessing pipeline for Delhi bus telemetry.

Functions
---------
- clean_gps          – remove drift, interpolate gaps, discard speed outliers
- filter_dwell_times – mark dwell-time pings near known bus stops using
                       spatial proximity, speed threshold, and DBSCAN clustering
- compute_segment_speeds – derive per-segment speeds between non-dwelling pings
"""

from __future__ import annotations

import math
from typing import List

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EARTH_RADIUS_KM = 6371.0
MAX_SPEED_KMH = 80.0  # hard cap for buses
MAX_DRIFT_M = 500.0    # discard points further than this from nearest route point


# ---------------------------------------------------------------------------
# Haversine helpers
# ---------------------------------------------------------------------------
def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two lat/lon points."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * 1000 * math.asin(math.sqrt(a))


def _haversine_m_vec(
    lat1: "pd.Series | np.ndarray",
    lon1: "pd.Series | np.ndarray",
    lat2: "pd.Series | np.ndarray",
    lon2: "pd.Series | np.ndarray",
) -> np.ndarray:
    """Vectorised haversine returning distances in metres."""
    rlat1 = np.radians(lat1)
    rlat2 = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(rlat1) * np.cos(rlat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * 1000 * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------
# 1. clean_gps
# ---------------------------------------------------------------------------
def clean_gps(df: pd.DataFrame) -> pd.DataFrame:
    """Remove GPS drift, interpolate missing pings, discard speed outliers.

    Steps
    -----
    1. Drop rows whose ``speed`` exceeds ``MAX_SPEED_KMH``.
    2. For each bus, compute point-to-point distance; drop points that jumped
       more than ``MAX_DRIFT_M`` from the previous ping (GPS teleportation).
    3. Interpolate small time gaps (≤ 60 s) in lat/lon linearly within each
       bus trajectory.

    Parameters
    ----------
    df : pd.DataFrame
        Raw telemetry with columns ``bus_id, route_id, timestamp, lat, lon,
        speed, heading``.

    Returns
    -------
    pd.DataFrame
        Cleaned copy (original is not mutated).
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values(["bus_id", "timestamp"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 1. Remove speed outliers
    df = df[df["speed"] <= MAX_SPEED_KMH].copy()

    # 2. Remove GPS drift (large jumps from previous ping)
    keep_mask = pd.Series(True, index=df.index)
    for _bus_id, grp in df.groupby("bus_id"):
        if len(grp) < 2:
            continue
        idx = grp.index
        dists = _haversine_m_vec(
            grp["lat"].iloc[:-1].values,
            grp["lon"].iloc[:-1].values,
            grp["lat"].iloc[1:].values,
            grp["lon"].iloc[1:].values,
        )
        # First point of each bus is always kept
        bad = np.where(dists > MAX_DRIFT_M)[0] + 1  # offset by 1 (skip first)
        keep_mask.iloc[idx[bad]] = False

    df = df[keep_mask].copy()
    df.reset_index(drop=True, inplace=True)

    # 3. Interpolate small gaps (≤ 60 s) per bus ONLY when there are multiple pings
    interpolated_parts: list[pd.DataFrame] = []
    for _bus_id, grp in df.groupby("bus_id"):
        if len(grp) < 2:
            interpolated_parts.append(grp)
            continue
        try:
            grp = grp.copy()
            grp.set_index("timestamp", inplace=True)
            grp = grp.resample("10s").asfreq()
            grp[["lat", "lon"]] = grp[["lat", "lon"]].interpolate(method="time", limit=6)
            for col in ["bus_id", "route_id"]:
                if col in grp.columns:
                    grp[col] = grp[col].ffill().bfill()
            for col in ["speed", "heading"]:
                if col in grp.columns:
                    grp[col] = grp[col].interpolate(method="linear", limit=6)
            grp.dropna(subset=["lat", "lon", "bus_id"], inplace=True)
            grp.reset_index(inplace=True)
            interpolated_parts.append(grp)
        except Exception:
            interpolated_parts.append(grp.reset_index() if "timestamp" not in grp.columns else grp)

    if interpolated_parts:
        df = pd.concat(interpolated_parts, ignore_index=True)
    df.sort_values(["bus_id", "timestamp"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ---------------------------------------------------------------------------
# 2. filter_dwell_times
# ---------------------------------------------------------------------------
def filter_dwell_times(
    df: pd.DataFrame,
    bus_stops: List[dict],
    radius_m: float = 50.0,
    speed_threshold: float = 3.0,
) -> pd.DataFrame:
    """Identify dwell-time pings using proximity + speed + DBSCAN clustering.

    A ping is marked as *dwelling* when **all** of:
    - It is within ``radius_m`` metres of a known bus stop.
    - Its ``speed`` is at or below ``speed_threshold`` km/h.
    - It belongs to a DBSCAN cluster of ≥ 2 nearby low-speed pings (eps
      derived from ``radius_m``, using lat/lon as features and
      ``haversine`` metric approximation).

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned telemetry (output of ``clean_gps``).
    bus_stops : list[dict]
        List of dicts with keys ``stop_id``, ``name``, ``lat``, ``lon``.
    radius_m : float
        Proximity radius in metres to consider a ping near a stop.
    speed_threshold : float
        Maximum speed (km/h) to be considered stationary.

    Returns
    -------
    pd.DataFrame
        Copy of *df* with an added boolean column ``is_dwelling``. All
        rows are kept.
    """
    df = df.copy()
    df["is_dwelling"] = False

    if df.empty or not bus_stops:
        return df

    stop_lats = np.array([s["lat"] for s in bus_stops])
    stop_lons = np.array([s["lon"] for s in bus_stops])

    # --- Step 1: proximity to any bus stop ---
    near_stop = np.zeros(len(df), dtype=bool)
    for i in range(len(bus_stops)):
        dists = _haversine_m_vec(
            df["lat"].values,
            df["lon"].values,
            np.full(len(df), stop_lats[i]),
            np.full(len(df), stop_lons[i]),
        )
        near_stop |= dists <= radius_m

    # --- Step 2: low speed ---
    low_speed = df["speed"].values <= speed_threshold

    candidate_mask = near_stop & low_speed
    candidate_idx = np.where(candidate_mask)[0]

    if len(candidate_idx) < 2:
        return df

    # --- Step 3: DBSCAN on candidates (per bus) ---
    for _bus_id, grp in df.iloc[candidate_idx].groupby("bus_id"):
        if len(grp) < 2:
            continue
        coords_rad = np.radians(grp[["lat", "lon"]].values)
        # eps in radians: radius_m / earth_radius_m
        eps_rad = radius_m / (EARTH_RADIUS_KM * 1000)
        clustering = DBSCAN(
            eps=eps_rad,
            min_samples=2,
            metric="haversine",
        ).fit(coords_rad)
        clustered = clustering.labels_ >= 0
        df.loc[grp.index[clustered], "is_dwelling"] = True

    return df


# ---------------------------------------------------------------------------
# 3. compute_segment_speeds
# ---------------------------------------------------------------------------
def compute_segment_speeds(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate speed between consecutive non-dwelling GPS points per bus.

    For each bus, non-dwelling pings are taken in chronological order and
    point-to-point speed is calculated as ``distance / time_delta``.  The
    result is stored in a new column ``segment_speed_kmh``.

    Parameters
    ----------
    df : pd.DataFrame
        Telemetry with an ``is_dwelling`` column (output of
        ``filter_dwell_times``).

    Returns
    -------
    pd.DataFrame
        Copy with an added ``segment_speed_kmh`` column (NaN for the first
        ping of each bus and for dwelling pings).
    """
    df = df.copy()
    df["segment_speed_kmh"] = np.nan
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    for _bus_id, grp in df.groupby("bus_id"):
        moving = grp[~grp["is_dwelling"]].sort_values("timestamp")
        if len(moving) < 2:
            continue

        lats = moving["lat"].values
        lons = moving["lon"].values
        times = moving["timestamp"].values

        dists_m = _haversine_m_vec(lats[:-1], lons[:-1], lats[1:], lons[1:])
        dt_s = (times[1:] - times[:-1]) / np.timedelta64(1, "s")

        # Avoid division by zero
        dt_s = np.where(dt_s == 0, np.nan, dt_s)
        speeds = (dists_m / 1000.0) / (dt_s / 3600.0)  # km/h

        # Assign to the *second* ping of each pair
        df.loc[moving.index[1:], "segment_speed_kmh"] = speeds

    return df
