import pandas as pd
import streamlit as st
import openmeteo_requests
import pandas as pd
import requests_cache
import numpy as np
from retry_requests import retry
from pathlib import Path
import pymongo
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from statsmodels.tsa.seasonal import STL
from scipy.fft import dct, idct
import scipy.stats as stats
from sklearn.neighbors import LocalOutlierFactor
from scipy.signal import stft

################################### 1.Get the data from API ###################################

@st.cache_data
def load_data_fromAPI(longitude, latitude, selected_year):
	# Setup the Open-Meteo API client with cache and retry on error
	cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
	retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
	openmeteo = openmeteo_requests.Client(session = retry_session)

	# Make sure all required weather variables are listed here
	# The order of variables in hourly or daily is important to assign them correctly below
	url = "https://archive-api.open-meteo.com/v1/archive"
	params = {
		"latitude": latitude,
		"longitude": longitude,
        "start_date": f"{selected_year}-01-01",
        "end_date": f"{selected_year}-12-31",
		"hourly": ["temperature_2m", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m", "precipitation"],
		"models": "era5",
		"timezone": "auto",
        "wind_speed_unit": "ms",
	}
	responses = openmeteo.weather_api(url, params=params)

	# Process first location. Add a for-loop for multiple locations or weather models
	response = responses[0]
	print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
	print(f"Date_range: {params['start_date']} - {params['end_date']}")
	print(f"Variables: {params['hourly']}")
	#print(f"Elevation: {response.Elevation()} m asl")
	#print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

	# Process hourly data. The order of variables needs to be the same as requested.
	hourly = response.Hourly()
	hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
	hourly_wind_speed_10m = hourly.Variables(1).ValuesAsNumpy()
	hourly_wind_gusts_10m = hourly.Variables(2).ValuesAsNumpy()
	hourly_wind_direction_10m = hourly.Variables(3).ValuesAsNumpy()
	hourly_precipitation = hourly.Variables(4).ValuesAsNumpy()

	hourly_data = {"date": pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left"
	)}

	hourly_data["temperature_2m"] = hourly_temperature_2m
	hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
	hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m
	hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
	hourly_data["precipitation"] = hourly_precipitation

	hourly_dataframe = pd.DataFrame(data = hourly_data)
	# Change the time zone to Europe/Oslo
	hourly_dataframe["date"] = hourly_dataframe["date"].dt.tz_convert("Europe/Oslo")
	hourly_dataframe = hourly_dataframe[hourly_dataframe["date"].dt.year == int(selected_year)]
	print(f"Sucessfully load the data")
	
	return hourly_dataframe

################################### 2.Get the data from MongoDB ###################################
# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

# Pull data from the collection including production and consumption data
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=259200)
def get_elhub_data(start_dt, end_dt):
    client = init_connection()
    db = client['elhub_db']
    # Load production data
    # Query only the needed time range
    # Normalize boundaries
    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    query = {
        "starttime": {
            "$gte": start_dt,
            "$lte": end_dt
        }
    }
    # Production data
    prod_items = list(
        db["production_data"].find(query)
    )
    df_prod = pd.DataFrame(prod_items)

    # Consumption data
    cons_items = list(
        db["consumption_data"].find(query)
    )
    df_cons = pd.DataFrame(cons_items)

    # Standardize timestamp
    if not df_prod.empty:
        df_prod["starttime"] = pd.to_datetime(df_prod["starttime"])
    if not df_cons.empty:
        df_cons["starttime"] = pd.to_datetime(df_cons["starttime"])
    return df_prod, df_cons

def filter_time_window(df, start_date, end_date):
    if df.empty:
        return df
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return df[(df["starttime"] >= start_dt) & (df["starttime"] <= end_dt)]


def get_group_list(df_prod, df_cons, mode):
    if mode == "Production":
        return sorted(df_prod["productiongroup"].dropna().unique())
    else:
        return sorted(df_cons["consumptiongroup"].dropna().unique())
    
def energy_format_kwh(x):
    if x >= 1e6:
        return f"{x/1e6:.2f} GWh"
    elif x >= 1e3:
        return f"{x/1e3:.2f} MWh"
    else:
        return f"{x:.0f} kWh"


