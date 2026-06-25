"""Render a draft's Markdown into an RTF document that Word opens and edits.

RTF is used instead of .docx so the pipeline keeps zero third-party
dependencies; Word reads and edits .rtf natively and can "Save As" .docx.
"""

from __future__ import annotations

import re
from pathlib import Path

_HEADING_SIZE = {1: 36, 2: 30, 3: 26, 4: 24, 5: 22, 6: 22}
_TABLE_WIDTH_TWIPS = 9360  # ~6.5in of content between 1in margins
_SEPARATOR_RE = re.compile(r"^:?-{2,}:?$")


def render_draft_doc(version_dir: Path) -> Path | None:
    """Write ``draft.rtf`` next to ``draft.md`` in a version dir."""
    draft_path = version_dir / "draft.md"
    if not draft_path.exists():
        return None
    rtf = markdown_to_rtf(draft_path.read_text(encoding="utf-8"))
    out_path = version_dir / "draft.rtf"
    out_path.write_text(rtf, encoding="ascii", errors="ignore")
    return out_path


def markdown_to_rtf(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    body: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("|") and stripped.count("|") >= 2:
            rows, index = _collect_table(lines, index)
            body.append(_table_to_rtf(rows))
            continue
        if not stripped:
            index += 1
            continue
        heading = re.match(r"(#{1,6})\s+(.*)", stripped)
        if heading:
            size = _HEADING_SIZE[len(heading.group(1))]
            body.append(r"{\b\fs%d %s\par}" % (size, _inline_to_rtf(heading.group(2))))
            index += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            body.append(r"{\pard\brdrb\brdrs\brdrw10\brsp20 \par}")
            index += 1
            continue
        bullet = re.match(r"[-*+]\s+(.*)", stripped)
        if bullet:
            body.append(r"{\pard\fi-200\li360 \bullet  %s\par}" % _inline_to_rtf(bullet.group(1)))
            index += 1
            continue
        numbered = re.match(r"(\d+)[.)]\s+(.*)", stripped)
        if numbered:
            body.append(
                r"{\pard\fi-200\li360 %s.  %s\par}"
                % (numbered.group(1), _inline_to_rtf(numbered.group(2)))
            )
            index += 1
            continue
        body.append(r"\pard %s\par" % _inline_to_rtf(stripped))
        index += 1

    header = r"{\rtf1\ansi\ansicpg1252\deff0{\fonttbl{\f0\fswiss Calibri;}}\fs22\sa120" + "\n"
    return header + "\n".join(body) + "\n}\n"


def _collect_table(lines: list[str], index: int) -> tuple[list[str], int]:
    rows: list[str] = []
    while index < len(lines) and lines[index].strip().startswith("|"):
        rows.append(lines[index].strip())
        index += 1
    return rows, index


def _table_to_rtf(rows: list[str]) -> str:
    parsed: list[list[str]] = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if all(_SEPARATOR_RE.match(cell.replace(" ", "")) or cell == "" for cell in cells):
            continue  # the |---|---| separator row
        parsed.append(cells)
    if not parsed:
        return r"\pard"
    ncols = max(len(row) for row in parsed)
    col_width = max(600, _TABLE_WIDTH_TWIPS // ncols)
    out: list[str] = []
    for row_index, row in enumerate(parsed):
        row = row + [""] * (ncols - len(row))
        parts = [r"\trowd\trgaph108"]
        for col in range(ncols):
            parts.append(r"\cellx%d" % (col_width * (col + 1)))
        for col in range(ncols):
            emphasis = r"\b " if row_index == 0 else ""
            parts.append(r"\pard\intbl %s%s\cell" % (emphasis, _inline_to_rtf(row[col])))
        parts.append(r"\row")
        out.append("".join(parts))
    out.append(r"\pard")
    return "\n".join(out)


_INLINE_SPLIT_RE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|_[^_]+?_)")


def _inline_to_rtf(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)  # inline code -> plain text
    text = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", text)  # links/images -> label
    pieces: list[str] = []
    for part in _INLINE_SPLIT_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            pieces.append(r"{\b %s}" % _escape(part[2:-2]))
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            pieces.append(r"{\i %s}" % _escape(part[1:-1]))
        elif part.startswith("_") and part.endswith("_") and len(part) >= 2:
            pieces.append(r"{\i %s}" % _escape(part[1:-1]))
        else:
            pieces.append(_escape(part))
    return "".join(pieces)


def _escape(text: str) -> str:
    out: list[str] = []
    for char in text:
        if char in "\\{}":
            out.append("\\" + char)
        elif ord(char) < 128:
            out.append(char)
        else:
            code = ord(char)
            if code > 32767:
                code -= 65536
            out.append(r"\u%d?" % code)
    return "".join(out)
