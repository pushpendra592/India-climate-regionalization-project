"""
Legacy merger utilities for combining normalized weather data with NASA POWER fields.

The active project pipeline is NASA-only. This module remains only for older
experiments that used a second weather source.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from config.settings import INTERIM_DIR
from config.feature_registry import NASA_COLUMN_RENAME
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("merger")


class DataMerger:
    """
    Merges a normalized daily weather frame with NASA POWER daily data.

    Merge key: (latitude, longitude, date)

    Usage:
        merger = DataMerger()
        merged = merger.merge(om_df, nasa_df)
        merger.save(merged)
    """

    def __init__(self, tolerance_km: float = 30.0):
        """
        Args:
            tolerance_km: Max distance between the two source grid points
                          to consider them the same location.
        """
        self.tolerance_km = tolerance_km

    def _rename_nasa_columns(self, nasa_df: pd.DataFrame) -> pd.DataFrame:
        """Rename NASA columns to clean names to avoid conflicts."""
        df = nasa_df.copy()
        df = df.rename(columns=NASA_COLUMN_RENAME)
        return df

    def _align_dates(self, om_df: pd.DataFrame, nasa_df: pd.DataFrame) -> tuple:
        """Ensure both DataFrames have matching date ranges."""
        om_df = om_df.copy()
        nasa_df = nasa_df.copy()

        om_df["date"] = pd.to_datetime(om_df["date"])
        nasa_df["date"] = pd.to_datetime(nasa_df["date"])

        # Find common date range
        common_start = max(om_df["date"].min(), nasa_df["date"].min())
        common_end = min(om_df["date"].max(), nasa_df["date"].max())

        om_df = om_df[(om_df["date"] >= common_start) & (om_df["date"] <= common_end)]
        nasa_df = nasa_df[(nasa_df["date"] >= common_start) & (nasa_df["date"] <= common_end)]

        logger.info(
            f"📅 Common date range: {common_start.date()} → {common_end.date()} "
            f"({(common_end - common_start).days} days)"
        )

        return om_df, nasa_df

    def _round_coordinates(self, df: pd.DataFrame, decimals: int = 1) -> pd.DataFrame:
        """
        Round coordinates for matching.
        Different sources may return slightly different coordinates.
        """
        df = df.copy()
        df["lat_round"] = df["latitude"].round(decimals)
        df["lon_round"] = df["longitude"].round(decimals)
        return df

    def merge(
        self,
        om_df: pd.DataFrame,
        nasa_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge normalized weather and NASA POWER dataframes.

        Args:
            om_df:   normalized daily weather data
            nasa_df: NASA POWER daily data

        Returns:
            Merged DataFrame
        """
        with Timer("Merging normalized weather + NASA POWER"):

            logger.info(
                f"📊 Input shapes - normalized weather: {om_df.shape} | NASA: {nasa_df.shape}"
            )

            # Step 1: Rename NASA columns
            nasa_df = self._rename_nasa_columns(nasa_df)

            # Step 2: Align date ranges
            om_df, nasa_df = self._align_dates(om_df, nasa_df)

            # Step 3: Round coordinates for matching
            om_df = self._round_coordinates(om_df)
            nasa_df = self._round_coordinates(nasa_df)

            # Step 4: Merge on rounded coordinates + date
            merged = pd.merge(
                om_df,
                nasa_df,
                on=["lat_round", "lon_round", "date"],
                how="left",
                suffixes=("", "_nasa"),
            )

            # Step 5: Clean up
            # Use the normalized weather coordinates as primary
            if "latitude_nasa" in merged.columns:
                merged.drop(columns=["latitude_nasa", "longitude_nasa"], inplace=True, errors="ignore")

            # Remove helper columns
            merged.drop(columns=["lat_round", "lon_round"], inplace=True, errors="ignore")

            # Step 6: Report merge quality
            total_rows = len(merged)
            nasa_cols = [c for c in merged.columns if c.startswith("nasa_")]
            nasa_matched = merged[nasa_cols[0]].notna().sum() if nasa_cols else 0
            match_pct = nasa_matched / total_rows * 100 if total_rows > 0 else 0

            logger.info(
                f"✅ Merged shape: {merged.shape} | "
                f"NASA match rate: {match_pct:.1f}% | "
                f"NASA columns added: {len(nasa_cols)}"
            )

            if match_pct < 50:
                logger.warning(
                    f"⚠️  Low NASA match rate ({match_pct:.1f}%). "
                    f"Check coordinate alignment."
                )

        return merged

    def save(self, merged_df: pd.DataFrame, filename: str = "merged_daily.csv"):
        """Save merged data."""
        path = INTERIM_DIR / filename
        merged_df.to_csv(path, index=False)
        size_mb = path.stat().st_size / (1024 * 1024)
        logger.info(f"💾 Saved merged data: {path.name} ({len(merged_df)} rows, {size_mb:.1f} MB)")

    def quality_report(self, merged_df: pd.DataFrame) -> dict:
        """Generate merge quality report."""
        report = {
            "total_rows": len(merged_df),
            "total_columns": len(merged_df.columns),
            "unique_points": merged_df[["latitude", "longitude"]].drop_duplicates().shape[0],
            "date_range": (
                str(merged_df["date"].min()),
                str(merged_df["date"].max()),
            ),
            "normalized_weather_columns": len([c for c in merged_df.columns if not c.startswith("nasa_")]),
            "nasa_columns": len([c for c in merged_df.columns if c.startswith("nasa_")]),
            "missing_pct": merged_df.isnull().mean().to_dict(),
        }
        return report

