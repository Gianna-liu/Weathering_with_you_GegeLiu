import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    """Load data from a CSV file."""
    df = pd.read_csv('data/open-meteo-subset.csv')
    df['time'] = pd.to_datetime(df['time'])
    return df
