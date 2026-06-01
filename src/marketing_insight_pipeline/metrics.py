"""Weighted KPI calculations for marketing performance data."""

from __future__ import annotations

import numpy as np
import pandas as pd

DIMENSION_COLUMNS = ["campaign_id", "campaign_name", "channel"]
MONTH_COLUMN = "month"
METRIC_COLUMNS = ["impressions", "clicks", "spend", "conversions", "revenue"]


def safe_divide(numerator: pd.Series | float, denominator: pd.Series | float) -> pd.Series | float:
    """Divide while returning NaN for zero denominators."""
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator / denominator
    if isinstance(result, pd.Series):
        return result.replace([np.inf, -np.inf], np.nan)
    return np.nan if denominator == 0 else result


def add_kpis(frame: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic weighted KPIs from already aggregated totals."""
    result = frame.copy()
    result["ctr_pct"] = safe_divide(result["clicks"], result["impressions"]) * 100
    result["cvr_pct"] = safe_divide(result["conversions"], result["clicks"]) * 100
    result["cpc"] = safe_divide(result["spend"], result["clicks"])
    result["cpm"] = safe_divide(result["spend"], result["impressions"]) * 1000
    result["cpa"] = safe_divide(result["spend"], result["conversions"])
    result["roas"] = safe_divide(result["revenue"], result["spend"])
    result["revenue_per_conversion"] = safe_divide(result["revenue"], result["conversions"])
    return result


def aggregate_performance(data: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
    """Aggregate raw data by dimensions, then calculate KPIs from totals."""
    grouped = (
        data.groupby(group_by, dropna=False, as_index=False)[METRIC_COLUMNS]
        .sum()
        .sort_values(group_by)
        .reset_index(drop=True)
    )
    return add_kpis(grouped)


def campaign_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return campaign-level weighted KPI summary."""
    return aggregate_performance(data, DIMENSION_COLUMNS)


def channel_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return channel-level weighted KPI summary."""
    return aggregate_performance(data, ["channel"])


def monthly_trend(data: pd.DataFrame) -> pd.DataFrame:
    """Return monthly weighted KPI trend."""
    dated = data.copy()
    dated[MONTH_COLUMN] = pd.to_datetime(dated["date"]).dt.to_period("M").astype(str)
    return aggregate_performance(dated, [MONTH_COLUMN])


def overall_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return a one-row all-campaign weighted KPI summary."""
    totals = data[METRIC_COLUMNS].sum().to_frame().T
    totals.insert(0, "scope", "All campaigns")
    return add_kpis(totals)
