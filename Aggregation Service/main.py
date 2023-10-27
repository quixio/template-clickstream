import quixstreams as qx
import time
from threading import Thread
import os
import redis
import pandas as pd
import humanize
from rocksdict import Rdict

# make sure the state dir exists
if not os.path.exists("state"):
    os.makedirs("state")

# rocksDb is used to hold state, state.dict is in the `state` folder which is maintained for us by Quix
# so we just init the rocks db using `state.dict` which will be loaded from the file system if it exists
db = Rdict("state/state.dict")

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient()

# Use Input topic to stream data in our service
consumer_topic = client.get_topic_consumer(os.environ["input"])

# Create the redis client, to store the aggregated data
r = redis.Redis(
    host=os.environ['redis_host'],
    port=os.environ['redis_port'],
    password=os.environ['redis_password'],
    decode_responses=True)

columns = {
    "timestamp": pd.Series(dtype='datetime64[ns]'),
    "original_timestamp": pd.Series(dtype='int'),
    "userId": pd.Series(dtype='str'),
    "ip": pd.Series(dtype='str'),
    "userAgent": pd.Series(dtype='str'),
    "productId": pd.Series(dtype='str'),
    "category": pd.Series(dtype='str'),
    "title": pd.Series(dtype='str'),
    "gender": pd.Series(dtype='str'),
    "country": pd.Series(dtype='str'),
    "deviceType": pd.Series(dtype='str'),
    "age": pd.Series(dtype='int'),
    "birthdate": pd.Series(dtype='datetime64[ns]'),
    "datetime": pd.Series(dtype='datetime64[ns]')
}

columns_from_enrich = ["timestamp", "original_timestamp", "userId", "ip", "userAgent", "productId",
                       "category", "title", "gender", "country", "deviceType", "age", "birthdate"]

# Default value for the last hour data, will be initialized from state store
if "last_hour_data" not in db.keys():
    print("Initialize last_hour_data in state store")
    initial_df = pd.DataFrame(columns)
    db["last_hour_data"] = initial_df

if "eight_hours_aggregation" not in db.keys():
    print("Initialize eight_hours_aggregation in state store")
    db["eight_hours_aggregation"] = pd.DataFrame(columns=["datetime", "userId", "count"])


def on_dataframe_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    """
    Callback called for each incoming dataframe. In this callback we will store
    the needed data (applying rolling windows accordingly) in the Quix state store
    """

    # Add datetime to the dataframe
    df["datetime"] = pd.to_datetime(df["timestamp"])

    # Append data to last_hour_data and save to database
    last_hour_data = db["last_hour_data"]
    last_hour_data = pd.concat([last_hour_data, df], ignore_index=True)
    db["last_hour_data"] = last_hour_data

    eight_hours_aggregation = db["eight_hours_aggregation"]
    aggregated = df.groupby([pd.Grouper(key='datetime', freq='30min'), 'userId']).size().reset_index(name='count')

    # Add df_copy to eight_hours_aggregation. If the datetime is the same, add both counts
    eight_hours_aggregation = (pd.concat([eight_hours_aggregation, aggregated])
                               .groupby(['datetime', 'userId']).sum().reset_index())
    db["eight_hours_aggregation"] = eight_hours_aggregation

    print("Dataframe handler received", len(df), "rows")
    print("Data in eight_hours_aggregation:", len(eight_hours_aggregation))
    print("Data in last_hour_data:", len(last_hour_data))


def calculate_device_popularity(df: pd.DataFrame):
    last_10_minutes = df[df["datetime"] > (pd.to_datetime(pd.Timestamp.now()) - pd.Timedelta(minutes=10))]
    last_10_minutes = last_10_minutes.groupby(['deviceType']).size().reset_index(name='count')

    total = last_10_minutes['count'].sum()

    if total == 0:
        empty_frame = pd.DataFrame([], columns=["Device", "Device type", "Percentage"])
        r.set("device_type_popularity", empty_frame.to_json())
        return

    mobile = last_10_minutes[last_10_minutes['deviceType'] == 'Mobile']['count'].sum() / total * 100
    tablet = last_10_minutes[last_10_minutes['deviceType'] == 'Tablet']['count'].sum() / total * 100
    desktop = last_10_minutes[last_10_minutes['deviceType'] == 'Desktop']['count'].sum() / total * 100
    other = 100.0 - mobile - tablet - desktop

    data = [["Device type", "Desktop", desktop],
            ["Device type", "Tablet", tablet],
            ["Device type", "Mobile", mobile],
            ["Device type", "Other", other]]

    device_type_popularity = pd.DataFrame(data, columns=["Device", "Device type", "Percentage"])
    r.set("device_type_popularity", device_type_popularity.to_json())


