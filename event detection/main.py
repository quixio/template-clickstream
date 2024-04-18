import os
from quixstreams import Application
from quixstreams.context import message_context
from datetime import timedelta, datetime

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="transformation-v13", auto_offset_reset="earliest", use_changelog_topics=False)

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)
sdf = sdf.update(lambda row: print(f"{row}"))

# filter out messages that lack these columns or have None for them.
sdf = sdf[(sdf.contains("age")) & (sdf["age"].notnull())]
sdf = sdf[(sdf.contains("gender")) & (sdf["gender"].notnull())]
sdf = sdf[(sdf.contains("userId")) & (sdf["userId"].notnull())]
sdf = sdf[(sdf.contains("productId")) & (sdf["productId"].notnull())]
sdf = sdf[(sdf.contains("category")) & (sdf["category"].notnull())]

def reducer(aggregated: dict, row: dict):
    
    if row is None: return aggregated

    gender = row["gender"]
    age = row["age"]
    offer = aggregated["offer"]
    has_visited_clothing = aggregated['has_visited_clothing']
    has_visited_shoes = aggregated['has_visited_shoes']
    timestamp = aggregated['timestamp']

    # Check to see if the offer has timed out. 
    # This is just for testing purposes so users can play with the UI and get offers more easily.
    if aggregated['offer_made_timestamp_ms'] != 0:
        # Get the current UTC time
        current_utc_time = datetime.utcnow()
        # Convert the offer_made_timestamp_ms to a datetime object
        offer_made_time = datetime.utcfromtimestamp(aggregated['offer_made_timestamp_ms'] / 1000000000)
        # Calculate the timedelta
        time_diff = current_utc_time - offer_made_time
        # Check if it has been more than 1 minute
        if time_diff.total_seconds() > 60:
            aggregated['offer'] = ''
            aggregated['offer_made_timestamp_ms'] = 0
            has_visited_shoes = False
            has_visited_clothing = False
            offer = ''

    if row['category'] == 'shoes':
        has_visited_shoes = True

    if row['category'] == 'clothing':
        has_visited_clothing = True

    # if user has visited required categories and has not had an offer in this window:
    if has_visited_clothing and has_visited_shoes and aggregated['offer_made_timestamp_ms'] == 0:

        def offer_made():
            # record the time the offer was made
            aggregated['offer_made_timestamp_ms'] = message_context().timestamp.milliseconds * 1000 * 1000

        # determine which offer should be sent
        if gender == "F" and 25 <= age <= 35:
            offer = "offer2"
            offer_made()
        if gender == "M" and 35 <= age <= 45:
            offer = "offer1"
            offer_made()
   
        return {
            'has_visited_clothing': has_visited_clothing,
            'has_visited_shoes': has_visited_shoes,
            'timestamp': timestamp,
            'offer_made_timestamp_ms': aggregated['offer_made_timestamp_ms'],
            'offer': offer
        }
    else:
        # send with a blank offer since they have received it in the last 60 seconds.
        return {
            'has_visited_clothing': has_visited_clothing,
            'has_visited_shoes': has_visited_shoes,
            'timestamp': timestamp,
            'offer_made_timestamp_ms': aggregated['offer_made_timestamp_ms'],
            'offer': ''
        }

def initializer(row: dict):
    return {
        "has_visited_clothing": False,
        "has_visited_shoes": False,
        "timestamp": message_context().timestamp.milliseconds * 1000 * 1000,
        "offer": '',
        'offer_made_timestamp_ms': 0
    }

sdf = sdf.tumbling_window(timedelta(minutes=5)).reduce(reducer, initializer).current()

sdf = sdf.filter(lambda row: row['value']['offer'] != '')
sdf = sdf.update(lambda row: print(f"{row}"))

sdf = sdf.apply(lambda row: {'Id': 'offer', 'key': str(message_context().key), 'Value': row["value"]['offer'], 'Timestamp': row['value']['timestamp']})
sdf = sdf.update(lambda row: print(f"{row}"))

sdf = sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)
