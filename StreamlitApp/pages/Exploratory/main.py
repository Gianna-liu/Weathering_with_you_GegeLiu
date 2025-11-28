import streamlit as st
from tools.utils import apply_theme

apply_theme("blue")

# ---- Init default local session state ---- #
if "expl_price_area" not in st.session_state:
    st.session_state.expl_price_area = "NO1"

if "expl_year" not in st.session_state:
    st.session_state.expl_year = 2021

#  ------------------ Page Title ------------------ 
st.header("Welcome to Exploratory Analysis 👋")
st.write("""
Here you can explore:
- ⚡ Electricity production & consumption distribution
- 📉 Weather time-series plots  

""")

# ------------------ Local page-level controls ------------------ 
st.sidebar.header("Exploratory Analysis Controls")
st.sidebar.info(
    "These settings apply to **all Exploratory subpages**.")
yr = st.sidebar.selectbox(
    "Year",
    [2021, 2022, 2023, 2024],
    key="expl_year",
    index=0
)

pa = st.sidebar.selectbox(
    "Price Area",
    ["NO1", "NO2", "NO3", "NO4", "NO5"],
    key="expl_price_area",
    index=0
)

# ------------------ Local Submenu ------------------ 
option = st.segmented_control(
     "Select an option below to start!",
    ["Electricity", "Weather"],
    default="Electricity"
)

if option == "Electricity":
    st.write("---")
    import pages.Exploratory.energy_plot as page
    page.run()

elif option == "Weather":
    st.write("---")
    import pages.Exploratory.weather_plot as page
    page.run()
