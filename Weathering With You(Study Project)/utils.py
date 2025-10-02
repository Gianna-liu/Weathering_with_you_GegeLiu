import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent  
    file_path = repo_root / "data" / filename
    # df = pd.read_csv('data/open-meteo-subset.csv')
    # df['time'] = pd.to_datetime(df['time'])
    return pd.read_csv(file_path)
