"""Adapter for loading project inputs through the adjacent smart-loader CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROMPT_CONTEXT_LIMIT = 24_000


@dataclass(frozen=True)
class LoadedInputGroup:
    label: str
    paths: tuple[Path, ...]
    results: tuple[dict[str, Any], ...]
    markdown: str

    @property
    def has_inputs(self) -> bool:
        return bool(self.paths)

    @property
    def summary(self) -> dict[str, Any]:
        totals = {
            "discoveredFiles": 0,
            "loadedFiles": 0,
            "skippedFiles": 0,
            "failedFiles": 0,
            "chunks": 0,
            "assets": 0,
        }
        for result in self.results:
            summary = result.get("summary", {})
            for key in totals:
                value = summary.get(key, 0)
                if isinstance(value, int):
                    totals[key] += value
        return totals

    @property
    def errors(self) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        for result in self.results:
            for error in result.get("errors", []):
                if isinstance(error, dict):
                    errors.append(error)
        return errors

    def metadata(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "paths": [str(path) for path in self.paths],
            "summary": self.summary,
            "errors": self.errors,
        }


class SmartLoader:
    """Small subprocess wrapper around smart-loader's JSON CLI output."""

    def __init__(self, cli_path: Path | None = None) -> None:
        self.cli_path = _resolve_cli(cli_path)

    def load_group(self, label: str, paths: Iterable[Path], output_dir: Path) -> LoadedInputGroup:
        normalized_paths = tuple(_unique_paths(paths))
        if not normalized_paths:
            return LoadedInputGroup(label=label, paths=(), results=(), markdown="")

        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        for index, input_path in enumerate(normalized_paths, start=1):
            asset_dir = output_dir / "assets" / label / f"input-{index}"
            results.append(self._load_path(input_path, asset_dir))

        return LoadedInputGroup(
            label=label,
            paths=normalized_paths,
            results=tuple(results),
            markdown=_render_group_markdown(label, normalized_paths, results),
        )

    def _load_path(self, input_path: Path, asset_dir: Path) -> dict[str, Any]:
        command = [
            *_command_prefix(self.cli_path),
            str(input_path),
            "--format",
            "json",
            "--asset-dir",
            str(asset_dir),
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise RuntimeError(f"smart-loader failed for {input_path}: {stderr or completed.stdout.strip()}")

        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"smart-loader returned invalid JSON for {input_path}: {exc}") from exc

        if not isinstance(result, dict):
            raise RuntimeError(f"smart-loader returned unexpected output for {input_path}")
        return result


def load_input_groups(
    data_paths: Iterable[Path],
    reference_paths: Iterable[Path],
    output_dir: Path,
    cli_path: Path | None = None,
) -> list[LoadedInputGroup]:
    data = tuple(_unique_paths(data_paths))
    references = tuple(_unique_paths(reference_paths))
    if not data and not references:
        return []

    loader = SmartLoader(cli_path)
    groups = [
        loader.load_group("data", data, output_dir),
        loader.load_group("references", references, output_dir),
    ]
    return [group for group in groups if group.has_inputs]


def render_context_for_prompt(groups: Iterable[LoadedInputGroup], limit: int = PROMPT_CONTEXT_LIMIT) -> str:
    sections = [group.markdown for group in groups if group.markdown.strip()]
    if not sections:
        return ""
    return _clip("\n\n---\n\n".join(sections), limit)


def append_context_to_brief(brief: str, groups: Iterable[LoadedInputGroup]) -> str:
    context = render_context_for_prompt(groups)
    if not context:
        return brief
    base = brief.strip() or "TODO"
    return f"{base}\n\n## Loaded Data And References\n\n{context}"


def resolve_input_paths(paths: Iterable[Path | str], base_dir: Path) -> list[Path]:
    resolved: list[Path] = []
    for path in paths:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        resolved.append(candidate.resolve())
    return resolved


