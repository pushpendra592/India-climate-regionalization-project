"""
End-to-end NASA POWER data collection and validation pipeline.
"""

import argparse
import math
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import INTERIM_DIR
from src.data_collection.grid_generator import GridGenerator
from src.data_collection.land_mask import LandMasker
from src.data_collection.nasa_power_client import NASAPowerClient
from src.data_collection.data_validator import DataValidator
from src.utils.io_helpers import save_dataframe
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("data_pipeline")


def _sample_points(points_df: pd.DataFrame, limit: int, strategy: str) -> pd.DataFrame:
    if limit >= len(points_df):
        return points_df.copy()

    if strategy == "head":
        selected = points_df.head(limit).copy()
        logger.info(f"Sampling strategy=head selected the first {len(selected)} points")
        return selected

    working = points_df.copy().reset_index(drop=True)
    bin_count = max(2, min(int(math.sqrt(limit)), 12))
    lat_bins = min(bin_count, working["latitude"].nunique())
    lon_bins = min(bin_count, working["longitude"].nunique())

    working["lat_bin"] = pd.qcut(working["latitude"], q=lat_bins, duplicates="drop")
    working["lon_bin"] = pd.qcut(working["longitude"], q=lon_bins, duplicates="drop")
    working["cell_rank"] = working.groupby(["lat_bin", "lon_bin"]).cumcount()

    selected_parts = []
    rank = 0
    while sum(len(part) for part in selected_parts) < limit:
        tier = working[working["cell_rank"] == rank]
        if tier.empty:
            break
        selected_parts.append(tier)
        rank += 1

    selected = pd.concat(selected_parts, ignore_index=True).drop_duplicates("point_id")
    selected = selected.sort_values(["cell_rank", "latitude", "longitude"]).head(limit).copy()

    logger.info(
        f"Sampling strategy={strategy} selected {len(selected)} points across "
        f"{selected[['lat_bin', 'lon_bin']].drop_duplicates().shape[0]} geographic cells"
    )

    return selected.drop(columns=["lat_bin", "lon_bin", "cell_rank"], errors="ignore")


def _prepare_points(
    apply_land_mask: bool = True,
    limit: int | None = None,
    sampling_strategy: str = "stratified",
):
    generator = GridGenerator()
    grid_df = generator.generate()
    generator.save()

    points_df = grid_df
    if apply_land_mask:
        masker = LandMasker()
        points_df = masker.apply(grid_df)
        masker.save_land_points(points_df)

    if limit is not None:
        points_df = _sample_points(points_df, limit, sampling_strategy)
        logger.info(f"Using a limited subset of {len(points_df)} points for this run")

    return grid_df, points_df


def run_data_pipeline(
    fetch_remote: bool = False,
    apply_land_mask: bool = True,
    resume: bool = True,
    max_workers: int = 5,
    limit: int | None = None,
    sampling_strategy: str = "stratified",
):
    with Timer("Full Data Pipeline"):
        grid_df, points_df = _prepare_points(
            apply_land_mask=apply_land_mask,
            limit=limit,
            sampling_strategy=sampling_strategy,
        )
        point_ids = points_df["point_id"].tolist()
        nasa_client = NASAPowerClient(max_workers=max_workers)

        if fetch_remote:
            logger.info("Fetching remote weather data from NASA POWER only")
            nasa_client.fetch_all(points_df, resume=resume)
        else:
            logger.info("Skipping remote collection and reusing local NASA POWER raw files")

        logger.info("Combining NASA POWER point files into interim dataset")
        nasa_combined = nasa_client.combine_all(point_ids=point_ids)
        save_dataframe(
            nasa_combined,
            INTERIM_DIR / "nasa_power_combined.parquet",
            description="combined NASA POWER data",
        )

        logger.info("Running validation on NASA POWER dataset")
        nasa_validation = DataValidator(nasa_combined).run_all(expected_points=len(points_df))

        return {
            "grid": grid_df,
            "land_points": points_df,
            "nasa_power": nasa_combined,
            "nasa_power_validation": nasa_validation,
        }


def build_parser():
    parser = argparse.ArgumentParser(description="Run NASA POWER data collection pipeline.")
    parser.add_argument("--fetch-remote", action="store_true", help="Download fresh NASA POWER data.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the run to the first N land points.")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel point downloads.")
    parser.add_argument("--no-resume", action="store_true", help="Disable resume behavior.")
    parser.add_argument("--no-land-mask", action="store_true", help="Use the raw grid without a land mask.")
    parser.add_argument(
        "--sampling",
        choices=["stratified", "head"],
        default="stratified",
        help="How to choose limited points: geographic stratified coverage or first-N order.",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    run_data_pipeline(
        fetch_remote=args.fetch_remote,
        apply_land_mask=not args.no_land_mask,
        resume=not args.no_resume,
        max_workers=args.workers,
        limit=args.limit,
        sampling_strategy=args.sampling,
    )
