import pycountry
from quixstreams import Application
from quixstreams import message_context

from datetime import datetime
import os
import redis
import json
from iptocc import get_country_code
from user_agents import parse

# import the dotenv module to load environment variables from a file f
from dotenv import load_dotenv
load_dotenv()

def on_processing_error(exc: Exception, row, logger) -> bool:
    logger.error('Ignore processing exception exc=%s row=%s', exc, row)
    return True

def on_consumer_error(exc: Exception, message, logger) -> bool:
    """
    Handle the consumer exception and ignore it
    """
    logger.error('Ignore consumer exception exc=%s offset=%s', exc, message.offset())
    return True

# Create an Application.
app = Application(consumer_group="enrichment-consumer-group-11", use_changelog_topics=False, auto_offset_reset="latest", on_processing_error=on_processing_error, on_consumer_error=on_consumer_error)

# Define the topic using the "output" environment variable
input_topic_name = os.getenv("input", "")
output_topic_name = os.getenv("output", "")
if input_topic_name == "":
    raise ValueError("The 'input' environment variable is required.")
if output_topic_name == "":
    raise ValueError("The 'output' environment variable is required.")

input_topic = app.topic(input_topic_name)
output_topic = app.topic(output_topic_name)

# Create a StreamingDataFrame to process inbound data
sdf = app.dataframe(input_topic)

# Create a producer to publish data to the output topic
producer = app.get_producer()

redis_client = redis.Redis(
    host=os.environ['redis_host'],
    port=int(os.environ['redis_port']),
    password=os.environ['redis_password'],
    username=os.environ.get('redis_username'),
    decode_responses=True)


# Method to calculate the age of a visitor
def calculate_age(birthdate: str):
    if birthdate is None:
        return None

    # Convert the birthdate string to a datetime object
    birthdate = datetime.strptime(birthdate, '%Y-%m-%d')

    # Get the current date
    current_date = datetime.now()

    # Calculate the age
    age = current_date.year - birthdate.year

    # Check if the birthday for this year has already occurred
    if (current_date.month, current_date.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


# Method to get the product category for a product from Redis
def get_product_category(product: str):
    return redis_client.hget(f'product:{product}', 'cat') or "Unknown"


# Method to get the product title for a product from Redis
def get_product_title(product: str):
    return redis_client.hget(f'product:{product}', 'title') or "Unknown"


# Method to get the visitor gender from Redis
def get_visitor_gender(visitor: str):
    return redis_client.hget(f'visitor:{visitor}', 'gender') or "U"


# Method to get the visitor birthdate from Redis
def get_visitor_birthdate(visitor: str):
    return redis_client.hget(f'visitor:{visitor}', 'birthday')


# Method to get the visitor age
def get_visitor_age(visitor: str):
    birthday = redis_client.hget(f'visitor:{visitor}', 'birthday')
    return calculate_age(birthday)


def get_country_from_ip(ip: str):
    try:
        country_code = get_country_code(ip)
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name
    except Exception as e:
        print(f"Error looking up country for IP {ip}:", e)

    return "Unknown"


def get_device_type(user_agent: str):
    try:
        ua = parse(user_agent)
        if ua.is_mobile:
            return "Mobile"
        elif ua.is_tablet:
            return "Tablet"
        elif ua.is_pc:
            return "Desktop"
        elif ua.is_bot:
            return "Bot"
        else:
            return "Other"
    except Exception as e:
        print(f"Error parsing user agent {user_agent}: {e}")

    return "Unknown"


def get_first_letter_of_gender(gender):
    return gender[0]


def convert_age_to_int(age):
    return int(age)


# Callback triggered for each new timeseries data. This method will enrich the data
def on_dataframe_handler(message):

    print(message)
    # Enrich data
    message['category'] = get_product_category(message['productId'])
    message['title'] = get_product_title(message['productId'])
    message['birthdate'] = get_visitor_birthdate(message['userId'])
    message['country'] = get_country_from_ip(message['ip'])
    message['deviceType'] = get_device_type(message['userAgent'])

    # For synthetic data (from csv) we don't have age. For data generated form our live web, we have age and gender
    if 'age' not in message:
        message['age'] = calculate_age(message['birthdate'])
    else:
        message['age'] = convert_age_to_int(message['age'])

    if 'gender' not in message:
        message['gender'] = get_visitor_gender(message['userId'])
    else:
        message['gender'] = get_first_letter_of_gender(message['gender'])

    message_key = message_context().key

    # publish the data to the output topic
    producer.produce(key=message_key.decode('utf-8'), 
                    topic=output_topic.name, 
                    value=json.dumps(message).encode('utf-8'))


# configure the dataframe handler to process each message as it arrives
sdf = sdf.update(on_dataframe_handler)

# Send messages to the output topic
sdf = sdf.to_topic(output_topic)


if __name__ == "__main__":
    # Run the Application. Also handles termination signals.
    app.run(sdf)