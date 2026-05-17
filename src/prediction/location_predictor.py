"""
Shared exact-location prediction flow for CLI and dashboard usage.
"""

from __future__ import annotations

import pickle

import numpy as np

from config.settings import MODELS_DIR, PROCESSED_DIR
from src.clustering.base_clusterer import BaseClusterer
from src.data_collection.nasa_power_client import NASAPowerClient
from src.insights.cluster_profiler import ClusterProfiler
from src.location.city_lookup import resolve_place
from src.preprocessing.aggregator import TemporalAggregator
from src.preprocessing.cleaner import DataCleaner
from src.preprocessing.feature_engineer import FeatureEngineer
from src.preprocessing.nasa_power_adapter import NASAPowerAdapter
from src.utils.io_helpers import load_dataframe, load_json
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("location_predictor")


class LocationPredictor:
    def __init__(self):
        self.profiler = ClusterProfiler()

    def _fetch_exact_location(self, lat: float, lon: float):
        client = NASAPowerClient(max_workers=1)
        raw = client._fetch_single_point(lat, lon)
        if raw is None or raw.empty:
            raise ValueError(f"No NASA POWER data returned for ({lat}, {lon}).")
        return raw

    def _build_location_features(self, raw_df):
        adapter = NASAPowerAdapter()
        cleaner = DataCleaner()
        engineer = FeatureEngineer()
        aggregator = TemporalAggregator()

        adapted = adapter.transform(raw_df)
        cleaned = cleaner.clean(adapted)
        featured = engineer.transform(cleaned)
        normals = aggregator.to_climate_normals(featured)
        return engineer.transform(normals)

    def _load_prediction_assets(self):
        metadata = load_json(MODELS_DIR / "prediction_metadata.json")

        with open(MODELS_DIR / "scaler.pkl", "rb") as handle:
            scaler = pickle.load(handle)
        with open(MODELS_DIR / "pca_reducer.pkl", "rb") as handle:
            reducer = pickle.load(handle)

        best_key = metadata.get("best_key")
        model = None
        model_path = MODELS_DIR / f"{best_key}_model.pkl"
        if best_key and model_path.exists():
            model = BaseClusterer.load(model_path)

        clustered_normals = load_dataframe(
            PROCESSED_DIR / "climate_normals_clustered.parquet",
            "clustered climate normals",
        )
        return metadata, scaler, reducer, model, clustered_normals

    def _prepare_feature_vector(self, normals, feature_cols):
        row = normals.copy()
        for col in feature_cols:
            if col not in row.columns:
                row[col] = np.nan
        return row[feature_cols]

    def _assign_cluster(
        self,
        location_vector_scaled,
        location_vector_reduced,
        metadata,
        scaler,
        reducer,
        model,
        clustered_normals,
    ):
        best_key = metadata.get("best_key")
        label_col = (
            f"cluster_{best_key}"
            if best_key and f"cluster_{best_key}" in clustered_normals.columns
            else "cluster"
        )

        predicted_cluster = None
        assignment_method = "nearest-centroid"
        confidence = None
        alternative_cluster = None

        if model is not None and hasattr(model, "predict"):
            try:
                predicted = model.predict(location_vector_reduced)
                predicted_cluster = int(predicted[0])
                assignment_method = f"model:{best_key}"
                if hasattr(model, "model") and hasattr(model.model, "predict_proba"):
                    probs = model.model.predict_proba(location_vector_reduced)[0]
                    ranked = np.argsort(probs)[::-1]
                    confidence = float(probs[ranked[0]])
                    if len(ranked) > 1:
                        alternative_cluster = int(ranked[1])
            except Exception:
                predicted_cluster = None

        if predicted_cluster is None:
            feature_cols = scaler.get_feature_names()
            X_train_scaled = scaler.transform(clustered_normals[feature_cols])
            X_train_reduced = reducer.transform(X_train_scaled)
            labels = clustered_normals[label_col].to_numpy()

            centroids = {}
            for cluster_id in sorted(set(labels)):
                if int(cluster_id) < 0:
                    continue
                centroids[int(cluster_id)] = X_train_reduced[labels == cluster_id].mean(axis=0)

            distances = {
                cluster_id: float(np.linalg.norm(location_vector_reduced[0] - centroid))
                for cluster_id, centroid in centroids.items()
            }
            ranked = sorted(distances.items(), key=lambda item: item[1])
            predicted_cluster = int(ranked[0][0])
            if len(ranked) > 1:
                alternative_cluster = int(ranked[1][0])
                nearest = ranked[0][1]
                second = ranked[1][1]
                confidence = float(1.0 - (nearest / (nearest + second + 1e-9)))
            else:
                confidence = 1.0

        return int(predicted_cluster), label_col, assignment_method, confidence, alternative_cluster

    def predict(self, lat: float, lon: float, location_name: str | None = None) -> dict:
        with Timer("Exact location prediction"):
            raw_df = self._fetch_exact_location(lat, lon)
            location_normals = self._build_location_features(raw_df)
            metadata, scaler, reducer, model, clustered_normals = self._load_prediction_assets()

            feature_cols = scaler.get_feature_names()
            location_normals = self._prepare_feature_vector(location_normals, feature_cols)
            training_feature_frame = clustered_normals[feature_cols].copy()
            training_medians = training_feature_frame.median(numeric_only=True)
            location_normals = location_normals.fillna(training_medians).fillna(0)

            scaled = scaler.transform(location_normals)
            reduced = reducer.transform(scaled)

            cluster_id, label_col, assignment_method, confidence, alternative_cluster = self._assign_cluster(
                scaled,
                reduced,
                metadata,
                scaler,
                reducer,
                model,
                clustered_normals,
            )

            auto_labels = metadata.get("auto_labels", {})
            label = auto_labels.get(str(cluster_id), f"Cluster {cluster_id}")
            alternative_label = (
                auto_labels.get(str(alternative_cluster), f"Cluster {alternative_cluster}")
                if alternative_cluster is not None
                else None
            )

            profile_df = clustered_normals.copy()
            if label_col != "cluster":
                profile_df["prediction_cluster"] = profile_df[label_col]
                profile_label_col = "prediction_cluster"
            else:
                profile_label_col = "cluster"

            description = self.profiler.describe_cluster(
                profile_df,
                cluster_id,
                scaler.get_feature_names(),
                profile_label_col,
            )

            nearest_examples = self.profiler.get_nearest_examples(
                profile_df,
                lat,
                lon,
                cluster_id,
                label_col=profile_label_col,
                limit=3,
            )

            result = {
                "location_name": location_name,
                "latitude": lat,
                "longitude": lon,
                "cluster_id": cluster_id,
                "cluster_label": label,
                "assignment_method": assignment_method,
                "best_algorithm": metadata.get("best_algorithm"),
                "confidence": round(float(confidence), 4) if confidence is not None else None,
                "alternative_cluster_id": alternative_cluster,
                "alternative_cluster_label": alternative_label,
                "summary": self.profiler.summarize_cluster_label(label),
                "reduced_coords": [
                    float(value) for value in reduced[0][: min(3, reduced.shape[1])]
                ] if reduced.shape[1] >= 1 else None,
                "top_characteristics": description.get("characteristics", [])[:5],
                "nearest_examples": nearest_examples,
            }

            logger.info(
                f"Assigned ({lat}, {lon}) to cluster {cluster_id} [{label}] using {assignment_method}"
            )
            return result

    def predict_place(self, place_name: str) -> dict:
        place = resolve_place(place_name)
        result = self.predict(place.latitude, place.longitude, location_name=place.name)
        result["state"] = place.state
        result["address"] = place.address
        return result

    def predict_city(self, city_name: str) -> dict:
        return self.predict_place(city_name)
