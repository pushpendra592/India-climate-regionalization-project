"""
Urban-planning interpretations of clustered climate conditions.
"""

import pandas as pd
import numpy as np


class UrbanPlanningInsights:
    """Summarize urban comfort and heat stress by cluster."""

    def generate(self, df: pd.DataFrame, label_col: str = "cluster") -> pd.DataFrame:
        rows = []

        for cluster_id, group in df.groupby(label_col):
            if cluster_id < 0:
                continue

            row = {
                "cluster": int(cluster_id),
                "points": int(len(group)),
                "temperature_2m_mean_mean": self._mean(group, "temperature_2m_mean"),
                "relative_humidity_2m_mean_mean": self._mean(group, "relative_humidity_2m_mean"),
                "wind_speed_10m_mean_mean": self._mean(group, "wind_speed_10m_mean"),
                "cloud_cover_mean_mean": self._mean(group, "cloud_cover_mean"),
                "shortwave_radiation_sum_mean": self._mean(group, "shortwave_radiation_sum"),
                "temperature_2m_mean_interannual_std_mean": self._mean(group, "temperature_2m_mean_interannual_std"),
            }
            row["thermal_stress_index_mean"] = self._thermal_stress(row)
            row["outdoor_comfort_score_mean"] = self._outdoor_comfort(row)
            row["heat_island_potential_mean"] = self._heat_island_potential(row)
            row["urban_comfort_score"] = self._comfort_score(row)
            row["urban_summary"] = self._summary(row)
            row["urban_recommendation"] = self._recommendation(row)
            rows.append(row)

        return pd.DataFrame(rows).sort_values("urban_comfort_score", ascending=False)

    @staticmethod
    def _mean(group: pd.DataFrame, column: str) -> float | None:
        return round(float(group[column].mean()), 3) if column in group.columns else None

    @staticmethod
    def _thermal_stress(row: dict) -> float:
        temp = row.get("temperature_2m_mean_mean") or 25.0
        humidity = row.get("relative_humidity_2m_mean_mean") or 60.0
        return round(max((temp - 24.0) / 4.5, 0.0) + max((humidity - 65.0) / 20.0, 0.0), 3)

    @staticmethod
    def _outdoor_comfort(row: dict) -> float:
        temp = row.get("temperature_2m_mean_mean") or 25.0
        humidity = row.get("relative_humidity_2m_mean_mean") or 60.0
        wind = row.get("wind_speed_10m_mean_mean") or 3.0
        temp_component = 1.0 - min(abs(temp - 24.0) / 12.0, 1.0)
        humidity_component = 1.0 - min(abs(humidity - 58.0) / 35.0, 1.0)
        wind_component = 1.0 - min(abs(wind - 3.0) / 4.0, 1.0)
        return round((temp_component * 0.45) + (humidity_component * 0.35) + (wind_component * 0.20), 3)

    @staticmethod
    def _heat_island_potential(row: dict) -> float:
        temp = row.get("temperature_2m_mean_mean") or 25.0
        solar = row.get("shortwave_radiation_sum_mean") or 18.0
        cloud = row.get("cloud_cover_mean_mean") or 50.0
        wind = row.get("wind_speed_10m_mean_mean") or 3.0
        raw = (
            max((temp - 25.0) / 8.0, 0.0)
            + max((solar - 18.0) / 5.0, 0.0)
            + max((55.0 - cloud) / 40.0, 0.0)
            + max((3.0 - wind) / 3.0, 0.0)
        ) / 4.0
        return round(min(max(raw, 0.0), 1.0), 3)

    @staticmethod
    def _comfort_score(row: dict) -> float:
        score = 0.0

        if row.get("outdoor_comfort_score_mean") is not None:
            score += row["outdoor_comfort_score_mean"] * 4.0
        if row.get("thermal_stress_index_mean") is not None:
            score -= max(row["thermal_stress_index_mean"], 0)
        if row.get("heat_island_potential_mean") is not None:
            score -= row["heat_island_potential_mean"] * 2.0
        if row.get("relative_humidity_2m_mean_mean") is not None and row["relative_humidity_2m_mean_mean"] > 75:
            score -= 0.5

        return round(score, 3)

    @staticmethod
    def _summary(row: dict) -> str:
        tags = []
        if row.get("heat_island_potential_mean") is not None and row["heat_island_potential_mean"] > 0.5:
            tags.append("cooling-infrastructure-priority")
        if row.get("outdoor_comfort_score_mean") is not None and row["outdoor_comfort_score_mean"] > 0.6:
            tags.append("outdoor-friendly")
        if row.get("thermal_stress_index_mean") is not None and row["thermal_stress_index_mean"] > 2:
            tags.append("thermal-discomfort-prone")
        if not tags:
            tags.append("moderate-urban-comfort")
        return ", ".join(tags)

    @staticmethod
    def _recommendation(row: dict) -> str:
        if row.get("heat_island_potential_mean") is not None and row["heat_island_potential_mean"] > 0.5:
            return "Prioritize shade, reflective materials, and urban cooling infrastructure."
        if row.get("outdoor_comfort_score_mean") is not None and row["outdoor_comfort_score_mean"] > 0.65:
            return "Suitable for public-space activation and walkable urban design."
        if row.get("thermal_stress_index_mean") is not None and row["thermal_stress_index_mean"] > 1.2:
            return "Focus on cooling corridors, ventilation, and heat-health planning."
        return "Moderate comfort profile; use mixed passive cooling and open-space strategies."

