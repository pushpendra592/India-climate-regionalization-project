import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.settings import INTERIM_DIR, PROCESSED_DIR, PROJECT_ROOT
from dashboard.components.data_loaders import load_preview_csv, load_scaler_pca_summary, load_feature_importance
from dashboard.components.styles import section_heading, kpi_tile
from dashboard.components.feature_catalog import FEATURE_CATALOG

from dashboard.components.enhanced_visuals import (
    render_box_plots,
    render_climate_heatmap,
    render_cluster_distribution_pie,
    render_correlation_matrix,
    render_geographic_coverage,
    render_metric_cards,
    render_parallel_coordinates,
    render_radar_chart,
)
from dashboard.components.map_widget import render_cluster_map
from dashboard.components.scatter_widget import render_cluster_scatter

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

def _algorithm_to_cluster_column(algorithm_name: str) -> str | None:
    mapping = {
        "K-Means": "cluster_kmeans",
        "K-Means(k=6)": "cluster_kmeans_k6",
        "K-Means(k=7)": "cluster_kmeans_k7",
        "K-Means(k=8)": "cluster_kmeans_k8",
        "Hierarchical(Ward)": "cluster_hierarchical_ward",
        "Hierarchical(Average)": "cluster_hierarchical_avg",
        "Hierarchical(Ward, k=6)": "cluster_hierarchical_ward_k6",
        "Hierarchical(Average, k=6)": "cluster_hierarchical_avg_k6",
        "Hierarchical(Ward, k=7)": "cluster_hierarchical_ward_k7",
        "Hierarchical(Average, k=7)": "cluster_hierarchical_avg_k7",
        "Hierarchical(Ward, k=8)": "cluster_hierarchical_ward_k8",
        "Hierarchical(Average, k=8)": "cluster_hierarchical_avg_k8",
        "DBSCAN": "cluster_dbscan",
        "HDBSCAN": "cluster_hdbscan",
        "GMM": "cluster_gmm",
        "GMM(k=6)": "cluster_gmm_k6",
        "GMM(k=7)": "cluster_gmm_k7",
        "GMM(k=8)": "cluster_gmm_k8",
    }
    return mapping.get(algorithm_name)

def _algorithm_family(algorithm_name: str) -> str:
    if algorithm_name.startswith("K-Means"): return "K-Means"
    if algorithm_name.startswith("Hierarchical(Ward"): return "Hierarchical (Ward)"
    if algorithm_name.startswith("Hierarchical(Average"): return "Hierarchical (Average)"
    if algorithm_name.startswith("GMM"): return "GMM"
    if algorithm_name.startswith("DBSCAN"): return "DBSCAN"
    if algorithm_name.startswith("HDBSCAN"): return "HDBSCAN"
    return algorithm_name

def _algorithm_k_value(algorithm_name: str) -> str:
    if algorithm_name in ["DBSCAN", "HDBSCAN"]: return "Auto"
    if "(k=" in algorithm_name: return algorithm_name.split("(k=")[1].split(")")[0]
    if "(Ward, k=" in algorithm_name: return algorithm_name.split("(Ward, k=")[1].split(")")[0]
    if "(Average, k=" in algorithm_name: return algorithm_name.split("(Average, k=")[1].split(")")[0]
    if algorithm_name in {"K-Means", "GMM", "Hierarchical(Ward)", "Hierarchical(Average)"}: return "4"
    return "Auto"

def _build_algorithm_selector_options(clustered_df: pd.DataFrame, comparison_df: pd.DataFrame) -> list[str]:
    options = []
    for algorithm_name in comparison_df["algorithm"].tolist():
        column_name = _algorithm_to_cluster_column(str(algorithm_name))
        if column_name and column_name in clustered_df.columns and algorithm_name not in options:
            options.append(str(algorithm_name))
    return options

def _prepare_algorithm_view(clustered_df: pd.DataFrame, selected_algorithm: str, metadata: dict) -> pd.DataFrame:
    selected_col = _algorithm_to_cluster_column(selected_algorithm)
    if not selected_col or selected_col not in clustered_df.columns: return clustered_df.copy()
    out = clustered_df.copy()
    out["cluster"] = out[selected_col]
    best_algorithm = metadata.get("best_algorithm")
    best_key = metadata.get("best_key")
    best_col = f"cluster_{best_key}" if best_key else "cluster"
    if selected_algorithm == best_algorithm or selected_col == best_col:
        if "cluster_label" not in out.columns:
            label_map = metadata.get("auto_labels", {})
            out["cluster_label"] = out["cluster"].map(
                lambda cid: label_map.get(str(int(cid)), f"Cluster {int(cid)}") if pd.notna(cid) and int(cid) >= 0 else "Noise/Outlier"
            )
        return out
    def _generic_label(cluster_id):
        if pd.isna(cluster_id): return "Unassigned"
        cluster_id = int(cluster_id)
        if cluster_id < 0: return "Noise/Outlier"
        return f"Cluster {cluster_id}"
    out["cluster_label"] = out["cluster"].map(_generic_label)
    return out

