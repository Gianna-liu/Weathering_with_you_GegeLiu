import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_data_fromAPI,get_basic_info, plot_outlier_detection_dct,plot_outlier_detection_lof

################################### 1. Load data from API ###################################
selected_year = 2021
st.title(f"Weather Data Quality Analysis — {selected_year}")

### Load the data
basic_info = get_basic_info()
selected_city = st.selectbox("Step 1.Select City", basic_info["city"])
latitude = float(basic_info.loc[basic_info["city"] == selected_city, "latitude"].iloc[0])
longitude = float(basic_info.loc[basic_info["city"] == selected_city, "longitude"].iloc[0])

weather_df = load_data_fromAPI(longitude, latitude, selected_year=selected_year)
weather_df['date'] = pd.to_datetime(weather_df['date'])

price_area = basic_info.loc[
    basic_info["city"] == selected_city, "price_area_code"
].iloc[0]

st.success(f"Using data from **{selected_city}** corresponding to **{price_area}**")

if weather_df is None or weather_df.empty:
    st.warning("No data returned for this location/year.")
    st.stop()

selected_variable = st.selectbox("Step 2.Select Variable", weather_df.columns.drop("date"), index=0)

tab1, tab2 = st.tabs(["Outlier/SPC analysis", "Anomaly/LOF analysis"])

with tab1:
    st.subheader("Outlier Detection - Statistical Process Control (SPC)")
    st.write("Step 3: Tune SPC Parameters")
    col1, col2 = st.columns(2)
    with col1:
        W_filter = st.number_input("High-pass Filter W_cutoff (cycles/hour)",
                                   min_value=0.0001, max_value=1.0, value=1 / (10 * 24), step=0.0001,
                                   format="%.5f")
    with col2:
        coef_k = st.slider("Sigma Multiplier (k)", min_value=1.0, max_value=5.0, value=3.0, step=0.5)


    fig,dct_summary = plot_outlier_detection_dct(
            hourly_dataframe=weather_df,
            selected_variable=selected_variable,
            W_filter=W_filter,
            coef_k=coef_k
        )

    if fig:
        st.plotly_chart(fig, use_container_width=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Samples", dct_summary["num_sample"])
        col2.metric("Outliers", dct_summary["num_outliers"])
        col3.metric("Outlier Ratio (%)", dct_summary["ratio_outlier"])

with tab2:
    st.subheader("Anomaly Detection - Local Outlier Factor (LOF)")
    st.write("Step 3: Tune SPC Parameters")
    col1, col2 = st.columns(2)
    with col1:
        contamination = st.slider("Contamination (Proportion of Outliers)",
                                  0.001, 0.1, 0.01, step=0.005)
    with col2:
        n_neighbors = st.slider("Number of Neighbors (n_neighbors)",
                                5, 100, 50, step=5)
    fig_lof, lof_summary = plot_outlier_detection_lof(
        hourly_dataframe=weather_df,
        selected_variable=selected_variable,
        contamination=contamination,
        n_neighbors=n_neighbors
    )
    if fig_lof:
        st.plotly_chart(fig_lof, use_container_width=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Samples", lof_summary["num_sample"])
        col2.metric("Outliers", lof_summary["num_outliers"])
        col3.metric("Outlier Ratio (%)", lof_summary["ratio_outlier"])
