# Citi Bike Demand‑Forecasting — Migration Plan

_(adapted from the NYC‑Taxi MLOps project)_
**Last updated · 2025‑05‑09**

---

## Project Goals

- Re‑use the taxi codebase to forecast **hourly Citi Bike demand per station**.
- Keep APIs/file‑formats unchanged wherever possible.
- Store features, models, and predictions in **Hopsworks**; surface live metrics with **Streamlit Community Cloud**.

---

## Project Folder Structure

The repository root is **`CITIBIKE_RIDES/`** (screenshot from VS Code shown earlier).
Below is the canonical layout after migration — notebooks, pipelines and code folders match the taxi repo, while raw data mirrors the Citi Bike download buckets.

```
CITIBIKE_RIDES
├── data
│   ├── raw
│   │   ├── 2023-citibike-tripdata
│   │   │   ├── 202301‑citibike‑tripdata
│   │   │   ├── … (one folder per month) …
│   │   │   └── 202312‑citibike‑tripdata
│   │   └── zip_files/                     # archived zips (kept for provenance)
│   └── processed
│       └── 2023/citibike_2023_all.parquet # single consolidated parquet (created)
├── frontend
│   ├── __init__.py
│   ├── frontend_monitor.py                # MAE / MAPE dashboard
│   └── frontend_v2.py                     # circle‑map analytics dashboard
├── notebooks
│   ├── 01_fetch_data.ipynb
│   ├── 02_validate_and_save.ipynb
│   ├── 03_transform_processed_data_into_ts_data.ipynb
│   ├── 04_transform_ts_data_into_features_and_targets.ipynb
│   ├── 05_transform_raw_data_into_features_and_targets.ipynb
│   ├── 06_visualization.ipynb
│   ├── 07_baseline_models.ipynb
│   ├── 08_xgboost_model.ipynb
│   ├── 09_lightgbm_model.ipynb
│   ├── 10_lgm_with_fe.ipynb
│   ├── 11_lgm_hyper.ipynb
│   ├── 12_load_features_hopsworks.ipynb
│   ├── 13_feature_pipeline.ipynb
│   ├── 14_model_training_pipeline.ipynb
│   ├── 15_predict_using_hopsworks_model.ipynb
│   ├── 16_inference_pipeline.ipynb
│   ├── 17_fetch_predictions.ipynb
│   ├── 18_plot_mae.ipynb
│   ├── 19_retraining_model.ipynb
│   ├── 20_hyperparameter_tuning.ipynb
│   ├── 21_fft_arma_arima_prophet.ipynb
│   ├── nyc_taxi_predictions.html           # legacy artefact (kept for reference)
│   ├── test_frontend_v2.ipynb
│   └── Untitled3.ipynb
├── pipelines
│   ├── __init__.py
│   ├── inference_pipeline.py
│   └── model_training_pipeline.py
├── src
│   ├── __init__.py
│   ├── config.py
│   ├── data_utils.py
│   ├── experiment_utils.py
│   ├── feature_pipeline.py
│   ├── frontend_v1.py
│   ├── frontend.py
│   ├── inference.py
│   ├── pipeline_utils.py
│   └── plot_utils.py
├── test
│   └── sample_app.py
├── requirements.txt
├── requirements_feature_pipeline.txt
├── requirements_with_version.txt
├── requirements_final.txt
├── todo.md
├── vscode_config.json
├── LICENSE
└── README.md
```

> **Note**: the migration scripts will **create** the `processed/` tree and Parquet files; everything else already exists in the repo.

---

## Raw‑Data Consolidation

- **Input** : 53 CSV files (\~6.9 GB) in `data/raw/2023‑*/`.
- **Output** : `data/processed/2023/citibike_2023_all.parquet` (PyArrow).
- **Steps**

  1. Chunk‑read (1 M rows) → cast to canonical schema.
  2. Drop _exact‑row_ duplicate `ride_id`s; log the count.
  3. External merge‑sort by `started_at`, `ride_id`.
  4. Write Parquet with `pyarrow` compression (`snappy`).

