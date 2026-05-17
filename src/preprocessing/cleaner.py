"""
Data cleaning: handle missing values, outliers, and invalid data.
"""

import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("cleaner")


class DataCleaner:
    """
    Cleans merged weather data.

    Steps:
      1. Remove columns with too many nulls
      2. Handle remaining nulls (interpolation / fill)
      3. Detect and cap outliers
      4. Remove duplicate rows
      5. Validate physical ranges

    Usage:
        cleaner = DataCleaner()
        clean_df = cleaner.clean(merged_df)
    """

    # Physical limits for sanity checking
    PHYSICAL_RANGES = {
        "temperature_2m_mean":          (-50, 55),
        "temperature_2m_max":           (-50, 60),
        "temperature_2m_min":           (-60, 50),
        "apparent_temperature_mean":    (-60, 65),
        "dewpoint_2m_mean":             (-60, 35),
        "relative_humidity_2m_mean":    (0, 100),
        "relative_humidity_2m_max":     (0, 100),
        "relative_humidity_2m_min":     (0, 100),
        "precipitation_sum":            (0, 500),
        "pressure_msl_mean":            (870, 1084),
        "cloud_cover_mean":             (0, 100),
        "wind_speed_10m_mean":          (0, 150),
        "wind_speed_10m_max":           (0, 250),
        "shortwave_radiation_sum":      (0, 50000),
        "nasa_solar_irradiance_allsky": (0, 12),
        "nasa_temperature_2m":          (-50, 55),
        "nasa_relative_humidity":       (0, 100),
    }

    def __init__(
        self,
        null_threshold: float = 0.5,
        outlier_method: str = "iqr",
        outlier_factor: float = 3.0,
    ):
        """
        Args:
            null_threshold: Drop columns with more than this fraction of nulls
            outlier_method: "iqr" or "zscore" or "physical"
            outlier_factor: IQR multiplier or Z-score threshold
        """
        self.null_threshold = null_threshold
        self.outlier_method = outlier_method
        self.outlier_factor = outlier_factor

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run full cleaning pipeline."""
        with Timer("Data cleaning"):
            logger.info(f"📊 Input shape: {df.shape}")

            df = self._remove_duplicates(df)
            df = self._drop_high_null_columns(df)
            df = self._handle_missing_values(df)
            df = self._handle_outliers(df)
            df = self._validate_physical_ranges(df)

            logger.info(f"✅ Cleaned shape: {df.shape}")

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows."""
        before = len(df)
        df = df.drop_duplicates(subset=["latitude", "longitude", "date"])
        removed = before - len(df)
        if removed > 0:
            logger.info(f"🗑️  Removed {removed} duplicate rows")
        return df

    def _drop_high_null_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop columns that are mostly null."""
        null_pct = df.isnull().mean()
        high_null_cols = null_pct[null_pct > self.null_threshold].index.tolist()

        # Never drop essential columns
        protected = ["date", "latitude", "longitude"]
        high_null_cols = [c for c in high_null_cols if c not in protected]

        if high_null_cols:
            logger.info(
                f"🗑️  Dropping {len(high_null_cols)} high-null columns "
                f"(>{self.null_threshold*100:.0f}% null): {high_null_cols}"
            )
            df = df.drop(columns=high_null_cols)

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill remaining missing values using smart strategies."""
        df = df.copy()
        total_nulls_before = df.isnull().sum().sum()

        # Strategy 1: For each point, interpolate time-series gaps
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric = [c for c in df.columns if c not in numeric_cols]

        # Group by location and interpolate within each point's time series
        filled_dfs = []
        for (lat, lon), group in df.groupby(["latitude", "longitude"]):
            group = group.sort_values("date")

            # Linear interpolation for small gaps (< 7 days)
            group[numeric_cols] = group[numeric_cols].interpolate(
                method="linear", limit=7, limit_direction="both"
            )

            filled_dfs.append(group)

        df = pd.concat(filled_dfs, ignore_index=True)

        # Strategy 2: Fill remaining with monthly median per location
        still_null = df[numeric_cols].isnull().sum().sum()
        if still_null > 0:
            df["month"] = pd.to_datetime(df["date"]).dt.month

            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    monthly_medians = df.groupby(
                        ["latitude", "longitude", "month"]
                    )[col].transform("median")
                    df[col] = df[col].fillna(monthly_medians)

            df.drop(columns=["month"], inplace=True)

        # Strategy 3: Fill any remaining with global column median
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())

        total_nulls_after = df.isnull().sum().sum()
        logger.info(
            f"🔧 Missing values: {total_nulls_before:,} → {total_nulls_after:,} "
            f"(filled {total_nulls_before - total_nulls_after:,})"
        )

        return df

    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and cap outliers."""
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Skip non-weather columns
        skip_cols = ["latitude", "longitude", "frost_hours", "hot_hours",
                     "comfortable_hours", "precipitation_hours", "dry_hours",
                     "calm_hours", "strong_wind_hours", "high_humidity_hours",
                     "low_cloud_hours", "overcast_hours", "weather_code_mode"]
        numeric_cols = [c for c in numeric_cols if c not in skip_cols]

        total_capped = 0

        if self.outlier_method == "iqr":
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                lower = Q1 - self.outlier_factor * IQR
                upper = Q3 + self.outlier_factor * IQR

                outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                if outliers > 0:
                    df[col] = df[col].clip(lower=lower, upper=upper)
                    total_capped += outliers

        elif self.outlier_method == "zscore":
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    z_scores = ((df[col] - mean) / std).abs()
                    outliers = (z_scores > self.outlier_factor).sum()
                    if outliers > 0:
                        lower = mean - self.outlier_factor * std
                        upper = mean + self.outlier_factor * std
                        df[col] = df[col].clip(lower=lower, upper=upper)
                        total_capped += outliers

        logger.info(f"📐 Outliers capped: {total_capped:,} values ({self.outlier_method})")

        return df

    def _validate_physical_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure values are within physically possible ranges."""
        df = df.copy()
        fixes = 0

        for col, (vmin, vmax) in self.PHYSICAL_RANGES.items():
            if col not in df.columns:
                continue

            violations = ((df[col] < vmin) | (df[col] > vmax)).sum()
            if violations > 0:
                df[col] = df[col].clip(lower=vmin, upper=vmax)
                fixes += violations

        if fixes > 0:
            logger.info(f"🔧 Physical range fixes: {fixes:,} values clipped")

        return df

    def summary(self, df: pd.DataFrame) -> dict:
        """Generate cleaning summary."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_columns": len(numeric_cols),
            "total_nulls": int(df.isnull().sum().sum()),
            "null_pct": round(df.isnull().mean().mean() * 100, 2),
            "unique_points": df[["latitude", "longitude"]].drop_duplicates().shape[0],
        }