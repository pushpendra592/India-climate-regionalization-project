# map_plots.py

"""
Geographic map visualizations for cluster results.
"""

import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from config.settings import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger("map_plots")


class MapVisualizer:
    """
    Creates interactive maps showing cluster assignments on India geography.

    Usage:
        mapper = MapVisualizer()
        mapper.plot_cluster_map(df, "cluster")
        mapper.plot_feature_heatmap(df, "temperature_2m_mean")
    """

    INDIA_CENTER = [22.5, 79.0]
    DEFAULT_ZOOM = 5

    def __init__(self, save_dir=None):
        self.save_dir = save_dir or FIGURES_DIR

    def _get_color_map(self, n_clusters: int) -> list:
        """Generate distinct colors for clusters."""
        cmap = cm.get_cmap("tab20", n_clusters)
        colors = [mcolors.rgb2hex(cmap(i)) for i in range(n_clusters)]
        return colors

    def plot_cluster_map(
        self,
        df: pd.DataFrame,
        label_col: str = "cluster",
        title: str = "Weather Pattern Clusters — India",
        cluster_labels: dict = None,
    ) -> folium.Map:
        """Plot cluster assignments on interactive India map."""
        m = folium.Map(
            location=self.INDIA_CENTER,
            zoom_start=self.DEFAULT_ZOOM,
            tiles="CartoDB positron",
        )

        unique_clusters = sorted(df[label_col].unique())
        n_clusters = len([c for c in unique_clusters if c >= 0])
        colors = self._get_color_map(n_clusters)

        # Add points
        for _, row in df.iterrows():
            cluster = int(row[label_col])

            if cluster == -1:
                color = "gray"
                name = "Noise"
            else:
                color = colors[cluster % len(colors)]
                name = cluster_labels.get(cluster, f"Cluster {cluster}") if cluster_labels else f"Cluster {cluster}"

            popup_text = (
                f"<b>{name}</b><br>"
                f"Lat: {row['latitude']:.2f}<br>"
                f"Lon: {row['longitude']:.2f}<br>"
            )

            # Add key feature values if available
            for feat in ["temperature_2m_mean", "precipitation_sum", "wind_speed_10m_mean"]:
                if feat in row.index and pd.notna(row[feat]):
                    popup_text += f"{feat}: {row[feat]:.1f}<br>"

            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                popup=folium.Popup(popup_text, max_width=200),
                tooltip=name,
            ).add_to(m)

        # Add legend
        legend_html = f'<div style="position:fixed;bottom:50px;left:50px;z-index:1000;background:white;padding:10px;border-radius:5px;border:2px solid gray;">'
        legend_html += f'<b>{title}</b><br>'
        for i, cluster in enumerate(unique_clusters):
            if cluster == -1:
                color = "gray"
                name = "Noise"
            else:
                color = colors[cluster % len(colors)]
                name = cluster_labels.get(cluster, f"Cluster {cluster}") if cluster_labels else f"Cluster {cluster}"
            legend_html += f'<i style="background:{color};width:12px;height:12px;display:inline-block;border-radius:50%;"></i> {name}<br>'
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))

        # Save
        path = self.save_dir / "cluster_map.html"
        m.save(str(path))
        logger.info(f"🗺️  Saved cluster map: {path.name}")

        return m

    def plot_feature_heatmap(
        self,
        df: pd.DataFrame,
        feature: str,
        title: str = None,
    ) -> folium.Map:
        """Plot a weather feature as a heatmap on India map."""
        m = folium.Map(
            location=self.INDIA_CENTER,
            zoom_start=self.DEFAULT_ZOOM,
            tiles="CartoDB dark_matter",
        )

        # Prepare heatmap data
        heat_data = df[["latitude", "longitude", feature]].dropna()

        # Normalize feature values to 0-1
        vmin = heat_data[feature].min()
        vmax = heat_data[feature].max()
        heat_data["normalized"] = (heat_data[feature] - vmin) / (vmax - vmin + 1e-8)

        heat_points = heat_data[["latitude", "longitude", "normalized"]].values.tolist()

        HeatMap(
            heat_points,
            min_opacity=0.4,
            max_zoom=10,
            radius=15,
            blur=10,
        ).add_to(m)

        title = title or f"{feature} Heatmap"
        path = self.save_dir / f"heatmap_{feature}.html"
        m.save(str(path))
        logger.info(f"🗺️  Saved heatmap: {path.name}")

        return m

    def plot_multi_feature_maps(
        self,
        df: pd.DataFrame,
        features: list,
    ) -> dict:
        """Create heatmaps for multiple features."""
        maps = {}
        for feat in features:
            if feat in df.columns:
                maps[feat] = self.plot_feature_heatmap(df, feat)
        return maps