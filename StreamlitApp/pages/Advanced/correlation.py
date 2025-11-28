import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from tools.widgets import render_time_controls, get_time_range
from tools.utils import load_data_fromAPI, get_basic_info,load_data_fromAPI,get_elhub_data,plot_lag_window_center
from datetime import datetime


def run():
    st.markdown(f"### ⚡ Meteorology ↔ Energy Correlation Explorer")

    # --------------------- Select price area and get coordinates ---------------------
    # Map page may have stored: st.session_state.selected_area_name = "NO1"
    st.markdown(f"#### 📍 Selected Price Area")

    if "selected_area_name" not in st.session_state:
        st.session_state.selected_area_name = "NO1"

    if "last_pin" not in st.session_state:
        st.session_state.last_pin = [59.9127, 10.7461]
    
    st.info(
    "This page automatically uses the selection from the **Map** page.\n\n"
    "**No map selection found?**\n"
    "We applied a default: **NO1 (Oslo)** with coordinates **59.9127, 10.7461**.\n\n"
    "To change the area or location, please return to the Map page."
)


    # 2. Get selection
    defined_area = st.session_state.selected_area_name
    lat, lon     = st.session_state.last_pin     # (lat, lon)

    # 3. Show current selection
    st.write(f"**Area:** {defined_area}")
    st.write(f"**Coordinates:** {lat:.4f}, {lon:.4f}")


    # --------------------- Select year and month for correlation analysis --------------------- 
    st.markdown(f"#### ⏳ Select a Monthly Time Range")
    col_year, col_month = st.columns(2)
    with col_year:
        defined_year = st.selectbox("Year", [2021, 2022, 2023, 2024], index=3)

    with col_month:
        defined_month = st.selectbox("Month", list(range(1, 13)), format_func=lambda x: f"{x:02d}")


    start_dt = pd.to_datetime(f"{defined_year}-{defined_month:02d}-01")
    end_dt   = start_dt + pd.offsets.MonthEnd(0)
    st.write(f"**Selected time range:** {start_dt.strftime('%Y-%m-%d')} → {end_dt.strftime('%Y-%m-%d')}")

    # Load weather data
    weather_df = load_data_fromAPI(lon, lat, selected_year=defined_year)

    if weather_df is None or weather_df.empty:
        st.warning("No data returned for this location/year.")
        st.stop()

    # Select meteorological variable
    meteo_options = {
        "Temperature (2m)": "temperature_2m",
        "Wind speed (10m)": "wind_speed_10m",
        "Wind gust (10m)": "wind_gusts_10m",
        "Precipitation": "precipitation",
    }
    # Arrange the selectbox of meteorological variables and selectbox of energy variables in the same line
    col1, col2 = st.columns(2)
    with col1:
    # set the default selected option to "Temperature (2m)"
        selected_meteo_label = col1.selectbox("Select meteorological variable", meteo_options.keys(), index=0)
        selected_meteo_col = meteo_options[selected_meteo_label]

    # Filter weather data to relevant columns and the defined month
    weather_df["date"] = pd.to_datetime(weather_df["date"])
    weather_df = weather_df[weather_df["date"].dt.month == defined_month].copy().reset_index(drop=True)
    df_weather = weather_df[["date", selected_meteo_col]].copy()

    # Handle the edge case for October
    if weather_df['date'].dt.month.iloc[0] == 10:
        x = weather_df.iloc[:-2,:].copy()
    else:
        x = weather_df.iloc[:-1,:].copy()

    weather_variable = weather_df.columns.tolist()
    weather_variable.remove("date")

    # st.write(df_weather.head())

    # Load energy data
    df_prod, df_cons = get_elhub_data(start_dt, end_dt)

    # Filter energy data to the defined year, defined month, and defined area
    def filter_year(df, selected_year, selected_month, selected_area, time_col="starttime"):
        """Return rows from df where the year and area match."""
        if df.empty:
            return df
        return df[(df[time_col].dt.year == selected_year) & (df["pricearea"] == selected_area) & (df[time_col].dt.month == selected_month)].copy().reset_index(drop=True)

    df_prod_selected = filter_year(df_prod, defined_year, defined_month, defined_area)
    df_cons_selected = filter_year(df_cons, defined_year, defined_month, defined_area)

    with col2:
        energy_options = {
            "Production – Hydro": ("Production", "hydro"),
            "Production – Wind": ("Production", "wind"),
            "Production – Solar": ("Production", "solar"),
            "Production – Thermal": ("Production", "thermal"),
            "Production – Other": ("Production", "other"),
            "Consumption – Households": ("Consumption", "household"),
            "Consumption – Cabin": ("Consumption", "cabin"),
            "Consumption – Primary": ("Consumption", "primary"),
            "Consumption – Secondary": ("Consumption", "secondary"),
            "Consumption – Tertiary": ("Consumption", "tertiary"),
        }
        selected_energy_label = col2.selectbox("Select energy variable", energy_options.keys())
        mode, group = energy_options[selected_energy_label]

    if mode == "Production":
        df_energy = df_prod_selected[df_prod_selected["productiongroup"] == group].copy().reset_index(drop=True)
    else:
        df_energy = df_cons_selected[df_cons_selected["consumptiongroup"] == group].drop(['year','month'], axis=1).copy().reset_index(drop=True)


    y= df_energy["quantitykwh"].reset_index(drop=True)

    # === Layout ===

    # --- Compact slider row ---
    col_lag, col_window, col_center = st.columns([1, 1, 2])
    with col_lag:
        lag = st.slider("Lag (hours)", 0, 120, 48)

    with col_window:
        window = st.slider("Window (hours)", 5, 240, 72)

    with col_center:
        center = st.slider("Center index", window//2, len(y)-window//2, 177)

    fig1, fig2, fig3 = plot_lag_window_center(x, y, selected_meteo_col, lag, window, center)

    st.subheader("Sliding Window Correlation")
    # Make plots more compact
    fig1.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
    fig2.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
    fig3.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))

    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)