import quixstreams as qx
import pandas as pd
import redis
from datetime import datetime


class QuixFunction:
    def __init__(self, consumer_stream: qx.StreamConsumer, topic_producer: qx.TopicProducer, r: redis.Redis):
        self.consumer_stream = consumer_stream
        self.topic_producer = topic_producer
        self.redis_client = r

    # Callback triggered for each new event (like stream created, parameters changed, etc.)
    def on_event_data_handler(self, stream_consumer: qx.StreamConsumer, data: qx.EventData):
        print(data.value)

        # Transform your data here.
        producer_stream = self.topic_producer.get_or_create_stream(stream_consumer.stream_id)
        producer_stream.events.publish(data)

    # Method to calculate the age of a visitor
    def calculate_age(self, birthdate: str):
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
    def get_product_category(self, product: str):
        return self.redis_client.hget(f'product:{product}', 'cat')

    # Method to get the visitor gender from Redis
    def get_visitor_gender(self, visitor: str):
        # Origin visitor format: {visitor_id}
        visitor_without_brackets = visitor.strip('{}')
        return self.redis_client.hget(f'visitor:{visitor_without_brackets}', 'gender')

    # Method to get the visitor birthdate from Redis
    def get_visitor_birthdate(self, visitor: str):
        visitor_without_brackets = visitor.strip('{}')
        return self.redis_client.hget(f'visitor:{visitor_without_brackets}', 'birthday')

    # Method to get the visitor age
    def get_visitor_age(self, visitor: str):
        visitor_without_brackets = visitor.strip('{}')
        birthday = self.redis_client.hget(f'visitor:{visitor_without_brackets}', 'birthday')
        return self.calculate_age(birthday)

    # Callback triggered for each new timeseries data. This method will enrich the data
    def on_dataframe_handler(self, stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
        # Enrich data
        df['Product Category'] = df['Product Page URL'].apply(self.get_product_category)
        df['Visitor Gender'] = df['Visitor Unique ID'].apply(self.get_visitor_gender)
        df['Visitor Birthdate'] = df['Visitor Unique ID'].apply(self.get_visitor_birthdate)
        df['Visitor Age'] = df['Visitor Birthdate'].apply(self.calculate_age)

        # Create a new stream (or reuse it if it was already created).
        # We will be using one stream per visitor id, so we can parallelise the processing
        # because the partitioning key will be the stream id
        producer_stream = self.topic_producer.get_or_create_stream(stream_consumer.stream_id)
        producer_stream.properties.parents.append(stream_consumer.stream_id)
        producer_stream.timeseries.buffer.publish(df)
