import quixstreams as qx
import os
import redis
import pandas as pd
from rocksdict import Rdict, Options

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

# Default value for the last hour data, will be initialized from state store
if "last_hour_data" not in db.keys():
    print("Initialize last_hour_data in state store")
    db["last_hour_data"] = pd.DataFrame()
last_hour_data = db["last_hour_data"]

if "eight_hours_aggregation" not in db.keys():
    print("Initialize eight_hours_aggregation in state store")
    db["eight_hours_aggregation"] = pd.DataFrame()
eight_hours_aggregation = db["eight_hours_aggregation"]

last_sent_to_redis = pd.to_datetime(pd.Timestamp.now())
buffer = pd.DataFrame()

def on_dataframe_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    """
    Callback called for each incoming dataframe. In this callback we will store
    the needed data (applying rolling windows accordingly) in the Quix state store
    and sending to Redis for later consumption.
    """
    global last_hour_data
    global last_sent_to_redis
    global buffer

    buffer = pd.concat([buffer, df], ignore_index=True)

    # Send data to redis only every second
    if (pd.to_datetime(pd.Timestamp.now()) - last_sent_to_redis).seconds < 1:
        return

    aggregate_eight_hours(buffer.copy())

    # Append data and discard data older than 1 hour
    temp = pd.concat([last_hour_data, buffer], ignore_index=True)
    temp = temp[temp["datetime"] > (pd.to_datetime(pd.Timestamp.now()) - pd.Timedelta(hours=1))]
    db["last_hour_data"] = temp

    # Get top viewed productId in the last hour, keep only productId, category and count
    products_last_hour = temp.groupby(['productId', 'category']).size().reset_index(name='count')
    products_last_hour = products_last_hour.sort_values(by=['count'], ascending=False).head(10)
    print("Products last hour:")
    print(products_last_hour)
    r.set("products_last_hour", products_last_hour.to_json(orient='records'))

    # Get latest 10 visiturs details (date and time, ip and country)
    latest_visitors = temp.tail(10)[:]
    latest_visitors["Date and Time"] = pd.to_datetime(latest_visitors["datetime"])
    latest_visitors = latest_visitors[['Date and Time', 'ip', 'country']]
    print("Latest visitors:")
    print(latest_visitors)
    r.set("latest_visitors", latest_visitors.to_json(orient='records'))

    # Get category popularity in the last hour
    category_popularity = temp.groupby(['category']).size().reset_index(name='count')
    category_popularity = category_popularity.sort_values(by=['count'], ascending=False)
    print("Category popularity:")
    print(category_popularity)
    r.set("category_popularity", category_popularity.to_json(orient='records'))

    # Get device type popularity in the last 10 minutes
    last_10_minutes = temp[temp["datetime"] > (pd.to_datetime(pd.Timestamp.now()) - pd.Timedelta(minutes=10))]
    device_type_popularity = last_10_minutes.groupby(['deviceType']).size().reset_index(name='count')
    device_type_popularity = device_type_popularity.sort_values(by=['count'], ascending=False)
    print("Device type popularity:")
    print(device_type_popularity)
    r.set("device_type_popularity", device_type_popularity.to_json(orient='records'))

    # Clear buffer
    last_sent_to_redis = pd.to_datetime(pd.Timestamp.now())
    buffer = pd.DataFrame()


def aggregate_eight_hours(df_copy: pd.DataFrame):
    global eight_hours_aggregation

    # Columns = ['datetime', 'userId', 'category', 'age', 'ip', 'gender', 'productId']
    # Group df_copy by userid and datetime (down to 30 minutes) and get the count

    df_copy = df_copy.groupby([pd.Grouper(key='datetime', freq='30min'), 'userId']).size().reset_index(name='count')

    # Add df_copy to eight_hours_aggregation. If the datetime is the same, add both counts
    eight_hours_aggregation = pd.concat([eight_hours_aggregation, df_copy]).groupby(
        ['datetime', 'userId']).sum().reset_index()

    # Store the eight_hours_aggregation in the state store
    db["eight_hours_aggregation"] = eight_hours_aggregation
    print(eight_hours_aggregation)

    # Get sessions (unique users) in the last 8 hours (segmented by 30 mins)
    aggregated_df = eight_hours_aggregation.groupby(['datetime']).size().reset_index(name='count')
    print(aggregated_df)

    # Store the aggregated_df in Redis
    r.set("sessions", aggregated_df.to_json(orient='records'))


def read_stream(consumer_stream: qx.StreamConsumer):
    # React to new data received from input topic.
    consumer_stream.timeseries.on_dataframe_received = on_dataframe_handler


if __name__ == "__main__":
    consumer_topic.on_stream_received = read_stream

    print("Listening to streams. Press CTRL-C to exit.")

    # Hook up to termination signal (for docker image) and CTRL-C
    # And handle graceful exit of the model.
    qx.App.run()
