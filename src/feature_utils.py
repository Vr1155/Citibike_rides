# src/feature_utils.py

def build_features_for_citibike(start_time, end_time):
    import pandas as pd
    from src.data_utils import add_lag_features_and_calendar_flags

    df = pd.read_parquet("data/processed/2023/citibike_2023_all.parquet")
    df["start_time"] = pd.to_datetime(df["started_at"]).dt.floor("H")
    df = df[(df["start_time"] >= start_time) & (df["start_time"] < end_time)]

    hourly_df = (
        df.groupby(["start_station_id", "start_time"])
        .size()
        .reset_index(name="rides")
    )

    full_index = pd.MultiIndex.from_product(
        [hourly_df["start_station_id"].unique(), pd.date_range(start=start_time, end=end_time, freq="H")],
        names=["start_station_id", "start_hour"]
    )
    df_full = (
        hourly_df.set_index(["start_station_id", "start_time"])
        .reindex(full_index, fill_value=0)
        .rename_axis(index=["start_station_id", "start_hour"])
        .reset_index()
    )

    return add_lag_features_and_calendar_flags(df_full)
