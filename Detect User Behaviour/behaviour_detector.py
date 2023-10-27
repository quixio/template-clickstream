import quixstreams as qx
import os
import pandas as pd
from datetime import timedelta, datetime

if 'window_minutes' not in os.environ:
    window_minutes = 30
else:
    window_minutes = int(os.environ['window_minutes'])


class BehaviourDetector:
    columns = ["time", "timestamp", "userId", "category", "age", "ip", "gender", "productId", "offer"]
    visitor_columns = ["userId", "offer", "category", "productId"]

    transitions = {
        "init": [
            {
                "condition": lambda row, current_state: row["category"] == "clothing",
                "next_state": "clothes_visited",
            }
        ],
        "clothes_visited": [
            {
                "condition": lambda row, current_state: row["category"] == "shoes",
                "next_state": "shoes_visited"
            },
            {
                "condition": lambda row, current_state: row["category"] == "clothing",
                "next_state": "clothes_visited"
            }
        ],
        "shoes_visited": [
            {
                "condition": lambda row, current_state: row["category"] == "clothing"
                                                        and row["productId"] != current_state["rows"][0]["productId"],
                "next_state": "offer"
            },
            {
                "condition": lambda row, current_state: row["category"] == "clothing"
                                                        and row["productId"] == current_state["rows"][0]["productId"],
                "next_state": "clothes_visited"
            }
        ]
    }

    def __init__(self):
        self._df = pd.DataFrame(columns=self.columns)
        self._special_offers_recipients = []

    # Method to process the incoming dataframe
    def process_dataframe(self, stream_consumer: qx.StreamConsumer, received_df: pd.DataFrame):
        # Filter out data that cannot apply for offers
        for label, row in received_df.iterrows():
            user_id = row["userId"]
            user_state = stream_consumer.get_dict_state(user_id)
            user_state["offer"] = "offer1" if row["gender"] == 'M' else "offer2"

            # Initialize state if not present
            if not "state" in user_state:
                user_state["state"] = "init"

            if not "rows" in user_state:
                user_state["rows"] = []

            # Ignore page refreshes
            if user_state["rows"] and user_state["rows"][-1]["productId"] == row["productId"]:
                continue

            # Transition to next state if condition is met
            transitioned = False
            for transition in self.transitions[user_state["state"]]:
                if transition["condition"](row, user_state):
                    user_state["state"] = transition["next_state"]
                    user_state["rows"].append(row)
                    transitioned = True
                    break

            # Reset to initial state if no transition was made
            if not transitioned:
                user_state["state"] = "init"
                user_state["time"] = []
                continue

            # Trigger offer
            if user_state["state"] == "offer":
                print("Triggered offer", user_state["offer"], "for", user_id)
                user_state["state"] = "init"
                user_state["time"] = []
                user_state["rows"] = []
                self._special_offers_recipients.append((user_id, user_state["offer"]))

    def get_special_offers_recipients(self) -> list:
        """Return the recipients of the special offers."""
        return self._special_offers_recipients

    def clear_special_offers_recipients(self):
        """Clear the recipients of the special offers."""
        self._special_offers_recipients = []
