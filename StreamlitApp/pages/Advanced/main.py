import streamlit as st
from tools.utils import apply_theme

apply_theme("purple")

# ------------------- Main Page -------------------
st.header("🚀 Advanced Analysis")
st.write("""
This section provides advanced methods for spatial analysis, correlation analysis, and predictive analyses, including:
- 🗺 **Map-based spatial analysis**
- ❄️ **Snow drift estimation**
- 🔗 **Meteorology ↔ Electricity correlation**
- 📈 **Forecasting (SARIMAX)**  
""")

# ------------------- Local Submenu -------------------
option = st.segmented_control(
     "Select an option below to start!",
    ["Map", "Snow Drift", "Correlation", "Forecasting"],
    default="Map"
)
st.write("---")

if option == "Map":
    import pages.Advanced.map_area as page
    page.run()

elif option == "Snow Drift":
    import pages.Advanced.snow_drift as page
    page.run()

elif option == "Correlation":
    import pages.Advanced.correlation as page
    page.run()

elif option == "Forecasting":
    import pages.Advanced.forecasting as page
    page.run()
