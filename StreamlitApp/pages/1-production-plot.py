# mongodb.py
import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import get_elhub_data


################################### 1. Connect to the Mongodb to load data ###################################
df = get_elhub_data()

################################### 2. Dispaly the data ###################################
st.title('Yearly & Hourly Production Overview by Price Area and Production Group in 2021')

# Create two colimns
col1, col2 = st.columns(2)

# The left col for the pie chart
with col1:
    st.subheader("1. Total Production Distribution by Price Area and Production Group")
    
    # define a radio 
    price_area = st.radio(label = "Step1: Select Price Area",
                          options = sorted(df['pricearea'].unique()),
                          key="price_area") # get the option from input and sort order

    df_area = df[df['pricearea'] == price_area] # filter the data with input option
    df_sub1 = df_area.groupby('productiongroup')['quantitykwh'].sum().reset_index() # aggregate the data

    # use plotly.express to plot the pie chart
    fig1 = px.pie(
        df_sub1,
        names='productiongroup',
        values='quantitykwh',
        title=f"Total Production - Price Area {price_area}"
    )
    # Modify the structure of the plot
    fig1.update_traces(textinfo='percent+label',
                       pull=[0.05]*len(df_sub1),
                       textfont_size=15,
                       domain={'x': [0, 0.9], 'y': [0, 0.8]} # modify the size of the figure
                       )
    # Define the layout of the whole plot, like the layout of the legend, title
    fig1.update_layout(
        legend_title=dict(
            text='Production Groups',
            font=dict(size=18)
            ),
        margin=dict(t=160),
        title=dict(text=f"Total Production of each Group - {price_area}", font=dict(size=16), y=0.95),
        legend=dict(
            orientation="h",
            y=-0.3,
            x=0.5,
            xanchor="center"
        ),
    )
    # Display the Plotly chart
    st.plotly_chart(fig1, use_container_width=True)


with col2:

    st.subheader("2. Hourly Production Trend")

    # get the unique value for each productiongroup
    production_group = st.pills("Step2: Select Production Groups",
                      options=sorted(df['productiongroup'].unique()),
                      default=["hydro"],
                      key="production_group",
                      selection_mode="single")
    
    # get the unique value for each month
    month = st.selectbox("Step3: Select Month", range(1,13))

    # Filter the DataFrame based on selected price area, production groups, and month
    df_month = df[(df['pricearea'] == price_area) &
                  (df['productiongroup'] == production_group) &
                  (pd.to_datetime(df['starttime']).dt.month == month)]
    
    fig2 = go.Figure()
    # Loop through each selected production group and create a separate line
    df_g = df_month[df_month['productiongroup'] == production_group].sort_values('starttime')
    fig2.add_trace(go.Scatter(
        x=pd.to_datetime(df_g['starttime']),
        y=df_g['quantitykwh'],
        mode='lines+markers',
        name=production_group
    ))
  
    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="Quantity kWh",
        title=f"Monthly Production Trend - {price_area} Month {month}",
        legend_title="Production Groups"
    )
    # Display the Plotly chart
    st.plotly_chart(fig2, use_container_width=True)



with st.expander("Data Source"):
    st.write("""
        This dataset comes from the [Elhub API PRODUCTION_PER_GROUP_MBA_HOUR](https://api.elhub.no). 
        It was loaded into Cassandra, filtered locally using PySpark, 
        stored in MongoDB, and visualized with Streamlit.
    """)