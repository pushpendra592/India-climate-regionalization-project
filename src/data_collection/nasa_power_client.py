"""
NASA POWER API client with parallel point downloads.
"""

import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import (
    NASA_POWER_BASE_URL,
    RAW_DIR,
    START_DATE,
    END_DATE,
    API_MAX_RETRIES,
)
from config.feature_registry import NASA_POWER_PARAMS
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("nasa_power")


class NASAPowerClient:
    def __init__(
        self,
        start_date: str = START_DATE,
        end_date: str = END_DATE,
        params: List[str] = None,
        save_dir: Path = None,
        max_workers: int = 5,
    ):
        self.start_date = start_date.replace("-", "")
        self.end_date = end_date.replace("-", "")
        self.params = params or NASA_POWER_PARAMS
        self.save_dir = save_dir or RAW_DIR / "nasa_power"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers

        self.failed_points = []
        self.success_count = 0

        logger.info(
            f"NASA POWER client initialized | Period: {start_date} to {end_date} | "
            f"Parameters: {len(self.params)} | Workers: {max_workers}"
        )

    @retry(
        stop=stop_after_attempt(API_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    )
    def _fetch_single_point(self, lat: float, lon: float) -> Optional[pd.DataFrame]:
        request_params = {
            "parameters": ",".join(self.params),
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": self.start_date,
            "end": self.end_date,
            "format": "JSON",
        }

        response = requests.get(NASA_POWER_BASE_URL, params=request_params, timeout=120)
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code} for ({lat}, {lon})")
            return None

        data = response.json()
        if "properties" not in data or "parameter" not in data["properties"]:
            logger.error(f"Invalid response for ({lat}, {lon})")
            return None

        records = self._parse_nasa_response(data)
        if not records:
            return None

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(
            df["YEAR"].astype(str).str.zfill(4)
            + df["MO"].astype(str).str.zfill(2)
            + df["DY"].astype(str).str.zfill(2),
            format="%Y%m%d",
        )
        df = df.drop(columns=["YEAR", "MO", "DY", "HR"], errors="ignore")
        df = df.replace(-999.0, pd.NA)
        df["latitude"] = lat
        df["longitude"] = lon
        return df

    def _parse_nasa_response(self, data: Dict) -> List[Dict]:
        records = []
        try:
            parameters = data["properties"]["parameter"]
            first_param = list(parameters.keys())[0]
            timestamps = sorted(parameters[first_param].keys())

            for ts in timestamps:
                row = {
                    "YEAR": int(ts[:4]),
                    "MO": int(ts[4:6]),
                    "DY": int(ts[6:8]),
                    "HR": int(ts[8:10]) if len(ts) >= 10 else 0,
                }
                for param in self.params:
                    row[param] = parameters.get(param, {}).get(ts, -999)
                records.append(row)
        except (KeyError, IndexError, ValueError) as exc:
            logger.error(f"Error parsing NASA response: {exc}")
        return records

    def _process_single_point(self, point_id: str, lat: float, lon: float) -> dict:
        try:
            df = self._fetch_single_point(lat, lon)
            if df is None:
                return {"point_id": point_id, "lat": lat, "lon": lon, "status": "failed"}

            filename = f"nasa_power_{point_id}_{lat}_{lon}.csv"
            df.to_csv(self.save_dir / filename, index=False)
            return {"point_id": point_id, "status": "success", "rows": len(df)}
        except Exception as exc:
            return {"point_id": point_id, "lat": lat, "lon": lon, "status": "failed", "error": str(exc)}

    def _get_completed_points(self) -> set:
        completed = set()
        for file in self.save_dir.glob("nasa_power_PT_*.csv"):
            parts = file.stem.split("_")
            try:
                lat = float(parts[-2])
                lon = float(parts[-1])
                completed.add((lat, lon))
            except (ValueError, IndexError):
                continue
        return completed

    def fetch_all(self, grid_df: pd.DataFrame, resume: bool = True) -> None:
        if resume:
            completed = self._get_completed_points()
            remaining = grid_df[
                ~grid_df.apply(lambda row: (row["latitude"], row["longitude"]) in completed, axis=1)
            ]
            if len(completed) > 0:
                logger.info(f"Resuming: {len(completed)} done, {len(remaining)} remaining")
        else:
            remaining = grid_df

        if len(remaining) == 0:
            logger.info("All selected NASA POWER points already downloaded")
            return

        with Timer(f"Fetching {len(remaining)} points from NASA POWER"):
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self._process_single_point,
                        row["point_id"],
                        row["latitude"],
                        row["longitude"],
                    ): row["point_id"]
                    for _, row in remaining.iterrows()
                }

                progress = tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="NASA POWER",
                    unit="points",
                )

                for future in progress:
                    result = future.result()
                    if result["status"] == "success":
                        self.success_count += 1
                    else:
                        self.failed_points.append(result)

                    progress.set_postfix(
                        {"success": self.success_count, "failed": len(self.failed_points)}
                    )

        if self.failed_points:
            pd.DataFrame(self.failed_points).to_csv(self.save_dir / "failed_points.csv", index=False)

    def combine_all(self, point_ids: Optional[List[str]] = None) -> pd.DataFrame:
        files = sorted(self.save_dir.glob("nasa_power_PT_*.csv"))
        if point_ids is not None:
            prefixes = {f"nasa_power_{point_id}" for point_id in point_ids}
            files = [file for file in files if any(file.stem.startswith(prefix) for prefix in prefixes)]

        if not files:
            raise FileNotFoundError(f"No files found in {self.save_dir}")

        logger.info(f"Combining {len(files)} NASA POWER files")
        frames = [pd.read_csv(file) for file in tqdm(files, desc="Combining")]
        combined = pd.concat(frames, ignore_index=True)
        if "date" in combined.columns:
            combined["date"] = pd.to_datetime(combined["date"])

        logger.info(
            f"Combined NASA POWER dataset: {len(combined)} rows | "
            f"{combined[['latitude', 'longitude']].drop_duplicates().shape[0]} unique points"
        )
        return combined
