import quixstreams as qx
import os
import pandas as pd
import logging
from rlh import RedisStreamLogHandler
import time
import redis
from rocksdict import Rdict


if 'window_minutes' not in os.environ:
    window_minutes = 30
else:
    window_minutes = int(os.environ['window_minutes'])


def check_time_elapsed(row, current_state):
    if len(current_state["rows"]) == 0:
        return True

    timestamp_row = row["timestamp"]
    timestamp_first_interaction = current_state["rows"][0]["timestamp"]
    window_ns = window_minutes * 60 * 1e9

    time_valid = timestamp_row - timestamp_first_interaction < window_ns
    return time_valid


class BehaviourDetector:
    columns = ["time", "timestamp", "userId", "category", "age", "ip", "gender", "productId", "offer"]
    visitor_columns = ["userId", "offer", "category", "productId"]

    transitions = {
        "init": [
            {
                "condition": lambda row, current_state: row["category"] == "clothing"
                                                        and ((row["gender"] == "M" and 35 <= row["age"] <= 45)
                                                             or (row["gender"] == "F" and 25 <= row["age"] <= 35)),
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
                "next_state": "clothes_visited_2"
            }
        ],
        "clothes_visited_2": [
            {
                "condition": lambda row, current_state: row["category"] == "shoes"
                                                        and row["productId"] != current_state["rows"][1]["productId"],
                "next_state": "shoes_visited_2"
            }
        ],
        "shoes_visited_2": [
            {
                "condition": lambda row, current_state: row["category"] == "shoes"
                                                        and row["productId"] != current_state["rows"][0]["productId"]
                                                        and row["productId"] != current_state["rows"][2]["productId"],
                "next_state": "offer"
            }
        ],
    }

    def __init__(self):
        self._special_offers_recipients = []

        self.logger = logging.getLogger("States")
        self.log_stream_name = "state_logs"
        redis_log_handler = RedisStreamLogHandler(stream_name=self.log_stream_name,
                                                  host=os.environ['redis_host'],
                                                  port=int(os.environ['redis_port']),
                                                  password=os.environ['redis_password'],
                                                  username=os.environ.get('redis_username'))
        self.redis_client = redis.Redis(host=os.environ['redis_host'],
                                        port=int(os.environ['redis_port']),
                                        password=os.environ['redis_password'],
                                        username=os.environ.get('redis_username'))
        redis_log_handler.setLevel(logging.INFO)
        self.logger.addHandler(redis_log_handler)

        # make sure the state dir exists
        if not os.path.exists("state"):
            os.makedirs("state")

        # rocksDb is used to hold state, state.dict is in the `state` folder which is maintained for us by Quix
        # so we just init the rocks db using `state.dict` which will be loaded from the file system if it exists
        self._db = Rdict("state/state.dict")

    # Method to process the incoming dataframe
    def process_dataframe(self, stream_consumer: qx.StreamConsumer, received_df: pd.DataFrame):
        for label, row in received_df.iterrows():
            user_id = row["userId"]
            self.logger.debug(f"Processing frame for {user_id}")

            # Filter out data that cannot apply for offers
            if "gender" not in row:
                self.logger.debug(f"User {user_id} does not have gender, ignoring")
                continue

            if "age" not in row:
                self.logger.debug(f"User {user_id} does not have age, ignoring")
                continue

            # Get state
            self.logger.debug(f"Getting state for {user_id}")
            start = time.time()
            if user_id not in self._db.keys():
                self._db[user_id] = {}
            user_state = self._db[user_id]
            self.logger.debug(f"Loaded state for {user_id}. Took {time.time() - start} seconds")

            # Initialize state if not present
            user_state["offer"] = "offer1" if row["gender"] == 'M' else "offer2"

            if "state" not in user_state:
                user_state["state"] = "init"

            if "rows" not in user_state:
                user_state["rows"] = []

            # Ignore page refreshes
            if user_state["rows"] and user_state["rows"][-1]["productId"] == row["productId"]:
                self.logger.debug(f"Ignoring page refresh for {user_id}")
                continue

            # Transition to next state if condition is met
            self.logger.debug(f"Applying transitions for {user_id}. Current state: {user_state['state']}")
            transitioned = False
            for transition in self.transitions[user_state["state"]]:
                if transition["condition"](row, user_state) and check_time_elapsed(row, user_state):
                    user_state["state"] = transition["next_state"]
                    user_state["rows"].append(row)
                    transitioned = True

                    # Only log to info if it is a real user interaction (real user interactions do not have original_timestamp value)
                    log_text = f"[User {user_id} entered state {user_state['state']}][Event: clicked {row['productId']}][Category: {row['category']}]"
                    if "original_timestamp" not in row:
                        self.logger.info(log_text)
                    else:
                        self.logger.debug(log_text)

                    break

            # Reset to initial state if no transition was made
            if not transitioned:
                self.logger.debug(f"Resetting state to init for {user_id}")
                user_state["state"] = "init"
                user_state["rows"] = []

            # Trigger offer
            elif user_state["state"] == "offer":
                # Only log to info if it is a real user interaction (real user interactions do not have original_timestamp value)
                log_text = f"[User {user_id} triggered offer {user_state['offer']}]"
                if "original_timestamp" not in row:
                    self.logger.info(log_text)
                else:
                    self.logger.debug(log_text)

                user_state["state"] = "init"
                user_state["rows"] = []
                self._special_offers_recipients.append((user_id, user_state["offer"]))

            # Save state
            self._db[user_id] = user_state

        # Finally, keep only the last 10 log entries
        self.redis_client.xtrim(self.log_stream_name, maxlen=10, approximate=True)

    def get_special_offers_recipients(self) -> list:
        """Return the recipients of the special offers."""
        return self._special_offers_recipients

    def clear_special_offers_recipients(self):
        """Clear the recipients of the special offers."""
        self._special_offers_recipients = []
