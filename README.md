# Weather Pattern Clustering

Weather Pattern Clustering for Localised Climate Insight Generation is an end-to-end unsupervised learning project focused on India-first climate segmentation. It now uses NASA POWER historical weather data, engineers weather and domain features, compares multiple clustering algorithms, and turns the resulting patterns into agriculture, energy, disaster-risk, and urban-planning insights.

## What This Project Does

- Builds a systematic latitude/longitude grid over the study region.
- Filters the grid to land points using a boundary mask.
- Collects historical weather data from NASA POWER.
- Cleans, normalizes, and engineers climate features at daily and aggregated timescales.
- Generates climate normals suitable for clustering.
- Compares K-Means, Hierarchical, DBSCAN, HDBSCAN, and GMM clustering approaches.
- Produces cluster profiles and domain-specific insight tables.
- Predicts the learned climate cluster for an exact latitude/longitude or supported city.
- Exposes a simple Streamlit dashboard for interactive lookup.

## Project Structure

- `config/`: region settings, feature registry, and global configuration.
- `src/data_collection/`: grid generation, land masking, API clients, validation.
- `src/location/`: supported city lookup for user-friendly prediction input.
- `src/prediction/`: reusable exact-location prediction logic.
- `src/preprocessing/`: merge, clean, aggregate, and feature engineering logic.
- `src/clustering/`: clustering algorithms, evaluation, optimization, and comparison.
- `src/insights/`: domain-specific insight generators.
- `pipelines/`: orchestration entrypoints for collection, preprocessing, clustering, and insights.
- `dashboard/`: Streamlit app for cluster exploration and city or coordinate prediction.
- `data/`: raw, interim, processed, and external artifacts.
- `outputs/`: reports, saved models, figures, and tables.

## Pipeline Order

1. `pipelines/data_pipeline.py`
2. `pipelines/preprocessing_pipeline.py`
3. `pipelines/clustering_pipeline.py`
4. `pipelines/insight_pipeline.py`
5. `pipelines/predict_location.py`

## Current Notes

- The workspace already contains sample raw and processed artifacts.
- The pipeline code now uses CSV-only dataset storage for interim and processed tables.
- For better India coverage on limited runs, `data_pipeline.py` now defaults to geographically stratified point selection instead of just taking the first `N` grid cells.
- Use `python pipelines\predict_location.py --list-cities` to see supported city names.
- Launch the dashboard with `streamlit run dashboard\app.py`.
- A compatible local Python 3.11 scientific environment is still needed to execute the full stack because the checked-in packages were built for CPython 3.11.
