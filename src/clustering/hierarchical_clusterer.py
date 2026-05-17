"""
Agglomerative (Hierarchical) clustering.
Best for: Understanding cluster hierarchy, dendrogram visualization.
"""

import time
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, fcluster
from src.clustering.base_clusterer import BaseClusterer
from src.utils.logger import get_logger

logger = get_logger("hierarchical")


class HierarchicalClusterer(BaseClusterer):
    """
    Agglomerative Hierarchical Clustering.

    Creates a hierarchy of clusters (dendrogram) and cuts at desired level.

    Usage:
        hc = HierarchicalClusterer(n_clusters=8)
        hc.fit(X_scaled)
        # Or explore dendrogram:
        hc.fit_linkage(X_scaled)
        hc.cut_tree(n_clusters=10)
    """

    def __init__(
        self,
        n_clusters: int = 8,
        linkage_method: str = "ward",
        metric: str = "euclidean",
    ):
        super().__init__(
            name=f"Hierarchical({linkage_method}, k={n_clusters})",
            params={
                "n_clusters": n_clusters,
                "linkage": linkage_method,
                "metric": metric,
            },
        )
        self.linkage_method = linkage_method
        self.linkage_matrix_ = None

        self.model = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage=linkage_method,
        )

    def fit(self, X: np.ndarray) -> 'HierarchicalClusterer':
        logger.info(
            f"🟠 Fitting Hierarchical ({self.linkage_method}, "
            f"k={self.params['n_clusters']})..."
        )

        start = time.time()
        self.model.fit(X)
        self.fit_time_ = time.time() - start

        self.labels_ = self.model.labels_
        self.X_ = X

        logger.info(
            f"✅ Hierarchical done in {self.fit_time_:.2f}s | "
            f"Clusters: {self.get_n_clusters()}"
        )

        return self

    def fit_linkage(self, X: np.ndarray) -> np.ndarray:
        """
        Compute full linkage matrix for dendrogram visualization.
        Use this when you want to explore different cuts.
        """
        logger.info(f"🌳 Computing linkage matrix ({self.linkage_method})...")

        start = time.time()
        self.linkage_matrix_ = linkage(X, method=self.linkage_method)
        self.X_ = X
        elapsed = time.time() - start

        logger.info(f"✅ Linkage computed in {elapsed:.2f}s")

        return self.linkage_matrix_

    def cut_tree(self, n_clusters: int) -> np.ndarray:
        """Cut dendrogram at specified number of clusters."""
        if self.linkage_matrix_ is None:
            raise ValueError("Call fit_linkage() first.")

        self.labels_ = fcluster(self.linkage_matrix_, n_clusters, criterion="maxclust") - 1
        self.n_clusters_ = n_clusters
        self.params["n_clusters"] = n_clusters

        logger.info(f"✂️  Cut tree at k={n_clusters}")
        return self.labels_

    def get_linkage_matrix(self) -> np.ndarray:
        """Return linkage matrix for dendrogram plotting."""
        return self.linkage_matrix_

    def get_params(self) -> dict:
        return self.params