def _resolve_cli(cli_path: Path | None) -> Path:
    candidates: list[Path] = []

    if cli_path:
        candidates.append(cli_path)

    env_path = os.getenv("ASL_SMART_LOADER")
    if env_path:
        candidates.append(Path(env_path))

    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        candidates.append(parent / "smart-loader")
    candidates.extend(
        [
            Path.cwd() / "smart-loader",
            Path.cwd().parent / "smart-loader",
        ]
    )

    for candidate in candidates:
        resolved = _candidate_cli(candidate)
        if resolved:
            return resolved

    executable = shutil.which("smart-loader")
    if executable:
        return Path(executable)

    raise RuntimeError(
        "smart-loader was not found. Set ASL_SMART_LOADER or pass --smart-loader with the CLI, dist/cli.js, or repo path."
    )


def _candidate_cli(candidate: Path) -> Path | None:
    if not candidate.exists():
        executable = shutil.which(str(candidate))
        return Path(executable) if executable else None

    if candidate.is_dir():
        for relative in ("dist/cli.js", "src/cli.ts"):
            cli = candidate / relative
            if cli.exists():
                return cli
        return None

    return candidate


def _command_prefix(cli_path: Path) -> list[str]:
    if cli_path.suffix == ".js":
        node = shutil.which("node")
        if not node:
            raise RuntimeError("smart-loader requires node to run dist/cli.js.")
        return [node, str(cli_path)]

    if cli_path.suffix == ".ts":
        tsx = shutil.which("tsx") or str(cli_path.parents[1] / "node_modules" / ".bin" / "tsx")
        if not Path(tsx).exists() and not shutil.which(tsx):
            raise RuntimeError("smart-loader src/cli.ts requires tsx.")
        return [tsx, str(cli_path)]

    return [str(cli_path)]


def _render_group_markdown(label: str, paths: tuple[Path, ...], results: list[dict[str, Any]]) -> str:
    title = "Loaded Data" if label == "data" else "Loaded References"
    sections = [f"# {title}", "", "Input paths:", *[f"- {path}" for path in paths], ""]
    summary = _combine_summaries(results)
    sections.extend(
        [
            "Summary:",
            f"- Discovered files: {summary['discoveredFiles']}",
            f"- Loaded files: {summary['loadedFiles']}",
            f"- Failed files: {summary['failedFiles']}",
            f"- Chunks: {summary['chunks']}",
            f"- Assets: {summary['assets']}",
            "",
        ]
    )

    errors = _collect_errors(results)
    if errors:
        sections.append("Load errors:")
        for error in errors:
            source = error.get("sourcePath", "unknown")
            reason = error.get("reason", "unknown error")
            sections.append(f"- {source}: {reason}")
        sections.append("")

    for result in results:
        for document in result.get("documents", []):
            if not isinstance(document, dict):
                continue
            relative = document.get("relativePath", document.get("sourcePath", "unknown"))
            format_name = document.get("format", "unknown")
            sections.extend([f"## {relative}", "", f"Format: {format_name}", ""])
            warnings = document.get("warnings", [])
            if warnings:
                sections.append("Warnings:")
                for warning in warnings:
                    sections.append(f"- {warning}")
                sections.append("")
            markdown = str(document.get("markdown") or document.get("text") or "").strip()
            sections.extend([_clip(markdown, 10_000), ""])

    return "\n".join(sections).strip()


def _combine_summaries(results: Iterable[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "discoveredFiles": 0,
        "loadedFiles": 0,
        "skippedFiles": 0,
        "failedFiles": 0,
        "chunks": 0,
        "assets": 0,
    }
    for result in results:
        summary = result.get("summary", {})
        for key in totals:
            value = summary.get(key, 0)
            if isinstance(value, int):
                totals[key] += value
    return totals


def _collect_errors(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for result in results:
        for error in result.get("errors", []):
            if isinstance(error, dict):
                errors.append(error)
    return errors


def _clip(text: str, limit: int) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[:limit].rstrip()}\n\n[TRUNCATED: {len(stripped) - limit} characters omitted]"


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = Path(path).resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return unique
