import quixstreams as qx
from behaviour_detector import BehaviourDetector
import os

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1qVTBRVE01TmtJNVJqSTNOVEpFUlVSRFF6WXdRVFF4TjBSRk56SkNNekpFUWpBNFFqazBSUSJ9.eyJodHRwczovL3F1aXguYWkvb3JnX2lkIjoiZGVtbyIsImh0dHBzOi8vcXVpeC5haS9vd25lcl9pZCI6ImF1dGgwfDExYjRjZmQyLWZiMjctNGIwNS05Y2MzLWRhNmE5YTZlNzRjNyIsImh0dHBzOi8vcXVpeC5haS90b2tlbl9pZCI6IjcyOGM4NGUwLWUxNWQtNGM1YS05MWRjLWQzMWE3N2E2M2Q2MyIsImh0dHBzOi8vcXVpeC5haS9leHAiOiIxNjk4NzA2ODAwIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLnF1aXguYWkvIiwic3ViIjoicWlkc050N3diM1c4d1FFcHVFN0NiR3pmMWNkbUo3WWtAY2xpZW50cyIsImF1ZCI6InF1aXgiLCJpYXQiOjE2OTc0NTY1MzUsImV4cCI6MTcwMDA0ODUzNSwiYXpwIjoicWlkc050N3diM1c4d1FFcHVFN0NiR3pmMWNkbUo3WWsiLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJwZXJtaXNzaW9ucyI6W119.MuwvlpR_SARux8YzI1yTPRX268CmpHmAD9vriOd_IJgly4GY_mTPW8zxGycp5q3nE20BHsBSXcTpxbdrAOLSY-FB83sN7GWIePcNGlfkNksxCkxsecJHR_vHfXxbJNz6VpTAc0IIV3KrBz3HEeou06qVNmW0xDd-AISu9RAKwYqE_KrfcxW-K5MCQPGVxZXMKq7Gx8fjfx12iZf-fH2YhBTjPfPQXsAA-pAvang60C4Xtq3dCLWrs_vFYhDOeDcS11gFaEj7PGPtbTZuXKIWVCVEzin7YzTqwVjUBNDbmxDodMuXmnQT2iJIHxqVjZxFcoHOiD68BeQ5lXoS48hEvA"
client = qx.QuixStreamingClient(token=TOKEN)

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
