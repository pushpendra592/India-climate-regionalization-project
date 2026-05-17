"""
Agriculture-facing interpretations of cluster characteristics.
"""

import pandas as pd
import numpy as np


class AgricultureInsights:
    """Generate agriculture-oriented cluster summaries."""

    def generate(self, df: pd.DataFrame, label_col: str = "cluster") -> pd.DataFrame:
        rows = []

        temp_series = df["temperature_2m_mean"] if "temperature_2m_mean" in df.columns else pd.Series(dtype=float)
        rain_series = df["precipitation_sum"] if "precipitation_sum" in df.columns else pd.Series(dtype=float)
        humidity_series = df["relative_humidity_2m_mean"] if "relative_humidity_2m_mean" in df.columns else pd.Series(dtype=float)
        solar_series = df["shortwave_radiation_sum"] if "shortwave_radiation_sum" in df.columns else pd.Series(dtype=float)

        for cluster_id, group in df.groupby(label_col):
            if cluster_id < 0:
                continue

            row = {
                "cluster": int(cluster_id),
                "points": int(len(group)),
                "temperature_2m_mean_mean": self._mean(group, "temperature_2m_mean"),
                "growing_degree_days_mean": self._mean(group, "growing_degree_days"),
                "precipitation_sum_mean": self._mean(group, "precipitation_sum"),
                "relative_humidity_2m_mean_mean": self._mean(group, "relative_humidity_2m_mean"),
                "shortwave_radiation_sum_mean": self._mean(group, "shortwave_radiation_sum"),
                "frost_risk_mean": self._mean(group, "frost_risk"),
                "heat_stress_mean": self._mean(group, "heat_stress"),
                "temperature_stability_mean": self._inverse_variability(group, "temperature_2m_mean_interannual_std"),
                "rainfall_reliability_mean": self._inverse_variability(group, "precipitation_sum_interannual_std"),
            }
            row["agriculture_suitability_score"] = self._agriculture_score(
                row,
                temp_series,
                rain_series,
                humidity_series,
                solar_series,
            )
            row["agriculture_summary"] = self._summary(row)
            row["agriculture_recommendation"] = self._recommendation(row)
            rows.append(row)

        return pd.DataFrame(rows).sort_values("agriculture_suitability_score", ascending=False)

    @staticmethod
    def _mean(group: pd.DataFrame, column: str) -> float | None:
        return round(float(group[column].mean()), 3) if column in group.columns else None

    @staticmethod
    def _inverse_variability(group: pd.DataFrame, column: str) -> float | None:
        if column not in group.columns:
            return None
        mean_val = float(group[column].mean())
        return round(1.0 / (1.0 + max(mean_val, 0.0)), 3)

    @staticmethod
    def _scaled_rank(value: float | None, series: pd.Series, invert: bool = False) -> float:
        valid = series.dropna()
        if value is None or valid.empty:
            return 0.5
        q10 = float(valid.quantile(0.1))
        q90 = float(valid.quantile(0.9))
        if np.isclose(q90, q10):
            score = 0.5
        else:
            score = (float(value) - q10) / (q90 - q10)
        score = min(max(score, 0.0), 1.0)
        return round(1.0 - score if invert else score, 3)

    @classmethod
    def _agriculture_score(
        cls,
        row: dict,
        temp_series: pd.Series,
        rain_series: pd.Series,
        humidity_series: pd.Series,
        solar_series: pd.Series,
    ) -> float:
        temp = row.get("temperature_2m_mean_mean")
        rain = row.get("precipitation_sum_mean")
        humidity = row.get("relative_humidity_2m_mean_mean")
        solar = row.get("shortwave_radiation_sum_mean")

        temp_score = 1.0 - min(abs((temp or 25.0) - 24.0) / 14.0, 1.0)
        rain_score = cls._scaled_rank(rain, rain_series)
        humidity_score = 1.0 - min(abs((humidity or 60.0) - 60.0) / 35.0, 1.0)
        solar_score = cls._scaled_rank(solar, solar_series)
        stability_score = row.get("temperature_stability_mean", 0.5)
        reliability_score = row.get("rainfall_reliability_mean", 0.5)
        frost_penalty = row.get("frost_risk_mean", 0.0) or 0.0
        heat_penalty = row.get("heat_stress_mean", 0.0) or 0.0

        score = (
            temp_score * 0.22
            + rain_score * 0.22
            + humidity_score * 0.14
            + solar_score * 0.10
            + stability_score * 0.14
            + reliability_score * 0.18
            - frost_penalty * 0.10
            - heat_penalty * 0.10
        )
        return round(score, 3)

    @staticmethod
    def _summary(row: dict) -> str:
        tags = []
        rain = row.get("precipitation_sum_mean")
        humidity = row.get("relative_humidity_2m_mean_mean")

        if row.get("frost_risk_mean") is not None and row["frost_risk_mean"] > 0.2:
            tags.append("frost-exposed")
        if row.get("heat_stress_mean") is not None and row["heat_stress_mean"] > 0.2:
            tags.append("heat-stressed")
        if rain is not None and rain < 1.2:
            tags.append("water-limited")
        if rain is not None and rain > 2.5:
            tags.append("rain-supported")
        if humidity is not None and humidity > 75:
            tags.append("humid-growing-zone")
        if not tags:
            tags.append("balanced-growing-conditions")
        return ", ".join(tags)

    @staticmethod
    def _recommendation(row: dict) -> str:
        if row.get("frost_risk_mean") is not None and row["frost_risk_mean"] > 0.2:
            return "Prefer cold-tolerant crops and short growing windows."
        if row.get("heat_stress_mean") is not None and row["heat_stress_mean"] > 0.2:
            return "Prioritize heat-resilient varieties and irrigation support."
        rain = row.get("precipitation_sum_mean")
        if rain is not None and rain < 1.2:
            return "Suitable for drought-tolerant cropping with water management."
        if rain is not None and rain > 2.5:
            return "Good fit for rain-fed agriculture with drainage planning."
        return "Balanced conditions for diversified cropping and stable seasonal planning."

