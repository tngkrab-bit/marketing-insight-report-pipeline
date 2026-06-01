"""Optional AI-assisted report summary using deterministic Python inputs."""

from __future__ import annotations

import logging
import os
from typing import Any

LOGGER = logging.getLogger(__name__)


def generate_ai_summary(context: dict[str, Any], *, model: str | None = None) -> str | None:
    """Generate an executive summary only when explicitly enabled by the CLI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        LOGGER.info("OPENAI_API_KEY is not set; skipping AI-assisted summary.")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        LOGGER.warning("The openai package is not installed; skipping AI-assisted summary.")
        return None

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    prompt = (
        "Write a concise executive summary for marketing leadership. "
        "Use only the supplied deterministic metrics and ranking outputs. "
        "Do not recalculate, invent, or modify KPI values.\n\n"
        f"Context:\n{context}"
    )
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=selected_model, input=prompt)
        return response.output_text.strip()
    except Exception as exc:
        LOGGER.warning("OpenAI summary generation failed; falling back to deterministic report: %s", exc)
        return None
