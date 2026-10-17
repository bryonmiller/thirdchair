"""A small OpenAI-compatible client for the portable tournament runner."""

from __future__ import annotations

import copy
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit


def is_openrouter(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    return host == "openrouter.ai" or host.endswith(".openrouter.ai")


def chat_payload(
    *, model: str, messages: list[dict[str, str]], temperature: float | None,
    max_tokens: int, seed: int | None, provider: dict[str, Any] | None = None,
    reasoning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One representation for the HTTP body and its research journal entry."""
    payload: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:
        payload["temperature"] = temperature
    if seed is not None:
        payload["seed"] = seed
    if provider is not None:
        payload["provider"] = provider
    if reasoning is not None:
        payload["reasoning"] = reasoning
    return copy.deepcopy(payload)


def response_provider(raw: dict[str, Any]) -> str | None:
    """Read a reported provider, never infer one from the requested model name."""
    provider = raw.get("provider")
    if isinstance(provider, str) and provider.strip():
        return provider
    metadata = raw.get("openrouter_metadata") or {}
    if not isinstance(metadata, dict):
        return None
    endpoints = metadata.get("endpoints") or {}
    if not isinstance(endpoints, dict):
        return None
    available = endpoints.get("available") or []
    if not isinstance(available, list):
        return None
    selected = {item["provider"] for item in available
                if isinstance(item, dict) and item.get("selected") is True
                and isinstance(item.get("provider"), str) and item["provider"].strip()}
    return next(iter(selected)) if len(selected) == 1 else None


@dataclass
class ModelResponse:
    content: str
    returned_model: str | None
    usage: dict[str, Any]
    raw: dict[str, Any]
    transport_attempts: list[dict[str, Any]] = field(default_factory=list)
    returned_provider: str | None = None
    finish_reason: str | None = None


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 180,
        extra_headers: dict[str, str] | None = None,
        provider: dict[str, Any] | None = None,
        reasoning: dict[str, Any] | None = None,
    ) -> None:
        base = base_url.rstrip("/")
        self.url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.extra_headers = dict(extra_headers or {})
        self.provider = copy.deepcopy(provider)
        self.reasoning = copy.deepcopy(reasoning)
        self.provider_metadata_required = is_openrouter(self.url)
        if self.provider_metadata_required and not any(
            name.lower() == "x-openrouter-metadata" for name in self.extra_headers
        ):
            self.extra_headers["X-OpenRouter-Metadata"] = "enabled"
        self.last_attempts: list[dict[str, Any]] = []

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = 0.2,
        max_tokens: int = 1200,
        seed: int | None = None,
    ) -> ModelResponse:
        payload = chat_payload(model=self.model, messages=messages, temperature=temperature,
                               max_tokens=max_tokens, seed=seed,
                               provider=self.provider, reasoning=self.reasoning)

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        self.last_attempts = []
        for attempt in range(4):
            event: dict[str, Any] = {"attempt": attempt + 1}
            self.last_attempts.append(event)
            request = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    decoded = json.loads(response.read().decode("utf-8"))
                choice = decoded["choices"][0]
                message_content = choice["message"].get("content")
                if isinstance(message_content, list):
                    message_content = "".join(
                        item.get("text", "")
                        for item in message_content
                        if isinstance(item, dict)
                    )
                if message_content is None:
                    message_content = ""
                if not isinstance(message_content, str):
                    raise TypeError("Invalid message content")
                event["status"] = "succeeded"
                return ModelResponse(
                    content=message_content,
                    returned_model=decoded.get("model"),
                    usage=decoded.get("usage") or {},
                    raw=decoded,
                    transport_attempts=list(self.last_attempts),
                    returned_provider=response_provider(decoded),
                    finish_reason=choice.get("finish_reason"),
                )
            except urllib.error.HTTPError as exc:
                event.update(status="http_error", http_status=exc.code)
                if exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                    # Error bodies/URLs can echo credentials. Keep the status, not the body.
                    raise RuntimeError(f"Model request failed with HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                event.update(status="transport_error", error_type=type(exc).__name__)
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                event.update(status="invalid_provider_response", error_type=type(exc).__name__)
                raise RuntimeError("Invalid provider response envelope") from exc
            if attempt < 3:
                time.sleep(2**attempt)
        raise RuntimeError("Model request failed after four transport attempts")

