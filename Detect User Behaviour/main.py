import quixstreams as qx
import os
import pandas as pd
from behaviour_detector import BehaviourDetector

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1qVTBRVE01TmtJNVJqSTNOVEpFUlVSRFF6WXdRVFF4TjBSRk56SkNNekpFUWpBNFFqazBSUSJ9.eyJodHRwczovL3F1aXguYWkvb3JnX2lkIjoiZGVtbyIsImh0dHBzOi8vcXVpeC5haS9vd25lcl9pZCI6ImF1dGgwfDExYjRjZmQyLWZiMjctNGIwNS05Y2MzLWRhNmE5YTZlNzRjNyIsImh0dHBzOi8vcXVpeC5haS90b2tlbl9pZCI6IjY5ZmQ4ZjYzLWQ2ZmMtNGMxNS04ZWVhLTI2MmZjM2VmNjMxMiIsImh0dHBzOi8vcXVpeC5haS9leHAiOiIxNjk4NzA2ODAwIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLnF1aXguYWkvIiwic3ViIjoiTzBvbmpMaUJtMWZsY3Z5bTZvazBHYmFibFNrb0ZaVGlAY2xpZW50cyIsImF1ZCI6InF1aXgiLCJpYXQiOjE2OTc2MTUwNzAsImV4cCI6MTcwMDIwNzA3MCwiYXpwIjoiTzBvbmpMaUJtMWZsY3Z5bTZvazBHYmFibFNrb0ZaVGkiLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJwZXJtaXNzaW9ucyI6W119.XRKP1zSmhqFLxDUpbB78aoV-zAT4T-jPE-oBd53aMDcZLRMylR97h7KP4MCFjAXpRWG6MGxLBM1zIk1GZNrKlsDSFwxG9gOa0owGm9-iR3QY_MYZkmiY1H-OxaaZNHw81GlN4xDLpBdnB2-m6_4pArG2qEeEkXsbkRXl9hVn_q57objMz0hipxq3azcbXN2k43dx9dm1vURKi4ITK1IhgPAq0RmS7CGzPGxAjlWVdZYeR2hHPzqArR8AzGFBBdtvPXsIRh7B78fqEXYW5-qR-2lSvgWe-DKlU-yEkKoUXRnQ9sJX5lat9yQqLR8UQDMjquqRjdT6tDRNY7C_0_pwDg"
client = qx.QuixStreamingClient(token=TOKEN)

print("Opening input and output topics")
consumer_topic = client.get_topic_consumer(os.environ["input"], "local")
producer_topic = client.get_topic_producer(os.environ["output"])
behaviour_detector = BehaviourDetector()

frames_received = 0


# Send special offers for each visitor in its own stream
def send_special_offers(special_offers: pd.DataFrame):
    print("All offers", special_offers)

    for index, row in special_offers.iterrows():
        visitor_id = row['Visitor Unique ID'].strip('{}')
        print("Sending offer to visitor", visitor_id)

        # Use the visitor ID as the stream name
        stream = producer_topic.get_or_create_stream(visitor_id)

        # Send the offer to the stream
        frame = pd.DataFrame([row])
        stream.timeseries.buffer.publish(frame)


def on_dataframe_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    global frames_received
    frames_received += 1
    if frames_received % 100 == 0:
        print(f"Received {frames_received} frames")

    behaviour_detector.process_dataframe(df)

    special_offers = behaviour_detector.get_special_offers_recipients()

    if not special_offers.empty:
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
