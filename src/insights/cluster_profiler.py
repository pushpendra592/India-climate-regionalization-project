"""
Profile and describe what each cluster represents.
"""

import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("profiler")


class ClusterProfiler:
    """
    Creates human-readable profiles for each cluster.

    Answers: "What makes Cluster 3 different from Cluster 5?"

    Usage:
        profiler = ClusterProfiler()
        profiles = profiler.profile(df_with_labels, feature_cols)
        profiler.describe_cluster(profiles, cluster_id=3)
    """

    # Climate classification thresholds (India-specific)
    CLIMATE_LABELS = {
        "temperature_2m_mean": [
            (float("-inf"), 10, "Cold"),
            (10, 20, "Cool"),
            (20, 28, "Moderate"),
            (28, 35, "Warm"),
            (35, float("inf"), "Hot"),
        ],
        "precipitation_sum": [
            (float("-inf"), 2, "Arid"),
            (2, 5, "Semi-Arid"),
            (5, 10, "Moderate"),
            (10, 20, "Wet"),
            (20, float("inf"), "Very Wet"),
        ],
        "relative_humidity_2m_mean": [
            (float("-inf"), 30, "Dry"),
            (30, 50, "Comfortable"),
            (50, 70, "Moderate"),
            (70, 85, "Humid"),
            (85, float("inf"), "Very Humid"),
        ],
    }

    FEATURE_ALIASES = {
        "temperature": ["temperature_2m_mean", "nasa_temperature_2m"],
        "precipitation": ["precipitation_sum", "nasa_precipitation"],
        "humidity": ["relative_humidity_2m_mean", "nasa_relative_humidity"],
        "wind": ["wind_speed_80m_mean", "wind_speed_10m_mean", "nasa_wind_speed_10m"],
        "solar": [
            "shortwave_radiation_sum",
            "nasa_solar_irradiance_allsky",
            "solar_utilization_ratio",
        ],
    }

    def _first_available(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _classify_threshold(self, value: float, thresholds: list[tuple[float, float, str]]) -> str | None:
        if pd.isna(value):
            return None
        for lower, upper, label in thresholds:
            if lower <= value < upper:
                return label
        return None

    def _classify_quantile(
        self,
        cluster_value: float,
        series: pd.Series,
        labels: tuple[str, str, str],
    ) -> str | None:
        valid = series.dropna()
        if valid.empty or pd.isna(cluster_value):
            return None
        q1 = valid.quantile(0.33)
        q2 = valid.quantile(0.66)
        if cluster_value <= q1:
            return labels[0]
        if cluster_value <= q2:
            return labels[1]
        return labels[2]

    def _derive_moisture_label(self, cluster_means: dict, all_data: pd.DataFrame) -> str | None:
        precip_col = self._first_available(all_data, self.FEATURE_ALIASES["precipitation"])
        humidity_col = self._first_available(all_data, self.FEATURE_ALIASES["humidity"])

        precip_value = cluster_means.get(precip_col) if precip_col else None
        humidity_value = cluster_means.get(humidity_col) if humidity_col else None

        precip_label = None
        humidity_label = None
        if precip_col:
            precip_label = self._classify_threshold(
                precip_value,
                self.CLIMATE_LABELS["precipitation_sum"],
            )
        if humidity_col:
            humidity_label = self._classify_threshold(
                humidity_value,
                self.CLIMATE_LABELS["relative_humidity_2m_mean"],
            )

        if precip_label in {"Arid", "Semi-Arid"} or humidity_label == "Dry":
            return "Dry"
        if precip_label in {"Wet", "Very Wet"} or humidity_label in {"Humid", "Very Humid"}:
            return "Humid"
        if humidity_label == "Comfortable":
            return "Balanced"
        if precip_label == "Moderate" or humidity_label == "Moderate":
            return "Moderate"
        return humidity_label or precip_label

    def _climate_label_for_cluster(
        self,
        df: pd.DataFrame,
        cluster_id: int,
        label_col: str = "cluster",
    ) -> str:
        cluster_data = df[df[label_col] == cluster_id]
        if cluster_data.empty:
            return f"Cluster {cluster_id}"

        cluster_means = cluster_data.mean(numeric_only=True).to_dict()
        parts = []

        temp_col = self._first_available(df, self.FEATURE_ALIASES["temperature"])
        if temp_col:
            temp_label = self._classify_threshold(
                cluster_means.get(temp_col),
                self.CLIMATE_LABELS["temperature_2m_mean"],
            )
            if temp_label:
                parts.append(temp_label)

        moisture_label = self._derive_moisture_label(cluster_means, df)
        if moisture_label:
            parts.append(moisture_label)

        wind_col = self._first_available(df, self.FEATURE_ALIASES["wind"])
        if wind_col:
            wind_label = self._classify_quantile(
                cluster_means.get(wind_col),
                df[wind_col],
                ("Calm", "Breezy", "Windy"),
            )
            if wind_label:
                parts.append(wind_label)

        solar_col = self._first_available(df, self.FEATURE_ALIASES["solar"])
        if solar_col:
            solar_label = self._classify_quantile(
                cluster_means.get(solar_col),
                df[solar_col],
                ("Low Solar", "Sunny", "High Solar"),
            )
            if solar_label and solar_label not in parts:
                parts.append(solar_label)

        if not parts:
            return f"Cluster {cluster_id}"

        return " ".join(parts[:4])

    def _regional_label_for_cluster(
        self,
        df: pd.DataFrame,
        cluster_id: int,
        label_col: str = "cluster",
    ) -> str:
        cluster_data = df[df[label_col] == cluster_id]
        if cluster_data.empty:
            return f"Cluster {cluster_id}"

        climate_label = self._climate_label_for_cluster(df, cluster_id, label_col)
        lat = float(cluster_data["latitude"].mean()) if "latitude" in cluster_data.columns else np.nan
        lon = float(cluster_data["longitude"].mean()) if "longitude" in cluster_data.columns else np.nan

        if not pd.isna(lat) and not pd.isna(lon):
            if lat >= 33.3:
                return "Upper Himalayan Cold Pocket"
            if lat >= 31.5:
                return "Western Himalayan Highlands"
            if lat >= 29.0 and lon <= 79.5:
                return "Northwest Highland Transition"
            if lon >= 88.0 and lat >= 23.0:
                return "Northeast Humid Belt"
            if lon <= 74.5 and lat >= 20.0:
                return "Northwest Dry Plains"
            if 76.0 <= lon <= 88.5 and lat >= 24.0:
                return "Gangetic Alluvial Plains"
            if 81.5 <= lon and 18.0 <= lat < 24.5:
                return "East-Central Monsoon Corridor"
            if 73.0 <= lon < 81.5 and 18.0 <= lat < 24.5:
                return "Central Inland Plateau"
            if lat < 18.5 and lon >= 76.0:
                return "Southern Peninsular Belt"
            if lat < 19.5 and lon < 76.0:
                return "Western Coastal South"
            if lon >= 82.0 and lat < 24.0:
                return "Eastern Coastal Transition"

        return climate_label

    def _friendly_feature_name(self, feature: str) -> str:
        aliases = {
            "temperature_2m_mean": "average temperature",
            "temperature_2m_max": "daytime temperature",
            "temperature_2m_min": "night temperature",
            "temperature_2m_mean_interannual_std": "year-to-year temperature variability",
            "precipitation_sum": "rainfall",
            "precipitation_sum_interannual_std": "year-to-year rainfall variability",
            "relative_humidity_2m_mean": "humidity",
            "relative_humidity_2m_max": "peak humidity",
            "relative_humidity_2m_min": "minimum humidity",
            "wind_speed_10m_mean": "surface wind speed",
            "wind_speed_80m_mean": "elevated wind speed",
            "wind_speed_10m_mean_interannual_std": "year-to-year wind variability",
            "wind_shear_coefficient": "wind shear",
            "shortwave_radiation_sum": "solar radiation",
            "solar_utilization_ratio": "solar consistency",
            "solar_wind_complementarity": "solar and wind complementarity",
            "wind_power_density_80m": "wind energy potential",
            "wind_power_density_120m": "mid-height wind energy potential",
            "wind_power_density_180m": "high-altitude wind energy potential",
            "cloud_cover_mean_interannual_std": "year-to-year cloud variability",
            "nasa_solar_irradiance_allsky": "all-sky solar potential",
            "nasa_solar_irradiance_clearsky": "clear-sky solar potential",
            "nasa_uv_index": "UV intensity",
            "nasa_relative_humidity": "humidity",
            "nasa_temperature_2m": "average temperature",
            "nasa_precipitation": "rainfall",
        }
        return aliases.get(feature, feature.replace("_", " "))

    def explain_characteristic(self, item: dict) -> str:
        feature_name = self._friendly_feature_name(item["feature"])
        is_very = item["description"].startswith("very ")
        is_high = "HIGH" in item["description"]
        comparative = "higher" if is_high else "lower"
        emphasis = "much " if is_very else ""

        if item["feature"] == "wind_shear_coefficient":
            return f"{emphasis}stronger vertical wind change than the India sample average"
        if item["feature"] == "solar_utilization_ratio":
            return f"{emphasis}more reliable solar availability than average"
        if item["feature"] == "solar_wind_complementarity":
            if "LOW" in item["description"]:
                return f"{emphasis}weaker solar-wind complementarity than average"
            return f"{emphasis}stronger solar-wind complementarity than average"
        if item["feature"] in {
            "wind_power_density_80m",
            "wind_power_density_120m",
            "wind_power_density_180m",
        }:
            return f"{emphasis}{comparative} wind energy potential than average"

        return f"{emphasis}{comparative} {feature_name} than the India sample average"

    def summarize_cluster_label(self, label: str) -> str:
        return f"This location fits a {label.lower()} climate pattern."

    def profile(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        label_col: str = "cluster",
    ) -> pd.DataFrame:
        """
        Create statistical profile for each cluster.

        Returns:
            DataFrame with mean, std, min, max for each feature per cluster
        """
        profiles = (
            df.groupby(label_col)[feature_cols]
            .agg(["mean", "std", "min", "max", "count"])
        )

        logger.info(f"📊 Profiled {profiles.index.nunique()} clusters × {len(feature_cols)} features")

        return profiles

    def profile_summary(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        label_col: str = "cluster",
    ) -> pd.DataFrame:
        """
        Create a simple mean-based profile (one row per cluster).
        """
        summary = df.groupby(label_col)[feature_cols].mean()
        summary["cluster_size"] = df.groupby(label_col).size()
        summary["cluster_pct"] = (
            summary["cluster_size"] / len(df) * 100
        ).round(1)

        return summary

    def describe_cluster(
        self,
        df: pd.DataFrame,
        cluster_id: int,
        feature_cols: list,
        label_col: str = "cluster",
    ) -> dict:
        """
        Generate human-readable description of a single cluster.
        """
        if df.columns.duplicated().any():
            logger.warning("Duplicate columns detected in cluster profile input; keeping first occurrence.")
            df = df.loc[:, ~df.columns.duplicated()].copy()

        cluster_data = df[df[label_col] == cluster_id]
        all_data = df

        description = {
            "cluster_id": cluster_id,
            "size": len(cluster_data),
            "pct": round(len(cluster_data) / len(all_data) * 100, 1),
            "characteristics": [],
        }

        for col in feature_cols:
            if col not in cluster_data.columns:
                continue

            cluster_mean = cluster_data[col].mean()
            global_mean = all_data[col].mean()
            global_std = all_data[col].std()

            if global_std == 0:
                continue

            # How many std deviations from global mean
            z_score = (cluster_mean - global_mean) / global_std

            if abs(z_score) > 0.5:
                direction = "HIGH" if z_score > 0 else "LOW"
                strength = "very " if abs(z_score) > 1.5 else ""

                description["characteristics"].append({
                    "feature": col,
                    "cluster_mean": round(cluster_mean, 2),
                    "global_mean": round(global_mean, 2),
                    "z_score": round(z_score, 2),
                    "description": f"{strength}{direction}",
                    "summary": self.explain_characteristic(
                        {
                            "feature": col,
                            "description": f"{strength}{direction}",
                        }
                    ),
                })

        # Sort by absolute z-score (most distinctive features first)
        description["characteristics"].sort(
            key=lambda x: abs(x["z_score"]), reverse=True
        )

        return description

    def auto_label_clusters(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        label_col: str = "cluster",
    ) -> dict:
        """
        Automatically generate descriptive labels for each cluster.

        Example: "Hot-Humid-Coastal" or "Cold-Dry-Highland"
        """
        labels = {}

        for cluster_id in df[label_col].unique():
            if cluster_id < 0:
                labels[cluster_id] = "Noise/Outlier"
                continue

            labels[cluster_id] = self._regional_label_for_cluster(df, int(cluster_id), label_col)

        logger.info(f"🏷️  Auto-labels: {labels}")
        return labels

    def domain_profile(
        self,
        df: pd.DataFrame,
        label_col: str = "cluster",
        domain: str = "energy",
    ) -> pd.DataFrame:
        """
        Profile clusters for a specific domain.
        """
        from config.feature_registry import get_domain_features

        domain_cols = [
            c for c in df.columns
            if any(c.startswith(f) for f in get_domain_features(domain))
        ]

        if not domain_cols:
            logger.warning(f"⚠️  No {domain} features found in data")
            return pd.DataFrame()

        return self.profile_summary(df, domain_cols, label_col)

    def get_nearest_examples(
        self,
        df: pd.DataFrame,
        latitude: float,
        longitude: float,
        cluster_id: int,
        label_col: str = "cluster",
        limit: int = 3,
    ) -> list[dict]:
        cluster_df = df[df[label_col] == cluster_id].copy()
        if cluster_df.empty or "latitude" not in cluster_df.columns or "longitude" not in cluster_df.columns:
            return []

        cluster_df["distance"] = np.sqrt(
            (cluster_df["latitude"] - latitude) ** 2 + (cluster_df["longitude"] - longitude) ** 2
        )
        nearest = cluster_df.nsmallest(limit, "distance")
        return [
            {
                "latitude": round(row["latitude"], 4),
                "longitude": round(row["longitude"], 4),
                "distance_deg": round(row["distance"], 4),
            }
            for _, row in nearest.iterrows()
        ]
