"""Generate static HTML views for versioned paper outputs."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .workspace import read_json, read_text, write_text


TEXT_SUFFIXES = {".json", ".md", ".txt"}
IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}

BASE_OUTPUT_ORDER = (
    "topic_proposal.md",
    "prompt.md",
    "inputs/seed_draft.md",
    "inputs/data.md",
    "inputs/references.md",
    "inputs/smart_loader.json",
    "reference_search.md",
    "reference_search.json",
    "web_research.md",
    "web_research.json",
    "research_plan.md",
    "draft.md",
    "revision_plan.md",
    "quality_scores.json",
    "metadata.json",
)


def render_version_html(version_dir: Path) -> None:
    html_dir = version_dir / "html"
    pages: list[tuple[str, str, str]] = []
    for relative in _output_files(version_dir):
        source = version_dir / relative
        output_name = _html_name(relative)
        title = _title_from_relative(relative)
        body = _render_file(source)
        write_text(html_dir / output_name, _page(title, body, pages=[]))
        pages.append((title, output_name, relative))

    assets_body = _assets_body(version_dir)
    if assets_body:
        write_text(html_dir / "assets.html", _page("Extracted Assets", assets_body, pages=[]))
        pages.append(("Extracted Assets", "assets.html", "inputs/assets/"))

    index_body = _index_body(version_dir, pages)
    write_text(html_dir / "index.html", _page(f"{version_dir.name} outputs", index_body, pages=pages))

    for title, output_name, _relative in pages:
        path = html_dir / output_name
        body = _extract_body(read_text(path))
        write_text(path, _page(title, body, pages=pages, current=output_name))


def _render_file(path: Path) -> str:
    if path.suffix == ".json":
        return f"<pre>{html.escape(json.dumps(read_json(path), indent=2, ensure_ascii=False))}</pre>"
    return _markdown_to_html(read_text(path))


def _output_files(version_dir: Path) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def add(relative: str) -> None:
        path = version_dir / relative
        if relative in seen or not path.exists() or not path.is_file():
            return
        if path.suffix.lower() not in TEXT_SUFFIXES:
            return
        seen.add(relative)
        ordered.append(relative)

    for relative in BASE_OUTPUT_ORDER:
        add(relative)

    for path in sorted(version_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(version_dir).as_posix()
        if relative.startswith("html/") or relative.startswith("inputs/assets/"):
            continue
        add(relative)

    return ordered


def _markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            blocks.append("<ul>\n" + "\n".join(f"<li>{_inline(item)}</li>" for item in list_items) + "\n</ul>")
            list_items.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code:
                language = f' data-language="{html.escape(code_lang)}"' if code_lang else ""
                blocks.append(f"<pre><code{language}>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                code_lang = ""
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
                code_lang = line[3:].strip()
            continue
        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            continue

        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            list_items.append(bullet.group(1))
            continue

        paragraph.append(line.strip())

    flush_paragraph()
    flush_list()
    if in_code:
        blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(blocks)


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _page(title: str, body: str, pages: list[tuple[str, str, str]], current: str | None = None) -> str:
    nav = ""
    if pages:
        links = []
        for page_title, href, _relative in pages:
            class_name = ' class="active"' if href == current else ""
            links.append(f'<a{class_name} href="{html.escape(href)}">{html.escape(page_title)}</a>')
        nav = "<nav>" + "\n".join(links) + "</nav>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #20231f; --muted: #687067; --line: #d9ded5; --bg: #f7f8f5; --accent: #0f766e; }}
    body {{ margin: 0; font-family: ui-serif, Georgia, Cambria, serif; background: var(--bg); color: var(--ink); line-height: 1.58; }}
    header {{ padding: 24px clamp(18px, 5vw, 64px); border-bottom: 1px solid var(--line); background: white; }}
    header h1 {{ margin: 0; font-size: clamp(24px, 3vw, 38px); letter-spacing: 0; }}
    main {{ display: grid; grid-template-columns: minmax(190px, 260px) minmax(0, 860px); gap: 32px; padding: 28px clamp(18px, 5vw, 64px); }}
    nav {{ position: sticky; top: 20px; align-self: start; display: grid; gap: 6px; font-family: ui-sans-serif, system-ui, sans-serif; font-size: 14px; }}
    nav a {{ color: var(--muted); text-decoration: none; padding: 7px 9px; border-radius: 6px; }}
    nav a.active, nav a:hover {{ background: white; color: var(--accent); }}
    article {{ min-width: 0; background: white; border: 1px solid var(--line); border-radius: 8px; padding: clamp(18px, 4vw, 44px); }}
    h1, h2, h3 {{ line-height: 1.2; letter-spacing: 0; }}
    h1 {{ font-size: 2rem; }}
    h2 {{ margin-top: 2em; border-bottom: 1px solid var(--line); padding-bottom: .25em; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    code {{ background: #eef4ef; padding: 0 .22em; border-radius: 4px; }}
    pre {{ overflow: auto; background: #f4f6f2; border: 1px solid var(--line); border-radius: 8px; padding: 14px; white-space: pre-wrap; }}
    li {{ margin: .25em 0; }}
    .index-list {{ display: grid; gap: 8px; }}
    .index-list a {{ font-family: ui-sans-serif, system-ui, sans-serif; color: var(--accent); }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    figure {{ margin: 0; border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #fbfcf9; }}
    figure img {{ width: 100%; height: auto; display: block; border: 1px solid var(--line); background: white; }}
    figcaption {{ margin-top: 8px; color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif; font-size: 13px; overflow-wrap: anywhere; }}
    @media (max-width: 820px) {{ main {{ grid-template-columns: 1fr; }} nav {{ position: static; }} }}
  </style>
</head>
<body>
  <header><h1>{html.escape(title)}</h1></header>
  <main>
    {nav}
    <article>{body}</article>
  </main>
</body>
</html>
"""


