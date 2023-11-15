import os
import quixstreams as qx
import pandas as pd
import time
from datetime import datetime
import threading
import re

# True = keep original timings.
# False = No delay! Speed through it as fast as possible.
keep_timing = "keep_timing" in os.environ and os.environ["keep_timing"] == "1"

# If the process is terminated on the command line or by the container
# setting this flag to True will tell the loops to stop and the code
# to exit gracefully.
shutting_down = False

# Quix Platform injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient()

# The producer topic is where the data will be published to
# It's the output from this demo data source code.
print("Opening output topic")
producer_topic = client.get_topic_producer(os.environ["output"])

# counters for the status messages
row_counter = 0
published_total = 0


def publish_row(row):
    global row_counter
    global published_total

    # create a DataFrame using the row
    df_row = pd.DataFrame([row])

    # add a new timestamp column with the current data and time
    df_row['timestamp'] = datetime.utcnow()

    # publish the data to the Quix stream created earlier
    stream_producer = producer_topic.get_or_create_stream(row['userId'])
    stream_producer.timeseries.publish(df_row)

    row_counter += 1

    if row_counter == 10:
        row_counter = 0
        published_total += 10
        print(f"Published {published_total} rows")


def get_product_id(url):
    match = re.search(r"http://www.acme.com/(\w+)/(\w+)", url)

    if match is not None:
        return match.group(2)

    return url


def process_csv_file(csv_file):
    global shutting_down

    # Read the CSV file into a pandas DataFrame
    print("TSV file loading.")
    df = pd.read_csv(csv_file, sep="\t")

    print("File loaded.")

    row_count = len(df)
    print(f"Publishing {row_count} rows.")

    df = df.rename(columns={
        "Visitor Unique ID": "userId",
        "IP Address": "ip",
        "29": "userAgent",  # The original file does not have name for this column
        "Unix Timestamp": "original_timestamp",
    })

    df["userId"] = df["userId"].apply(lambda x: x.strip("{}"))
    df["productId"] = df["Product Page URL"].apply(get_product_id)

    # Get subset of columns, so it's easier to work with
    df = df[["original_timestamp", "userId", "ip", "userAgent", "productId"]]

    # Get the column headers as a list
    headers = df.columns.tolist()

    # If shutdown has been requested, exit the loop.
    while not shutting_down:
        # Iterate over the rows and send them to the API
        for index, row in df.iterrows():

            # If shutdown has been requested, exit the loop.
            if shutting_down:
                break

            # Create a dictionary that includes both column headers and row values
            row_data = {header: row[header] for header in headers}
            publish_row(row_data)

            if not keep_timing:
                # Don't want to keep the original timing or no timestamp? That's ok, just sleep for 200ms
                time.sleep(0.2)
            else:
                # Delay sending the next row if it exists
                # The delay is calculated using the original timestamps and ensure the data
                # is published at a rate similar to the original data rates
                if index + 1 < len(df):
                    current_timestamp = pd.to_datetime(row['original_timestamp'], unit='s')
                    next_timestamp = pd.to_datetime(df.at[index + 1, 'original_timestamp'], unit='s')
                    time_difference = next_timestamp - current_timestamp
                    delay_seconds = time_difference.total_seconds()

                    # handle < 0 delays
                    if delay_seconds < 0:
                        delay_seconds = 0

                    if delay_seconds > 10:
                        delay_seconds = 10

                    time.sleep(delay_seconds)


# Run the CSV processing in a thread
processing_thread = threading.Thread(target=process_csv_file, args=('omniture-logs.tsv',))
processing_thread.start()


# Run this method before shutting down.
# In this case we set a flag to tell the loops to exit gracefully.
def before_shutdown():
    global shutting_down
    print("Shutting down")

    # set the flag to True to stop the loops as soon as possible.
    shutting_down = True


# keep the app running and handle termination signals.
qx.App.run(before_shutdown=before_shutdown)

print("Exiting.")
