import os
from quixstreams import Application

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application.Quix("transformation-v1", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

sdf = sdf.update(lambda row: print(row))

sdf = sdf.to_topic(output_topic, key=lambda key: key['all-data'])

if __name__ == "__main__":
    app.run(sdf)