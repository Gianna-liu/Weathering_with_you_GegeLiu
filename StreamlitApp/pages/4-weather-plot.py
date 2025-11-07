import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_data_fromAPI,get_basic_info

################################### 1. Load data from API ###################################
selected_year = 2021
st.title(f"Yearly & Hourly Weather Overview — {selected_year}")

basic_info = get_basic_info()
selected_city = st.selectbox("Step 1: Select City", basic_info["city"])

# Extract latitude and longitude for the selected city
latitude = float(basic_info.loc[basic_info["city"] == selected_city, "latitude"].iloc[0])
longitude = float(basic_info.loc[basic_info["city"] == selected_city, "longitude"].iloc[0])

weather_df = load_data_fromAPI(longitude, latitude, selected_year=selected_year)
weather_df['date'] = pd.to_datetime(weather_df['date'])

# Display information about the selected location
price_area = basic_info.loc[
    basic_info["city"] == selected_city, "price_area_code"
].iloc[0]
st.success(f"Using data from **{selected_city}** corresponding to **{price_area}**")

if weather_df is None or weather_df.empty:
    st.warning("No data returned for this location/year.")
    st.stop()

################################### 2. Create plots to display the data ###################################
### First step, select one Variable
option_meteo = st.selectbox(
    label = "Step 2: Select one Variable",
    options = weather_df.columns.drop('date').to_list() + ["Show all"],
    index=0,
    help="Select a single variable or choose 'All columns' to display everything"
)

### Second step, select one month
weather_df["year_month"] = weather_df["date"].dt.strftime("%Y-%m")
month_list = sorted(weather_df['year_month'].unique())

option_month = st.select_slider(
    "Step3: Select one month",
    options = month_list,
    value=month_list[0],  # The value of the slider when it first renders.
)

st.write(f"You selected: {selected_city}, {option_meteo} and {option_month}")

### Third step, prepare the data and plot
df_filtered = weather_df[weather_df['year_month'] <= option_month]
start_month = df_filtered['year_month'].min()
if option_meteo != "Show all":
    option_df = df_filtered[['date', option_meteo]]
else:
    option_df = df_filtered.drop(columns=['year_month'])

# Plot the selected variable(s)
if option_meteo != "Show all":
    fig = px.line(
        df_filtered,
        x="date",
        y=option_meteo,
        title=f"{option_meteo} from {start_month} to {option_month}",
        labels={"date": "Date", option_meteo: option_meteo},
    )
else:
    df_melt = df_filtered.melt(id_vars="date", var_name="variable", value_name="value")
    fig = px.line(
        df_melt,
        x="date",
        y="value",
        color="variable",
        title=f"All variables from {start_month} to {option_month}",
        labels={"date": "Date", "value": "Value", "variable": "Variable"},
    )


st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
