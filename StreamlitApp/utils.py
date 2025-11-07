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

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_elhub_data():
    client = init_connection()
    db = client['elhub_db']
    collection = db['production_data']
    items = list(collection.find({}, {"_id": 0}))
    df_production = pd.DataFrame(items)
    df_production['starttime'] = pd.to_datetime(df_production['starttime'])
    df_production = df_production.sort_values("starttime")
    return df_production

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

def plot_outlier_detection_dct(hourly_dataframe, selected_variable: str, W_filter: float = 1/(10*24), coef_k: float = 3):
    selected_data = hourly_dataframe[selected_variable]
    N = hourly_dataframe.shape[0]
    dt = 1
    W = np.linspace(0, 1/(2*dt), N) # cycles/hour
    # Discrete Cosine transform
    fourier_signal = dct(selected_data.values, type=1, norm="forward")
    filtered_fourier_signal = fourier_signal.copy()
    filtered_fourier_signal[(W < W_filter)] = 0 # high-pass filter
    satv = idct(filtered_fourier_signal, type=1, norm="forward")

    # Median absolute deviation
    coef_k = coef_k
    trimmed_means = stats.trim_mean(satv, 0.05)
    mad =stats.median_abs_deviation(satv)
    sd = mad * 1.4826
    # Find the boundaries
    upper_boundary = trimmed_means + coef_k * sd
    lower_boundary = trimmed_means - coef_k * sd
    # Detect the outliers
    outliers = satv[np.abs(satv-trimmed_means) > coef_k*sd]
    outliers_index = np.where(np.abs(satv-trimmed_means) > coef_k*sd)[0]

    # Plot data and add lines for +/- 3 SD and the identified outliers
    fig = go.Figure()
    fig.add_hline(y=upper_boundary,line_color='red',line_dash='dash',annotation_text=f'{coef_k}*SD (Upper)',annotation_position='top right')
    fig.add_hline(y=lower_boundary,line_color='red',line_dash='dash',annotation_text=f'{coef_k}*SD (Lower)',annotation_position='top right')
    fig.add_trace(go.Scatter(x=hourly_dataframe['date'], y=selected_data, mode='markers', marker=dict(color='blue'), name='normal'))
    fig.add_trace(go.Scatter(x=hourly_dataframe.loc[outliers_index,'date'], y=outliers, mode='markers', marker=dict(color='orange'), name='outlier'))
    fig.update_layout(title=f'The distribution of {selected_variable} with boundaries and outliers', xaxis_title='Time (hourly)', yaxis_title='Values')

    summary = {
        "variable": selected_variable,
        "num_sample": N,
        "Sigma Multiplier (k)":coef_k,
        "High-pass Filter W_cutoff":W_filter,
        "upper_boundary": upper_boundary,
        "lower_boundary": lower_boundary,
        "num_outliers": len(outliers_index),
        "ratio_outlier": round(len(outliers_index) / N * 100, 2)
    }
    return fig,summary


################################### 6.Check the data quality with LOF ###################################

def plot_outlier_detection_lof(hourly_dataframe,selected_variable: str, contamination: float = 0.01, n_neighbors: int = 20):
    selected_data = hourly_dataframe[[selected_variable]].copy()
    selected_data['index'] = selected_data.index

    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    pred_labels = lof.fit_predict(selected_data)

    # Separate normal and outliers
    outlier_mask = pred_labels == -1
    normal_mask = pred_labels == 1


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hourly_dataframe.loc[normal_mask, 'date'],y=selected_data.loc[normal_mask, selected_variable], mode='markers', marker=dict(color='blue'), name='normal'))
    fig.add_trace(go.Scatter(x=hourly_dataframe.loc[outlier_mask, 'date'],y=selected_data.loc[outlier_mask, selected_variable], mode='markers', marker=dict(color='orange'), name='outlier'))
    fig.update_layout(title=f'The distribution of {selected_variable} with outliers', xaxis_title='Time (hourly)', yaxis_title='Values')

    return fig

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