import os
import pandas as pd
from datetime import timedelta, datetime

if 'window_minutes' not in os.environ:
    window_minutes = 30
else:
    window_minutes = int(os.environ['window_minutes'])

# Applies for an offer if:
#   - Women: 25-35, within the last 30mins
#       - Open a page (any) in shoes cat
#       - Subsequently, open a page (any) in clothing cat
#       - Subsequently, open another page (different page from #1) in shoes cat
#   - Men 36-45, same as above but show different offer. (edited)

offers = {
    "offer1": {
        "age": [36, 45],
        "gender": "M"
    },
    "offer2": {
        "age": [25, 35],
        "gender": "F"
    }
}

offer_categories = ["clothing", "shoes", "clothing"]


def applies_for_offer(row):
    """Check if the visitor applies for any offer and return the offer code"""
    if "age" not in row \
            or "gender" not in row:
        return None

    for key, value in offers.items():
        if value["age"][0] <= row["age"] <= value["age"][1] \
                and row["gender"] == value["gender"]:
            return key

    return None


class BehaviourDetector:
    columns = ["time", "timestamp", "userId", "category", "age", "ip", "gender", "productId", "offer"]
    visitor_columns = ["userId", "offer", "category", "productId"]

    def __init__(self):
        self._df = pd.DataFrame(columns=self.columns)
        self._special_offers_recipients = pd.DataFrame(columns=self.visitor_columns)

    # Method to process the incoming dataframe
    def process_dataframe(self, received_df: pd.DataFrame):
        # Filter out data that cannot apply for offers
        received_df["offer"] = received_df.apply(applies_for_offer, axis=1)
        received_df = received_df[received_df["offer"].notnull()]

        # Exit if there is no data to process
        if len(received_df) == 0:
            return

        # Merge incoming data with existing data
        self._merge_dataframe(received_df)

        # Remove old data and page refreshes
        self._remove_old_data(minutes=window_minutes)
        self._remove_page_refreshes()

        # If a visitor has more than 3 records (without page refreshes), remove all but the last 3
        # This is to keep detecting possible offers if the 3 first visits do not apply for any offer
        self._df = self._df.groupby('userId').tail(3)

        # Here we group data by visitor and category, add a new column with all categories and
        # product ids
        aggregated_data = (self._df.groupby(['userId', 'offer'])
                           .agg({'category': list,
                                 'productId': list})
                           .reset_index())

        for index, row in aggregated_data.iterrows():
            if len(row['category']) != len(offer_categories):
                continue
            if row['category'] != offer_categories:
                continue
            if row['productId'][0] == row['productId'][2]:
                continue

            valid_offer = pd.DataFrame([[row['userId'], row['offer'], row['category'], row['productId']]],
                                       columns=self.visitor_columns)
            self._special_offers_recipients = pd.concat([self._special_offers_recipients, valid_offer],
                                                        ignore_index=True)

        # Remove records if we already sent an offer
        self._remove_visitors(self._special_offers_recipients)

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
        """Check if the visitor applies for any offer."""
        return applies_for_offer(row) is not None

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
