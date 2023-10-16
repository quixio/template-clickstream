import quixstreams as qx
import pandas as pd
from datetime import timedelta, datetime


class BehaviourDetector:
    columns = ["time", "Visitor Unique ID", "Product Category", "Visitor Age", "Visitor Gender", "Purchase ID",
               "Product Page URL"]

    def __init__(self, topic_producer: qx.TopicProducer):
        self.topic_producer = topic_producer
        self.df = pd.DataFrame(columns=self.columns)

    # Callback triggered for each new timeseries data
    def on_dataframe_handler(self, stream_consumer: qx.StreamConsumer, received_df: pd.DataFrame):
        # Merge incoming data with existing data
        self.merge_dataframe(received_df)

        # Remove old data
        self.remove_old_data(minutes=30)

        # Get visitors who opened 3 or more products in the same category
        visitors = self.get_visitors_opened_same_category()

        # Remove visitors from the dataframe, so we don't launch same offer to the same visitor
        self.remove_visitors(visitors)

        for _, row in visitors.items():
            print(f"Sending offer to {row['Visitor Unique ID']} for category {row['Product Category']}")
            stream = self.topic_producer.get_or_create_stream(row['Visitor Unique ID'])
            stream.timeseries.publish(pd.DataFrame(row))

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

    def get_visitors_opened_same_category(self) -> pd.DataFrame:
        """Get visitors who opened 3 or more products in the same category."""

        visits = self.remove_page_refreshes()

        # Group by visitor and category, and count the number of rows
        visitors = visits.groupby(["Visitor Unique ID", "Product Category"]).size()

        # Keep only the visitors who opened 3 or more products in the same category
        visitors = visitors[visitors > 2]
        return visitors

    def remove_visitors(self, visitors):
        """Remove visitors from the dataframe, so we don't launch same offer to the same visitor."""

        self.df = self.df[~self.df['Visitor Unique ID'].isin(visitors.index.get_level_values(0))]

    def remove_page_refreshes(self) -> pd.DataFrame:
        """Remove consecutive duplicates of "Product Page URL" for same visitor."""

        # First, we sort the dataframe by Visitor Unique ID and time, so we can detect if the visitor refreshed the page
        df_sorted = self.df.sort_values(by=["Visitor Unique ID", "time"])

        # Then, remove if the Visitor Unique ID and Product Page URL are the same as the previous row
        duplicate_condition = ((df_sorted["Visitor Unique ID"] == df_sorted["Visitor Unique ID"].shift(1)) &
                               (df_sorted["Product Page URL"] == df_sorted["Product Page URL"].shift(1)))
        df_filtered = df_sorted[~duplicate_condition]

        return df_filtered
