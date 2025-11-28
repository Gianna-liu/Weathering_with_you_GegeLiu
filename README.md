# ⚡️ Electricity & 🌧️ Weather Analytics Dashboard
_A project for **IND320 – Data to Decisions (NMBU)**_

A Streamlit-based interactive dashboard analyzing **electricity production/consumption** (Elhub) and **weather conditions** (Open-Meteo) for Norwegian price areas **NO1–NO5**.

Streamlit App link:
🔗 https://weatheringwithyou-gegeliu.streamlit.app/

---

## 📁 Modules

### **📊 Exploratory Analysis**
- Electricity production & consumption (Elhub, hourly)
- Weather time-series visualization (Open-Meteo ERA5)
- Interactive filtering by **year** and **price area**

### **🔍 Quality Checks**
- STL decomposition (seasonality & trend)
- Spectrogram (frequency analysis)
- High-pass (DCT) + SPC outlier detection
- LOF anomaly detection for weather variables

### **🚀 Advanced Analysis**
- Interactive Folium map with GeoJSON boundaries
- Snow drift estimation
- Sliding-window correlation (meteorology ↔ electricity)
- SARIMAX forecasting with optional weather predictors

---

## 📊 Data Sources

### ⚡ **Electricity — Elhub API**
Official API documentation:  
🔗 https://api.elhub.no/energy-data-api  

Datasets used:
- `PRODUCTION_PER_GROUP_MBA_HOUR`
- `CONSUMPTION_PER_GROUP_MBA_HOUR`

### 🌧️ **Weather — Open-Meteo (ERA5)**
Official API documentation:  
🔗 https://open-meteo.com/ 

Variables included:
- `temperature_2m` — °C  
- `wind_speed_10m` — m/s  
- `wind_gusts_10m` — m/s  
- `wind_direction_10m` — degrees  
- `precipitation` — mm  