def get_area_means(df, mode, group, start_date, end_date, aggregation):
    # 1. Filter by time window
    df = filter_time_window(df, start_date, end_date)
    # st.write(df.head())

    # 2. Filter by production/consumption group
    if mode == "Production":
        df = df[df["productiongroup"] == group]
    else:
        df = df[df["consumptiongroup"] == group]

    if df.empty:
        return pd.DataFrame(columns=["area", "value"])

    # 3. Apply aggregation: Daily / Monthly / Yearly
    if aggregation == "Daily":
        df["period"] = df["starttime"].dt.to_period("D")
    elif aggregation == "Monthly":
        df["period"] = df["starttime"].dt.to_period("M")
    elif aggregation == "Yearly":
        df["period"] = df["starttime"].dt.to_period("Y")
    else:
        raise ValueError("Invalid aggregation value")

    # 4. First aggregation: sum per period per area
    # (one value per day/month/year for each price area)
    df_agg = (
        df.groupby(["pricearea", "period"])["quantitykwh"]
        .sum()
        .reset_index()
    )

    # 5. Second aggregation: mean across selected periods
    df_mean = (
        df_agg.groupby("pricearea")["quantitykwh"]
        .mean()
        .reset_index()
        .rename(columns={"pricearea": "area", "quantitykwh": "value_raw"})
    )

    # 6. Add formatted string for display
    df_mean["value"] = df_mean["value_raw"].apply(energy_format_kwh)

    return df_mean

################################### 3.Save the basic info ###################################

def get_basic_info():
    """Return DataFrame containing Norwegian price area & coordinates."""
    basic_data = {
        "city": ["Oslo", "Kristiansand", "Trondheim", "Tromsø", "Bergen"],
        "price_area_code": ["NO1", "NO2", "NO3", "NO4", "NO5"],
        "latitude": [59.9127, 58.1467, 63.4305, 69.6489, 60.393],
        "longitude": [10.7461, 7.9956, 10.3951, 18.9551, 5.3242],
    }
    return pd.DataFrame(basic_data)

################################### 4.Check the data quality with STL ###################################

def plot_stl_decompostion(df_production, area:str = 'NO1',group:str = 'hydro',period:int = 24,seasonal:int = 4*10+1,trend:int =24*30+1 ,robust:bool = True):
    df_subset = df_production[(df_production['pricearea']==area) & (df_production['productiongroup']==group)]
    df_subset.reset_index(inplace=True,drop=True)
    stl = STL(df_subset["quantitykwh"], period=period,seasonal=seasonal,trend=trend,robust=robust)
    res = stl.fit() # Contains the components and a plot function
    ## Plot the results
    fig = go.Figure()
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,subplot_titles=["Observed", "Trend", "Seasonal", "Residual"],vertical_spacing=0.05)
    # original data
    fig.add_trace(go.Scatter(x=df_subset['starttime'],y=df_subset["quantitykwh"],mode='lines',name='Observed',line=dict(color='blue')),row=1, col=1)
    # Trend
    fig.add_trace(go.Scatter(x=df_subset['starttime'],y=res.trend,mode='lines',name='Trend',line=dict(color='orange')),row=2, col=1)
    # Seasonal
    fig.add_trace(go.Scatter(x=df_subset['starttime'],y=res.seasonal,mode='lines',name='Seasonal',line=dict(color='green')),row=3, col=1)
    # Residual
    fig.add_trace(go.Scatter(x=df_subset['starttime'],y=res.resid,mode='lines',name='Residual',line=dict(color='gray', dash='dot')),row=4, col=1)
    fig.update_layout(title=f'The STL decomposition of area:{area} and productiongroup:{group}', xaxis4_title='Time (hourly)', yaxis_title='Values',height=900)

    return fig

################################### 5.Check the data quality with SPC ###################################

