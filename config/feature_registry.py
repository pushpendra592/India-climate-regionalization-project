"""
Central registry of all features used in the project.
Single source of truth — every module reads from here.

DATA STRATEGY:
  Open-Meteo (era5): Core hourly weather → aggregated to daily
  NASA POWER:        Solar, soil proxy, specific humidity → daily
  DERIVED:           Wind at heights, indices, flags → computed
"""

# ══════════════════════════════════════════════════════════════
#  NASA POWER DAILY PARAMETERS (fills gaps)
# ══════════════════════════════════════════════════════════════

NASA_POWER_PARAMS = [
    # Solar / Radiation (NASA's unique strength)
    "ALLSKY_SFC_SW_DWN",
    "CLRSKY_SFC_SW_DWN",
    "ALLSKY_KT",
    "ALLSKY_SFC_LW_DWN",
    "ALLSKY_SFC_UV_INDEX",

    # Temperature
    "T2M",
    "T2MDEW",
    "TS",                  # Earth skin temp ≈ soil surface temp

    # Moisture
    "RH2M",
    "QV2M",                # Specific humidity (unique)
    "PRECTOTCORR",

    # Wind
    "WS10M",
    "WD10M",

    # Pressure & Cloud
    "PS",
    "CLOUD_AMT",
]

# ══════════════════════════════════════════════════════════════
#  NASA POWER → Clean Column Name Mapping
# ══════════════════════════════════════════════════════════════

NASA_COLUMN_RENAME = {
    "ALLSKY_SFC_SW_DWN":    "nasa_solar_irradiance_allsky",
    "CLRSKY_SFC_SW_DWN":    "nasa_solar_irradiance_clearsky",
    "ALLSKY_KT":            "nasa_clearness_index",
    "ALLSKY_SFC_LW_DWN":    "nasa_longwave_radiation",
    "ALLSKY_SFC_UV_INDEX":  "nasa_uv_index",
    "T2M":                  "nasa_temperature_2m",
    "T2MDEW":               "nasa_dewpoint_2m",
    "TS":                   "nasa_earth_skin_temperature",
    "RH2M":                 "nasa_relative_humidity",
    "QV2M":                 "nasa_specific_humidity",
    "PRECTOTCORR":          "nasa_precipitation",
    "WS10M":                "nasa_wind_speed_10m",
    "WD10M":                "nasa_wind_direction_10m",
    "PS":                   "nasa_surface_pressure",
    "CLOUD_AMT":            "nasa_cloud_amount",
}

# ══════════════════════════════════════════════════════════════
#  AGGREGATION RULES: Hourly → Daily (Open-Meteo only)
# ══════════════════════════════════════════════════════════════

AGGREGATION_RULES = {
    # Temperature
    "temperature_2m":               ["mean", "max", "min", "std"],
    "apparent_temperature":         ["mean", "max", "min"],
    "dewpoint_2m":                  ["mean", "min"],

    # Moisture
    "relative_humidity_2m":         ["mean", "max", "min"],
    "vapour_pressure_deficit":      ["mean", "max"],

    # Precipitation
    "precipitation":                ["sum", "max"],
    "rain":                         ["sum"],
    "showers":                      ["sum"],
    "snowfall":                     ["sum"],
    "snow_depth":                   ["max", "mean"],

    # Pressure
    "pressure_msl":                 ["mean", "min", "max", "std"],
    "surface_pressure":             ["mean"],

    # Cloud
    "cloud_cover":                  ["mean", "max", "min"],
    "cloud_cover_low":              ["mean"],
    "cloud_cover_mid":              ["mean"],
    "cloud_cover_high":             ["mean"],

    # Wind
    "wind_speed_10m":               ["mean", "max", "std"],
    "wind_direction_10m":           ["mean"],
    "wind_gusts_10m":               ["max"],

    # Solar
    "shortwave_radiation":          ["sum", "max", "mean"],
    "et0_fao_evapotranspiration":   ["sum"],

    # Metadata
    "weather_code":                 ["mode"],
}

# ══════════════════════════════════════════════════════════════
#  BONUS HOURLY DERIVED (computed during aggregation)
# ══════════════════════════════════════════════════════════════

HOURLY_DERIVED_FEATURES = {
    "frost_hours":          "count(temperature_2m < 0) per day",
    "hot_hours":            "count(temperature_2m > 35) per day",
    "comfortable_hours":    "count(18 <= temperature_2m <= 28) per day",
    "precipitation_hours":  "count(precipitation > 0) per day",
    "dry_hours":            "count(precipitation == 0) per day",
    "calm_hours":           "count(wind_speed_10m < 5) per day",
    "strong_wind_hours":    "count(wind_speed_10m > 40) per day",
    "high_humidity_hours":  "count(relative_humidity_2m > 90) per day",
    "low_cloud_hours":      "count(cloud_cover < 20) per day",
    "overcast_hours":       "count(cloud_cover > 80) per day",
}

