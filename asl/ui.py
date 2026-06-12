"""Small local web UI for configuring and running ASL projects."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__
from .catalog import catalog_payload
from .llm import LLMClient
from .pipeline import DEFAULT_REVIEWERS, PaperPipeline, init_project
from .smart_loader import SmartLoaderSettings
from .workspace import read_json, read_text


def run_ui(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> None:
    server = ThreadingHTTPServer((host, port), _handler_factory(Path.cwd()))
    url = f"http://{host}:{server.server_port}"
    print(url, flush=True)
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _handler_factory(cwd: Path) -> type[BaseHTTPRequestHandler]:
    class ASLUIHandler(BaseHTTPRequestHandler):
        server_version = f"ASLUI/{__version__}"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_html(_INDEX_HTML)
                return
            if parsed.path == "/app.css":
                self._send_text(_APP_CSS, "text/css; charset=utf-8")
                return
            if parsed.path == "/app.js":
                self._send_text(_APP_JS, "text/javascript; charset=utf-8")
                return
            if parsed.path == "/api/catalog":
                self._send_json({"cwd": str(cwd), "home": str(Path.home()), **catalog_payload()})
                return
            if parsed.path == "/api/browse":
                params = parse_qs(parsed.query)
                path_value = params.get("path", [str(cwd)])[0]
                path = _resolve_path(path_value or str(cwd), cwd)
                self._send_json(_browse_payload(path, cwd))
                return
            if parsed.path == "/api/projects":
                params = parse_qs(parsed.query)
                root = _resolve_path(params.get("root", [str(cwd)])[0], cwd)
                self._send_json({"root": str(root), "projects": _list_projects(root)})
                return
            if parsed.path == "/api/project":
                params = parse_qs(parsed.query)
                project_dir = _resolve_path(params.get("projectDir", [""])[0], cwd)
                self._send_json(_project_payload(project_dir))
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = self._read_json()
                if parsed.path == "/api/init":
                    self._send_json(_create_project(payload, cwd))
                    return
                if parsed.path == "/api/run":
                    self._send_json(_run_project(payload, cwd))
                    return
                if parsed.path == "/api/mkdir":
                    self._send_json(_create_directory(payload, cwd))
                    return
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except Exception as exc:  # noqa: BLE001 - UI should return readable failures.
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw or "{}")

        def _send_html(self, body: str) -> None:
            self._send_text(body, "text/html; charset=utf-8")

        def _send_text(self, body: str, content_type: str) -> None:
            data = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, value: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            data = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return ASLUIHandler


def _create_project(payload: dict, cwd: Path) -> dict:
    root = _resolve_path(payload.get("root") or str(cwd), cwd)
    project = init_project(
        root=root,
        slug=payload.get("slug") or None,
        title=payload["title"],
        topic=payload["topic"],
        research_question=payload.get("researchQuestion") or None,
        brief=payload.get("brief") or "",
        data_paths=tuple(Path(path) for path in _split_paths(payload.get("data"))),
        reference_paths=tuple(Path(path) for path in _split_paths(payload.get("references"))),
        model_routes=_model_routes(payload.get("models", {})),
        start_mode=payload.get("startMode") or "from-scratch",
        seed_draft_path=Path(payload["seedDraftFile"]) if payload.get("seedDraftFile") else None,
    )
    return {"projectDir": str(project), "project": _project_payload(project)}


def _run_project(payload: dict, cwd: Path) -> dict:
    project_dir = _resolve_path(payload["projectDir"], cwd)
    reviewers = tuple(_split_csv(payload.get("reviewers")) or DEFAULT_REVIEWERS)
    pipeline = PaperPipeline(
        project_dir,
        client=LLMClient(offline=bool(payload.get("offline"))),
        data_paths=tuple(Path(path) for path in _split_paths(payload.get("data"))),
        reference_paths=tuple(Path(path) for path in _split_paths(payload.get("references"))),
        smart_loader_path=Path(payload["smartLoader"]) if payload.get("smartLoader") else None,
        smart_loader_settings=_loader_settings(payload.get("loader", {})),
        model_routes=_model_routes(payload.get("models", {})),
        start_mode=payload.get("startMode") or None,
        seed_draft_path=Path(payload["seedDraftFile"]) if payload.get("seedDraftFile") else None,
    )
    created = pipeline.run(cycles=max(1, int(payload.get("cycles") or 1)), reviewers=reviewers)
    return {
        "created": [str(path) for path in created],
        "project": _project_payload(project_dir),
        "latest": _version_payload(created[-1]) if created else {},
    }


def _browse_payload(path: Path, cwd: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"path not found: {path}")
    directory = path if path.is_dir() else path.parent
    entries = []
    for child in sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        try:
            stat = child.stat()
        except OSError:
            continue
        entries.append(
            {
                "name": child.name,
                "path": str(child),
                "type": "directory" if child.is_dir() else "file",
                "size": stat.st_size if child.is_file() else None,
            }
        )
    parent = directory.parent if directory.parent != directory else None
    return {
        "cwd": str(cwd),
        "home": str(Path.home()),
        "path": str(directory),
        "parent": str(parent) if parent else None,
        "entries": entries,
    }


def _create_directory(payload: dict, cwd: Path) -> dict:
    parent = _resolve_path(str(payload.get("path") or cwd), cwd)
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("folder name is required")
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError("folder name must be a single directory name")
    directory = parent / name
    directory.mkdir(parents=False, exist_ok=False)
    return _browse_payload(directory, cwd)


def _project_payload(project_dir: Path) -> dict:
    manifest_path = project_dir / "project.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"project.json not found: {project_dir}")

    versions = []
    for child in sorted(project_dir.iterdir(), key=lambda path: path.name):
        if not child.is_dir() or not child.name.startswith("v"):
            continue
        metadata_path = child / "metadata.json"
        versions.append(
            {
                "name": child.name,
                "path": str(child),
                "metadata": read_json(metadata_path) if metadata_path.exists() else {},
            }
        )
    return {
        "path": str(project_dir),
        "manifest": read_json(manifest_path),
        "versions": versions,
        "acceptedVersion": _accepted_marker(project_dir),
        "latest": _version_payload(Path(versions[-1]["path"])) if versions else {},
    }


def _version_payload(version_dir: Path) -> dict:
    files = {}
    for relative in (
        "topic_proposal.md",
        "research_plan.md",
        "draft.md",
        "revision_plan.md",
        "quality_scores.json",
        "metadata.json",
    ):
        path = version_dir / relative
        if path.exists():
            files[relative] = _preview(path)
    reviews_dir = version_dir / "reviews"
    if reviews_dir.exists():
        for review in sorted(reviews_dir.glob("*.md")):
            files[f"reviews/{review.name}"] = _preview(review)
    payload = {"path": str(version_dir), "files": files}
    html_index = version_dir / "html" / "index.html"
    if html_index.exists():
        payload["htmlIndex"] = str(html_index)
    return payload


def _preview(path: Path, limit: int = 12_000) -> str:
    if path.suffix == ".json":
        return json.dumps(read_json(path), ensure_ascii=False, indent=2)[:limit]
    if (mimetypes.guess_type(path.name)[0] or "").startswith("text/") or path.suffix in {".md", ".txt"}:
        return read_text(path)[:limit]
    return ""


def _list_projects(root: Path) -> list[dict[str, str]]:
    papers = root / "papers"
    if not papers.exists():
        return []
    projects = []
    for child in sorted(papers.iterdir(), key=lambda path: path.name):
        manifest_path = child / "project.json"
        if child.is_dir() and manifest_path.exists():
            try:
                manifest = read_json(manifest_path)
            except json.JSONDecodeError:
                manifest = {}
            projects.append(
                {
                    "path": str(child),
                    "slug": child.name,
                    "title": manifest.get("title", child.name),
                    "topic": manifest.get("topic", ""),
                }
            )
    return projects


def _accepted_marker(project_dir: Path) -> str | None:
    marker = project_dir / "accepted_version.txt"
    if not marker.exists():
        return None
    value = marker.read_text(encoding="utf-8").strip()
    return value or None


def _resolve_path(value: str, cwd: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


def _model_routes(models: dict) -> dict[str, str]:
    routes = {}
    if not isinstance(models, dict):
        return routes
    for role in ("default", "plan", "draft", "review", "revision", "score"):
        value = str(models.get(role, "")).strip()
        if value:
            routes[role] = value
    return routes


def _loader_settings(loader: object) -> SmartLoaderSettings:
    if not isinstance(loader, dict):
        loader = {}
    return SmartLoaderSettings(
        pdf_render_pages=_bool_setting(loader.get("pdfRenderPages"), True),
        pdf_max_pages=_int_setting(loader.get("pdfMaxPages"), 25),
        pdf_dpi=_int_setting(loader.get("pdfDpi"), 180),
        ocr_assets=_bool_setting(loader.get("ocrAssets"), True),
        ocr_language=str(loader.get("ocrLanguage") or "eng").strip() or "eng",
    )


def _bool_setting(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off"}
    return bool(value)


def _int_setting(value: object, default: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError):
        return default
    return max(1, parsed)


def _split_paths(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item for item in (part.strip() for part in str(value).replace(",", "\n").splitlines()) if item]


def _split_csv(value: object) -> list[str]:
    if not value:
        return []
    return [item for item in (part.strip() for part in str(value).split(",")) if item]


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Academic Sludge Line</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <header class="topbar">
    <div>
      <h1>Academic Sludge Line</h1>
      <p id="workspace"></p>
    </div>
    <div class="top-actions">
      <button id="refreshBtn" type="button">Refresh</button>
    </div>
  </header>

  <main class="layout">
    <section class="panel setup-panel" aria-labelledby="setupTitle">
      <div class="tabs" role="tablist">
        <button class="tab active" data-tab="run" type="button">Run</button>
        <button class="tab" data-tab="init" type="button">New Paper</button>
        <button class="tab" data-tab="providers" type="button">Providers</button>
      </div>

      <form id="runForm" class="view active" data-view="run">
        <h2 id="setupTitle">Run Pipeline</h2>
        <label>Project
          <select id="projectSelect"></select>
        </label>
        <label><span class="label-text">Project path <span class="required-star" aria-hidden="true">*</span></span>
          <div class="path-field">
            <input id="runProjectDir" name="projectDir" autocomplete="off" required>
            <button type="button" class="browse-btn" data-target="runProjectDir" data-mode="dir">Browse</button>
          </div>
        </label>
        <div class="inline-fields">
          <label>Cycles
            <input id="cycles" name="cycles" type="number" min="1" value="1">
          </label>
          <label>Reviewers
            <input id="reviewers" name="reviewers" value="methods,evidence,style">
          </label>
        </div>
        <div class="inline-fields">
          <label>Start mode
            <select id="runStartMode">
              <option value="">Project default</option>
              <option value="from-scratch">From scratch</option>
              <option value="discover-topic">Discover topic</option>
              <option value="rewrite">Rewrite</option>
            </select>
          </label>
          <label><span class="label-text">Seed draft <span id="runSeedDraftRequired" class="required-star hidden" aria-hidden="true">*</span></span>
            <div class="path-field">
              <input id="runSeedDraft" placeholder="path/to/draft.md">
              <button type="button" class="browse-btn" data-target="runSeedDraft" data-mode="file">Browse</button>
            </div>
          </label>
        </div>
        <label class="checkline">
          <input id="offline" name="offline" type="checkbox" checked>
          Offline
        </label>
        <div id="runModelRoutes" class="routes"></div>
        <label>Additional data
          <textarea id="runData" rows="3"></textarea>
          <button type="button" class="secondary browse-btn" data-target="runData" data-mode="any" data-append="true">Add Path</button>
        </label>
        <label>Additional references
          <textarea id="runReferences" rows="3"></textarea>
          <button type="button" class="secondary browse-btn" data-target="runReferences" data-mode="any" data-append="true">Add Path</button>
        </label>
        <label>smart-loader
          <div class="path-field">
            <input id="smartLoader" placeholder="../smart-loader">
            <button type="button" class="browse-btn" data-target="smartLoader" data-mode="any">Browse</button>
          </div>
        </label>
        <div class="loader-options">
          <label class="checkline">
            <input id="pdfRenderPages" type="checkbox" checked>
            Render PDF pages
          </label>
          <label class="checkline">
            <input id="ocrAssets" type="checkbox" checked>
            OCR extracted images
          </label>
          <div class="inline-fields">
            <label>PDF max pages
              <input id="pdfMaxPages" type="number" min="1" value="25">
            </label>
            <label>PDF DPI
              <input id="pdfDpi" type="number" min="72" value="180">
            </label>
          </div>
          <label>OCR language
            <input id="ocrLanguage" value="eng">
          </label>
        </div>
        <button class="primary" type="submit">Run</button>
      </form>

      <form id="initForm" class="view" data-view="init">
        <h2>New Paper</h2>
        <label><span class="label-text">Workspace root <span class="required-star" aria-hidden="true">*</span></span>
          <div class="path-field">
            <input id="root" value="." required>
            <button type="button" class="browse-btn" data-target="root" data-mode="dir">Browse</button>
          </div>
        </label>
        <div class="inline-fields">
          <label>Start mode
            <select id="initStartMode">
              <option value="from-scratch">From scratch with topic</option>
              <option value="discover-topic">Discover topic from inputs</option>
              <option value="rewrite">Rewrite existing draft</option>
            </select>
          </label>
          <label><span class="label-text">Seed draft <span id="initSeedDraftRequired" class="required-star hidden" aria-hidden="true">*</span></span>
            <div class="path-field">
              <input id="initSeedDraft" placeholder="path/to/draft.md">
              <button type="button" class="browse-btn" data-target="initSeedDraft" data-mode="file">Browse</button>
            </div>
          </label>
        </div>
        <div class="inline-fields">
          <label>Slug
            <input id="slug" autocomplete="off">
          </label>
          <label><span class="label-text">Title <span class="required-star" aria-hidden="true">*</span></span>
            <input id="title" required autocomplete="off">
          </label>
        </div>
        <label><span class="label-text">Topic <span id="topicRequired" class="required-star" aria-hidden="true">*</span></span>
          <input id="topic" autocomplete="off" required>
        </label>
        <label>Research question
          <input id="researchQuestion" autocomplete="off">
        </label>
        <label>Brief
          <textarea id="brief" rows="6"></textarea>
        </label>
        <div id="initModelRoutes" class="routes"></div>
        <label>Data
          <textarea id="initData" rows="3"></textarea>
          <button type="button" class="secondary browse-btn" data-target="initData" data-mode="any" data-append="true">Add Path</button>
        </label>
        <label>References
          <textarea id="initReferences" rows="3"></textarea>
          <button type="button" class="secondary browse-btn" data-target="initReferences" data-mode="any" data-append="true">Add Path</button>
        </label>
        <button class="primary" type="submit">Create</button>
      </form>

      <section class="view providers-view" data-view="providers">
        <h2>Providers</h2>
        <div id="providerList" class="provider-list"></div>
      </section>
    </section>

    <section class="panel output-panel">
      <div class="output-head">
        <h2>Output</h2>
        <span id="status" class="status">Ready</span>
      </div>
      <div id="projectSummary" class="summary"></div>
      <div id="fileTabs" class="file-tabs"></div>
      <pre id="preview"></pre>
    </section>
  </main>

  <div id="browserModal" class="modal" hidden>
    <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="browserTitle">
      <div class="modal-head">
        <h2 id="browserTitle">Browse</h2>
        <button id="browserClose" type="button">Close</button>
      </div>
      <div class="browser-toolbar">
        <button id="browserHome" type="button">Home</button>
        <button id="browserWorkspace" type="button">Workspace</button>
        <button id="browserUp" type="button">Up</button>
        <button id="browserUseCurrent" type="button">Use Current</button>
      </div>
      <input id="browserPath" class="browser-path" autocomplete="off">
      <div class="mkdir-row">
        <input id="newFolderName" placeholder="New folder">
        <button id="createFolderBtn" type="button">Create</button>
      </div>
      <div id="browserEntries" class="browser-entries"></div>
    </div>
  </div>

  <script src="/app.js"></script>
</body>
</html>
"""


