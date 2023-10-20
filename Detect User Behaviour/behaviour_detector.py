import os
import time
import pandas as pd
from collections import deque
from datetime import timedelta, datetime

import requests

if 'window_minutes' not in os.environ:
    window_minutes = 30
else:
    window_minutes = int(os.environ['window_minutes'])


def applies_for_offer1(row):
    """Check if the visitor applies for offer 1."""
    if not "category" in row \
            or not "age" in row \
            or not "gender" in row:
        return False

    if row["category"] in ["home&garden", "automotive"] \
            and 35 <= row["age"] <= 60 \
            and row["gender"] == "M":
        return True

    return False


def applies_for_offer2(row):
    """Check if the visitor applies for offer 2."""
    if not "category" in row \
            or not "age" in row \
            or not "gender" in row:
        return False

    if row["category"] in ["clothing", "shoes", "handbags"] \
            and 25 <= row["age"] <= 35 \
            and row["gender"] == "F":
        return True

    return False


class BehaviourDetector:
    columns = ["time", "timestamp", "userId", "category", "age", "ip", "gender", "productId"]

    def __init__(self):
        self._df = pd.DataFrame(columns=self.columns)
        self._special_offers_recipients = pd.DataFrame()

    # Method to process the incoming dataframe
    def process_dataframe(self, received_df: pd.DataFrame):
        # Filter out data that cannot apply for offers
        received_df = received_df[received_df.apply(self._check_offers, axis=1)]

        # Exit if there is no data to process
        if len(received_df) == 0:
            return

        # Merge incoming data with existing data
        self._merge_dataframe(received_df)

        # Remove old data and page refreshes
        self._remove_old_data(minutes=window_minutes)
        self._remove_page_refreshes()

        # Here we group data by visitor and category, add a new column with the aggregated categories,
        # and count the number of rows
        aggregated_data = (self._df.groupby(['userId', 'ip'])['category']
                           .agg([('aggregated_product_category', ', '.join), ('count', 'count')]).reset_index())

        # And we keep only the visitors who opened 3 or more products in the same category
        visitors_to_send_offers = aggregated_data[aggregated_data['count'] > 2]
        self._special_offers_recipients = pd.concat([self._special_offers_recipients, visitors_to_send_offers],
                                                    ignore_index=True)

        # Remove visitors from the dataframe, so we don't launch the offer to the same visitor until they visit
        # 3 or more products in the selected categories again
        self._remove_visitors(visitors_to_send_offers)

    def get_special_offers_recipients(self):
        """Return the recipients of the special offers."""
        return self._special_offers_recipients

    def clear_special_offers_recipients(self):
        """Clear the recipients of the special offers."""
        self._special_offers_recipients = pd.DataFrame()

    def _merge_dataframe(self, new_df: pd.DataFrame):
        """Merge the new DataFrame with the existing DataFrame."""
        # Convert timestamp to datetime, so we can filter by time
        new_df['time'] = pd.to_datetime(new_df['timestamp'], unit='ns')

        # Pick only the columns we need
        new_df = new_df[[col for col in self.columns if col in new_df.columns]]

        # Concatenate the two DataFrames
        self._df = pd.concat([self._df, new_df], ignore_index=True)

    def _remove_old_data(self, minutes: int):
        """Remove data older than X minutes."""
        # If we want to keep last x minutes
        minutes_ago = datetime.utcnow() - timedelta(minutes=minutes)

        # If we want to keep data for x minutes (since last received)
        # minutes_ago = self.df['time'].max() - timedelta(minutes=minutes)

        self._df = self._df[self._df['time'] > minutes_ago]

    def _check_offers(self, row):
        """Check if the visitor applies for offer 1 or 2."""
        return applies_for_offer1(row) or applies_for_offer2(row)

    def _remove_visitors(self, visitors: pd.DataFrame):
        """Remove visitors from the dataframe, so we don't launch same offer to the same visitor."""
        self._df = self._df[~self._df['userId'].isin(visitors['userId'])]

    def _remove_page_refreshes(self):
        """Remove consecutive duplicates of "Product Page URL" for same visitor."""

        # First, we sort the dataframe by userId and time, so we can detect if the visitor refreshed the page
        df_sorted = self._df.sort_values(by=["userId", "time"])

        # Then, remove if the userId and Product Page URL are the same as the previous row
        duplicate_condition = ((df_sorted["userId"] == df_sorted["userId"].shift(1)) &
                               (df_sorted["productId"] == df_sorted["productId"].shift(1)))
        self._df = df_sorted[~duplicate_condition]
