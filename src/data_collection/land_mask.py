"""
Filter grid points to keep only land-based points.
Uses India boundary GeoJSON to mask ocean points.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from config.settings import EXTERNAL_DIR, INTERIM_DIR
from config.grid_config import get_active_region
from src.utils.logger import get_logger

logger = get_logger("land_mask")


class LandMasker:
    """
    Filters grid points to retain only those on land.
    
    Supports two modes:
        1. GeoJSON boundary file (precise, recommended)
        2. Natural Earth low-res (fallback, built into geopandas)
    
    Usage:
        masker = LandMasker()
        land_points = masker.apply(grid_df)
    """

    def __init__(self, boundary_file: str = None):
        self.config = get_active_region()
        self.boundary = None

        if boundary_file:
            self._load_boundary(boundary_file)
        elif self.config.get("boundary_file"):
            boundary_path = EXTERNAL_DIR / self.config["boundary_file"]
            if boundary_path.exists():
                self._load_boundary(boundary_path)
            else:
                logger.warning(
                    f"⚠️  Boundary file not found: {boundary_path}. "
                    f"Using Natural Earth fallback."
                )
                self._load_natural_earth()
        else:
            self._load_natural_earth()

    def _load_boundary(self, path: Path):
        """Load boundary from GeoJSON file."""
        path = Path(path)
        gdf = gpd.read_file(path)
        self.boundary = gdf.geometry.unary_union
        logger.info(f"🗺️  Loaded boundary from: {path.name}")

    def _load_natural_earth(self):
        """Fallback: Use built-in Natural Earth dataset."""
        try:
            # Newer geopandas — download from URL
            url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
            world = gpd.read_file(url)
            name_col = "NAME"
        except Exception:
            try:
                # Older geopandas — built-in dataset
                world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
                name_col = "name"
            except Exception:
                raise RuntimeError(
                    "Cannot load Natural Earth data. "
                    "Please download India boundary GeoJSON manually. "
                    "Run: python setup_data.py"
                )

        region_name = self.config["name"]

        if region_name == "India":
            country = world[world[name_col] == "India"]
        elif region_name == "Global":
            country = world
        else:
            country = world[world[name_col] == region_name]

        if country.empty:
            logger.warning(f"⚠️  '{region_name}' not found. Using all land.")
            country = world

        self.boundary = country.geometry.unary_union
        logger.info(f"🗺️  Loaded Natural Earth boundary for: {region_name}")

    def apply(self, grid_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter grid points — keep only those inside the land boundary.
        
        Args:
            grid_df: DataFrame with 'latitude' and 'longitude' columns
        
        Returns:
            Filtered DataFrame with only land points
        """
        if self.boundary is None:
            raise ValueError("No boundary loaded.")

        total_points = len(grid_df)

        # Create geometry column
        geometry = [
            Point(lon, lat)
            for lat, lon in zip(grid_df["latitude"], grid_df["longitude"])
        ]
        gdf = gpd.GeoDataFrame(grid_df, geometry=geometry, crs="EPSG:4326")

        # Spatial filter
        land_mask = gdf.geometry.within(self.boundary)
        land_df = grid_df[land_mask].reset_index(drop=True)

        # Reassign point IDs
        land_df["point_id"] = [f"PT_{i:05d}" for i in range(len(land_df))]

        removed = total_points - len(land_df)
        logger.info(
            f"🏝️  Land masking: {total_points} → {len(land_df)} points "
            f"({removed} ocean/border points removed)"
        )

        return land_df

    def save_land_points(self, land_df: pd.DataFrame, filename: str = "grid_points_india.csv"):
        """Save filtered land points."""
        path = INTERIM_DIR / filename
        land_df.to_csv(path, index=False)
        logger.info(f"💾 Saved land points: {path}")