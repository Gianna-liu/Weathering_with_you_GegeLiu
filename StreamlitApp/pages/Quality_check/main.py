import streamlit as st
from tools.utils import apply_theme

apply_theme("gray")

# -------------------- Sidebar Controls --------------------
st.sidebar.header("Quality Check Controls")
st.sidebar.info("These settings apply to all Quality Check subpages.")

if "qc_year" not in st.session_state:
    st.session_state.qc_year = 2021

if "qc_price_area" not in st.session_state:
    st.session_state.qc_price_area = "NO1"

yr = st.sidebar.selectbox(
    "Year",
    [2021, 2022, 2023, 2024],
    key="qc_year",
)

pa = st.sidebar.selectbox(
    "Price Area",
    ["NO1", "NO2", "NO3", "NO4", "NO5"],
    key="qc_price_area",
)

# -------------------- Main Page --------------------
st.subheader("🔍 Data Quality & Anomaly Detection")
st.write("""
This section contains analysis for detecting anomalies and inspecting data quality:
- 📉 **STL decomposition** of electricity production  
- 🎧 **Spectrogram** for frequency-domain analysis  
- ⚠️ **High-pass (DCT) + Statistical Process Control (SPC)** outlier detection for selected weather variable  
- 🔍 **Local Outlier Factor (LOF) anomaly detection** for selected weather variable  

""")

# -------------------- Local Submenu --------------------
option = st.segmented_control(
    "Select an option below to start!",
    ["Electricity", "Weather"],
    default="Electricity"
)

if option == "Electricity":
    import pages.Quality_check.production_quality as page
    page.run()

elif option == "Weather":
    import pages.Quality_check.weather_quality as page
    page.run()
