"""Command-line interface for the marketing insight pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from marketing_insight_pipeline.ai_insights import generate_ai_summary
from marketing_insight_pipeline.metrics import campaign_summary, channel_summary, monthly_trend, overall_summary
from marketing_insight_pipeline.ranking import efficiency_review_candidates, potential_scale_candidates, rank_campaigns
from marketing_insight_pipeline.reporter import build_report, write_report
from marketing_insight_pipeline.validator import validate_and_clean

LOGGER = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate marketing performance analytics reports.")
    parser.add_argument("--input", type=Path, help="Input campaign CSV path.")
    parser.add_argument("--demo", action="store_true", help="Use bundled sample campaign data.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Directory for generated outputs.")
    parser.add_argument("--objective", choices=["traffic", "conversion", "revenue"], default="conversion")
    parser.add_argument("--min-spend", type=float, default=100.0)
    parser.add_argument("--min-clicks", type=int, default=25)
    parser.add_argument("--min-conversions", type=int, default=1)
    parser.add_argument("--enable-ai-summary", action="store_true", help="Use OpenAI API for optional summary text.")
    parser.add_argument("--openai-model", default=None, help="OpenAI model override for AI summary.")
    return parser.parse_args(argv)


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "sample_campaign_data.csv"


def run(args: argparse.Namespace) -> dict[str, Path]:
    """Run the complete analytics pipeline."""
    if args.demo:
        input_path = _sample_path()
    elif args.input:
        input_path = args.input
    else:
        raise SystemExit("Provide --input PATH or use --demo.")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_data = pd.read_csv(input_path)
    validation, data = validate_and_clean(raw_data, output_dir / "data_quality_report.json")

    campaigns = campaign_summary(data)
    channels = channel_summary(data)
    monthly = monthly_trend(data)
    overall = overall_summary(data)
    ranked = rank_campaigns(
        campaigns,
        args.objective,
        min_spend=args.min_spend,
        min_clicks=args.min_clicks,
        min_conversions=args.min_conversions,
    )
    scale = potential_scale_candidates(ranked, args.objective)
    review = efficiency_review_candidates(campaigns, args.objective)

    campaign_path = output_dir / "campaign_performance_summary.csv"
    channel_path = output_dir / "channel_performance_summary.csv"
    monthly_path = output_dir / "monthly_performance_trend.csv"
    report_path = output_dir / "example_analytics_report.md"

    campaigns.to_csv(campaign_path, index=False)
    channels.to_csv(channel_path, index=False)
    monthly.to_csv(monthly_path, index=False)

    ai_summary = None
    if args.enable_ai_summary:
        ai_summary = generate_ai_summary(
            {
                "objective": args.objective,
                "overall": overall.to_dict(orient="records"),
                "top_campaigns": ranked.head(3).to_dict(orient="records"),
                "scale_candidates": scale.to_dict(orient="records"),
                "review_candidates": review.to_dict(orient="records"),
            },
            model=args.openai_model,
        )

    markdown = build_report(
        objective=args.objective,
        overall=overall,
        campaign_summary=campaigns,
        channel_summary=channels,
        ranked=ranked,
        scale_candidates=scale,
        review_candidates=review,
        validation=validation.to_dict(),
        ai_summary=ai_summary,
    )
    write_report(markdown, report_path)

    LOGGER.info("Wrote report to %s", report_path)
    return {
        "campaign_summary": campaign_path,
        "channel_summary": channel_path,
        "monthly_trend": monthly_path,
        "quality_report": output_dir / "data_quality_report.json",
        "markdown_report": report_path,
    }


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    outputs = run(parse_args(argv))
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
