import streamlit as st
from datetime import datetime
import pandas as pd

# ---------------------- Time Controls Widget ----------------------
def render_time_controls():
    st.subheader("⏳ Time Settings")

    #---------- INIT DEFAULTS ----------
    defaults = {
        "agg": "Monthly",     # default level
        "year": "2021",
        "month": "All",
        "day": "All",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ---------- FIRST ROW ----------
    c1, c2, c3 = st.columns([1, 1, 1])

    # Aggregation
    with c1:
        st.selectbox(
            "Aggregation",
            ["Daily", "Monthly", "Yearly", "All"],
            key="agg"
        )

    agg = st.session_state.agg

    # ---------- second row ----------
    with c2:
        if agg in ["Daily", "Monthly", "Yearly"]:
            st.selectbox(
                "Year",
                ["All", 2021, 2022, 2023, 2024],
                key="year"
            )

    with c3:
        if agg in ["Daily", "Monthly"]:
            st.selectbox(
                "Month",
                ["All"] + list(range(1, 13)),
                key="month"
            )

    # Daily to extra Day selector
    if agg == "Daily":
        d1, d2 = st.columns([1, 1])
        with d1:
            if st.session_state.month == "All":
                st.session_state.day = "All"
                st.write("Day: All (because Month=All)")
            else:
                st.selectbox(
                    "Day",
                    ["All"] + list(range(1, 32)),
                    key="day"
                )


# ---------------------- Time Range Getter ----------------------
def get_time_range():
    agg = st.session_state.agg
    year = st.session_state.year
    month = st.session_state.month
    day = st.session_state.day

    DATA_MIN = datetime.datetime(2021, 1, 1)
    DATA_MAX = datetime.datetime(2024, 12, 31, 23, 59, 59)

    # All data
    if agg == "All":
        return DATA_MIN, DATA_MAX

    # yearly
    if agg == "Yearly":
        if year == "All":
            return DATA_MIN, DATA_MAX
        start = datetime.datetime(int(year), 1, 1)
        end   = datetime.datetime(int(year), 12, 31, 23, 59, 59)
        return start, end

    # monthly
    if agg == "Monthly":
        if year == "All":
            return DATA_MIN, DATA_MAX
        if month == "All":
            start = datetime.datetime(int(year), 1, 1)
            end   = datetime.datetime(int(year), 12, 31, 23, 59, 59)
            return start, end

        start = datetime.datetime(int(year), int(month), 1)
        # next month
        if int(month) == 12:
            end = datetime.datetime(int(year), 12, 31, 23, 59, 59)
        else:
            end = datetime.datetime(int(year), int(month)+1, 1) - datetime.timedelta(seconds=1)
        return start, end

    # daily
    if agg == "Daily":
        if year == "All":
            return DATA_MIN, DATA_MAX
        if month == "All":
            start = datetime.datetime(int(year), 1, 1)
            end   = datetime.datetime(int(year), 12, 31, 23, 59, 59)
            return start, end

        if day == "All":
            start = datetime.datetime(int(year), int(month), 1)
            if int(month) == 12:
                end = datetime.datetime(int(year), 12, 31, 23, 59, 59)
            else:
                end = datetime.datetime(int(year), int(month)+1, 1) - datetime.timedelta(seconds=1)
            return start, end

        # specific day
        d = datetime.date(int(year), int(month), int(day))
        start = datetime.datetime.combine(d, datetime.time.min)
        end   = datetime.datetime.combine(d, datetime.time.max)
        return start, end

    # fallback
    return DATA_MIN, DATA_MAX


def render_time_selector():
    st.markdown(f"#### ⏱️ Select Time Range")

    # --- Aggregation selector ---
    aggregation = st.radio(
        "Aggregation",
        ["Daily", "Monthly", "Yearly"],
        horizontal=True,
        index=0
    )

    # --- daily mode ---
    if aggregation == "Daily":
        start_date = st.date_input("Start date", value=datetime(2021, 1, 1))
        end_date   = st.date_input("End date",   value=datetime(2021, 1, 31))

        start_date = pd.to_datetime(start_date)
        end_date   = pd.to_datetime(end_date)

    # --- monthly mode ---
    elif aggregation == "Monthly":
        col1, col2 = st.columns(2)

        with col1:
            start_year  = st.number_input("Start year", min_value=2000, max_value=2100, value=2021)
            start_month = st.number_input("Start month", min_value=1, max_value=12, value=1)

        with col2:
            end_year  = st.number_input("End year", min_value=2000, max_value=2100, value=2021)
            end_month = st.number_input("End month", min_value=1, max_value=12, value=12)

        start_date = pd.to_datetime(f"{start_year}-{start_month:02d}-01")
        end_date   = pd.to_datetime(f"{end_year}-{end_month:02d}-01") + pd.offsets.MonthEnd(0)

    # --- yearly mode ---
    elif aggregation == "Yearly":
        col1, col2 = st.columns(2)

        with col1:
            start_year = st.number_input("Start year", min_value=2000, max_value=2100, value=2021)

        with col2:
            end_year   = st.number_input("End year", min_value=2000, max_value=2100, value=2021)

        start_date = pd.to_datetime(f"{start_year}-01-01")
        end_date   = pd.to_datetime(f"{end_year}-12-31")

    # --- safety check ---
    if end_date < start_date:
        st.error(f"❌ Invalid period: End date ({end_date.date()}) is earlier than start date ({start_date.date()})")
        st.stop()   # Stop executing the rest of the script

    # --- Show selected period ---
    st.info(f"Selected period: **{start_date.date()} → {end_date.date()}**")

    return aggregation, start_date, end_date
