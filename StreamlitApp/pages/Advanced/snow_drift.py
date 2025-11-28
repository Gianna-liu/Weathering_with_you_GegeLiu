import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

from tools.utils import load_data_fromAPI
from tools.Snow_drift import compute_snow_transport, compute_average_sector, plot_rose


def run():
    st.markdown(f"### ❄️ Snow Drift Analysis (July → June Snow Years)")

    # ---------------------  Check area + coordinates from Map page --------------------- 

    st.subheader("📍 Selected Price Area from Map page")

    
    if "selected_area_name" not in st.session_state or st.session_state.selected_area_name is None:
        st.error("⚠ Please go to the Map page and select a price area (NO1–NO5).")
        st.stop()

    if "last_pin" not in st.session_state or st.session_state.last_pin is None:
        st.error("⚠ Please click a location on the map first.")
        st.stop()

    area_name = st.session_state.selected_area_name
    lat, lon = st.session_state.last_pin

    st.write(f"**Area:** {area_name}")
    st.write(f"**Coordinates:** {lat:.4f}, {lon:.4f}")

    # --------------------- Select snow-year range---------------------
    def season_label(s):
        return f"{s}–{str(s+1)[2:]}  (Jul→Jun)"

    st.subheader("⏳ Select a Snow Year Range")

    colA, colB = st.columns(2)

    start_season = colA.selectbox(
        "Start Snow Year",
        [2019, 2020, 2021, 2022, 2023],
        index=0,
        format_func=season_label,
        key="start_season"
    )

    end_season = colB.selectbox(
        "End Snow Year",
        [2019, 2020, 2021, 2022, 2023],
        index=4,
        format_func=season_label,
        key="end_season"
    )

    if end_season < start_season:
        st.error("End season must be ≥ start season.")
        st.stop()

    # --------------------- Compute Qt per season ---------------------
    results = []
    season_dfs = {}

    for season in range(start_season, end_season + 1):

        year1 = season
        year2 = season + 1

        with st.spinner(f"Processing {season_label(season)} ..."):
            df_y1 = load_data_fromAPI(lon, lat, year1)
            df_y2 = load_data_fromAPI(lon, lat, year2)

            df = pd.concat([df_y1, df_y2], ignore_index=True)
            df.sort_values("date", inplace=True)

            # Slice the snow-year: July → June
            season_start = pd.Timestamp(year1, 7, 1, tz="Europe/Oslo")
            season_end   = pd.Timestamp(year2, 6, 30, 23, 59, tz="Europe/Oslo")

            df_season = df[(df["date"] >= season_start) & (df["date"] <= season_end)].copy()
            if df_season.empty:
                continue

            # SWE: precipitation only when temp < 1°C
            df_season["Swe"] = df_season.apply(
                lambda r: r["precipitation"] if r["temperature_2m"] < 1 else 0,
                axis=1
            )

            # Snow drift model parameters
            T = 3000
            F = 30000
            theta = 0.5

            hourly_wind = df_season["wind_speed_10m"].tolist()
            total_Swe = df_season["Swe"].sum()

            result = compute_snow_transport(T, F, theta, total_Swe, hourly_wind)

            Qt_kg = result["Qt (kg/m)"]
            Qt_tonnes = Qt_kg / 1000.0

            results.append({
                "season_year": season,
                "season_label": season_label(season),
                "Qt_tonnes": Qt_tonnes,
            })
            season_dfs[season] = df_season

    df_results = pd.DataFrame(results)

    # --------------------- Calculate Monthly Snow Drift (Qt per Month) ---------------------

    monthly_rows = []

    for season in range(start_season, end_season + 1):

        df_season = season_dfs.get(season)
        if df_season is None or df_season.empty:
            continue

        # Ensure SWE is present
        df_season["Swe"] = df_season.apply(
            lambda r: r["precipitation"] if r["temperature_2m"] < 1 else 0,
            axis=1
        )

        # group by month
        df_season = df_season.set_index("date")
        grouped = df_season.groupby(pd.Grouper(freq="M"))

        for month, df_month in grouped:

            if df_month.empty:
                continue

            monthly_SWE = df_month["Swe"].sum()
            monthly_wind = df_month["wind_speed_10m"].tolist()

            # use SAME model as Yearly Qt
            result = compute_snow_transport(T, F, theta, monthly_SWE, monthly_wind)
            Qt_month_kg = result["Qt (kg/m)"]
            Qt_month_tonnes = Qt_month_kg / 1000.0

            monthly_rows.append({
                "season": season,
                "season_label": season_label(season),
                "month_label": month.strftime("%Y-%m"),
                "Qt_monthly": Qt_month_tonnes
            })

    df_monthly = pd.DataFrame(monthly_rows)


    # --------------------- Two-column layout: Annual Qt and Monthly Qt --------------------- 

    st.subheader("📈 Snow Drift Overview")

    st.info(
        "**Qt – Total Snow Transport (tonnes/m)**\n"
        "Represents the total amount of snow transported by wind per meter width during a given period (Jul–Jun)."
    )

    colA, colB = st.columns([0.9, 1.2])

    # Left Column
    with colA:
        st.markdown("#### Annual Qt")
        if df_results.empty:
            st.warning("No annual snow drift data.")
        else:
            df_results["short_label"] = df_results["season_year"].astype(str) + "–" + (df_results["season_year"]+1).astype(str).str[2:]
            fig_annual = px.bar(
                df_results,
                x="short_label",
                y="Qt_tonnes",
                title=" ",
                # text_auto=".1f",
                color_discrete_sequence=["#82E2C4"],
            )

            fig_annual.update_traces(
            # textposition="inside",
            # insidetextanchor="end",
            # textfont_size=16,
            # textfont_color="#1C2828",
            # marker_color="#77D4B7",
            # marker_line_color="#2F4F4F",
            # marker_line_width=1.2,
            width=0.45,
            opacity=0.95,
        )

            fig_annual.update_layout(
                template="simple_white",
                title_x=0.5,
                xaxis_title="Snow Year (Jul–Jun)",
                yaxis_title="Qt (tonnes/m)",
                height=420,
                xaxis_tickangle=-30,
                margin=dict(l=10, r=10, t=40, b=10),
                font_family="Helvetica",
                font_color="#2F4F4F",

            )
            fig_annual.update_xaxes(title_font=dict(size=13), tickfont=dict(size=12))
        
            st.plotly_chart(fig_annual, use_container_width=True)
            with st.expander("Exact Qt Values"):
                st.dataframe(df_results[["short_label", "Qt_tonnes"]])

    # Right Column
    with colB:
        st.markdown("#### Monthly Qt (Jul–Jun)")

        if df_monthly.empty:
            st.warning("No monthly drift available.")
        else:
            # Month order Jul->Jun
            month_order = ["07","08","09","10","11","12","01","02","03","04","05","06"]

            df_monthly["MM"] = df_monthly["month_label"].str[-2:]
            df_monthly["MM"] = pd.Categorical(df_monthly["MM"], categories=month_order, ordered=True)
            df_m_sorted = df_monthly.sort_values(["season", "MM"])

            fig_month = px.line(
                df_m_sorted,
                x="MM",
                y="Qt_monthly",
                color="season_label",
                markers=True,
                #title="Monthly Snow Drift (Qt) — Jul → Jun",
            )

            fig_month.update_layout(
                xaxis_title="Month (Snow Year)",
                yaxis_title="Qt (tonnes/m)",
                template="plotly_dark",
                height=420,
                margin=dict(l=10, r=10, t=40, b=10)
            )

            st.plotly_chart(fig_month, use_container_width=True)

    # --------------------- Wind Rose – Select exact season --------------------- 
    st.markdown("## 🌬 Wind Rose for a Selected Snow Year")

    if df_results.empty:
        st.info("No valid seasons available for wind rose.")
    else:
        available_seasons = df_results["season_year"].tolist()
        default_index = len(available_seasons) // 2

        selected_season = st.selectbox(
            "Choose Snow Year",
            available_seasons,
            index=default_index,
            format_func=season_label,
            key="wind_rose_season"
        )

        df_rose = season_dfs.get(selected_season)

        if df_rose is None or df_rose.empty:
            st.warning("No data for this season.")
        else:
            avg_sectors = compute_average_sector(df_rose)

            Qt_kg_selected = (
                df_results[df_results["season_year"] == selected_season]["Qt_tonnes"].iloc[0] * 1000
            )

            st.write(f"Wind Rose for **{season_label(selected_season)}**, Area **{area_name}**")

            fig_rose = plot_rose(avg_sectors, Qt_kg_selected)
            values = [v / 1000 for v in avg_sectors]

            st.plotly_chart(fig_rose, use_container_width=True)
