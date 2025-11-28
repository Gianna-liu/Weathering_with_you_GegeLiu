from tools.utils import get_elhub_data, plot_stl_decompostion, plot_spectrogram
import streamlit as st
import pandas as pd


# --------------------  Production Data Quality-------------------- 
def render_qc_production(df):

    price_area = st.session_state.qc_price_area

    # -------------------- 1. Select Production Group -------------------- #
    # Pretty inline heading + pills
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.markdown("##### 📌 Step 1: Choose Production Group:")
    with col_b:
        group = st.pills(
            "",
            options=sorted(df["productiongroup"].unique()),
            default=[sorted(df["productiongroup"].unique())[0]],
            key="qc_production_group",
            selection_mode="single",
        )

    df_area = df[df["pricearea"] == price_area]

    if df_area.empty:
        st.warning("No data available for this Price Area.")
        st.stop()

    df_group = df_area[df_area["productiongroup"] == group].sort_values("starttime")

    # -------------------- 2. Two Tabs: STL / Spectrogram -------------------- #
    tab_stl, tab_spec = st.tabs(["📉 STL Decomposition", "🎧 Spectrogram"])

    # -------------------- STL TAB -------------------- #
    with tab_stl:
        # st.subheader("Seasonal-Trend Decomposition (STL)")
        st.markdown("##### 📌 Step 2: Tune STL parameters below:")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            period = st.number_input("Period", min_value=1, max_value=168, value=24, step=1)
        with col2:
            seasonal = st.slider("Seasonal Window", min_value=3, max_value=241, value=41, step=2)
        with col3:
            trend = st.slider("Trend Window", min_value=5, max_value=721, value=121, step=2)
        with col4:
            robust = st.checkbox("Robust Mode", value=True)

        fig_stl = plot_stl_decompostion(
            df_group,
            area=price_area,
            group=group,
            period=period,
            seasonal=seasonal,
            trend=trend,
            robust=robust
        )

        if fig_stl:
            st.plotly_chart(fig_stl, use_container_width=True)

    # -------------------- Spectrogram TAB -------------------- #
    with tab_spec:
        st.subheader("Spectrogram Analysis")
        st.write("Tune window parameters below:")

        col1, col2 = st.columns(2)
        with col1:
            nperseg = st.slider("Window Length (hours)", min_value=10, max_value=240, value=40, step=5)
        with col2:
            noverlap = st.slider("Overlap (hours)", min_value=0, max_value=120, value=20, step=5)

        fig_spec = plot_spectrogram(
            df_group,
            area=price_area,
            group=group,
            nperseg=nperseg,
            noverlap=noverlap
        )

        if fig_spec:
            st.plotly_chart(fig_spec, use_container_width=True)


# -------------------- Main QC Electricity Page -------------------- 

def run():

    st.markdown("### ⚡ Electricity Production Quality Check — STL & Spectrogram")

    # -------------------- Use global QC parameters -------------------- #
    year = st.session_state.qc_year
    price_area = st.session_state.qc_price_area

    st.info(f"Current selection → Year: **{year}**, Price Area: **{price_area}**")

    # -------------------- Load production data -------------------- #
    start_dt = pd.Timestamp(f"{year}-01-01")
    end_dt = pd.Timestamp(f"{year}-12-31")

    df_prod, _ = get_elhub_data(start_dt=start_dt, end_dt=end_dt)

    if df_prod.empty:
        st.warning("No production data found for selected year.")
        return

    render_qc_production(df_prod)