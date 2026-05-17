"""
Point-graph visualization of clustered climate locations in PCA space.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.settings import MODELS_DIR
from dashboard.components.map_widget import get_cluster_color
from src.utils.io_helpers import load_pickle


@st.cache_resource(show_spinner=False)
def _load_projection_models():
    scaler = load_pickle(MODELS_DIR / "scaler.pkl")
    reducer = load_pickle(MODELS_DIR / "pca_reducer.pkl")
    return scaler, reducer


@st.cache_data(show_spinner=False)
def _build_projection(clustered_df: pd.DataFrame) -> tuple[pd.DataFrame, list[float]]:
    projected_df = clustered_df.copy()

    if {"pc1", "pc2", "pc3"}.issubset(projected_df.columns):
        explained = []
        return projected_df, explained

    scaler, reducer = _load_projection_models()
    feature_cols = scaler.get_feature_names()

    feature_frame = projected_df[feature_cols].copy()
    training_medians = feature_frame.median(numeric_only=True)
    feature_frame = feature_frame.fillna(training_medians).fillna(0)

    x_scaled = scaler.transform(feature_frame)
    x_reduced = reducer.transform(x_scaled)

    for idx in range(x_reduced.shape[1]):
        projected_df[f"pc{idx + 1}"] = x_reduced[:, idx]

    explained = []
    if hasattr(reducer, "get_explained_variance"):
        explained = list(reducer.get_explained_variance() * 100)

    return projected_df, explained


def _ellipse_trace(
    subset: pd.DataFrame,
    x_col: str,
    y_col: str,
    color: str,
    label: str,
) -> go.Scatter | None:
    if len(subset) < 3:
        return None

    coords = subset[[x_col, y_col]].dropna().to_numpy()
    if len(coords) < 3:
        return None

    covariance = np.cov(coords, rowvar=False)
    if covariance.shape != (2, 2) or np.linalg.det(covariance) <= 0:
        return None

    values, vectors = np.linalg.eigh(covariance)
    order = values.argsort()[::-1]
    values = values[order]
    vectors = vectors[:, order]

    theta = np.linspace(0, 2 * np.pi, 120)
    circle = np.stack([np.cos(theta), np.sin(theta)])
    radii = 1.8 * np.sqrt(np.maximum(values, 1e-9))
    ellipse = vectors @ np.diag(radii) @ circle
    center = coords.mean(axis=0).reshape(2, 1)
    outline = ellipse + center

    return go.Scatter(
        x=outline[0],
        y=outline[1],
        mode="lines",
        name=f"{label} boundary",
        line={"color": color, "width": 2, "dash": "dot"},
        opacity=0.55,
        hoverinfo="skip",
        showlegend=False,
    )


def render_cluster_scatter(
    clustered_df: pd.DataFrame,
    prediction: dict | None = None,
    axis_pair: str = "PC1 vs PC2",
):
    projected_df, explained = _build_projection(clustered_df)
    fig = go.Figure()
    axis_map = {
        "PC1 vs PC2": ("pc1", "pc2", 0, 1),
        "PC1 vs PC3": ("pc1", "pc3", 0, 2),
        "PC2 vs PC3": ("pc2", "pc3", 1, 2),
    }
    x_col, y_col, x_idx, y_idx = axis_map.get(axis_pair, ("pc1", "pc2", 0, 1))

    cluster_ids = sorted(projected_df["cluster"].dropna().unique())
    for idx, cluster_id in enumerate(cluster_ids):
        subset = projected_df[projected_df["cluster"] == cluster_id]
        region_label = (
            str(subset["cluster_label"].dropna().iloc[0])
            if "cluster_label" in subset.columns and subset["cluster_label"].notna().any()
            else None
        )
        label = "Noise/Outlier" if int(cluster_id) < 0 else f"Cluster {int(cluster_id)}"
        color = get_cluster_color(region_label, int(cluster_id), idx)

        fig.add_trace(
            go.Scattergl(
                x=subset[x_col],
                y=subset[y_col],
                mode="markers",
                name=label,
                customdata=np.column_stack(
                    [
                        subset["latitude"].to_numpy(),
                        subset["longitude"].to_numpy(),
                    ]
                ),
                hovertemplate=(
                    f"{label}<br>"
                    f"{f'Region: {region_label}<br>' if region_label else ''}"
                    "Lat: %{customdata[0]:.2f}<br>"
                    "Lon: %{customdata[1]:.2f}<br>"
                    f"{x_col.upper()}: %{{x:.2f}}<br>"
                    f"{y_col.upper()}: %{{y:.2f}}<extra></extra>"
                ),
                marker={
                    "size": 7,
                    "color": color,
                    "opacity": 0.8,
                    "line": {"color": "white", "width": 0.4},
                },
            )
        )

        centroid_x = float(subset[x_col].mean())
        centroid_y = float(subset[y_col].mean())
        fig.add_trace(
            go.Scatter(
                x=[centroid_x],
                y=[centroid_y],
                mode="markers+text",
                name=f"{label} centroid",
                text=[label],
                textposition="top center",
                hovertemplate=(
                    f"{label}<br>"
                    f"{f'Region: {region_label}<br>' if region_label else ''}"
                    "Centroid<br>"
                    f"{x_col.upper()}: {centroid_x:.2f}<br>"
                    f"{y_col.upper()}: {centroid_y:.2f}<extra></extra>"
                ),
                marker={
                    "size": 14,
                    "color": color,
                    "symbol": "x",
                    "line": {"color": "#111111", "width": 1.5},
                },
                textfont={"size": 10, "color": color},
                showlegend=False,
            )
        )

        ellipse = _ellipse_trace(subset, x_col, y_col, color, label)
        if ellipse is not None:
            fig.add_trace(ellipse)

    if prediction and prediction.get("reduced_coords"):
        coords = prediction["reduced_coords"]
        if max(x_idx, y_idx) < len(coords):
            pc1 = coords[x_idx]
            pc2 = coords[y_idx]
        else:
            pc1, pc2 = coords[0], coords[1]
        prediction_name = prediction.get("location_name") or "Predicted location"
        fig.add_trace(
            go.Scattergl(
                x=[pc1],
                y=[pc2],
                mode="markers",
                name=prediction_name,
                hovertemplate=(
                    f"{prediction_name}<br>"
                    f"Cluster: {prediction['cluster_id']}<br>"
                    f"Label: {prediction['cluster_label']}<br>"
                    f"{x_col.upper()}: %{{x:.2f}}<br>"
                    f"{y_col.upper()}: %{{y:.2f}}<extra></extra>"
                ),
                marker={
                    "size": 14,
                    "color": "#111111",
                    "symbol": "star",
                    "line": {"color": "#F4D35E", "width": 1.5},
                },
            )
        )

    x_title = x_col.upper()
    y_title = y_col.upper()
    if len(explained) > max(x_idx, y_idx):
        x_title = f"{x_col.upper()} ({explained[x_idx]:.1f}% variance)"
        y_title = f"{y_col.upper()} ({explained[y_idx]:.1f}% variance)"

    fig.update_layout(
        height=560,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        dragmode=False,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        xaxis_title=x_title,
        yaxis_title=y_title,
        plot_bgcolor="#F8F6F0",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis={"fixedrange": True},
        yaxis={"fixedrange": True},
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": False,
            "displayModeBar": False,
        },
    )
