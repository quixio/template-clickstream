import streamlit as st
import plotly.express as px
from io import StringIO
import pandas as pd
import time
import redis
import os

# Basic configuration of the Streamlit dashboard
st.set_page_config(
    page_title="Real-Time User Stats Dashboard (Quix)",
    page_icon="✅",
    layout="wide",
    menu_items={
        'About': "This dashboard shows real-time user stats the Clickstream template. More info at https://quix.io"
    }
)

st.header("Real-Time User Stats Dashboard", divider="blue")
st.markdown(
"""This dashboard vizualizes real-time agreggations and statistics from a demo clickstream. The clickstream data is being streamed from a sample log file for an online retailer and processed in a Pipeline hosted in Quix—a cloud-native solution for building event streaming applications.

* To explore the back-end services that power this Dashboard, check out this Quix pipeline. (link: https://portal.platform.quix.ai/pipeline?workspace=demo-clickstream-aggregationservice )

* To see how real-time clickstream analysis can be used to trigger events in a front end, see our complimentary Clickstream Event Detection demo.(link: https://template-clickstream-front-end.vercel.app/)
""")

redis_host = ""
redis_port = ""
redis_password = ""

default_height = 200

# work out which environment we're running on!
# check for Quix__Workspace__Id to see if we are in Quix platform.
if os.environ.get("Quix__Workspace__Id") is not None:
    # this is running in Quix
    # attempt to get these from environment variables
    print("Getting Redis credentials from Quix environment variables")
    redis_host = os.environ.get("redis_host")
    redis_port = os.environ.get("redis_port")
    redis_password = os.environ.get("redis_password")
elif os.environ.get("redis_host") is not None:
    # this is running in Streamlit and the 'redis_host' secret is available
    # attempt to get these from streamlit secrets
    print("Getting Redis credentials from Streamlit secrets")
    redis_host = st.secrets.redis_host
    redis_port = st.secrets.redis_port
    redis_password = st.secrets.redis_password
else:
    # we don't know where this is running. Make sure you set the values for:
    print("We don't know where this is running. Make sure you set the values for:")
    print(" - redis_host")
    print(" - redis_port")
    print(" - redis_password")

r = redis.Redis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=True)

# DASHBOARD LAYOUT SECTION
# The dashboard layout will consist of 3 columns and two rows.
with st.container():
    col11, col12, col13 = st.columns(3)
    with col11:
        # Header of the first column
        st.header("Visitors in the last 15 minutes")
        # A placeholder for the first chart to update it later with data
        placeholder_col11 = st.empty()

    with col12:
        # Header of the second column
        st.header("Sessions in the last 8 hours")
        # A placeholder for the second chart to update it later with data
        placeholder_col12 = st.empty()

    with col13:
        # Header of the second column
        st.header("Right now")
        # A placeholder for the second chart to update it later with data
        placeholder_col13 = st.empty()

with st.container():
    col21, col22, col23 = st.columns(3)
    with col21:
        # Header of the first column
        st.header("Top 10 viewed pages in the last hour")
        # A placeholder for the first chart to update it later with data
        placeholder_col21 = st.empty()

    with col22:
        # Header of the second column
        st.header("Latest Visitor Details")
        # A placeholder for the second chart to update it later with data
        placeholder_col22 = st.empty()

    with col23:
        # Header of the second column
        st.header("Category popularity in the Last Hour")
        # A placeholder for the second chart to update it later with data
        placeholder_col23 = st.empty()

with st.container():
    col31, col32 = st.columns([1, 2])
    with col31:
        # Header of the first column
        st.header("Top 10 viewed pages in the last hour")
        # A placeholder for the first chart to update it later with data
        placeholder_col31 = st.empty()

    with col32:
        # Header of the second column
        st.header("Latest Visitor Details")
        # A placeholder for the second chart to update it later with data
        placeholder_col32 = st.empty()

