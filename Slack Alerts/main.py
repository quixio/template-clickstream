import asyncio
from datetime import datetime, timedelta

import quixstreams as qx
import os
import pandas as pd
import requests

last_timestamp = None
last_message_sent = None

# Send alerts to this Slack webhook URL
webhook_url = os.environ.get("webhook_url")

# Send alerts if we haven't received data in the last hour
timeout = int(os.environ.get("timeout", 3600))

# Send alerts every 10 minutes
interval = int(os.environ.get("interval", 600))

# keep the main loop running
run = True


def on_dataframe_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    global last_timestamp

    last_timestamp = datetime.now()

    # Here we can inspect the data and send alerts if needed, for example if category is None
    if df["category"].isnull().values.any():
        print("No category found in data. Sending alert message.")
        send_alert_message("No category found. Please, check the Data Enrichment service.")


# Callback called for each incoming stream
def read_stream(stream_consumer: qx.StreamConsumer):
    # React to new data received from input topic.
    stream_consumer.timeseries.on_dataframe_received = on_dataframe_handler


def send_alert_message(msg: str):
    global last_message_sent, webhook_url

    if last_message_sent is None or last_message_sent < datetime.now() - timedelta(seconds=interval):
        last_message_sent = datetime.now()
        slack_message = {"message": msg}
        res = requests.post(webhook_url, json=slack_message)
        if not res.ok:
            print(res.status_code, res.text)
    else:
        print(f"Alert message was sent less than {interval} seconds ago. Skipping.")


# Check that we have received data in the last 1 hour
async def check_data():
    global last_timestamp

    while run:
        print("Checking...")
        print("Last message:", last_timestamp)
        if last_timestamp is not None and last_timestamp < datetime.now() - timedelta(
                seconds=timeout) and webhook_url is not None:
            # Send alert message
            print("No data received in the last hour. Sending alert message.")
            send_alert_message(f"No data received in the last hour in topic {os.environ['input']}")

        await asyncio.sleep(60)


def before_shutdown():
    global run
    run = False


async def start_loop():
    # Quix injects credentials automatically to the client.
    # Alternatively, you can always pass an SDK token manually as an argument.
    client = qx.QuixStreamingClient()

    print("Opening input and output topics")
    consumer_topic = client.get_topic_consumer(os.environ["input"])

    # Hook up events before initiating read to avoid losing out on any data
    consumer_topic.on_stream_received = read_stream

    print("Listening to streams. Press CTRL-C to exit.")
    qx.App.run(before_shutdown=before_shutdown)


async def main():
    # Start the main loop
    await asyncio.gather(start_loop(), check_data())


if __name__ == "__main__":
    asyncio.run(main())
