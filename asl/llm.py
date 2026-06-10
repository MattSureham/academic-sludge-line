"""Small LLM adapter with an offline fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .templates import SYSTEM_POLICY


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str


class LLMClient:
    """Generate text through OpenAI Responses API or a caller-supplied fallback."""

    def __init__(self, offline: bool = False, model: str | None = None) -> None:
        self.offline = offline
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("ASL_MODEL", "gpt-4.1-mini")

    @property
    def available(self) -> bool:
        return bool(self.api_key) and not self.offline

    def generate(self, prompt: str, fallback: str) -> LLMResult:
        if not self.available:
            return LLMResult(text=fallback, provider="offline", model="template")

        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": SYSTEM_POLICY},
                {"role": "user", "content": prompt},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            note = f"\n\n<!-- LLM call failed; offline fallback used: {type(exc).__name__}: {exc} -->"
            return LLMResult(text=fallback + note, provider="offline-after-error", model="template")

        return LLMResult(text=_extract_text(body) or fallback, provider="openai", model=self.model)


def _extract_text(body: dict) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]

    chunks: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()

