"""Auditable literature-reference search helpers."""

from __future__ import annotations

import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from .workspace import read_json, utc_now, write_json, write_text


@dataclass(frozen=True)
class ReferenceSearchSettings:
    enabled: bool = False
    provider: str = "crossref"
    max_results: int = 8


@dataclass(frozen=True)
class ReferenceCandidate:
    query: str
    title: str
    authors: tuple[str, ...] = ()
    year: str = ""
    container: str = ""
    doi: str = ""
    url: str = ""
    snippet: str = ""
    provider: str = "crossref"

    def metadata(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReferenceSearchResult:
    enabled: bool
    provider: str
    query: str = ""
    candidates: tuple[ReferenceCandidate, ...] = ()
    errors: tuple[str, ...] = ()

    def metadata(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "query": self.query,
            "candidates": [candidate.metadata() for candidate in self.candidates],
            "errors": list(self.errors),
        }


def run_reference_search(
    manifest: dict,
    brief: str,
    output_dir: Path,
    settings: ReferenceSearchSettings,
) -> ReferenceSearchResult:
    if not settings.enabled:
        return ReferenceSearchResult(enabled=False, provider=settings.provider)

    query = _build_reference_query(manifest, brief)
    candidates: list[ReferenceCandidate] = []
    errors: list[str] = []
    if query:
        try:
            candidates = _search(query, settings)
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{query}: {type(exc).__name__}: {exc}")
    else:
        errors.append("No topic, title, research question, or brief text available for reference search.")

    result = ReferenceSearchResult(
        enabled=True,
        provider=settings.provider,
        query=query,
        candidates=tuple(candidates),
        errors=tuple(errors),
    )
    write_json(output_dir / "reference_search.json", result.metadata())
    write_text(output_dir / "reference_search.md", format_reference_search(result))
    return result


def append_reference_search_to_brief(brief: str, result: ReferenceSearchResult) -> str:
    if not result.enabled:
        return brief
    return f"{brief.strip() or 'TODO'}\n\n{reference_search_context(result)}"


def reference_search_context(result: ReferenceSearchResult) -> str:
    lines = [
        "## Reference Search Leads",
        "",
        "Use these as candidate references only. Verify relevance, metadata, and full text before citing.",
        "",
        f"Query: {result.query or 'TODO: no query generated'}",
        "",
        "Candidates:",
    ]
    if result.candidates:
        for index, candidate in enumerate(result.candidates, 1):
            details = _candidate_detail(candidate)
            lines.append(f"{index}. {details}")
    else:
        lines.append("- No reference candidates returned.")
    if result.errors:
        lines.extend(["", "Search errors:"])
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_reference_search(result: ReferenceSearchResult) -> str:
    lines = [
        "# Reference Search",
        "",
        f"Provider: {result.provider}",
        f"Enabled: {str(result.enabled).lower()}",
        "",
    ]
    if not result.enabled:
        lines.append("Reference search was not enabled for this run.")
        return "\n".join(lines)
    lines.append(reference_search_context(result))
    return "\n".join(lines)


def update_reference_sources_ledger(project_dir: Path, version_name: str, result: ReferenceSearchResult) -> None:
    if not result.enabled or not result.candidates:
        return

    path = project_dir / "sources.json"
    existing = read_json(path) if path.exists() else []
    if not isinstance(existing, list):
        existing = []
    seen = {str(item.get("url") or item.get("doi") or item.get("title") or "") for item in existing if isinstance(item, dict)}
    for candidate in result.candidates:
        key = candidate.url or candidate.doi or candidate.title
        if key in seen:
            continue
        existing.append(
            {
                "kind": "reference",
                "title": candidate.title,
                "authors": list(candidate.authors),
                "year": candidate.year,
                "container": candidate.container,
                "doi": candidate.doi,
                "url": candidate.url,
                "snippet": candidate.snippet,
                "query": candidate.query,
                "provider": candidate.provider,
                "version": version_name,
                "captured_at": utc_now(),
            }
        )
        seen.add(key)
    write_json(path, existing)


def _candidate_detail(candidate: ReferenceCandidate) -> str:
    authors = ", ".join(candidate.authors[:4])
    if len(candidate.authors) > 4:
        authors = f"{authors}, et al."
    year = f" ({candidate.year})" if candidate.year else ""
    container = f" - {candidate.container}" if candidate.container else ""
    url = f" {candidate.url}" if candidate.url else ""
    doi = f" DOI: {candidate.doi}" if candidate.doi else ""
    snippet = f" - {candidate.snippet}" if candidate.snippet else ""
    prefix = f"{authors}{year}. " if authors or year else ""
    return f"{prefix}{candidate.title}{container}.{doi}{url}{snippet}".strip()


def _build_reference_query(manifest: dict, brief: str) -> str:
    candidates = [
        str(manifest.get("research_question") or ""),
        str(manifest.get("topic") or ""),
        str(manifest.get("title") or ""),
    ]
    brief_line = next((line.strip() for line in brief.splitlines() if len(line.strip()) > 24), "")
    if brief_line:
        candidates.append(brief_line)
    for candidate in candidates:
        query = _clean_query(candidate)
        if query and not query.lower().startswith("todo"):
            return query
    return ""


def _clean_query(value: str) -> str:
    value = re.sub(r"\[[^\]]+\]", " ", value)
    value = re.sub(r"[#*_`>]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .,:;")
    return value[:220]


def _search(query: str, settings: ReferenceSearchSettings) -> list[ReferenceCandidate]:
    if settings.provider != "crossref":
        raise ValueError(f"unsupported reference search provider: {settings.provider}")
    return _search_crossref(query, max_results=max(1, settings.max_results))


def _search_crossref(query: str, max_results: int) -> list[ReferenceCandidate]:
    params = urllib.parse.urlencode(
        {
            "query.bibliographic": query,
            "rows": max_results,
            "sort": "relevance",
            "order": "desc",
        }
    )
    request = urllib.request.Request(
        f"https://api.crossref.org/works?{params}",
        headers={"User-Agent": _user_agent()},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))

    items = body.get("message", {}).get("items", [])
    if not isinstance(items, list):
        return []
    candidates: list[ReferenceCandidate] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        candidate = _candidate_from_crossref_item(query, item)
        if not candidate.title:
            continue
        key = candidate.doi or candidate.url or candidate.title.lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
        if len(candidates) >= max_results:
            break
    return candidates


