import quixstreams as qx
import pandas as pd
import redis
from datetime import datetime, date

class QuixFunction:
    def __init__(self, consumer_stream: qx.StreamConsumer, r: redis.Redis):
        self.consumer_stream = consumer_stream
        self.redis_client = r

    # Callback triggered for each new event
    def on_event_data_handler(self, stream_consumer: qx.StreamConsumer, data: qx.EventData):
        print(data.value)

        # Transform your data here.

        self.producer_stream.events.publish(data)

    def calculate_age(self, birthday: str):
        today = date.today()
        birthdate = datetime.strptime(birthday, '%Y-%m-%d')
        # Calculate the difference between the current date and the birthday
        difference = today - birthdate

        # Calculate the person's age in years
        age_in_years = difference.days // 365

        return age_in_years

    # Callback triggered for each new timeseries data
    def on_dataframe_handler(self, stream_consumer: qx.StreamConsumer, df: pd.DataFrame):

        try:
            product = df['Product Page URL']
            cat = self.redis_client.hget(f'product:{product}', 'cat')
            if cat is not None:
                df['Product Category'] = cat
        except Exception as e:
            print("Exception calculating product category", e)
            pass

        try:
            visitor = df['Visitor Unique ID'].strip('{}')
            gender = self.redis_client.hget(f'visitor:{visitor}', 'gender')
            birthday = self.redis_client.hget(f'visitor:{visitor}', 'birthday')
            
            if gender is not None:
                df['Visitor Gender'] = gender
    
            if birthday is not None:
                df['Visitor Birthday'] = birthday
                df['Visitor Age'] = self.calculate_age(birthday)
        except Exception as e2:
            print("Exception enriching visitor data", e2)

        self.producer_stream.timeseries.buffer.publish(df)