# ══════════════════════════════════════════════════════════════
#  DERIVED FEATURES (computed in feature engineering phase)
# ══════════════════════════════════════════════════════════════

DERIVED_FEATURES = {
    # ═══ Core (from Open-Meteo aggregated) ═══
    "temp_range_daily": {
        "formula": "temperature_2m_max - temperature_2m_min",
        "unit": "°C",
        "tier": 1,
        "domain": "all",
    },
    "sunshine_fraction": {
        "formula": "low_cloud_hours / 24",
        "unit": "ratio",
        "tier": 1,
        "domain": "energy",
    },
    "precipitation_intensity": {
        "formula": "precipitation_sum / precipitation_hours (where > 0)",
        "unit": "mm/hr",
        "tier": 1,
        "domain": "disaster",
    },
    "cloud_stratification": {
        "formula": "cloud_cover_high_mean - cloud_cover_low_mean",
        "unit": "%",
        "tier": 1,
        "domain": "energy",
    },

    # ═══ Energy: Wind at heights (from 10m extrapolation) ═══
    "wind_speed_80m_mean": {
        "formula": "wind_speed_10m_mean * (80/10)^alpha",
        "unit": "km/h",
        "tier": 2,
        "domain": "energy",
        "note": "alpha=0.14 (open), 0.25 (urban), 0.10 (sea)",
    },
    "wind_speed_120m_mean": {
        "formula": "wind_speed_10m_mean * (120/10)^alpha",
        "unit": "km/h",
        "tier": 2,
        "domain": "energy",
    },
    "wind_speed_180m_mean": {
        "formula": "wind_speed_10m_mean * (180/10)^alpha",
        "unit": "km/h",
        "tier": 2,
        "domain": "energy",
    },
    "wind_power_density_80m": {
        "formula": "0.5 * 1.225 * (wind_speed_80m/3.6)^3",
        "unit": "W/m²",
        "tier": 2,
        "domain": "energy",
    },
    "wind_power_density_120m": {
        "formula": "0.5 * 1.225 * (wind_speed_120m/3.6)^3",
        "unit": "W/m²",
        "tier": 2,
        "domain": "energy",
    },

    # ═══ Energy: Solar ═══
    "solar_utilization_ratio": {
        "formula": "nasa_solar_irradiance_allsky / nasa_solar_irradiance_clearsky",
        "unit": "ratio",
        "tier": 2,
        "domain": "energy",
    },

    # ═══ Agriculture ═══
    "growing_degree_days": {
        "formula": "max(0, temperature_2m_mean - 10)",
        "unit": "°C",
        "tier": 2,
        "domain": "agriculture",
    },
    "soil_temp_proxy": {
        "formula": "nasa_earth_skin_temperature (TS)",
        "unit": "°C",
        "tier": 2,
        "domain": "agriculture",
    },
    "aridity_index": {
        "formula": "precipitation_sum / et0_fao_evapotranspiration_sum",
        "unit": "ratio",
        "tier": 2,
        "domain": "agriculture",
    },

    # ═══ Disaster ═══
    "heavy_rain_flag": {
        "formula": "precipitation_sum > 50",
        "unit": "binary",
        "tier": 1,
        "domain": "disaster",
    },
    "extreme_wind_flag": {
        "formula": "wind_gusts_10m_max > 60",
        "unit": "binary",
        "tier": 1,
        "domain": "disaster",
    },
    "pressure_drop_flag": {
        "formula": "pressure_msl_std > threshold",
        "unit": "binary",
        "tier": 1,
        "domain": "disaster",
    },

    # ═══ Urban ═══
    "thermal_discomfort_hours": {
        "formula": "hot_hours + high_humidity_hours overlap",
        "unit": "hours",
        "tier": 2,
        "domain": "urban",
    },
}

# ══════════════════════════════════════════════════════════════
#  FEATURE METADATA — ALL SOURCES COMBINED
# ══════════════════════════════════════════════════════════════

