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
# Step 2: Run Feature Engineering
# ─────────────────────────────────────────────────────────────
logger.info("Building features for CitiBike...")
ts_data = build_features_for_citibike(fetch_data_from, fetch_data_to)
logger.info(f"Generated time-series features: {ts_data.shape[0]} rows, {ts_data.shape[1]} columns")

# ─────────────────────────────────────────────────────────────
# Step 3: Connect to Hopsworks and Feature Store
# ─────────────────────────────────────────────────────────────
logger.info("Logging into Hopsworks...")
project = hopsworks.login(project=HOPSWORKS_PROJECT_NAME, api_key_value=HOPSWORKS_API_KEY)
feature_store = project.get_feature_store()

logger.info(f"Connected to project '{HOPSWORKS_PROJECT_NAME}'")

# ─────────────────────────────────────────────────────────────
# Step 4: Write to Feature Group
# ─────────────────────────────────────────────────────────────
logger.info(f"Inserting into Feature Group: {FEATURE_GROUP_NAME} (v{FEATURE_GROUP_VERSION})...")
feature_group = feature_store.get_feature_group(
    name=FEATURE_GROUP_NAME,
    version=FEATURE_GROUP_VERSION,
)
feature_group.insert(ts_data, write_options={"wait_for_job": False})
logger.info("Feature data successfully inserted into Hopsworks.")
