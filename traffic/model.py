"""Traffic speed model for Delhi bus network."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

import pandas as pd

from .segments import RoadSegment, snap_to_segment

# Free-flow speeds (km/h) by road type
FREE_FLOW_SPEEDS: dict[str, float] = {
    "expressway": 60.0,
    "arterial": 40.0,
    "local": 30.0,
    "congested_zone": 15.0,
}

# Congestion thresholds as fraction of free-flow speed
_CONGESTION_THRESHOLDS = {
    "free_flow": 0.75,
    "moderate": 0.50,
    "heavy": 0.25,
}


class TrafficModel:
    """Computes and maintains real-time speed estimates per road segment."""

    def __init__(self) -> None:
        # segment_id -> list of observed speeds (km/h)
        self._observations: dict[str, list[float]] = defaultdict(list)
        # segment_id -> current estimated speed (km/h)
        self._speeds: dict[str, float] = {}
        # segment_id -> road_type
        self._road_types: dict[str, str] = {}
        # segment_id -> midpoint (lat, lon)
        self._midpoints: dict[str, tuple[float, float]] = {}

    def update(self, telemetry_df: pd.DataFrame, segments: List[RoadSegment]) -> None:
        """Process bus telemetry to compute real-time speeds per road segment.

        Filters out dwelling buses and computes the average speed of moving buses
        on each segment. Segments without recent observations fall back to free-flow.
        """
        self._road_types.clear()
        self._midpoints.clear()
        self._observations.clear()

        for seg in segments:
            self._road_types[seg.segment_id] = seg.road_type
            self._midpoints[seg.segment_id] = (
                (seg.start_lat + seg.end_lat) / 2.0,
                (seg.start_lon + seg.end_lon) / 2.0,
            )

        # Filter out dwelling buses if column exists
        moving_df = telemetry_df
        if "is_dwelling" in telemetry_df.columns:
            moving_df = telemetry_df[~telemetry_df["is_dwelling"].astype(bool)]

        # Collect speeds snapped to segments
        if not moving_df.empty and "lat" in moving_df.columns and "lon" in moving_df.columns:
            has_speed = "speed" in moving_df.columns
            for _, row in moving_df.iterrows():
                spd = float(row["speed"]) if has_speed and pd.notna(row["speed"]) else 0.0
                if spd > 0.0:
                    seg = snap_to_segment(float(row["lat"]), float(row["lon"]), segments)
                    self._observations[seg.segment_id].append(spd)

        # Average speeds per segment
        for seg in segments:
            sid = seg.segment_id
            obs = self._observations.get(sid, [])
            if obs:
                self._speeds[sid] = round(sum(obs) / len(obs), 1)
            else:
                self._speeds[sid] = FREE_FLOW_SPEEDS.get(seg.road_type, 30.0)

    def get_segment_speed(self, segment_id: str) -> float:
        """Return current speed on a segment in km/h."""
        return self._speeds.get(segment_id, 30.0)

    def get_congestion_level(self, segment_id: str) -> str:
        """Return 'free_flow', 'moderate', 'heavy', or 'gridlock'."""
        speed = self.get_segment_speed(segment_id)
        road_type = self._road_types.get(segment_id, "arterial")
        ff = FREE_FLOW_SPEEDS.get(road_type, 40.0)

        if ff <= 0.0:
            return "gridlock"

        ratio = speed / ff
        if ratio >= _CONGESTION_THRESHOLDS["free_flow"]:
            return "free_flow"
        elif ratio >= _CONGESTION_THRESHOLDS["moderate"]:
            return "moderate"
        elif ratio >= _CONGESTION_THRESHOLDS["heavy"]:
            return "heavy"
        else:
            return "gridlock"

    def get_all_speeds(self) -> Dict[str, float]:
        """Return all segment speeds as {segment_id: speed_kmh}."""
        return dict(self._speeds)

    def get_heatmap_data(self) -> List[Dict[str, Any]]:
        """Return list of {lat, lon, weight, intensity} for congestion heatmap visualization.

        Weight is 0.0 (free flow) to 1.0 (gridlock).
        """
        heatmap: list[dict[str, Any]] = []
        for sid, (lat, lon) in self._midpoints.items():
            speed = self.get_segment_speed(sid)
            road_type = self._road_types.get(sid, "arterial")
            ff = FREE_FLOW_SPEEDS.get(road_type, 40.0)

            if ff > 0.0:
                # Slower speed = higher congestion weight
                weight = max(0.0, min(1.0, 1.0 - (speed / ff)))
            else:
                weight = 1.0

            w_val = round(weight, 3)
            heatmap.append({
                "lat": lat,
                "lon": lon,
                "weight": w_val,
                "intensity": w_val,  # For compatibility with folium HeatMap
            })
        return heatmap
