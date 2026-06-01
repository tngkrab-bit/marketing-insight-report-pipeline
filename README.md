# Marketing Insight Report Pipeline

A public-safe Python CLI project for validating marketing campaign data, calculating weighted KPIs, ranking campaigns by objective, and generating a Markdown analytics report.

## Business Problem

Marketing teams often repeat the same manual workflow: validate campaign exports, calculate KPI summaries, compare channels, find promising campaigns, and write an executive-ready report. This project turns that workflow into a deterministic pipeline that can be reviewed, tested, and extended without exposing confidential campaign data.

## Key Features

- CSV schema and data quality validation
- Weighted KPI calculation from aggregated numerators and denominators
- Campaign, channel, and monthly performance summaries
- Objective-based campaign ranking for traffic, conversion, or revenue
- Rule-based scale and efficiency review candidate lists
- Markdown report generation without requiring an API key
- Optional OpenAI-assisted executive summary
- pytest coverage for validation, metrics, ranking, reporting, and disabled AI behavior

## Why Weighted KPI Calculation Matters

CTR, CVR, CPC, CPA, ROAS, and similar KPIs should be calculated from aggregated totals at the reporting grain. For example, campaign-level CTR is total clicks divided by total impressions, not the simple average of daily CTR values. This avoids giving small rows the same influence as high-volume rows.

## Project Structure

```text
marketing-insight-report-pipeline/
├── .github/
│   └── workflows/
│       └── tests.yml
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── LICENSE
├── CONTRIBUTING.md
├── AGENTS.md
├── src/
│   └── marketing_insight_pipeline/
│       ├── __init__.py
│       ├── cli.py
│       ├── validator.py
│       ├── metrics.py
│       ├── ranking.py
│       ├── reporter.py
│       └── ai_insights.py
├── data/
│   └── sample_campaign_data.csv
├── outputs/
│   └── example_analytics_report.md
└── tests/
    ├── test_ai_insights.py
    ├── test_validator.py
    ├── test_metrics.py
    ├── test_ranking.py
    └── test_reporter.py
```

## Installation

```bash
python -m pip install -e ".[dev]"
```

To use the optional OpenAI summary feature:

```bash
python -m pip install -e ".[dev,ai]"
```

## Demo Run

```bash
python -m marketing_insight_pipeline.cli --demo --output-dir outputs
```

## Analyze Your Own CSV

Input CSV files must include these columns:

```text
date, campaign_id, campaign_name, channel, impressions, clicks, spend, conversions, revenue
```

Run:

```bash
python -m marketing_insight_pipeline.cli \
  --input data/sample_campaign_data.csv \
  --output-dir outputs \
  --objective conversion
```

Available objectives are `traffic`, `conversion`, and `revenue`.

Qualification thresholds can be adjusted:

```bash
python -m marketing_insight_pipeline.cli \
  --demo \
  --output-dir outputs \
  --objective revenue \
  --min-spend 500 \
  --min-clicks 50 \
  --min-conversions 5
```

## Optional OpenAI API Summary

The optional AI-assisted summary uses the official OpenAI Python SDK with the Responses API pattern:

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(model="gpt-5.4-mini", input="...")
print(response.output_text)
```

Set environment variables before running:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-5.4-mini"
```

Then run:

```bash
python -m marketing_insight_pipeline.cli \
  --demo \
  --output-dir outputs \
  --objective conversion \
  --enable-ai-summary
```

The AI feature receives only deterministic Python-generated metrics and ranking outputs. It must not recalculate or invent KPI values.

## Candidate Selection Rules

Potential scale and efficiency review candidates are objective-aware:

- `traffic` scale candidates have above-median CTR and at-or-below-median CPC. Traffic review candidates have bottom-quartile CTR or top-quartile CPC.
- `conversion` scale candidates have above-median conversion volume and at-or-below-median CPA. Conversion review candidates have bottom-quartile CVR or top-quartile CPA.
- `revenue` scale candidates have above-median ROAS and above-median revenue. Revenue review candidates have bottom-quartile ROAS or bottom-quartile revenue.

These rules are deterministic and are intended to guide follow-up analysis, not replace business judgment.

## API Key Security

Never commit API keys, real account identifiers, client names, customer data, or confidential performance data. `.env.example` includes only variable names. Keep real secrets in your local environment or a secure secret manager.

## Generated Outputs

- `outputs/data_quality_report.json`
- `outputs/campaign_performance_summary.csv`
- `outputs/channel_performance_summary.csv`
- `outputs/monthly_performance_trend.csv`
- `outputs/example_analytics_report.md`

Only `outputs/example_analytics_report.md` is kept in the repository as an example artifact. Generated CSV and JSON files are ignored and should be regenerated locally.

## Public-Safe Data Notice

The sample data and generated example outputs use synthetic campaign names and public-safe values only. They are not based on real client, customer, or account data.

## Roadmap

- Add additional attribution-aware warning rules
- Support configurable ranking weights
- Add chart image exports for reports
- Add richer schema documentation for downstream BI tools

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for issue, pull request, test, and data safety guidelines.

## License

MIT License. See [LICENSE](LICENSE).
