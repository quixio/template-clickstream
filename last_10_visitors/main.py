from quixstreams import Application
from quixstreams.state import State
import os

# import the dotenv module to load environment variables from a file
from dotenv import load_dotenv
load_dotenv()

import uuid
def main():
    app = Application(consumer_group="site-visitor-details"+str(uuid.uuid4()), auto_offset_reset='earliest', use_changelog_topics=False)

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

    def get_users(message, state: State):
        users = state.get('users', {}) # get the users dict from state, or init to empty dict
        userId = message['userId']
        ip = message['ip']
        country = message['country']

        if userId not in users: # if we havent seen this user
            users[userId] = {'ip': ip, 'country': country}

            # Ensure only the last 10 items are kept
            if len(users) > 10:
                oldest_keys = list(users)[:-10]  # Get all keys except the last 10
                for key in oldest_keys:
                    del users[key]  # Remove the oldest entries
                    
            state.set('users', users) # update state with the latest list
        return users # return this dict, it's what we want to see in the downstream service

    # apply this function to each message received from kafka, enable state.
    sdf = sdf.apply(get_users, True)

    sdf = sdf.update(lambda row: print(f'{row}'))

    # publish the data to a topic
    sdf = sdf.to_topic(output_topic)    

    # run the pipeline defined above
    app.run(sdf)

if __name__ == "__main__":
    main()