from quixstreams import Application
from quixstreams.context import message_context
from datetime import timedelta, datetime
import os

# import the dotenv module to load environment variables from a file
from dotenv import load_dotenv
load_dotenv()


def main():
    app = Application(consumer_group="site-visitor-details", use_changelog_topics=False)

    # Define the topic using the "output" environment variable
    input_topic_name = os.getenv("input", "")
    if input_topic_name == "":
        raise ValueError("The 'input' environment variable is required.")

    input_topic = app.topic(input_topic_name)

    output_topic_name = os.getenv("output", "")
    if output_topic_name == "":
        raise ValueError("The 'output' environment variable is required.")

    output_topic = app.topic(output_topic_name)

    # Create a StreamingDataFrame to process inbound data
    sdf = app.dataframe(input_topic)

    # this function will be called for all but the first message
    # it increments the stateful count of the product
     # this funciton will be called for every row received
    # it adds the product from the row to state
    def reducer(aggregated: dict, row: dict):
        # Check if 'userId' is in any of the dictionaries in the array
        if not any(d['userId'] == row['userId'] for d in aggregated):
            # If the userId is not found, add the new dictionary to the array
            aggregated.append({
                "userId": row["userId"],
                "ip": row["ip"],
                "country": row["country"],
                "timestamp": message_context().timestamp.milliseconds * 1000 * 1000,
            })
        
        return aggregated


    # this function will be called for only the first message
    # it initializes the state object with the productId count (starting with 1)
    def initializer(row: dict):
        return [{
                "userId": row["userId"],
                "ip": row["ip"],
                "country": row["country"],
                "timestamp": message_context().timestamp.milliseconds * 1000 * 1000,
            }]
        
    # create a hopping window
    # pass each row to the reducer/init functions
    sdf = sdf.hopping_window(timedelta(seconds=60), timedelta(seconds=30)).reduce(reducer, initializer).current()

    def last_10_in_window(rows: dict):
        # Sort the dictionary by time and take the most recent 10
        return sorted(rows, key=lambda x: x['timestamp'], reverse=True)[:10]
        
    # now we overwrite the 'value' column with:
    # the top 10 most recent users
    sdf["value"] = sdf["value"].apply(last_10_in_window)

    sdf = sdf.apply(lambda row: row['value'][0])

    # print data after any stage of the pipeline to see what you're working with
    sdf = sdf.update(lambda row: print(row))

    # publish the data to a topic
    sdf = sdf.to_topic(output_topic)    

    # run the pipeline defined above
    app.run(sdf)

if __name__ == "__main__":
    main()