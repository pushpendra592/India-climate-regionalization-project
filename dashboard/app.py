"""
Streamlit dashboard for India climate clusters and exact-location lookup.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.sidebar import render_sidebar
from dashboard.components.styles import inject_styles
from src.prediction.location_predictor import LocationPredictor

from dashboard.components.data_loaders import load_clustered_data
from dashboard.components.tab_renderers import (
    _render_project_section,
    _render_how_it_works,
    _render_model_training_section,
    _render_cluster_explorer,
    _render_domain_insights,
)

def main():
    st.set_page_config(page_title="India Climate Cluster Explorer", layout="wide")
    inject_styles()
    
    st.title("India Climate Cluster Explorer")
    st.caption("Train on India-wide points, then classify any supported place into a learned climate cluster.")

    (
        clustered_df,
        comparison_df,
        cluster_profiles_df,
        agriculture_df,
        energy_df,
        disaster_df,
        urban_df,
        metadata,
    ) = load_clustered_data()
    
    controls = render_sidebar()
    predictor = LocationPredictor()

    prediction = None
    if controls["trigger"]:
        with st.spinner("Fetching NASA POWER history and assigning a climate cluster..."):
            prediction = predictor.predict_place(controls["place_name"])

    project_tab, pipeline_tab, training_tab, explorer_tab, insights_tab = st.tabs(
        [
            "1. Project",
            "2. Data Collection to Model Input",
            "3. Model Training and Outputs",
            "4. Clustering Exploration",
            "5. Domain Insights",
        ]
    )

    with project_tab:
        _render_project_section(clustered_df, comparison_df, metadata)

    with pipeline_tab:
        _render_how_it_works(clustered_df, comparison_df, metadata)

    with training_tab:
        _render_model_training_section(clustered_df, comparison_df, cluster_profiles_df, metadata, prediction)

    with explorer_tab:
        _render_cluster_explorer(clustered_df, cluster_profiles_df, metadata)

    with insights_tab:
        _render_domain_insights(
            clustered_df,
            agriculture_df,
            energy_df,
            disaster_df,
            urban_df,
        )


if __name__ == "__main__":
    main()
