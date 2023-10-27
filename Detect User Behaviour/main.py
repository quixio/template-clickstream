import quixstreams as qx
import os
import pandas as pd
from behaviour_detector import BehaviourDetector

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient()

print("Opening input and output topics")
consumer_topic = client.get_topic_consumer(os.environ["input"])
producer_topic = client.get_topic_producer(os.environ["output"])

behaviour_detector = BehaviourDetector()
frames_received = 0


# Send special offers for each visitor in its own stream
def send_special_offers(special_offers: list):
    for visitor_id, offer in special_offers:
        print("Sending offer to visitor", visitor_id)

        # Use the visitor ID as the stream name
        stream = producer_topic.get_or_create_stream(visitor_id)

        # Send the offer to the stream
        stream.events.publish(qx.EventData("offer", pd.Timestamp.utcnow(), offer))


# Callback called for each incoming dataframe
def on_dataframe_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    global frames_received
    frames_received += 1
    if frames_received % 100 == 0:
        print(f"Received {frames_received} frames")

    # Original dataframe may contain more than one row
    behaviour_detector.process_dataframe(stream_consumer, df)

    # And the special offers recipients may contain 0 or more rows
    special_offers = behaviour_detector.get_special_offers_recipients()

    if len(special_offers) > 0:
        send_special_offers(special_offers)
        behaviour_detector.clear_special_offers_recipients()


# Callback called for each incoming stream
def read_stream(consumer_stream: qx.StreamConsumer):
    # React to new data received from input topic.
    consumer_stream.timeseries.on_dataframe_received = on_dataframe_handler


if __name__ == "__main__":
    # Hook up events before initiating read to avoid losing out on any data
    consumer_topic.on_stream_received = read_stream

    print("Listening to streams. Press CTRL-C to exit.")

    # Hook up to termination signal (for docker image) and CTRL-C
    # And handle graceful exit of the model.
    qx.App.run()
