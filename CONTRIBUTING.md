# Contributing

Thank you for improving this project.

## Issues and Pull Requests

Open an issue for bugs, documentation gaps, or proposed enhancements. Pull requests should describe the business question being addressed, the implementation approach, and any changes to generated outputs.

## Code Style and Tests

Use clear type hints, docstrings where they clarify behavior, and explicit error handling. Run the full test suite before submitting:

```bash
python -m pytest
```

For local development, install the package with development dependencies:

```bash
python -m pip install -e ".[dev,ai]"
```

## Data Safety

Do not upload real customer data, client names, account identifiers, personally identifiable information, or confidential campaign details. Use synthetic data for examples and tests.

## Suggesting KPIs or Features

When proposing a new KPI or ranking rule, include the formula, aggregation level, expected edge cases, and at least one test that proves deterministic behavior.
