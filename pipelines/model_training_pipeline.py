import joblib
from hsml.model_schema import ModelSchema
from hsml.schema import Schema
from sklearn.metrics import mean_absolute_error

import src.config as config
from src.data_utils import transform_ts_data_info_features_and_target
from src.inference import (
    fetch_days_data,
    get_hopsworks_project,
    load_metrics_from_registry,
)
from src.pipeline_utils import get_pipeline

# ─────────────────────────────────────────────────────────────
# Step 1: Load data from feature store
# ─────────────────────────────────────────────────────────────
print("📥 Fetching CitiBike time-series data from Hopsworks...")
ts_data = fetch_days_data(180)

# ─────────────────────────────────────────────────────────────
# Step 2: Transform to lag-based supervised learning data
# ─────────────────────────────────────────────────────────────
print("🧪 Transforming time-series data into supervised features/target...")
features, targets = transform_ts_data_info_features_and_target(
    ts_data, window_size=24 * 28, step_size=23
)

# ─────────────────────────────────────────────────────────────
# Step 3: Load Best Hyperparameters (from Optuna)
# ─────────────────────────────────────────────────────────────
best_parameters = {
    "n_estimators": 709,
    "learning_rate": 0.02070598529017565,
    "num_leaves": 877,
    "max_depth": 9,
    "min_child_samples": 94,
    "subsample": 0.5363259753060031,
    "colsample_bytree": 0.9194824646782057,
    "objective": "regression_l1",
    "random_state": 42,
}

# ─────────────────────────────────────────────────────────────
# Step 4: Train model
# ─────────────────────────────────────────────────────────────
print("🎯 Training LightGBM with Optuna best hyperparameters...")
pipeline = get_pipeline(**best_parameters)
pipeline.fit(features, targets)

# ─────────────────────────────────────────────────────────────
# Step 5: Evaluate performance
# ─────────────────────────────────────────────────────────────
predictions = pipeline.predict(features)
test_mae = mean_absolute_error(targets, predictions)

print(f"📉 New model MAE: {test_mae:.4f}")
metric = load_metrics_from_registry()
print(f"📈 Previous model MAE: {metric['test_mae']:.4f}")

# ─────────────────────────────────────────────────────────────
# Step 6: Register if improved
# ─────────────────────────────────────────────────────────────
if test_mae < metric.get("test_mae"):
    print("✅ New model outperforms previous. Registering...")

    model_path = config.MODELS_DIR / "lgb_model.pkl"
    joblib.dump(pipeline, model_path)

    input_schema = Schema(features)
    output_schema = Schema(targets)
    model_schema = ModelSchema(input_schema=input_schema, output_schema=output_schema)

    project = get_hopsworks_project()
    model_registry = project.get_model_registry()

    model = model_registry.sklearn.create_model(
        name="citibike_demand_predictor_next_hour",
        metrics={"test_mae": test_mae},
        input_example=features.sample(),
        model_schema=model_schema,
    )
    model.save(str(model_path))
else:
    print("🚫 New model did not beat previous MAE. Skipping registration.")
