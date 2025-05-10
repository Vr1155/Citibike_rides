def transform_ts_data_info_features_and_target_bike(
    df, feature_col="rides", window_size=12, step_size=1
):
    """
    CitiBike version of transform_ts_data_info_features_and_target().
    Uses 'start_hour' and 'start_station_id' instead of taxi columns.
    """
    location_ids = df["start_station_id"].unique()
    transformed_data = []

    for location_id in location_ids:
        try:
            location_data = df[df["start_station_id"] == location_id].reset_index(drop=True)
            values = location_data[feature_col].values
            times = location_data["start_hour"].values

            if len(values) <= window_size:
                raise ValueError("Not enough data to create even one window.")

            rows = []
            for i in range(0, len(values) - window_size, step_size):
                features = values[i : i + window_size]
                target = values[i + window_size]
                target_time = times[i + window_size]
                row = np.append(features, [target, location_id, target_time])
                rows.append(row)

            feature_columns = [f"{feature_col}_t-{window_size - i}" for i in range(window_size)]
            all_columns = feature_columns + ["target", "start_station_id", "start_hour"]
            transformed_df = pd.DataFrame(rows, columns=all_columns)

            transformed_data.append(transformed_df)

        except ValueError as e:
            print(f"Skipping start_station_id {location_id}: {str(e)}")

    if not transformed_data:
        raise ValueError("No data could be transformed.")

    final_df = pd.concat(transformed_data, ignore_index=True)
    features = final_df[feature_columns + ["start_hour", "start_station_id"]]
    targets = final_df["target"]
    return features, targets


def transform_ts_data_info_features_bike(
    df, feature_col="rides", window_size=12, step_size=1
):
    location_ids = df["start_station_id"].unique()
    transformed_data = []

    for location_id in location_ids:
        try:
            location_data = df[df["start_station_id"] == location_id].reset_index(drop=True)
            values = location_data[feature_col].values
            times = location_data["start_hour"].values

            if len(values) <= window_size:
                raise ValueError("Not enough data to create even one window.")

            rows = []
            for i in range(0, len(values) - window_size, step_size):
                features = values[i : i + window_size]
                target_time = times[i + window_size]
                row = np.append(features, [location_id, target_time])
                rows.append(row)

            feature_columns = [f"{feature_col}_t-{window_size - i}" for i in range(window_size)]
            all_columns = feature_columns + ["start_station_id", "start_hour"]
            transformed_df = pd.DataFrame(rows, columns=all_columns)
            transformed_data.append(transformed_df)

        except ValueError as e:
            print(f"Skipping start_station_id {location_id}: {str(e)}")

    if not transformed_data:
        raise ValueError("No data could be transformed.")

    return pd.concat(transformed_data, ignore_index=True)
