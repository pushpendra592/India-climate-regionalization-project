"""
Feature catalog: name, label, description, and formula for every engineered feature.
Used by the pipeline walkthrough section of the dashboard.
"""

FEATURE_CATALOG = {
    "Core Derived Features": [
        {
            "name": "temp_range_daily",
            "label": "Daily Temperature Range",
            "description": "Measures how much the temperature swings between day and night. High values indicate continental-style climates; low values indicate coastal or cloud-buffered regions.",
            "formula": "T_max - T_min",
        },
        {
            "name": "humidity_range",
            "label": "Daily Humidity Range",
            "description": "The spread between maximum and minimum relative humidity in a day. Captures how dry the air becomes at its driest point relative to its most humid.",
            "formula": "RH_max - RH_min",
        },
        {
            "name": "pressure_range",
            "label": "Daily Pressure Range",
            "description": "Difference between the highest and lowest mean-sea-level pressure recorded in a day. Larger ranges can signal frontal or storm activity.",
            "formula": "P_msl_max - P_msl_min",
        },
        {
            "name": "cloud_stratification",
            "label": "Cloud Stratification",
            "description": "Vertical contrast between high-altitude and low-altitude cloud cover. Positive values mean more high cloud than low cloud, typical of convective systems.",
            "formula": "cloud_cover_high - cloud_cover_low",
        },
        {
            "name": "sunshine_fraction",
            "label": "Sunshine Fraction",
            "description": "Proportion of the day with minimal low cloud obstruction. Used as a proxy for actual sunshine hours when direct solar data is unavailable.",
            "formula": "low_cloud_hours / 24",
        },
        {
            "name": "precipitation_intensity",
            "label": "Precipitation Intensity",
            "description": "Average rainfall rate during hours when it actually rains. Distinguishes between light drizzle spread over many hours versus heavy bursts.",
            "formula": "precip_sum / precip_hours  (0 when precip_hours = 0)",
        },
    ],
    "Wind Extrapolation": [
        {
            "name": "wind_speed_80m_mean",
            "label": "Wind Speed at 80 m",
            "description": "Wind speed estimated at 80 m hub height using the wind power law. Relevant for small to mid-scale wind turbine assessment.",
            "formula": "WS_10m x (80 / 10)^alpha  (alpha = 0.143 default)",
        },
        {
            "name": "wind_speed_120m_mean",
            "label": "Wind Speed at 120 m",
            "description": "Wind speed at the hub height of modern utility-scale onshore turbines. Primary wind energy assessment metric in this project.",
            "formula": "WS_10m x (120 / 10)^alpha",
        },
        {
            "name": "wind_speed_180m_mean",
            "label": "Wind Speed at 180 m",
            "description": "Wind speed at the hub height of the largest current offshore turbine designs. Indicates high-altitude wind resource potential.",
            "formula": "WS_10m x (180 / 10)^alpha",
        },
        {
            "name": "wind_shear_coefficient",
            "label": "Wind Shear Coefficient",
            "description": "How steeply wind speed increases with altitude. High shear means turbines gain significantly more energy at height. Computed from the 10 m and 120 m estimates.",
            "formula": "log(WS_120m / WS_10m) / log(120 / 10)  (when both > 0)",
        },
    ],
    "Energy Features": [
        {
            "name": "wind_power_density_80m",
            "label": "Wind Power Density at 80 m",
            "description": "Kinetic energy available per unit rotor area at 80 m. Scales with the cube of wind speed, so small wind gains produce large power gains.",
            "formula": "0.5 x 1.225 x (WS_80m / 3.6)^3   [W/m^2]",
        },
        {
            "name": "wind_power_density_120m",
            "label": "Wind Power Density at 120 m",
            "description": "Standard metric for utility-scale wind energy site screening. The 1.225 kg/m^3 value assumes sea-level air density.",
            "formula": "0.5 x 1.225 x (WS_120m / 3.6)^3   [W/m^2]",
        },
        {
            "name": "wind_power_density_180m",
            "label": "Wind Power Density at 180 m",
            "description": "High-altitude wind resource metric for next-generation turbine planning.",
            "formula": "0.5 x 1.225 x (WS_180m / 3.6)^3   [W/m^2]",
        },
        {
            "name": "solar_utilization_ratio",
            "label": "Solar Utilization Ratio",
            "description": "How much of the theoretical clear-sky solar irradiance actually reaches the surface on average. A value near 1 indicates consistently clear skies.",
            "formula": "solar_allsky / solar_clearsky  (0 when clearsky = 0)",
        },
        {
            "name": "solar_wind_complementarity",
            "label": "Solar-Wind Complementarity",
            "description": "Captures whether solar and wind are negatively correlated at a location. Positive values mean when wind is low, solar is high, and vice versa — ideal for hybrid plant planning.",
            "formula": "-(solar_normalized x wind_normalized)",
        },
    ],
    "Agriculture Features": [
        {
            "name": "growing_degree_days",
            "label": "Growing Degree Days",
            "description": "Accumulated heat above the 10 C base temperature that drives crop development. Higher values indicate longer or warmer growing seasons.",
            "formula": "max(0, T_mean - 10)",
        },
        {
            "name": "frost_risk",
            "label": "Frost Risk Flag",
            "description": "Binary indicator that nighttime temperature dropped below freezing. Used to count frost days per year during aggregation.",
            "formula": "1 if T_min < 0 C  else 0",
        },
        {
            "name": "heat_stress",
            "label": "Heat Stress Flag",
            "description": "Binary indicator that daytime temperature exceeded 40 C, a threshold beyond which most crops suffer productivity loss.",
            "formula": "1 if T_max > 40 C  else 0",
        },
        {
            "name": "aridity_index",
            "label": "Aridity Index",
            "description": "Ratio of rainfall to potential evapotranspiration. Values below 0.5 indicate arid to semi-arid conditions where irrigation is typically required.",
            "formula": "precip_sum / ET0_fao  (NaN when ET0 = 0)",
        },
        {
            "name": "soil_temp_proxy",
            "label": "Soil Temperature Proxy",
            "description": "NASA surface skin temperature used as a proxy for shallow soil temperature. Influences seed germination thresholds and root-zone activity.",
            "formula": "T_skin  (NASA EARTH_SKIN_TEMP parameter)",
        },
        {
            "name": "soil_air_temp_diff",
            "label": "Soil-Air Temperature Difference",
            "description": "How much warmer or cooler the soil surface is relative to the air. Useful for identifying areas with strong radiative heating or cooling.",
            "formula": "T_skin - T_2m_mean",
        },
    ],
    "Disaster Risk Features": [
        {
            "name": "heavy_rain_flag",
            "label": "Heavy Rain Flag",
            "description": "Binary flag marking days with more than 50 mm of rainfall, the standard threshold for heavy precipitation alerts in India.",
            "formula": "1 if precip_sum > 50 mm  else 0",
        },
        {
            "name": "extreme_rain_flag",
            "label": "Extreme Rain Flag",
            "description": "Binary flag for days exceeding 100 mm of rainfall — classified as very heavy rain by the India Meteorological Department.",
            "formula": "1 if precip_sum > 100 mm  else 0",
        },
        {
            "name": "extreme_wind_flag",
            "label": "Extreme Wind Flag",
            "description": "Binary flag for days when wind gusts exceed 60 km/h, sufficient to cause minor structural damage and disrupt outdoor activities.",
            "formula": "1 if wind_gust_max > 60 km/h  else 0",
        },
        {
            "name": "storm_wind_flag",
            "label": "Storm Wind Flag",
            "description": "Binary flag for days with gale-force wind gusts above 90 km/h, associated with cyclones and severe thunderstorms.",
            "formula": "1 if wind_gust_max > 90 km/h  else 0",
        },
        {
            "name": "pressure_instability",
            "label": "Pressure Instability Flag",
            "description": "Flags days where intra-day pressure variation exceeds 5 hPa, indicating passage of fronts or mesoscale convective systems.",
            "formula": "1 if pressure_msl_std > 5 hPa  else 0",
        },
        {
            "name": "flood_risk_indicator",
            "label": "Flood Risk Indicator",
            "description": "Composite signal combining heavy rain occurrence with rainfall duration. Longer heavy rain events have greater runoff and waterlogging potential.",
            "formula": "heavy_rain_flag x precip_hours",
        },
    ],
    "Urban Planning Features": [
        {
            "name": "thermal_stress_index",
            "label": "Thermal Stress Index",
            "description": "Difference between how hot it feels (apparent temperature) and the actual measured air temperature. Larger positive values indicate high humidity or wind-driven heat stress.",
            "formula": "T_apparent_mean - T_2m_mean",
        },
        {
            "name": "outdoor_comfort_score",
            "label": "Outdoor Comfort Score",
            "description": "Composite index combining hours that are thermally comfortable, dry, and calm. Normalized to a 0-1 scale over a 72-hour reference window.",
            "formula": "(comfortable_hours + dry_hours + calm_hours) / 72",
        },
        {
            "name": "heat_island_potential",
            "label": "Heat Island Potential",
            "description": "Index indicating susceptibility to urban heat island effects. High hot hours, low wind, and minimal cloud cover create conditions where urban surfaces retain heat.",
            "formula": "(hot_hours + calm_hours + low_cloud_hours) / 72",
        },
    ],
    "Seasonal and Monsoon Enrichment": [
        {
            "name": "monsoon_rainfall_share",
            "label": "Monsoon Rainfall Share",
            "description": "Fraction of total annual precipitation that falls during the June-September monsoon season. India's rainfall is highly seasonal, and this metric captures that dependency.",
            "formula": "rain_JJA / rain_annual",
        },
        {
            "name": "pre_monsoon_heat_contrast",
            "label": "Pre-Monsoon Heat Contrast",
            "description": "Temperature difference between the pre-monsoon (April-May) and monsoon (June-September) seasons. Captures the heat build-up before the monsoon onset.",
            "formula": "Derived from seasonal aggregation: T_mean(AMJ) - T_mean(JJAS)",
        },
        {
            "name": "seasonal_humidity_contrast",
            "label": "Seasonal Humidity Contrast",
            "description": "Humidity difference between the wettest and driest seasons. High contrast indicates a strongly seasonal moisture regime.",
            "formula": "Derived from seasonal aggregation: RH_mean(wet season) - RH_mean(dry season)",
        },
        {
            "name": "seasonal_wind_contrast",
            "label": "Seasonal Wind Contrast",
            "description": "Wind speed difference between the windiest and calmest seasons. Captures the monsoon wind reversal characteristic of the Indian subcontinent.",
            "formula": "Derived from seasonal aggregation: WS_mean(max season) - WS_mean(min season)",
        },
        {
            "name": "seasonal_cloud_contrast",
            "label": "Seasonal Cloud Contrast",
            "description": "Difference in cloud cover between the cloudiest and clearest seasons. Reflects the seasonal transition from clear winter skies to overcast monsoon conditions.",
            "formula": "Derived from seasonal aggregation: cloud_mean(max) - cloud_mean(min)",
        },
        {
            "name": "winter_to_monsoon_solar_ratio",
            "label": "Winter-to-Monsoon Solar Ratio",
            "description": "How much more solar irradiance a location receives in winter compared to the monsoon. High values indicate the monsoon heavily suppresses solar generation.",
            "formula": "solar_mean(DJF) / solar_mean(JJAS)",
        },
        {
            "name": "rainfall_seasonality_index",
            "label": "Rainfall Seasonality Index",
            "description": "Measure of how concentrated annual rainfall is within a few months. Scores near 1 indicate extremely seasonal rainfall; near 0 indicates year-round rain.",
            "formula": "Derived from monthly aggregation: coefficient of variation of monthly precipitation",
        },
        {
            "name": "annual_temp_cycle_range",
            "label": "Annual Temperature Cycle Range",
            "description": "Difference between the warmest and coldest month mean temperatures. Captures the strength of the annual temperature cycle — largest in continental interiors.",
            "formula": "T_mean(hottest month) - T_mean(coldest month)",
        },
    ],
}
