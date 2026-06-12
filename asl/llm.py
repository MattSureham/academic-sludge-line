"""Small LLM adapter with an offline fallback."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .catalog import PROVIDERS
from .local_providers import cc_switch_settings_for_ref
from .templates import SYSTEM_POLICY


ROLE_DEFAULT = "default"
ROLE_PLAN = "plan"
ROLE_DRAFT = "draft"
ROLE_REVIEW = "review"
ROLE_REVISION = "revision"
ROLE_SCORE = "score"

MODEL_ROLES = (ROLE_DEFAULT, ROLE_PLAN, ROLE_DRAFT, ROLE_REVIEW, ROLE_REVISION, ROLE_SCORE)
LOCAL_AGENT_TIMEOUT_SECONDS = int(os.getenv("ASL_LOCAL_AGENT_TIMEOUT", "300"))
LOCAL_AGENT_DEFAULT_MODEL_NAMES = {"", "default", "configured", "local"}
_GENERATION_ERRORS = (
    urllib.error.URLError,
    TimeoutError,
    json.JSONDecodeError,
    KeyError,
    TypeError,
    ValueError,
    OSError,
    subprocess.TimeoutExpired,
)


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    attempts: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    endpoint: str | None = None

    @property
    def label(self) -> str:
        suffix = f"@{self.endpoint}" if self.endpoint else ""
        return f"{self.provider}:{self.model}{suffix}"


@dataclass(frozen=True)
class ModelRoutes:
    raw: dict[str, str]
    routes: dict[str, tuple[ModelSpec, ...]]

    @classmethod
    def build(cls, default_model: str | None = None, routes: Mapping[str, str] | None = None) -> "ModelRoutes":
        raw: dict[str, str] = {}
        default = default_model or os.getenv("ASL_MODEL") or PROVIDERS["openai"].default_model
        raw[ROLE_DEFAULT] = default
        for role, value in (routes or {}).items():
            if role in MODEL_ROLES and value:
                raw[role] = value

        parsed = {role: parse_model_chain(value) for role, value in raw.items()}
        return cls(raw=raw, routes=parsed)

    def with_overrides(self, routes: Mapping[str, str]) -> "ModelRoutes":
        raw = dict(self.raw)
        for role, value in routes.items():
            if role in MODEL_ROLES and value:
                raw[role] = value
        return ModelRoutes.build(routes=raw)

    def for_role(self, role: str) -> tuple[ModelSpec, ...]:
        return self.routes.get(role) or self.routes[ROLE_DEFAULT]

    def metadata(self) -> dict[str, list[str]]:
        return {role: [spec.label for spec in specs] for role, specs in self.routes.items()}


class LLMClient:
    """Generate text through role-specific model routes with an offline fallback."""

    def __init__(
        self,
        offline: bool = False,
        model: str | None = None,
        model_routes: Mapping[str, str] | None = None,
    ) -> None:
        self.offline = offline
        self.routes = ModelRoutes.build(default_model=model, routes=model_routes)
        default = self.routes.for_role(ROLE_DEFAULT)[0]
        self.api_key = _api_key_for(default)
        self.model = default.model

    @property
    def available(self) -> bool:
        if self.offline:
            return False
        return any(_spec_available(spec) for spec in self.routes.for_role(ROLE_DEFAULT))

    def with_model_routes(self, routes: Mapping[str, str]) -> "LLMClient":
        return LLMClient(offline=self.offline, model_routes=self.routes.with_overrides(routes).raw)

    def route_metadata(self) -> dict[str, list[str]]:
        return self.routes.metadata()

    def generate(self, prompt: str, fallback: str, role: str = ROLE_DEFAULT) -> LLMResult:
        if not self.available:
            if self.offline:
                return LLMResult(text=fallback, provider="offline", model="template")

        attempts: list[str] = []
        for spec in self.routes.for_role(role):
            if spec.provider in {"offline", "template"}:
                return LLMResult(text=fallback, provider="offline", model="template", attempts=tuple(attempts))

            if not _spec_available(spec):
                attempts.append(f"{spec.label}: missing credentials or endpoint")
                continue

            try:
                text = self._generate_with_spec(spec, prompt)
            except _GENERATION_ERRORS as exc:
                attempts.append(f"{spec.label}: {type(exc).__name__}: {exc}")
                continue

            if text.strip():
                return LLMResult(text=text, provider=spec.provider, model=spec.model, attempts=tuple(attempts))
            attempts.append(f"{spec.label}: empty response")

        if attempts:
            missing_only = all("missing credentials or endpoint" in attempt for attempt in attempts)
            if missing_only:
                return LLMResult(text=fallback, provider="offline", model="template", attempts=tuple(attempts))
            joined = "; ".join(attempts)
            note = f"\n\n<!-- LLM call failed; offline fallback used: {joined} -->"
            return LLMResult(
                text=fallback + note,
                provider="offline-after-error",
                model="template",
                attempts=tuple(attempts),
            )

        return LLMResult(text=fallback, provider="offline", model="template")

    def generate_all(self, prompt: str, fallback: str, role: str) -> list[LLMResult]:
        if self.offline:
            return [LLMResult(text=fallback, provider="offline", model="template")]

        results: list[LLMResult] = []
        for spec in self.routes.for_role(role):
            results.append(self.generate_one(prompt, fallback, spec))
        return results or [LLMResult(text=fallback, provider="offline", model="template")]

    def generate_one(self, prompt: str, fallback: str, spec: ModelSpec) -> LLMResult:
        if spec.provider in {"offline", "template"}:
            return LLMResult(text=fallback, provider="offline", model="template")
        if not _spec_available(spec):
            attempt = f"{spec.label}: missing credentials or endpoint"
            return LLMResult(text=fallback, provider="offline", model="template", attempts=(attempt,))

        try:
            text = self._generate_with_spec(spec, prompt)
        except _GENERATION_ERRORS as exc:
            attempt = f"{spec.label}: {type(exc).__name__}: {exc}"
            note = f"\n\n<!-- LLM call failed; offline fallback used: {attempt} -->"
            return LLMResult(
                text=fallback + note,
                provider="offline-after-error",
                model="template",
                attempts=(attempt,),
            )

        if text.strip():
            return LLMResult(text=text, provider=spec.provider, model=spec.model)
        attempt = f"{spec.label}: empty response"
        note = f"\n\n<!-- LLM call failed; offline fallback used: {attempt} -->"
        return LLMResult(
            text=fallback + note,
            provider="offline-after-error",
            model="template",
            attempts=(attempt,),
        )

    def _generate_with_spec(self, spec: ModelSpec, prompt: str) -> str:
        if spec.provider == "openai":
            return _call_openai_responses(spec, prompt)
        if spec.provider == "anthropic":
            return _call_anthropic(spec, prompt)
        if spec.provider == "gemini":
            return _call_gemini(spec, prompt)
        if spec.provider == "ollama":
            return _call_ollama(spec, prompt)
        if spec.provider == "minimax":
            return _call_minimax(spec, prompt)
        if spec.provider in {"deepseek", "qwen", "kimi", "kimi-code", "openai-compat"}:
            return _call_chat_completions(spec, prompt)
        if spec.provider == "claude-code":
            return _call_claude_code(spec, prompt)
        if spec.provider == "codex":
            return _call_codex_cli(spec, prompt)
        raise ValueError(f"unsupported provider: {spec.provider}")


def parse_model_chain(value: str) -> tuple[ModelSpec, ...]:
    specs = []
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        endpoint = None
        if "@" in item:
            item, endpoint = item.split("@", 1)
            endpoint = endpoint.strip() or None
        if item in {"offline", "template"}:
            specs.append(ModelSpec(provider="offline", model="template"))
            continue
        if ":" in item:
            provider, model = item.split(":", 1)
        else:
            provider, model = os.getenv("ASL_PROVIDER", "openai"), item
        specs.append(ModelSpec(provider=provider.strip().lower(), model=model.strip(), endpoint=endpoint))

    if not specs:
        raise ValueError("model route must include at least one model")
    return tuple(specs)


def _call_openai_responses(spec: ModelSpec, prompt: str) -> str:
    payload = {
        "model": spec.model,
        "input": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": prompt},
        ],
    }
    body = _post_json(
        _endpoint_for(spec, "/responses"),
        payload,
        {"Authorization": f"Bearer {_api_key_for(spec)}"},
    )
    return _extract_openai_responses_text(body)


def _call_chat_completions(spec: ModelSpec, prompt: str) -> str:
    payload = {
        "model": spec.model,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {}
    api_key = _api_key_for(spec)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = _post_json(_endpoint_for(spec, "/chat/completions"), payload, headers)
    return body["choices"][0]["message"]["content"].strip()


def _call_anthropic(spec: ModelSpec, prompt: str) -> str:
    payload = {
        "model": spec.model,
        "max_tokens": 4096,
        "system": SYSTEM_POLICY,
        "messages": [{"role": "user", "content": prompt}],
    }
    body = _post_json(
        _endpoint_for(spec, "/messages"),
        payload,
        {
            "x-api-key": _api_key_for(spec),
            "anthropic-version": "2023-06-01",
        },
    )
    chunks = []
    for item in body.get("content", []):
        if item.get("type") == "text" and isinstance(item.get("text"), str):
            chunks.append(item["text"])
    return "\n".join(chunks).strip()


def _call_gemini(spec: ModelSpec, prompt: str) -> str:
    base = _endpoint_for(spec, f"/models/{spec.model}:generateContent")
    url = f"{base}?key={_api_key_for(spec)}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_POLICY}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    body = _post_json(url, payload, {})
    chunks = []
    for candidate in body.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if isinstance(part.get("text"), str):
                chunks.append(part["text"])
    return "\n".join(chunks).strip()


def _call_ollama(spec: ModelSpec, prompt: str) -> str:
    payload = {
        "model": spec.model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": prompt},
        ],
    }
    body = _post_json(_endpoint_for(spec, "/api/chat"), payload, {})
    return body.get("message", {}).get("content", "").strip()


def _call_minimax(spec: ModelSpec, prompt: str) -> str:
    payload = {
        "model": spec.model,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 4096,
    }
    body = _post_json(
        _endpoint_for(spec, "/text/chatcompletion_v2"),
        payload,
        {"Authorization": f"Bearer {_api_key_for(spec)}"},
    )
    return body["choices"][0]["message"]["content"].strip()


def _call_claude_code(spec: ModelSpec, prompt: str) -> str:
    command = os.getenv("ASL_CLAUDE_CODE_COMMAND", "claude")
    args = [
        command,
        "-p",
        "--output-format",
        "text",
        "--no-session-persistence",
        "--tools",
        "",
    ]
    if spec.model not in LOCAL_AGENT_DEFAULT_MODEL_NAMES:
        args.extend(["--model", spec.model])

    settings = cc_switch_settings_for_ref(spec.endpoint)
    if settings:
        args.extend(["--settings", json.dumps(settings)])

    completed = subprocess.run(
        args,
        input=_agent_prompt(prompt),
        capture_output=True,
        text=True,
        timeout=LOCAL_AGENT_TIMEOUT_SECONDS,
        cwd=Path.cwd(),
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(_subprocess_error("claude-code", completed))
    return completed.stdout.strip()


def _call_codex_cli(spec: ModelSpec, prompt: str) -> str:
    command = os.getenv("ASL_CODEX_COMMAND", "codex")
    output_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="asl-codex-", suffix=".txt", delete=False) as output:
            output_path = Path(output.name)

        args = [
            command,
            "exec",
            "--cd",
            str(Path.cwd()),
            "--sandbox",
            "read-only",
            "--ask-for-approval",
            "never",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--output-last-message",
            str(output_path),
        ]
        if spec.endpoint and not spec.endpoint.startswith("cc-switch:"):
            args.extend(["--profile", spec.endpoint])
        if spec.model not in LOCAL_AGENT_DEFAULT_MODEL_NAMES:
            args.extend(["--model", spec.model])
        args.append("-")

        completed = subprocess.run(
            args,
            input=_agent_prompt(prompt),
            capture_output=True,
            text=True,
            timeout=LOCAL_AGENT_TIMEOUT_SECONDS,
            cwd=Path.cwd(),
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError(_subprocess_error("codex", completed))

        if output_path.exists():
            output_text = output_path.read_text(encoding="utf-8").strip()
            if output_text:
                return output_text
        return completed.stdout.strip()
    finally:
        if output_path and output_path.exists():
            output_path.unlink()


def _agent_prompt(prompt: str) -> str:
    return f"{SYSTEM_POLICY}\n\n{prompt}"


def _subprocess_error(provider: str, completed: subprocess.CompletedProcess[str]) -> str:
    stderr = (completed.stderr or "").strip()
    stdout = (completed.stdout or "").strip()
    detail = stderr or stdout or f"exit code {completed.returncode}"
    return f"{provider} failed: {detail[:1000]}"


def _extract_openai_responses_text(body: dict) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]

    chunks: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _endpoint_for(spec: ModelSpec, path: str) -> str:
    endpoint = spec.endpoint or _env_endpoint_for(spec.provider) or _default_endpoint_for(spec.provider)
    endpoint = endpoint.rstrip("/")
    if endpoint.endswith(path):
        return endpoint
    return f"{endpoint}{path}"


def _default_endpoint_for(provider: str) -> str:
    entry = PROVIDERS.get(provider)
    endpoint = entry.default_endpoint if entry else ""
    if not endpoint:
        raise ValueError(f"endpoint is required for provider: {provider}")
    return endpoint


def _env_endpoint_for(provider: str) -> str:
    env_name = f"ASL_{_provider_env_prefix(provider)}_ENDPOINT"
    return os.getenv(env_name, "")


def _api_key_for(spec: ModelSpec) -> str:
    provider = spec.provider
    prefix = _provider_env_prefix(provider)
    explicit = os.getenv(f"ASL_{prefix}_API_KEY", "")
    if explicit:
        return explicit

    entry = PROVIDERS.get(provider)
    for name in entry.api_key_envs if entry else ():
        value = os.getenv(name, "")
        if value:
            return value
    return ""


def _provider_env_prefix(provider: str) -> str:
    return provider.upper().replace("-", "_")


def _spec_available(spec: ModelSpec) -> bool:
    if spec.provider in {"offline", "template", "ollama"}:
        return True
    if spec.provider == "claude-code":
        return bool(shutil.which(os.getenv("ASL_CLAUDE_CODE_COMMAND", "claude")))
    if spec.provider == "codex":
        return bool(shutil.which(os.getenv("ASL_CODEX_COMMAND", "codex")))
    if spec.provider == "openai-compat":
        return bool(spec.endpoint or _env_endpoint_for(spec.provider) or _default_endpoint_for(spec.provider))
    return bool(_api_key_for(spec))
