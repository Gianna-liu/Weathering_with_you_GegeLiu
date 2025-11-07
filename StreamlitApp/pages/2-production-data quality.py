from utils import get_elhub_data, plot_stl_decompostion
import streamlit as st

df = get_elhub_data()

st.title("Production Data Quality Analysis")

tab1, tab2 = st.tabs(["STL analysis", "Spectrogram"])

# get the value from production-plot page
# area = st.session_state.get("price_area", "NO1")
# group = st.session_state.get("production_group", "hydro")
# if "price_area" not in st.session_state or "production_group" not in st.session_state:
#     st.warning("⚠️ Please go back to the Home page and make selections first.")

with tab1:
    st.header("Seasonal-Trend Decomposition (STL)")
    with st.container():
        st.subheader("Step 1 Select Data ranges")
        col1, col2 = st.columns(2)
        with col1:
            price_area = st.radio(
                "Select Price Area",
                options=sorted(df['pricearea'].unique()),
                key="price_area"
            )
        with col2:
            production_group = st.radio(
                "Select Production Group",
                options=sorted(df['productiongroup'].unique()),
                key="production_group"
            )
        st.success(f"Using data from **{price_area} - {production_group}**")

    st.subheader("Step 2 Tune STL Parameters")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        period = st.number_input("Period", min_value=1, max_value=168, value=24, step=1)
    with col2:
        seasonal = st.slider("Seasonal Window", min_value=3, max_value=241, value=41, step=2)
    with col3:
        trend = st.slider("Trend Window", min_value=5, max_value=720, value=721, step=2)
    with col4:
        robust = st.checkbox("Use Robust Fitting", value=True)

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


with tab2:
    st.info("This tab will show the high-pass filtered data (coming soon).")