- **Canonical columns**:
  `ride_id, rideable_type, started_at, ended_at, start_station_name, start_station_id, end_station_name, end_station_id, start_lat, start_lng, end_lat, end_lng, member_casual`
- **Timezone**: treat datetimes as naïve **America/New_York**.

---

## Feature Engineering

1. **Aggregate** rides per `start_station_id` × `start_hour` → `ride_count`.
2. **Lag features**: `rides_t‑1 … rides_t‑672` (28 days).
3. **Calendar features**: hour & weekday sine/cosine, holiday flag.
4. **Rolling 30‑day popularity**.
5. **Rider mix**: `member_share`, `share_electric`, `share_classic`.
6. **Label** column added as `"target"` (copy of `ride_count`).
7. **Station coordinates**: first run extracts unique `(start_station_id, lat, lon)` into memory; optional `stations_fg` for reuse.

---

## Feature Store (Hopsworks)

| Object        | Name                      | Version | Primary Key                         | Event Time        |
| ------------- | ------------------------- | ------- | ----------------------------------- | ----------------- |
| Feature Group | `bike_hourly_fg`          | 1       | `start_station_id`                  | `start_hour`      |
| Feature View  | `bike_hourly_fv`          | 1       | —                                   | —                 |
| Prediction FG | `bike_demand_predictions` | 1       | `start_station_id, prediction_hour` | `prediction_hour` |

---

## Training & Validation

- **Dataset window**: 2023‑01‑01 → 2023‑12‑31.
- **Split**:

  - Train ≤ 2023‑08‑31
  - Validation 2023‑09‑01 → 2023‑10‑31
  - Test ≥ 2023‑11‑01

- **Model**: LightGBM (regression_l1).
- **Hyper‑parameter tuning**: Optuna, 75 trials, best pipeline saved as `citibike_lgbm_optuna_best`.

---

## Drift & Retraining

- Compute 7‑day rolling MAE from `bike_demand_predictions`.
- **Trigger** retrain when weekly MAE > **1.5 × training MAE**.
- New model registered and auto‑promoted if it beats previous validation MAE.

---

## Inference Pipeline

- Runs **hourly** via GitHub Action (`5 * * * *`).
- Retrieves latest hour’s features, predicts next hour, writes to `bike_demand_predictions` (offline + online).

---

## Dashboards (Streamlit Community Cloud)

| App                     | Purpose                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------- |
| **frontend_monitor.py** | Displays MAE / MAPE over a selectable window; pulls data from feature store.        |
| **frontend_v2.py**      | Interactive circle‑map of station demand, top‑N lists, and time‑series drill‑downs. |

Secrets required in Streamlit: `HOPSWORKS_API_KEY`, `HOPSWORKS_PROJECT_NAME`.

---

## GitHub Actions Schedules (UTC)

- **Feature engineering** — `30 0 * * *`
- **Model training** — `0 1 * * *`
- **Inference** — `5 * * * *`

---

## Dependencies

- Python 3.12
- Key libs : `pandas`, `pyarrow`, `lightgbm`, `optuna`, `plotly`, `folium`, `geopandas`, `streamlit`, `hopsworks`.

---

## Credentials & Secrets

| Secret                     | Where used                |
| -------------------------- | ------------------------- |
| **HOPSWORKS_API_KEY**      | GitHub Actions, Streamlit |
| **HOPSWORKS_PROJECT_NAME** | GitHub Actions, Streamlit |

---

## First‑Run Checklist

1. Place raw CSVs in `data/raw/2023‑*`.
2. Run consolidation script → verify Parquet & duplicate log.
3. Execute notebooks 02 → 05 once to generate tabular Parquet.
4. Register `bike_hourly_fg` via notebook 12.
5. Run hyper‑parameter tuning (notebook 20) → model registry.
6. Add Hopsworks secrets to GitHub & Streamlit.
7. Enable GitHub Actions workflows.
8. Deploy Streamlit app; confirm live predictions & MAE metrics.
9. Monitor drift; enjoy 🚴📈!
