"""
End-to-end clustering pipeline.
"""

import sys
from pathlib import Path
import pickle
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR, MODELS_DIR, TABLES_DIR
from src.preprocessing.scaler import FeatureScaler, DimensionalityReducer
from src.clustering.optimizer import ClusterOptimizer
from src.clustering.comparison import ClusterComparison
from src.insights.cluster_profiler import ClusterProfiler
from src.utils.io_helpers import load_dataframe, save_dataframe, save_json
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("clustering_pipeline")


def _select_feature_columns(normals):
    exclude = {
        "latitude",
        "longitude",
        "date",
        "year",
        "month",
        "season",
        "cluster",
        "cluster_size",
        "cluster_pct",
        "days_count",
    }
    cols = [
        col for col in normals.select_dtypes(include=[np.number]).columns
        if col not in exclude
    ]

    redundant_aliases = {
        "nasa_temperature_2m": "temperature_2m_mean",
        "nasa_relative_humidity": "relative_humidity_2m_mean",
        "nasa_precipitation": "precipitation_sum",
        "nasa_wind_speed_10m": "wind_speed_10m_mean",
        "nasa_wind_direction_10m": "wind_direction_10m_mean",
        "nasa_surface_pressure": "surface_pressure_mean",
        "nasa_cloud_amount": "cloud_cover_mean",
    }
    cols = [
        col for col in cols
        if not (col in redundant_aliases and redundant_aliases[col] in cols)
    ]
    return cols


def _choose_final_climate_model(comparison_df):
    if len(comparison_df) == 0:
        return None

    allowed_prefixes = (
        "K-Means",
        "Hierarchical(Ward",
        "Hierarchical(Average",
        "GMM",
    )

    def _sorted_candidates(df):
        return df.sort_values(
            [
                "max_cluster_share",
                "silhouette",
                "cluster_balance",
                "davies_bouldin",
                "calinski_harabasz",
            ],
            ascending=[True, False, False, True, False],
        )

    climate_candidates = comparison_df[
        comparison_df["algorithm"].astype(str).str.startswith(allowed_prefixes)
        & comparison_df["n_clusters"].between(6, 8, inclusive="both")
        & (comparison_df["n_noise"].fillna(0) == 0)
        & (comparison_df["max_cluster_share"].fillna(1.0) <= 0.45)
    ].copy()

    if len(climate_candidates) > 0:
        return _sorted_candidates(climate_candidates).iloc[0]

    relaxed_climate = comparison_df[
        comparison_df["algorithm"].astype(str).str.startswith(allowed_prefixes)
        & comparison_df["n_clusters"].between(6, 8, inclusive="both")
        & (comparison_df["n_noise"].fillna(0) == 0)
        & (comparison_df["max_cluster_share"].fillna(1.0) <= 0.55)
    ].copy()

    if len(relaxed_climate) > 0:
        return _sorted_candidates(relaxed_climate).iloc[0]

    broad_coverage = comparison_df[
        comparison_df["algorithm"].astype(str).str.startswith(allowed_prefixes)
        & comparison_df["n_clusters"].between(5, 9, inclusive="both")
        & (comparison_df["n_noise"].fillna(0) <= max(1, 0.05 * comparison_df["n_samples"].max()))
        & (comparison_df["max_cluster_share"].fillna(1.0) <= 0.60)
    ].copy()

    if len(broad_coverage) > 0:
        return _sorted_candidates(broad_coverage).iloc[0]

    broad_allowed = comparison_df[
        comparison_df["algorithm"].astype(str).str.startswith(allowed_prefixes)
    ].copy()
    if len(broad_allowed) > 0:
        return _sorted_candidates(broad_allowed).iloc[0]

    return _sorted_candidates(comparison_df).iloc[0]


