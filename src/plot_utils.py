"""
plot_utils.py – universal plotting helpers for both NYC‑Taxi and Citi Bike projects.

Key upgrades over the taxi‑only version:
• Works directly with Series that have a DatetimeIndex (Citi Bike pipeline)
• Keeps backward compatibility with the original `row_id` + `features` signature
• Lets caller choose column names via `time_col` and `location_col`
• Adds `title` kwarg so notebooks can set their own figure title cleanly
"""

from datetime import timedelta
from typing import Optional

import pandas as pd
import plotly.express as px


def _legacy_plot(features: pd.DataFrame, targets: pd.Series, row_id: int, predictions: Optional[pd.Series] = None):
    """Internal helper recreating the original taxi‑style plot (row‑index selection)."""
    # Extract the location’s row
    location_features = features.iloc[row_id]
    actual_target = targets.iloc[row_id]

    # Time‑series columns (lagged ride counts)
    ts_cols = [c for c in features.columns if c.startswith("rides_t-")]
    ts_values = [location_features[c] for c in ts_cols] + [actual_target]

    # Build date range up to the ‘current’ hour
    dates = pd.date_range(
        start=location_features["pickup_hour"] - timedelta(hours=len(ts_cols)),
        end=location_features["pickup_hour"],
        freq="h",
    )

    fig = px.line(
        x=dates,
        y=ts_values,
        template="plotly_white",
        markers=True,
        title=(
            f"Pickup Hour: {location_features['pickup_hour']}, "
            f"Location ID: {location_features['pickup_location_id']}"
        ),
        labels={"x": "Time", "y": "Ride Counts"},
    )

    # Actual value marker (green)
    fig.add_scatter(
        x=dates[-1:],
        y=[actual_target],
        line_color="green",
        mode="markers",
        marker_size=10,
        name="Actual Value",
    )

    # Optional prediction marker (red)
    if predictions is not None:
        fig.add_scatter(
            x=dates[-1:],
            y=[predictions.iloc[row_id]],
            line_color="red",
            mode="markers",
            marker_symbol="x",
            marker_size=15,
            name="Prediction",
        )
    return fig


def plot_aggregated_time_series(
    y_true: pd.Series,
    y_pred: Optional[pd.Series] = None,
    *,
    title: str = "",
    location_col: str = "pickup_location_id",
    features: Optional[pd.DataFrame] = None,
    row_id: Optional[int] = None,
    time_col: str = "pickup_hour",
):
    """Flexible time-series plotter that supports both Citi Bike and legacy taxi data.

    Parameters
    ----------
    y_true : pd.Series
        Truth values (must share index with *y_pred* if provided).
    y_pred : Optional[pd.Series]
        Forecast values aligned on the same index as *y_true* (optional).
    title : str, optional
        Plot title; auto-generated if blank.
    location_col : str, optional
        Name of the location identifier column in *features* (default taxi). Ignored
        when plotting purely from *y_true*/*y_pred*.
    features : Optional[pd.DataFrame]
        Full feature dataframe – needed only for legacy row‑selection mode.
    row_id : Optional[int]
        Legacy mode: integer row index to pick from *features*/*targets*.
    time_col : str, optional
        Name of timestamp column in *features* (legacy mode only).
    """

    # ------- Legacy taxi mode -------------------------------------------------
    if features is not None and row_id is not None:
        return _legacy_plot(features, y_true, row_id, y_pred)

    # ------- Modern mode: DatetimeIndex‑based ---------------------------------
    if not isinstance(y_true.index, pd.DatetimeIndex):
        raise ValueError(
            "y_true must have a DatetimeIndex or you must supply features+row_id"
        )

    if y_pred is not None and not y_true.index.equals(y_pred.index):
        raise ValueError("y_true and y_pred must share the same index")

    # Build figure
    fig = px.line(
        x=y_true.index,
        y=y_true.values,
        template="plotly_white",
        markers=True,
        title=title or "Ride Demand vs Time",
        labels={"x": "Time", "y": "Ride Counts"},
    )

    # Add prediction marker if provided (plotly can overlay another line too)
    if y_pred is not None:
        fig.add_scatter(
            x=y_pred.index,
            y=y_pred.values,
            mode="lines+markers",
            line_dash="dash",
            name="Prediction",
        )
    return fig


def plot_prediction(
    features: pd.DataFrame,
    prediction: pd.DataFrame,
    *,
    time_col: str = "pickup_hour",
    location_col: str = "pickup_location_id",
):
    """Plot a single timestamp’s historical lags plus predicted next‑hour demand."""

    ts_cols = [c for c in features.columns if c.startswith("rides_t-")]
    ts_values = [features[c].iloc[0] for c in ts_cols] + prediction["predicted_demand"].tolist()

    pickup_hour = pd.Timestamp(features[time_col].iloc[0])
    dates = pd.date_range(start=pickup_hour - timedelta(hours=len(ts_cols)), end=pickup_hour, freq="h")

    fig = px.line(
        x=dates,
        y=ts_values,
        template="plotly_white",
        markers=True,
        title=(
            f"{time_col}: {pickup_hour}, "
            f"{location_col}: {features[location_col].iloc[0]}"
        ),
        labels={"x": "Time", "y": "Ride Counts"},
    )

    # Prediction marker
    fig.add_scatter(
        x=[pickup_hour],
        y=prediction["predicted_demand"].tolist(),
        line_color="red",
        mode="markers",
        marker_symbol="x",
        marker_size=10,
        name="Prediction",
    )

    return fig
