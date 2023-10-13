import quixstreams as qx
import pandas as pd
import redis

class QuixFunction:
    def __init__(self, consumer_stream: qx.StreamConsumer, producer_stream: qx.StreamProducer, r: redis.Redis):
        self.consumer_stream = consumer_stream
        self.producer_stream = producer_stream
        self.redis_client = r

    # Callback triggered for each new event
    def on_event_data_handler(self, stream_consumer: qx.StreamConsumer, data: qx.EventData):
        print(data.value)

        # Transform your data here.

        self.producer_stream.events.publish(data)

    # Callback triggered for each new timeseries data
    def on_dataframe_handler(self, stream_consumer: qx.StreamConsumer, df: pd.DataFrame):

        try:
            product = df['Product Page URL']
            cat = self.redis_client.hget(f'product:{product}', 'cat')
            df['Product Category'] = cat
        except:
            pass

        try:
            visitor = df['Visitor Unique ID'].strip('{}')
            gender = self.redis_client.hget(f'visitor:{visitor}', 'gender')
            birthday = self.redis_client.hget(f'visitor:{visitor}', 'birthday')
            df['Visitor Gender'] = gender
            df['Visitor Birthday'] = birthday
            df['Visitor Age'] = self.calculate_age(birthday)
        except:
            pass    

        self.producer_stream.timeseries.buffer.publish(output_df)
