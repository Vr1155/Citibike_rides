from datetime import datetime, timedelta
import pandas as pd

import src.config as config
from src.inference import (
    get_feature_store,
    get_model_predictions,
    load_model_from_registry,
)
from src.data_utils import transform_ts_data_into_lag_features  # replace this if your lag builder is elsewhere

# Current timestamp in UTC
current_date = pd.Timestamp.now(tz="Etc/UTC")
feature_store = get_feature_store()

# Define fetch window: last 28 days
fetch_data_to = current_date - timedelta(hours=1)
fetch_data_from = current_date - timedelta(days=28)
print(f"Fetching features from {fetch_data_from} to {fetch_data_to}")

# Load from CitiBike hourly feature view
feature_view = feature_store.get_feature_view(
    name=config.FEATURE_VIEW_NAME,
    version=config.FEATURE_VIEW_VERSION
)

ts_data = feature_view.get_batch_data(
    start_time=fetch_data_from - timedelta(days=1),
    end_time=fetch_data_to + timedelta(days=1),
)

# Keep only rows within target window
ts_data = ts_data[ts_data.start_hour.between(fetch_data_from, fetch_data_to)]
ts_data = ts_data.sort_values(["start_station_id", "start_hour"]).reset_index(drop=True)
ts_data["start_hour"] = ts_data["start_hour"].dt.tz_localize(None)

# Transform into lag features
features = transform_ts_data_into_lag_features(
    ts_data,
    window_size=24 * 28,
    step_size=23
)

# Run model inference
model = load_model_from_registry()
predictions = get_model_predictions(model, features)
predictions["prediction_hour"] = current_date.ceil("h")

# Push predictions into Hopsworks feature group
pred_fg = feature_store.get_or_create_feature_group(
    name=config.FEATURE_GROUP_MODEL_PREDICTION,
    version=1,
    description="CitiBike hourly demand predictions",
    primary_key=["start_station_id", "prediction_hour"],
    event_time="prediction_hour",
)

pred_fg.insert(predictions, write_options={"wait_for_job": False})
