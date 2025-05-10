import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import hopsworks
import pandas as pd

from src.config import (
    HOPSWORKS_PROJECT_NAME,
    HOPSWORKS_API_KEY,
    FEATURE_GROUP_NAME,
    FEATURE_GROUP_VERSION,
)

# this is a helper function:
from src.feature_utils import build_features_for_citibike

# ─────────────────────────────────────────────────────────────
# Configure Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Step 1: Time Range Setup
# ─────────────────────────────────────────────────────────────
current_date = pd.to_datetime(datetime.now(timezone.utc)).ceil("h")
fetch_data_to = current_date
fetch_data_from = current_date - timedelta(days=28)

logger.info(f"Running CitiBike Feature Pipeline")
logger.info(f"Current datetime (UTC): {current_date}")
logger.info(f"Fetching ride data from {fetch_data_from} to {fetch_data_to}")

# ─────────────────────────────────────────────────────────────
# Step 2: Login to Hopsworks and download .parquet from dataset
# ─────────────────────────────────────────────────────────────
project = hopsworks.login(project=HOPSWORKS_PROJECT_NAME, api_key_value=HOPSWORKS_API_KEY)
dataset_api = project.get_dataset_api()

local_parquet_path = "data/processed/2023/citibike_2023_all.parquet"
os.makedirs("data/processed/2023", exist_ok=True)

if not os.path.exists(local_parquet_path):
    logger.info("Downloading citibike_2023_all.parquet from Hopsworks Dataset storage...")
    dataset_api.download("Resources/citibike/citibike_2023_all.parquet/citibike_2023_all.parquet", local_path=local_parquet_path)
    logger.info("Download complete.")

# ─────────────────────────────────────────────────────────────
# Step 3: Run Feature Engineering
# ─────────────────────────────────────────────────────────────
logger.info("Building features for CitiBike...")
ts_data = build_features_for_citibike(fetch_data_from, fetch_data_to, parquet_path=local_parquet_path)
logger.info(f"Generated time-series features: {ts_data.shape[0]} rows, {ts_data.shape[1]} columns")

# ─────────────────────────────────────────────────────────────
# Step 4: Connect to Feature Store and Insert Features
# ─────────────────────────────────────────────────────────────
logger.info("Connecting to the Feature Store...")
feature_store = project.get_feature_store()
logger.info(f"Inserting into Feature Group: {FEATURE_GROUP_NAME} (v{FEATURE_GROUP_VERSION})...")
feature_group = feature_store.get_feature_group(
    name=FEATURE_GROUP_NAME,
    version=FEATURE_GROUP_VERSION,
)
feature_group.insert(ts_data, write_options={"wait_for_job": False})
logger.info("Feature data successfully inserted into Hopsworks.")