def calculate_category_popularity(df: pd.DataFrame):
    category_popularity = df.groupby(['category']).size().reset_index(name='count')
    category_popularity = category_popularity.sort_values(by=['count'], ascending=False)
    r.set("category_popularity", category_popularity.to_json())


def calculate_10_last_visitors(df: pd.DataFrame):
    latest_visitors = df.tail(10)[:]
    now = pd.Timestamp.now()
    latest_visitors['Date and Time'] = latest_visitors['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    latest_visitors['Relative Time'] = (now - pd.to_datetime(latest_visitors['datetime'])).dt.to_pytimedelta()
    latest_visitors['Relative Time'] = latest_visitors['Relative Time'].apply(lambda x: humanize.naturaltime(x))
    latest_visitors = latest_visitors.sort_values(by='datetime', ascending=False)
    latest_visitors = latest_visitors[['Relative Time', 'Date and Time', 'ip', 'country']]
    r.set('latest_visitors', latest_visitors.to_json())


def calculate_products_last_hour(df: pd.DataFrame):
    products_last_hour = df.groupby(['productId', 'category']).size().reset_index(name='count')
    products_last_hour = products_last_hour.sort_values(by=['count'], ascending=False).head(10)
    r.set("products_last_hour", products_last_hour.to_json())


def calculate_visits_last_15min(df: pd.DataFrame):
    last_15_minutes = df[df["datetime"] > (pd.to_datetime(pd.Timestamp.now()) - pd.Timedelta(minutes=15))]
    last_15_minutes = last_15_minutes.groupby(pd.Grouper(key='datetime', freq='1min')).size().reset_index(name='count')
    r.set("last_15_minutes", last_15_minutes.to_json())


def aggregate_eight_hours(df: pd.DataFrame):
    # Store the eight_hours_aggregation in the state store
    eight_hours_aggregation = db["eight_hours_aggregation"]

    # Get the last 8 hours
    eight_hours = df[df["datetime"] >= (pd.to_datetime(pd.Timestamp.now()) - pd.Timedelta(hours=8))]

    if not eight_hours.equals(eight_hours_aggregation):
        db["eight_hours_aggregation"] = eight_hours

    # Store the aggregated_df in Redis
    r.set("sessions", eight_hours.to_json())


def read_stream(consumer_stream: qx.StreamConsumer):
    # React to new data received from input topic.
    consumer_stream.timeseries.on_dataframe_received = on_dataframe_handler


def send_data_to_redis():
    while True:
        try:
            # Append data and discard data older than 1 hour
            last_hour_data = db["last_hour_data"]
            one_hour = pd.to_datetime(pd.Timestamp.now()) - pd.Timedelta(hours=1)
            updated_last_hour_data = last_hour_data[last_hour_data["datetime"] > one_hour]

            if not updated_last_hour_data.equals(last_hour_data):
                last_hour_data = updated_last_hour_data
                db["last_hour_data"] = last_hour_data

            # This method uses its own rolling window, so we only have to pass the buffer
            aggregate_eight_hours(db["eight_hours_aggregation"].copy())

            # Get average visits in the last 15 minutes
            calculate_visits_last_15min(last_hour_data.copy())

            # Get top viewed productId in the last hour, keep only productId, category and count
            calculate_products_last_hour(last_hour_data.copy())

            # Get latest 10 visitors details (date and time, ip and country)
            calculate_10_last_visitors(last_hour_data.copy())

            # Get category popularity in the last hour
            calculate_category_popularity(last_hour_data.copy())

            # Get device type popularity in the last 10 minutes
            calculate_device_popularity(last_hour_data.copy())

            # Send all data
            sorted_data = last_hour_data.sort_values(by='datetime', ascending=False)
            r.set("raw_data", sorted_data.head(100).to_json())

            # Sleep for 1 second
            time.sleep(1)
        except Exception as e:
            print("Error in sender thread", e)


if __name__ == "__main__":
    consumer_topic.on_stream_received = read_stream

    print("Listening to streams. Press CTRL-C to exit.")

    t = Thread(target=send_data_to_redis)
    t.start()

    # Hook up to termination signal (for docker image) and CTRL-C
    # And handle graceful exit of the model.
    qx.App.run()
