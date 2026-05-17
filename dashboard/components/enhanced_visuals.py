"""
Enhanced visualization components for the climate dashboard.
Provides interactive plotly charts for better data exploration.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sklearn.preprocessing import MinMaxScaler, StandardScaler


FRIENDLY_FEATURE_NAMES = {
    "nasa_solar_irradiance_allsky": "All-Sky Solar Potential",
    "nasa_solar_irradiance_clearsky": "Clear-Sky Solar Potential",
    "nasa_clearness_index": "Clearness Index",
    "nasa_longwave_radiation": "Longwave Radiation",
    "nasa_uv_index": "UV Index",
    "nasa_dewpoint_2m": "Dew Point",
    "nasa_temperature_2m": "Temperature at 2m",
    "nasa_relative_humidity": "Relative Humidity",
    "nasa_earth_skin_temperature": "Surface Skin Temperature",
    "nasa_specific_humidity": "Specific Humidity",
    "temperature_2m_mean": "Mean Temperature",
    "temperature_2m_max": "Maximum Temperature",
    "temperature_2m_min": "Minimum Temperature",
    "dewpoint_2m_mean": "Mean Dew Point",
    "relative_humidity_2m_mean": "Mean Relative Humidity",
    "relative_humidity_2m_max": "Maximum Relative Humidity",
    "relative_humidity_2m_min": "Minimum Relative Humidity",
    "precipitation_sum": "Rainfall",
    "surface_pressure_mean": "Surface Pressure",
    "wind_speed_120m_mean": "Wind Speed at 120m",
    "shortwave_radiation_sum": "Solar Radiation",
}


def _pretty_feature_name(name: str) -> str:
    return FRIENDLY_FEATURE_NAMES.get(name, name.replace("_", " ").title())


def render_cluster_distribution_pie(clustered_df: pd.DataFrame):
    """Render interactive pie chart showing cluster distribution."""
    if "cluster_label" not in clustered_df.columns:
        st.warning("Cluster labels are required for the distribution chart.")
        return

    cluster_counts = clustered_df.groupby("cluster_label").size().reset_index(name="count")

    fig = px.pie(
        cluster_counts,
        values="count",
        names="cluster_label",
        title="Climate Region Distribution",
        color_discrete_sequence=["#C0392B", "#A93226", "#CD6155", "#D98880", "#F2D7D5", "#6b7280", "#9ca3af", "#d1d5db"],
        hole=0.4,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Points: %{value}<br>Percentage: %{percent}<extra></extra>",
    )

    fig.update_layout(
        showlegend=True,
        height=420,
        margin=dict(t=60, b=20, l=20, r=20),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_climate_heatmap(cluster_profiles_df: pd.DataFrame):
    """Render heatmap of climate features across clusters."""
    feature_cols = [
        "temperature_2m_mean",
        "precipitation_sum",
        "relative_humidity_2m_mean",
        "shortwave_radiation_sum",
        "wind_speed_120m_mean",
    ]

    available_cols = [col for col in feature_cols if col in cluster_profiles_df.columns]
    if not available_cols or "cluster_label" not in cluster_profiles_df.columns:
        st.warning("Insufficient data for heatmap visualization.")
        return

    heatmap_data = cluster_profiles_df[["cluster_label"] + available_cols].copy().set_index("cluster_label")
    scaler = StandardScaler()
    normalized_data = pd.DataFrame(
        scaler.fit_transform(heatmap_data),
        columns=heatmap_data.columns,
        index=heatmap_data.index,
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=normalized_data.values,
            x=[_pretty_feature_name(col) for col in normalized_data.columns],
            y=normalized_data.index,
            colorscale="RdBu",
            text=heatmap_data.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="Normalized<br>Value"),
        )
    )

    fig.update_layout(
        title="Climate Features Heatmap Across Regions",
        xaxis_title="Climate Features",
        yaxis_title="Climate Regions",
        height=max(420, len(normalized_data) * 52),
        margin=dict(t=80, b=80, l=150, r=80),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_parallel_coordinates(clustered_df: pd.DataFrame):
    """Render parallel coordinates plot for cluster comparison."""
    feature_cols = [
        "temperature_2m_mean",
        "precipitation_sum",
        "relative_humidity_2m_mean",
        "cluster",
    ]
    available_cols = [col for col in feature_cols if col in clustered_df.columns]
    if len(available_cols) < 3:
        return

    plot_data = clustered_df[available_cols].copy()
    if len(plot_data) > 1000:
        plot_data = plot_data.sample(1000, random_state=42)

    dimensions = []
    for col in available_cols:
        if col != "cluster":
            dimensions.append(
                dict(
                    label=_pretty_feature_name(col),
                    values=plot_data[col],
                )
            )

    fig = go.Figure(
        data=go.Parcoords(
            line=dict(
                color=plot_data["cluster"],
                colorscale="Reds",
                showscale=True,
                cmin=float(plot_data["cluster"].min()),
                cmax=float(plot_data["cluster"].max()),
            ),
            dimensions=dimensions,
        )
    )

    fig.update_layout(
        title="Multi-dimensional Climate Feature Comparison",
        height=520,
        margin=dict(t=80, b=50, l=80, r=80),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_box_plots(clustered_df: pd.DataFrame):
    """Render box plots for climate variables across clusters."""
    if "cluster_label" not in clustered_df.columns:
        return

    features = ["temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"]
    available_features = [f for f in features if f in clustered_df.columns]
    if not available_features:
        return

    fig = make_subplots(
        rows=1,
        cols=len(available_features),
        subplot_titles=[_pretty_feature_name(f) for f in available_features],
    )

    colors = ["#C0392B", "#A93226", "#CD6155", "#D98880", "#F2D7D5", "#6b7280", "#9ca3af", "#d1d5db"]
    cluster_names = sorted(clustered_df["cluster_label"].dropna().unique())
    for idx, feature in enumerate(available_features, start=1):
        for cluster_idx, cluster_name in enumerate(cluster_names):
            cluster_data = clustered_df[clustered_df["cluster_label"] == cluster_name][feature]
            fig.add_trace(
                go.Box(
                    y=cluster_data,
                    name=cluster_name,
                    marker_color=colors[cluster_idx % len(colors)],
                    showlegend=(idx == 1),
                ),
                row=1,
                col=idx,
            )

    fig.update_layout(
        title_text="Distribution of Climate Variables Across Regions",
        height=520,
        showlegend=True,
        margin=dict(t=80, b=50, l=50, r=50),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_3d_scatter(clustered_df: pd.DataFrame):
    """Render 3D scatter plot of clusters."""
    pca_cols = ["PC1", "PC2", "PC3"]
    if all(col in clustered_df.columns for col in pca_cols):
        x_col, y_col, z_col = pca_cols
    elif all(
        col in clustered_df.columns
        for col in ["temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"]
    ):
        x_col, y_col, z_col = "temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"
    else:
        return

    plot_data = clustered_df.copy()
    if len(plot_data) > 2000:
        plot_data = plot_data.sample(2000, random_state=42)

    color_col = "cluster_label" if "cluster_label" in plot_data.columns else "cluster"
    hover_cols = [col for col in ["latitude", "longitude"] if col in plot_data.columns]

    fig = px.scatter_3d(
        plot_data,
        x=x_col,
        y=y_col,
        z=z_col,
        color=color_col,
        hover_data=hover_cols or None,
        color_discrete_sequence=["#C0392B", "#A93226", "#CD6155", "#D98880", "#F2D7D5", "#6b7280", "#9ca3af", "#d1d5db"],
        title="3D Cluster Visualization",
    )
    fig.update_traces(marker=dict(size=4, opacity=0.7))
    fig.update_layout(
        height=620,
        margin=dict(t=50, b=20, l=20, r=20),
        scene=dict(
            xaxis_title=_pretty_feature_name(x_col),
            yaxis_title=_pretty_feature_name(y_col),
            zaxis_title=_pretty_feature_name(z_col),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_time_series_comparison(clustered_df: pd.DataFrame):
    """Render comparison of seasonal patterns across clusters."""
    seasonal_cols = [
        col for col in clustered_df.columns if "monsoon" in col.lower() or "seasonal" in col.lower()
    ]
    if not seasonal_cols or "cluster_label" not in clustered_df.columns:
        return

    st.subheader("Seasonal Pattern Comparison")
    for col in seasonal_cols[:3]:
        fig = go.Figure()
        for cluster_name in sorted(clustered_df["cluster_label"].dropna().unique()):
            cluster_data = clustered_df[clustered_df["cluster_label"] == cluster_name][col]
            fig.add_trace(
                go.Box(
                    y=cluster_data,
                    name=cluster_name,
                    boxmean="sd",
                )
            )

        fig.update_layout(
            title=_pretty_feature_name(col) + " Distribution",
            yaxis_title="Value",
            xaxis_title="Climate Region",
            height=420,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_correlation_matrix(clustered_df: pd.DataFrame, selected_cluster: int | None = None):
    """Render correlation matrix for selected cluster or all data."""
    numeric_cols = clustered_df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ["cluster", "latitude", "longitude", "PC1", "PC2", "PC3", "pc1", "pc2", "pc3"]
    feature_cols = [col for col in numeric_cols if col not in exclude_cols][:10]
    if len(feature_cols) < 3:
        return

    if selected_cluster is not None and "cluster" in clustered_df.columns:
        data = clustered_df[clustered_df["cluster"] == selected_cluster][feature_cols]
        title = f"Feature Correlations - Cluster {selected_cluster}"
    else:
        data = clustered_df[feature_cols]
        title = "Feature Correlations - All Data"

    corr_matrix = data.corr(numeric_only=True)
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=[_pretty_feature_name(col)[:20] for col in corr_matrix.columns],
            y=[_pretty_feature_name(col)[:20] for col in corr_matrix.columns],
            colorscale="RdBu",
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 8},
            colorbar=dict(title="Correlation"),
        )
    )

    fig.update_layout(
        title=title,
        height=620,
        margin=dict(t=80, b=100, l=100, r=80),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_radar_chart(cluster_profiles_df: pd.DataFrame, selected_clusters: list[str] | None = None):
    """Render radar chart comparing multiple clusters."""
    feature_cols = [
        "temperature_2m_mean",
        "precipitation_sum",
        "relative_humidity_2m_mean",
        "shortwave_radiation_sum",
        "wind_speed_120m_mean",
    ]
    available_cols = [col for col in feature_cols if col in cluster_profiles_df.columns]
    if len(available_cols) < 3 or "cluster_label" not in cluster_profiles_df.columns:
        return

    data = cluster_profiles_df[["cluster_label"] + available_cols].copy()
    scaler = MinMaxScaler()
    data[available_cols] = scaler.fit_transform(data[available_cols])
    if selected_clusters:
        data = data[data["cluster_label"].isin(selected_clusters)]

    categories = [_pretty_feature_name(col) for col in available_cols]
    fig = go.Figure()
    for _, row in data.iterrows():
        values = row[available_cols].values.tolist()
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=row["cluster_label"],
                opacity=0.6,
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Climate Region Profiles Comparison",
        height=620,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_metric_cards(
    clustered_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    best_algorithm: str | None = None,
    best_score: float | None = None,
):
    n_points = len(clustered_df.drop_duplicates(subset=["latitude", "longitude"]))
    n_clusters = clustered_df["cluster"].nunique() if "cluster" in clustered_df.columns else 0
    best_algo = best_algorithm or (comparison_df.iloc[0]["algorithm"] if not comparison_df.empty else "N/A")
    if isinstance(best_algo, str) and best_algo.startswith("GMM"):
        best_algo = "GMM"
    score_value = (
        float(best_score)
        if best_score is not None
        else (
            float(comparison_df.iloc[0]["silhouette"])
            if not comparison_df.empty and "silhouette" in comparison_df.columns
            else 0.0
        )
    )

    metrics = [
        (f"{n_points:,}", "Data points"),
        (str(n_clusters), "Climate regions"),
        (best_algo, "Algorithm"),
        (f"{score_value:.3f}", "Silhouette score"),
    ]

    cols = st.columns(4)
    for col, (value, label) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div style="background: #ffffff;
                            border: 1px solid #e5e7eb;
                            border-top: 3px solid #C0392B;
                            border-radius: 6px;
                            padding: 16px 18px;
                            min-height: 92px;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;">
                    <div style="font-size: 0.7rem;
                                color: #9ca3af;
                                text-transform: uppercase;
                                letter-spacing: 0.07em;
                                margin-bottom: 6px;">{label}</div>
                    <div style="font-size: 1.9rem;
                                font-weight: 700;
                                color: #C0392B;
                                line-height: 1.1;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_geographic_coverage(clustered_df: pd.DataFrame):
    """Render geographic coverage statistics."""
    if not all(col in clustered_df.columns for col in ["latitude", "longitude"]):
        return

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Latitude Distribution", "Longitude Distribution"],
    )

    fig.add_trace(
        go.Histogram(x=clustered_df["latitude"], name="Latitude", marker_color="#C0392B", nbinsx=30),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Histogram(x=clustered_df["longitude"], name="Longitude", marker_color="#D98880", nbinsx=30),
        row=1,
        col=2,
    )

    fig.update_layout(
        title_text="Geographic Coverage Analysis",
        showlegend=False,
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