def _assets_body(version_dir: Path) -> str:
    asset_root = version_dir / "inputs" / "assets"
    if not asset_root.exists():
        return ""

    image_items = []
    other_items = []
    for path in sorted(asset_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(version_dir).as_posix()
        label = path.relative_to(asset_root).as_posix()
        href = f"../{relative}"
        if path.suffix.lower() in IMAGE_SUFFIXES:
            image_items.append(
                "<figure>"
                f'<img src="{html.escape(href, quote=True)}" alt="{html.escape(label, quote=True)}">'
                f"<figcaption><code>{html.escape(label)}</code></figcaption>"
                "</figure>"
            )
        else:
            other_items.append(
                f'<li><a href="{html.escape(href, quote=True)}">{html.escape(label)}</a></li>'
            )

    if not image_items and not other_items:
        return ""

    sections = []
    if image_items:
        sections.append("<h2>Extracted Images</h2>")
        sections.append('<div class="asset-grid">' + "\n".join(image_items) + "</div>")
    if other_items:
        sections.append("<h2>Other Assets</h2>")
        sections.append("<ul>" + "\n".join(other_items) + "</ul>")
    return "\n".join(sections)


def _index_body(version_dir: Path, pages: list[tuple[str, str, str]]) -> str:
    items = "\n".join(
        f'<li><a href="{html.escape(href)}">{html.escape(title)}</a> <span>{html.escape(relative)}</span></li>'
        for title, href, relative in pages
    )
    return f"""
<h2>Version Directory</h2>
<p><code>{html.escape(str(version_dir))}</code></p>
<h2>Files</h2>
<ul class="index-list">
{items}
</ul>
"""


def _title_from_relative(relative: str) -> str:
    stem = Path(relative).stem.replace("_", " ").replace("-", " ")
    if relative.startswith("reviews/"):
        return f"{stem.title()} Review"
    return stem.title()


def _html_name(relative: str) -> str:
    safe = relative.replace("/", "_").rsplit(".", 1)[0]
    return f"{safe}.html"


def _extract_body(page: str) -> str:
    match = re.search(r"<article>(.*)</article>", page, flags=re.DOTALL)
    return match.group(1) if match else page
