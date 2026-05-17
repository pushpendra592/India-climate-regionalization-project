"""
Validates collected data for completeness and quality.
"""

import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("validator")


class DataValidator:
    """
    Validates weather data for:
        - Missing values
        - Date continuity
        - Value range checks
        - Point coverage
    """

    # Expected ranges for sanity checks
    VALID_RANGES = {
        "temperature_2m_mean": (-50, 60),
        "temperature_2m_max": (-50, 65),
        "temperature_2m_min": (-60, 50),
        "precipitation_sum": (0, 500),
        "relative_humidity_2m_mean": (0, 100),
        "pressure_msl_mean": (870, 1084),
        "cloud_cover_mean": (0, 100),
        "wind_speed_10m_mean": (0, 200),
        "wind_speed_10m_max": (0, 300),
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.issues = []

    def check_missing_values(self) -> dict:
        """Check missing values per column."""
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df) * 100).round(2)

        report = {}
        for col in missing[missing > 0].index:
            report[col] = {
                "missing_count": int(missing[col]),
                "missing_pct": float(missing_pct[col]),
            }
            if missing_pct[col] > 10:
                self.issues.append(f"⚠️  {col}: {missing_pct[col]}% missing")

        logger.info(f"Missing value check: {len(report)} columns with nulls")
        return report

    def check_date_continuity(self) -> dict:
        """Check for gaps in date sequences per point."""
        gaps = {}

        for point_id, group in self.df.groupby(["latitude", "longitude"]):
            dates = pd.to_datetime(group["date"]).sort_values()
            expected = pd.date_range(dates.min(), dates.max(), freq="D")
            missing_dates = expected.difference(dates)

            if len(missing_dates) > 0:
                gaps[str(point_id)] = len(missing_dates)
                if len(missing_dates) > 30:
                    self.issues.append(
                        f"⚠️  Point {point_id}: {len(missing_dates)} missing dates"
                    )

        logger.info(f"Date continuity: {len(gaps)} points with gaps")
        return gaps

    def check_value_ranges(self) -> dict:
        """Check if values fall within expected physical ranges."""
        outliers = {}

        for col, (vmin, vmax) in self.VALID_RANGES.items():
            if col not in self.df.columns:
                continue

            out_of_range = (
                (self.df[col] < vmin) | (self.df[col] > vmax)
            ).sum()

            if out_of_range > 0:
                outliers[col] = int(out_of_range)
                pct = out_of_range / len(self.df) * 100
                if pct > 1:
                    self.issues.append(
                        f"⚠️  {col}: {out_of_range} values outside [{vmin}, {vmax}]"
                    )

        logger.info(f"Range check: {len(outliers)} columns with out-of-range values")
        return outliers

    def check_point_coverage(self, expected_points: int = None) -> dict:
        """Check how many unique points have data."""
        unique_points = self.df.groupby(["latitude", "longitude"]).size()

        report = {
            "total_points": len(unique_points),
            "min_records_per_point": int(unique_points.min()),
            "max_records_per_point": int(unique_points.max()),
            "mean_records_per_point": float(unique_points.mean().round(1)),
        }

        if expected_points:
            report["expected_points"] = expected_points
            report["coverage_pct"] = round(len(unique_points) / expected_points * 100, 1)

        logger.info(f"Point coverage: {report['total_points']} points with data")
        return report

    def run_all(self, expected_points: int = None) -> dict:
        """Run all validation checks."""
        logger.info("🔍 Running full data validation...")

        report = {
            "missing_values": self.check_missing_values(),
            "date_continuity": self.check_date_continuity(),
            "value_ranges": self.check_value_ranges(),
            "point_coverage": self.check_point_coverage(expected_points),
            "issues": self.issues,
        }

        if self.issues:
            logger.warning(f"⚠️  Found {len(self.issues)} issues:")
            for issue in self.issues:
                logger.warning(f"   {issue}")
        else:
            logger.info("✅ All validation checks passed!")

        return report
