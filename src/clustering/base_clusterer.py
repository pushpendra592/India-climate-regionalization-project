"""
Abstract base class for all clustering algorithms.
Ensures consistent interface across K-Means, DBSCAN, GMM, etc.
"""

from abc import ABC, abstractmethod
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger("clusterer")


class BaseClusterer(ABC):
    """
    Abstract base class for clustering algorithms.

    All clusterers must implement:
      - fit(X) → self
      - get_labels() → array
      - get_params() → dict

    Usage:
        clusterer = KMeansClusterer(n_clusters=8)
        clusterer.fit(X_scaled)
        labels = clusterer.get_labels()
    """

    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}
        self.model = None
        self.labels_ = None
        self.X_ = None
        self.n_clusters_ = None
        self.fit_time_ = None

    @abstractmethod
    def fit(self, X: np.ndarray) -> 'BaseClusterer':
        """Fit the clustering model to data."""
        pass

    def get_labels(self) -> np.ndarray:
        """Return cluster labels."""
        if self.labels_ is None:
            raise ValueError("Model not fitted yet. Call fit() first.")
        return self.labels_

    @abstractmethod
    def get_params(self) -> dict:
        """Return model parameters."""
        pass

    def get_n_clusters(self) -> int:
        """Return number of clusters found."""
        if self.labels_ is None:
            return 0
        unique = np.unique(self.labels_)
        # Exclude noise label (-1) for DBSCAN
        return len([l for l in unique if l >= 0])

    def get_cluster_sizes(self) -> dict:
        """Return size of each cluster."""
        if self.labels_ is None:
            return {}
        unique, counts = np.unique(self.labels_, return_counts=True)
        return {int(k): int(v) for k, v in zip(unique, counts)}

    def save(self, path: Path):
        """Save the fitted model."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"💾 Saved {self.name} model: {path}")

    @staticmethod
    def load(path: Path) -> 'BaseClusterer':
        """Load a saved model."""
        with open(path, "rb") as f:
            return pickle.load(f)

    def summary(self) -> dict:
        """Return a summary of the clustering result."""
        return {
            "algorithm": self.name,
            "params": self.get_params(),
            "n_clusters": self.get_n_clusters(),
            "cluster_sizes": self.get_cluster_sizes(),
            "n_samples": len(self.labels_) if self.labels_ is not None else 0,
            "fit_time": self.fit_time_,
        }

    def __repr__(self):
        return f"{self.name}(n_clusters={self.get_n_clusters()}, params={self.params})"