"""Transparent objective-based campaign ranking."""

from __future__ import annotations

import pandas as pd


def _normalize_high(series: pd.Series) -> pd.Series:
    minimum = series.min()
    maximum = series.max()
    if pd.isna(minimum) or pd.isna(maximum) or maximum == minimum:
        return pd.Series(1.0, index=series.index)
    return (series - minimum) / (maximum - minimum)


def _normalize_low(series: pd.Series) -> pd.Series:
    return 1 - _normalize_high(series)


def apply_qualification(
    summary: pd.DataFrame,
    *,
    min_spend: float = 0.0,
    min_clicks: int = 0,
    min_conversions: int = 0,
) -> pd.DataFrame:
    """Filter campaigns to reduce small-sample overinterpretation."""
    return summary[
        (summary["spend"] >= min_spend)
        & (summary["clicks"] >= min_clicks)
        & (summary["conversions"] >= min_conversions)
    ].copy()


def rank_campaigns(
    summary: pd.DataFrame,
    objective: str,
    *,
    min_spend: float = 0.0,
    min_clicks: int = 0,
    min_conversions: int = 0,
) -> pd.DataFrame:
    """Rank campaigns using explicit deterministic rules for each objective."""
    qualified = apply_qualification(
        summary,
        min_spend=min_spend,
        min_clicks=min_clicks,
        min_conversions=min_conversions,
    )
    if qualified.empty:
        return qualified.assign(rank_score=pd.Series(dtype=float), rank=pd.Series(dtype=int))

    ranked = qualified.copy()
    if objective == "traffic":
        ranked["rank_score"] = 0.55 * _normalize_low(ranked["cpc"]) + 0.45 * _normalize_high(ranked["ctr_pct"])
    elif objective == "conversion":
        ranked["rank_score"] = 0.60 * _normalize_low(ranked["cpa"]) + 0.40 * _normalize_high(ranked["conversions"])
    elif objective == "revenue":
        ranked["rank_score"] = 0.65 * _normalize_high(ranked["roas"]) + 0.35 * _normalize_high(ranked["revenue"])
    else:
        raise ValueError("objective must be one of: traffic, conversion, revenue")

    ranked = ranked.sort_values(["rank_score", "revenue"], ascending=[False, False]).reset_index(drop=True)
    ranked["rank"] = ranked.index + 1
    return ranked


def potential_scale_candidates(ranked: pd.DataFrame, objective: str, limit: int = 3) -> pd.DataFrame:
    """Return objective-aware high-performing campaigns to consider scaling."""
    if ranked.empty:
        return ranked
    if objective == "traffic":
        candidates = ranked[(ranked["ctr_pct"] >= ranked["ctr_pct"].median()) & (ranked["cpc"] <= ranked["cpc"].median())]
    elif objective == "conversion":
        candidates = ranked[
            (ranked["conversions"] >= ranked["conversions"].median()) & (ranked["cpa"] <= ranked["cpa"].median())
        ]
    elif objective == "revenue":
        candidates = ranked[(ranked["roas"] >= ranked["roas"].median()) & (ranked["revenue"] >= ranked["revenue"].median())]
    else:
        raise ValueError("objective must be one of: traffic, conversion, revenue")
    return candidates.head(limit).copy()


def efficiency_review_candidates(summary: pd.DataFrame, objective: str, limit: int = 3) -> pd.DataFrame:
    """Return objective-aware campaigns with weak efficiency for budget review."""
    if summary.empty:
        return summary
    if objective == "traffic":
        candidates = summary[(summary["ctr_pct"] <= summary["ctr_pct"].quantile(0.25)) | (summary["cpc"] >= summary["cpc"].quantile(0.75))]
        return candidates.sort_values(["ctr_pct", "cpc"], ascending=[True, False]).head(limit).copy()
    if objective == "conversion":
        candidates = summary[
            (summary["cvr_pct"] <= summary["cvr_pct"].quantile(0.25)) | (summary["cpa"] >= summary["cpa"].quantile(0.75))
        ]
        return candidates.sort_values(["cvr_pct", "cpa"], ascending=[True, False]).head(limit).copy()
    if objective == "revenue":
        candidates = summary[
            (summary["roas"] <= summary["roas"].quantile(0.25)) | (summary["revenue"] <= summary["revenue"].quantile(0.25))
        ]
        return candidates.sort_values(["roas", "revenue"], ascending=[True, True]).head(limit).copy()
    raise ValueError("objective must be one of: traffic, conversion, revenue")
