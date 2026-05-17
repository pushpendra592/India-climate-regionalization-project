"""
Clustering evaluation metrics — all internal (no labels needed).
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    silhouette_score,
    silhouette_samples,
    calinski_harabasz_score,
    davies_bouldin_score,
)
from src.utils.logger import get_logger

logger = get_logger("evaluator")


class ClusterEvaluator:
    """
    Evaluates clustering quality using internal metrics.

    Metrics:
      - Silhouette Score:        Higher is better [-1, 1]
      - Calinski-Harabasz Index: Higher is better
      - Davies-Bouldin Index:    Lower is better
      - Cluster balance:         How evenly sized clusters are

    Usage:
        evaluator = ClusterEvaluator()
        scores = evaluator.evaluate(X_scaled, labels)
        evaluator.compare([km_result, db_result, gmm_result])
    """

    def evaluate(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        algorithm_name: str = "Unknown",
    ) -> dict:
        """
        Compute all evaluation metrics.

        Args:
            X: Scaled feature matrix
            labels: Cluster labels

        Returns:
            Dictionary of metric scores
        """
        # Filter out noise points (label == -1) for metrics
        valid_mask = labels >= 0
        X_valid = X[valid_mask]
        labels_valid = labels[valid_mask]

        n_clusters = len(np.unique(labels_valid))
        n_noise = (~valid_mask).sum()

        # Need at least 2 clusters for metrics
        if n_clusters < 2:
            logger.warning(f"⚠️  {algorithm_name}: Only {n_clusters} cluster(s). Cannot compute metrics.")
            return {
                "algorithm": algorithm_name,
                "n_clusters": n_clusters,
                "n_samples": len(labels),
                "n_noise": int(n_noise),
                "silhouette": None,
                "calinski_harabasz": None,
                "davies_bouldin": None,
            }

        # Compute metrics
        sil_score = silhouette_score(X_valid, labels_valid)
        ch_score = calinski_harabasz_score(X_valid, labels_valid)
        db_score = davies_bouldin_score(X_valid, labels_valid)

        # Cluster balance (coefficient of variation of cluster sizes)
        unique, counts = np.unique(labels_valid, return_counts=True)
        balance = 1 - (counts.std() / counts.mean()) if counts.mean() > 0 else 0

        scores = {
            "algorithm": algorithm_name,
            "n_clusters": n_clusters,
            "n_samples": len(labels),
            "n_noise": int(n_noise),
            "noise_pct": round(n_noise / len(labels) * 100, 1),
            "silhouette": round(sil_score, 4),
            "calinski_harabasz": round(ch_score, 2),
            "davies_bouldin": round(db_score, 4),
            "cluster_balance": round(balance, 4),
            "min_cluster_size": int(counts.min()),
            "max_cluster_size": int(counts.max()),
            "mean_cluster_size": round(counts.mean(), 1),
            "min_cluster_share": round(counts.min() / len(labels_valid), 4),
            "max_cluster_share": round(counts.max() / len(labels_valid), 4),
        }

        logger.info(
            f"📊 {algorithm_name}: Silhouette={sil_score:.4f} | "
            f"CH={ch_score:.1f} | DB={db_score:.4f} | "
            f"Clusters={n_clusters} | Noise={n_noise}"
        )

        return scores

    def silhouette_per_cluster(
        self, X: np.ndarray, labels: np.ndarray
    ) -> dict:
        """Get silhouette score per cluster (for visualization)."""
        valid_mask = labels >= 0
        X_valid = X[valid_mask]
        labels_valid = labels[valid_mask]

        if len(np.unique(labels_valid)) < 2:
            return {}

        sample_scores = silhouette_samples(X_valid, labels_valid)

        per_cluster = {}
        for label in np.unique(labels_valid):
            mask = labels_valid == label
            per_cluster[int(label)] = {
                "mean": round(sample_scores[mask].mean(), 4),
                "std": round(sample_scores[mask].std(), 4),
                "min": round(sample_scores[mask].min(), 4),
                "size": int(mask.sum()),
            }

        return per_cluster

    def compare(self, results: list) -> pd.DataFrame:
        """
        Compare multiple clustering results side by side.

        Args:
            results: List of dicts from evaluate()

        Returns:
            Comparison DataFrame sorted by silhouette score
        """
        df = pd.DataFrame(results)

        # Add composite score (weighted combination)
        if "silhouette" in df.columns:
            df["composite_score"] = (
                df["silhouette"].fillna(0) * 0.4
                + (1 / (df["davies_bouldin"].fillna(10) + 0.01)) * 0.3
                + df["cluster_balance"].fillna(0) * 0.3
            )

            df = df.sort_values("composite_score", ascending=False)

        logger.info(f"\n📊 Algorithm Comparison:\n{df.to_string(index=False)}")

        return df
