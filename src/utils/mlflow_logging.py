"""
mlflow_logging.py – unified MLflow helpers for Taxi and Citi Bike projects.

Placed under **src/utils/** so notebooks can do:
```python
from src.utils.mlflow_logging import set_mlflow_tracking, log_model_to_mlflow
```

Key improvements vs. legacy `experiment_utils.py`:
• `experiment_name` is **optional** – if omitted we fall back to `model_name` or a default.
• Graceful fallback when `MLFLOW_TRACKING_URI` is not set (uses local `mlruns/`).
• Accepts any model that implements `.predict(X)`.
• Keeps identical behaviour for old code that still passes `experiment_name`.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import mlflow
from mlflow.models import infer_signature

# --------------------------------------------------------------------------- #
# Logging setup
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #

def set_mlflow_tracking() -> None:
    """Configure MLflow tracking URI if environment variable is present.

    If **MLFLOW_TRACKING_URI** is missing, MLflow will default to a local file
    store at `./mlruns/`. This makes the helper safe for laptops as well as
    remote tracking servers (e.g. on AWS S3, Hopsworks, or Databricks).
    """
    uri = os.getenv("MLFLOW_TRACKING_URI")
    if uri:
        mlflow.set_tracking_uri(uri)
        logger.info("MLflow tracking URI set from environment.")
    else:
        default_uri = f"file://{Path.cwd() / 'mlruns'}"
        mlflow.set_tracking_uri(default_uri)
        logger.warning(
            "MLFLOW_TRACKING_URI not found; falling back to local store at %s",
            default_uri,
        )


def log_model_to_mlflow(
    model: Any,
    X_sample,
    *,
    model_name: Optional[str] = None,
    metric_name: str = "metric",
    score: Optional[float] = None,
    experiment_name: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
):
    """Log a model + metadata to MLflow.

    Parameters
    ----------
    model : Any
        Fitted model implementing `.predict(X)`.
    X_sample : pd.DataFrame | np.ndarray
        Sample input for signature inference and validation.
    model_name : str, optional
        Name to register the model under. Also used as experiment name when
        *experiment_name* is omitted.
    metric_name : str, default "metric"
        Metric name to log (*score* must be provided).
    score : float, optional
        Metric value to log.
    experiment_name : str, optional
        MLflow experiment. If missing we fall back to *model_name* or
        "citibike_baselines".
    params : dict, optional
        Hyper‑parameters to log.
    """

    # -------- safety checks --------------------------------------------------
    if not hasattr(model, "predict"):
        raise AttributeError("model object must implement a .predict() method")

    if experiment_name is None:
        experiment_name = model_name or "citibike_baselines"

    # Ensure MLflow is initialised
    set_mlflow_tracking()
    mlflow.set_experiment(experiment_name)
    logger.info("Using MLflow experiment: %s", experiment_name)

    # Start run
    with mlflow.start_run():
        if params:
            mlflow.log_params(params)
            logger.info("Logged params: %s", params)

        if score is not None:
            mlflow.log_metric(metric_name, score)
            logger.info("Logged %s: %.4f", metric_name, score)

        # Infer signature (works for pandas/numpy)
        try:
            signature = infer_signature(X_sample, model.predict(X_sample))
        except Exception as err:  # noqa: BLE001
            logger.warning("Could not infer signature automatically: %s", err)
            signature = None

        # Decide artifact path
        art_path = "model_artifact"
        if model_name is None:
            model_name = model.__class__.__name__

        # Log model – supports sklearn & generic pyfunc via mlflow.pyfunc
        try:
            model_info = mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path=art_path,
                registered_model_name=model_name,
                signature=signature,
                input_example=X_sample,
            )
        except mlflow.MlflowException:
            # Fallback to pyfunc if not sklearn‑serialisable
            model_info = mlflow.pyfunc.log_model(
                python_model=model,
                artifact_path=art_path,
                registered_model_name=model_name,
                signature=signature,
                input_example=X_sample,
            )
        logger.info("Model logged under name: %s", model_name)
        return model_info
