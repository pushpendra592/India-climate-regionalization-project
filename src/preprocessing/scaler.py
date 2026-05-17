"""
Feature scaling and dimensionality reduction for clustering.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA
from src.utils.logger import get_logger

logger = get_logger("scaler")


class FeatureScaler:
    """
    Scales features for clustering. Different algorithms need different scaling.

    Usage:
        scaler = FeatureScaler(method="standard")
        X_scaled = scaler.fit_transform(df, feature_cols)
        X_new = scaler.transform(new_df)
    """

    SCALERS = {
        "standard": StandardScaler,       # K-Means, GMM
        "minmax": MinMaxScaler,           # When bounded [0,1] needed
        "robust": RobustScaler,           # DBSCAN (handles outliers better)
    }

    def __init__(self, method: str = "standard"):
        if method not in self.SCALERS:
            raise ValueError(f"Unknown method: {method}. Use: {list(self.SCALERS.keys())}")

        self.method = method
        self.scaler = self.SCALERS[method]()
        self.feature_cols = None
        self.is_fitted = False

    def fit_transform(
        self,
        df: pd.DataFrame,
        feature_cols: list = None,
        exclude_cols: list = None,
    ) -> np.ndarray:
        """
        Fit scaler and transform data.

        Args:
            df: Input DataFrame
            feature_cols: Columns to scale (if None, uses all numeric)
            exclude_cols: Columns to exclude

        Returns:
            Scaled numpy array
        """
        exclude = set(exclude_cols or ["latitude", "longitude", "date", "year", "month", "season"])

        if feature_cols is None:
            feature_cols = [
                c for c in df.select_dtypes(include=[np.number]).columns
                if c not in exclude
            ]

        usable_feature_cols = []
        dropped_all_nan = []
        for col in feature_cols:
            if df[col].notna().any():
                usable_feature_cols.append(col)
            else:
                dropped_all_nan.append(col)

        if dropped_all_nan:
            logger.warning(
                f"Skipping {len(dropped_all_nan)} all-NaN features before scaling"
            )

        if not usable_feature_cols:
            raise ValueError("No usable numeric features available for scaling.")

        self.feature_cols = usable_feature_cols
        X = df[usable_feature_cols].values.copy()

        # Handle any remaining NaN
        nan_count = np.isnan(X).sum()
        if nan_count > 0:
            logger.warning(f"⚠️  {nan_count} NaN values found — filling with column median")
            col_medians = np.nanmedian(X, axis=0)
            for i in range(X.shape[1]):
                if np.isnan(col_medians[i]):
                    col_medians[i] = 0.0
                mask = np.isnan(X[:, i])
                X[mask, i] = col_medians[i]

        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True

        logger.info(
            f"📐 Scaled {len(usable_feature_cols)} features using {self.method} | "
            f"Shape: {X_scaled.shape}"
        )

        return X_scaled

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform new data using fitted scaler."""
        if not self.is_fitted:
            raise ValueError("Scaler not fitted. Call fit_transform first.")

        X = df[self.feature_cols].values
        return self.scaler.transform(X)

    def get_feature_names(self) -> list:
        """Return feature column names."""
        return self.feature_cols

    def inverse_transform(self, X_scaled: np.ndarray) -> pd.DataFrame:
        """Convert scaled data back to original scale."""
        X_original = self.scaler.inverse_transform(X_scaled)
        return pd.DataFrame(X_original, columns=self.feature_cols)


class DimensionalityReducer:
    """
    Reduces feature dimensions for visualization and clustering.

    Usage:
        reducer = DimensionalityReducer()
        X_reduced = reducer.fit_pca(X_scaled, n_components=0.95)
    """

    def __init__(self):
        self.pca = None
        self.n_components = None

    def fit_pca(
        self,
        X: np.ndarray,
        n_components: float = 0.95,
        feature_names: list = None,
    ) -> np.ndarray:
        """
        Apply PCA for dimensionality reduction.

        Args:
            X: Scaled feature matrix
            n_components: Variance to retain (0.95 = 95%) or exact number

        Returns:
            Reduced feature matrix
        """
        self.pca = PCA(n_components=n_components)
        X_reduced = self.pca.fit_transform(X)
        self.n_components = self.pca.n_components_

        logger.info(
            f"📉 PCA: {X.shape[1]} → {self.n_components} components | "
            f"Variance retained: {self.pca.explained_variance_ratio_.sum()*100:.1f}%"
        )

        # Log top contributing features per component
        if feature_names:
            for i in range(min(3, self.n_components)):
                top_features = np.argsort(np.abs(self.pca.components_[i]))[::-1][:5]
                top_names = [feature_names[j] for j in top_features]
                variance = self.pca.explained_variance_ratio_[i] * 100
                logger.info(
                    f"   PC{i+1} ({variance:.1f}%): {top_names}"
                )

        return X_reduced

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform new data."""
        return self.pca.transform(X)

    def get_explained_variance(self) -> np.ndarray:
        """Return explained variance ratio per component."""
        return self.pca.explained_variance_ratio_
