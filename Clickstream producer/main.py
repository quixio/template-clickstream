from quixstreams import Application
from datetime import datetime
import pandas as pd
import time
import json
import re
import os


# import the dotenv module to load environment variables from a file
from dotenv import load_dotenv
load_dotenv()

# If the process is terminated on the command line or by the container
# setting this flag to True will tell the loops to stop and the code
# to exit gracefully.
shutting_down = False

# Create an Application.
app = Application(use_changelog_topics=False)

# Define the topic using the "output" environment variable
topic_name = os.getenv("output", "")
if topic_name == "":
    raise ValueError("The 'output' environment variable is required. This is the output topic that data will be published to.")

topic = app.topic(topic_name)

# Create a pre-configured Producer object.
# Producer is already setup to use Quix brokers.
# It will also ensure that the topics exist before producing to them if
# Application is initiliazed with "auto_create_topics=True" (the default).
producer = app.get_producer()

# counters for the status messages
row_counter = 0
published_total = 0


def publish_row(row):
    global row_counter
    global published_total

    # add a new timestamp column with the current data and time
    row['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')    

    # Serialize row_data to a JSON string
    json_data = json.dumps(row)
    # Encode the JSON string to a byte array
    serialized_value = json_data.encode('utf-8')
    
    print(row)
    stream_id = row['userId']
    producer.produce(
        topic=topic.name,
        key=stream_id,
        value=serialized_value
    )

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


def check_is_int(current_timestamp):
    # Check if they are already ints or strings that can be cast to an int
    if isinstance(current_timestamp, int):
        return current_timestamp
    elif isinstance(current_timestamp, str) and current_timestamp.isdigit():
        return int(current_timestamp)
    else:
        print("current_timestamp is not an integer or string representing an integer. Defaulting to now.")
        return int(datetime.now().timestamp())


def main(csv_file):
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

            # We're going to keep it simple and just wait 500ms before handling the next row
            # if you wanted to get fancy you could implement logic to work out the delay till 
            # the next row based on the delta between timestamps.
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        # Get the directory of the currently running file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        main(f'{current_dir}/omniture-logs.tsv')
        # main(f'{current_dir}/test-data.csv')
        
    except KeyboardInterrupt:
        # set the flag to True to stop the loops as soon as possible.
        shutting_down = True
        print("Exiting.")
