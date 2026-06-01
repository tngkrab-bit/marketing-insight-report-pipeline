import pandas as pd

from marketing_insight_pipeline.metrics import campaign_summary


def test_weighted_ctr_cpa_roas_are_calculated_from_totals() -> None:
    frame = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "campaign_id": "A",
                "campaign_name": "Alpha",
                "channel": "Paid Search",
                "impressions": 100,
                "clicks": 10,
                "spend": 100.0,
                "conversions": 5,
                "revenue": 500.0,
            },
            {
                "date": "2026-01-02",
                "campaign_id": "A",
                "campaign_name": "Alpha",
                "channel": "Paid Search",
                "impressions": 900,
                "clicks": 45,
                "spend": 350.0,
                "conversions": 10,
                "revenue": 850.0,
            },
        ]
    )
    summary = campaign_summary(frame).iloc[0]
    assert summary["ctr_pct"] == 5.5
    assert summary["cpa"] == 30.0
    assert summary["roas"] == 3.0
