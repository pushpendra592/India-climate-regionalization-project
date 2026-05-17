"""
HDBSCAN clustering.
Best for: Varying density clusters, automatic cluster count.
"""

import time
import numpy as np

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

from src.clustering.base_clusterer import BaseClusterer
from src.utils.logger import get_logger

logger = get_logger("hdbscan")


class HDBSCANClusterer(BaseClusterer):
    """
    HDBSCAN — Hierarchical DBSCAN.

    Advantages over DBSCAN:
      - Auto-selects number of clusters
      - Handles varying density clusters
      - Provides cluster membership probabilities

    Usage:
        hdb = HDBSCANClusterer(min_cluster_size=10)
        hdb.fit(X_scaled)
    """

    def __init__(
        self,
        min_cluster_size: int = 10,
        min_samples: int = None,
        metric: str = "euclidean",
        cluster_selection_method: str = "eom",
    ):
        if not HDBSCAN_AVAILABLE:
            raise ImportError("hdbscan not installed. Run: pip install hdbscan")

        super().__init__(
            name=f"HDBSCAN(min_size={min_cluster_size})",
            params={
                "min_cluster_size": min_cluster_size,
                "min_samples": min_samples,
                "metric": metric,
                "cluster_selection_method": cluster_selection_method,
            },
        )
        self.model = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_method=cluster_selection_method,
        )

    def fit(self, X: np.ndarray) -> 'HDBSCANClusterer':
        logger.info(
            f"🟣 Fitting HDBSCAN (min_cluster_size={self.params['min_cluster_size']})..."
        )

        start = time.time()
        self.model.fit(X)
        self.fit_time_ = time.time() - start

        self.labels_ = self.model.labels_
        self.X_ = X

        n_clusters = self.get_n_clusters()
        n_noise = (self.labels_ == -1).sum()

        logger.info(
            f"✅ HDBSCAN done in {self.fit_time_:.2f}s | "
            f"Clusters: {n_clusters} | "
            f"Noise: {n_noise} ({n_noise/len(self.labels_)*100:.1f}%)"
        )

        return self

    def get_params(self) -> dict:
        return {
            **self.params,
            "n_noise": int((self.labels_ == -1).sum()) if self.labels_ is not None else None,
        }

    def get_probabilities(self) -> np.ndarray:
        """Return cluster membership probabilities."""
        return self.model.probabilities_

    def get_outlier_scores(self) -> np.ndarray:
        """Return outlier scores."""
        return self.model.outlier_scores_