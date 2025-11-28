import streamlit as st
import datetime

st.set_page_config(
    page_title="Energy & Weather Analytics",
    page_icon="⚡",
    layout="wide"
)

# --- Title ---
st.markdown("<h1 style='text-align:center;'>⚡️Electricity & 🌧️ Weather Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:gray;'>Norway Price Areas (NO1–NO5), 2021–2024</h4>", unsafe_allow_html=True)
st.write("")
st.write("")

# --- Description ---
st.markdown("""
This dashboard analyzes **Norwegian electricity production/consumption** (Elhub) and **weather conditions**
(Open-Meteo) across **NO1–NO5 price areas** from 2021–2024.

It is organized into three main modules:
""")

# --- Dark-mode Cards ---
CARD_STYLE = """
    padding:20px;
    border-radius:12px;
    background-color:rgba(255,255,255,0.06);
    border:1px solid rgba(255,255,255,0.15);
    color:#EEEEEE;
"""

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="{CARD_STYLE}">
        <h3 style="color:#82B1FF;">1.Exploratory Analysis</h3>
        <p>Explore patterns, distributions in electricity and weather data.</p>
        <b>Includes:</b>
        <ul>
            <li>Electricity Exploration</li>
            <li>Weather Exploration</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="{CARD_STYLE}">
        <h3 style="color:#FFAB91;">2.Quality Checks</h3>
        <p>Detect outliers, and seasonal behaviors and validate data integrity.</p>
        <b>Includes:</b>
        <ul>
            <li>Electricity Quality</li>
            <li>Weather Quality</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="{CARD_STYLE}">
        <h3 style="color:#A5D6A7;">3.Advanced Analysis</h3>
        <p>Combine weather and electricity for correlation, forecasting, and map-based analysis.</p>
        <b>Includes:</b>
        <ul>
            <li>Map Analysis</li>
            <li>Snow Drift Analysis</li>
            <li>Weather–Electricity Correlation</li>
            <li>Forecasting Models</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #111111;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: #DDDDDD !important;
}

/* Active menu item */
div[data-testid="stSidebar"] button[aria-current="page"] {
    background-color: #333333 !important;
    color: white !important;
    border-radius: 6px;
}

/* Hover effect */
div[data-testid="stSidebar"] button:hover {
    background-color: #444444 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("### 🚩 Data Sources")

with st.expander("Show details"):
    st.markdown("""
###  **⚡️Electricity Data — Elhub API**  
Elhub API provides hourly electricity production and consumption data:  
- `PRODUCTION_PER_GROUP_MBA_HOUR`
- `CONSUMPTION_PER_GROUP_MBA_HOUR`

**Processing pipeline:**
1. Downloaded via Elhub API  
2. Stored in **Cassandra**  
3. Transformed locally using **PySpark**  
4. Exported and stored in **MongoDB** for using in Streamlit  

**Price Areas (NO1–NO5) and representative locations:**
- **NO1 — Oslo**  
- **NO2 — Kristiansand**  
- **NO3 — Trondheim**  
- **NO4 — Tromsø**  
- **NO5 — Bergen**  
---

### 🌦️ **Weather Data - Open-Meteo API**  
Weather variables are retrieved using the **Open-Meteo Historical API**, based on the **ECMWF ERA5 reanalysis model**.
                
**Weather variables included:**
- `temperature_2m` — Air temperature at 2 meters (**°C**) 
- `wind_speed_10m` — Mean wind speed at 10 meters (**m/s**)  
- `wind_gusts_10m` — Maximum wind gust at 10 meters (**m/s**)  
- `wind_direction_10m` — Wind direction (**degrees**)  
- `precipitation` — Total precipitation (**mm**)  

Data is queried per latitude/longitude for each city in NO1–NO5. 
                    """) 

st.markdown("### 📚 Project Background")
                
with st.expander("Show details"):
    st.markdown("""
    This project is part of the **IND320 – Data to Decisions** course at **NMBU**.  
    It integrates:
    - Exploratory Analysis
    - Interactive Visualization
    - Outlier and Anomaly Detection (DCT, SPC, LOF, Spectrograms, STL, etc.)  
    - Sliding Window Correlation  
    - Time-series Forecasting (SARIMAX)
                
    The dashboard is built using **Streamlit** for interactive exploration.

    **Developed by:** Gege Liu (Master Student, NMBU)
                
    **GitHub Repo:** https://github.com/Gianna-liu/IND320_dashboard_GegeLiu
    """)