import streamlit as st
import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import INTERIM_DIR, MODELS_DIR, PROCESSED_DIR, TABLES_DIR
from src.utils.io_helpers import load_dataframe, load_json, load_pickle

@st.cache_data(show_spinner=False)
def load_clustered_data():
    clustered = load_dataframe(PROCESSED_DIR / "climate_normals_clustered.parquet", "clustered climate normals")
    comparison = load_dataframe(TABLES_DIR / "algorithm_comparison.parquet", "algorithm comparison")
    cluster_profiles = load_dataframe(TABLES_DIR / "cluster_profiles.parquet", "cluster profiles")
    agriculture = load_dataframe(TABLES_DIR / "agriculture_insights.parquet", "agriculture insights")
    energy = load_dataframe(TABLES_DIR / "energy_insights.parquet", "energy insights")
    disaster = load_dataframe(TABLES_DIR / "disaster_insights.parquet", "disaster insights")
    urban = load_dataframe(TABLES_DIR / "urban_insights.parquet", "urban insights")
    metadata = load_json(MODELS_DIR / "prediction_metadata.json")
    return clustered, comparison, cluster_profiles, agriculture, energy, disaster, urban, metadata


@st.cache_data(show_spinner=False)
def load_feature_importance() -> pd.DataFrame:
    metadata = load_json(MODELS_DIR / "prediction_metadata.json")
    reducer = load_pickle(MODELS_DIR / "pca_reducer.pkl")
    feature_cols = metadata.get("feature_cols", [])

    if not feature_cols or not hasattr(reducer, "pca"):
        return pd.DataFrame(columns=["feature", "importance"])

    pca = reducer.pca
    explained = pca.explained_variance_ratio_
    n_components = min(3, len(explained))
    weighted = abs(pca.components_[:n_components]).T @ explained[:n_components]
    importance = 100 * weighted / weighted.max()

    feature_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance": importance,
        }
    ).sort_values("importance", ascending=False)
    return feature_df


@st.cache_data(show_spinner=False)
def load_preview_csv(path: Path, nrows: int = 5) -> pd.DataFrame:
    try:
        return pd.read_csv(path, nrows=nrows)
    except FileNotFoundError:
        return pd.DataFrame({"Notice": [f"Data preview for {path.name} is not available in the deployed environment."]})


@st.cache_data(show_spinner=False)
def load_csv_columns(path: Path) -> list[str]:
    try:
        return list(pd.read_csv(path, nrows=0).columns)
    except FileNotFoundError:
        return []


@st.cache_data(show_spinner=False)
def load_scaler_pca_summary() -> dict:
    scaler = load_pickle(MODELS_DIR / "scaler.pkl")
    reducer = load_pickle(MODELS_DIR / "pca_reducer.pkl")
    feature_names = scaler.get_feature_names()
    explained = reducer.get_explained_variance() if hasattr(reducer, "get_explained_variance") else []
    
    def _pretty_feature_name(name: str) -> str:
        aliases = {
            "nasa_solar_irradiance_allsky": "All-Sky Solar Potential",
            "nasa_solar_irradiance_clearsky": "Clear-Sky Solar Potential",
            "nasa_clearness_index": "Clearness Index",
            "nasa_longwave_radiation": "Longwave Radiation",
            "nasa_uv_index": "UV Index",
            "nasa_dewpoint_2m": "Dew Point",
            "nasa_earth_skin_temperature": "Surface Skin Temperature",
            "nasa_specific_humidity": "Specific Humidity",
            "temperature_2m_mean": "Mean Temperature",
            "precipitation_sum": "Rainfall",
            "relative_humidity_2m_mean": "Relative Humidity",
            "wind_speed_120m_mean": "Wind Speed at 120m",
            "monsoon_rainfall_share": "Monsoon Rainfall Share",
            "seasonal_humidity_contrast": "Seasonal Humidity Contrast",
            "annual_temp_cycle_range": "Annual Temperature Cycle Range",
        }
        return aliases.get(name, name.replace("_", " ").title())
    
    top_components = []
    if hasattr(reducer, "pca") and feature_names:
        for idx in range(min(3, len(explained))):
            component = reducer.pca.components_[idx]
            top_idx = sorted(range(len(component)), key=lambda i: abs(component[i]), reverse=True)[:5]
            top_components.append(
                {
                    "component": f"PC{idx + 1}",
                    "variance_pct": float(explained[idx] * 100),
                    "top_features": [_pretty_feature_name(feature_names[i]) for i in top_idx],
                }
            )
    return {
        "feature_count": len(feature_names),
        "reduced_components": len(explained),
        "variance_retained_pct": float(sum(explained) * 100) if len(explained) else None,
        "top_components": top_components,
    }
