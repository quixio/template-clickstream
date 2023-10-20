import quixstreams as qx
from datetime import datetime
import pandas as pd
import os
import redis

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient()

print("Opening input and output topics")
consumer_topic = client.get_topic_consumer(os.environ["input"], "default-consumer-group")
producer_topic = client.get_topic_producer(os.environ["output"])

redis_client = redis.Redis(
    host=os.environ['redis_host'],
    port=os.environ['redis_port'],
    password=os.environ['redis_password'],
    decode_responses=True)


# Method to calculate the age of a visitor
def calculate_age(birthdate: str):
    if birthdate is None:
        return None

    # Convert the birthdate string to a datetime object
    birthdate = datetime.strptime(birthdate, '%Y-%m-%d')

    # Get the current date
    current_date = datetime.now()

    # Calculate the age
    age = current_date.year - birthdate.year

    # Check if the birthday for this year has already occurred
    if (current_date.month, current_date.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


# Method to get the product category for a product from Redis
def get_product_category(product: str):
    return redis_client.hget(f'product:{product}', 'cat') or "Unknown"

# Method to get the product title for a product from Redis
def get_product_title(product: str):
    return redis_client.hget(f'product:{product}', 'title') or "Unknown"


# Method to get the visitor gender from Redis
def get_visitor_gender(visitor: str):
    return redis_client.hget(f'visitor:{visitor}', 'gender') or "U"


# Method to get the visitor birthdate from Redis
def get_visitor_birthdate(visitor: str):
    return redis_client.hget(f'visitor:{visitor}', 'birthday')


# Method to get the visitor age
def get_visitor_age(visitor: str):
    birthday = redis_client.hget(f'visitor:{visitor}', 'birthday')
    return calculate_age(birthday)



# Callback triggered for each new timeseries data. This method will enrich the data
def on_dataframe_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    # Enrich data
    df['category'] = df['productId'].apply(get_product_category)
    df['title'] = df['productId'].apply(get_product_title)
    df['gender'] = df['userId'].apply(get_visitor_gender)
    df['birthdate'] = df['userId'].apply(get_visitor_birthdate)
    df['age'] = df['birthdate'].apply(calculate_age)

    # Create a new stream (or reuse it if it was already created).
    # We will be using one stream per visitor id, so we can parallelise the processing
    # because the partitioning key will be the stream id
    producer_stream = producer_topic.get_or_create_stream(stream_consumer.stream_id)
    producer_stream.properties.parents.append(stream_consumer.stream_id)
    producer_stream.timeseries.buffer.publish(df)


# Callback called for each incoming stream
def read_stream(consumer_stream: qx.StreamConsumer):
    # React to new data received from input topic.
    consumer_stream.timeseries.on_dataframe_received = on_dataframe_handler


# Hook up events before initiating read to avoid losing out on any data
consumer_topic.on_stream_received = read_stream

print("Listening to streams. Press CTRL-C to exit.")

# Hook up to termination signal (for docker image) and CTRL-C
# And handle graceful exit of the model.
qx.App.run()
