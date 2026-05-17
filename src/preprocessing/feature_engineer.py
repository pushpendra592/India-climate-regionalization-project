"""
Feature engineering: derived features, wind extrapolation, indices.
"""

import pandas as pd
import numpy as np
from config.feature_registry import (
    WIND_SHEAR_EXPONENTS,
    WIND_EXTRAPOLATION_HEIGHTS,
)
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("feature_engineer")


class FeatureEngineer:
    """
    Computes derived features from raw/aggregated weather data.

    Categories:
      - Temperature indices
      - Wind extrapolation to turbine heights
      - Energy potential features
      - Agriculture features
      - Disaster risk features
      - Urban comfort features
    """

    def __init__(self, wind_shear_alpha: float = None):
        self.alpha = wind_shear_alpha or WIND_SHEAR_EXPONENTS["default"]

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run all feature engineering steps."""
        with Timer("Feature engineering"):
            logger.info(f"Input: {df.shape}")
            df = df.copy()
            initial_cols = set(df.columns)

            df = self._core_features(df)
            df = self._wind_extrapolation(df)
            df = self._energy_features(df)
            df = self._agriculture_features(df)
            df = self._disaster_features(df)
            df = self._urban_features(df)

            new_features = sorted(set(df.columns) - initial_cols)
            logger.info(f"Output: {df.shape} (+{len(new_features)} new features)")

        return df

    def _core_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "temperature_2m_max" in df.columns and "temperature_2m_min" in df.columns:
            df["temp_range_daily"] = df["temperature_2m_max"] - df["temperature_2m_min"]

        if "temperature_2m_mean" not in df.columns:
            if "temperature_2m_max" in df.columns and "temperature_2m_min" in df.columns:
                df["temperature_2m_mean"] = (
                    df["temperature_2m_max"] + df["temperature_2m_min"]
                ) / 2

        if "apparent_temperature_max" in df.columns and "apparent_temperature_min" in df.columns:
            df["apparent_temp_range"] = (
                df["apparent_temperature_max"] - df["apparent_temperature_min"]
            )

        if "relative_humidity_2m_max" in df.columns and "relative_humidity_2m_min" in df.columns:
            df["humidity_range"] = (
                df["relative_humidity_2m_max"] - df["relative_humidity_2m_min"]
            )

        if "pressure_msl_max" in df.columns and "pressure_msl_min" in df.columns:
            df["pressure_range"] = df["pressure_msl_max"] - df["pressure_msl_min"]

        if "cloud_cover_high_mean" in df.columns and "cloud_cover_low_mean" in df.columns:
            df["cloud_stratification"] = (
                df["cloud_cover_high_mean"] - df["cloud_cover_low_mean"]
            )

        if "low_cloud_hours" in df.columns:
            df["sunshine_fraction"] = df["low_cloud_hours"] / 24.0

        if "precipitation_sum" in df.columns and "precipitation_hours" in df.columns:
            df["precipitation_intensity"] = np.where(
                df["precipitation_hours"] > 0,
                df["precipitation_sum"] / df["precipitation_hours"],
                0,
            )

        logger.info("Core features added")
        return df

    def _wind_extrapolation(self, df: pd.DataFrame) -> pd.DataFrame:
        if "wind_speed_10m_mean" not in df.columns:
            logger.warning("No wind_speed_10m_mean; skipping extrapolation")
            return df

        for height in WIND_EXTRAPOLATION_HEIGHTS:
            df[f"wind_speed_{height}m_mean"] = df["wind_speed_10m_mean"] * (height / 10) ** self.alpha

            if "wind_speed_10m_max" in df.columns:
                df[f"wind_speed_{height}m_max"] = (
                    df["wind_speed_10m_max"] * (height / 10) ** self.alpha
                )

        if "wind_speed_120m_mean" in df.columns:
            df["wind_shear_coefficient"] = np.where(
                (df["wind_speed_10m_mean"] > 0) & (df["wind_speed_120m_mean"] > 0),
                np.log(df["wind_speed_120m_mean"] / df["wind_speed_10m_mean"]) / np.log(120 / 10),
                self.alpha,
            )

        logger.info(f"Wind extrapolation added for heights: {WIND_EXTRAPOLATION_HEIGHTS}")
        return df

    def _energy_features(self, df: pd.DataFrame) -> pd.DataFrame:
        air_density = 1.225

        for height in WIND_EXTRAPOLATION_HEIGHTS:
            ws_col = f"wind_speed_{height}m_mean"
            if ws_col in df.columns:
                ws_ms = df[ws_col] / 3.6
                df[f"wind_power_density_{height}m"] = 0.5 * air_density * ws_ms ** 3

        if "nasa_solar_irradiance_allsky" in df.columns and "nasa_solar_irradiance_clearsky" in df.columns:
            df["solar_utilization_ratio"] = np.where(
                df["nasa_solar_irradiance_clearsky"] > 0,
                df["nasa_solar_irradiance_allsky"] / df["nasa_solar_irradiance_clearsky"],
                0,
            )

        if "shortwave_radiation_sum" in df.columns and "wind_speed_10m_mean" in df.columns:
            solar_norm = (df["shortwave_radiation_sum"] - df["shortwave_radiation_sum"].mean()) / (
                df["shortwave_radiation_sum"].std() + 1e-8
            )
            wind_norm = (df["wind_speed_10m_mean"] - df["wind_speed_10m_mean"].mean()) / (
                df["wind_speed_10m_mean"].std() + 1e-8
            )
            df["solar_wind_complementarity"] = -(solar_norm * wind_norm)

        logger.info("Energy features added")
        return df

    def _agriculture_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "temperature_2m_mean" in df.columns:
            df["growing_degree_days"] = np.maximum(0, df["temperature_2m_mean"] - 10)

        if "temperature_2m_min" in df.columns:
            df["frost_risk"] = (df["temperature_2m_min"] < 0).astype(int)

        if "temperature_2m_max" in df.columns:
            df["heat_stress"] = (df["temperature_2m_max"] > 40).astype(int)

        if "precipitation_sum" in df.columns and "et0_fao_evapotranspiration_sum" in df.columns:
            df["aridity_index"] = np.where(
                df["et0_fao_evapotranspiration_sum"] > 0,
                df["precipitation_sum"] / df["et0_fao_evapotranspiration_sum"],
                np.nan,
            )

        if "nasa_earth_skin_temperature" in df.columns:
            df["soil_temp_proxy"] = df["nasa_earth_skin_temperature"]

            if "temperature_2m_mean" in df.columns:
                df["soil_air_temp_diff"] = (
                    df["nasa_earth_skin_temperature"] - df["temperature_2m_mean"]
                )

        logger.info("Agriculture features added")
        return df

    def _disaster_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "precipitation_sum" in df.columns:
            df["heavy_rain_flag"] = (df["precipitation_sum"] > 50).astype(int)
            df["extreme_rain_flag"] = (df["precipitation_sum"] > 100).astype(int)

        if "wind_gusts_10m_max" in df.columns:
            df["extreme_wind_flag"] = (df["wind_gusts_10m_max"] > 60).astype(int)
            df["storm_wind_flag"] = (df["wind_gusts_10m_max"] > 90).astype(int)

        if "pressure_msl_std" in df.columns:
            df["pressure_instability"] = (df["pressure_msl_std"] > 5).astype(int)

        if "heavy_rain_flag" in df.columns and "precipitation_hours" in df.columns:
            df["flood_risk_indicator"] = df["heavy_rain_flag"] * df["precipitation_hours"]

        logger.info("Disaster features added")
        return df

    def _urban_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "apparent_temperature_mean" in df.columns and "temperature_2m_mean" in df.columns:
            df["thermal_stress_index"] = (
                df["apparent_temperature_mean"] - df["temperature_2m_mean"]
            )

        if all(c in df.columns for c in ["comfortable_hours", "dry_hours", "calm_hours"]):
            df["outdoor_comfort_score"] = (
                df["comfortable_hours"] + df["dry_hours"] + df["calm_hours"]
            ) / 72

        if all(c in df.columns for c in ["hot_hours", "calm_hours", "low_cloud_hours"]):
            df["heat_island_potential"] = (
                df["hot_hours"] + df["calm_hours"] + df["low_cloud_hours"]
            ) / 72

        logger.info("Urban features added")
        return df
