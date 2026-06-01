import pandas as pd

from marketing_insight_pipeline.reporter import build_report


def test_basic_report_generates_without_api_key() -> None:
    overall = pd.DataFrame(
        [{"impressions": 1000, "clicks": 50, "spend": 100.0, "conversions": 5, "revenue": 400.0, "ctr_pct": 5.0, "cvr_pct": 10.0, "cpa": 20.0, "roas": 4.0}]
    )
    campaigns = pd.DataFrame(
        [{"campaign_name": "Alpha", "channel": "Paid Search", "spend": 100.0, "clicks": 50, "conversions": 5, "revenue": 400.0, "cpa": 20.0, "roas": 4.0, "rank": 1, "rank_score": 1.0}]
    )
    channels = pd.DataFrame(
        [{"channel": "Paid Search", "spend": 100.0, "conversions": 5, "revenue": 400.0, "ctr_pct": 5.0, "cpa": 20.0, "roas": 4.0}]
    )
    report = build_report(
        objective="conversion",
        overall=overall,
        campaign_summary=campaigns,
        channel_summary=channels,
        ranked=campaigns,
        scale_candidates=campaigns,
        review_candidates=campaigns,
        validation={"row_count": 1, "warnings": []},
    )
    assert "Executive Summary" in report
    assert "Alpha ranked first" in report
