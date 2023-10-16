import quixstreams as qx
from quix_function import QuixFunction
import os
import redis


# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient()

print("Opening input and output topics")
consumer_topic = client.get_topic_consumer(os.environ["input"], "default-consumer-group")
producer_topic = client.get_topic_producer(os.environ["output"])

r = redis.Redis(
    host=os.environ['redis_host'],
    port=os.environ['redis_port'],
    password=os.environ['redis_password'],
    decode_responses=True)


# Callback called for each incoming stream
def read_stream(consumer_stream: qx.StreamConsumer):
    # Handle the data in a function to simplify the example.
    # Note that we will be creating one function per visitor for this example.
    quix_function = QuixFunction(consumer_stream, producer_topic, r)

    # React to new data received from input topic.
    consumer_stream.timeseries.on_dataframe_received = quix_function.on_dataframe_handler


# Hook up events before initiating read to avoid losing out on any data
consumer_topic.on_stream_received = read_stream

print("Listening to streams. Press CTRL-C to exit.")

# Hook up to termination signal (for docker image) and CTRL-C
# And handle graceful exit of the model.
qx.App.run()
