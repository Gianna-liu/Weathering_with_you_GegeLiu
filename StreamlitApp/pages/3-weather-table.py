import streamlit as st
import pandas as pd
from utils import load_data_fromAPI,get_basic_info

selected_year = 2021
st.title(f"First-Month Weather Data — {selected_year}")

basic_info = get_basic_info()
selected_city = st.selectbox("Select City", basic_info["city"])
latitude = float(basic_info.loc[basic_info["city"] == selected_city, "latitude"].iloc[0])
longitude = float(basic_info.loc[basic_info["city"] == selected_city, "longitude"].iloc[0])

weather_df = load_data_fromAPI(longitude, latitude, selected_year=selected_year)
weather_df = weather_df[weather_df['date'].dt.month == 1]

price_area = basic_info.loc[
    basic_info["city"] == selected_city, "price_area_code"
].iloc[0]

st.success(f"Using data from **{selected_city}** corresponding to **{price_area}**")


if weather_df is None or weather_df.empty:
    st.warning("No data returned for this location/year.")
    st.stop()

for col in weather_df.columns:
    if col != "date":
        df_var = pd.DataFrame({
            "Variable": [col],
            "Series": [weather_df[col].tolist()]
        })
        st.data_editor(
        df_var,
        column_config={
            "Variable": st.column_config.TextColumn(label="Variable", width="medium"),
            "Series": st.column_config.LineChartColumn("Value",help=f"Row-wise sparkline for {col}",width="large"),
        },
        hide_index=True,
        )

with st.expander("Data Source"):
    st.write("""
        This dataset is retrieved from the **[Open-Meteo API](https://open-meteo.com/)**,  
    which provides historical reanalysis data using the **ERA5** model.
    """)