def run_clustering():
    """Run the full clustering pipeline."""
    with Timer("Full Clustering Pipeline"):
        normals = load_dataframe(PROCESSED_DIR / "climate_normals.parquet", "climate normals")
        feature_cols = _select_feature_columns(normals)
        logger.info(f"Using {len(feature_cols)} numeric features for clustering")

        if len(normals) < 3:
            raise ValueError(
                f"Need at least 3 grid points for clustering, found {len(normals)}."
            )

        scaler = FeatureScaler(method="standard")
        X_scaled = scaler.fit_transform(normals, feature_cols)
        feature_cols = scaler.get_feature_names()

        reducer = DimensionalityReducer()
        X_reduced = reducer.fit_pca(X_scaled, n_components=0.95, feature_names=feature_cols)

        optimizer = ClusterOptimizer()
        elbow_results = optimizer.silhouette_analysis(X_reduced)
        bic_results = optimizer.gmm_bic_aic(X_reduced)
        try:
            optimal_k = optimizer.find_optimal_k(X_reduced, method="silhouette")
        except ValueError:
            if len(normals) <= 3:
                optimal_k = 2
                logger.warning(
                    "Too few samples for silhouette-based K selection; using K=2 fallback"
                )
            else:
                optimal_k = optimizer.find_optimal_k(X_reduced, method="bic")
                logger.warning(
                    "Silhouette-based K selection unavailable; falling back to BIC"
                )

        optimal_k = max(2, min(optimal_k, len(normals) - 1))
        climate_k_values = [
            k for k in range(6, min(8, len(normals) - 1) + 1)
            if k >= 2
        ]
        candidate_ks = sorted({optimal_k, optimal_k + 2, optimal_k + 4, *climate_k_values})
        candidate_ks = [k for k in candidate_ks if 2 <= k < len(normals)]
        dbscan_eps = float(np.percentile(optimizer.estimate_dbscan_eps(X_reduced), 90))

        comparison = ClusterComparison(X_reduced)
        results = comparison.run_all(
            optimal_k=optimal_k,
            candidate_ks=candidate_ks,
            dbscan_eps=dbscan_eps,
            dbscan_min_samples=5,
            hdbscan_min_cluster_size=max(10, len(normals) // 50),
        )

        comparison_df = comparison.get_comparison()
        selected_row = _choose_final_climate_model(comparison_df)
        best_algorithm = selected_row["algorithm"] if selected_row is not None else comparison.get_best_algorithm()
        best_key = comparison.get_key_for_algorithm(best_algorithm)
        if best_key is None and results:
            best_key = next(iter(results))
            best_algorithm = comparison_df.iloc[0]["algorithm"] if len(comparison_df) else best_key

        logger.info(f"Selected final climate model: {best_algorithm}")
        if selected_row is not None:
            logger.info(
                "Selection metrics | clusters=%s | noise=%s | silhouette=%s | max_share=%s",
                selected_row.get("n_clusters"),
                selected_row.get("n_noise"),
                selected_row.get("silhouette"),
                selected_row.get("max_cluster_share"),
            )

        all_labels = comparison.get_all_labels()
        for name, labels in all_labels.items():
            normals[f"cluster_{name}"] = labels

        if best_key is not None:
            normals["cluster"] = all_labels[best_key]
        else:
            normals["cluster"] = 0

        profiler = ClusterProfiler()
        profile_summary = profiler.profile_summary(normals, feature_cols, "cluster")
        auto_labels = profiler.auto_label_clusters(normals, feature_cols, "cluster")
        normals["cluster_label"] = normals["cluster"].map(auto_labels).fillna("Unassigned")
        cluster_descriptions = {
            int(cluster_id): profiler.describe_cluster(normals, int(cluster_id), feature_cols, "cluster")
            for cluster_id in sorted(c for c in normals["cluster"].unique() if c >= 0)
        }

        save_dataframe(normals, PROCESSED_DIR / "climate_normals_clustered.parquet", "clustered climate normals")
        save_dataframe(comparison_df, TABLES_DIR / "algorithm_comparison.parquet", "algorithm comparison")
        save_dataframe(profile_summary.reset_index(), TABLES_DIR / "cluster_profiles.parquet", "cluster profiles")
        save_dataframe(elbow_results, TABLES_DIR / "optimization_elbow.parquet", "elbow optimization")
        save_dataframe(bic_results, TABLES_DIR / "optimization_bic.parquet", "gmm bic optimization")
        save_json(
            {
                "best_algorithm": best_algorithm,
                "best_key": best_key,
                "feature_cols": feature_cols,
                "auto_labels": {str(k): v for k, v in auto_labels.items()},
                "cluster_descriptions": {str(k): v for k, v in cluster_descriptions.items()},
            },
            MODELS_DIR / "prediction_metadata.json",
            "prediction metadata",
        )

        for name, clusterer in results.items():
            clusterer.save(MODELS_DIR / f"{name}_model.pkl")

        with open(MODELS_DIR / "scaler.pkl", "wb") as handle:
            pickle.dump(scaler, handle)
        with open(MODELS_DIR / "pca_reducer.pkl", "wb") as handle:
            pickle.dump(reducer, handle)

        return {
            "normals": normals,
            "comparison": comparison_df,
            "profiles": profile_summary,
            "auto_labels": auto_labels,
            "descriptions": cluster_descriptions,
            "optimal_k": optimal_k,
            "best_algorithm": best_algorithm,
            "best_key": best_key,
            "reducer": reducer,
            "results": results,
        }


if __name__ == "__main__":
    run_clustering()
