import sys
import types

import pandas as pd

from marketing_insight_pipeline.ai_insights import generate_ai_summary
from marketing_insight_pipeline.reporter import build_report


def test_ai_summary_does_not_call_api_when_disabled_by_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert generate_ai_summary({"overall": []}) is None


def test_ai_summary_returns_none_when_api_call_fails(monkeypatch, caplog) -> None:
    class FailingResponses:
        def create(self, **kwargs):
            raise RuntimeError("simulated outage")

    class FailingClient:
        def __init__(self, api_key):
            self.responses = FailingResponses()

    fake_openai = types.SimpleNamespace(OpenAI=FailingClient)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    assert generate_ai_summary({"overall": []}) is None
    assert "falling back to deterministic report" in caplog.text


def test_deterministic_report_is_generated_after_ai_failure(monkeypatch) -> None:
    class FailingResponses:
        def create(self, **kwargs):
            raise RuntimeError("simulated outage")

    class FailingClient:
        def __init__(self, api_key):
            self.responses = FailingResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FailingClient))
    ai_summary = generate_ai_summary({"overall": []})

    overall = pd.DataFrame(
        [
            {
                "impressions": 1000,
                "clicks": 50,
                "spend": 100.0,
                "conversions": 5,
                "revenue": 400.0,
                "ctr_pct": 5.0,
                "cvr_pct": 10.0,
                "cpa": 20.0,
                "roas": 4.0,
            }
        ]
    )
    campaigns = pd.DataFrame(
        [
            {
                "campaign_name": "Alpha",
                "channel": "Paid Search",
                "spend": 100.0,
                "clicks": 50,
                "conversions": 5,
                "revenue": 400.0,
                "cpa": 20.0,
                "roas": 4.0,
                "rank": 1,
                "rank_score": 1.0,
            }
        ]
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
        ai_summary=ai_summary,
    )

    assert ai_summary is None
    assert "The analysis covers 1,000 impressions" in report