def plot_outlier_detection_dct(hourly_dataframe,selected_variable: str, W_filter: float = 1/(10*24), coef_k: float = 3):
    signal = hourly_dataframe[selected_variable].to_numpy(float)
    N = hourly_dataframe.shape[0]
    dt = 1
    W = np.linspace(0, 1/(2*dt), N) # cycles/hour

    # check and fill NaN values with mean
    if np.isnan(signal).any():
        signal = np.nan_to_num(signal, nan=np.nanmean(signal))

    # Discrete Cosine transform
    fourier_signal = dct(signal, norm="ortho")

    # high-pass filter to keep the high-frequency components
    filtered_hp_signal = fourier_signal.copy()
    filtered_hp_signal[(W < W_filter)] = 0 
    satv = idct(filtered_hp_signal, norm="ortho") 

    # low-pass filter to keep the trend
    filtered_lp_signal = fourier_signal.copy()
    filtered_lp_signal[(W > W_filter)] = 0 
    trend = idct(filtered_lp_signal, norm="ortho") 

    # Median absolute deviation
    coef_k = coef_k
    mad_raw = stats.median_abs_deviation(satv, scale=1.0)
    sd = mad_raw * 1.4826
    print(sd)
    # Find the boundaries
    upper_boundary = trend + coef_k * sd
    lower_boundary = trend - coef_k * sd

    # Detect the outliers
    outlier_mask = (signal > upper_boundary) | (signal < lower_boundary)

    fig = go.Figure()

    # Plot trend
    fig.add_trace(go.Scatter(
        x=hourly_dataframe['date'], y=trend,
        mode="lines", line=dict(color="green"),
        name="Trend"
    ))

    # Upper and lower dynamic boundaries
    fig.add_trace(go.Scatter(
        x=hourly_dataframe['date'], y=upper_boundary,
        mode="lines", line=dict(color='red', dash='dash'),
        name=f"{coef_k}*SD (Upper)"
    ))

    fig.add_trace(go.Scatter(
        x=hourly_dataframe['date'], y=lower_boundary,
        mode="lines", line=dict(color='red', dash='dash'),
        name=f"{coef_k}*SD (Lower)"
    ))

    # Normal points
    fig.add_trace(go.Scatter(
        x=hourly_dataframe['date'], y=signal,
        mode="markers", marker=dict(color="blue", size=5),
        name="Normal"
    ))

    # Outliers
    fig.add_trace(go.Scatter(
        x=hourly_dataframe.loc[outlier_mask, 'date'],
        y=signal[outlier_mask],
        mode="markers", marker=dict(color="orange", size=8),
        name="Outliers"
    ))

    fig.update_layout(
        title=f"DCT-Based Outlier Detection (High-pass SATV) for {selected_variable}",
        xaxis_title="Time",
        yaxis_title="Value"
    )
    # add some basic info about the outliers
    summary = {
        "variable": selected_variable,
        "num_sample": N,
        "Sigma Multiplier (k)":coef_k,
        "High-pass Filter W_cutoff":W_filter,
        "num_outliers": int(outlier_mask.sum()),
        "ratio_outlier": round(outlier_mask.sum() / N * 100, 2),
    }
    return fig,summary


################################### 6.Check the data quality with LOF ###################################

def plot_outlier_detection_lof(hourly_dataframe,selected_variable: str, contamination: float = 0.01, n_neighbors: int = 50):
    selected_data = hourly_dataframe[[selected_variable]].copy()

    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    pred_labels = lof.fit_predict(selected_data)

    # Separate normal and outliers
    outlier_mask = pred_labels == -1
    normal_mask = pred_labels == 1


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hourly_dataframe.loc[normal_mask, 'date'],y=selected_data.loc[normal_mask, selected_variable], mode='markers', marker=dict(color='blue'), name='normal'))
    fig.add_trace(go.Scatter(x=hourly_dataframe.loc[outlier_mask, 'date'],y=selected_data.loc[outlier_mask, selected_variable], mode='markers', marker=dict(color='orange'), name='outlier'))
    fig.update_layout(title=f'The distribution of {selected_variable} with outliers', xaxis_title='Time (hourly)', yaxis_title='Values')

    # Add the brief summary
    summary = {
        "variable": selected_variable,
        "num_sample": len(selected_data),
        "contamination_param":contamination,
        "n_neighbors":n_neighbors,
        "num_outliers": outlier_mask.sum(),
        "ratio_outlier": round(outlier_mask.mean() * 100, 2),
        "mean_value": round(selected_data[selected_variable].mean(), 2)
    }

    return fig, summary

