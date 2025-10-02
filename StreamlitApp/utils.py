import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    script_path = Path(__file__).resolve()
    root = script_path.parent
    current = script_path.parent

    while current != current.parent:
        if (current / ".git").exists():
            root = current
            break
        current = current.parent

    file_path = root / "StreamlitApp" / "data" / filename
    df = pd.read_csv(file_path, parse_dates=['time'])
    return df
