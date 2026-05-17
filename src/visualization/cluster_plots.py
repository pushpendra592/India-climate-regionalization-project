"""
Visualization functions for clustering results.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from sklearn.decomposition import PCA
from config.settings import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger("cluster_plots")


class ClusterVisualizer:
    """
    Creates all clustering-related visualizations.

    Usage:
        viz = ClusterVisualizer()
        viz.plot_elbow(elbow_results)
        viz.plot_silhouette(X, labels)
        viz.plot_clusters_2d(X, labels)
        viz.plot_comparison(comparison_df)
    """

    def __init__(self, save_dir=None, style="seaborn-v0_8-whitegrid"):
        self.save_dir = save_dir or FIGURES_DIR
        try:
            plt.style.use(style)
        except Exception:
            plt.style.use("seaborn-v0_8")

    def _save_fig(self, fig, name: str):
        path = self.save_dir / f"{name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        logger.info(f"💾 Saved: {path.name}")

    def plot_elbow(self, results: pd.DataFrame):
        """Plot elbow curve (inertia vs K)."""
        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.plot(results["k"], results["inertia"], "bo-", linewidth=2, markersize=8)
        ax1.set_xlabel("Number of Clusters (K)", fontsize=12)
        ax1.set_ylabel("Inertia", fontsize=12, color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")

        if "silhouette" in results.columns:
            ax2 = ax1.twinx()
            ax2.plot(results["k"], results["silhouette"], "rs-", linewidth=2, markersize=8)
            ax2.set_ylabel("Silhouette Score", fontsize=12, color="red")
            ax2.tick_params(axis="y", labelcolor="red")

        plt.title("Elbow Method + Silhouette Score", fontsize=14, fontweight="bold")
        ax1.grid(True, alpha=0.3)
        fig.tight_layout()

        self._save_fig(fig, "elbow_silhouette")
        plt.show()

    def plot_silhouette_analysis(self, X: np.ndarray, labels: np.ndarray, title: str = ""):
        """Plot silhouette diagram per cluster."""
        from sklearn.metrics import silhouette_samples

        valid_mask = labels >= 0
        X_valid = X[valid_mask]
        labels_valid = labels[valid_mask]
        n_clusters = len(np.unique(labels_valid))

        sample_scores = silhouette_samples(X_valid, labels_valid)

        fig, ax = plt.subplots(figsize=(10, max(6, n_clusters * 0.8)))

        y_lower = 10
        colors = cm.nipy_spectral(np.linspace(0, 1, n_clusters))

        for i, label in enumerate(sorted(np.unique(labels_valid))):
            cluster_scores = sample_scores[labels_valid == label]
            cluster_scores.sort()

            size = len(cluster_scores)
            y_upper = y_lower + size

            ax.fill_betweenx(
                np.arange(y_lower, y_upper),
                0,
                cluster_scores,
                facecolor=colors[i],
                edgecolor=colors[i],
                alpha=0.7,
            )
            ax.text(-0.05, y_lower + 0.5 * size, str(label))
            y_lower = y_upper + 10

        avg_score = sample_scores.mean()
        ax.axvline(x=avg_score, color="red", linestyle="--", label=f"Avg: {avg_score:.3f}")

        ax.set_xlabel("Silhouette Score")
        ax.set_ylabel("Cluster")
        ax.set_title(f"Silhouette Analysis {title}", fontsize=14, fontweight="bold")
        ax.legend()

        self._save_fig(fig, f"silhouette_{title.replace(' ', '_').lower()}")
        plt.show()

    def plot_clusters_2d(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        title: str = "",
        feature_names: list = None,
    ):
        """Plot clusters in 2D using PCA."""
        pca = PCA(n_components=2)
        X_2d = pca.fit_transform(X)

        fig, ax = plt.subplots(figsize=(12, 8))

        unique_labels = np.unique(labels)
        colors = cm.nipy_spectral(np.linspace(0, 1, len(unique_labels)))

        for label, color in zip(unique_labels, colors):
            mask = labels == label
            name = "Noise" if label == -1 else f"Cluster {label}"
            alpha = 0.3 if label == -1 else 0.7
            marker = "x" if label == -1 else "o"

            ax.scatter(
                X_2d[mask, 0],
                X_2d[mask, 1],
                c=[color],
                label=name,
                alpha=alpha,
                marker=marker,
                s=30,
            )

        var_explained = pca.explained_variance_ratio_
        ax.set_xlabel(f"PC1 ({var_explained[0]*100:.1f}%)", fontsize=12)
        ax.set_ylabel(f"PC2 ({var_explained[1]*100:.1f}%)", fontsize=12)
        ax.set_title(f"Cluster Visualization (PCA) {title}", fontsize=14, fontweight="bold")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        self._save_fig(fig, f"clusters_2d_{title.replace(' ', '_').lower()}")
        plt.show()

    def plot_comparison(self, comparison_df: pd.DataFrame):
        """Plot algorithm comparison chart."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        metrics = [
            ("silhouette", "Silhouette Score (higher=better)", "Greens_d"),
            ("davies_bouldin", "Davies-Bouldin (lower=better)", "Reds_d"),
            ("cluster_balance", "Cluster Balance (higher=better)", "Blues_d"),
        ]

        for ax, (col, title, cmap) in zip(axes, metrics):
            data = comparison_df[comparison_df[col].notna()]
            if len(data) == 0:
                continue

            bars = ax.barh(data["algorithm"], data[col], color=sns.color_palette(cmap, len(data)))
            ax.set_title(title, fontsize=11, fontweight="bold")
            ax.grid(True, alpha=0.3, axis="x")

            for bar, val in zip(bars, data[col]):
                ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                        f"  {val:.3f}", va="center", fontsize=9)

        fig.suptitle("Clustering Algorithm Comparison", fontsize=14, fontweight="bold")
        fig.tight_layout()
        self._save_fig(fig, "algorithm_comparison")
        plt.show()

    def plot_radar_profile(
        self,
        profiles: pd.DataFrame,
        feature_cols: list,
        cluster_labels: dict = None,
    ):
        """Radar chart showing cluster profiles."""
        from math import pi

        n_clusters = len(profiles)
        n_features = len(feature_cols)

        # Normalize features to 0-1 range
        normalized = profiles[feature_cols].copy()
        for col in feature_cols:
            col_min = normalized[col].min()
            col_max = normalized[col].max()
            if col_max > col_min:
                normalized[col] = (normalized[col] - col_min) / (col_max - col_min)

        # Create angles
        angles = [n / float(n_features) * 2 * pi for n in range(n_features)]
        angles += angles[:1]  # Complete the circle

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        colors = cm.nipy_spectral(np.linspace(0, 1, n_clusters))

        for idx, (cluster_id, row) in enumerate(normalized.iterrows()):
            values = row[feature_cols].values.tolist()
            values += values[:1]

            label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}") if cluster_labels else f"Cluster {cluster_id}"
            ax.plot(angles, values, "o-", linewidth=2, label=label, color=colors[idx])
            ax.fill(angles, values, alpha=0.1, color=colors[idx])

        # Clean feature names for display
        clean_names = [f.replace("_mean", "").replace("_sum", "").replace("_", " ").title()
                       for f in feature_cols]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(clean_names, size=8)
        ax.set_title("Cluster Profiles", size=14, fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

        fig.tight_layout()
        self._save_fig(fig, "radar_profiles")
        plt.show()