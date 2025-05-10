Below is an end‑to‑end **technical play‑by‑play** of everything we accomplished in this thread, in the exact order it happened, with every decision, fix, and code artifact accounted for. Treat it as a ready‑to‑load “context primer” for any future LLM session: paste it in and the model will instantly understand where the Citi Bike migration stands and why each file looks the way it does.

---

## 0⃣ Starting State

- **Input:**

  - Raw Citi Bike CSVs (12 month‑folders under `data/raw/2023‑citibike‑tripdata/…`).
  - NYC‑Taxi notebooks 02‑06 that needed porting.

- **Goal:**

  - Re‑create the same raw‑►features pipeline for Citi Bike, but make every transformation _visible inside Jupyter_ before persisting to Parquet.
  - Add rich diagnostics/visualisation so we can eyeball the dataset at each stage.

---

## 1⃣⃣ Notebook 02 ➞ `02_validate_and_save_citibike.py`

| Step    | What we did                                            | Key details / pitfalls fixed                                                                                                                                            |
| ------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1.1** | Created a new canvas script based on Taxi notebook 02. | File: **`02_validate_and_save_citibike.py`**                                                                                                                            |
| **1.2** | Switched constants & schema.                           | `RAW_FOLDER = data/raw/2023‑citibike‑tripdata`; canonical columns list for Citi Bike.                                                                                   |
| **1.3** | Modified file discovery.                               | Recursive `Path.rglob("*citibike‑tripdata*.csv*")` so it sees files inside month sub‑dirs.                                                                              |
| **1.4** | Fixed dtypes.                                          | `start_station_id` / `end_station_id` set to **string** (needed after `SYS038` parse error).                                                                            |
| **1.5** | Dropped taxi‑specific validations.                     | Removed distance / fare checks; kept ride‑ID uniqueness; kept timestamps order.                                                                                         |
| **1.6** | **Geo filter turned into flag.**                       | We no longer drop out‑of‑bounds rides; instead `df["off_grid"] = ~mask_geo`.                                                                                            |
| **1.7** | Added first‑run _quick Plotly_ map.                    | Produces `reports/citibike_startpoints_map.html` for a fast sanity check.                                                                                               |
| **1.8** | Path‑resolver for notebooks vs repo root.              | `DATA_DIR` auto‑detects so the code works whether run from `/notebooks` or repo root.                                                                                   |
| **1.9** | Output artefacts.                                      | _On success_ the script writes:<br>   • `data/processed/2023/citibike_2023_all.parquet` (rides)<br>   • `data/processed/stations_2023.parquet` (unique station‑lat/lon) |

---

## 2⃣⃣ Merged Notebooks 03‑04‑05 ➞ `03_transform_full_pipeline_citibike.py`

| Stage   | Transformation                                              | Visible output inside notebook                                                                                                                                                                                                                                 |
| ------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **2.1** | **Load** consolidated parquet.                              | `.head()` preview.                                                                                                                                                                                                                                             |
| **2.2** | **Aggregate** rides → hourly counts per `start_station_id`. | `.head()`, shape.                                                                                                                                                                                                                                              |
| **2.3** | **Expand** to full hour × station grid (zero‑fill).         | Shows missing‑value fill statistics.                                                                                                                                                                                                                           |
| **2.4** | **Feature engineering**                                     | _Per row_:<br>   • 1‑day, 7‑day, 28‑day lags (`lag_24`, `lag_168`, `lag_672`)<br>   • 7‑day rolling mean (`roll7`)<br>   • Cyclical sin/cos for `hour`, `dow`<br>   • `is_weekend`, `is_holiday` flags (US holidays 2023)<br>   • `target` = next‑hour `rides` |
| **2.5** | Inline diagnostics                                          |  • Calls `quick_visualize` to plot rides for ≤5 stations.<br>  • `.head()` / `.tail()` of final DF.                                                                                                                                                            |
| **2.6** | **Persist** features _after_ eyeballing.                    | `data/processed/2023/citibike_hourly_features.parquet`                                                                                                                                                                                                         |
| **2.7** | Re‑load features & extra plots                              |  • Month bar, hour box, hour×DOW heatmap, Pearson corr heatmap, multi‑feature timeseries.                                                                                                                                                                      |

_The script has **no `main` guard**—running the last cell executes everything automatically._

---

## 3⃣⃣ Standalone Visuals ➞ `06_visualization_citibike.py`

This notebook is a read‑only analytics dashboard for the feature parquet.

| Block                         | Content & Fixes                                                                                                                                                       |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **3.1 Loader**                | Dynamically resolves `DATA_DIR` and loads:<br>   • `.../citibike_hourly_features.parquet`<br>   • `.../stations_2023.parquet` (or rebuilds from features if missing). |
| **3.2 Column guards**         | Auto‑creates `month`, `hour`, `dow` if absent (fixed KeyError on `month`).                                                                                            |
| **3.3 Station‑ID harmoniser** | Renames `station_id` → `start_station_id` etc. so merges never fail (fixed KeyError on merge).                                                                        |
| **3.4 Visual helpers**        | Functions: `plot_network_total`, `plot_box_hour`, `plot_monthly_seasonality`, `plot_heatmap_hour_dow`, `plot_corr_heatmap`, `plot_map_avg_rides`.                     |
| **3.5 Execution**             | Calls every plot in sequence—run once, get the full visual suite.                                                                                                     |

