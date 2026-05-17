"""
India-focused map rendering helpers for the Streamlit dashboard.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


INDIA_CLUSTER_COLORS = [
    "#F472B6",
    "#1F6E8C",
    "#2D6A4F",
    "#E09F3E",
    "#7B2CBF",
    "#D62828",
    "#3A86FF",
    "#5C4033",
]


def get_cluster_color(label: str | None, cluster_id: int | None = None, fallback_index: int = 0) -> str:
    if cluster_id is not None and int(cluster_id) < 0:
        return "#9E9E9E"
    if cluster_id is not None:
        return INDIA_CLUSTER_COLORS[int(cluster_id) % len(INDIA_CLUSTER_COLORS)]
    return INDIA_CLUSTER_COLORS[fallback_index % len(INDIA_CLUSTER_COLORS)]


def render_cluster_map(clustered_df: pd.DataFrame, prediction: dict | None = None):
    fig = go.Figure()

    cluster_df = clustered_df.copy()
    cluster_ids = sorted(cluster_df["cluster"].dropna().unique())

    for idx, cluster_id in enumerate(cluster_ids):
        subset = cluster_df[cluster_df["cluster"] == cluster_id]
        region_label = (
            str(subset["cluster_label"].dropna().iloc[0])
            if "cluster_label" in subset.columns and subset["cluster_label"].notna().any()
            else None
        )
        label = (
            "Noise/Outlier"
            if int(cluster_id) < 0
            else (region_label or f"Cluster {int(cluster_id)}")
        )
        color = get_cluster_color(region_label, int(cluster_id), idx)

        fig.add_trace(
            go.Scattergeo(
                lon=subset["longitude"],
                lat=subset["latitude"],
                mode="markers",
                name=label,
                text=[label] * len(subset),
                hovertemplate="%{text}<extra></extra>",
                marker={
                    "size": 6,
                    "color": color,
                    "opacity": 0.75,
                    "line": {"color": "white", "width": 0.4},
                },
            )
        )

    if prediction:
        prediction_name = prediction.get("location_name") or "Predicted location"
        fig.add_trace(
            go.Scattergeo(
                lon=[prediction["longitude"]],
                lat=[prediction["latitude"]],
                mode="markers",
                name=prediction_name,
                customdata=[[prediction["cluster_id"], prediction["cluster_label"]]],
                hovertemplate=(
                    f"{prediction_name}<br>"
                    "Cluster ID: %{customdata[0]}<br>"
                    "Label: %{customdata[1]}<br>"
                    "Lat: %{lat:.2f}<br>"
                    "Lon: %{lon:.2f}<extra></extra>"
                ),
                marker={
                    "size": 13,
                    "color": "#111111",
                    "symbol": "star",
                    "line": {"color": "#F4D35E", "width": 1.5},
                },
            )
        )

    fig.update_layout(
        height=620,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        dragmode=False,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        geo={
            "scope": "asia",
            "projection_type": "mercator",
            "showland": True,
            "landcolor": "#F7F3E8",
            "showocean": True,
            "oceancolor": "#DCEAF7",
            "showlakes": True,
            "lakecolor": "#DCEAF7",
            "showcoastlines": True,
            "coastlinecolor": "#4F5D75",
            "coastlinewidth": 1,
            "showcountries": True,
            "countrycolor": "#4F5D75",
            "countrywidth": 1,
            "showsubunits": True,
            "subunitcolor": "#9AA5B1",
            "subunitwidth": 0.6,
            "showframe": False,
            "bgcolor": "rgba(0,0,0,0)",
            "lonaxis": {"range": [67, 98.5]},
            "lataxis": {"range": [6, 38.5]},
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": False,
            "displayModeBar": False,
        },
    )
