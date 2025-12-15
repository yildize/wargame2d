"""Lightweight helper for OpenRouter model metadata."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterable


def fetch_models(base_url: str = "https://openrouter.ai/api/v1") -> list[dict[str, Any]]:
    """
    Fetch the list of models from OpenRouter.

    Args:
        base_url: Override for testing.

    Returns:
        List of model dicts.

    Raises:
        RuntimeError: For HTTP/parse errors.
    """
    headers = {"Accept": "application/json"}

    req = urllib.request.Request(f"{base_url.rstrip('/')}/models", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310 (external HTTP call expected)
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenRouter returned HTTP {exc.code}: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch models: {exc}") from exc

    data = payload.get("data")
    if not isinstance(data, Iterable):
        raise RuntimeError("OpenRouter response missing 'data' list")
    return list(data)


def find_model_by_id(
    model_id: str,
    base_url: str = "https://openrouter.ai/api/v1",
    pretty: bool = False,
) -> dict[str, Any] | str | None:
    """
    Return a single model record matching the id (pretty JSON string if requested).

    Args:
        model_id: Exact model id to locate (e.g., \"qwen/qwen3-coder:exacto\").
        pretty: If True, return a JSON-formatted string; otherwise return the raw dict.
    """
    models = fetch_models(base_url=base_url)
    for model in models:
        if model.get("id") == model_id:
            return json.dumps(model, indent=2, sort_keys=True) if pretty else model
    return None


if __name__ == "__main__":
    # Simple demo: fetch and display one model by id.
    MODEL_ID = "qwen/qwen3-vl-30b-a3b-thinking"
    result = find_model_by_id(MODEL_ID, pretty=True)
    if result:
        print(result)
    else:
        print(f"model not found: {MODEL_ID}")