_APP_CSS = """
:root {
  --bg: #f6f7f4;
  --ink: #20231f;
  --muted: #697069;
  --line: #d9ded5;
  --panel: #ffffff;
  --accent: #0f766e;
  --accent-strong: #115e59;
  --warn: #9a3412;
  --soft: #eef4ef;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--ink);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px;
  line-height: 1.4;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid var(--line);
  background: #fbfcf9;
}

h1, h2 {
  margin: 0;
  letter-spacing: 0;
}

h1 { font-size: 20px; }
h2 { font-size: 16px; margin-bottom: 14px; }

#workspace {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.layout {
  display: grid;
  grid-template-columns: minmax(360px, 520px) minmax(0, 1fr);
  gap: 0;
  min-height: calc(100vh - 73px);
}

.panel {
  padding: 20px 24px;
}

.setup-panel {
  border-right: 1px solid var(--line);
  background: var(--panel);
  overflow: auto;
}

.output-panel {
  min-width: 0;
  overflow: hidden;
}

.tabs, .file-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

button, select, input, textarea {
  font: inherit;
}

button {
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  border-radius: 6px;
  padding: 8px 11px;
  cursor: pointer;
}

button:hover { border-color: var(--accent); }

.primary {
  width: 100%;
  margin-top: 12px;
  background: var(--accent);
  color: white;
  border-color: var(--accent);
  font-weight: 650;
}

.primary:hover { background: var(--accent-strong); }

.secondary {
  width: max-content;
  min-width: 96px;
}

.tab.active, .file-tabs button.active {
  border-color: var(--accent);
  background: var(--soft);
  color: var(--accent-strong);
}

.view { display: none; }
.view.active { display: block; }

label {
  display: grid;
  gap: 6px;
  margin: 12px 0;
  color: var(--muted);
  font-size: 12px;
  font-weight: 650;
}

.label-text {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.required-star {
  color: #dc2626;
  font-weight: 900;
}

.required-star.hidden {
  display: none;
}

input, textarea, select {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 9px 10px;
  color: var(--ink);
  background: #fff;
  min-height: 38px;
}

textarea {
  resize: vertical;
  min-height: 76px;
}

.inline-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.path-field {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.path-field input {
  min-width: 0;
}

.checkline {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--ink);
}

.checkline input {
  width: 16px;
  min-height: 16px;
}

.route-row {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  gap: 10px;
  align-items: end;
  margin: 10px 0;
}

.route-row span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  padding-bottom: 10px;
}

.route-row input {
  margin-top: 6px;
}

.loader-options {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 12px;
  background: #fbfcf9;
  margin: 12px 0;
}

.loader-options .checkline {
  margin: 8px 0;
}

.output-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.status {
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 5px 9px;
  background: #fff;
  font-size: 12px;
}

.summary {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
  color: var(--muted);
}

.provider-list {
  display: grid;
  gap: 8px;
}

.provider-item {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 12px;
  background: #fff;
  display: grid;
  gap: 4px;
}

.provider-item strong { color: var(--ink); }
.provider-item .ok { color: var(--accent-strong); }
.provider-item .missing { color: var(--warn); }

.modal {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgb(32 35 31 / 38%);
  z-index: 20;
}

.modal[hidden] {
  display: none;
}

.modal-panel {
  width: min(920px, 100%);
  max-height: min(760px, calc(100vh - 36px));
  overflow: hidden;
  display: grid;
  grid-template-rows: auto auto auto auto minmax(0, 1fr);
  gap: 10px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 24px 80px rgb(32 35 31 / 24%);
}

.modal-head, .browser-toolbar, .mkdir-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.modal-head {
  justify-content: space-between;
}

.browser-path {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.mkdir-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
}

.browser-entries {
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.browser-entry {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr) auto auto;
  gap: 8px;
  align-items: center;
  min-height: 42px;
  padding: 7px 9px;
  border-bottom: 1px solid var(--line);
}

.browser-entry:last-child {
  border-bottom: 0;
}

.browser-entry code {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: transparent;
  padding: 0;
}

.entry-kind {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

pre {
  margin: 0;
  height: calc(100vh - 190px);
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  padding: 16px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}

@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; }
  .setup-panel { border-right: 0; border-bottom: 1px solid var(--line); }
  .inline-fields, .route-row, .path-field, .mkdir-row, .browser-entry { grid-template-columns: 1fr; }
  .route-row span { padding-bottom: 0; }
  .secondary { width: 100%; }
  pre { height: 50vh; }
}
"""


