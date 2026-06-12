"""Provider and model catalog aligned with the adjacent teamagents config."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .local_providers import discover_local_model_presets, local_cli_configured


@dataclass(frozen=True)
class ProviderCatalogEntry:
    provider: str
    name: str
    default_model: str
    default_endpoint: str | None
    requires_api_key: bool
    api_key_envs: tuple[str, ...]


@dataclass(frozen=True)
class ModelPreset:
    id: str
    name: str
    provider: str
    model: str
    capabilities: tuple[str, ...]
    endpoint: str | None = None

    @property
    def route(self) -> str:
        suffix = f"@{self.endpoint}" if self.endpoint else ""
        return f"{self.provider}:{self.model}{suffix}"


PROVIDERS: dict[str, ProviderCatalogEntry] = {
    "anthropic": ProviderCatalogEntry(
        provider="anthropic",
        name="Anthropic (Claude)",
        default_model="claude-sonnet-4-20250514",
        default_endpoint="https://api.anthropic.com/v1",
        requires_api_key=True,
        api_key_envs=("ANTHROPIC_API_KEY",),
    ),
    "openai": ProviderCatalogEntry(
        provider="openai",
        name="OpenAI",
        default_model="gpt-4o",
        default_endpoint="https://api.openai.com/v1",
        requires_api_key=True,
        api_key_envs=("OPENAI_API_KEY",),
    ),
    "gemini": ProviderCatalogEntry(
        provider="gemini",
        name="Google Gemini",
        default_model="gemini-2.0-flash",
        default_endpoint="https://generativelanguage.googleapis.com/v1beta",
        requires_api_key=True,
        api_key_envs=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    ),
    "ollama": ProviderCatalogEntry(
        provider="ollama",
        name="Ollama (Local)",
        default_model="mistral",
        default_endpoint="http://127.0.0.1:11434",
        requires_api_key=False,
        api_key_envs=(),
    ),
    "openai-compat": ProviderCatalogEntry(
        provider="openai-compat",
        name="OpenAI-Compatible (vLLM, LM Studio, etc.)",
        default_model="local-model",
        default_endpoint="http://127.0.0.1:8000/v1",
        requires_api_key=False,
        api_key_envs=("OPENAI_COMPAT_API_KEY",),
    ),
    "deepseek": ProviderCatalogEntry(
        provider="deepseek",
        name="DeepSeek",
        default_model="deepseek-chat",
        default_endpoint="https://api.deepseek.com/v1",
        requires_api_key=True,
        api_key_envs=("DEEPSEEK_API_KEY",),
    ),
    "minimax": ProviderCatalogEntry(
        provider="minimax",
        name="MiniMax",
        default_model="abab6.5s-chat",
        default_endpoint="https://api.minimax.chat/v1/text/chatcompletion_v2",
        requires_api_key=True,
        api_key_envs=("MINIMAX_API_KEY", "MINIMAX_CN_API_KEY"),
    ),
    "qwen": ProviderCatalogEntry(
        provider="qwen",
        name="Alibaba Qwen",
        default_model="qwen-max",
        default_endpoint="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        requires_api_key=True,
        api_key_envs=("QWEN_API_KEY",),
    ),
    "kimi": ProviderCatalogEntry(
        provider="kimi",
        name="Moonshot Kimi",
        default_model="kimi-latest",
        default_endpoint="https://api.moonshot.ai/v1",
        requires_api_key=True,
        api_key_envs=("MOONSHOT_API_KEY", "KIMI_API_KEY"),
    ),
    "kimi-code": ProviderCatalogEntry(
        provider="kimi-code",
        name="Moonshot Kimi for Coding",
        default_model="kimi-for-coding",
        default_endpoint="https://api.kimi.com/coding/v1",
        requires_api_key=True,
        api_key_envs=("KIMI_API_KEY",),
    ),
    "claude-code": ProviderCatalogEntry(
        provider="claude-code",
        name="Claude Code CLI (Local)",
        default_model="default",
        default_endpoint=None,
        requires_api_key=False,
        api_key_envs=(),
    ),
    "codex": ProviderCatalogEntry(
        provider="codex",
        name="Codex CLI (Local)",
        default_model="default",
        default_endpoint=None,
        requires_api_key=False,
        api_key_envs=(),
    ),
}


MODEL_PRESETS: tuple[ModelPreset, ...] = (
    ModelPreset("openai", "OpenAI GPT-4o", "openai", "gpt-4o", ("writing", "reasoning", "analysis")),
    ModelPreset("anthropic", "Claude Sonnet", "anthropic", "claude-sonnet-4-20250514", ("writing", "analysis")),
    ModelPreset("gemini", "Gemini 2.0 Flash", "gemini", "gemini-2.0-flash", ("general", "multimodal")),
    ModelPreset("deepseek", "DeepSeek", "deepseek", "deepseek-chat", ("planning", "analysis", "reasoning")),
    ModelPreset(
        "deepseek-reasoner",
        "DeepSeek Reasoner",
        "deepseek",
        "deepseek-reasoner",
        ("planning", "reasoning", "analysis"),
    ),
    ModelPreset("deepseek-v4-pro", "DeepSeek V4 Pro", "deepseek", "deepseek-v4-pro", ("coding", "analysis")),
    ModelPreset("deepseek-v4-flash", "DeepSeek V4 Flash", "deepseek", "deepseek-v4-flash", ("iteration", "coding")),
    ModelPreset("minimax-m2.7", "MiniMax M2.7", "minimax", "minimax-m2.7", ("creative", "writing", "reasoning")),
    ModelPreset("minimax-m2.5", "MiniMax M2.5", "minimax", "minimax-m2.5", ("creative", "writing")),
    ModelPreset("minimax-m2.1", "MiniMax M2.1", "minimax", "minimax-m2.1", ("creative", "writing")),
    ModelPreset("minimax-m1", "MiniMax M1", "minimax", "minimax-m1", ("creative", "design")),
    ModelPreset("minimax-abab", "MiniMax ABAB6.5s", "minimax", "abab6.5s-chat", ("creative", "writing")),
    ModelPreset("qwen", "Qwen 3.5", "qwen", "qwen-max", ("coding", "reasoning", "analysis")),
    ModelPreset("kimi", "Kimi K2.6", "kimi", "kimi-latest", ("coding", "analysis", "reasoning")),
    ModelPreset("kimi-code", "Kimi Code", "kimi-code", "kimi-for-coding", ("coding", "debugging")),
    ModelPreset(
        "vllm",
        "vLLM",
        "openai-compat",
        os.getenv("VLLM_MODEL", "meta-llama/Llama-4-Scout-17B-16E-Instruct"),
        ("local", "coding", "analysis"),
        os.getenv("VLLM_ENDPOINT", "http://127.0.0.1:8000/v1"),
    ),
    ModelPreset(
        "lmstudio",
        "LM Studio",
        "openai-compat",
        os.getenv("LMSTUDIO_MODEL", "local-model"),
        ("local", "creative", "reasoning"),
        os.getenv("LMSTUDIO_ENDPOINT", "http://127.0.0.1:1234/v1"),
    ),
    ModelPreset("ollama", "Ollama Mistral", "ollama", "mistral", ("local", "general")),
    ModelPreset("claude-code-default", "Claude Code", "claude-code", "default", ("local", "writing", "review", "agent")),
    ModelPreset("codex-default", "Codex CLI", "codex", "default", ("local", "writing", "review", "agent")),
)


def catalog_payload() -> dict:
    model_presets = _catalog_model_presets()
    return {
        "providers": [
            {
                "provider": entry.provider,
                "name": entry.name,
                "defaultModel": entry.default_model,
                "defaultEndpoint": entry.default_endpoint,
                "requiresApiKey": entry.requires_api_key,
                "apiKeyEnvs": list(entry.api_key_envs),
                "configured": provider_configured(entry.provider),
            }
            for entry in PROVIDERS.values()
        ],
        "models": [
            {
                "id": preset.id,
                "name": preset.name,
                "provider": preset.provider,
                "model": preset.model,
                "endpoint": preset.endpoint,
                "route": preset.route,
                "capabilities": list(preset.capabilities),
            }
            for preset in model_presets
        ],
        "roles": [
            {"id": "plan", "name": "Research plan"},
            {"id": "draft", "name": "Draft"},
            {"id": "review", "name": "Review"},
            {"id": "revision", "name": "Revision plan"},
            {"id": "score", "name": "Score gate"},
        ],
    }


def provider_configured(provider: str) -> bool:
    if provider in {"claude-code", "codex"}:
        return local_cli_configured(provider)
    entry = PROVIDERS.get(provider)
    if not entry:
        return False
    if not entry.requires_api_key:
        return True
    provider_prefix = provider.upper().replace("-", "_")
    if os.getenv(f"ASL_{provider_prefix}_API_KEY"):
        return True
    return any(os.getenv(env_name) for env_name in entry.api_key_envs)


def _catalog_model_presets() -> tuple[ModelPreset, ...]:
    presets = list(MODEL_PRESETS)
    for local in discover_local_model_presets():
        presets.append(
            ModelPreset(
                id=local.id,
                name=local.name,
                provider=local.provider,
                model=local.model,
                capabilities=local.capabilities,
                endpoint=local.endpoint,
            )
        )

    seen: set[str] = set()
    unique: list[ModelPreset] = []
    for preset in presets:
        key = preset.route
        if key in seen:
            continue
        seen.add(key)
        unique.append(preset)
    return tuple(unique)
