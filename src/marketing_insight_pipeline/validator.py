"""Input schema and data quality validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "date",
    "campaign_id",
    "campaign_name",
    "channel",
    "impressions",
    "clicks",
    "spend",
    "conversions",
    "revenue",
]

NUMERIC_COLUMNS = ["impressions", "clicks", "spend", "conversions", "revenue"]


@dataclass
class ValidationResult:
    """Structured validation output."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    row_count: int = 0

    def to_dict(self) -> dict[str, object]:
        """Return JSON-serializable validation details."""
        return asdict(self)


class DataValidationError(ValueError):
    """Raised when input data fails required validation."""


def clean_campaign_data(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with parsed dates and numeric metric columns."""
    cleaned = data.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    return cleaned


def validate_campaign_data(data: pd.DataFrame) -> ValidationResult:
    """Validate campaign data and distinguish blocking errors from warnings."""
    errors: list[str] = []
    warnings: list[str] = []

    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return ValidationResult(False, errors, warnings, len(data))

    cleaned = clean_campaign_data(data)
    if cleaned["date"].isna().any():
        bad_count = int(cleaned["date"].isna().sum())
        errors.append(f"Invalid date values found in {bad_count} row(s).")

    for column in NUMERIC_COLUMNS:
        numeric = cleaned[column]
        if numeric.isna().any():
            errors.append(f"Column '{column}' contains blank or non-numeric values.")
        if (numeric < 0).any():
            errors.append(f"Column '{column}' contains negative values.")

    if (cleaned["clicks"] > cleaned["impressions"]).any():
        errors.append("Clicks cannot exceed impressions.")

    duplicate_count = int(data.duplicated().sum())
    if duplicate_count:
        errors.append(f"Exact duplicate rows found: {duplicate_count}.")

    conversion_over_clicks = cleaned["conversions"] > cleaned["clicks"]
    if conversion_over_clicks.any():
        warnings.append(
            "Conversions exceed clicks in "
            f"{int(conversion_over_clicks.sum())} row(s); this may reflect view-through conversion "
            "or cross-session attribution."
        )

    return ValidationResult(not errors, errors, warnings, len(data))


def validate_and_clean(data: pd.DataFrame, report_path: Path) -> tuple[ValidationResult, pd.DataFrame]:
    """Validate data, write a quality report, and return cleaned data on success."""
    result = validate_or_raise(data, report_path)
    return result, clean_campaign_data(data)


def validate_or_raise(data: pd.DataFrame, report_path: Path) -> ValidationResult:
    """Validate data, write a JSON quality report, and raise on blocking errors."""
    result = validate_campaign_data(data)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    for warning in result.warnings:
        LOGGER.warning(warning)
    for error in result.errors:
        LOGGER.error(error)

    if not result.valid:
        raise DataValidationError(f"Input validation failed. See {report_path}")
    LOGGER.info("Data validation passed for %s row(s).", result.row_count)
    return result
