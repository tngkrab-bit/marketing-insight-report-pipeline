"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _fmt(value: object, digits: int = 2) -> str:
    if pd.isna(value):
        return "n/a"
    if isinstance(value, (float, np.floating)):
        return f"{value:,.{digits}f}"
    if isinstance(value, (int, np.integer)):
        return f"{value:,}"
    return str(value)


def _markdown_table(frame: pd.DataFrame, columns: list[str], limit: int = 5) -> str:
    view = frame.loc[:, columns].head(limit).copy()
    if view.empty:
        return "_No qualifying rows._"
    headers = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(_fmt(row[column]) for column in columns) + " |")
    return "\n".join([headers, separator, *rows])


def build_report(
    *,
    objective: str,
    overall: pd.DataFrame,
    campaign_summary: pd.DataFrame,
    channel_summary: pd.DataFrame,
    ranked: pd.DataFrame,
    scale_candidates: pd.DataFrame,
    review_candidates: pd.DataFrame,
    validation: dict[str, object],
    ai_summary: str | None = None,
) -> str:
    """Build a public-safe Markdown analytics report."""
    total = overall.iloc[0]
    top = ranked.iloc[0] if not ranked.empty else None
    executive_summary = ai_summary or (
        f"The analysis covers {int(total['impressions']):,} impressions, "
        f"{int(total['clicks']):,} clicks, and ${float(total['spend']):,.2f} in spend. "
        f"Overall ROAS is {_fmt(total['roas'])}, with a weighted CTR of {_fmt(total['ctr_pct'])}%."
    )

    top_line = (
        f"{top['campaign_name']} ranked first for the {objective} objective with score {_fmt(top['rank_score'])}."
        if top is not None
        else "No campaign met the qualification thresholds."
    )

    warnings = validation.get("warnings", [])
    warning_text = "\n".join(f"- {item}" for item in warnings) if warnings else "- No validation warnings."

    return f"""# Marketing Analytics Report

## Analysis Scope

- Objective: `{objective}`
- Rows analyzed: {validation.get("row_count", 0)}
- Data source: synthetic public-safe campaign data

## Executive Summary

{executive_summary}

{top_line}

## KPI Summary

| Metric | Value |
| --- | --- |
| Impressions | {_fmt(total['impressions'], 0)} |
| Clicks | {_fmt(total['clicks'], 0)} |
| Spend | ${_fmt(total['spend'])} |
| Conversions | {_fmt(total['conversions'], 0)} |
| Revenue | ${_fmt(total['revenue'])} |
| Weighted CTR | {_fmt(total['ctr_pct'])}% |
| Weighted CVR | {_fmt(total['cvr_pct'])}% |
| CPA | ${_fmt(total['cpa'])} |
| ROAS | {_fmt(total['roas'])} |

## Channel Comparison

{_markdown_table(channel_summary.sort_values("roas", ascending=False), ["channel", "spend", "conversions", "revenue", "ctr_pct", "cpa", "roas"])}

## Top Qualified Campaign

{_markdown_table(ranked, ["rank", "campaign_name", "channel", "spend", "clicks", "conversions", "cpa", "roas", "rank_score"], 1)}

## Potential Scale Candidates

{_markdown_table(scale_candidates, ["rank", "campaign_name", "channel", "spend", "conversions", "cpa", "roas", "rank_score"])}

## Efficiency Review Candidates

{_markdown_table(review_candidates, ["campaign_name", "channel", "spend", "conversions", "cpa", "roas"])}

## Interpretation Notes

- KPIs are calculated from aggregated numerator and denominator totals, not from simple averages of row-level rates.
- Objective ranking is deterministic and rule-based: traffic favors CPC and CTR, conversion favors CPA and conversion volume, and revenue favors ROAS and revenue.
- Qualification thresholds help reduce overinterpretation of very small samples.
- AI-assisted text, when enabled, receives only deterministic Python-generated metrics and is not allowed to recalculate KPI values.

## Data Quality Notes

{warning_text}
"""


def write_report(markdown: str, output_path: Path) -> None:
    """Write a Markdown report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
