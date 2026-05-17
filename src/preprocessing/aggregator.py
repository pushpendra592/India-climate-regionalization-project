"""
Temporal aggregation: Daily to Monthly, Seasonal, and Yearly.
"""

import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("aggregator")


class TemporalAggregator:
    """Aggregate daily weather features into multiple temporal resolutions."""

    SEASONS = {
        "Winter": [12, 1, 2],
        "Pre-Monsoon": [3, 4, 5],
        "Monsoon": [6, 7, 8, 9],
        "Post-Monsoon": [10, 11],
    }

    SUM_COLS = [
        "precipitation_sum",
        "rain_sum",
        "showers_sum",
        "snowfall_sum",
        "shortwave_radiation_sum",
        "et0_fao_evapotranspiration_sum",
        "frost_hours",
        "hot_hours",
        "comfortable_hours",
        "precipitation_hours",
        "dry_hours",
        "calm_hours",
        "strong_wind_hours",
        "high_humidity_hours",
        "low_cloud_hours",
        "overcast_hours",
    ]

    MAX_COLS = [
        "temperature_2m_max",
        "apparent_temperature_max",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "precipitation_max",
        "shortwave_radiation_max",
        "vapour_pressure_deficit_max",
    ]

    MIN_COLS = [
        "temperature_2m_min",
        "apparent_temperature_min",
        "dewpoint_2m_min",
        "relative_humidity_2m_min",
        "pressure_msl_min",
    ]

    EXCLUDED_AGG_COLS = {
        "latitude",
        "longitude",
        "year",
        "month",
        "season_year",
    }

    SEASONAL_FEATURE_COLS = [
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "relative_humidity_2m_mean",
        "wind_speed_10m_mean",
        "cloud_cover_mean",
        "shortwave_radiation_sum",
    ]

    def _get_agg_rules(self, df: pd.DataFrame) -> dict:
        rules = {}

        for col in df.select_dtypes(include=[np.number]).columns:
            if col in self.EXCLUDED_AGG_COLS:
                continue

            if col in self.SUM_COLS:
                rules[col] = "sum"
            elif col in self.MAX_COLS:
                rules[col] = "max"
            elif col in self.MIN_COLS:
                rules[col] = "min"
            elif "mode" in col:
                rules[col] = lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else np.nan
            else:
                rules[col] = "mean"

        return rules

    def to_monthly(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        with Timer("Daily to Monthly aggregation"):
            df = daily_df
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["date"] = pd.to_datetime(df["date"])
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month

            rules = self._get_agg_rules(df)
            rules_with_count = {**rules, "date": "count"}

            monthly = (
                df.groupby(["latitude", "longitude", "year", "month"])
                .agg(rules_with_count)
                .rename(columns={"date": "days_count"})
                .reset_index()
            )

            logger.info(
                f"Monthly aggregation complete: {len(monthly)} rows across "
                f"{monthly[['latitude', 'longitude']].drop_duplicates().shape[0]} points"
            )
            return monthly

    def to_seasonal(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        with Timer("Daily to Seasonal aggregation"):
            df = daily_df
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["date"] = pd.to_datetime(df["date"])
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month

            month_to_season = {}
            for season, months in self.SEASONS.items():
                for month in months:
                    month_to_season[month] = season

            df["season"] = df["month"].map(month_to_season)
            df["season_year"] = df["year"]
            df.loc[df["month"] == 12, "season_year"] = df["year"] + 1

            rules = self._get_agg_rules(df)
            rules_with_count = {**rules, "date": "count"}

            seasonal = (
                df.groupby(["latitude", "longitude", "season_year", "season"])
                .agg(rules_with_count)
                .rename(columns={"date": "days_count"})
                .reset_index()
            )

            logger.info(
                f"Seasonal aggregation complete: {len(seasonal)} rows across "
                f"{seasonal[['latitude', 'longitude']].drop_duplicates().shape[0]} points"
            )
            return seasonal

    def to_yearly(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        with Timer("Daily to Yearly aggregation"):
            df = daily_df
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["date"] = pd.to_datetime(df["date"])
            df["year"] = df["date"].dt.year

            rules = self._get_agg_rules(df)
            rules_with_count = {**rules, "date": "count"}

            yearly = (
                df.groupby(["latitude", "longitude", "year"])
                .agg(rules_with_count)
                .rename(columns={"date": "days_count"})
                .reset_index()
            )

            logger.info(
                f"Yearly aggregation complete: {len(yearly)} rows across "
                f"{yearly[['latitude', 'longitude']].drop_duplicates().shape[0]} points"
            )
            return yearly

    def to_climate_normals(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        with Timer("Computing climate normals"):
            df = daily_df
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["date"] = pd.to_datetime(df["date"])

            rules = self._get_agg_rules(df)
            normal_rules = {col: "mean" for col in rules}

            normals = (
                df.groupby(["latitude", "longitude"])
                .agg(normal_rules)
                .reset_index()
            )

            yearly = self.to_yearly(df)
            variability_cols = [
                "temperature_2m_mean",
                "precipitation_sum",
                "wind_speed_10m_mean",
                "cloud_cover_mean",
            ]

            for col in variability_cols:
                if col in yearly.columns:
                    yearly_std = (
                        yearly.groupby(["latitude", "longitude"])[col]
                        .std()
                        .reset_index()
                        .rename(columns={col: f"{col}_interannual_std"})
                    )
                    normals = normals.merge(yearly_std, on=["latitude", "longitude"], how="left")

            seasonal = self.to_seasonal(df)
            normals = self._add_seasonal_signatures(normals, seasonal)

            monthly = self.to_monthly(df)
            normals = self._add_monthly_seasonality(normals, monthly)

            logger.info(
                f"Climate normals ready: {len(normals)} points x {len(normals.columns)} columns"
            )
            return normals

    def _add_seasonal_signatures(self, normals: pd.DataFrame, seasonal: pd.DataFrame) -> pd.DataFrame:
        seasonal_means = (
            seasonal.groupby(["latitude", "longitude", "season"])
            .mean(numeric_only=True)
            .reset_index()
        )

        for col in self.SEASONAL_FEATURE_COLS:
            if col not in seasonal_means.columns:
                continue

            pivot = (
                seasonal_means.pivot_table(
                    index=["latitude", "longitude"],
                    columns="season",
                    values=col,
                )
                .rename(
                    columns=lambda season: f"{col}_{str(season).lower().replace('-', '_').replace(' ', '_')}"
                )
                .reset_index()
            )
            normals = normals.merge(pivot, on=["latitude", "longitude"], how="left")

        metric_cols = set(normals.columns)

        if {
            "precipitation_sum_monsoon",
            "precipitation_sum",
        }.issubset(metric_cols):
            normals["monsoon_rainfall_share"] = np.where(
                normals["precipitation_sum"] > 0,
                normals["precipitation_sum_monsoon"] / normals["precipitation_sum"],
                0,
            )

        if {
            "temperature_2m_mean_pre_monsoon",
            "temperature_2m_mean_winter",
        }.issubset(metric_cols):
            normals["pre_monsoon_heat_contrast"] = (
                normals["temperature_2m_mean_pre_monsoon"] - normals["temperature_2m_mean_winter"]
            )

        if {
            "relative_humidity_2m_mean_monsoon",
            "relative_humidity_2m_mean_pre_monsoon",
        }.issubset(metric_cols):
            normals["seasonal_humidity_contrast"] = (
                normals["relative_humidity_2m_mean_monsoon"]
                - normals["relative_humidity_2m_mean_pre_monsoon"]
            )

        if {
            "wind_speed_10m_mean_monsoon",
            "wind_speed_10m_mean_winter",
        }.issubset(metric_cols):
            normals["seasonal_wind_contrast"] = (
                normals["wind_speed_10m_mean_monsoon"] - normals["wind_speed_10m_mean_winter"]
            )

        if {
            "cloud_cover_mean_monsoon",
            "cloud_cover_mean_winter",
        }.issubset(metric_cols):
            normals["seasonal_cloud_contrast"] = (
                normals["cloud_cover_mean_monsoon"] - normals["cloud_cover_mean_winter"]
            )

        if {
            "shortwave_radiation_sum_winter",
            "shortwave_radiation_sum_monsoon",
        }.issubset(metric_cols):
            normals["winter_to_monsoon_solar_ratio"] = np.where(
                normals["shortwave_radiation_sum_monsoon"] > 0,
                normals["shortwave_radiation_sum_winter"] / normals["shortwave_radiation_sum_monsoon"],
                0,
            )

        return normals

    def _add_monthly_seasonality(self, normals: pd.DataFrame, monthly: pd.DataFrame) -> pd.DataFrame:
        monthly_means = (
            monthly.groupby(["latitude", "longitude", "month"])
            .mean(numeric_only=True)
            .reset_index()
        )

        if "precipitation_sum" in monthly_means.columns:
            precip_pivot = (
                monthly_means.pivot_table(
                    index=["latitude", "longitude"],
                    columns="month",
                    values="precipitation_sum",
                )
                .reset_index()
            )

            month_cols = [col for col in precip_pivot.columns if isinstance(col, (int, np.integer))]
            monthly_precip = precip_pivot[month_cols]
            annual_monthly_mean = monthly_precip.mean(axis=1).replace(0, np.nan)
            rainy_peak = monthly_precip.max(axis=1)

            precip_pivot["rainfall_seasonality_index"] = (
                monthly_precip.std(axis=1) / annual_monthly_mean
            ).fillna(0)
            precip_pivot["peak_month_rainfall_share"] = (
                rainy_peak / monthly_precip.sum(axis=1).replace(0, np.nan)
            ).fillna(0)
            precip_pivot["wettest_month"] = monthly_precip.idxmax(axis=1).astype(float)

            normals = normals.merge(
                precip_pivot[
                    [
                        "latitude",
                        "longitude",
                        "rainfall_seasonality_index",
                        "peak_month_rainfall_share",
                        "wettest_month",
                    ]
                ],
                on=["latitude", "longitude"],
                how="left",
            )

        if "temperature_2m_mean" in monthly_means.columns:
            temp_seasonality = (
                monthly_means.groupby(["latitude", "longitude"])["temperature_2m_mean"]
                .agg(["max", "min", "std"])
                .reset_index()
                .rename(
                    columns={
                        "max": "monthly_temp_peak",
                        "min": "monthly_temp_trough",
                        "std": "monthly_temp_variability",
                    }
                )
            )
            temp_seasonality["annual_temp_cycle_range"] = (
                temp_seasonality["monthly_temp_peak"] - temp_seasonality["monthly_temp_trough"]
            )
            normals = normals.merge(temp_seasonality, on=["latitude", "longitude"], how="left")

        return normals
