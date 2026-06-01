import pandas as pd
import pytest

from marketing_insight_pipeline.metrics import campaign_summary
from marketing_insight_pipeline.validator import DataValidationError, validate_and_clean, validate_campaign_data, validate_or_raise


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "campaign_id": "CMP-1",
                "campaign_name": "Example",
                "channel": "Paid Search",
                "impressions": 100,
                "clicks": 10,
                "spend": 20.0,
                "conversions": 2,
                "revenue": 100.0,
            }
        ]
    )


def test_missing_required_column_errors() -> None:
    frame = valid_frame().drop(columns=["revenue"])
    result = validate_campaign_data(frame)
    assert not result.valid
    assert "Missing required columns: revenue" in result.errors[0]


def test_negative_metric_errors() -> None:
    frame = valid_frame()
    frame.loc[0, "spend"] = -1
    result = validate_campaign_data(frame)
    assert not result.valid
    assert any("negative" in error for error in result.errors)


def test_clicks_over_impressions_errors() -> None:
    frame = valid_frame()
    frame.loc[0, "clicks"] = 101
    result = validate_campaign_data(frame)
    assert not result.valid
    assert "Clicks cannot exceed impressions." in result.errors


def test_conversions_over_clicks_warns() -> None:
    frame = valid_frame()
    frame.loc[0, "conversions"] = 11
    result = validate_campaign_data(frame)
    assert result.valid
    assert result.warnings


def test_validate_or_raise_writes_quality_report(tmp_path) -> None:
    frame = valid_frame()
    frame.loc[0, "clicks"] = 101
    with pytest.raises(DataValidationError):
        validate_or_raise(frame, tmp_path / "data_quality_report.json")
    assert (tmp_path / "data_quality_report.json").exists()


def test_string_numeric_values_are_cleaned_before_analysis(tmp_path) -> None:
    frame = valid_frame().astype(
        {
            "impressions": "string",
            "clicks": "string",
            "spend": "string",
            "conversions": "string",
            "revenue": "string",
        }
    )
    validation, cleaned = validate_and_clean(frame, tmp_path / "data_quality_report.json")

    assert validation.valid
    assert cleaned["date"].dtype.kind == "M"
    assert cleaned["impressions"].dtype.kind in {"i", "u", "f"}
    summary = campaign_summary(cleaned).iloc[0]
    assert summary["ctr_pct"] == 10.0
    assert summary["roas"] == 5.0
