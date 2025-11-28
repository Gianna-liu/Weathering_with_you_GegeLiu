⚡️ Electricity & 🌧️ Weather Analytics Dashboard

Norway Price Areas (NO1–NO5), 2021–2024

A Streamlit-based interactive dashboard analyzing electricity production/consumption (Elhub) and weather conditions (Open-Meteo) for Norwegian price areas NO1–NO5.

A project for IND320 – Data to Decisions (NMBU)

📌 Overview

This Streamlit dashboard combines electricity data (Elhub) and weather data (Open-Meteo ERA5) to explore patterns, detect anomalies, analyze spatial behavior, and perform forecasting across Norway’s five price areas (NO1–NO5).
The app includes:

Exploratory analysis of electricity and weather
Quality checks (STL, spectrograms, DCT+SPC, LOF)
Advanced analysis (map visualization, snow drift, correlation, forecasting)

🗂 Modules
1️⃣ Exploratory Analysis
    Interactive plots for electricity production/consumption and weather time-series.

2️⃣ Quality Check
  Tools for detecting outliers and anomalies using:
  STL decomposition
  Spectrograms
  High-pass DCT + SPC
  Local Outlier Factor (LOF)

3️⃣ Advanced Analysis

  Map-based price area analysis
  Snow drift estimation
  Weather–energy correlation
  SARIMAX forecasting

📡 Data Sources
⚡ Electricity (Elhub API)
Hourly production & consumption
Processed through Cassandra → PySpark → MongoDB

🌦 Weather (Open-Meteo ERA5)
Variables include:
temperature_2m, wind_speed_10m, wind_gusts_10m,
wind_direction_10m, precipitation

Representative cities:
NO1: Oslo, NO2: Kristiansand, NO3: Trondheim, NO4: Tromsø, NO5: Bergen