---

## 4⃣⃣ Key Pitfalls We Solved

1. **Nested month folders** – used `rglob` recursion.
2. **Alphanumeric station IDs (`SYS038`)** – switched ID dtype to `string`.
3. **Out‑of‑bound geo points** – replaced row‑drop with flagging.
4. **Notebook vs project‑root paths** – dynamic `DATA_DIR`.
5. **Missing calendar columns** – auto‑derived in visual notebook.
6. **Station metadata merge failure** – column harmoniser.

---

## 5⃣⃣ Files & Their Responsibilities

| File (canvas)                                | What it does                                                         | Outputs                                                              |
| -------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **`02_validate_and_save_citibike.py`**       | Raw CSV → validated Parquet (+ station parquet)                      | `citibike_2023_all.parquet`, `stations_2023.parquet`, quick HTML map |
| **`03_transform_full_pipeline_citibike.py`** | Raw Parquet → hourly grid → engineered features → final Parquet      | `citibike_hourly_features.parquet` + multiple inline plots           |
| **`06_visualization_citibike.py`**           | Loads features/stations and produces an interactive visual dashboard | Inline Plotly figures (network totals, heatmaps, bubble map, etc.)   |

Everything is self‑contained: install requirements (`pandas`, `plotly`, `holidays`, `numpy`) and run notebooks 02 ➞ 03 ➞ 06.

---

## 6⃣⃣ Next‑Run Checklist (for future you / any LLM)

1. **Place** raw monthly CSVs under `data/raw/2023‑citibike‑tripdata/202301‑.../`.
2. **Run** notebook 02 cell – verify ride & station parquet + HTML map appear.
3. **Run** notebook 03 cell – watch transformations + final Parquet.
4. **Run** notebook 06 cell – visual sanity check on trends, seasonality, geo distribution.
5. **Proceed** to modelling (LightGBM + Optuna) exactly as outlined in `project_plan.md`.

No hidden dependencies, no hard‑coded paths beyond the project‑root `data/` hierarchy, and every intermediate DataFrame is previewed before being written, preventing silent schema drift.

---

## 7⃣⃣ Notebook 06 Update ➞ Top‑3 Station Selection

| Step    | What we added/changed                                   | Key details & artefacts                                                                                           |
| ------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **7.1** | **Top‑3 detector** appended to the end of the notebook. | Calculates cumulative `rides` per `start_station_id` from the engineered feature parquet.                         |
| **7.2** | Interactive bar chart for manual eyeballing.            | Uses Plotly to show Top‑10 stations; visually confirms the workload distribution.                                 |
| **7.3** | **Persisted selected stations**                         | Writes list of the three busiest station IDs to `data/processed/2023/top3_stations.json`.                         |
| **7.4** | **Filtered training dataset**                           | Filters feature DF to only those stations and writes `data/processed/2023/citibike_hourly_features_top3.parquet`. |
| **7.5** | Notebook save path fixed                                | Re‑exported notebook as `06_visualization_top_3.ipynb` while keeping original insights intact.                    |
| **7.6** | Script counterpart (for CI)                             | Added `06_visualization_top3.py` in `/src/` so GitHub Actions can run the same logic headlessly.                  |

These changes satisfy the grading‑rubric requirement to **“select top 3 locations and store the transformed data in Hopsworks.”** Future notebooks (07+ modelling) should read the new Top‑3 parquet, and CI pipelines can pick up the JSON list to stay schema‑agnostic.

---

## 8⃣⃣ Hopsworks Ingestion and 672 Lag Features for Top‑3 Stations

| Step    | What we implemented                                     | Key details                                                                                                                  |
| ------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **8.1** | Feature Group for Top‑3 stations' features              | Created in `12_load_features_hopsworks.ipynb`, FG named `bike_hourly_fg`, data from `citibike_hourly_features_top3.parquet`. |
| **8.2** | Feature View created                                    | Registered as `bike_hourly_fv` version 1.                                                                                    |
| **8.3** | Environment setup for Hopsworks                         | `.env` file used for secrets; `python-dotenv` integrated; relative path fixes for notebooks.                                 |
| **8.4** | Script created to generate 672 lag features             | `13_generate_top3_lag672_features.py` created full `lag_1` to `lag_672` columns from `target_t_plus_1`, per station.         |
| **8.5** | Data filtered to only last 672 hours for top-3 stations | Ensures compute efficiency and satisfies rubric for 28-day lag model.                                                        |
| **8.6** | Feature Group for lag_672 features pushed to Hopsworks  | Created in `14_push_lag672_top3_to_hopsworks.py`, registered as `bike_lag672_top3_fg` (offline only).                        |
| **8.7** | Final parquet path                                      | Stored at `data/processed/2023/citibike_lag672_top3.parquet`                                                                 |

✅ This closes the Data Engineering phase entirely. All rubric checkboxes are fulfilled. Model notebooks can now safely assume:
• `bike_hourly_fv` → for inference/test lookup
• `bike_lag672_top3_fg` → for training LightGBM w/ full lag stack
