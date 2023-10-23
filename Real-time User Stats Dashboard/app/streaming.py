import pandas as pd
import quixstreams as qx
from datetime import datetime

from .store import StreamStateStore

__all__ = ("start_quixstreams",)

valid_columns = ["original_timestamp", "timestamp", "userId", "ip", "userAgent", "productId", "category", "title", "gender", "birthDate", "age", "country"]

qx.Logging.update_factory(qx.LogLevel.Debug)


def get_age_group(age):
    if age < 10:
        return "0-9"
    elif age < 20:
        return "10-19"
    elif age < 30:
        return "20-29"
    elif age < 40:
        return "30-39"
    elif age < 50:
        return "40-49"
    elif age < 60:
        return "50-59"
    elif age < 70:
        return "60-69"
    else:
        return "70+"


def start_quixstreams(topic_name: str, state_store: StreamStateStore):
    """
    Start streaming data from Quix
    :param topic_name: Input topic name
    :param state_store: Instance of store.StreamStateStore to keep the dataframe rows
    """
    client = qx.QuixStreamingClient()

    consumer_topic = client.get_topic_consumer(
        topic_name, None, auto_offset_reset=qx.AutoOffsetReset.Latest
    )

    def read_stream(stream_consumer: qx.StreamConsumer):
        """
        Callback to react to new data received from input topic.
        Called for each incoming stream.
        """

        def on_read_pandas_data(_: qx.StreamConsumer, df_i: pd.DataFrame):
            """
            Callback called for each incoming data frame
            """
            df_i["hour"] = pd.to_datetime(df_i["timestamp"]).dt.floor("H")

            if "age" in df_i.columns:
                df_i["ageGroup"] = df_i["age"].apply(get_age_group)
            else:
                df_i["ageGroup"] = "Unknown"

            if "gender" in df_i.columns:
                df_i["gender"] = df_i["gender"].apply(lambda x: x[0] if isinstance(x, str) else "U")
            else:
                df_i["gender"] = "U"

            #df_i = df_i[[col for col in valid_columns if col in df_i.columns]]

            # Add new data to the store
            state_store.append(df_i)

        stream_consumer.timeseries.on_dataframe_received = on_read_pandas_data

    consumer_topic.on_stream_received = read_stream
    qx.App.run()