def _user_agent() -> str:
    contact = os.getenv("ASL_CONTACT_EMAIL", "").strip()
    if contact:
        return f"academic-sludge-line/0.1 (mailto:{contact})"
    return "academic-sludge-line/0.1"


def _candidate_from_crossref_item(query: str, item: dict) -> ReferenceCandidate:
    doi = str(item.get("DOI") or "").strip()
    url = f"https://doi.org/{doi}" if doi else str(item.get("URL") or "").strip()
    return ReferenceCandidate(
        query=query,
        title=_first_text(item.get("title")),
        authors=tuple(_authors(item.get("author"))),
        year=_published_year(item),
        container=_first_text(item.get("container-title")),
        doi=doi,
        url=url,
        snippet=_strip_markup(str(item.get("abstract") or ""))[:500],
        provider="crossref",
    )


def _first_text(value: object) -> str:
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value or "").strip()


def _authors(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for author in value[:8]:
        if not isinstance(author, dict):
            continue
        family = str(author.get("family") or "").strip()
        given = str(author.get("given") or "").strip()
        literal = str(author.get("name") or "").strip()
        if family and given:
            names.append(f"{given} {family}")
        elif family:
            names.append(family)
        elif literal:
            names.append(literal)
    return names


def _published_year(item: dict) -> str:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        value = item.get(key)
        if not isinstance(value, dict):
            continue
        parts = value.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            return str(parts[0][0])
    return ""


def _strip_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()
