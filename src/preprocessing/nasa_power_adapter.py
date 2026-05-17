"""
Normalize NASA POWER daily data into the project's generic weather schema.
"""

import pandas as pd
from config.feature_registry import NASA_COLUMN_RENAME


class NASAPowerAdapter:
    """Convert raw NASA POWER output into a daily weather table used downstream."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy().rename(columns=NASA_COLUMN_RENAME)

        if "date" in out.columns:
            out["date"] = pd.to_datetime(out["date"])

        alias_pairs = {
            "temperature_2m_mean": "nasa_temperature_2m",
            "dewpoint_2m_mean": "nasa_dewpoint_2m",
            "relative_humidity_2m_mean": "nasa_relative_humidity",
            "precipitation_sum": "nasa_precipitation",
            "wind_speed_10m_mean": "nasa_wind_speed_10m",
            "wind_direction_10m_mean": "nasa_wind_direction_10m",
            "surface_pressure_mean": "nasa_surface_pressure",
            "pressure_msl_mean": "nasa_surface_pressure",
            "cloud_cover_mean": "nasa_cloud_amount",
            "shortwave_radiation_sum": "nasa_solar_irradiance_allsky",
        }

        for alias, source in alias_pairs.items():
            if source in out.columns and alias not in out.columns:
                out[alias] = out[source]

        if "temperature_2m_mean" in out.columns:
            out["temperature_2m_max"] = out["temperature_2m_mean"]
            out["temperature_2m_min"] = out["temperature_2m_mean"]

        if "relative_humidity_2m_mean" in out.columns:
            out["relative_humidity_2m_max"] = out["relative_humidity_2m_mean"]
            out["relative_humidity_2m_min"] = out["relative_humidity_2m_mean"]

        if "wind_speed_10m_mean" in out.columns:
            out["wind_speed_10m_max"] = out["wind_speed_10m_mean"]

        if "cloud_cover_mean" in out.columns:
            out["cloud_cover_low_mean"] = out["cloud_cover_mean"]
            out["cloud_cover_mid_mean"] = out["cloud_cover_mean"]
            out["cloud_cover_high_mean"] = out["cloud_cover_mean"]

        return out