# REAL-TIME METRICS SECTION
# Below we update the charts with the data we receive from Quix in real time.
# Each second Streamlit requests new data from Quix (via Redis) and updates the charts.
# Keep the dashboard layout code before "while" loop, otherwise new elements
# will be appended on each iteration.
while True:
    with placeholder_col11.container():
        # count visits per minute in the last 15 minutes
        data = StringIO(r.get("last_15_minutes"))
        df = pd.read_json(data)

        # Create a base dataframe with rows for each minute in the last 15 minutes rounded to the minute
        round_to_minute = pd.Timestamp.now().floor('min')
        base_df = pd.DataFrame(pd.date_range(end=round_to_minute, periods=15, freq='min'), columns=['datetime'])

        # Then merge the two dataframes by time and fill missing values with 0, so we have a value for each minute
        df = pd.merge(base_df, df, on='datetime', how='left').fillna(0)

        fig = px.line(df, x="datetime", y="count", height=default_height)
        fig.update_xaxes(title_text='Time', tickformat='%H:%M')
        fig.update_yaxes(title_text='Visits', range=[0, max(1, max(df['count']))])  # Set y minimum always 0
        fig.update_layout(margin=dict(r=5, l=5, t=15, b=15))
        st.plotly_chart(fig, use_container_width=True)

    with placeholder_col12.container():
        # Sessions in the last 8 hours (segmented by 30 mins)
        sessions = StringIO(r.get("sessions"))
        df = pd.read_json(sessions)

        # Create a base dataframe with rows for each minute in the last 15 minutes
        hour = pd.Timestamp.now().floor('h')
        base_df = pd.DataFrame(pd.date_range(end=hour, periods=16, freq='30min'), columns=['datetime'])

        # Then merge the two dataframes by time and fill missing values with 0, so we have a value for each minute
        df = pd.merge(base_df, df, on='datetime', how='left').fillna(0)

        # Draw a bar chart with time as x axis and sessions as y axis
        fig = px.bar(df, x="datetime", y="count", height=default_height)
        fig.update_xaxes(title_text='Time', tickformat='%H:%M')
        fig.update_yaxes(title_text='Sessions', range=[0, max(1, max(df['count']))])  # Set y minimum always 0
        fig.update_layout(margin=dict(r=5, l=5, t=15, b=15))
        st.plotly_chart(fig, use_container_width=True)

    with placeholder_col13.container():
        popularity = StringIO(r.get("device_type_popularity"))
        chart_df = pd.read_json(popularity)

        if chart_df.empty:
            st.markdown("N/A")
            continue

        # Create 2 columns
        c1, c2 = st.columns([1, 2])

        # Calculate the sum of all devices
        total_devices = chart_df['Total'].sum()
        c1.markdown(f"Total devices")
        c1.markdown(f"# {total_devices}")

        # Calculate the percentage of each device type
        chart_df['Percentage'] = (chart_df['Total'] / total_devices) * 100

        # Plot a pie chart in the second column with distinct colors for each device
        # Hide the percentage of each color if it is 0%
        chart_df = chart_df[chart_df['Percentage'] != 0]
        fig = px.pie(chart_df, values='Percentage', names='Device type', height=default_height, color='Device type')
        fig.update_layout(margin=dict(r=5, l=5, t=15, b=15))
        c2.plotly_chart(fig, use_container_width=True)

    with placeholder_col21.container():
        # Top 10 viewed pages in the last hour
        products_last_hour = StringIO(r.get("products_last_hour"))
        df = pd.read_json(products_last_hour)
        st.dataframe(df, hide_index=True, use_container_width=True, height=default_height)

    with placeholder_col22.container():
        # Latest 10 Visitor Details
        data = StringIO(r.get("latest_visitors"))
        df = pd.read_json(data)
        st.dataframe(df, hide_index=True, use_container_width=True, height=default_height)

    with placeholder_col23.container():
        # Category popularity in the Last Hour
        data = StringIO(r.get("category_popularity"))
        df = pd.read_json(data)

        if df.empty:
            st.markdown("N/A")
            continue

        # Draw a bar chart with distinct colors for each bar. Hide X axis title so we have more space for the chart
        fig = px.bar(df, x="category", y="count", height=default_height, color="category")
        #fig.update_xaxes(title_text='Category')
        fig.update_layout(xaxis_title=None, margin=dict(r=5, l=5, t=5, b=5))
        fig.update_yaxes(title_text='Visits', range=[0, max(1, max(df['count']))])
        st.plotly_chart(fig, use_container_width=True)

    # Display the raw dataframe data
    with placeholder_col32.container():
        st.markdown("### Raw Data View")
        data = StringIO(r.get("raw_data"))
        if data is None:
            continue
        real_time_df_copy = pd.read_json(data)
        st.dataframe(real_time_df_copy, hide_index=True)

    # Wait for one second before asking for new data from Quix
    time.sleep(1)
