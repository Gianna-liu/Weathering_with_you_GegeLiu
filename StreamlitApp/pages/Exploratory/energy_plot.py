# mongodb.py
import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tools.utils import get_elhub_data


def render_energy_page(df, mode):
    """
    mode = "Production" or "Consumption"
    df   = df_prod or df_cons
    """

    #  -------------------Choose the group column based on mode  -------------------
    group_col = "productiongroup" if mode == "Production" else "consumptiongroup"

    # Two columns layout

    col1, col2 = st.columns(2)

    # Pie Chart

    with col1:

        st.markdown(f"#### 1. {mode} Distribution")

        price_area = st.session_state.expl_price_area

        df_area = df[df["pricearea"] == price_area]
        df_sum = df_area.groupby(group_col)["quantitykwh"].sum().reset_index()

        fig1 = px.pie(
            df_sum,
            names=group_col,
            values="quantitykwh",
            title=f"Total {mode} — Price Area {price_area}",
        )

        fig1.update_traces(
            texttemplate="%{label} (%{percent})",
            pull=[0.02] * len(df_sum),
            textfont_size=13,
        )

        fig1.update_layout(
            legend_title="Groups",
            margin=dict(t=150, b=30, l=20, r=20)
        )

        st.plotly_chart(fig1, use_container_width=True)


    #  ------------------- Hourly Trend  -------------------

    with col2:
        st.markdown(f"#### 2. Hourly {mode} Trend")

        # group selector
        group = st.pills(
            "Select Group",
            options=sorted(df[group_col].unique()),
            default=[sorted(df[group_col].unique())[0]],
            key=f"group_{mode}",
            selection_mode="single",
        )

        month = st.selectbox(
            "Select Month",
            range(1, 13),
            key=f"month_{mode}"
        )

        df_month = df[
            (df["pricearea"] == price_area)
            & (df[group_col] == group)
            & (pd.to_datetime(df["starttime"]).dt.month == month)
        ]

        df_month = df_month.sort_values("starttime")

        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=pd.to_datetime(df_month["starttime"]),
                y=df_month["quantitykwh"],
                mode="lines+markers",
                name=group,
            )
        )

        fig2.update_layout(
            xaxis_title="Time",
            yaxis_title="Quantity (kWh)",
            title=f"{mode} Trend — {price_area}, Month {month}",
        )

        st.plotly_chart(fig2, use_container_width=True)



#  ------------------- Main page logic with tabs -------------------
def run():

    st.markdown("### Yearly Electricity Overview — Production & Consumption")

    year = st.session_state.expl_year
    price_area = st.session_state.expl_price_area

    st.info(f"Current selection → Year: **{year}**, Price Area: **{price_area}**")

    # Load data for selected year
    start_dt = pd.Timestamp(f"{year}-01-01")
    end_dt   = pd.Timestamp(f"{year}-12-31")

    df_prod, df_cons = get_elhub_data(start_dt, end_dt)


    # Tabs for Production & Consumption
    tab_prod, tab_cons = st.tabs(["📈 Production", "📉 Consumption"])

    with tab_prod:
        render_energy_page(df_prod, mode="Production")

    with tab_cons:
        render_energy_page(df_cons, mode="Consumption")