FEATURE_METADATA = {
    # ═══ Open-Meteo Core (Tier 1) ═══
    "temperature_2m":               {"unit": "°C",     "tier": 1, "source": "normalized_weather", "domain": "all"},
    "apparent_temperature":         {"unit": "°C",     "tier": 1, "source": "normalized_weather", "domain": "urban"},
    "dewpoint_2m":                  {"unit": "°C",     "tier": 1, "source": "normalized_weather", "domain": "all"},
    "relative_humidity_2m":         {"unit": "%",      "tier": 1, "source": "normalized_weather", "domain": "all"},
    "vapour_pressure_deficit":      {"unit": "kPa",    "tier": 1, "source": "normalized_weather", "domain": "all"},
    "precipitation":                {"unit": "mm",     "tier": 1, "source": "normalized_weather", "domain": "all"},
    "rain":                         {"unit": "mm",     "tier": 1, "source": "normalized_weather", "domain": "all"},
    "showers":                      {"unit": "mm",     "tier": 1, "source": "normalized_weather", "domain": "all"},
    "snowfall":                     {"unit": "cm",     "tier": 1, "source": "normalized_weather", "domain": "all"},
    "snow_depth":                   {"unit": "m",      "tier": 1, "source": "normalized_weather", "domain": "disaster"},
    "pressure_msl":                 {"unit": "hPa",    "tier": 1, "source": "normalized_weather", "domain": "all"},
    "surface_pressure":             {"unit": "hPa",    "tier": 1, "source": "normalized_weather", "domain": "all"},
    "cloud_cover":                  {"unit": "%",      "tier": 1, "source": "normalized_weather", "domain": "all"},
    "cloud_cover_low":              {"unit": "%",      "tier": 1, "source": "normalized_weather", "domain": "energy"},
    "cloud_cover_mid":              {"unit": "%",      "tier": 1, "source": "normalized_weather", "domain": "energy"},
    "cloud_cover_high":             {"unit": "%",      "tier": 1, "source": "normalized_weather", "domain": "energy"},
    "wind_speed_10m":               {"unit": "km/h",   "tier": 1, "source": "normalized_weather", "domain": "all"},
    "wind_direction_10m":           {"unit": "°",      "tier": 1, "source": "normalized_weather", "domain": "all"},
    "wind_gusts_10m":               {"unit": "km/h",   "tier": 1, "source": "normalized_weather", "domain": "disaster"},
    "shortwave_radiation":          {"unit": "W/m²",   "tier": 1, "source": "normalized_weather", "domain": "energy"},
    "et0_fao_evapotranspiration":   {"unit": "mm",     "tier": 1, "source": "normalized_weather", "domain": "agriculture"},

    # ═══ NASA POWER (Tier 2 enrichment) ═══
    "nasa_solar_irradiance_allsky":   {"unit": "kWh/m²/day", "tier": 2, "source": "nasa", "domain": "energy"},
    "nasa_solar_irradiance_clearsky": {"unit": "kWh/m²/day", "tier": 2, "source": "nasa", "domain": "energy"},
    "nasa_clearness_index":           {"unit": "ratio",      "tier": 2, "source": "nasa", "domain": "energy"},
    "nasa_longwave_radiation":        {"unit": "kWh/m²/day", "tier": 2, "source": "nasa", "domain": "energy"},
    "nasa_uv_index":                  {"unit": "index",      "tier": 2, "source": "nasa", "domain": "all"},
    "nasa_earth_skin_temperature":    {"unit": "°C",         "tier": 2, "source": "nasa", "domain": "agriculture"},
    "nasa_specific_humidity":         {"unit": "g/kg",       "tier": 2, "source": "nasa", "domain": "all"},
    "nasa_cloud_amount":              {"unit": "%",          "tier": 2, "source": "nasa", "domain": "all"},
}

# ══════════════════════════════════════════════════════════════
#  WIND EXTRAPOLATION CONFIG
# ══════════════════════════════════════════════════════════════

WIND_SHEAR_EXPONENTS = {
    "open_terrain":     0.14,    # Grasslands, open fields
    "rural":            0.20,    # Scattered trees, farms
    "suburban":         0.25,    # Towns, small cities
    "urban":            0.33,    # Dense cities
    "water":            0.10,    # Coastal, offshore
    "default":          0.14,    # When terrain is unknown
}

WIND_EXTRAPOLATION_HEIGHTS = [80, 120, 180]  # meters


# ══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def get_tier1_features() -> list:
    """Return only Tier 1 (core clustering) features."""
    return [k for k, v in FEATURE_METADATA.items() if v["tier"] == 1]


def get_tier2_features(domain: str = None) -> list:
    """Return Tier 2 features, optionally filtered by domain."""
    if domain:
        return [k for k, v in FEATURE_METADATA.items()
                if v["tier"] == 2 and v["domain"] == domain]
    return [k for k, v in FEATURE_METADATA.items() if v["tier"] == 2]


def get_domain_features(domain: str) -> list:
    """Return ALL features for a specific domain (both tiers)."""
    return [
        k for k, v in FEATURE_METADATA.items()
        if v["domain"] in (domain, "all")
    ]


def get_source_features(source: str) -> list:
    """Return features from a specific source."""
    return [k for k, v in FEATURE_METADATA.items() if v["source"] == source]


def get_aggregation_columns() -> list:
    """Return list of all aggregated column names."""
    columns = []
    for param, aggs in AGGREGATION_RULES.items():
        for agg in aggs:
            columns.append(f"{param}_{agg}")
    return columns


