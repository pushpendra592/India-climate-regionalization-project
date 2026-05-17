"""
Gaussian Mixture Model clustering.
Best for: Soft clustering with probabilities, elliptical clusters.
"""

import time
import numpy as np
from sklearn.mixture import GaussianMixture
from src.clustering.base_clusterer import BaseClusterer
from src.utils.logger import get_logger

logger = get_logger("gmm")


class GMMClusterer(BaseClusterer):
    """
    Gaussian Mixture Model — soft/probabilistic clustering.

    Key advantage: Each point gets PROBABILITY of belonging to each cluster.
    Great for climate transition zones.

    Usage:
        gmm = GMMClusterer(n_components=8)
        gmm.fit(X_scaled)
        probs = gmm.get_probabilities()
    """

    def __init__(
        self,
        n_components: int = 8,
        covariance_type: str = "full",
        max_iter: int = 200,
        n_init: int = 5,
        random_state: int = 42,
    ):
        super().__init__(
            name=f"GMM(k={n_components}, cov={covariance_type})",
            params={
                "n_components": n_components,
                "covariance_type": covariance_type,
                "max_iter": max_iter,
                "n_init": n_init,
                "random_state": random_state,
            },
        )
        self.model = GaussianMixture(
            n_components=n_components,
            covariance_type=covariance_type,
            max_iter=max_iter,
            n_init=n_init,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray) -> 'GMMClusterer':
        logger.info(f"🔴 Fitting GMM (k={self.params['n_components']})...")

        start = time.time()
        self.model.fit(X)
        self.fit_time_ = time.time() - start

        self.labels_ = self.model.predict(X)
        self.X_ = X

        logger.info(
            f"✅ GMM done in {self.fit_time_:.2f}s | "
            f"Clusters: {self.get_n_clusters()} | "
            f"BIC: {self.model.bic(X):.2f} | "
            f"AIC: {self.model.aic(X):.2f} | "
            f"Converged: {self.model.converged_}"
        )

        return self

    def get_params(self) -> dict:
        return {
            **self.params,
            "bic": self.model.bic(self.X_) if self.X_ is not None else None,
            "aic": self.model.aic(self.X_) if self.X_ is not None else None,
            "converged": self.model.converged_ if hasattr(self.model, "converged_") else None,
        }

    def get_probabilities(self) -> np.ndarray:
        """Return probability of each point belonging to each cluster."""
        return self.model.predict_proba(self.X_)

    def get_uncertainty(self) -> np.ndarray:
        """
        Return clustering uncertainty for each point.
        High uncertainty = point is in a transition zone between clusters.
        """
        probs = self.get_probabilities()
        sorted_probs = np.sort(probs, axis=1)[:, ::-1]
        # Uncertainty = 1 - (highest_prob - second_highest_prob)
        uncertainty = 1 - (sorted_probs[:, 0] - sorted_probs[:, 1])
        return uncertainty

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        """Predict clusters for new data."""
        return self.model.predict(X_new)

    def score(self, X: np.ndarray) -> float:
        """Return log-likelihood score."""
        return self.model.score(X)