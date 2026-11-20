"""Lightweight ML traffic speed predictor with historical fallback."""

from __future__ import annotations

import warnings
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

# Check optional ML backends
_HAS_SKLEARN = False
try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import LabelEncoder
    _HAS_SKLEARN = True
except ImportError:
    pass

_HAS_XGBOOST = False
try:
    import xgboost as xgb
    _HAS_XGBOOST = True
except ImportError:
    pass


class TrafficPredictor:
    """Predicts traffic speed for road segments using gradient boosting or historical averages."""

    def __init__(self) -> None:
        self._model: Any = None
        self._label_encoder: Any = None
        self._segment_map: dict[str, int] = {}
        self._trained: bool = False

        # Fallback storage: segment_id -> {(hour, dow): [speeds]}
        self._history_buckets: dict[str, dict[tuple[int, int], list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # Segment global average speeds
        self._segment_global_avg: dict[str, float] = {}

    def train(self, historical_data: pd.DataFrame) -> None:
        """Train the model on historical traffic telemetry/records.

        Expected DataFrame columns: segment_id, speed, and timestamp (or hour_of_day, day_of_week).
        """
        if historical_data.empty:
            return

        df = historical_data.copy()

        # Extract temporal features
        if "timestamp" in df.columns:
            dt_series = pd.to_datetime(df["timestamp"])
            df["hour_of_day"] = dt_series.dt.hour
            df["day_of_week"] = dt_series.dt.dayofweek
        else:
            if "hour_of_day" not in df.columns:
                df["hour_of_day"] = 12
            if "day_of_week" not in df.columns:
                df["day_of_week"] = 2

        # Populate historical fallback buckets
        for _, row in df.iterrows():
            sid = str(row["segment_id"])
            h = int(row["hour_of_day"])
            dow = int(row["day_of_week"])
            spd = float(row["speed"]) if pd.notna(row["speed"]) else 30.0
            self._history_buckets[sid][(h, dow)].append(spd)

        # Compute global average speed per segment
        for sid, buckets in self._history_buckets.items():
            all_spds = [s for spds in buckets.values() for s in spds]
            self._segment_global_avg[sid] = sum(all_spds) / len(all_spds) if all_spds else 30.0

        df["historical_avg_speed"] = df["segment_id"].astype(str).map(self._segment_global_avg).fillna(30.0)

        # Encode segment_id
        if _HAS_SKLEARN:
            self._label_encoder = LabelEncoder()
            df["segment_id_encoded"] = self._label_encoder.fit_transform(df["segment_id"].astype(str))
        else:
            unique_sids = sorted(df["segment_id"].astype(str).unique())
            self._segment_map = {sid: idx for idx, sid in enumerate(unique_sids)}
            df["segment_id_encoded"] = df["segment_id"].astype(str).map(self._segment_map)

        # Train ML model if backend available
        feature_cols = ["hour_of_day", "day_of_week", "segment_id_encoded", "historical_avg_speed"]
        X = df[feature_cols].values
        y = df["speed"].values

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if _HAS_XGBOOST:
                    self._model = xgb.XGBRegressor(
                        n_estimators=80,
                        max_depth=4,
                        learning_rate=0.1,
                        verbosity=0,
                        random_state=42,
                    )
                    self._model.fit(X, y)
                elif _HAS_SKLEARN:
                    self._model = GradientBoostingRegressor(
                        n_estimators=80,
                        max_depth=4,
                        learning_rate=0.1,
                        random_state=42,
                    )
                    self._model.fit(X, y)
        except Exception:
            self._model = None

        self._trained = True

    def predict(self, segment_id: str, future_minutes: int = 30) -> float:
        """Predict speed (km/h) on segment_id at future_minutes from now."""
        target_time = datetime.now() + timedelta(minutes=future_minutes)
        future_hour = target_time.hour
        future_dow = target_time.weekday()

        hist_avg = self._segment_global_avg.get(segment_id, 30.0)

        # If ML model is trained, attempt inference
        if self._model is not None:
            try:
                if self._label_encoder is not None:
                    encoded_sid = int(self._label_encoder.transform([segment_id])[0])
                else:
                    encoded_sid = self._segment_map.get(segment_id, 0)

                features = [[future_hour, future_dow, encoded_sid, hist_avg]]
                pred_speed = float(self._model.predict(features)[0])
                return max(5.0, round(pred_speed, 1))
            except Exception:
                pass  # Fall through to fallback

        # Fallback to historical average
        return round(self._predict_fallback(segment_id, future_hour, future_dow, hist_avg), 1)

    def _predict_fallback(self, segment_id: str, hour: int, dow: int, hist_avg: float) -> float:
        """Heuristic / statistical fallback based on hour and day."""
        buckets = self._history_buckets.get(segment_id, {})
        # Exact hour & day match
        if (hour, dow) in buckets and buckets[(hour, dow)]:
            return sum(buckets[(hour, dow)]) / len(buckets[(hour, dow)])

        # Same hour, any day
        hour_spds = [s for (h, _), spds in buckets.items() if h == hour for s in spds]
        if hour_spds:
            return sum(hour_spds) / len(hour_spds)

        # Time-of-day rush hour heuristic adjustment
        # Morning rush: 8-10, Evening rush: 17-20
        speed = hist_avg
        if (8 <= hour <= 10) or (17 <= hour <= 20):
            speed *= 0.7  # 30% reduction during rush hours
        elif 0 <= hour <= 5:
            speed *= 1.25  # Faster late night

        return max(5.0, speed)
