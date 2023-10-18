import pandas as pd
import quixstreams as qx

from .store import StreamStateStore

__all__ = ("start_quixstreams",)

valid_columns = ["Date and Time", "Product Category", "Visitor Age Group", "Visitor Gender"]

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
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1qVTBRVE01TmtJNVJqSTNOVEpFUlVSRFF6WXdRVFF4TjBSRk56SkNNekpFUWpBNFFqazBSUSJ9.eyJodHRwczovL3F1aXguYWkvb3JnX2lkIjoiZGVtbyIsImh0dHBzOi8vcXVpeC5haS9vd25lcl9pZCI6ImF1dGgwfDExYjRjZmQyLWZiMjctNGIwNS05Y2MzLWRhNmE5YTZlNzRjNyIsImh0dHBzOi8vcXVpeC5haS90b2tlbl9pZCI6ImZmMjJmZDM3LWU3ZDctNDRmOS1iNGVmLTBlYmIwMDJlM2ZkYSIsImh0dHBzOi8vcXVpeC5haS9leHAiOiIxNjk4NzA2ODAwIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLnF1aXguYWkvIiwic3ViIjoiZE1jMjFGVXhsNDJVcE5JSzNHVm5Ka3BtUHpJeGJCa1lAY2xpZW50cyIsImF1ZCI6InF1aXgiLCJpYXQiOjE2OTc2Mzk2ODIsImV4cCI6MTcwMDIzMTY4MiwiYXpwIjoiZE1jMjFGVXhsNDJVcE5JSzNHVm5Ka3BtUHpJeGJCa1kiLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJwZXJtaXNzaW9ucyI6W119.ZXNJTSMtJbVnAQxoaxal2jr0l4QP9mVA_5LgeNQOrfL8YbDTgz5V_5zt6SBR_D79UNs8EvAXm6XLYn8UKdskt99-MkF9pxYJn3_kf1h7isStjeTIRCgO10aItdBV7XYk2BiKcNpQ1Vh6nTuqHOjt5mTv1tLL0VH_pzdoJhOrMkHFDsSSVt8hi7u8JyDJZ0VLLMq78a_tP5dwgpfwDWQKa0brQOlTZVpVS3YC9HNswUj_0Jb0ad6famROk7NBT3lv4hO2ikDybeEZH5qJteQ-fHhnBNaAUkJiGacZTSDzQXM_LyhP3x5wD3DhNE-EQp27uk3allJXorynGbFIeZqeng"
    client = qx.QuixStreamingClient(token=token)

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
            df_i["Date and Time"] = pd.to_datetime(df_i["Date and Time"])

            if "Visitor Age" in df_i.columns:
                df_i["Visitor Age Group"] = df_i["Visitor Age"].apply(get_age_group)
            else:
                df_i["Visitor Age Group"] = "Unknown"

            if "Visitor Gender" in df_i.columns:
                df_i["Visitor Gender"] = df_i["Visitor Gender"].apply(lambda x: x[0] if isinstance(x, str) else "U")
            else:
                df_i["Visitor Gender"] = "U"

            df_i = df_i[[col for col in valid_columns if col in df_i.columns]]

            # Add new data to the store
            state_store.append(df_i)

        stream_consumer.timeseries.on_dataframe_received = on_read_pandas_data

    consumer_topic.on_stream_received = read_stream
    qx.App.run()
