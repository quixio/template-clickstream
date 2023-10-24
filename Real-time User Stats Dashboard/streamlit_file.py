import time
import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

from app.conf import (
    STREAMLIT_DATAFRAME_POLL_PERIOD,
)
from app.streamlit_utils import get_stream_df

# Basic configuration of the Streamlit dashboard
st.set_page_config(
    page_title="Real-Time User Stats Dashboard",
    page_icon="✅",
    layout="wide",
)


# DASHBOARD LAYOUT SECTION
# The dashboard layout will consist of 3 columns and two rows.
col11, col12, col13 = st.columns(3)
with col11:
    # Header of the first column
    st.markdown("### Average visits in the last 15 minutes")
    # A placeholder for the first chart to update it later with data
    placeholder_col11 = st.empty()

with col12:
    # Header of the second column
    st.markdown("### Sessions in the last 8 hours")
    # A placeholder for the second chart to update it later with data
    placeholder_col12 = st.empty()

with col13:
    # Header of the second column
    st.markdown("### Right now")
    # A placeholder for the second chart to update it later with data
    placeholder_col13 = st.empty()

col21, col22, col23 = st.columns(3)
with col11:
    # Header of the first column
    st.markdown("### Top 10 viewed pages in the last hour")
    # A placeholder for the first chart to update it later with data
    placeholder_col21 = st.empty()

with col12:
    # Header of the second column
    st.markdown("### Latest Visitor Details")
    # A placeholder for the second chart to update it later with data
    placeholder_col22 = st.empty()

with col13:
    # Header of the second column
    st.markdown("### Category popularity in the Last Hour")
    # A placeholder for the second chart to update it later with data
    placeholder_col23 = st.empty()

# A placeholder for the raw data table
placeholder_raw = st.empty()

# REAL-TIME METRICS SECTION
# Below we update the charts with the data we receive from Quix in real time.
# Each 2s Streamlit requests new data from Quix and updates the charts.
# Keep the dashboard layout code before "while" loop, otherwise new elements
# will be appended on each iteration.
while True:
    # Wait for the streaming data to become available
    real_time_df = get_stream_df()
    print(f"Receive data from Quix. Total rows: {len(real_time_df)}")
    # The df can be shared between threads and changed over time, so we copy it
    real_time_df_copy = real_time_df[:]

    with placeholder_col11.container():
        # count visits per minute in the last 15 minutes
        df = real_time_df_copy[
            real_time_df_copy["datetime"] > (datetime.datetime.utcnow() - datetime.timedelta(minutes=15))]

        # Aggregate by minute
        df = df.groupby(pd.Grouper(key='datetime', freq='1min')).size().reset_index(name='count')

        fig = px.line(df, x="datetime", y="count", height=310)
        fig.update_xaxes(title_text='Time', tickformat='%H:%M')
        fig.update_yaxes(title_text='Visits', range=[0, max(df['count'])])  # Set y minimum always 0
        st.plotly_chart(fig)

    with placeholder_col12.container():
        # Sessions in the last 8 hours (segmented by 30 mins)
        df = real_time_df_copy[
            real_time_df_copy["datetime"] > (datetime.datetime.utcnow() - datetime.timedelta(hours=8))]

        # Group per visitor
        df = df.groupby(['datetime', 'userId']).size().reset_index(name='count')

        # Aggregate by 30 minutes (sum counts)
        df = df.groupby(pd.Grouper(key='datetime', freq='30min')).sum('count').reset_index()

        fig = px.line(df, x="datetime", y="count", height=310)
        fig.update_xaxes(title_text='Time', tickformat='%H:%M')
        fig.update_yaxes(title_text='Sessions', range=[0, max(df['count'])])  # Set y minimum always 0
        st.plotly_chart(fig, use_container_width=True)

    with placeholder_col13.container():
        # Right now, group by device type
        df = real_time_df_copy[
            real_time_df_copy["datetime"] > (datetime.datetime.utcnow() - datetime.timedelta(minutes=10))]

        # Keep unique userId
        df = df.drop_duplicates(subset=['userId'])

        df = df.groupby(['deviceType']).size().reset_index(name='count')

        total = df['count'].sum()
        mobile = df[df['deviceType'] == 'Mobile']['count'].sum() / total * 100
        tablet = df[df['deviceType'] == 'Tablet']['count'].sum() / total * 100
        desktop = df[df['deviceType'] == 'Desktop']['count'].sum() / total * 100
        other = 100.0 - mobile - tablet - desktop

        title = f"{total} active users on site"
        x_data = [[desktop, tablet, mobile, other]]
        labels = ["Desktop", "Tablet", "Mobile", "Other"]
        y_data = ["Device type"]

        data = [["Device type", "Desktop", desktop],
                ["Device type", "Tablet", tablet],
                ["Device type", "Mobile", mobile],
                ["Device type", "Other", other]]

        chart_df = pd.DataFrame(data, columns=["Device", "Device type", "Percentage"])

        fig = px.bar(chart_df, y="Device", x="Percentage", color="Device type", orientation="h", height=270)
        fig.update_layout(
            barmode='stack',
            yaxis={'categoryorder':'total ascending'},
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

        st.markdown(title)
        st.plotly_chart(fig, use_container_width=True)

    with placeholder_col21.container():
        # Top 10 viewed pages in the last hour
        df = real_time_df_copy[
            real_time_df_copy["datetime"] > (datetime.datetime.utcnow() - datetime.timedelta(hours=1))]
        df = df.groupby(['productId', 'category']).size().reset_index(name='count')
        df = df.sort_values(by=['count'], ascending=False).head(10)
        st.dataframe(df, hide_index=True, use_container_width=True)

    with placeholder_col22.container():
        # Latest 10 Visitor Details
        # Get last 10 rows
        df = real_time_df_copy.tail(10)[:]
        df["Date and Time"] = pd.to_datetime(df["datetime"])
        df = df[['Date and Time', 'ip', 'country']]
        st.dataframe(df, hide_index=True, use_container_width=True)

    with placeholder_col23.container():
        # Category popularity in the Last Hour
        df = real_time_df_copy[
            real_time_df_copy["datetime"] > (datetime.datetime.utcnow() - datetime.timedelta(hours=1))]
        df = df.groupby(['category']).size().reset_index(name='count')
        df = df.sort_values(by=['count'], ascending=False)

        # Draw a pie chart
        fig = px.pie(df, values='count', names='category')
        st.plotly_chart(fig, use_container_width=True)

    # Display the raw dataframe data
    with placeholder_raw.container():
        st.markdown("### Raw Data View")
        st.dataframe(real_time_df_copy)

    # Wait for 2s before asking for new data from Quix
    time.sleep(STREAMLIT_DATAFRAME_POLL_PERIOD)
