"""
Disaster and climate-risk interpretations of cluster behavior.
"""

import pandas as pd
import numpy as np


class DisasterRiskInsights:
    """Estimate cluster-level hazard intensity using derived weather flags."""

    def generate(self, df: pd.DataFrame, label_col: str = "cluster") -> pd.DataFrame:
        rows = []

        for cluster_id, group in df.groupby(label_col):
            if cluster_id < 0:
                continue

            row = {
                "cluster": int(cluster_id),
                "points": int(len(group)),
                "heavy_rain_flag_mean": self._mean(group, "heavy_rain_flag"),
                "extreme_rain_flag_mean": self._mean(group, "extreme_rain_flag"),
                "precipitation_sum_mean": self._mean(group, "precipitation_sum"),
                "precipitation_sum_interannual_std_mean": self._mean(group, "precipitation_sum_interannual_std"),
                "wind_speed_120m_mean_mean": self._mean(group, "wind_speed_120m_mean"),
                "wind_power_density_120m_mean": self._mean(group, "wind_power_density_120m"),
                "cloud_cover_mean_interannual_std_mean": self._mean(group, "cloud_cover_mean_interannual_std"),
                "relative_humidity_2m_mean_mean": self._mean(group, "relative_humidity_2m_mean"),
                "solar_utilization_ratio_mean": self._mean(group, "solar_utilization_ratio"),
            }
            row["disaster_risk_score"] = self._risk_score(row)
            row["dominant_hazard"] = self._dominant_hazard(row)
            row["disaster_summary"] = self._summary(row)
            row["risk_recommendation"] = self._recommendation(row)
            rows.append(row)

        return pd.DataFrame(rows).sort_values("disaster_risk_score", ascending=False)

    @staticmethod
    def _mean(group: pd.DataFrame, column: str) -> float | None:
        return round(float(group[column].mean()), 3) if column in group.columns else None

    @staticmethod
    def _risk_score(row: dict) -> float:
        rain_risk = min((row.get("precipitation_sum_mean") or 0.0) / 3.0, 1.0)
        rain_variability = min((row.get("precipitation_sum_interannual_std_mean") or 0.0) / 150.0, 1.0)
        wind_risk = min((row.get("wind_power_density_120m_mean") or 0.0) / 3.0, 1.0)
        cloud_variability = min((row.get("cloud_cover_mean_interannual_std_mean") or 0.0) / 10.0, 1.0)
        humidity_risk = min((row.get("relative_humidity_2m_mean_mean") or 0.0) / 100.0, 1.0)
        drought_risk = min(
            max(((row.get("solar_utilization_ratio_mean") or 0.0) - 0.5) * 2.0, 0.0)
            + max((1.5 - (row.get("precipitation_sum_mean") or 0.0)) / 1.5, 0.0),
            1.0,
        )

        score = (
            rain_risk * 0.24
            + rain_variability * 0.18
            + wind_risk * 0.18
            + cloud_variability * 0.14
            + humidity_risk * 0.10
            + drought_risk * 0.16
        )
        return round(score, 3)

    @staticmethod
    def _dominant_hazard(row: dict) -> str:
        rainfall = (row.get("precipitation_sum_mean") or 0.0) + (row.get("precipitation_sum_interannual_std_mean") or 0.0) / 100.0
        wind = (row.get("wind_power_density_120m_mean") or 0.0) + (row.get("wind_speed_120m_mean_mean") or 0.0) / 10.0
        dryness = max((row.get("solar_utilization_ratio_mean") or 0.0) - 0.5, 0.0) + max((1.5 - (row.get("precipitation_sum_mean") or 0.0)), 0.0)
        hazard_scores = {
            "Heavy Rain / Flooding": rainfall,
            "High Wind Exposure": wind,
            "Dry Spell / Drought Stress": dryness,
        }
        return max(hazard_scores, key=hazard_scores.get)

    @staticmethod
    def _summary(row: dict) -> str:
        tags = []
        if row.get("precipitation_sum_mean") is not None and row["precipitation_sum_mean"] > 2.5:
            tags.append("flood-prone")
        if row.get("wind_power_density_120m_mean") is not None and row["wind_power_density_120m_mean"] > 1.8:
            tags.append("storm-exposed")
        if row.get("solar_utilization_ratio_mean") is not None and row["solar_utilization_ratio_mean"] > 0.55:
            tags.append("dry-spell-sensitive")
        if not tags:
            tags.append("lower-observed-extreme-risk")
        return ", ".join(tags)

    @staticmethod
    def _recommendation(row: dict) -> str:
        hazard = row.get("dominant_hazard", "")
        if hazard == "Heavy Rain / Flooding":
            return "Prioritize drainage, runoff management, and flood-resilient infrastructure."
        if hazard == "High Wind Exposure":
            return "Strengthen wind-resilient design standards and network reliability planning."
        if hazard == "Dry Spell / Drought Stress":
            return "Prioritize water security, reservoir planning, and drought monitoring."
        return "Maintain baseline climate-risk monitoring with region-specific preparedness."

