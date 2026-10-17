"""A small OpenAI-compatible client for the portable tournament runner."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    content: str
    returned_model: str | None
    usage: dict[str, Any]
    raw: dict[str, Any]
    transport_attempts: list[dict[str, Any]] = field(default_factory=list)


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 180,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        base = base_url.rstrip("/")
        self.url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.extra_headers = extra_headers or {}
        self.last_attempts: list[dict[str, Any]] = []

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        seed: int | None = None,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed

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
                event["status"] = "succeeded"
                message_content = decoded["choices"][0]["message"]["content"]
                if isinstance(message_content, list):
                    message_content = "".join(
                        item.get("text", "")
                        for item in message_content
                        if isinstance(item, dict)
                    )
                return ModelResponse(
                    content=str(message_content),
                    returned_model=decoded.get("model"),
                    usage=decoded.get("usage") or {},
                    raw=decoded,
                    transport_attempts=list(self.last_attempts),
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

