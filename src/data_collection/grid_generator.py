"""
Generate systematic grid points for a given region.
"""

import numpy as np
import pandas as pd
from config.grid_config import get_active_region
from config.settings import INTERIM_DIR
from src.utils.logger import get_logger
from src.utils.io_helpers import save_parquet

logger = get_logger("grid_generator")


class GridGenerator:
    """
    Generates a regular latitude/longitude grid for any region.
    
    Usage:
        generator = GridGenerator()
        grid_df = generator.generate()
        generator.save()
    """

    def __init__(self, region_config: dict = None):
        self.config = region_config or get_active_region()
        self.grid_df = None

        logger.info(
            f"🌍 GridGenerator initialized for: {self.config['name']} | "
            f"Spacing: {self.config['grid_spacing']}°"
        )

    def generate(self) -> pd.DataFrame:
        """
        Generate grid points within the bounding box.
        
        Returns:
            DataFrame with columns: [point_id, latitude, longitude]
        """
        lats = np.arange(
            self.config["lat_min"],
            self.config["lat_max"] + self.config["grid_spacing"],
            self.config["grid_spacing"],
        )
        lons = np.arange(
            self.config["lon_min"],
            self.config["lon_max"] + self.config["grid_spacing"],
            self.config["grid_spacing"],
        )

        # Create all combinations
        grid_points = []
        point_id = 0

        for lat in lats:
            for lon in lons:
                grid_points.append({
                    "point_id": f"PT_{point_id:05d}",
                    "latitude": round(lat, 4),
                    "longitude": round(lon, 4),
                })
                point_id += 1

        self.grid_df = pd.DataFrame(grid_points)

        logger.info(
            f"📍 Generated {len(self.grid_df)} grid points | "
            f"Lat range: [{lats.min():.1f}, {lats.max():.1f}] | "
            f"Lon range: [{lons.min():.1f}, {lons.max():.1f}]"
        )

        return self.grid_df

    def save(self, filename: str = "grid_points_raw.csv") -> None:
        """Save grid points to interim directory."""
        if self.grid_df is None:
            raise ValueError("No grid generated yet. Call generate() first.")

        path = INTERIM_DIR / filename
        self.grid_df.to_csv(path, index=False)
        logger.info(f"💾 Saved grid points: {path}")

    def summary(self) -> dict:
        """Return a summary of the generated grid."""
        if self.grid_df is None:
            return {"status": "No grid generated"}

        return {
            "region": self.config["name"],
            "total_points": len(self.grid_df),
            "grid_spacing": self.config["grid_spacing"],
            "lat_range": (self.grid_df["latitude"].min(), self.grid_df["latitude"].max()),
            "lon_range": (self.grid_df["longitude"].min(), self.grid_df["longitude"].max()),
            "approx_resolution_km": self.config["grid_spacing"] * 111,
        }