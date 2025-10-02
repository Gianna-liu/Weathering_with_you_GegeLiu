from utils import load_data
import streamlit as st
import plotly.express as px
import pandas as pd

### Load the data
weather_df = load_data()

### First step, select the index and add one option
option_meteo = st.selectbox(
    label = "Step1: Please select one index",
    options = weather_df.columns.drop('time').to_list() + ["Show all"],
    index=0,
    help="Select a single variable or choose 'All columns' to display everything"
)

### Second step, select one month
weather_df["year_month"] = weather_df["time"].dt.strftime("%Y-%m")
month_list = sorted(weather_df['year_month'].unique())

option_month = st.select_slider(
    "Step2: Please select one month",
    options = month_list,
    value = '2020-01' # The value of the slider when it first renders.
)

st.write("You selected:", option_meteo, 'and',option_month)

### Third step, prepare the data and plot
df_filtered = weather_df[weather_df['year_month'] <= option_month]

if option_meteo != "Show all":
    option_df = df_filtered[['time', option_meteo]]
else:
    option_df = df_filtered.pop('year_month')

if option_meteo != "Show all":
    fig = px.line(
        df_filtered,
        x="time",
        y=option_meteo,
        title=f"{option_meteo} in {option_month}",
        labels={"time": "Date", option_meteo: option_meteo},
    )
else:
    df_melt = df_filtered.melt(id_vars="time", var_name="variable", value_name="value")
    fig = px.line(
        df_melt,
        x="time",
        y="value",
        color="variable",
        title=f"All variables in {option_month}",
        labels={"time": "Date", "value": "Value", "variable": "Variable"},
    )

st.plotly_chart(fig, use_container_width=True)
