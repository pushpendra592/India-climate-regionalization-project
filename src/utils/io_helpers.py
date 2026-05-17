"""
Input/output helpers for consistent CSV-based storage.
"""

import json
import pickle
from pathlib import Path
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("io")

PARQUET_AVAILABLE = False
DEFAULT_FORMAT = "csv"
logger.info("Storage format: csv (parquet disabled by project setting)")


def _csv_path(path: Path) -> Path:
    path = Path(path)
    if path.suffix.lower() != ".csv":
        return path.with_suffix(".csv")
    return path


def save_dataframe(df: pd.DataFrame, path: Path, description: str = "data"):
    """Save DataFrame as CSV only."""
    csv_path = _csv_path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)

    size_mb = csv_path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved {description}: {csv_path.name} ({len(df)} rows, {size_mb:.1f} MB)")


def load_dataframe(path: Path, description: str = "data") -> pd.DataFrame:
    """Load DataFrame from CSV only."""
    csv_path = _csv_path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {description}: {csv_path.name} ({len(df)} rows)")
    return df


def save_parquet(df, path, description="data"):
    save_dataframe(df, path, description)


def load_parquet(path, description="data"):
    return load_dataframe(path, description)


def save_json(data: dict, path: Path, description: str = "config"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved {description}: {path.name}")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pickle(obj, path: Path, description: str = "object"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    logger.info(f"Saved {description}: {path.name}")


def load_pickle(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)
