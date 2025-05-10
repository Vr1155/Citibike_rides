# src/feature_utils.py

def build_features_for_citibike(start_time, end_time, parquet_path):
    import pandas as pd
    import numpy as np
    import holidays

    # Drop timezone from bounds to avoid tz-aware/naive comparison issues
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)

    # Load and filter data
    df = pd.read_parquet(parquet_path, columns=["started_at", "start_station_id"])
    df["start_time"] = pd.to_datetime(df["started_at"]).dt.floor("H")

    # Filter to December 2023 only
    df = df[df["start_time"].dt.month == 12]
    df = df[(df["start_time"] >= start_time) & (df["start_time"] < end_time)]

    # Group to hourly demand
    hourly_df = (
        df.groupby(["start_station_id", "start_time"])
        .size()
        .reset_index(name="rides")
    )

    # Create complete station × hourly grid
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

    # Add lag and calendar features
    df_full = add_lag_features_and_calendar_flags(df_full)

    return df_full


def add_lag_features_and_calendar_flags(df):
    df = df.sort_values(["start_station_id", "start_hour"])

    # Lag features
    for lag in [1, 24, 168, 672]:
        df[f"lag_{lag}"] = df.groupby("start_station_id")["rides"].shift(lag)

    # Rolling means
    df["rollmean_24"] = df.groupby("start_station_id")["rides"].shift(1).rolling(window=24).mean()
    df["rollmean_168"] = df.groupby("start_station_id")["rides"].shift(1).rolling(window=168).mean()

    # Calendar/time encodings
    df["hour"] = df["start_hour"].dt.hour
    df["dow"] = df["start_hour"].dt.dayofweek
    df["doy"] = df["start_hour"].dt.dayofyear
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["sin_dow"] = np.sin(2 * np.pi * df["dow"] / 7)
    df["cos_dow"] = np.cos(2 * np.pi * df["dow"] / 7)
    df["is_weekend"] = df["dow"] >= 5

    # US holidays (2023)
    us_holidays = holidays.US(years=[2023])
    df["is_holiday"] = df["start_hour"].dt.date.astype("datetime64").isin(us_holidays)

    # Forecast target: rides at t+1
    df["target_t_plus_1"] = df.groupby("start_station_id")["rides"].shift(-1)

    return df
