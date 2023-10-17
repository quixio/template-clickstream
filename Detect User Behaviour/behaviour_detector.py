import os
import time
from collections import deque

import quixstreams as qx
import pandas as pd
from datetime import timedelta, datetime

import requests

if 'window_minutes' not in os.environ:
    window_minutes = 30
else:
    window_minutes = int(os.environ['window_minutes'])


class BehaviourDetector:
    columns = ["time", "Visitor Unique ID", "Product Category", "Visitor Age", "IP Address", "Visitor Gender",
               "Purchase ID", "Product Page URL"]

    def __init__(self, topic_producer: qx.TopicProducer):
        self.topic_producer = topic_producer
        self.df = pd.DataFrame(columns=self.columns)
        self.frames_received = 0

        # Initialize a deque to keep track of webhook calls
        self.webhook_calls = deque()

        # Placeholder for webhook URL
        self.webhook_url = 'https://hook.eu2.make.com/b0yr6fsuhu4fmaeoghrtwtmeb0i05ah1'

    def call_webhook(self, ip_address, unique_categories):
        # Get the current time
        current_time = time.time()

        # Remove timestamps older than an hour (3600 seconds)
        webhook_calls = deque([t for t in self.webhook_calls if current_time - t < 3600])

        # Check if we've exceeded the rate limit
        if len(webhook_calls) >= 10:
            print("Rate limit exceeded. Skipping webhook call.")
            return

        # Call the webhook (replace with actual call)
        print("######### CALLING WEBHOOK ######### ")
        print(ip_address, unique_categories)
        result = requests.post(self.webhook_url, json={'ip_address': ip_address, 'unique_urls': unique_categories})
        print("Result:", result.status_code)

        # Add the current timestamp to the deque
        self.webhook_calls.append(current_time)

    # Callback triggered for each new timeseries data
    def on_dataframe_handler(self, stream_consumer: qx.StreamConsumer, received_df: pd.DataFrame):
        self.frames_received += 1
        if self.frames_received % 100 == 0:
            print(f"Received {self.frames_received} frames")

        # Filter out data that cannot apply for offers
        received_df = received_df[received_df.apply(self.check_offers, axis=1)]

        # Exit if there is no data to process
        if len(received_df) == 0:
            return

        # Merge incoming data with existing data
        self.merge_dataframe(received_df)

        # Remove old data and page refreshes
        self.remove_old_data(minutes=window_minutes)
        self.remove_page_refreshes()

        # Here we group data by visitor and category, add a new column with the aggregated categories,
        # and count the number of rows
        aggregated_data = (self.df.groupby(['Visitor Unique ID', 'IP Address'])['Product Category']
                           .agg([('aggregated_product_category', ', '.join), ('count', 'count')]).reset_index())

        # And we keep only the visitors who opened 3 or more products in the same category
        visitors_to_send_offers = aggregated_data[aggregated_data['count'] > 2]

        # Remove visitors from the dataframe, so we don't launch the offer to the same visitor until they visit
        # 3 or more products in the selected categories again
        self.remove_visitors(visitors_to_send_offers)

        # Call the webhook
        for label, row in visitors_to_send_offers.iterrows():
            self.call_webhook(row['IP Address'], row['aggregated_product_category'])

    def merge_dataframe(self, new_df: pd.DataFrame):
        """Merge the new DataFrame with the existing DataFrame."""

        # Convert timestamp to datetime, so we can filter by time
        new_df['time'] = pd.to_datetime(new_df['timestamp'], unit='ns')

        # Pick only the columns we need
        new_df = new_df[[col for col in self.columns if col in new_df.columns]]

        # Concatenate the two DataFrames
        self.df = pd.concat([self.df, new_df], ignore_index=True)

    def remove_old_data(self, minutes: int):
        """Remove data older than X minutes."""

        # If we want to keep last x minutes
        minutes_ago = datetime.utcnow() - timedelta(minutes=minutes)

        # If we want to keep data for x minutes (since last received)
        # minutes_ago = self.df['time'].max() - timedelta(minutes=minutes)

        self.df = self.df[self.df['time'] > minutes_ago]

    def check_offers(self, row):
        """Check if the visitor applies for offer 1 or 2."""
        return self.applies_for_offer1(row) or self.applies_for_offer2(row)

    def applies_for_offer1(self, row):
        if row["Product Category"] in ["home&garden", "automotive"] \
                and 35 <= row["Visitor Age"] <= 60 \
                and row["Visitor Gender"] == "M":
            return True

        return False

    def applies_for_offer2(self, row):
        """Check if the visitor applies for offer 1."""
        if row["Product Category"] in ["clothing", "shoes", "handbags"] \
                and 25 <= row["Visitor Age"] <= 35 \
                and row["Visitor Gender"] == "F":
            return True

        return False

    def get_visitors_opened_same_category(self) -> pd.DataFrame:
        """Get visitors who opened 3 or more products in the same category."""

        # Group by visitor and category, and count the number of rows
        group_fields = ["Visitor Unique ID", "Visitor Age", "IP Address", "Visitor Gender", "Product Category"]
        visitors = visits.groupby(group_fields).size()

        # Keep only the visitors who opened 3 or more products in the same category
        visitors = visitors[visitors > 2]
        return visitors

    def remove_visitors(self, visitors: pd.DataFrame):
        """Remove visitors from the dataframe, so we don't launch same offer to the same visitor."""

        self.df = self.df[~self.df['Visitor Unique ID'].isin(visitors['Visitor Unique ID'])]

    def remove_page_refreshes(self):
        """Remove consecutive duplicates of "Product Page URL" for same visitor."""

        # First, we sort the dataframe by Visitor Unique ID and time, so we can detect if the visitor refreshed the page
        df_sorted = self.df.sort_values(by=["Visitor Unique ID", "time"])

        # Then, remove if the Visitor Unique ID and Product Page URL are the same as the previous row
        duplicate_condition = ((df_sorted["Visitor Unique ID"] == df_sorted["Visitor Unique ID"].shift(1)) &
                               (df_sorted["Product Page URL"] == df_sorted["Product Page URL"].shift(1)))
        self.df = df_sorted[~duplicate_condition]
