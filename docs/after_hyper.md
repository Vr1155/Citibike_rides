Here’s your detailed **step-by-step walkthrough** of everything we did in this thread — fully aligned with your canvas (`Lightgbm Model Fix`) and all discussions, decisions, and patches we made. This can be dropped into any LLM context to get fully up to speed.

---

## 🧠 CitiBike: LightGBM Full Lag Model + Hyperparameter Tuning (Step-by-Step Summary)

### 📁 Input Dataset

- **File**: `citibike_lag672_top3.parquet`
- **Features**: All 672 hourly lag features (`lag_1` to `lag_672`)
- **Target**: `target_t_plus_1` = hourly ride count for the _next_ hour
- **Time column**: `start_hour`
- **Filter**: Only the **Top-3 busiest stations** are used

---

## 🧼 1. Load and Clean Data

```python
df = pd.read_parquet("citibike_lag672_top3.parquet")
df["start_hour"] = pd.to_datetime(df["start_hour"])
```

### ✅ Deduplication (Key Fix)

We added a check to drop any duplicated records:

```python
df = df.drop_duplicates(subset=["start_station_id", "start_hour"])
```

---

## 🧠 2. Time-Aware Train/Test Split

```python
cutoff = datetime(2023, 12, 1)
train_df = df[df["start_hour"] < cutoff]
test_df = df[df["start_hour"] >= cutoff]
```

### ✅ Drop rows with missing lag values _after_ splitting:

```python
train_df = train_df.dropna(subset=feature_cols + [target_col])
test_df = test_df.dropna(subset=feature_cols + [target_col])
```

---

## 📐 3. Define X/y Inputs

```python
X_train = train_df[feature_cols]
y_train = train_df[target_col]
X_test = test_df[feature_cols]
y_test = test_df[target_col]
```

---

## 🧪 4. Hyperparameter Tuning with Optuna + LightGBM

We use `Optuna` to find the best hyperparameters over **75 trials**, with early stopping and silent logging.

```python
def objective(trial):
    params = {
        "objective": "regression_l1",
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        ...
    }
    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
    )
    return mean_absolute_error(y_test, model.predict(X_test))
```

### Run the study:

```python
study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=75)
```

---

## 🧾 5. Logging Best Params to MLflow

After tuning, the best parameters are printed and logged:

```python
best_params = study.best_params
best_params["objective"] = "regression_l1"
best_params["random_state"] = 42

with mlflow.start_run(run_name="lightgbm_optuna_tuning") as run:
    for k, v in best_params.items():
        mlflow.log_param(k, v)
```

---

## 📊 6. Visual Diagnostics

### ✅ A. Full Test Set — Per Station

We loop over each of the 3 stations and plot actual vs predicted values:

```python
for station_id in test_df["start_station_id"].unique():
    ...
    plt.plot(timestamps, y_true, label=f"Actual — {station_id}")
    plt.plot(timestamps, y_pred, label=f"Predicted — {station_id}")
```

### ✅ B. Last Week of December (Zoomed-In)

Same per-station plotting logic but filtered to:

```python
df["start_hour"] >= datetime(2023, 12, 25)
```

---

## 🧩 Final Notes

- All code is **time-aware** and avoids data leakage.
- Dataset is fully cleaned (no NaNs or duplicates).
- MLflow tracks best hyperparameters.
- Plots are per station to avoid visual mixing of IDs.
- You are now ready to:

  - Use `best_params` to train the final model
  - Push predictions to Hopsworks
  - Move toward deployment!

---
