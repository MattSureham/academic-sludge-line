"""Discovery helpers for locally configured agent CLIs and cc-switch profiles."""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class LocalModelPreset:
    id: str
    name: str
    provider: str
    model: str
    capabilities: tuple[str, ...]
    endpoint: str | None = None


@dataclass(frozen=True)
class CCSwitchProfile:
    id: str
    name: str
    model: str
    env: dict[str, str]


def local_cli_configured(provider: str) -> bool:
    if provider == "claude-code":
        return bool(shutil.which(os.getenv("ASL_CLAUDE_CODE_COMMAND", "claude")))
    if provider == "codex":
        return bool(shutil.which(os.getenv("ASL_CODEX_COMMAND", "codex")))
    return False


def discover_local_model_presets(cwd: Path | None = None) -> list[LocalModelPreset]:
    presets = [
        LocalModelPreset(
            id="claude-code-local",
            name="Claude Code (local config)",
            provider="claude-code",
            model=_configured_claude_model() or "default",
            capabilities=("local", "writing", "review", "agent"),
        ),
        LocalModelPreset(
            id="codex-local",
            name="Codex CLI (local config)",
            provider="codex",
            model=_configured_codex_model() or "default",
            capabilities=("local", "writing", "review", "agent"),
        ),
    ]

    for profile in discover_cc_switch_profiles(cwd):
        presets.append(
            LocalModelPreset(
                id=f"cc-switch-{profile.id}",
                name=f"cc-switch: {profile.name}",
                provider="claude-code",
                model=profile.model,
                capabilities=("local", "writing", "review", "cc-switch"),
                endpoint=f"cc-switch:{profile.id}",
            )
        )
    return _dedupe_presets(presets)


def cc_switch_settings_for_ref(ref: str | None, cwd: Path | None = None) -> dict[str, dict[str, str]] | None:
    if not ref or not ref.startswith("cc-switch:"):
        return None
    profile_id = ref.split(":", 1)[1]
    for profile in discover_cc_switch_profiles(cwd):
        if profile.id == profile_id:
            return {"env": dict(profile.env)}
    return None


def discover_cc_switch_profiles(cwd: Path | None = None) -> list[CCSwitchProfile]:
    profiles: list[CCSwitchProfile] = []
    for path in _cc_switch_config_paths(cwd or Path.cwd()):
        payload = _read_json_file(path)
        if payload is None:
            continue
        profiles.extend(_profiles_from_payload(payload, path))
    for path in _cc_switch_db_paths():
        profiles.extend(_profiles_from_sqlite(path))
    return _dedupe_profiles(profiles)


def _configured_claude_model() -> str | None:
    env_model = os.getenv("ANTHROPIC_MODEL") or os.getenv("CLAUDE_MODEL")
    if env_model:
        return env_model

    settings = _read_json_file(Path.home() / ".claude" / "settings.json")
    env = settings.get("env", {}) if isinstance(settings, dict) else {}
    if isinstance(env, dict):
        return _first_string(
            env.get("ANTHROPIC_MODEL"),
            env.get("ANTHROPIC_DEFAULT_SONNET_MODEL"),
            env.get("ANTHROPIC_DEFAULT_OPUS_MODEL"),
            env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL"),
        )
    return None


def _configured_codex_model() -> str | None:
    config = Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    if not config.exists():
        return os.getenv("CODEX_MODEL")
    text = config.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?m)^model\s*=\s*[\"']([^\"']+)[\"']", text)
    return os.getenv("CODEX_MODEL") or (match.group(1).strip() if match else None)


def _cc_switch_config_paths(cwd: Path) -> list[Path]:
    paths: list[Path] = []
    for env_name in ("ASL_CC_SWITCH_CONFIG", "CC_SWITCH_CONFIG"):
        value = os.getenv(env_name)
        if value:
            paths.extend(_expand_config_candidate(Path(value).expanduser()))

    for root in (cwd, Path.home(), Path.home() / ".config"):
        paths.extend(
            [
                root / ".cc-switch.json",
                root / ".cc-switch" / "config.json",
                root / ".cc-switch" / "providers.json",
                root / "cc-switch" / "config.json",
                root / "cc-switch" / "providers.json",
            ]
        )

    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _cc_switch_db_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.getenv("ASL_CC_SWITCH_DB")
    if env_path:
        paths.append(Path(env_path).expanduser())
    paths.append(Path.home() / ".cc-switch" / "cc-switch.db")
    return [path for path in paths if path.exists()]


def _expand_config_candidate(path: Path) -> list[Path]:
    if path.is_dir():
        return [
            path / "config.json",
            path / "providers.json",
            path / ".cc-switch.json",
        ]
    return [path]