def _cluster_label_map(clustered_df: pd.DataFrame) -> dict[int, str]:
    unique_rows = clustered_df[["cluster", "cluster_label"]].dropna().drop_duplicates(subset=["cluster"])
    return {int(row["cluster"]): str(row["cluster_label"]) for _, row in unique_rows.iterrows()}

def _attach_cluster_labels(df: pd.DataFrame, label_map: dict[int, str]) -> pd.DataFrame:
    if "cluster" not in df.columns: return df
    out = df.copy()
    out["cluster_label"] = out["cluster"].map(label_map).fillna("Unassigned")
    cols = out.columns.tolist()
    if "cluster_label" in cols:
        cols.insert(1, cols.pop(cols.index("cluster_label")))
        out = out[cols]
    return out



def _render_project_section(clustered_df: pd.DataFrame, comparison_df: pd.DataFrame, metadata: dict):
    section_heading("About the Project")
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("""
            <div class="info-card">
            <h4 style="margin-top:0;margin-bottom:8px;color:#111827;">Project purpose</h4>
            This project builds a <strong>data-driven climate regionalization of India</strong> using NASA POWER weather data and
            unsupervised machine learning.<br><br>
            Instead of manually assigning traditional climate zones, the workflow learns regions directly from long-term
            weather behavior across India.
            <h4 style="margin-top:16px;margin-bottom:8px;color:#111827;">Core idea</h4>
            <ul>
            <li>Collect India-wide weather data</li>
            <li>Clean and standardize the data</li>
            <li>Engineer climate-focused features</li>
            <li>Aggregate weather into long-term climate signatures</li>
            <li>Train multiple clustering models</li>
            <li>Choose the most useful full-coverage regionalization</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    with right:
        st.markdown(f"""
            <div class="info-card">
            <h4 style="margin-top:0;margin-bottom:8px;color:#111827;">Project highlights</h4>
            <ul>
            <li><strong>Training points:</strong> {len(clustered_df.drop_duplicates(subset=["latitude", "longitude"])):,}</li>
            <li><strong>Algorithms compared:</strong> {comparison_df["algorithm"].nunique() if "algorithm" in comparison_df.columns else len(comparison_df)}</li>
            <li><strong>Final production model:</strong> {metadata.get("best_algorithm", "N/A")}</li>
            <li><strong>Final climate regions:</strong> {clustered_df["cluster"].nunique()}</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        st.info("The focus is not just better clustering scores. The focus is a geographically meaningful, interpretable climate map of India.")
    section_heading("Final learned climate regions")
    label_df = clustered_df[["cluster", "cluster_label"]].drop_duplicates().sort_values("cluster").reset_index(drop=True)
    st.dataframe(label_df, use_container_width=True, hide_index=True)

def _render_prediction_result(prediction: dict):
    section_heading("Prediction Result")
    top = st.columns(4)
    top[0].metric("Cluster Name", prediction["cluster_label"])
    top[1].metric("Cluster ID", prediction["cluster_id"])
    top[2].metric("Assignment", prediction["assignment_method"])
    confidence = prediction.get("confidence")
    top[3].metric("Confidence", f"{confidence * 100:.0f}%" if confidence is not None else "N/A", help="For the selected production GMM model, this reflects the strongest cluster membership probability.")
    if confidence is not None:
        st.progress(max(0.0, min(1.0, float(confidence))), text=f"Assignment confidence: {confidence * 100:.1f}%")
    info_cols = st.columns([1.2, 1])
    with info_cols[0]:
        st.markdown(f"<div class='pred-card'><div class='pred-label'>Resolved Place</div><div class='pred-value'>{prediction.get('location_name', 'Unknown')}</div></div>", unsafe_allow_html=True)
        if prediction.get("address"): st.caption(prediction["address"])
        st.write(prediction["summary"])
        if prediction.get("alternative_cluster_label"):
            st.write(f"Closest alternative region: **{prediction['alternative_cluster_label']}** (Cluster {prediction['alternative_cluster_id']})")
    with info_cols[1]:
        st.markdown("**Why this place matches**")
        for item in prediction["top_characteristics"]:
            st.write(f"- {item['summary']}")
    if prediction["nearest_examples"]:
        st.markdown("**Nearest climate twins**")
        st.dataframe(pd.DataFrame(prediction["nearest_examples"]), use_container_width=True, hide_index=True)

def _render_overview(clustered_df: pd.DataFrame, comparison_df: pd.DataFrame, cluster_profiles_df: pd.DataFrame, metadata: dict, prediction: dict | None):
    algorithm_options = _build_algorithm_selector_options(clustered_df, comparison_df)
    default_algorithm = metadata.get("best_algorithm")
    default_index = algorithm_options.index(default_algorithm) if default_algorithm in algorithm_options else 0
    initial_algorithm = st.session_state.get("overview_algorithm_selector", algorithm_options[default_index] if algorithm_options else None)
    if initial_algorithm not in algorithm_options and algorithm_options: initial_algorithm = algorithm_options[default_index]
    family_map: dict[str, list[str]] = {}
    for option in algorithm_options: family_map.setdefault(_algorithm_family(option), []).append(option)
    family_order = [name for name in ["GMM", "K-Means", "Hierarchical (Ward)", "Hierarchical (Average)", "DBSCAN", "HDBSCAN"] if name in family_map]
    current_family = _algorithm_family(initial_algorithm) if initial_algorithm else family_order[0]
    current_k = _algorithm_k_value(initial_algorithm) if initial_algorithm else "Auto"
    
    metrics_placeholder = st.container()
    st.markdown("<br>", unsafe_allow_html=True)
    
    selector_left, selector_mid, selector_right = st.columns([1, 1, 2])
    with selector_left:
        selected_family = st.selectbox("Model", family_order, index=family_order.index(current_family) if current_family in family_order else 0, key="overview_model_family_selector")
    available_algorithms = family_map.get(selected_family, [])
    available_k_values = []
    for alg in available_algorithms:
        k_val = _algorithm_k_value(alg)
        if k_val not in available_k_values: available_k_values.append(k_val)
    with selector_mid:
        selected_k = st.selectbox("k value", available_k_values, index=available_k_values.index(current_k) if current_k in available_k_values else 0, key="overview_model_k_selector")
    matching_algorithms = [alg for alg in available_algorithms if _algorithm_k_value(alg) == selected_k]
    selected_algorithm = matching_algorithms[0] if matching_algorithms else available_algorithms[0]
    st.session_state["overview_algorithm_selector"] = selected_algorithm
    active_clustered_df = _prepare_algorithm_view(clustered_df, selected_algorithm, metadata)
    label_map = _cluster_label_map(active_clustered_df)
    profile_for_viz = cluster_profiles_df.copy()
    if "cluster_label" not in profile_for_viz.columns: profile_for_viz = _attach_cluster_labels(profile_for_viz, label_map)
    selected_row = comparison_df[comparison_df["algorithm"] == selected_algorithm].head(1)
    selected_score = float(selected_row.iloc[0]["silhouette"]) if not selected_row.empty and "silhouette" in selected_row.columns else None
    
    with metrics_placeholder:
        render_metric_cards(active_clustered_df, comparison_df, best_algorithm=selected_algorithm, best_score=selected_score)
        
    with selector_right:
        if selected_algorithm == default_algorithm: st.caption("Showing the final production clustering output used throughout the project.")
        else: st.caption("Showing an alternate saved clustering output for comparison. Prediction and domain insights still use the final production model.")
    left, right = st.columns([1.25, 1])
    with left:
        section_heading("Training Coverage Map")
        render_cluster_map(active_clustered_df, prediction if selected_algorithm == default_algorithm else None)
    with right:
        section_heading("Current Training Ranking")
        ranking_cols = [col for col in ["algorithm", "n_clusters", "silhouette", "max_cluster_share", "composite_score"] if col in comparison_df.columns]
        st.dataframe(comparison_df[ranking_cols], use_container_width=True, hide_index=True)
    section_heading("Cluster Point Graph", "Each point is a location projected into PCA climate space using PC1 vs PC3.")
    render_cluster_scatter(active_clustered_df, prediction if selected_algorithm == default_algorithm else None, axis_pair="PC1 vs PC3")
    vis_left, vis_right = st.columns(2)
    with vis_left: render_cluster_distribution_pie(active_clustered_df)
    with vis_right: render_geographic_coverage(active_clustered_df)
    section_heading("Regional Climate Comparison")
    if selected_algorithm == default_algorithm: render_climate_heatmap(profile_for_viz)
    else: st.info("This heatmap stays tied to the final production model profiles. Use the map, scatter plot, and distribution charts above to compare alternate algorithm outputs.")
    with st.expander("More distribution visuals", expanded=False):
        section_heading("Climate Variable Spread")
        render_box_plots(active_clustered_df)
        section_heading("Feature Relationship Overview")
        render_parallel_coordinates(active_clustered_df)
    if prediction: _render_prediction_result(prediction)

def _render_cluster_methodology_card(cluster_id: int, metadata: dict, label_map: dict[int, str], subset: pd.DataFrame, total_points: int):
    description = metadata.get("cluster_descriptions", {}).get(str(cluster_id), {})
    region_name = label_map.get(cluster_id, f"Cluster {cluster_id}")
    st.markdown(f"### {region_name}")
    left, right = st.columns([1, 1.25])
    with left:
        st.write(f"- Cluster ID: `{cluster_id}`")
        st.write(f"- Locations: `{len(subset)}`")
        st.write(f"- Coverage: `{len(subset) / max(total_points, 1) * 100:.1f}%`")
        if {"temperature_2m_mean", "precipitation_sum", "wind_speed_120m_mean"}.issubset(subset.columns):
            st.write(f"- Temp: `{subset['temperature_2m_mean'].mean():.2f}°C`")
            st.write(f"- Rain: `{subset['precipitation_sum'].mean():.2f}`")
            st.write(f"- Wind 120m: `{subset['wind_speed_120m_mean'].mean():.2f}`")
    with right:
        st.markdown("**Why this cluster is different**")
        for item in description.get("characteristics", [])[:5]: st.write(f"- {item['summary']}")

def _render_cluster_explorer(clustered_df: pd.DataFrame, cluster_profiles_df: pd.DataFrame, metadata: dict):
    section_heading("Cluster Explorer")
    label_map = _cluster_label_map(clustered_df)
    cluster_choices = sorted(label_map.items(), key=lambda item: item[0])
    selected_cluster = st.selectbox("Choose a cluster", options=[cluster_id for cluster_id, _ in cluster_choices], format_func=lambda cid: f"{cid} - {label_map.get(cid, f'Cluster {cid}')}", key="cluster_explorer_select")
    subset = clustered_df[clustered_df["cluster"] == selected_cluster].copy()
    if subset.empty:
        st.info("No points found for the selected cluster.")
        return
    metric_cols = st.columns(4)
    metric_cols[0].metric("Cluster ID", int(selected_cluster))
    metric_cols[1].metric("Region Name", label_map.get(int(selected_cluster), f"Cluster {selected_cluster}"))
    metric_cols[2].metric("Points", int(len(subset)))
    metric_cols[3].metric("Coverage", f"{len(subset) / len(clustered_df) * 100:.1f}%")
    _render_cluster_methodology_card(int(selected_cluster), metadata, label_map, subset, len(clustered_df))
    map_col, stats_col = st.columns([1.2, 1])
    with map_col:
        st.markdown("**Selected Cluster on India Map**")
        render_cluster_map(subset)
    with stats_col:
        st.markdown("**Regional Summary**")
        if {"latitude", "longitude"}.issubset(subset.columns):
            st.write(f"- Mean location: ({subset['latitude'].mean():.2f}, {subset['longitude'].mean():.2f})")
            st.write(f"- Latitude range: {subset['latitude'].min():.2f} to {subset['latitude'].max():.2f}")
            st.write(f"- Longitude range: {subset['longitude'].min():.2f} to {subset['longitude'].max():.2f}")
        if "temperature_2m_mean" in subset.columns: st.write(f"- Mean temperature: {subset['temperature_2m_mean'].mean():.2f}")
        if "precipitation_sum" in subset.columns: st.write(f"- Mean rainfall: {subset['precipitation_sum'].mean():.2f}")
        if "relative_humidity_2m_mean" in subset.columns: st.write(f"- Mean humidity: {subset['relative_humidity_2m_mean'].mean():.2f}")
    st.markdown("**Selected Cluster in PCA Space**")
    render_cluster_scatter(subset, axis_pair="PC1 vs PC3")
    profile_for_viz = cluster_profiles_df.copy()
    if "cluster_label" not in profile_for_viz.columns: profile_for_viz = _attach_cluster_labels(profile_for_viz, label_map)
    selected_label = label_map.get(int(selected_cluster), f"Cluster {selected_cluster}")
    radar_col, corr_col = st.columns(2)
    with radar_col:
        st.markdown("**Regional Feature Profile**")
        render_radar_chart(profile_for_viz, selected_clusters=[selected_label])
    with corr_col:
        st.markdown("**Within-Cluster Correlations**")
        render_correlation_matrix(clustered_df, selected_cluster=selected_cluster)
    st.markdown("**Sample locations**")
    sample_cols = [col for col in ["latitude", "longitude", "cluster", "cluster_label", "temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean"] if col in subset.columns]
    st.dataframe(subset[sample_cols].head(50), use_container_width=True, hide_index=True)
    st.markdown("**Cluster profile row**")
    if "cluster" in cluster_profiles_df.columns:
        profile_row = cluster_profiles_df[cluster_profiles_df["cluster"] == selected_cluster].copy()
        if not profile_row.empty:
            profile_row = _attach_cluster_labels(profile_row, label_map)
            show_profile_cols = [col for col in ["cluster", "cluster_label", "cluster_size", "cluster_pct", "temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean", "shortwave_radiation_sum", "wind_speed_120m_mean", "monsoon_rainfall_share"] if col in profile_row.columns]
            st.dataframe(profile_row[show_profile_cols], use_container_width=True, hide_index=True)

def _render_domain_insights(clustered_df: pd.DataFrame, agriculture_df: pd.DataFrame, energy_df: pd.DataFrame, disaster_df: pd.DataFrame, urban_df: pd.DataFrame):
    section_heading("Domain Insights", "How learned climate regions translate into agriculture, energy, disaster, and urban planning context.")
    st.markdown("""
        - `Agriculture`: Climate → rainfall reliability → crop environment → recommendation  
        - `Energy`: Climate → solar and wind potential → resource mix → siting signal  
        - `Disaster`: Climate → extreme-weather-style indicators → hazard tendency → preparedness signal  
        - `Urban`: Climate → heat, humidity, comfort → planning suitability → adaptation guidance
    """)
    label_map = _cluster_label_map(clustered_df)
    agri, energy, disaster, urban = st.tabs(["Agriculture", "Energy", "Disaster", "Urban"])
    with agri:
        agri_view = _attach_cluster_labels(agriculture_df, label_map)
        st.caption("Agricultural suitability and moisture/heat context by climate region.")
        if not agri_view.empty and "agriculture_suitability_score" in agri_view.columns:
            best = agri_view.sort_values("agriculture_suitability_score", ascending=False).iloc[0]
            cols = st.columns(3)
            cols[0].metric("Top Agriculture Region", str(best["cluster_label"]))
            cols[1].metric("Suitability Score", f"{float(best['agriculture_suitability_score']):.3f}")
            cols[2].metric("Points", int(best["points"]))
        show_cols = [col for col in ["cluster", "cluster_label", "points", "agriculture_suitability_score", "agriculture_summary", "agriculture_recommendation", "temperature_2m_mean_mean", "precipitation_sum_mean", "relative_humidity_2m_mean_mean", "rainfall_reliability_mean"] if col in agri_view.columns]
        st.dataframe(agri_view[show_cols], use_container_width=True, hide_index=True)
    with energy:
        energy_view = _attach_cluster_labels(energy_df, label_map)
        st.caption("Renewable energy potential by cluster using solar and wind indicators.")
        if not energy_view.empty and "energy_potential_score" in energy_view.columns:
            best = energy_view.sort_values("energy_potential_score", ascending=False).iloc[0]
            cols = st.columns(3)
            cols[0].metric("Top Energy Region", str(best["cluster_label"]))
            cols[1].metric("Energy Score", f"{float(best['energy_potential_score']):.3f}")
            cols[2].metric("Resource Mix", str(best.get("resource_mix", "N/A")))
        show_cols = [col for col in ["cluster", "cluster_label", "points", "energy_potential_score", "resource_mix", "energy_summary", "energy_recommendation", "shortwave_radiation_sum_mean", "wind_power_density_120m_mean", "solar_utilization_ratio_mean"] if col in energy_view.columns]
        st.dataframe(energy_view[show_cols], use_container_width=True, hide_index=True)
    with disaster:
        disaster_view = _attach_cluster_labels(disaster_df, label_map)
        st.caption("Observed extreme-weather-style indicators summarized by cluster.")
        if not disaster_view.empty and "disaster_risk_score" in disaster_view.columns:
            highest = disaster_view.sort_values("disaster_risk_score", ascending=False).iloc[0]
            cols = st.columns(3)
            cols[0].metric("Highest Risk Region", str(highest["cluster_label"]))
            cols[1].metric("Risk Score", f"{float(highest['disaster_risk_score']):.3f}")
            cols[2].metric("Dominant Hazard", str(highest.get("dominant_hazard", "N/A")))
        show_cols = [col for col in ["cluster", "cluster_label", "points", "disaster_risk_score", "dominant_hazard", "disaster_summary", "risk_recommendation", "precipitation_sum_mean", "precipitation_sum_interannual_std_mean", "wind_power_density_120m_mean"] if col in disaster_view.columns]
        st.dataframe(disaster_view[show_cols], use_container_width=True, hide_index=True)
    with urban:
        urban_view = _attach_cluster_labels(urban_df, label_map)
        st.caption("Urban comfort and thermal context across the learned climate regions.")
        if not urban_view.empty and "urban_comfort_score" in urban_view.columns:
            best = urban_view.sort_values("urban_comfort_score", ascending=False).iloc[0]
            cols = st.columns(3)
            cols[0].metric("Best Urban Comfort Region", str(best["cluster_label"]))
            cols[1].metric("Comfort Score", f"{float(best['urban_comfort_score']):.3f}")
            cols[2].metric("Urban Summary", str(best.get("urban_summary", "N/A")))
        show_cols = [col for col in ["cluster", "cluster_label", "points", "urban_comfort_score", "urban_summary", "urban_recommendation", "thermal_stress_index_mean", "outdoor_comfort_score_mean", "heat_island_potential_mean", "temperature_2m_mean_mean", "relative_humidity_2m_mean_mean"] if col in urban_view.columns]
        st.dataframe(urban_view[show_cols], use_container_width=True, hide_index=True)

def _render_feature_importance_chart(feature_df: pd.DataFrame):
    if feature_df.empty:
        st.info("Feature-importance view is not available for the current saved PCA assets.")
        return
    top_features = feature_df.head(10).sort_values("importance", ascending=True)
    fig = go.Figure(go.Bar(x=top_features["importance"], y=[_pretty_feature_name(name) for name in top_features["feature"]], orientation="h", marker_color="#C0392B", text=[f"{value:.0f}%" for value in top_features["importance"]], textposition="outside"))
    fig.update_layout(title="Dominant Features Driving PCA Climate Separation", xaxis_title="Relative Importance", yaxis_title="Feature", height=430, margin={"l": 0, "r": 0, "t": 50, "b": 0}, plot_bgcolor="#ffffff", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def _render_pipeline_data_walkthrough(metadata: dict):
    section_heading("Raw Data to Model Input", "This walkthrough shows how the project transforms raw NASA POWER records into the final PCA-ready input used by the clustering model.")
    raw_path = PROJECT_ROOT / "data" / "previews" / "nasa_power_combined.csv"
    cleaned_path = PROJECT_ROOT / "data" / "previews" / "merged_daily.csv"
    feature_daily_path = PROJECT_ROOT / "data" / "previews" / "feature_matrix_daily.csv"
    monthly_path = PROJECT_ROOT / "data" / "previews" / "feature_matrix_monthly.csv"
    seasonal_path = PROJECT_ROOT / "data" / "previews" / "feature_matrix_seasonal.csv"
    yearly_path = PROJECT_ROOT / "data" / "previews" / "feature_matrix_yearly.csv"
    normals_path = PROJECT_ROOT / "data" / "previews" / "climate_normals.csv"
    walkthrough_stages = [
        {"title": "1. Raw NASA POWER Data", "summary": "Daily weather records collected for each valid India land point.", "path": raw_path, "preview_cols": ["latitude", "longitude", "date", "ALLSKY_SFC_SW_DWN", "T2M", "RH2M", "PRECTOTCORR", "WS10M"], "notes": ["Contains the raw API field names.", "One row represents one day at one location.", "This is the true raw weather input stage."]},
        {"title": "2. Normalized and Cleaned Daily Data", "summary": "NASA fields renamed into project-friendly climate columns and cleaned.", "path": cleaned_path, "preview_cols": ["latitude", "longitude", "date", "temperature_2m_mean", "relative_humidity_2m_mean", "precipitation_sum", "wind_speed_10m_mean", "shortwave_radiation_sum"], "notes": ["Column names are standardized.", "Duplicates are removed, missing values are filled, and physical limits are enforced.", "This is the clean daily weather base used for feature engineering."]},
        {"title": "3. Daily Feature Matrix", "summary": "Derived climate features are added to the cleaned daily data.", "path": feature_daily_path, "preview_cols": ["latitude", "longitude", "temperature_2m_mean", "temp_range_daily", "wind_speed_120m_mean", "wind_power_density_120m", "growing_degree_days", "soil_air_temp_diff"], "notes": ["This is where the project moves beyond raw weather variables.", "Energy, agriculture, disaster, and urban indicators are all created here."]},
        {"title": "4. Monthly / Seasonal / Yearly Aggregation", "summary": "Daily weather signals are compressed into climate-scale summaries.", "path": monthly_path, "preview_cols": ["latitude", "longitude", "year", "month", "temperature_2m_mean", "precipitation_sum", "wind_speed_120m_mean"], "notes": ["Monthly aggregation keeps time structure while reducing day-level noise.", "Parallel seasonal and yearly tables are also produced for long-term descriptors."]},
        {"title": "5. Climate Normals", "summary": "Each location becomes one long-term climate signature row.", "path": normals_path, "preview_cols": ["latitude", "longitude", "temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean", "wind_speed_120m_mean", "shortwave_radiation_sum"], "notes": ["This is the core model input table before scaling.", "It captures long-term climate behavior instead of daily weather noise."]},
    ]
    for stage in walkthrough_stages:
        st.markdown(f"#### {stage['title']}")
        st.write(stage["summary"])
        for note in stage["notes"]: st.write(f"- {note}")
        preview_df = load_preview_csv(stage["path"], nrows=5)
        preview_cols = [col for col in stage["preview_cols"] if col in preview_df.columns]
        st.dataframe(preview_df[preview_cols] if preview_cols else preview_df.head(5), use_container_width=True, hide_index=True)
        st.caption(f"Source file: {stage['path'].name}")
        st.markdown("<br>", unsafe_allow_html=True)
            
    section_heading("Features Added During Feature Engineering")
    for group_name, features in FEATURE_CATALOG.items():
        with st.expander(group_name, expanded=False):
            for feature in features:
                st.markdown(f"""
                <div class="feat-card">
                    <div class="feat-name">{feature['name']}</div>
                    <div class="feat-label">{feature['label']}</div>
                    <div class="feat-desc">{feature['description']}</div>
                    <div class="feat-formula-label">Formula:</div>
                    <div class="feat-formula">{feature['formula']}</div>
                </div>
                """, unsafe_allow_html=True)
                
    section_heading("Aggregation Outputs")
    agg_cols = st.columns(3)
    with agg_cols[0]:
        st.markdown("**Monthly features**")
        monthly_preview = load_preview_csv(monthly_path, nrows=3)
        show_cols = [col for col in ["latitude", "longitude", "year", "month", "temperature_2m_mean", "precipitation_sum"] if col in monthly_preview.columns]
        st.dataframe(monthly_preview[show_cols], use_container_width=True, hide_index=True)
    with agg_cols[1]:
        st.markdown("**Seasonal features**")
        seasonal_preview = load_preview_csv(seasonal_path, nrows=3)
        show_cols = [col for col in ["latitude", "longitude", "year", "season", "temperature_2m_mean", "precipitation_sum"] if col in seasonal_preview.columns]
        st.dataframe(seasonal_preview[show_cols], use_container_width=True, hide_index=True)
    with agg_cols[2]:
        st.markdown("**Yearly features**")
        yearly_preview = load_preview_csv(yearly_path, nrows=3)
        show_cols = [col for col in ["latitude", "longitude", "year", "temperature_2m_mean", "precipitation_sum", "wind_speed_120m_mean"] if col in yearly_preview.columns]
        st.dataframe(yearly_preview[show_cols], use_container_width=True, hide_index=True)
    section_heading("Scaling and PCA")
    scaler_info = load_scaler_pca_summary()
    k1, k2, k3 = st.columns(3)
    k1.metric("Features before scaling", scaler_info["feature_count"])
    k2.metric("PCA components kept", scaler_info["reduced_components"])
    k3.metric("Variance retained", f"{scaler_info['variance_retained_pct']:.1f}%" if scaler_info["variance_retained_pct"] is not None else "N/A")
    st.write("Before clustering, the model uses the climate-normal feature table, scales the numeric variables, and compresses them into PCA components. Those PCA components are the direct input to the clustering algorithms.")
    if scaler_info["top_components"]:
        st.dataframe(pd.DataFrame(scaler_info["top_components"]), use_container_width=True, hide_index=True)
    section_heading("Final Model Input")
    st.write("The final input to the clustering models is not raw daily weather. It is a row-per-location climate feature matrix built from long-term climate normals, engineered derived features, seasonal enrichment, scaling, and PCA reduction.")
    st.write(f"- Final selected production model: **{metadata.get('best_algorithm', 'N/A')}**")
    st.write(f"- Saved feature count before PCA: **{len(metadata.get('feature_cols', []))}**")

def _render_how_it_works(clustered_df: pd.DataFrame, comparison_df: pd.DataFrame, metadata: dict):
    section_heading("Data Collection to Model Input", "A step-by-step walkthrough from raw NASA POWER weather records to the final PCA-ready input used by the clustering model.")
    stages = [
        ("Data Collection", ["1,153 valid land points across India", "NASA POWER daily weather data", "15 raw weather parameters"]),
        ("Data Normalization & Cleaning", ["Unified column names", "Removed duplicates", "Filled missing values, capped outliers, enforced physical limits"]),
        ("Feature Engineering", ["Wind extrapolation at 80m, 120m, 180m", "Energy, agriculture, disaster, and urban indicators", "60+ total climate features"]),
        ("Temporal Aggregation", ["Monthly, seasonal, yearly summaries", "Climate normals per location", "Monsoon and seasonality enrichment"]),
        ("Scaling & PCA", ["Standardized climate features", "Reduced dimensionality while retaining ~95% variance", "Prepared stable climate space for clustering"]),
        ("Clustering", ["Compared K-Means, Hierarchical, DBSCAN, HDBSCAN, GMM", "Selected full-coverage production model", f"Final model: {metadata.get('best_algorithm', 'N/A')}"]),
        ("Interpretation & Insights", ["Human-readable climate region labels", "Agriculture, energy, disaster, and urban summaries", "Cluster profiles and nearest examples"]),
        ("Prediction", ["Enter any place name", "Fetch location weather history", "Assign the place to the closest learned climate region"]),
    ]
    for i, (title, bullets) in enumerate(stages):
        num = i + 1
        st.markdown(f"""
            <div class='pip-row'>
                <div class='pip-num'>{num}</div>
                <div>
                    <div class='pip-title'>{title}</div>
                    <div class='pip-desc'>{' • '.join(bullets)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    section_heading("Data Journey")
    left, right = st.columns(2)
    with left:
        st.markdown("""
            <div class="journey-box">
                <h4>Raw Data</h4>
                <ul>
                    <li>1,153 points over India</li>
                    <li>Daily time series</li>
                    <li>15 raw NASA POWER weather variables</li>
                    <li>Needs cleaning, aggregation, and enrichment</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    with right:
        st.markdown(f"""
            <div class="journey-box">
                <h4>Processed Climate Intelligence</h4>
                <ul>
                    <li>{clustered_df['cluster'].nunique()} final climate regions</li>
                    <li>Climate normals per location</li>
                    <li>{len(metadata.get('feature_cols', []))}+ clustering-ready features</li>
                    <li>Ready for sector-specific insights and place prediction</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    section_heading("Stage Explorer")
    st.markdown("#### Data Collection (1,153 locations)")
    st.write("- Source: NASA POWER API")
    st.write("- Grid: 0.5° spacing over India")
    st.write("- Parameters: temperature, rainfall, humidity, solar, wind, pressure, cloud cover")
    st.write("- Time range: 2000-01-01 to 2024-12-31")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### Feature Engineering (60+ features created)")
    st.write("- Wind power density at 80m, 120m, and 180m")
    st.write("- Growing degree days, frost risk, heat stress")
    st.write("- Solar-wind complementarity and solar utilization ratio")
    st.write("- Monsoon share, seasonal contrasts, interannual variability")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("#### Clustering Algorithm Comparison")
    ranking_cols = [col for col in ["algorithm", "n_clusters", "silhouette", "max_cluster_share", "composite_score"] if col in comparison_df.columns]
    st.dataframe(comparison_df[ranking_cols], use_container_width=True, hide_index=True)
    st.write(f"Selected production model: **{metadata.get('best_algorithm', 'N/A')}**")
    section_heading("Feature Importance")
    _render_feature_importance_chart(load_feature_importance())
    _render_pipeline_data_walkthrough(metadata)

def _render_model_training_section(clustered_df: pd.DataFrame, comparison_df: pd.DataFrame, cluster_profiles_df: pd.DataFrame, metadata: dict, prediction: dict | None):
    section_heading("Model Training and Model Outputs", "Compare trained clustering outputs, inspect the final production view, and review alternate saved model results.")
    _render_overview(clustered_df, comparison_df, cluster_profiles_df, metadata, prediction)
