from utils import load_data
import streamlit as st
import pandas as pd

st.title('Display the first month of the meteo')

weather_df = load_data()
weather_df = weather_df[weather_df['time'].dt.month == 1]


for col in weather_df.columns:
    if col != "time":
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
