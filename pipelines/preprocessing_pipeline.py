"""
End-to-end preprocessing pipeline for NASA POWER-only data.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import INTERIM_DIR, PROCESSED_DIR
from src.preprocessing.cleaner import DataCleaner
from src.preprocessing.aggregator import TemporalAggregator
from src.preprocessing.feature_engineer import FeatureEngineer
from src.preprocessing.nasa_power_adapter import NASAPowerAdapter
from src.utils.io_helpers import load_dataframe, save_dataframe
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("preprocessing_pipeline")


def run_preprocessing():
    with Timer("Full Preprocessing Pipeline"):
        logger.info("Loading NASA POWER interim dataset")
        nasa_df = load_dataframe(INTERIM_DIR / "nasa_power_combined.parquet", "NASA POWER combined")

        adapter = NASAPowerAdapter()
        merged = adapter.transform(nasa_df)
        save_dataframe(merged, INTERIM_DIR / "merged_daily.parquet", "normalized NASA daily weather data")

        cleaner = DataCleaner()
        cleaned = cleaner.clean(merged)

        engineer = FeatureEngineer()
        featured = engineer.transform(cleaned)
        save_dataframe(featured, PROCESSED_DIR / "feature_matrix_daily.parquet", "daily feature matrix")

        aggregator = TemporalAggregator()
        monthly = aggregator.to_monthly(featured)
        save_dataframe(monthly, PROCESSED_DIR / "feature_matrix_monthly.parquet", "monthly feature matrix")

        seasonal = aggregator.to_seasonal(featured)
        save_dataframe(seasonal, PROCESSED_DIR / "feature_matrix_seasonal.parquet", "seasonal feature matrix")

        yearly = aggregator.to_yearly(featured)
        save_dataframe(yearly, PROCESSED_DIR / "feature_matrix_yearly.parquet", "yearly feature matrix")

        normals = aggregator.to_climate_normals(featured)
        normals = engineer.transform(normals)
        save_dataframe(normals, PROCESSED_DIR / "climate_normals.parquet", "climate normals")

        logger.info("Preprocessing complete")
        return {
            "daily": featured,
            "monthly": monthly,
            "seasonal": seasonal,
            "yearly": yearly,
            "normals": normals,
        }


if __name__ == "__main__":
    run_preprocessing()
