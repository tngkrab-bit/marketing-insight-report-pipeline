import pandas as pd

from marketing_insight_pipeline.ranking import efficiency_review_candidates, potential_scale_candidates, rank_campaigns


def ranking_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "campaign_id": "A",
                "campaign_name": "Alpha",
                "channel": "Paid Search",
                "impressions": 1000,
                "clicks": 100,
                "spend": 100.0,
                "conversions": 20,
                "revenue": 600.0,
                "ctr_pct": 10.0,
                "cpc": 1.0,
                "cpa": 5.0,
                "roas": 6.0,
            },
            {
                "campaign_id": "B",
                "campaign_name": "Beta",
                "channel": "Paid Social",
                "impressions": 1000,
                "clicks": 80,
                "spend": 220.0,
                "conversions": 10,
                "revenue": 400.0,
                "ctr_pct": 8.0,
                "cpc": 2.75,
                "cpa": 22.0,
                "roas": 1.82,
            },
            {
                "campaign_id": "C",
                "campaign_name": "Gamma",
                "channel": "Display",
                "impressions": 5000,
                "clicks": 25,
                "spend": 50.0,
                "conversions": 1,
                "revenue": 75.0,
                "ctr_pct": 0.5,
                "cvr_pct": 4.0,
                "cpc": 2.0,
                "cpa": 50.0,
                "roas": 1.5,
            },
        ]
    )


def test_conversion_ranking_prefers_low_cpa_and_volume() -> None:
    ranked = rank_campaigns(ranking_frame(), "conversion", min_spend=0, min_clicks=0, min_conversions=0)
    assert ranked.iloc[0]["campaign_name"] == "Alpha"
    assert ranked.iloc[0]["rank"] == 1


def test_qualification_threshold_filters_small_samples() -> None:
    ranked = rank_campaigns(ranking_frame(), "revenue", min_spend=200, min_clicks=0, min_conversions=0)
    assert list(ranked["campaign_name"]) == ["Beta"]


def test_candidate_selection_is_objective_aware() -> None:
    frame = ranking_frame()
    traffic_ranked = rank_campaigns(frame, "traffic", min_spend=0, min_clicks=0, min_conversions=0)
    conversion_ranked = rank_campaigns(frame, "conversion", min_spend=0, min_clicks=0, min_conversions=0)
    revenue_ranked = rank_campaigns(frame, "revenue", min_spend=0, min_clicks=0, min_conversions=0)

    traffic_scale = potential_scale_candidates(traffic_ranked, "traffic")
    conversion_scale = potential_scale_candidates(conversion_ranked, "conversion")
    revenue_scale = potential_scale_candidates(revenue_ranked, "revenue")
    traffic_review = efficiency_review_candidates(frame, "traffic")
    conversion_review = efficiency_review_candidates(frame, "conversion")
    revenue_review = efficiency_review_candidates(frame, "revenue")

    assert "Alpha" in set(traffic_scale["campaign_name"])
    assert "Alpha" in set(conversion_scale["campaign_name"])
    assert "Alpha" in set(revenue_scale["campaign_name"])
    assert "Gamma" in set(traffic_review["campaign_name"])
    assert "Gamma" in set(conversion_review["campaign_name"])
    assert "Gamma" in set(revenue_review["campaign_name"])
