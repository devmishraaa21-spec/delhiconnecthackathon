"""
Synthetic GPS telemetry generator for Delhi buses.

Generates realistic GPS pings for 100 buses across defined routes,
with congestion-aware speed profiles, dwell times, GPS noise, and
time-of-day rush-hour patterns.

Usage:
    python generate_synthetic.py              # 2 hours of data (default)
    python generate_synthetic.py --hours 4    # 4 hours of data
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import random
import sys
from datetime import datetime, timedelta
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Import stop / route data from sibling module
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from delhi_bus_stops import (  # noqa: E402
    BUS_ROUTES,
    BUS_STOPS,
    CONGESTED_STOPS,
    EXPRESSWAY_STOPS,
    RING_ROAD_STOPS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_BUSES = 100
DEFAULT_HOURS = 2
PING_INTERVAL_MIN = 10  # seconds
PING_INTERVAL_MAX = 30
EARTH_RADIUS_KM = 6371.0
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_telemetry.csv")

# Speed ranges in km/h by zone type
SPEED_CONGESTED = (5.0, 15.0)
SPEED_ARTERIAL = (20.0, 40.0)
SPEED_RING_ROAD = (40.0, 60.0)
SPEED_EXPRESSWAY = (40.0, 60.0)

# Rush hour windows (hour-of-day, 24h)
MORNING_RUSH = (8, 10)
EVENING_RUSH = (17, 20)
RUSH_SPEED_FACTOR = 0.6  # multiply speed by this during rush hours

# Dwell-time range at stops (seconds)
DWELL_MIN = 30
DWELL_MAX = 120

# GPS noise in metres
GPS_NOISE_MIN = 10.0
GPS_NOISE_MAX = 50.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_stop_lookup: dict[str, dict] = {s["stop_id"]: s for s in BUS_STOPS}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return initial bearing in degrees from point 1 to point 2."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _add_gps_noise(lat: float, lon: float) -> Tuple[float, float]:
    """Add random GPS drift in [GPS_NOISE_MIN, GPS_NOISE_MAX] metres."""
    noise_m = random.uniform(GPS_NOISE_MIN, GPS_NOISE_MAX)
    angle = random.uniform(0, 2 * math.pi)
    dlat = (noise_m * math.cos(angle)) / 111_320.0
    dlon = (noise_m * math.sin(angle)) / (111_320.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def _speed_for_segment(from_id: str, to_id: str) -> Tuple[float, float]:
    """Return (min_speed, max_speed) in km/h for a route segment."""
    if from_id in RING_ROAD_STOPS or to_id in RING_ROAD_STOPS:
        return SPEED_RING_ROAD
    if from_id in EXPRESSWAY_STOPS or to_id in EXPRESSWAY_STOPS:
        return SPEED_EXPRESSWAY
    if from_id in CONGESTED_STOPS or to_id in CONGESTED_STOPS:
        return SPEED_CONGESTED
    return SPEED_ARTERIAL


def _is_rush_hour(dt: datetime) -> bool:
    h = dt.hour
    return MORNING_RUSH[0] <= h < MORNING_RUSH[1] or EVENING_RUSH[0] <= h < EVENING_RUSH[1]


def _interpolate(lat1: float, lon1: float, lat2: float, lon2: float, frac: float) -> Tuple[float, float]:
    """Linear interpolation between two points (good enough for short city segments)."""
    return lat1 + (lat2 - lat1) * frac, lon1 + (lon2 - lon1) * frac


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------
def _generate_bus_telemetry(
    bus_id: str,
    route: dict,
    start_time: datetime,
    duration_hours: float,
) -> List[dict]:
    """Generate GPS pings for one bus travelling its route back and forth."""

    stop_ids: list[str] = route["stop_ids"]
    route_id = route["route_id"]
    end_time = start_time + timedelta(hours=duration_hours)

    records: list[dict] = []
    current_time = start_time
    # Start at the first stop
    direction = 1  # 1 = forward, -1 = reverse
    seg_idx = 0  # index into stop_ids for the *from* stop

    while current_time < end_time:
        from_sid = stop_ids[seg_idx]
        to_idx = seg_idx + direction
        # Reverse at ends
        if to_idx < 0 or to_idx >= len(stop_ids):
            direction *= -1
            to_idx = seg_idx + direction
        to_sid = stop_ids[to_idx]

        from_stop = _stop_lookup[from_sid]
        to_stop = _stop_lookup[to_sid]

        seg_dist_km = _haversine(from_stop["lat"], from_stop["lon"], to_stop["lat"], to_stop["lon"])
        if seg_dist_km < 0.001:
            seg_idx = to_idx
            continue

        # Determine speed for segment
        spd_lo, spd_hi = _speed_for_segment(from_sid, to_sid)
        base_speed_kmh = random.uniform(spd_lo, spd_hi)
        if _is_rush_hour(current_time):
            base_speed_kmh *= RUSH_SPEED_FACTOR

        base_speed_kmh = max(base_speed_kmh, 2.0)
        seg_time_s = (seg_dist_km / base_speed_kmh) * 3600

        heading = _bearing(from_stop["lat"], from_stop["lon"], to_stop["lat"], to_stop["lon"])

        # Emit pings along the segment
        elapsed_in_seg = 0.0
        while elapsed_in_seg < seg_time_s and current_time < end_time:
            frac = min(elapsed_in_seg / seg_time_s, 1.0)
            lat, lon = _interpolate(
                from_stop["lat"], from_stop["lon"],
                to_stop["lat"], to_stop["lon"],
                frac,
            )
            lat, lon = _add_gps_noise(lat, lon)

            # Slight per-ping speed jitter (±15 %)
            jitter = random.uniform(0.85, 1.15)
            ping_speed = base_speed_kmh * jitter

            records.append(
                {
                    "bus_id": bus_id,
                    "route_id": route_id,
                    "timestamp": current_time.isoformat(),
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "speed": round(ping_speed, 2),
                    "heading": round(heading + random.uniform(-5, 5), 2),
                }
            )

            interval = random.randint(PING_INTERVAL_MIN, PING_INTERVAL_MAX)
            current_time += timedelta(seconds=interval)
            elapsed_in_seg += interval

        # --- Dwell at the destination stop ---
        if current_time < end_time:
            dwell = random.randint(DWELL_MIN, DWELL_MAX)
            dwell_end = current_time + timedelta(seconds=dwell)
            while current_time < dwell_end and current_time < end_time:
                dlat, dlon = _add_gps_noise(to_stop["lat"], to_stop["lon"])
                records.append(
                    {
                        "bus_id": bus_id,
                        "route_id": route_id,
                        "timestamp": current_time.isoformat(),
                        "lat": round(dlat, 6),
                        "lon": round(dlon, 6),
                        "speed": round(random.uniform(0, 2.0), 2),
                        "heading": round(heading + random.uniform(-10, 10), 2),
                    }
                )
                current_time += timedelta(seconds=random.randint(PING_INTERVAL_MIN, PING_INTERVAL_MAX))

        seg_idx = to_idx

    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(hours: float = DEFAULT_HOURS) -> str:
    random.seed(42)
    # Assign buses to routes round-robin
    all_records: list[dict] = []
    start_dt = datetime(2026, 11, 18, 7, 0, 0)  # start at 7 AM

    for bus_num in range(NUM_BUSES):
        route = BUS_ROUTES[bus_num % len(BUS_ROUTES)]
        bus_id = f"BUS-{bus_num + 1:03d}"
        # Stagger start times up to 15 minutes
        offset = random.randint(0, 900)
        bus_start = start_dt + timedelta(seconds=offset)
        records = _generate_bus_telemetry(bus_id, route, bus_start, hours)
        all_records.extend(records)

    # Sort globally by timestamp
    all_records.sort(key=lambda r: r["timestamp"])

    # Write CSV
    fieldnames = ["bus_id", "route_id", "timestamp", "lat", "lon", "speed", "heading"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"Generated {len(all_records):,} GPS pings for {NUM_BUSES} buses over {hours}h")
    print(f"Saved to {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Delhi bus telemetry")
    parser.add_argument("--hours", type=float, default=DEFAULT_HOURS, help="Duration in hours")
    args = parser.parse_args()
    main(args.hours)
