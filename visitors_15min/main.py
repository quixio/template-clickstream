from quixstreams import Application
from datetime import timedelta, datetime
import os

# import the dotenv module to load environment variables from a file
from dotenv import load_dotenv
load_dotenv()


import uuid
def main():
    app = Application(consumer_group="visitors-15min"+str(uuid.uuid4()), use_changelog_topics=False, auto_offset_reset='earliest')

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

    def initializer(row: dict):
        return {
            'user_ids': []
        }

    # this funciton will be called for every row received
    def row_processor(state: dict, row: dict):
        
        user_ids = state['user_ids'] # get user_ids array from state
        userId = row['userId']
        if userId not in user_ids: # if the userId has not already been seen in this window
            user_ids.append(userId) # add it to the list of ids seen
            state['user_ids'] = user_ids # update state
        return state

    # create a 15 minute hopping window with a 60 second step
    sdf = sdf.hopping_window(timedelta(minutes=15), timedelta(seconds=60)).reduce(row_processor, initializer).current()
    
    # combine the length of the user_ids list in state and the timestamp representing the start of the window
    sdf = sdf.apply(lambda row: {"timestamp": row['start'], "count": len(row['value']['user_ids'])})
    
    # print data after any stage of the pipeline to see what you're working with
    sdf = sdf.update(lambda row: print(row))

    # output rows:
    # {'timestamp': 1712920080000, 'count': 2}
    # {'timestamp': 1712920140000, 'count': 0}
    # {'timestamp': 1712919300000, 'count': 3}
    # {'timestamp': 1712919360000, 'count': 3}
    # {'timestamp': 1712919420000, 'count': 3}
    # {'timestamp': 1712919480000, 'count': 3}

    # publish the data to a topic
    sdf = sdf.to_topic(output_topic)

    # run the pipeline defined above
    app.run(sdf)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)