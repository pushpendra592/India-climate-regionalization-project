"""
K-Means and K-Means++ clustering.
Best for: Spherical, well-separated clusters.
"""

import time
import numpy as np
from sklearn.cluster import KMeans
from src.clustering.base_clusterer import BaseClusterer
from src.utils.logger import get_logger

logger = get_logger("kmeans")


class KMeansClusterer(BaseClusterer):
    """
    K-Means clustering with K-Means++ initialization.

    Usage:
        km = KMeansClusterer(n_clusters=8)
        km.fit(X_scaled)
        labels = km.get_labels()
    """

    def __init__(
        self,
        n_clusters: int = 8,
        init: str = "k-means++",
        n_init: int = 10,
        max_iter: int = 300,
        random_state: int = 42,
    ):
        super().__init__(
            name=f"KMeans(k={n_clusters})",
            params={
                "n_clusters": n_clusters,
                "init": init,
                "n_init": n_init,
                "max_iter": max_iter,
                "random_state": random_state,
            },
        )
        self.model = KMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray) -> 'KMeansClusterer':
        logger.info(f"🔵 Fitting K-Means (k={self.params['n_clusters']})...")

        start = time.time()
        self.model.fit(X)
        self.fit_time_ = time.time() - start

        self.labels_ = self.model.labels_
        self.X_ = X
        self.n_clusters_ = self.params["n_clusters"]

        logger.info(
            f"✅ K-Means done in {self.fit_time_:.2f}s | "
            f"Inertia: {self.model.inertia_:.2f} | "
            f"Iterations: {self.model.n_iter_}"
        )

        return self

    def get_params(self) -> dict:
        return {
            **self.params,
            "inertia": self.model.inertia_ if hasattr(self.model, "inertia_") else None,
            "n_iter": self.model.n_iter_ if hasattr(self.model, "n_iter_") else None,
        }

    def get_centroids(self) -> np.ndarray:
        """Return cluster centroids."""
        return self.model.cluster_centers_

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        """Predict cluster for new data."""
        return self.model.predict(X_new)