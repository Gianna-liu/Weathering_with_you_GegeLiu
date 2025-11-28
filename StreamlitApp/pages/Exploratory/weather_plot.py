import streamlit as st
import plotly.express as px
import pandas as pd
from tools.utils import load_data_fromAPI,get_basic_info

def run():

    # ------------------- Read global state -------------------
    year = st.session_state.expl_year
    price_area = st.session_state.expl_price_area

    st.markdown(f"### Yearly Weather Overview")

    # ------------------- Load basic info ---------------------
    basic_info = get_basic_info()

    # Find the default city associated with selected price area
    matched_row = basic_info[basic_info["price_area_code"] == price_area]

    if matched_row.empty:
        st.error(f"No location found for price area {price_area}")
        st.stop()

    selected_city = matched_row["city"].iloc[0]
    latitude = float(matched_row["latitude"].iloc[0])
    longitude = float(matched_row["longitude"].iloc[0])

    st.info(f"Current selection → Year: **{year}**, Price Area: **{price_area}**")

    # ------------------- Load weather from API -------------------
    weather_df = load_data_fromAPI(longitude, latitude, selected_year=year)

    if weather_df is None or weather_df.empty:
        st.warning("No data returned for this location/year.")
        st.stop()

    weather_df['date'] = pd.to_datetime(weather_df['date'])
    weather_df["year_month"] = weather_df["date"].dt.strftime("%Y-%m")

# ------------------- Two column layout for selectors -------------------
    col_left, col_right = st.columns([1.2, 2])

    with col_left:

        # Variables
        st.markdown("#### 📌 Step 1: Choose a variable")
        option_meteo = st.selectbox(
            "",
            options=weather_df.columns.drop(['date', 'year_month']).to_list() + ["Show all"],
            index=0
        )

        st.markdown("---")

        # Month selector
        st.markdown("#### ⏳ Step 2: Select time range")

        month_list = sorted(weather_df['year_month'].unique())

        start_month, end_month = st.select_slider(
            "",
            options=month_list,
            value=(month_list[0], month_list[0]),  # default: first month only
        )

        st.markdown(f"""
        <p style="color:#9CA3AF; font-size:14px;">
        Selected period: <b>{start_month}</b> → <b>{end_month}</b>
        </p>
        """, unsafe_allow_html=True)


    with col_right:
        # ------------------- Filter data -------------------
        df_filtered = weather_df[
            (weather_df['year_month'] >= start_month) &
            (weather_df['year_month'] <= end_month)
        ]

        if option_meteo != "Show all":
            df_plot = df_filtered[['date', option_meteo]]
        else:
            df_plot = df_filtered.drop(columns=['year_month'])

        # ------------------- Plot -------------------
        if option_meteo != "Show all":
            fig = px.line(
                df_plot,
                x="date",
                y=option_meteo,
                title=f"{option_meteo} — {start_month} to {end_month}",
            )
        else:
            df_melt = df_filtered.melt(id_vars="date", var_name="variable", value_name="value")
            fig = px.line(
                df_melt,
                x="date",
                y="value",
                color="variable",
                title=f"All Variables — {start_month} to {end_month}",
            )

        fig.update_layout(
            title_x=0.0,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E5E7EB"),
            margin=dict(t=70, l=10, r=20, b=10)
        )

        st.plotly_chart(fig, use_container_width=True)