def _read_json_file(path: Path) -> Any | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _profiles_from_payload(payload: Any, path: Path) -> list[CCSwitchProfile]:
    candidates: list[tuple[str, dict[str, Any]]] = []
    if isinstance(payload, dict):
        for key in ("providers", "profiles", "configs"):
            value = payload.get(key)
            candidates.extend(_named_dict_items(value))
        if not candidates:
            candidates.extend(_named_dict_items(payload))
    elif isinstance(payload, list):
        candidates.extend(_named_dict_items(payload))

    profiles = []
    for fallback_name, data in candidates:
        profile = _profile_from_mapping(fallback_name, data, path)
        if profile:
            profiles.append(profile)
    return profiles


def _profiles_from_sqlite(path: Path) -> list[CCSwitchProfile]:
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, settings_config
            FROM providers
            WHERE app_type = 'claude'
            ORDER BY sort_index, name
            """
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        try:
            conn.close()
        except UnboundLocalError:
            pass

    profiles = []
    for row in rows:
        try:
            settings = json.loads(row["settings_config"] or "{}")
        except json.JSONDecodeError:
            continue
        if not isinstance(settings, dict):
            continue
        settings.setdefault("id", row["name"] or row["id"])
        settings.setdefault("name", row["name"] or row["id"])
        profile = _profile_from_mapping(row["name"] or row["id"], settings, path)
        if profile:
            profiles.append(profile)
    return profiles


def _named_dict_items(value: Any) -> list[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if isinstance(item, dict):
                items.append((str(key), item))
        return items
    if isinstance(value, list):
        items = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                name = _first_string(item.get("id"), item.get("name"), item.get("provider")) or f"profile-{index}"
                items.append((name, item))
        return items
    return []


def _profile_from_mapping(fallback_name: str, data: dict[str, Any], path: Path) -> CCSwitchProfile | None:
    env = _env_from_mapping(data)
    model = _first_string(
        data.get("model"),
        data.get("defaultModel"),
        data.get("ANTHROPIC_MODEL"),
        env.get("ANTHROPIC_MODEL"),
        env.get("ANTHROPIC_DEFAULT_SONNET_MODEL"),
        _first_from_iterable(data.get("models")),
    )
    if not model:
        return None

    name = _first_string(data.get("name"), data.get("label"), data.get("provider"), fallback_name) or fallback_name
    profile_id = _slugify(_first_string(data.get("id"), data.get("key"), fallback_name, path.stem) or fallback_name)
    return CCSwitchProfile(id=profile_id, name=name, model=model, env=env)


def _env_from_mapping(data: dict[str, Any]) -> dict[str, str]:
    env: dict[str, str] = {}
    raw_env = data.get("env")
    if isinstance(raw_env, dict):
        for key, value in raw_env.items():
            if isinstance(value, (str, int, float)):
                env[str(key)] = str(value)

    aliases = {
        "ANTHROPIC_BASE_URL": ("anthropicBaseUrl", "anthropic_base_url", "baseUrl", "baseURL", "base_url", "url"),
        "ANTHROPIC_AUTH_TOKEN": ("anthropicAuthToken", "anthropic_auth_token", "authToken", "token"),
        "ANTHROPIC_API_KEY": ("anthropicApiKey", "anthropic_api_key", "apiKey", "api_key"),
        "ANTHROPIC_MODEL": ("anthropicModel", "anthropic_model", "model"),
    }
    for env_name, keys in aliases.items():
        for key in keys:
            value = data.get(key)
            if isinstance(value, (str, int, float)) and str(value).strip():
                env.setdefault(env_name, str(value).strip())
                break
    return env


def _first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _first_from_iterable(value: Any) -> str | None:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, dict)):
        return None
    for item in value:
        if isinstance(item, str) and item.strip():
            return item.strip()
        if isinstance(item, dict):
            found = _first_string(item.get("model"), item.get("name"), item.get("id"))
            if found:
                return found
    return None


def _dedupe_presets(presets: list[LocalModelPreset]) -> list[LocalModelPreset]:
    seen: set[tuple[str, str, str | None]] = set()
    unique: list[LocalModelPreset] = []
    for preset in presets:
        key = (preset.provider, preset.model, preset.endpoint)
        if key in seen:
            continue
        seen.add(key)
        unique.append(preset)
    return unique


def _dedupe_profiles(profiles: list[CCSwitchProfile]) -> list[CCSwitchProfile]:
    seen: set[str] = set()
    unique: list[CCSwitchProfile] = []
    for profile in profiles:
        key = profile.id
        if key in seen:
            continue
        seen.add(key)
        unique.append(profile)
    return unique


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-")
    return slug or "profile"
