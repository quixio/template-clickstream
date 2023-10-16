import quixstreams as qx
from behaviour_detector import BehaviourDetector
import os

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient()

print("Opening input and output topics")
consumer_topic = client.get_topic_consumer(os.environ["input"], "default-consumer-group")
producer_topic = client.get_topic_producer(os.environ["output"])
behaviour_detector = BehaviourDetector(producer_topic)


# Callback called for each incoming stream
def read_stream(consumer_stream: qx.StreamConsumer):
    # React to new data received from input topic.
    consumer_stream.timeseries.on_dataframe_received = behaviour_detector.on_dataframe_handler


# Hook up events before initiating read to avoid losing out on any data
consumer_topic.on_stream_received = read_stream

print("Listening to streams. Press CTRL-C to exit.")

# Hook up to termination signal (for docker image) and CTRL-C
# And handle graceful exit of the model.
qx.App.run()
