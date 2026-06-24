"""Adapter for loading project inputs through the adjacent smart-loader CLI."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROMPT_CONTEXT_LIMIT = 24_000
REFERENCE_CONTEXT_STRATEGIES = ("select", "balanced", "head")
_SELECT_FULL_CHARS = 3_500
_SELECT_SHORT_CHARS = 600
_BALANCED_MIN_CHARS = 400
_MIN_BLOCK_CHARS = 200


@dataclass(frozen=True)
class SmartLoaderSettings:
    pdf_render_pages: bool = True
    pdf_max_pages: int = 25
    pdf_dpi: int = 180
    ocr_assets: bool = True
    ocr_language: str = "eng"


@dataclass(frozen=True)
class ReferenceContextSettings:
    """How the loaded data/reference text is fitted into the prompt budget.

    strategy:
      - "select"   (default): rank documents by relevance to the topic; give the
                    top `full_count` a full slice and the rest a short excerpt, so
                    every document is represented instead of only the first few.
      - "balanced": split the budget evenly across all documents.
      - "head":     legacy behaviour — concatenate and truncate the head.
    """

    strategy: str = "select"
    limit: int = PROMPT_CONTEXT_LIMIT
    full_count: int = 6


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

    def __init__(self, cli_path: Path | None = None, settings: SmartLoaderSettings | None = None) -> None:
        self.cli_path = _resolve_cli(cli_path)
        self.settings = settings or SmartLoaderSettings()

    def load_group(self, label: str, paths: Iterable[Path], output_dir: Path) -> LoadedInputGroup:
        normalized_paths = tuple(_unique_paths(paths))
        if not normalized_paths:
            return LoadedInputGroup(label=label, paths=(), results=(), markdown="")

        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        for index, input_path in enumerate(normalized_paths, start=1):
            asset_dir = output_dir / "assets" / label / f"input-{index}"
            results.append(self._load_path(input_path, asset_dir))
        if self.settings.ocr_assets:
            _annotate_results_with_ocr(results, self.settings.ocr_language)

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
        if self.settings.pdf_render_pages:
            command.extend(
                [
                    "--pdf-render-pages",
                    "--pdf-max-pages",
                    str(self.settings.pdf_max_pages),
                    "--pdf-dpi",
                    str(self.settings.pdf_dpi),
                ]
            )
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
    settings: SmartLoaderSettings | None = None,
) -> list[LoadedInputGroup]:
    data = tuple(_unique_paths(data_paths))
    references = tuple(_unique_paths(reference_paths))
    if not data and not references:
        return []

    loader = SmartLoader(cli_path, settings=settings)
    groups = [
        loader.load_group("data", data, output_dir),
        loader.load_group("references", references, output_dir),
    ]
    return [group for group in groups if group.has_inputs]


def render_context_for_prompt(
    groups: Iterable[LoadedInputGroup],
    settings: ReferenceContextSettings | None = None,
    query: str = "",
) -> str:
    settings = settings or ReferenceContextSettings()
    sections = [group.markdown for group in groups if group.markdown.strip()]
    if not sections:
        return ""
    combined = "\n\n---\n\n".join(sections)
    return budget_reference_context(combined, settings, query)


def append_context_to_brief(
    brief: str,
    groups: Iterable[LoadedInputGroup],
    settings: ReferenceContextSettings | None = None,
    query: str = "",
) -> str:
    context = render_context_for_prompt(groups, settings, query)
    if not context:
        return brief
    base = brief.strip() or "TODO"
    return f"{base}\n\n## Loaded Data And References\n\n{context}"


def budget_reference_context(
    combined: str,
    settings: ReferenceContextSettings | None = None,
    query: str = "",
    limit: int | None = None,
) -> str:
    """Fit concatenated document markdown into `limit` chars using the strategy.

    Documents are split on their `## ` headers; the preamble (group header and
    load summary) is preserved. "head" falls back to plain head-truncation.
    """
    settings = settings or ReferenceContextSettings()
    limit = settings.limit if limit is None else limit
    combined = combined.strip()
    if limit <= 0 or len(combined) <= limit:
        return combined
    if settings.strategy == "head":
        return _clip(combined, limit)

    preamble, blocks = _split_doc_blocks(combined)
    if not blocks:
        return _clip(combined, limit)

    preamble = preamble.strip()
    body_budget = max(_MIN_BLOCK_CHARS, limit - len(preamble) - 2)
    if settings.strategy == "balanced":
        kept = _budget_balanced(blocks, body_budget)
    else:
        kept = _budget_select(blocks, body_budget, query, settings.full_count)
    body = "\n\n".join(block for block in kept if block.strip())
    rendered = f"{preamble}\n\n{body}".strip() if preamble else body
    return _clip(rendered, limit)


def _split_doc_blocks(text: str) -> tuple[str, list[str]]:
    parts = re.split(r"(?m)(?=^## )", text)
    if len(parts) <= 1:
        return text, []
    preamble = parts[0]
    blocks = [part.strip() for part in parts[1:] if part.strip()]
    return preamble, blocks


def _budget_balanced(blocks: list[str], budget: int) -> list[str]:
    per_doc = max(_BALANCED_MIN_CHARS, budget // max(1, len(blocks)))
    kept: list[str] = []
    used = 0
    for block in blocks:
        if used >= budget:
            kept.append(_doc_title_line(block) + "\n[omitted to fit prompt budget]")
            continue
        allow = min(per_doc, budget - used)
        clipped = _clip_block(block, allow)
        kept.append(clipped)
        used += len(clipped)
    return kept


def _budget_select(blocks: list[str], budget: int, query: str, full_count: int) -> list[str]:
    order = sorted(range(len(blocks)), key=lambda i: (-_relevance(blocks[i], query), i))
    caps = {
        index: (_SELECT_FULL_CHARS if rank < max(1, full_count) else _SELECT_SHORT_CHARS)
        for rank, index in enumerate(order)
    }
    rendered: dict[int, str] = {}
    used = 0
    for index in order:
        block = blocks[index]
        if used >= budget:
            rendered[index] = _doc_title_line(block) + "\n[omitted to fit prompt budget]"
            used += len(rendered[index])
            continue
        allow = min(caps[index], max(_MIN_BLOCK_CHARS, budget - used))
        clipped = _clip_block(block, allow)
        rendered[index] = clipped
        used += len(clipped)
    return [rendered[index] for index in range(len(blocks))]


def _relevance(block: str, query: str) -> int:
    tokens = set(re.findall(r"[a-z0-9]{4,}", query.lower()))
    if not tokens:
        return 0
    lowered = block.lower()
    title = _doc_title_line(block).lower()
    return sum(lowered.count(token) + 2 * title.count(token) for token in tokens)


def _clip_block(block: str, allow: int) -> str:
    header, _, body = block.partition("\n")
    if len(block) <= allow:
        return block
    body_budget = max(0, allow - len(header) - 1)
    if not body or body_budget <= 0:
        return header.rstrip()
    return f"{header}\n{body[:body_budget].rstrip()}\n[…]"


def _doc_title_line(block: str) -> str:
    return block.split("\n", 1)[0].strip()


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
    bundled_loader = current_file.parent / "_vendor" / "smart-loader"
    candidates.append(bundled_loader)
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
        "smart-loader was not found. ASL includes a bundled loader under asl/_vendor/smart-loader; "
        "run npm ci there if its dependencies are missing, or set ASL_SMART_LOADER/pass --smart-loader "
        "with another CLI, dist/cli.js, or repo path."
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
    titles = {
        "data": "Loaded Data",
        "references": "Loaded References",
        "seed_draft": "Loaded Seed Draft",
    }
    title = titles.get(label, f"Loaded {label.replace('_', ' ').title()}")
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
            assets = document.get("assets", [])
            if assets:
                sections.append("Extracted assets:")
                for asset in assets:
                    if not isinstance(asset, dict):
                        continue
                    label_text = asset.get("originalName") or Path(str(asset.get("filePath", "asset"))).name
                    asset_kind = asset.get("kind", "asset")
                    sections.append(f"- {label_text} ({asset_kind}): {asset.get('filePath', '')}")
                    ocr_text = asset.get("ocrText")
                    if ocr_text:
                        sections.append(f"  OCR: {_clip(str(ocr_text), 2000)}")
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


def _annotate_results_with_ocr(results: list[dict[str, Any]], language: str) -> None:
    executable = shutil.which("tesseract")
    if not executable:
        _append_loader_warning_if_assets(results, "OCR requested for extracted images, but tesseract was not found.")
        return

    for result in results:
        for document in result.get("documents", []):
            if not isinstance(document, dict):
                continue
            for asset in document.get("assets", []):
                if not isinstance(asset, dict):
                    continue
                mime_type = str(asset.get("mimeType", ""))
                if not mime_type.startswith("image/"):
                    continue
                file_path = Path(str(asset.get("filePath", "")))
                if not file_path.exists():
                    continue
                completed = subprocess.run(
                    [executable, str(file_path), "stdout", "-l", language],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if completed.returncode == 0 and completed.stdout.strip():
                    asset["ocrText"] = completed.stdout.strip()
                elif completed.stderr.strip():
                    warnings = document.setdefault("warnings", [])
                    warnings.append(f"OCR failed for {file_path.name}: {completed.stderr.strip()}")


def _append_loader_warning_if_assets(results: list[dict[str, Any]], warning: str) -> None:
    for result in results:
        for document in result.get("documents", []):
            if isinstance(document, dict):
                has_image_asset = any(
                    isinstance(asset, dict) and str(asset.get("mimeType", "")).startswith("image/")
                    for asset in document.get("assets", [])
                )
                if has_image_asset:
                    document.setdefault("warnings", []).append(warning)


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
