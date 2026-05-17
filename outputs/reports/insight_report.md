# Weather Pattern Clustering Insight Report

## Agriculture

cluster,points,temperature_2m_mean_mean,growing_degree_days_mean,precipitation_sum_mean,relative_humidity_2m_mean_mean,shortwave_radiation_sum_mean,frost_risk_mean,heat_stress_mean,temperature_stability_mean,rainfall_reliability_mean,agriculture_suitability_score,agriculture_summary,agriculture_recommendation
0,135,25.539,15.539,2.201,69.919,17.607,0.0,0.0,0.733,0.011,0.638,balanced-growing-conditions,Balanced conditions for diversified cropping and stable seasonal planning.
6,200,26.227,16.227,1.612,66.059,19.212,0.0,0.0,0.721,0.009,0.608,balanced-growing-conditions,Balanced conditions for diversified cropping and stable seasonal planning.
4,231,26.056,16.056,1.465,55.612,18.734,0.0,0.0,0.708,0.012,0.581,balanced-growing-conditions,Balanced conditions for diversified cropping and stable seasonal planning.
3,89,20.132,10.276,2.61,75.883,14.982,0.0,0.0,0.731,0.008,0.559,"rain-supported, humid-growing-zone",Good fit for rain-fed agriculture with drainage planning.
5,222,25.714,15.714,1.385,51.769,17.479,0.0,0.0,0.639,0.014,0.513,balanced-growing-conditions,Balanced conditions for diversified cropping and stable seasonal planning.


## Energy

cluster,points,shortwave_radiation_sum_mean,wind_speed_120m_mean_mean,wind_power_density_120m_mean,solar_utilization_ratio_mean,solar_wind_complementarity_mean,cloud_cover_mean_mean,energy_potential_score,resource_mix,energy_summary,energy_recommendation
2,139,19.761,5.06,1.756,0.546,-0.758,33.793,0.696,Solar-Led,solar-favored,Best suited for utility-scale solar with cloud-aware generation planning.
6,200,19.212,5.624,2.443,0.515,-0.874,50.961,0.696,Hybrid Solar-Wind,"solar-favored, wind-favored",Strong candidate for hybrid renewable parks with storage integration.
4,231,18.734,4.808,1.502,0.528,-0.255,44.402,0.566,Solar-Led,moderate-renewable-potential,Best suited for utility-scale solar with cloud-aware generation planning.
1,49,18.436,4.752,1.76,0.459,-0.22,66.756,0.477,Balanced Renewable,moderate-renewable-potential,Moderate multi-source renewable potential with balanced deployment options.
5,222,17.479,4.101,0.91,0.567,-0.134,42.252,0.442,Balanced Renewable,hybrid-friendly,Moderate multi-source renewable potential with balanced deployment options.


## Disaster Risk

cluster,points,heavy_rain_flag_mean,extreme_rain_flag_mean,precipitation_sum_mean,precipitation_sum_interannual_std_mean,wind_speed_120m_mean_mean,wind_power_density_120m_mean,cloud_cover_mean_interannual_std_mean,relative_humidity_2m_mean_mean,solar_utilization_ratio_mean,disaster_risk_score,dominant_hazard,disaster_summary,risk_recommendation
1,49,0.0,0.0,0.704,73.783,4.752,1.76,9.651,62.354,0.459,0.533,High Wind Exposure,lower-observed-extreme-risk,Strengthen wind-resilient design standards and network reliability planning.
6,200,0.0,0.0,1.612,105.705,5.624,2.443,3.28,66.059,0.515,0.519,High Wind Exposure,storm-exposed,Strengthen wind-resilient design standards and network reliability planning.
3,89,0.0,0.0,2.61,125.74,2.31,0.209,3.707,75.883,0.515,0.505,Heavy Rain / Flooding,flood-prone,"Prioritize drainage, runoff management, and flood-resilient infrastructure."
2,139,0.0,0.0,0.808,80.139,5.06,1.756,6.261,42.983,0.546,0.485,High Wind Exposure,lower-observed-extreme-risk,Strengthen wind-resilient design standards and network reliability planning.
0,135,0.0,0.0,2.201,92.006,3.903,0.823,3.391,69.919,0.532,0.464,Heavy Rain / Flooding,lower-observed-extreme-risk,"Prioritize drainage, runoff management, and flood-resilient infrastructure."


## Urban Planning

cluster,points,temperature_2m_mean_mean,relative_humidity_2m_mean_mean,wind_speed_10m_mean_mean,cloud_cover_mean_mean,shortwave_radiation_sum_mean,temperature_2m_mean_interannual_std_mean,thermal_stress_index_mean,outdoor_comfort_score_mean,heat_island_potential_mean,urban_comfort_score,urban_summary,urban_recommendation
5,222,25.714,51.769,2.896,42.252,17.479,0.566,0.381,0.868,0.111,2.869,outdoor-friendly,Suitable for public-space activation and walkable urban design.
4,231,26.056,55.612,3.395,44.402,18.734,0.412,0.457,0.879,0.136,2.787,outdoor-friendly,Suitable for public-space activation and walkable urban design.
0,135,25.539,69.919,2.756,53.414,17.607,0.364,0.588,0.811,0.047,2.562,outdoor-friendly,Suitable for public-space activation and walkable urban design.
6,200,26.227,66.059,3.972,50.961,19.212,0.387,0.548,0.787,0.124,2.352,outdoor-friendly,Suitable for public-space activation and walkable urban design.
1,49,-2.59,62.354,3.356,66.756,18.436,0.276,0.0,0.489,0.022,1.912,moderate-urban-comfort,Moderate comfort profile; use mixed passive cooling and open-space strategies.

