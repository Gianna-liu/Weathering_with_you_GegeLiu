from utils import get_elhub_data, plot_stl_decompostion, plot_spectrogram
import streamlit as st

################################### 1. Connect to the Mongodb to load data ###################################
df = get_elhub_data()

st.title("Production Data Quality Analysis")

# get the value from production-plot page
# area = st.session_state.get("price_area", "NO1")
# group = st.session_state.get("production_group", "hydro")

################################### 2. Create two radio for selecting the area and group ###################################
with st.container():
    st.write("Step 1: Select Data Filters")
    col1, col2 = st.columns(2)

    with col1:
        price_area = st.radio(
            "Select Price Area",
            options=sorted(df["pricearea"].unique()), # list the option of pricearea
            key="price_area"
        )
    with col2:
        production_group = st.radio(
            "Select Production Group",
            options=sorted(df["productiongroup"].unique()), # list the option of productiongroup
            key="production_group"
        )

    st.success(f"Using data from **{price_area} - {production_group}**")

################################### 3. Create two tabs to display the analysis ###################################

tab1, tab2 = st.tabs(["STL analysis", "Spectrogram"])

# One tab for STL analysis
with tab1:
    st.subheader("Seasonal-Trend Decomposition (STL)")
    st.write("Step 2 Tune STL Parameters")

    # create four interactive widgets to tune the params
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        period = st.number_input("Period", min_value=1, max_value=168, value=24, step=1)
    with col2:
        seasonal = st.slider("Seasonal Window", min_value=3, max_value=241, value=41, step=2)
    with col3:
        trend = st.slider("Trend Window", min_value=5, max_value=720, value=721, step=2)
    with col4:
        robust = st.checkbox("Use Robust Fitting", value=True)

    # perform a Seasonal-Trend decomposition using LOESS (STL) on data
    fig = plot_stl_decompostion(
            df,
            area=price_area,
            group=production_group,
            period=period,
            seasonal=seasonal,
            trend=trend,
            robust=robust
        )

    if fig:
        st.plotly_chart(fig, use_container_width=True)

# One tab for Spectrogram analysis
with tab2:
    st.subheader("Spectrogram Analysis")
    st.write("Step 2: Tune Spectrogram Parameters")

    # create two interactive widgets to tune the params
    col1, col2 = st.columns(2)
    with col1:
        nperseg = st.slider("Window Length (hours)", min_value=10, max_value=240, value=40, step=5)
    with col2:
        noverlap = st.slider("Window Overlap (hours)", min_value=0, max_value=120, value=20, step=5)

    # perform a Short-Time Fourier Transform of data
    fig_spec = plot_spectrogram(
        df,
        area=price_area,
        group=production_group,
        nperseg=nperseg,
        noverlap=noverlap
    )

    if fig_spec:
        st.plotly_chart(fig_spec, use_container_width=True)