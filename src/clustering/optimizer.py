"""
Hyperparameter optimization for clustering algorithms.
Elbow method, silhouette analysis, BIC/AIC for GMM.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors
from config.settings import K_RANGE, RANDOM_STATE
from src.utils.logger import get_logger
from src.utils.timer import Timer

logger = get_logger("optimizer")


class ClusterOptimizer:
    """
    Find optimal clustering parameters.

    Methods:
      - Elbow method (K-Means inertia)
      - Silhouette analysis (K-Means, GMM)
      - BIC/AIC curves (GMM)
      - Epsilon estimation (DBSCAN)

    Usage:
        optimizer = ClusterOptimizer()
        results = optimizer.elbow_method(X)
        optimal_k = optimizer.find_optimal_k(X)
    """

    def __init__(self, k_range: range = None, random_state: int = RANDOM_STATE):
        self.k_range = k_range or K_RANGE
        self.random_state = random_state

    def elbow_method(self, X: np.ndarray) -> pd.DataFrame:
        """
        Run elbow method — plot inertia vs K.
        """
        with Timer("Elbow method"):
            results = []

            valid_k_values = [k for k in self.k_range if 2 <= k < len(X)]

            for k in valid_k_values:
                km = KMeans(
                    n_clusters=k,
                    init="k-means++",
                    n_init=10,
                    random_state=self.random_state,
                )
                km.fit(X)

                results.append({
                    "k": k,
                    "inertia": km.inertia_,
                    "n_iter": km.n_iter_,
                })

                logger.info(f"   K={k}: inertia={km.inertia_:.2f}")

            df = pd.DataFrame(results)

            # Calculate rate of change (for automatic elbow detection)
            df["inertia_diff"] = df["inertia"].diff()
            df["inertia_diff2"] = df["inertia_diff"].diff()

        return df

    def silhouette_analysis(self, X: np.ndarray) -> pd.DataFrame:
        """
        Run silhouette analysis for range of K values.
        """
        with Timer("Silhouette analysis"):
            results = []

            valid_k_values = [k for k in self.k_range if 2 <= k < len(X)]

            for k in valid_k_values:
                km = KMeans(
                    n_clusters=k,
                    init="k-means++",
                    n_init=10,
                    random_state=self.random_state,
                )
                labels = km.fit_predict(X)

                sil = silhouette_score(X, labels)

                results.append({
                    "k": k,
                    "silhouette": sil,
                    "inertia": km.inertia_,
                })

                logger.info(f"   K={k}: silhouette={sil:.4f}")

            df = pd.DataFrame(results)

        return df

    def gmm_bic_aic(self, X: np.ndarray) -> pd.DataFrame:
        """
        Compute BIC and AIC for range of GMM components.
        Lower BIC = better model.
        """
        with Timer("GMM BIC/AIC analysis"):
            results = []

            valid_k_values = [k for k in self.k_range if 1 <= k <= len(X)]

            for k in valid_k_values:
                gmm = GaussianMixture(
                    n_components=k,
                    covariance_type="full",
                    n_init=3,
                    random_state=self.random_state,
                )
                gmm.fit(X)

                results.append({
                    "k": k,
                    "bic": gmm.bic(X),
                    "aic": gmm.aic(X),
                    "converged": gmm.converged_,
                })

                logger.info(f"   K={k}: BIC={gmm.bic(X):.1f}, AIC={gmm.aic(X):.1f}")

            df = pd.DataFrame(results)

        return df

    def estimate_dbscan_eps(self, X: np.ndarray, k: int = 5) -> np.ndarray:
        """
        Estimate DBSCAN eps using k-nearest neighbor distance.
        Plot the sorted distances — the "knee" is a good eps value.
        """
        with Timer(f"DBSCAN eps estimation (k={k})"):
            if len(X) < 2:
                raise ValueError("Need at least 2 samples to estimate DBSCAN epsilon.")

            k = max(1, min(k, len(X)))
            nn = NearestNeighbors(n_neighbors=k)
            nn.fit(X)
            distances, _ = nn.kneighbors(X)

            # Sort the k-th nearest neighbor distances
            k_distances = np.sort(distances[:, k - 1])

            logger.info(
                f"   Distance stats: "
                f"min={k_distances.min():.4f}, "
                f"median={np.median(k_distances):.4f}, "
                f"max={k_distances.max():.4f}"
            )

        return k_distances

    def find_optimal_k(self, X: np.ndarray, method: str = "silhouette") -> int:
        """
        Automatically find the optimal number of clusters.

        Args:
            method: "silhouette" or "elbow" or "bic"

        Returns:
            Optimal K value
        """
        if method == "silhouette":
            results = self.silhouette_analysis(X)
            if results.empty:
                raise ValueError("Not enough samples for silhouette-based K selection.")
            optimal_k = results.loc[results["silhouette"].idxmax(), "k"]

        elif method == "elbow":
            results = self.elbow_method(X)
            if results.empty:
                raise ValueError("Not enough samples for elbow-based K selection.")
            # Find max second derivative (elbow point)
            optimal_k = results.loc[results["inertia_diff2"].idxmax(), "k"]

        elif method == "bic":
            results = self.gmm_bic_aic(X)
            if results.empty:
                raise ValueError("Not enough samples for BIC-based K selection.")
            optimal_k = results.loc[results["bic"].idxmin(), "k"]

        else:
            raise ValueError(f"Unknown method: {method}")

        logger.info(f"🎯 Optimal K ({method}): {optimal_k}")
        return int(optimal_k)