################################### 6.Plot the spectrogram ###################################
def plot_spectrogram(df_production,area: str = "NO1",group: str = "hydro",nperseg: int = 40,noverlap: int = 20):
    df_subset = df_production[(df_production["pricearea"] == area)& (df_production["productiongroup"] == group)].sort_values("starttime")
    y = df_subset["quantitykwh"].values
    fs = 1
    f, t, Zxx = stft(y, fs=fs, nperseg=nperseg, noverlap=noverlap)

    fig = go.Figure()
    magnitude = np.abs(Zxx)
    start_time = df_subset["starttime"].iloc[0]
    t_datetime = [start_time + pd.Timedelta(hours=float(h)) for h in t]

    fig.add_trace(go.Heatmap(
        x=t_datetime,
        y=f,
        z=magnitude,
        colorscale="Viridis",
        colorbar=dict(title="Amplitude"),
        zmin=0,
        zmax=magnitude.max() * 0.8,
        hovertemplate="Date: %{x|%Y-%m-%d %H:%M}<br>Freq: %{y:.4f}/h<br>Amp: %{z:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title=f"Spectrogram of {group} production — {area}",
        xaxis_title='Time (hourly)',
        yaxis_title="Frequency [1/hour]",
        template="plotly_white",
        height=600,
    )
    fig.update_yaxes(range=[0, 0.05])
    return fig


################################### 7.Plot the wind rose ###################################

##### Plot lag-window-center correlation plots #####
def plot_lag_window_center(x, y, variable, lag, window, center):
    
    # 1) ---- Global correlation  -----
    corr_matrix = np.corrcoef(y[lag:], x[variable][0:len(x)-lag])
    global_corr = corr_matrix[0,1]

    # 2) ---- Sliding Window Correlation ----
    z = x[variable].copy()
    z.index = z.index + lag

    SWC = y.rolling(window, center=True).corr(z)

    # ---------------------
    #  Plot 1: Energy (y)
    # ---------------------
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=y.index, y=y.values,
        mode="lines",
        name="Energy (y)"
    ))

    # Red line window
    left = max(0, center - window//2 + lag)
    right = min(len(y)-1, center + window//2 + lag)

    fig1.add_trace(go.Scatter(
        x=y.index[left:right],
        y=y.values[left:right],
        mode="lines",
        line=dict(color="red", width=3),
        name="Window segment"
    ))

    fig1.update_layout(title="Energy (y) with sliding window")

    # ---------------------
    #  Plot 2: Meteorology (x[variable])
    # ---------------------
    xv = x[variable]

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=xv.index, y=xv.values,
        mode="lines",
        name=f"Meteorology: {variable}"
    ))

    left2 = max(0, center - window//2)
    right2 = min(len(x)-1, center + window//2)

    fig2.add_trace(go.Scatter(
        x=xv.index[left2:right2],
        y=xv.values[left2:right2],
        mode="lines",
        line=dict(color="red", width=3),
        name="Window segment"
    ))

    fig2.update_layout(title=f"Meteorology ({variable}) with sliding window")

    # ---------------------
    #  Plot 3: SWC
    # ---------------------
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=SWC.index, y=SWC.values,
        mode="lines",
        name="SWC"
    ))

    # red dot = center+lag
    idx = center + lag
    if 0 <= idx < len(SWC):
        fig3.add_trace(go.Scatter(
            x=[SWC.index[idx]],
            y=[SWC.values[idx]],
            mode="markers",
            marker=dict(color="red", size=10),
            name="current SWC"
        ))

    fig3.update_layout(
        title=f"Sliding Window Correlation (Global Corr = {global_corr:.3f})",
        yaxis=dict(range=[-1,1])
    )

    return fig1, fig2, fig3

def apply_theme(group):
    if group == "blue":
        sidebar = "#3c63a7"
    elif group == "gray":
        sidebar = "#5f6f8f"
    elif group == "purple":
        sidebar = "#8b5fd2"
    else:
        sidebar = "#232020"

    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] > div {{
        background-color: {sidebar} !important;
        border-radius: 6px;
        padding-top: 20px;
        padding-left: 10px;
        padding-right: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)