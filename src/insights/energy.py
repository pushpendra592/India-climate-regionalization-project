"""
Energy-focused interpretations of clustered climate patterns.
"""

import pandas as pd
import numpy as np


class EnergyInsights:
    """Summarize renewable-energy potential by cluster."""

    def generate(self, df: pd.DataFrame, label_col: str = "cluster") -> pd.DataFrame:
        rows = []

        solar_series = df["shortwave_radiation_sum"] if "shortwave_radiation_sum" in df.columns else pd.Series(dtype=float)
        wind_series = df["wind_power_density_120m"] if "wind_power_density_120m" in df.columns else pd.Series(dtype=float)
        consistency_series = df["solar_utilization_ratio"] if "solar_utilization_ratio" in df.columns else pd.Series(dtype=float)

        for cluster_id, group in df.groupby(label_col):
            if cluster_id < 0:
                continue

            row = {
                "cluster": int(cluster_id),
                "points": int(len(group)),
                "shortwave_radiation_sum_mean": self._mean(group, "shortwave_radiation_sum"),
                "wind_speed_120m_mean_mean": self._mean(group, "wind_speed_120m_mean"),
                "wind_power_density_120m_mean": self._mean(group, "wind_power_density_120m"),
                "solar_utilization_ratio_mean": self._mean(group, "solar_utilization_ratio"),
                "solar_wind_complementarity_mean": self._mean(group, "solar_wind_complementarity"),
                "cloud_cover_mean_mean": self._mean(group, "cloud_cover_mean"),
            }
            row["energy_potential_score"] = self._energy_score(
                row,
                solar_series,
                wind_series,
                consistency_series,
            )
            row["resource_mix"] = self._resource_mix(row)
            row["energy_summary"] = self._summary(row)
            row["energy_recommendation"] = self._recommendation(row)
            rows.append(row)

        return pd.DataFrame(rows).sort_values("energy_potential_score", ascending=False)

    @staticmethod
    def _mean(group: pd.DataFrame, column: str) -> float | None:
        return round(float(group[column].mean()), 3) if column in group.columns else None

    @staticmethod
    def _scaled_rank(value: float | None, series: pd.Series) -> float:
        valid = series.dropna()
        if value is None or valid.empty:
            return 0.5
        q10 = float(valid.quantile(0.1))
        q90 = float(valid.quantile(0.9))
        if np.isclose(q90, q10):
            score = 0.5
        else:
            score = (float(value) - q10) / (q90 - q10)
        return round(min(max(score, 0.0), 1.0), 3)

    @classmethod
    def _energy_score(
        cls,
        row: dict,
        solar_series: pd.Series,
        wind_series: pd.Series,
        consistency_series: pd.Series,
    ) -> float:
        solar_score = cls._scaled_rank(row.get("shortwave_radiation_sum_mean"), solar_series)
        wind_score = cls._scaled_rank(row.get("wind_power_density_120m_mean"), wind_series)
        consistency_score = cls._scaled_rank(row.get("solar_utilization_ratio_mean"), consistency_series)
        complementarity = row.get("solar_wind_complementarity_mean") or 0.0
        complementarity_score = min(max((complementarity + 1.0) / 2.0, 0.0), 1.0)

        score = (
            solar_score * 0.30
            + wind_score * 0.35
            + consistency_score * 0.20
            + complementarity_score * 0.15
        )
        return round(score, 3)

    @staticmethod
    def _resource_mix(row: dict) -> str:
        solar = row.get("shortwave_radiation_sum_mean") or 0.0
        wind = row.get("wind_power_density_120m_mean") or 0.0
        if solar >= 19 and wind >= 1.8:
            return "Hybrid Solar-Wind"
        if solar >= 18.5:
            return "Solar-Led"
        if wind >= 1.8:
            return "Wind-Led"
        return "Balanced Renewable"

    @staticmethod
    def _summary(row: dict) -> str:
        tags = []
        if row.get("shortwave_radiation_sum_mean") is not None and row["shortwave_radiation_sum_mean"] > 19:
            tags.append("solar-favored")
        if row.get("wind_power_density_120m_mean") is not None and row["wind_power_density_120m_mean"] > 1.8:
            tags.append("wind-favored")
        if row.get("solar_wind_complementarity_mean") is not None and row["solar_wind_complementarity_mean"] > -0.2:
            tags.append("hybrid-friendly")
        if not tags:
            tags.append("moderate-renewable-potential")
        return ", ".join(tags)

    @staticmethod
    def _recommendation(row: dict) -> str:
        mix = row.get("resource_mix", "Balanced Renewable")
        if mix == "Hybrid Solar-Wind":
            return "Strong candidate for hybrid renewable parks with storage integration."
        if mix == "Solar-Led":
            return "Best suited for utility-scale solar with cloud-aware generation planning."
        if mix == "Wind-Led":
            return "Best suited for elevated wind development and transmission planning."
        return "Moderate multi-source renewable potential with balanced deployment options."

