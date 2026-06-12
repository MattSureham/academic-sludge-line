"""Auditable lightweight web-research helpers."""

from __future__ import annotations

import json
import html
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .workspace import read_json, utc_now, write_json, write_text


@dataclass(frozen=True)
class WebResearchSettings:
    enabled: bool = False
    provider: str = "duckduckgo"
    max_queries: int = 3
    max_results_per_query: int = 5


@dataclass(frozen=True)
class WebSource:
    query: str
    title: str
    url: str
    snippet: str
    provider: str

    def metadata(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class WebResearchResult:
    enabled: bool
    provider: str
    queries: tuple[str, ...] = ()
    sources: tuple[WebSource, ...] = ()
    errors: tuple[str, ...] = ()

    def metadata(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "queries": list(self.queries),
            "sources": [source.metadata() for source in self.sources],
            "errors": list(self.errors),
        }


def run_web_research(
    manifest: dict,
    brief: str,
    output_dir: Path,
    settings: WebResearchSettings,
) -> WebResearchResult:
    if not settings.enabled:
        return WebResearchResult(enabled=False, provider=settings.provider)

    queries = tuple(_build_queries(manifest, brief, settings.max_queries))
    sources: list[WebSource] = []
    errors: list[str] = []
    seen_urls: set[str] = set()
    for query in queries:
        try:
            results = _search(query, settings)
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{query}: {type(exc).__name__}: {exc}")
            continue

        for source in results:
            if source.url in seen_urls:
                continue
            seen_urls.add(source.url)
            sources.append(source)

    result = WebResearchResult(
        enabled=True,
        provider=settings.provider,
        queries=queries,
        sources=tuple(sources),
        errors=tuple(errors),
    )
    write_json(output_dir / "web_research.json", result.metadata())
    write_text(output_dir / "web_research.md", format_web_research(result))
    return result


def append_web_research_to_brief(brief: str, result: WebResearchResult) -> str:
    if not result.enabled:
        return brief
    return f"{brief.strip() or 'TODO'}\n\n{web_research_context(result)}"


def web_research_context(result: WebResearchResult) -> str:
    lines = [
        "## Web Research Leads",
        "",
        "Use these as leads only. Verify source authority and exact claims before citing.",
        "",
        "Queries:",
    ]
    if result.queries:
        lines.extend(f"- {query}" for query in result.queries)
    else:
        lines.append("- TODO: no query generated")
    lines.extend(["", "Sources:"])
    if result.sources:
        for index, source in enumerate(result.sources, 1):
            snippet = f" - {source.snippet}" if source.snippet else ""
            lines.append(f"{index}. {source.title} ({source.url}){snippet}")
    else:
        lines.append("- No web sources returned.")
    if result.errors:
        lines.extend(["", "Search errors:"])
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_web_research(result: WebResearchResult) -> str:
    lines = [
        "# Web Research",
        "",
        f"Provider: {result.provider}",
        f"Enabled: {str(result.enabled).lower()}",
        "",
    ]
    if not result.enabled:
        lines.append("Web research was not enabled for this run.")
        return "\n".join(lines)
    lines.append(web_research_context(result))
    return "\n".join(lines)


def update_sources_ledger(project_dir: Path, version_name: str, result: WebResearchResult) -> None:
    if not result.enabled or not result.sources:
        return

    path = project_dir / "sources.json"
    existing = read_json(path) if path.exists() else []
    if not isinstance(existing, list):
        existing = []
    seen = {str(item.get("url", "")) for item in existing if isinstance(item, dict)}
    for source in result.sources:
        if source.url in seen:
            continue
        existing.append(
            {
                "kind": "web",
                "title": source.title,
                "url": source.url,
                "snippet": source.snippet,
                "query": source.query,
                "provider": source.provider,
                "version": version_name,
                "captured_at": utc_now(),
            }
        )
        seen.add(source.url)
    write_json(path, existing)


def _build_queries(manifest: dict, brief: str, limit: int) -> list[str]:
    candidates = [
        str(manifest.get("research_question") or ""),
        str(manifest.get("topic") or ""),
        str(manifest.get("title") or ""),
    ]
    brief_line = next((line.strip() for line in brief.splitlines() if len(line.strip()) > 24), "")
    if brief_line:
        candidates.append(brief_line)

    queries: list[str] = []
    for candidate in candidates:
        query = _clean_query(candidate)
        if not query or query.lower().startswith("todo"):
            continue
        if query.lower() not in {item.lower() for item in queries}:
            queries.append(query)
        if len(queries) >= max(1, limit):
            break
    return queries


def _clean_query(value: str) -> str:
    value = re.sub(r"\[[^\]]+\]", " ", value)
    value = re.sub(r"[#*_`>]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .,:;")
    return value[:180]


def _search(query: str, settings: WebResearchSettings) -> list[WebSource]:
    if settings.provider != "duckduckgo":
        raise ValueError(f"unsupported web research provider: {settings.provider}")
    return _search_duckduckgo(query, max_results=max(1, settings.max_results_per_query))


def _search_duckduckgo(query: str, max_results: int) -> list[WebSource]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
    )
    request = urllib.request.Request(
        f"https://api.duckduckgo.com/?{params}",
        headers={"User-Agent": "academic-sludge-line/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))

    sources: list[WebSource] = []
    if body.get("AbstractURL") and body.get("AbstractText"):
        sources.append(
            WebSource(
                query=query,
                title=str(body.get("Heading") or body["AbstractURL"]),
                url=str(body["AbstractURL"]),
                snippet=str(body["AbstractText"]),
                provider="duckduckgo",
            )
        )
    for topic in _flatten_related_topics(body.get("RelatedTopics", [])):
        if len(sources) >= max_results:
            break
        url = str(topic.get("FirstURL") or "")
        text = str(topic.get("Text") or "")
        if not url or not text:
            continue
        title = text.split(" - ", 1)[0].strip() or url
        sources.append(
            WebSource(
                query=query,
                title=title,
                url=url,
                snippet=text,
                provider="duckduckgo",
            )
        )
    if not sources:
        sources.extend(_search_duckduckgo_html(query, max_results=max_results))
    return sources[:max_results]


def _search_duckduckgo_html(query: str, max_results: int) -> list[WebSource]:
    params = urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        f"https://html.duckduckgo.com/html/?{params}",
        headers={"User-Agent": "academic-sludge-line/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        page = response.read().decode("utf-8", errors="replace")

    sources: list[WebSource] = []
    pattern = re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(page):
        if len(sources) >= max_results:
            break
        url = _decode_duckduckgo_href(html.unescape(match.group(1)))
        title = _strip_html(match.group(2))
        if not url or not title:
            continue
        window = page[match.end() : match.end() + 1200]
        snippet_match = re.search(
            r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
            window,
            flags=re.IGNORECASE | re.DOTALL,
        )
        snippet = _strip_html(snippet_match.group(1)) if snippet_match else ""
        sources.append(
            WebSource(
                query=query,
                title=title,
                url=url,
                snippet=snippet,
                provider="duckduckgo",
            )
        )
    return sources


def _flatten_related_topics(items: Iterable[object]) -> list[dict]:
    flattened: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("Topics"), list):
            flattened.extend(_flatten_related_topics(item["Topics"]))
        else:
            flattened.append(item)
    return flattened


def _decode_duckduckgo_href(href: str) -> str:
    parsed = urllib.parse.urlparse(href)
    params = urllib.parse.parse_qs(parsed.query)
    if params.get("uddg"):
        return params["uddg"][0]
    return href


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()
