⚡️ Electricity & 🌧️ Weather Analytics Dashboard

A Streamlit-based interactive dashboard analyzing electricity production/consumption (Elhub) and weather conditions (Open-Meteo) for Norwegian price areas NO1–NO5.

A project for IND320 – Data to Decisions (NMBU)

🚀 Features
1. Exploratory Analysis

· Electricity production & consumption (Elhub, hourly)

· Weather timeseries and visualization (Open-Meteo ERA5)

· Interactive filtering by year and price area

2. Quality Checks

· STL decomposition (seasonality & trend)

· Spectrogram frequency analysis

· High-pass (DCT) + SPC outlier detection

· LOF anomaly detection for weather variables

3. Advanced Analysis

· Interactive Folium map with GeoJSON boundaries

· Snow drift estimation

· Sliding-window meteorology ↔ electricity correlation

· SARIMAX forecasting with exogenous weather variables

📊 Data Sources

Electricity — Elhub API

· PRODUCTION_PER_GROUP_MBA_HOUR

· CONSUMPTION_PER_GROUP_MBA_HOUR

Processing Pipeline:
Elhub API → Cassandra → PySpark → MongoDB → Streamlit

🌦 Weather — Open-Meteo (ERA5)

Weather variables used:

· temperature_2m (°C)

· wind_speed_10m (m/s)

· wind_gusts_10m (m/s)

· wind_direction_10m (degrees)

· precipitation (mm)







