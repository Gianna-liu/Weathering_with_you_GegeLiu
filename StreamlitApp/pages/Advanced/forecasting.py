import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import statsmodels.api as sm

from tools.utils import get_elhub_data,get_basic_info,load_data_fromAPI

def run():
    # -------------------------------------------------------------
    # PAGE TITLE
    # -------------------------------------------------------------
    st.markdown(f"### 📈 Energy Forecasting (SARIMAX)")

    # 1) Price area & coordinates from Map page (must use Map selection)
    # -------------------------------------------------------------
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
    # Read values from session_state
    defined_area = st.session_state.selected_area_name
    lat, lon = st.session_state.last_pin   # (lat, lon)

    # Display them
    st.write(f"**Area:** {defined_area}")
    st.write(f"**Coordinates:** {lat:.4f}, {lon:.4f}")

    # -------------------------------------------------------------
    # 2) Training period selection
    # -------------------------------------------------------------

    st.markdown(f"#### ⏳ Select Training Date Range")

    col_start, col_end = st.columns(2)

    train_start_dt = pd.to_datetime(
        col_start.date_input(
            "Start Date",
            value=pd.to_datetime("2021-01-01"),
            min_value=pd.to_datetime("2021-01-01"),
            max_value=pd.to_datetime("2024-12-31"),
        )
    )

    train_end_dt = pd.to_datetime(
        col_end.date_input(
            "End Date",
            value=pd.to_datetime("2021-03-31"),
            min_value=train_start_dt,
            max_value=pd.to_datetime("2024-12-31"),
        )
    )

    # ---- Extra Validation ----
    if train_end_dt < train_start_dt:
        st.error("❗ End date must be after start date.")
        st.stop()

    st.write(f"**Training window:** {train_start_dt.date()} → {train_end_dt.date()}")



    # -------------------------------------------------------------
    # 3) Choose energy variable
    # -------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### ⚡ Select one group to Forecast")
        energy_options = {
            "Production – Hydro": ("Production", "hydro"),
            "Production – Wind": ("Production", "wind"),
            "Production – Thermal": ("Production", "thermal"),
            "Consumption – Households": ("Consumption", "households"),
            "Consumption – Industry": ("Consumption", "industry"),
        }
        energy_keys = list(energy_options.keys())
        default_index = energy_keys.index("Production – Hydro")

        selected_energy_label = st.selectbox(
            "Energy variable",
            energy_keys,
            index=default_index
    )
        
        mode, group = energy_options[selected_energy_label]

    # -------------------------------------------------------------
    # 4) Optional: Weather exogenous variables
    # -------------------------------------------------------------
    with col2:
        st.markdown(f"#### 🌦 Select Exogenous Variables (Optional)")

        use_exog = st.checkbox(
            "Include meteorological variables as exogenous features?",
            value=False
        )
        exog_df = None

        if use_exog:
            meteo_vars = st.multiselect(
                "Select weather variables",
                [
                    "temperature_2m",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "precipitation",
                ],
                default=["temperature_2m"],   # optional default
            )
            if len(meteo_vars) == 0:
                st.warning("Please select at least one meteorological variable or disable exogenous features.")
            else:
                # Show preview
                st.info(f"Using **{len(meteo_vars)}** meteorological variables as exogenous inputs")

                # Align weather to the same time range as energy
                train_start_tz = pd.to_datetime(train_start_dt).tz_localize("Europe/Oslo")
                train_end_tz   = pd.to_datetime(train_end_dt).tz_localize("Europe/Oslo")
                weather_df_raw = load_data_fromAPI(lon, lat, selected_year=train_start_dt.year)
                weather_df = weather_df_raw[(weather_df_raw["date"] >= train_start_tz) &(weather_df_raw["date"] <= train_end_tz)].reset_index(drop=True)
                exog_df = weather_df.set_index("date")[meteo_vars]

                agg_dict = {
                    "temperature_2m": "mean",      # temperature → daily mean
                    "wind_speed_10m": "mean",      # wind speed → daily mean
                    "wind_gusts_10m": "max",       # gust → daily max (合理)
                    "precipitation": "sum",        # precip → daily total (必用 sum)
                }

                # Keep only selected exogenous variables:
                selected_exog = meteo_vars

                # Daily aggregation:
                exog_df = (
                    weather_df.set_index("date")[selected_exog]
                    .resample("D")
                    .agg({var: agg_dict[var] for var in selected_exog})
                )
        else:
            st.caption("No exogenous variables selected.")


    # -------------------------------------------------------------
    # 4) SARIMAX parameter selectors
    # -------------------------------------------------------------
    st.markdown(f"#### ⚙ SARIMAX Parameters")

    col_p, col_d, col_q = st.columns(3)
    p = col_p.number_input("p (AR)", 0, 5, 1)
    d = col_d.number_input("d (Diff)", 0, 2, 0)
    q = col_q.number_input("q (MA)", 0, 5, 0)

    col_P, col_D, col_Q, col_s = st.columns(4)
    P = col_P.number_input("P", 0, 5, 1, 0)
    D = col_D.number_input("D", 0, 2, 0, 1)
    Q = col_Q.number_input("Q", 0, 5, 1, 0)
    s = col_s.number_input("s (season length)", 1, 7*4, 7, 7)  # default weekly seasonality

    # -------------------------------------------------------------
    # 5) Forecast horizon
    # -------------------------------------------------------------
    st.markdown(f"#### ⏳ Select Forecast Horizon")
    horizon = st.slider("Forecast Horizon (days)", 2, 30, 7)
    exog_future = None
    if use_exog:
        # -------------------------------------------------------------
        # Load future weather for exogenous variables
        # -------------------------------------------------------------
        future_weather_raw = load_data_fromAPI(lon, lat, selected_year=train_end_dt.year + 1)
        future_weather = pd.concat([weather_df_raw, future_weather_raw])
        #future_weather_raw["date"] = pd.to_datetime(future_weather_raw["date"]).dt.tz_convert("Europe/Oslo")
        agg_dict = {
                    "temperature_2m": "mean",      # temperature → daily mean
                    "wind_speed_10m": "mean",      # wind speed → daily mean
                    "wind_gusts_10m": "max",       # gust → daily max (合理)
                    "precipitation": "sum",        # precip → daily total (必用 sum)
                }

                # Keep only selected exogenous variables:
        selected_exog = meteo_vars
        # Daily aggregation:
        future_weather_daily = (
            future_weather.set_index("date")[selected_exog]
            .resample("D")
            .agg({var: agg_dict[var] for var in selected_exog})
        )
        future_start = train_end_dt + pd.Timedelta(days=1)
        future_end   = future_start + pd.Timedelta(days=horizon-1)
        future_start_tz = pd.to_datetime(future_start).tz_localize("Europe/Oslo") 
        future_end_tz = pd.to_datetime(future_end).tz_localize("Europe/Oslo")

        if len(meteo_vars) > 0:
            # filter the future exogenous variables based on the selected time range
            exog_future = future_weather_daily[future_weather_daily.index.to_series().between(future_start_tz, future_end_tz)][meteo_vars]
        else:
            exog_future = None
        # st.write(exog_future.head())


    df_prod, df_cons = get_elhub_data(train_start_dt, train_end_dt)

    # --- Filter helper ---
    def filter_energy(df, mode, group, area, train_start_dt, train_end_dt):
        if df.empty:
            return pd.DataFrame()

        df["starttime"] = pd.to_datetime(df["starttime"])

        if mode == "Production":
            sub = df[(df["productiongroup"] == group) & (df["pricearea"] == area)]
        else:
            sub = df[(df["consumptiongroup"] == group) & (df["pricearea"] == area)]

        # Year filter
        sub = sub[
            (sub["starttime"] >= train_start_dt) &
            (sub["starttime"] <= train_end_dt)
        ]
        # Sort and reset
        return sub.sort_values("starttime").reset_index(drop=True)


    # choose df based on mode
    if mode == "Production":
        df_energy = filter_energy(df_prod, mode, group, defined_area, train_start_dt, train_end_dt)
        value_col = "quantitykwh"
    else:
        df_energy = filter_energy(df_cons, mode, group, defined_area, train_start_dt, train_end_dt)
        value_col = "quantitykwh"

    if df_energy.empty:
        st.error("No energy data found for this selection.")
        st.stop()

    # --- Prepare training data ---
    df_energy = df_energy.drop_duplicates(subset="starttime")
    # --- Prepare time series y(t) ---
    df_energy = df_energy[["starttime", value_col]].rename(columns={"starttime": "time", value_col: "value"})
    # df_energy = df_energy.set_index("time").asfreq("H")   # ensure hourly frequency
    df_energy = (
        df_energy.set_index("time")
        .resample("D")       # daily
        .sum()               # total energy of the day
    )
    df_energy["value"] = df_energy["value"].interpolate()  # fill missing hours


    # y —— training series
    y = df_energy["value"]

    if use_exog:
        exog_df['time'] = y.index
        exog_df = exog_df.set_index("time")

    # SARIMAX model
    try:
        model = sm.tsa.statespace.SARIMAX(
            y,
            order=(p, d, q),
            seasonal_order=(P, D, Q, s),
            exog=exog_df if use_exog and exog_df is not None else None,
            enforce_stationarity=False,
            enforce_invertibility=False
        )

        results = model.fit(disp=False)
        st.success("Model successfully fitted.")

    except Exception as e:
        st.error(f"Model fitting error: {e}")
        st.stop()

    # -------------------------------------------------------------
    # 6) Forecasting and visualization
    # -------------------------------------------------------------
    st.markdown(f"#### 🚀 Forecast Results")
    forecast = results.get_forecast(steps=horizon, exog=exog_future)
    # forecast = results.get_forecast(steps=horizon)
    # forecast = results.get_prediction(dynamic = len(y), full_results=True)
    mean_forecast = forecast.predicted_mean
    conf_int = forecast.conf_int()

    fig = go.Figure()

    # 1) Training data
    fig.add_trace(go.Scatter(
        x=y.index,
        y=y,
        mode='lines',
        name='Training Data',
        line=dict(color='white')
    ))

    # 2) Forecast mean
    fig.add_trace(go.Scatter(
        x=mean_forecast.index,
        y=mean_forecast.values,
        mode='lines',
        name='Forecast',
        line=dict(color='cyan')
    ))

    # 3) Confidence Interval
    fig.add_trace(go.Scatter(
        x=conf_int.index,
        y=conf_int.iloc[:, 0],
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=conf_int.index,
        y=conf_int.iloc[:, 1],
        mode='lines',
        fill='tonexty',
        name='Confidence Interval',
        line=dict(width=0),
        fillcolor='rgba(0, 200, 255, 0.2)'
    ))

    fig.update_layout(
        height=400,
        template="plotly_dark",
        title="SARIMAX Forecast with Confidence Intervals",
        xaxis_title="Time",
        yaxis_title=value_col,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"#### 📊 Model Summary")
    st.write(results.summary())