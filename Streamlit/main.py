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

redis_host = ""
redis_port = ""
redis_password = ""

# work out which environment we're running on!
# check for Quix__Workspace__Id to see if we are in Quix platform.
if os.environ.get("Quix__Workspace__Id") is not None:
    # this is running in Quix
    # attempt to get these from environment variables
    redis_host = os.environ.get("redis_host")
    redis_port = os.environ.get("redis_port")
    redis_password = os.environ.get("redis_password")
elif st.secrets["redis_host"] is not None:
    # this is running in Streamlit and the 'redis_host' secret is available
    # attempt to get these from streamlit secrets
    redis_host = st.secrets.redis_host
    redis_port = st.secrets.redis_port
    redis_password = st.secrets.redis_password
else:
    # we don't know where this is running. Make sure you set the values for:
    print("We don't know where this is running. Make sure you set the values for:")
    print("redis_host")
    print("redis_port")
    print("redis_password")
    pass

r = redis.Redis(
    host=st.secrets.redis_host,
    port=st.secrets.redis_port,
    password=st.secrets.redis_password,
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

# A placeholder for the raw data table
placeholder_raw = st.empty()

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

        fig = px.line(df, x="datetime", y="count", height=310)
        fig.update_xaxes(title_text='Time', tickformat='%H:%M')
        fig.update_yaxes(title_text='Visits', range=[0, max(1, max(df['count']))])  # Set y minimum always 0
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

        fig = px.line(df, x="datetime", y="count", height=310)
        fig.update_xaxes(title_text='Time', tickformat='%H:%M')
        fig.update_yaxes(title_text='Sessions', range=[0, max(1, max(df['count']))])  # Set y minimum always 0
        st.plotly_chart(fig, use_container_width=True)

    with placeholder_col13.container():
        popularity = StringIO(r.get("device_type_popularity"))
        chart_df = pd.read_json(popularity)

        if chart_df.empty:
            st.markdown("N/A")
            continue

        fig = px.bar(chart_df, y="Device", x="Percentage", color="Device type", orientation="h", height=270)
        fig.update_layout(
            barmode='stack',
            yaxis={'categoryorder': 'total ascending'},
            hovermode="x",
            bargap=0.1,
            bargroupgap=0.1,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                xanchor="center",
                x=0.5
            )
        )

        fig.update_traces(texttemplate='%{value:.2f}%', textposition='inside')
        fig.update_xaxes(visible=False, showticklabels=False)
        fig.update_yaxes(visible=False, showticklabels=False)

        st.plotly_chart(fig, use_container_width=True)

    with placeholder_col21.container():
        # Top 10 viewed pages in the last hour
        products_last_hour = StringIO(r.get("products_last_hour"))
        df = pd.read_json(products_last_hour)
        st.dataframe(df, hide_index=True, use_container_width=True)

    with placeholder_col22.container():
        # Latest 10 Visitor Details
        data = StringIO(r.get("latest_visitors"))
        df = pd.read_json(data)
        st.dataframe(df, hide_index=True, use_container_width=True)

    with placeholder_col23.container():
        # Category popularity in the Last Hour
        data = StringIO(r.get("category_popularity"))
        df = pd.read_json(data)

        if df.empty:
            st.markdown("N/A")
            continue

        # Draw a pie chart
        fig = px.pie(df, values='count', names='category')
        st.plotly_chart(fig, use_container_width=True)

    # Display the raw dataframe data
    with placeholder_raw.container():
        st.markdown("### Raw Data View")
        data = StringIO(r.get("raw_data"))
        if data is None:
            continue
        real_time_df_copy = pd.read_json(data)
        st.dataframe(real_time_df_copy, hide_index=True)

    # Wait for one second before asking for new data from Quix
    time.sleep(1)