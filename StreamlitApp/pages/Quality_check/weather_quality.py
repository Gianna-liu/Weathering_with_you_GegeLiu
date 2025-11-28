import streamlit as st
import pandas as pd
from tools.utils import (
    load_data_fromAPI,
    get_basic_info,
    plot_outlier_detection_dct,
    plot_outlier_detection_lof
)


# -------------------- Weather QC page (SPC + LOF)-------------------- 
def run():

    st.markdown("### 🌦 Weather Data Quality Check — SPC & LOF")

    # -------------------- Global shared state -------------------- #
    year = st.session_state.qc_year
    price_area = st.session_state.qc_price_area

    # -------------------- Load metadata and pick one representative location -------------------- #
    basic_info = get_basic_info()

    # filter rows that match price_area
    pa_rows = basic_info[basic_info["price_area_code"] == price_area]

    if pa_rows.empty:
        st.error(f"No weather location found for price area: {price_area}")
        st.stop()

    # pick the first location for this price area
    lat = float(pa_rows.iloc[0]["latitude"])
    lon = float(pa_rows.iloc[0]["longitude"])

    # -------------------- Load weather data -------------------- #
    city = pa_rows.iloc[0]["city"]
    st.info(
        f"Current selection → Year: **{year}**, Price Area: **{price_area}** \n"
        f"\n"
        f"Weather data for **{price_area}** uses the representative location:\n"
        f"- City: **{city}**\n"
        f"- Latitude: {lat:.4f}\n"
        f"- Longitude: {lon:.4f}\n\n"
        "Note: Price areas cover large regions; This analysis uses one fixed point within the area."
    )
    weather_df = load_data_fromAPI(lon, lat, selected_year=year)
    weather_df["date"] = pd.to_datetime(weather_df["date"])

    if weather_df.empty:
        st.warning("No weather data available.")
        st.stop()

    # -------------------- Step 1: Select variable -------------------- #
    st.markdown("##### 📌 Step 1: Choose weather variable")
    variable = st.selectbox(
        "",
        options=list(weather_df.columns.drop("date")),
        key="qc_weather_var"
    )

    df_var = weather_df[["date", variable]].copy()

    # -------------------- Step 2: Two tabs (SPC / LOF) -------------------- #
    tab_spc, tab_lof = st.tabs(["📉 SPC (DCT High-pass) Outliers", "🔍 LOF Anomaly Detection"])


    # -------------------- TAB 1 — SPC / DCT BASED HIGH-PASS OUTLIER DETECTION -------------------- 

    with tab_spc:
        st.markdown("##### 📌 Step 2: Tune SPC (DCT) parameters")

        col1, col2 = st.columns(2)
        with col1:
            W_filter = st.number_input(
                "High-pass Cutoff (W_filter)",
                min_value=0.0001,
                max_value=1.0,
                value=1 / (10 * 24),
                step=0.0001,
                format="%.5f"
            )
        with col2:
            coef_k = st.slider(
                "Sigma Multiplier (k)",
                min_value=1.0, max_value=5.0,
                value=3.0, step=0.5
            )

        fig_spc, summary_spc = plot_outlier_detection_dct(
            hourly_dataframe=df_var,
            selected_variable=variable,
            W_filter=W_filter,
            coef_k=coef_k
        )

        if fig_spc:
            st.plotly_chart(fig_spc, use_container_width=True)

            colA, colB, colC = st.columns(3)
            colA.metric("Samples", summary_spc["num_sample"])
            colB.metric("Outliers", summary_spc["num_outliers"])
            colC.metric("Outlier Rate (%)", summary_spc["ratio_outlier"])


    # -------------------- TAB 2 — LOF ANOMALY DETECTION-------------------- 

    with tab_lof:
        st.markdown("##### 📌 Step 2: Tune LOF parameters")

        col1, col2 = st.columns(2)
        with col1:
            contamination = st.slider(
                "Outlier proportion",
                0.001, 0.1, 0.01, step=0.005
            )
        with col2:
            n_neighbors = st.slider(
                "Number of neighbors",
                5, 100, 50, step=5
            )

        fig_lof, summary_lof = plot_outlier_detection_lof(
            hourly_dataframe=df_var,
            selected_variable=variable,
            contamination=contamination,
            n_neighbors=n_neighbors
        )

        if fig_lof:
            st.plotly_chart(fig_lof, use_container_width=True)

            colA, colB, colC = st.columns(3)
            colA.metric("Samples", summary_lof["num_sample"])
            colB.metric("Outliers", summary_lof["num_outliers"])
            colC.metric("Outlier Rate (%)", summary_lof["ratio_outlier"])
