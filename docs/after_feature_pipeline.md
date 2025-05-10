Here is your full, detailed technical walkthrough of **everything we did** in previous thread to get your CitiBike Feature Engineering pipeline running on GitHub Actions, integrated with Hopsworks 4.2, with full lag support and schema-safe deployment.

---

## 🚧 Migration Goal

**Migrate and scale the NYC Taxi hourly demand forecasting pipeline** to work with CitiBike data:

- Replace `pickup_hour`/`pickup_location_id` with `start_hour`/`start_station_id`
- Generate 672 hourly lag features
- Insert into Hopsworks Feature Store using CI via GitHub Actions
- Make the pipeline **memory-safe** and **schema-aligned**

---

## 🧱 Step-by-Step Technical Walkthrough

### 1. 🔁 NYC → CitiBike Feature Pipeline Refactor

- We started with a legacy `feature_pipeline.py` and `feature_utils.py` built for NYC taxi data
- We rewrote it to:

  - Use `start_station_id`, `start_hour`
  - Read from the full `.parquet` CitiBike file (1.5 GB)
  - Build a complete grid of (station × hourly time index)

---

### 2. 💾 File Source: Large `.parquet` upload

- You uploaded `citibike_2023_all.parquet` (\~1.5GB) to:

  ```
  Resources/citibike/citibike_2023_all.parquet/citibike_2023_all.parquet
  ```

- We used the Hopsworks SDK:

  ```python
  dataset_api.download("Resources/citibike/.../citibike_2023_all.parquet", ...)
  ```

- Avoided `hops.hdfs.download()` which only works in Jupyter environments

---

### 3. ⚙️ GitHub Actions CI Setup

- Created `feature_pipeline.yml`:

  ```yaml
  python-version: "3.9"
  run: python -m src.feature_pipeline
  ```

- Installed dependencies using `pyproject.toml` via:

  ```yaml
  pip install .
  ```

---

### 4. 🧠 Dependency Troubleshooting (Big One)

#### ❌ Problem: `hopsworks==3.0.5` required `hsfs<3.1.0`, but such a version doesn’t exist

#### ❌ `hopsworks==3.7.1` doesn’t exist either

#### ✅ Solution:

- Use `hopsworks==4.2.1` (compatible with your backend 4.2.0)
- Use `pandas==1.5.3`, `numpy==1.24.4` to avoid ABI mismatch
- Remove `hsfs` pinning — it’s bundled with `hopsworks`

---

### 5. 📦 Memory Optimization for GitHub CI

- Your `.parquet` file was huge — caused memory crash (`exit code 143`)
- ✅ Fix:

  - Slice only **December 2023**
  - Add `.copy()` to defragment DataFrame
  - Filter by `df["start_time"].dt.month == 12`

---

### 6. 🕰️ Timezone Comparison Bug Fix

- GitHub Actions raised:

  ```
  TypeError: Cannot compare tz-aware and tz-naive datetime-like objects
  ```

- ✅ Fix:

  ```python
  start_time = start_time.replace(tzinfo=None)
  ```

---

### 7. 📊 Full 672 Lag Feature Support

- You wanted `lag_1` through `lag_672`, not just \[1, 24, 168, 672]
- ✅ We updated `add_lag_features_and_calendar_flags()` to:

  ```python
  for lag in range(1, 673):
      df[f"lag_{lag}"] = df.groupby("start_station_id")["rides"].shift(lag)
  ```

---

### 8. 🧠 Avoiding Schema Conflicts

- We ran into Hopsworks errors like:

  ```
  - pickup_hour missing from schema
  - lag_670 does not exist in Feature Group
  ```

- ✅ Fix:

  - Use `get_or_create_feature_group(...)`
  - Let Hopsworks infer schema from new DataFrame
  - Avoid `get_feature_group(...)` which assumes fixed schema

---

### 9. ⚠️ PerformanceWarning Fix

You saw:

```
DataFrame is highly fragmented — use df.copy() to defragment
```

- ✅ Fix: just added `df = df.copy()` after column generation

---

### 10. 🧪 Final Run & Result

- ✅ GitHub Action downloaded `.parquet`
- ✅ Sliced December rows
- ✅ Generated all features
- ✅ Registered and inserted into Feature Store
- ✅ No crashes, no schema errors
- ✅ Skipped insert if no rows were found (with warning)

---

## 🧯 Pitfalls to Avoid

| Pitfall                                     | Avoidance                                                |
| ------------------------------------------- | -------------------------------------------------------- |
| ❌ Memory crash from 1.5GB load             | Slice input to a known window (e.g. December)            |
| ❌ tz-aware vs tz-naive errors              | Use `.replace(tzinfo=None)`                              |
| ❌ Missing schema columns                   | Use `get_or_create_feature_group()`                      |
| ❌ ABI mismatch (`ValueError: numpy dtype`) | Pin compatible pandas + numpy                            |
| ❌ `hops` module errors                     | Use only `hopsworks` SDK (`hops` is internal to Jupyter) |
| ❌ Fragmented DataFrame warning             | Use `df.copy()` after many `.insert()` calls             |

---

## 🏁 Final Deliverables in Repo

| File                                     | Purpose                                           |
| ---------------------------------------- | ------------------------------------------------- |
| `feature_pipeline.py`                    | Pulls, transforms, registers and inserts features |
| `feature_utils.py`                       | Builds lag features and calendar features         |
| `pyproject.toml`                         | Dependency management for GitHub Actions          |
| `.github/workflows/feature_pipeline.yml` | Scheduled + manual GitHub Action                  |
| `.parquet` in Hopsworks                  | Source of all hourly ride demand                  |

---

Up next, you'd like the **training pipeline** or **inference pipeline** set up next.
