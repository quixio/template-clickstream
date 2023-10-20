import time
import streamlit as st
import pandas as pd

from app.conf import (
    STREAMLIT_DATAFRAME_POLL_PERIOD,
)
from app.streamlit_utils import get_stream_df, draw_line_chart_failsafe

# Basic configuration of the Streamlit dashboard
st.set_page_config(
    page_title="Real-Time Data Science Dashboard",
    page_icon="✅",
    layout="wide",
)

# PARAMETERS SECTION
# Define a list of parameters to show in select widgets.
AVAILABLE_PARAMS = [
    "Visitor Age Group",
    "Visitor Gender",
    "Product Category",
    "Visitor Birthdate",
]

# DASHBOARD LAYOUT SECTION
# The dashboard layout will consist of 2 columns and one row.
# Each column will have a select widget with available parameters to plot,
# and a chart with the real-time data from Quix, that will be updated in real-time.
# The last row will have a table with raw data.
col1, col2 = st.columns(2)
with col1:
    # Header of the first column
    st.markdown("### Chart 1 Title")
    # Select for the first chart
    parameter1 = st.selectbox(
        label="PARAMETER",
        options=AVAILABLE_PARAMS,
        index=0,
        key="parameter1",
        label_visibility="visible",
    )
    # A placeholder for the first chart to update it later with data
    placeholder_col1 = st.empty()

with col2:
    # Header of the second column
    st.markdown("### Chart 2 Title")
    # Select for the second chart
    parameter2 = st.selectbox(
        label="PARAMETER",
        options=AVAILABLE_PARAMS,
        index=1,
        key="parameter2",
        label_visibility="visible",
    )
    # A placeholder for the second chart to update it later with data
    placeholder_col2 = st.empty()

# A placeholder for gender - category table
placeholder_gender_category = st.empty()

# A placeholder for age group - category table
placeholder_age_group_category = st.empty()

# A placeholder for 5 most active visitors table
placeholder_most_active_visitors = st.empty()

# A placeholder for the raw data table
placeholder_raw = st.empty()

# REAL-TIME METRICS SECTION
# Below we update the charts with the data we receive from Quix in real time.
# Each 0.5s Streamlit requests new data from Quix and updates the charts.
# Keep the dashboard layout code before "while" loop, otherwise new elements
# will be appended on each iteration.
while True:
    # Wait for the streaming data to become available
    real_time_df = get_stream_df()
    print(f"Receive data from Quix. Total rows: {len(real_time_df)}")
    # The df can be shared between threads and changed over time, so we copy it
    real_time_df_copy = real_time_df[:]

    # with placeholder_col1.container():
    #     # Plot line chart in the first column
    #     draw_line_chart_failsafe(
    #         real_time_df_copy,
    #         # Use "datetime" column for X axis
    #         x="Date and Time",
    #         # Use a column from the first select widget for Y axis
    #         # You may also plot multiple values
    #         y=[parameter1],
    #     )
    #
    # # Plot line chart in the second column
    # with placeholder_col2.container():
    #     draw_line_chart_failsafe(
    #         real_time_df_copy,
    #         x="Date and Time",
    #         # Use a column from the second select widget for Y axis
    #         y=[parameter2],
    #     )

    # Display categories grouped by gender
    with placeholder_gender_category.container():
        st.markdown("### Category per gender")
        df = real_time_df_copy.groupby(["gender", "category"]).size().reset_index(name="count")
        df_pivot = df.pivot(index='category', columns='gender', values='count')

        st.dataframe(df_pivot)

    # Display categories grouped by age group
    with placeholder_age_group_category.container():
        st.markdown("### Category per age group")
        df = real_time_df_copy.groupby(["ageGroup", "category"]).size().reset_index(name="count")
        df_pivot = df.pivot(index='category', columns='ageGroup', values='count')

        st.dataframe(df_pivot)

    # Display 5 most active visitors
    with placeholder_most_active_visitors.container():
        st.markdown("### 5 most active visitors in the last hour")
        # Get data only from last hour
        df = real_time_df_copy[real_time_df_copy["datetime"] > (pd.Timestamp.now() - pd.Timedelta(hours=1))]

        df = df.groupby(["userId", "gender", "ageGroup"]).size().reset_index(name="count")
        df = df.sort_values(by=['count'], ascending=False).head(5)
        st.dataframe(df)

    # Display the raw dataframe data
    with placeholder_raw.container():
        st.markdown("### Raw Data View")
        st.dataframe(real_time_df_copy)

    # Wait for 0.5s before asking for new data from Quix
    time.sleep(STREAMLIT_DATAFRAME_POLL_PERIOD)
