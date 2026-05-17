"""
DBSCAN clustering.
Best for: Arbitrary shapes, noise detection, no need to specify K.
"""

import time
import numpy as np
from sklearn.cluster import DBSCAN
from src.clustering.base_clusterer import BaseClusterer
from src.utils.logger import get_logger

logger = get_logger("dbscan")


class DBSCANClusterer(BaseClusterer):
    """
    DBSCAN — Density-Based Spatial Clustering of Applications with Noise.

    Key advantage: Finds arbitrarily shaped clusters and identifies outliers.
    Key challenge: eps and min_samples are sensitive to data scale.

    Usage:
        db = DBSCANClusterer(eps=0.5, min_samples=5)
        db.fit(X_scaled)
    """

    def __init__(
        self,
        eps: float = 0.5,
        min_samples: int = 5,
        metric: str = "euclidean",
    ):
        super().__init__(
            name=f"DBSCAN(eps={eps}, min={min_samples})",
            params={
                "eps": eps,
                "min_samples": min_samples,
                "metric": metric,
            },
        )
        self.model = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric=metric,
        )

    def fit(self, X: np.ndarray) -> 'DBSCANClusterer':
        logger.info(
            f"🟢 Fitting DBSCAN (eps={self.params['eps']}, "
            f"min_samples={self.params['min_samples']})..."
        )

        start = time.time()
        self.model.fit(X)
        self.fit_time_ = time.time() - start

        self.labels_ = self.model.labels_
        self.X_ = X

        n_clusters = self.get_n_clusters()
        n_noise = (self.labels_ == -1).sum()
        noise_pct = n_noise / len(self.labels_) * 100

        logger.info(
            f"✅ DBSCAN done in {self.fit_time_:.2f}s | "
            f"Clusters: {n_clusters} | "
            f"Noise points: {n_noise} ({noise_pct:.1f}%)"
        )

        if noise_pct > 30:
            logger.warning(f"⚠️  High noise ({noise_pct:.1f}%) — consider increasing eps")

        return self

    def get_params(self) -> dict:
        return {
            **self.params,
            "n_noise": int((self.labels_ == -1).sum()) if self.labels_ is not None else None,
        }

    def get_core_sample_indices(self) -> np.ndarray:
        """Return indices of core samples."""
        return self.model.core_sample_indices_