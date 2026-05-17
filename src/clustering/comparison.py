"""
Compare all clustering algorithms side by side.
"""

import numpy as np
import pandas as pd
from src.clustering.kmeans_clusterer import KMeansClusterer
from src.clustering.dbscan_clusterer import DBSCANClusterer
from src.clustering.hdbscan_clusterer import HDBSCANClusterer
from src.clustering.hierarchical_clusterer import HierarchicalClusterer
from src.clustering.gmm_clusterer import GMMClusterer
from src.clustering.evaluator import ClusterEvaluator
from src.clustering.optimizer import ClusterOptimizer
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("comparison")


class ClusterComparison:
    """Run multiple clustering algorithms and compare their scores."""

    def __init__(self, X: np.ndarray):
        self.X = X
        self.evaluator = ClusterEvaluator()
        self.results = {}
        self.scores = []
        self.algorithm_key_map = {}

    def _store_score(self, key: str, labels: np.ndarray, algorithm_name: str):
        score = self.evaluator.evaluate(self.X, labels, algorithm_name)
        self.scores.append(score)
        self.algorithm_key_map[score["algorithm"]] = key

    def run_all(
        self,
        optimal_k: int = 8,
        candidate_ks: list[int] | None = None,
        dbscan_eps: float = None,
        dbscan_min_samples: int = 5,
        hdbscan_min_cluster_size: int = 10,
    ) -> dict:
        with Timer("Running all clustering algorithms"):
            ks = candidate_ks or [optimal_k]
            ks = sorted({k for k in ks if 2 <= k < len(self.X)})

            for idx, k in enumerate(ks):
                km_key = "kmeans" if idx == 0 else f"kmeans_k{k}"
                km_name = "K-Means" if idx == 0 else f"K-Means(k={k})"
                km = KMeansClusterer(n_clusters=k).fit(self.X)
                self.results[km_key] = km
                self._store_score(km_key, km.get_labels(), km_name)

            for idx, k in enumerate(ks):
                ward_key = "hierarchical_ward" if idx == 0 else f"hierarchical_ward_k{k}"
                ward_name = "Hierarchical(Ward)" if idx == 0 else f"Hierarchical(Ward, k={k})"
                hc_ward = HierarchicalClusterer(n_clusters=k, linkage_method="ward").fit(self.X)
                self.results[ward_key] = hc_ward
                self._store_score(ward_key, hc_ward.get_labels(), ward_name)

                avg_key = "hierarchical_avg" if idx == 0 else f"hierarchical_avg_k{k}"
                avg_name = "Hierarchical(Average)" if idx == 0 else f"Hierarchical(Average, k={k})"
                hc_avg = HierarchicalClusterer(n_clusters=k, linkage_method="average").fit(self.X)
                self.results[avg_key] = hc_avg
                self._store_score(avg_key, hc_avg.get_labels(), avg_name)

            if dbscan_eps is None:
                dbscan_eps = float(np.median(ClusterOptimizer().estimate_dbscan_eps(self.X)))
                logger.info(f"Auto eps: {dbscan_eps:.4f}")

            dbscan = DBSCANClusterer(eps=dbscan_eps, min_samples=dbscan_min_samples).fit(self.X)
            self.results["dbscan"] = dbscan
            self._store_score("dbscan", dbscan.get_labels(), "DBSCAN")

            try:
                hdbscan = HDBSCANClusterer(min_cluster_size=hdbscan_min_cluster_size).fit(self.X)
                self.results["hdbscan"] = hdbscan
                self._store_score("hdbscan", hdbscan.get_labels(), "HDBSCAN")
            except ImportError:
                logger.warning("HDBSCAN not available; skipping")

            for idx, k in enumerate(ks):
                gmm_key = "gmm" if idx == 0 else f"gmm_k{k}"
                gmm_name = "GMM" if idx == 0 else f"GMM(k={k})"
                gmm = GMMClusterer(n_components=k).fit(self.X)
                self.results[gmm_key] = gmm
                self._store_score(gmm_key, gmm.get_labels(), gmm_name)

        return self.results

    def get_comparison(self) -> pd.DataFrame:
        return self.evaluator.compare(self.scores)

    def get_best_algorithm(self) -> str:
        comparison = self.get_comparison()
        if len(comparison) == 0:
            return "None"
        return comparison.iloc[0]["algorithm"]

    def get_result(self, name: str):
        return self.results.get(name)

    def get_all_labels(self) -> dict:
        return {name: clusterer.get_labels() for name, clusterer in self.results.items()}

    def get_key_for_algorithm(self, algorithm_name: str):
        return self.algorithm_key_map.get(algorithm_name)
