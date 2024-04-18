import os
import ssl
import time
import json
import redis
import queue
import asyncio
import threading
import websockets
import pandas as pd
import streamlit as st
from io import StringIO
from datetime import timedelta, datetime
import plotly.express as px

import ast

# base url to the websocket server running in the environment
base_websocket_url = 'wss://web-socket-subscriber-demo-clickstreamanalysis-migration.deployments.quix.io/topic'

# Dictionary to hold queues for each topic
data_queues = {}

async def websocket_reader(topic, data_queue, data_handler):
    uri = f"{base_websocket_url}/{topic}"
    # Create an SSL context that does not verify the certificate
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(uri, ssl=ssl_context) as websocket:
        while True:
            data = await websocket.recv()
            # print(f'Data in "{topic}" is :: {data}')
            if data is None:
                print(f"No data in {topic}.. sleeping for 1 second.")
                time.sleep(1)
            else:
                data_queue.put(json.loads(data))
                data_handler(data)

def start_websocket_thread(topic, data_handler):
    # Ensure that the data_queue for this topic is created before starting the thread
    if topic not in data_queues:
        data_queues[topic] = queue.Queue()
    asyncio.new_event_loop().run_until_complete(websocket_reader(topic, data_queues[topic], data_handler))

last_10_users = {}
def last_10_data_handler(data):
    global last_10_users
    # Here we receive json with the last 10 visitors details.
    # So just store it for use in the page.
    # print(data)
    last_10_users = data

# {
#   "start": 1713437330000,
#   "end": 1713437930000,
#   "value": {
#     "Desktop": 107,
#     "Mobile": 2
#   }
# }

device_types = {}
def device_type_data_handler(data):
    global device_types
    device_types = data

last_15min_visitors = []
def last_15min_visitors_data_handler(data):
    # Here we receive a count and a window timestamp. this needs to be added to the array.
    last_15min_visitors.append(json.loads(data))
    print(f"{len(last_15min_visitors)}")

# Start a WebSocket reader thread for each specific topic
threading.Thread(target=start_websocket_thread, args=("users-last-10",last_10_data_handler,), daemon=True).start()
threading.Thread(target=start_websocket_thread, args=("device-type",device_type_data_handler,), daemon=True).start()
threading.Thread(target=start_websocket_thread, args=("visitors-last-15min",last_15min_visitors_data_handler,), daemon=True).start()

with st.container():
    st.header("Visitors in the last 15 minutes")
    # A placeholder for the chart to update it later with data
    visitors_last_15_min_data_placeholder = st.empty()

    st.header("Last 10 site visitors")
    # A placeholder for the chart to update it later with data
    last_10_site_visitors_data_placeholder = st.empty()

    st.header("Visitor device type")
    # A placeholder for the chart to update it later with data
    visitor_device_type_data_placeholder = st.empty()

while True:

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
    # Visitors in the last 15 minutes
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
    # Keep only the last 900 items
    last_15min_visitors = last_15min_visitors[-900:]

    # Parse the JSON strings into dictionaries and convert the timestamp
    visitor_data = []
    for json_str in last_15min_visitors:
        data = json.loads(json_str)
        # Convert the timestamp from milliseconds to a datetime object
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        visitor_data.append(data)

    if visitor_data != []:

        # Create a DataFrame from the list of dictionaries
        visitors_df = pd.DataFrame(visitor_data)

        # Create a line graph using plotly
        fig = px.line(visitors_df, x='timestamp', y='count', title='Visitors in the last 15 minutes')
        visitors_last_15_min_data_placeholder.plotly_chart(fig, width=800, height=600)
    # End -- Visitors in the last 15 minutes

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
    # Last 10 site visitors
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
    if last_10_users != {}:
        last_10_users_dict = json.loads(json.loads(last_10_users))

        data = []
        index = []
        for key, value in last_10_users_dict.items():
            index.append(key)
            data.append(value)

        # Convert the data into a DataFrame
        visitors_df = pd.DataFrame(data, index=index)

        # Convert the data into a DataFrame
        visitors_df = pd.DataFrame(data, index=index)
        table_html = visitors_df.to_html().replace('<table', '<table style="width:800px; height:600px"')
        last_10_site_visitors_data_placeholder.markdown(table_html, unsafe_allow_html=True)
    # End -- Last 10 site visitors

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
    # Visitor device type
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
    if device_types != {}:
        devices_dict = json.loads(json.loads(device_types))
        print(devices_dict.values())
        device_counts = devices_dict['value']
        fig = px.pie(names=device_counts.keys(), values=device_counts.values())
        visitor_device_type_data_placeholder.plotly_chart(fig, width=800, height=600)
    # End -- Visitor device type


    time.sleep(0.5)