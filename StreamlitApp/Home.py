import streamlit as st
import datetime

st.set_page_config(
    page_title="Energy & Weather Analytics",
    page_icon="⚡",
    layout="wide"
)

pages = {
    "🏠 Home": [ st.Page("pages/frontpage.py", title="Introduction", url_path="front") ],

    "📊 Exploratory Analysis": [
        st.Page("pages/Exploratory/main.py", title="Overview", url_path="exploratory"),
    ],

    "🔍 Quality Check": [
        st.Page("pages/Quality_check/main.py", title="Overview", url_path="quality"),
    ],

    "🚀 Advanced Analysis": [
        st.Page("pages/Advanced/main.py", title="Overview", url_path="advanced"),
    ]
}

pg = st.navigation(pages)
pg.run()