_APP_JS = """
const state = {
  catalog: null,
  projects: [],
  currentProject: null,
  latestFiles: {},
  browser: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

function setStatus(text) {
  $("status").textContent = text;
}

function setRequiredState(inputId, starId, enabled) {
  const input = $(inputId);
  const star = $(starId);
  if (input) input.required = enabled;
  if (star) star.classList.toggle("hidden", !enabled);
}

function updateRequiredMarkers() {
  const initMode = $("initStartMode").value;
  const runMode = $("runStartMode").value;
  setRequiredState("topic", "topicRequired", initMode !== "discover-topic");
  setRequiredState("initSeedDraft", "initSeedDraftRequired", initMode === "rewrite");
  setRequiredState("runSeedDraft", "runSeedDraftRequired", runMode === "rewrite");
}

function routeRows(containerId) {
  const container = $(containerId);
  container.innerHTML = "";
  for (const role of state.catalog.roles) {
    const row = document.createElement("div");
    row.className = "route-row";
    const label = document.createElement("span");
    label.textContent = role.name;
    const wrap = document.createElement("div");
    const select = document.createElement("select");
    select.dataset.role = role.id;
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Default";
    select.appendChild(blank);
    for (const model of state.catalog.models) {
      const option = document.createElement("option");
      option.value = model.route;
      option.textContent = `${model.name} · ${model.route}`;
      select.appendChild(option);
    }
    const input = document.createElement("input");
    input.dataset.role = role.id;
    input.placeholder = "provider:model,provider:model";
    select.addEventListener("change", () => { input.value = select.value; });
    wrap.append(select, input);
    row.append(label, wrap);
    container.appendChild(row);
  }
}

function collectRoutes(containerId) {
  const routes = {};
  document.querySelectorAll(`#${containerId} input[data-role]`).forEach((input) => {
    const value = input.value.trim();
    if (value) routes[input.dataset.role] = value;
  });
  return routes;
}

async function loadCatalog() {
  state.catalog = await api("/api/catalog");
  $("workspace").textContent = state.catalog.cwd;
  routeRows("runModelRoutes");
  routeRows("initModelRoutes");
  renderProviders();
}

async function loadProjects() {
  const data = await api(`/api/projects?root=${encodeURIComponent($("root")?.value || ".")}`);
  state.projects = data.projects;
  const select = $("projectSelect");
  select.innerHTML = "";
  for (const project of state.projects) {
    const option = document.createElement("option");
    option.value = project.path;
    option.textContent = `${project.slug} · ${project.title}`;
    select.appendChild(option);
  }
  if (state.projects[0] && !$("runProjectDir").value) {
    $("runProjectDir").value = state.projects[0].path;
    await loadProject(state.projects[0].path);
  }
}

async function loadProject(projectDir) {
  if (!projectDir) return;
  state.currentProject = await api(`/api/project?projectDir=${encodeURIComponent(projectDir)}`);
  renderProject(state.currentProject);
}

function renderProject(project) {
  const manifest = project.manifest || {};
  const latest = project.latest || {};
  state.latestFiles = latest.files || {};
  const htmlLine = latest.htmlIndex ? `<div>HTML: <code>${latest.htmlIndex}</code></div>` : "";
  $("projectSummary").innerHTML = `
    <div><strong>${manifest.title || "Untitled"}</strong></div>
    <div>${manifest.topic || ""}</div>
    <div>${project.path}</div>
    <div>${project.versions.length} version(s)</div>
    <div>Accepted: ${project.acceptedVersion || "none yet"}</div>
    ${htmlLine}
  `;
  renderFileTabs();
}

function renderFileTabs() {
  const tabs = $("fileTabs");
  const entries = Object.entries(state.latestFiles);
  tabs.innerHTML = "";
  if (!entries.length) {
    $("preview").textContent = "";
    return;
  }
  entries.forEach(([name, value], index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = name;
    button.className = index === 0 ? "active" : "";
    button.addEventListener("click", () => {
      tabs.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      $("preview").textContent = value;
    });
    tabs.appendChild(button);
  });
  $("preview").textContent = entries[0][1];
}

function renderProviders() {
  const list = $("providerList");
  list.innerHTML = "";
  for (const provider of state.catalog.providers) {
    const item = document.createElement("div");
    item.className = "provider-item";
    const status = provider.configured ? "Configured" : "Needs key";
    const statusClass = provider.configured ? "ok" : "missing";
    item.innerHTML = `
      <strong>${provider.name}</strong>
      <span>${provider.provider}:${provider.defaultModel}</span>
      <span class="${statusClass}">${status}</span>
    `;
    list.appendChild(item);
  }
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === name));
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.dataset.view === name));
}

function fieldPathValue(targetId, append) {
  const field = $(targetId);
  if (!field) return state.catalog?.cwd || ".";
  if (!append) return field.value.trim() || state.catalog?.cwd || ".";
  const lines = field.value.split(/\\r?\\n/).map((line) => line.trim()).filter(Boolean);
  return lines[lines.length - 1] || $("root")?.value || state.catalog?.cwd || ".";
}

async function openPathBrowser(button) {
  const target = button.dataset.target;
  state.browser = {
    target,
    mode: button.dataset.mode || "any",
    append: button.dataset.append === "true",
  };
  $("browserTitle").textContent = button.dataset.mode === "file" ? "Browse Files" : "Browse Folders";
  $("browserModal").hidden = false;
  await browseTo(fieldPathValue(target, state.browser.append));
}

async function browseTo(path) {
  const data = await api(`/api/browse?path=${encodeURIComponent(path || state.catalog.cwd)}`);
  if (!state.browser) state.browser = {};
  state.browser.current = data;
  renderBrowser(data);
}

function renderBrowser(data) {
  $("browserPath").value = data.path;
  $("browserUp").disabled = !data.parent;
  $("browserUseCurrent").disabled = state.browser?.mode === "file";
  const entries = $("browserEntries");
  entries.innerHTML = "";
  for (const entry of data.entries) {
    const row = document.createElement("div");
    row.className = "browser-entry";
    const kind = document.createElement("span");
    kind.className = "entry-kind";
    kind.textContent = entry.type === "directory" ? "Folder" : "File";
    const name = document.createElement("code");
    name.textContent = entry.name;
    const open = document.createElement("button");
    open.type = "button";
    open.textContent = "Open";
    open.disabled = entry.type !== "directory";
    open.addEventListener("click", () => browseTo(entry.path).catch(showError));
    const select = document.createElement("button");
    select.type = "button";
    select.textContent = "Select";
    select.disabled = !canSelectEntry(entry.type);
    select.addEventListener("click", () => selectBrowserPath(entry.path));
    row.append(kind, name, open, select);
    entries.appendChild(row);
  }
}

function canSelectEntry(type) {
  const mode = state.browser?.mode || "any";
  return mode === "any" || mode === type || (mode === "dir" && type === "directory");
}

function selectBrowserPath(path) {
  const target = state.browser?.target;
  if (!target) return;
  const field = $(target);
  if (!field) return;
  if (state.browser?.append && field.tagName === "TEXTAREA") {
    const existing = field.value.trim();
    field.value = existing ? `${existing}\\n${path}` : path;
  } else {
    field.value = path;
  }
  closeBrowser();
  if (target === "root") {
    loadProjects().catch(showError);
  }
  if (target === "runProjectDir") {
    loadProject(path).catch(showError);
  }
}

function closeBrowser() {
  $("browserModal").hidden = true;
  $("newFolderName").value = "";
  state.browser = null;
}

async function createFolderFromBrowser() {
  const name = $("newFolderName").value.trim();
  const current = state.browser?.current?.path;
  if (!name || !current) return;
  const data = await api("/api/mkdir", {
    method: "POST",
    body: JSON.stringify({ path: current, name }),
  });
  $("newFolderName").value = "";
  state.browser.current = data;
  renderBrowser(data);
}

async function createProject(event) {
  event.preventDefault();
  setStatus("Creating");
  const payload = {
    root: $("root").value,
    startMode: $("initStartMode").value,
    seedDraftFile: $("initSeedDraft").value,
    slug: $("slug").value,
    title: $("title").value,
    topic: $("topic").value,
    researchQuestion: $("researchQuestion").value,
    brief: $("brief").value,
    data: $("initData").value,
    references: $("initReferences").value,
    models: collectRoutes("initModelRoutes"),
  };
  const result = await api("/api/init", { method: "POST", body: JSON.stringify(payload) });
  $("runProjectDir").value = result.projectDir;
  await loadProjects();
  renderProject(result.project);
  switchTab("run");
  setStatus("Created");
}

async function runProject(event) {
  event.preventDefault();
  setStatus("Running");
  const payload = {
    projectDir: $("runProjectDir").value,
    cycles: $("cycles").value,
    startMode: $("runStartMode").value,
    seedDraftFile: $("runSeedDraft").value,
    offline: $("offline").checked,
    reviewers: $("reviewers").value,
    data: $("runData").value,
    references: $("runReferences").value,
    smartLoader: $("smartLoader").value,
    loader: {
      pdfRenderPages: $("pdfRenderPages").checked,
      pdfMaxPages: $("pdfMaxPages").value,
      pdfDpi: $("pdfDpi").value,
      ocrAssets: $("ocrAssets").checked,
      ocrLanguage: $("ocrLanguage").value,
    },
    models: collectRoutes("runModelRoutes"),
  };
  const result = await api("/api/run", { method: "POST", body: JSON.stringify(payload) });
  renderProject(result.project);
  setStatus("Done");
}

function bind() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
  $("refreshBtn").addEventListener("click", async () => {
    setStatus("Refreshing");
    await loadCatalog();
    await loadProjects();
    if ($("runProjectDir").value) await loadProject($("runProjectDir").value);
    setStatus("Ready");
  });
  $("projectSelect").addEventListener("change", async (event) => {
    $("runProjectDir").value = event.target.value;
    await loadProject(event.target.value);
  });
  $("runProjectDir").addEventListener("change", async (event) => loadProject(event.target.value));
  $("initStartMode").addEventListener("change", updateRequiredMarkers);
  $("runStartMode").addEventListener("change", updateRequiredMarkers);
  document.querySelectorAll(".browse-btn").forEach((button) => {
    button.addEventListener("click", () => openPathBrowser(button).catch(showError));
  });
  $("browserClose").addEventListener("click", closeBrowser);
  $("browserHome").addEventListener("click", () => browseTo(state.catalog.home).catch(showError));
  $("browserWorkspace").addEventListener("click", () => browseTo(state.catalog.cwd).catch(showError));
  $("browserUp").addEventListener("click", () => browseTo(state.browser.current.parent).catch(showError));
  $("browserUseCurrent").addEventListener("click", () => selectBrowserPath(state.browser.current.path));
  $("browserPath").addEventListener("keydown", (event) => {
    if (event.key === "Enter") browseTo(event.target.value).catch(showError);
  });
  $("createFolderBtn").addEventListener("click", () => createFolderFromBrowser().catch(showError));
  $("newFolderName").addEventListener("keydown", (event) => {
    if (event.key === "Enter") createFolderFromBrowser().catch(showError);
  });
  $("initForm").addEventListener("submit", (event) => createProject(event).catch(showError));
  $("runForm").addEventListener("submit", (event) => runProject(event).catch(showError));
  updateRequiredMarkers();
}

function showError(error) {
  setStatus("Error");
  $("preview").textContent = error.message || String(error);
}

async function boot() {
  bind();
  await loadCatalog();
  await loadProjects();
}

boot().catch(showError);
"""
