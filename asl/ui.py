"""Small local web UI for configuring and running ASL projects."""

from __future__ import annotations

import json
import mimetypes
import tempfile
import threading
import time
import traceback
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

from . import __version__
from .catalog import catalog_payload
from .llm import LLMClient
from .pipeline import DEFAULT_REVIEWERS, DRAFT_PROMPT_BUDGET, PaperPipeline, init_project, init_project_at
from .reference_search import ReferenceSearchSettings
from .smart_loader import (
    PROMPT_CONTEXT_LIMIT,
    REFERENCE_CONTEXT_STRATEGIES,
    ReferenceContextSettings,
    SmartLoader,
    SmartLoaderSettings,
)
from .web_research import WebResearchSettings
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
    jobs: dict[str, _RunJob] = {}
    project_jobs: dict[str, str] = {}
    jobs_lock = threading.Lock()

    class ASLUIHandler(BaseHTTPRequestHandler):
        server_version = f"ASLUI/{__version__}"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
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
                if parsed.path.startswith("/api/jobs/"):
                    job_id = parsed.path.rsplit("/", 1)[-1]
                    with jobs_lock:
                        job = jobs.get(job_id)
                    if not job:
                        self._send_json({"error": "job not found"}, HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(job.snapshot())
                    return
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except Exception as exc:  # noqa: BLE001 - UI should return readable failures.
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = self._read_json()
                if parsed.path == "/api/init":
                    self._send_json(_create_project(payload, cwd))
                    return
                if parsed.path == "/api/run":
                    self._send_json(_start_run_job(payload, cwd, jobs, project_jobs, jobs_lock))
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
    title = _project_title(payload)
    project = init_project(
        root=root,
        slug=payload.get("slug") or None,
        title=title,
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


def _project_title(payload: dict) -> str:
    title = str(payload.get("title") or "").strip()
    if title:
        return title
    topic = str(payload.get("topic") or "").strip()
    if topic:
        return topic
    slug = str(payload.get("slug") or "").strip()
    if slug:
        return slug.replace("-", " ").replace("_", " ").title()
    return "Untitled Paper"


class _RunJob:
    def __init__(self, job_id: str, project_dir: Path) -> None:
        self.id = job_id
        self.project_dir = project_dir
        self.status = "queued"
        self.created_at = time.time()
        self.started_at: float | None = None
        self.finished_at: float | None = None
        self.progress: dict[str, object] = {"stage": "queued", "message": "Queued"}
        self.events: list[dict[str, object]] = []
        self.result: dict | None = None
        self.error: str | None = None
        self.traceback: str | None = None
        self._lock = threading.Lock()

    def mark_running(self) -> None:
        with self._lock:
            self.status = "running"
            self.started_at = time.time()
            self._append_event({"stage": "running", "message": "Run started"})

    def update(self, event: dict[str, object]) -> None:
        with self._lock:
            self.progress = dict(event)
            self._append_event(event)

    def finish(self, result: dict) -> None:
        with self._lock:
            self.status = "succeeded"
            self.finished_at = time.time()
            self.result = result
            self.progress = {"stage": "complete", "message": "Run complete"}
            self._append_event(self.progress)

    def fail(self, error: str, stack: str) -> None:
        with self._lock:
            self.status = "failed"
            self.finished_at = time.time()
            self.error = error
            self.traceback = stack
            self.progress = {"stage": "failed", "message": error}
            self._append_event(self.progress)

    def snapshot(self) -> dict:
        with self._lock:
            finished = self.finished_at or time.time()
            start = self.started_at or self.created_at
            return {
                "id": self.id,
                "projectDir": str(self.project_dir),
                "status": self.status,
                "createdAt": self.created_at,
                "startedAt": self.started_at,
                "finishedAt": self.finished_at,
                "elapsedSeconds": max(0, round(finished - start, 1)),
                "progress": dict(self.progress),
                "events": list(self.events[-30:]),
                "result": self.result,
                "error": self.error,
                "traceback": self.traceback,
            }

    def _append_event(self, event: dict[str, object]) -> None:
        self.events.append({"time": time.time(), **event})
        if len(self.events) > 80:
            self.events = self.events[-80:]


def _start_run_job(
    payload: dict,
    cwd: Path,
    jobs: dict[str, _RunJob],
    project_jobs: dict[str, str],
    jobs_lock: threading.Lock,
) -> dict:
    project_dir = _project_dir_from_payload(payload, cwd)
    project_key = str(project_dir)
    run_payload = dict(payload)
    with jobs_lock:
        existing_id = project_jobs.get(project_key)
        existing = jobs.get(existing_id or "")
        if existing and existing.status in {"queued", "running"}:
            return {"jobId": existing.id, "job": existing.snapshot(), "reused": True}
        if existing_id:
            project_jobs.pop(project_key, None)

        created_project = _ensure_project_for_run(project_dir, payload, cwd)
        if created_project:
            run_payload["_inputsPersistedInAutoProject"] = True
        job = _RunJob(uuid.uuid4().hex[:12], project_dir)
        jobs[job.id] = job
        project_jobs[project_key] = job.id
        if created_project:
            job.update({"stage": "project_create", "message": f"Created project at {project_dir}"})

    def worker() -> None:
        job.mark_running()
        try:
            result = _run_project(run_payload, cwd, progress=job.update)
        except Exception as exc:  # noqa: BLE001 - surfaced to the local UI.
            job.fail(str(exc), traceback.format_exc())
        else:
            job.finish(result)
        finally:
            with jobs_lock:
                if project_jobs.get(project_key) == job.id:
                    project_jobs.pop(project_key, None)

    thread = threading.Thread(target=worker, name=f"asl-run-{job.id}", daemon=True)
    thread.start()
    return {"jobId": job.id, "job": job.snapshot(), "reused": False}


def _run_project(payload: dict, cwd: Path, progress: Callable[[dict[str, object]], None] | None = None) -> dict:
    project_dir = _project_dir_from_payload(payload, cwd)
    created_project = False
    if not payload.get("_inputsPersistedInAutoProject"):
        created_project = _ensure_project_for_run(project_dir, payload, cwd)
    inputs_persisted = bool(payload.get("_inputsPersistedInAutoProject") or created_project)
    reviewers = tuple(_split_csv(payload.get("reviewers")) or DEFAULT_REVIEWERS)
    pipeline = PaperPipeline(
        project_dir,
        client=LLMClient(
            offline=bool(payload.get("offline")),
            allow_agent_tools=bool(payload.get("allowAgentTools")),
            allow_local_agents=_bool_setting(payload.get("allowLocalAgents"), True),
        ),
        data_paths=() if inputs_persisted else tuple(Path(path) for path in _split_paths(payload.get("data"))),
        reference_paths=() if inputs_persisted else tuple(Path(path) for path in _split_paths(payload.get("references"))),
        smart_loader_path=Path(payload["smartLoader"]) if payload.get("smartLoader") else None,
        smart_loader_settings=_loader_settings(payload.get("loader", {})),
        model_routes=_model_routes(payload.get("models", {})),
        start_mode=payload.get("startMode") or None,
        seed_draft_path=Path(payload["seedDraftFile"]) if payload.get("seedDraftFile") else None,
        web_research_settings=_web_research_settings(payload.get("webResearch", {})),
        reference_search_settings=_reference_search_settings(payload.get("referenceSearch", {})),
        from_version=payload.get("fromVersion") or None,
        additional_context=payload.get("additionalContext") or None,
        prompt_budget=_int_setting(payload.get("maxPromptChars"), DRAFT_PROMPT_BUDGET),
        reference_context_settings=_reference_context_settings(payload.get("referenceContext", {})),
        progress_callback=progress,
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
    manifest_path = _require_project_manifest(project_dir)

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
        "reference_search.md",
        "reference_search.json",
        "web_research.md",
        "web_research.json",
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


def _project_dir_from_payload(payload: dict, cwd: Path) -> Path:
    value = str(payload.get("projectDir") or "").strip()
    if not value:
        raise ValueError(
            "Project path is required. Enter a new papers/<slug> path to auto-create it, "
            "or select an existing paper project."
        )
    return _resolve_path(value, cwd)


def _ensure_project_for_run(project_dir: Path, payload: dict, cwd: Path) -> bool:
    manifest_path = project_dir / "project.json"
    if manifest_path.exists():
        return False
    if project_dir.exists():
        if not project_dir.is_dir():
            raise NotADirectoryError(f"Project path is not a folder: {project_dir}")
        if any(project_dir.iterdir()):
            raise FileNotFoundError(
                f"{project_dir} is not an ASL paper project because project.json is missing. "
                "Choose a new or empty project folder to auto-create, or use New Paper to configure it."
            )

    start_mode = _auto_project_start_mode(payload)
    title = _auto_project_title(project_dir, payload)
    topic = None if start_mode == "discover-topic" else title
    init_project_at(
        project_dir,
        title=title,
        topic=topic,
        brief=_auto_project_brief(start_mode),
        data_paths=tuple(Path(path) for path in _split_paths(payload.get("data"))),
        reference_paths=tuple(Path(path) for path in _split_paths(payload.get("references"))),
        model_routes=_model_routes(payload.get("models", {})),
        start_mode=start_mode,
        seed_draft_path=Path(payload["seedDraftFile"]) if payload.get("seedDraftFile") else None,
        input_root=cwd,
        allow_existing_empty=True,
    )
    return True


def _auto_project_start_mode(payload: dict) -> str:
    value = str(payload.get("startMode") or "").strip()
    if value:
        return value
    if payload.get("seedDraftFile"):
        return "rewrite"
    return "from-scratch"


def _auto_project_title(project_dir: Path, payload: dict) -> str:
    seed_draft = payload.get("seedDraftFile")
    if seed_draft:
        inferred = _infer_seed_draft_title(Path(seed_draft), payload)
        if inferred:
            return inferred
    return _title_from_project_path(project_dir)


def _infer_seed_draft_title(seed_draft: Path, payload: dict) -> str | None:
    if not seed_draft.exists():
        return None
    text_suffixes = {".md", ".markdown", ".txt", ".tex", ".rst"}
    if seed_draft.suffix.lower() in text_suffixes:
        try:
            title = _title_from_markdownish_text(read_text(seed_draft))
        except UnicodeDecodeError:
            title = None
        if title:
            return title

    try:
        loader_settings = _loader_settings(payload.get("loader", {}))
        title_settings = SmartLoaderSettings(
            pdf_render_pages=False,
            pdf_max_pages=loader_settings.pdf_max_pages,
            pdf_dpi=loader_settings.pdf_dpi,
            ocr_assets=False,
            ocr_language=loader_settings.ocr_language,
        )
        loader = SmartLoader(
            Path(payload["smartLoader"]) if payload.get("smartLoader") else None,
            settings=title_settings,
        )
        with tempfile.TemporaryDirectory(prefix="asl-seed-title-") as tmp:
            group = loader.load_group("seed_draft", [seed_draft], Path(tmp))
    except Exception:
        return None
    return _title_from_loaded_seed_group(group)


def _title_from_loaded_seed_group(group: object) -> str | None:
    results = getattr(group, "results", ())
    for result in results:
        if not isinstance(result, dict):
            continue
        for document in result.get("documents", []):
            if not isinstance(document, dict):
                continue
            for candidate in (
                document.get("title"),
                _pdf_metadata_title(document),
                _title_from_markdownish_text(str(document.get("markdown") or document.get("text") or "")),
            ):
                title = _clean_title(candidate)
                if title:
                    return title
    return None


def _pdf_metadata_title(document: dict) -> object:
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        return None
    info = metadata.get("info")
    if isinstance(info, dict):
        return info.get("Title")
    return None


def _title_from_markdownish_text(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines()[:80] if line.strip()]
    for line in lines:
        if line.startswith("#"):
            return _clean_title(line.lstrip("#").strip())
    for line in lines[:12]:
        title = _clean_title(line)
        if title and len(title) >= 8:
            return title
    return None


def _title_from_project_path(project_dir: Path) -> str:
    name = project_dir.name.replace("-", " ").replace("_", " ").strip()
    return name.title() if name else "Untitled Paper"


def _clean_title(value: object) -> str | None:
    title = " ".join(str(value or "").strip().split())
    if not title:
        return None
    title = title.strip("#:;,- ")
    if not title or title.lower() in {"untitled", "loaded seed draft"}:
        return None
    return title[:220]


def _auto_project_brief(start_mode: str) -> str:
    if start_mode == "discover-topic":
        return (
            "Identify a viable academic paper topic from the supplied data and references. "
            "Do not fabricate citations or results; mark missing evidence as TODO."
        )
    if start_mode == "rewrite":
        return (
            "Rewrite and improve the supplied draft using the supplied data and references. "
            "Do not fabricate citations or results; mark missing evidence as TODO."
        )
    return (
        "Write a rigorous academic paper using the supplied data and references. "
        "Do not fabricate citations or results; mark missing evidence as TODO."
    )


def _require_project_manifest(project_dir: Path) -> Path:
    manifest_path = project_dir / "project.json"
    help_text = (
        "Click Run with a new or empty project path to auto-create it, or choose an "
        "existing papers/<slug> folder that contains project.json."
    )
    if not project_dir.exists():
        raise FileNotFoundError(f"Paper project not found: {project_dir}. {help_text}")
    if not project_dir.is_dir():
        raise NotADirectoryError(f"Project path is not a folder: {project_dir}. {help_text}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Paper project manifest is missing: {manifest_path}. {help_text}")
    return manifest_path


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


def _web_research_settings(payload: object) -> WebResearchSettings:
    if not isinstance(payload, dict):
        payload = {}
    return WebResearchSettings(
        enabled=_bool_setting(payload.get("enabled"), False),
        max_queries=_int_setting(payload.get("maxQueries"), 3),
        max_results_per_query=_int_setting(payload.get("maxResultsPerQuery"), 5),
    )


def _reference_search_settings(payload: object) -> ReferenceSearchSettings:
    if not isinstance(payload, dict):
        payload = {}
    return ReferenceSearchSettings(
        enabled=_bool_setting(payload.get("enabled"), False),
        max_results=_int_setting(payload.get("maxResults"), 8),
    )


def _reference_context_settings(payload: object) -> ReferenceContextSettings:
    if not isinstance(payload, dict):
        payload = {}
    strategy = str(payload.get("strategy") or "select").strip().lower()
    if strategy not in REFERENCE_CONTEXT_STRATEGIES:
        strategy = "select"
    return ReferenceContextSettings(
        strategy=strategy,
        limit=_int_setting(payload.get("chars"), PROMPT_CONTEXT_LIMIT),
        full_count=_int_setting(payload.get("fullCount"), 6),
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
          <span class="field-note">Choose an existing project, or enter a new/empty path and Run will auto-create it.</span>
        </label>
        <div class="inline-fields">
          <label>Iterations
            <input id="cycles" name="cycles" type="number" min="1" value="1">
            <span class="field-note">1 iteration creates 1 new version.</span>
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
              <input id="runSeedDraft" placeholder="path/to/draft.md/pdf/docx">
              <button type="button" class="browse-btn" data-target="runSeedDraft" data-mode="file">Browse</button>
            </div>
          </label>
        </div>
        <div class="inline-fields">
          <label>Start from version
            <select id="fromVersion">
              <option value="">Latest accepted</option>
            </select>
            <span class="field-note">Override the baseline draft for this run.</span>
          </label>
          <label>Max prompt chars
            <input id="maxPromptChars" type="number" min="5000" value="20000">
          </label>
        </div>
        <div class="inline-fields">
          <label>Reference strategy
            <select id="referenceContextStrategy">
              <option value="select">select — top-N full + rest summarized</option>
              <option value="balanced">balanced — even share across all</option>
              <option value="full">full — all references, raise the chars limit</option>
            </select>
            <span class="field-note">How loaded references are fitted into the prompt.</span>
          </label>
          <label>Reference context chars
            <input id="referenceContextChars" type="number" min="2000" value="24000">
            <span class="field-note">For full: raise this to fit more (grows the prompt).</span>
          </label>
          <label>Full references (select)
            <input id="referenceContextFull" type="number" min="1" value="6">
          </label>
        </div>
        <label>Focus guidance
          <textarea id="focusGuidance" rows="3" placeholder="Additional context or direction for the next draft..."></textarea>
        </label>
        <label class="checkline">
          <input id="offline" name="offline" type="checkbox">
          Offline
        </label>
        <div class="check-grid">
          <label class="checkline">
            <input id="webResearch" type="checkbox">
            Web research
          </label>
          <label class="checkline">
            <input id="referenceSearch" type="checkbox">
            Reference search
          </label>
          <label class="checkline">
            <input id="allowAgentTools" type="checkbox">
            Agent web/tools
          </label>
          <label class="checkline" title="Allow Claude Code and Codex subprocess providers">
            <input id="allowLocalAgents" type="checkbox" checked>
            Terminal providers
          </label>
        </div>
        <div class="inline-fields compact-fields">
          <label>Search queries
            <input id="webResearchMaxQueries" type="number" min="1" value="3">
          </label>
          <label>Results/query
            <input id="webResearchMaxResults" type="number" min="1" value="5">
          </label>
          <label>Max references
            <input id="referenceSearchMaxResults" type="number" min="1" value="8">
          </label>
        </div>
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
            <input id="smartLoader" placeholder="optional override; built-in by default">
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
        <button id="runButton" class="primary" type="submit">Run</button>
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
              <input id="initSeedDraft" placeholder="path/to/draft.md/pdf/docx">
              <button type="button" class="browse-btn" data-target="initSeedDraft" data-mode="file">Browse</button>
            </div>
          </label>
        </div>
        <div class="inline-fields">
          <label>Slug
            <input id="slug" autocomplete="off">
          </label>
          <label>Title
            <input id="title" autocomplete="off">
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
      <div id="runFeedback" class="run-feedback" hidden>
        <div class="run-feedback-head">
          <strong id="runFeedbackTitle">Pipeline run</strong>
          <span id="runFeedbackMeta"></span>
        </div>
        <div class="progress-track" aria-hidden="true"><div id="runProgressBar"></div></div>
        <div id="runFeedbackMessage" class="run-message"></div>
        <ol id="runEvents" class="run-events"></ol>
      </div>
      <div id="projectSummary" class="summary"></div>
      <div id="fileTabs" class="file-tabs"></div>
      <pre id="preview"></pre>
    </section>
  </main>

  <div id="browserModal" class="modal" hidden>
    <div class="modal-panel path-browser-panel" role="dialog" aria-modal="true" aria-labelledby="browserTitle">
      <div class="modal-head">
        <h2 id="browserTitle">Browse</h2>
        <button id="browserClose" class="quiet-button" type="button">Close</button>
      </div>
      <div class="browser-path-row">
        <button id="browserBack" class="nav-button" type="button" title="Back" aria-label="Back">&lt;</button>
        <button id="browserForward" class="nav-button" type="button" title="Forward" aria-label="Forward">&gt;</button>
        <button id="browserUp" class="nav-button wide" type="button" title="Parent folder">Up</button>
        <input id="browserPath" class="browser-path" autocomplete="off" aria-label="Current path">
      </div>
      <div class="browser-shortcuts">
        <button id="browserHome" type="button">Home</button>
        <button id="browserWorkspace" type="button">Workspace</button>
      </div>
      <div id="browserEntries" class="browser-entries"></div>
      <div class="browser-footer">
        <div class="mkdir-row">
          <input id="newFolderName" placeholder="New folder">
          <button id="createFolderBtn" type="button">Create</button>
        </div>
        <div class="browser-actions">
          <button id="browserCancel" type="button">Cancel</button>
          <button id="browserUseCurrent" class="browser-primary" type="button">Choose Current</button>
        </div>
      </div>
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
button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

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

.field-note {
  color: var(--muted);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.3;
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

.compact-fields label {
  margin-top: 4px;
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

.check-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
  margin: 4px 0 0;
}

.check-grid .checkline {
  margin: 6px 0;
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

.run-feedback {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  padding: 12px;
  margin-bottom: 14px;
  display: grid;
  gap: 10px;
}

.run-feedback[hidden] {
  display: none;
}

.run-feedback-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.run-feedback-head strong {
  font-size: 13px;
}

#runFeedbackMeta {
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
}

.progress-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1ec;
}

#runProgressBar {
  width: 0%;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 180ms ease;
}

.run-message {
  color: var(--ink);
  font-size: 13px;
}

.run-events {
  margin: 0;
  padding: 0;
  display: grid;
  gap: 5px;
  list-style: none;
  max-height: 160px;
  overflow: auto;
}

.run-events li {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 8px;
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}

.run-events .event-stage {
  color: var(--accent-strong);
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
  color: var(--muted);
}

.model-summary {
  border-top: 1px solid var(--line);
  margin-top: 4px;
  padding-top: 10px;
  color: var(--ink);
}

.model-summary ul {
  display: grid;
  gap: 5px;
  margin: 6px 0 0;
  padding-left: 18px;
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1.35;
  overflow-wrap: anywhere;
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
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 24px 80px rgb(32 35 31 / 24%);
}

.path-browser-panel {
  width: min(820px, calc(100vw - 32px));
  padding: 0;
  gap: 0;
}

.modal-head, .mkdir-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.modal-head {
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}

.quiet-button {
  padding: 6px 10px;
  color: var(--muted);
}

.browser-path-row {
  display: grid;
  grid-template-columns: auto auto auto minmax(0, 1fr);
  gap: 6px;
  align-items: center;
  padding: 12px 16px 8px;
}

.nav-button {
  width: 34px;
  min-width: 34px;
  padding: 7px 0;
  text-align: center;
}

.nav-button.wide {
  width: auto;
  padding-inline: 10px;
}

.browser-path {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  min-height: 34px;
}

.browser-shortcuts {
  display: flex;
  gap: 6px;
  padding: 0 16px 12px;
  border-bottom: 1px solid var(--line);
}

.browser-shortcuts button {
  padding: 5px 9px;
  color: var(--muted);
  font-size: 12px;
}

.mkdir-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  min-width: 0;
}

.mkdir-row input {
  min-height: 34px;
  font-size: 13px;
}

.mkdir-row button {
  padding-block: 6px;
}

.browser-footer {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--line);
  background: #fbfcf9;
}

.browser-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  align-items: center;
}

.browser-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 650;
}

.browser-primary:hover {
  background: var(--accent-strong);
}

.browser-entries {
  overflow: auto;
  border: 0;
  border-radius: 0;
  min-height: 260px;
}

.browser-entry {
  display: grid;
  grid-template-columns: 78px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-height: 36px;
  padding: 6px 16px;
  border-bottom: 1px solid var(--line);
}

.browser-entry:hover {
  background: #f8faf6;
}

.browser-entry[data-special="parent"] {
  background: #fbfcf9;
}

.browser-entry:last-child {
  border-bottom: 0;
}

.entry-name {
  width: 100%;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  padding: 3px 0;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}

.entry-name:hover {
  border-color: transparent;
}

.entry-name.can-open,
.entry-name.can-select {
  cursor: pointer;
}

.entry-name.can-open {
  color: var(--accent-strong);
  font-weight: 700;
}

.entry-name.can-open:hover,
.entry-name.can-select:hover {
  text-decoration: underline;
}

.entry-action {
  border: 0;
  background: transparent;
  color: var(--accent-strong);
  padding: 3px 6px;
  font-size: 12px;
  font-weight: 650;
}

.entry-action:hover {
  background: var(--soft);
  border-color: transparent;
}

.entry-kind {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.browser-empty {
  padding: 18px;
  color: var(--muted);
  font-size: 13px;
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
  .inline-fields, .route-row, .path-field { grid-template-columns: 1fr; }
  .compact-fields { grid-template-columns: 1fr 1fr; }
  .check-grid { grid-template-columns: 1fr; }
  .browser-path-row { grid-template-columns: auto auto auto minmax(0, 1fr); }
  .browser-entry { grid-template-columns: 62px minmax(0, 1fr) auto; }
  .route-row span { padding-bottom: 0; }
  .secondary { width: 100%; }
  pre { height: 50vh; }
}

@media (max-width: 560px) {
  .browser-footer { grid-template-columns: 1fr; }
  .browser-actions { justify-content: stretch; }
  .browser-actions button { flex: 1; }
}
"""


_APP_JS = """
const state = {
  catalog: null,
  projects: [],
  currentProject: null,
  latestFiles: {},
  browser: null,
  activeRunJobId: null,
  runPollTimer: null,
};

const $ = (id) => document.getElementById(id);

const RUN_STAGE_PROGRESS = {
  queued: 0,
  project_create: 1,
  running: 2,
  seed_baseline: 2,
  seed_baseline_complete: 3,
  cycle_start: 4,
  version_prepare: 7,
  previous_draft: 10,
  seed_draft: 13,
  inputs: 18,
  topic_discovery: 28,
  reference_search: 32,
  web_research: 36,
  prompt_record: 42,
  plan: 50,
  draft: 62,
  review: 75,
  revision: 84,
  quality_gate: 91,
  metadata: 96,
  cycle_complete: 99,
  complete: 100,
  failed: 100,
};

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

function setRunControls(running) {
  const button = $("runButton");
  if (!button) return;
  button.disabled = running;
  button.textContent = running ? "Running..." : "Run";
}

function runProgressPercent(job) {
  if (!job) return 0;
  if (job.status === "succeeded") return 100;
  const progress = job.progress || {};
  const stagePercent = RUN_STAGE_PROGRESS[progress.stage] ?? 5;
  const cycle = Math.max(1, Number(progress.cycle || 1));
  const total = Math.max(1, Number(progress.total_cycles || 1));
  return Math.max(0, Math.min(100, ((cycle - 1) * 100 + stagePercent) / total));
}

function renderRunJob(job) {
  if (!job) return;
  const panel = $("runFeedback");
  panel.hidden = false;
  const progress = job.progress || {};
  const cycle = progress.cycle && progress.total_cycles ? `iteration ${progress.cycle}/${progress.total_cycles}` : job.status;
  const version = progress.version ? ` · ${progress.version}` : "";
  const elapsed = typeof job.elapsedSeconds === "number" ? `${job.elapsedSeconds.toFixed(1)}s` : "";
  $("runFeedbackTitle").textContent = `Pipeline ${job.status}`;
  $("runFeedbackMeta").textContent = `${cycle}${version} · ${elapsed} · ${job.id}`;
  $("runProgressBar").style.width = `${runProgressPercent(job)}%`;
  $("runFeedbackMessage").textContent = progress.message || job.error || "Working";

  const events = $("runEvents");
  events.innerHTML = "";
  for (const event of (job.events || []).slice(-12).reverse()) {
    const item = document.createElement("li");
    const stage = document.createElement("span");
    stage.className = "event-stage";
    stage.textContent = `${eventStageLabel(event.stage)}:`;
    const message = document.createElement("span");
    message.textContent = event.message || "";
    item.append(stage, message);
    events.appendChild(item);
  }
}

function eventStageLabel(stage) {
  return String(stage || "stage").replaceAll("_", " ").replace(/^cycle\\b/, "iteration");
}

function stopRunPolling() {
  if (state.runPollTimer) {
    clearTimeout(state.runPollTimer);
    state.runPollTimer = null;
  }
}

async function pollRunJob(jobId) {
  const job = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
  if (state.activeRunJobId !== jobId) return;
  renderRunJob(job);
  if (job.status === "queued" || job.status === "running") {
    state.runPollTimer = setTimeout(() => {
      pollRunJob(jobId).catch((error) => {
        stopRunPolling();
        state.activeRunJobId = null;
        setRunControls(false);
        showError(error);
      });
    }, 1000);
    return;
  }
  stopRunPolling();
  state.activeRunJobId = null;
  setRunControls(false);
  if (job.status === "succeeded") {
    if (job.result?.project) {
      $("runProjectDir").value = job.result.project.path;
      await loadProjects();
      $("projectSelect").value = job.result.project.path;
      renderProject(job.result.project);
    }
    setStatus("Done");
    return;
  }
  setStatus("Error");
  $("preview").textContent = job.traceback || job.error || "Pipeline failed";
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
  try {
    state.currentProject = await api(`/api/project?projectDir=${encodeURIComponent(projectDir)}`);
    renderProject(state.currentProject);
  } catch (error) {
    if (isMissingProjectError(error)) {
      state.currentProject = null;
      renderPendingProject(projectDir);
      setStatus("Ready");
      return;
    }
    throw error;
  }
}

function populateFromVersion(project) {
  const select = $("fromVersion");
  const current = select.value;
  select.innerHTML = '<option value="">Latest accepted</option>';
  for (const version of (project.versions || [])) {
    const option = document.createElement("option");
    option.value = version.name;
    const meta = version.metadata || {};
    const score = meta.quality_score != null ? ` · score ${meta.quality_score}` : "";
    option.textContent = `${version.name}${score}`;
    select.appendChild(option);
  }
  if (current && [...select.options].some((o) => o.value === current)) {
    select.value = current;
  }
}

function renderProject(project) {
  const manifest = project.manifest || {};
  const latest = project.latest || {};
  state.latestFiles = latest.files || {};
  const summary = $("projectSummary");
  summary.innerHTML = "";
  const titleLine = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = manifest.title || "Untitled";
  titleLine.appendChild(title);
  summary.appendChild(titleLine);
  for (const text of [
    manifest.topic || "",
    project.path,
    `${project.versions.length} version(s)`,
    `Accepted: ${project.acceptedVersion || "none yet"}`,
  ]) {
    const line = document.createElement("div");
    line.textContent = text;
    summary.appendChild(line);
  }
  if (latest.htmlIndex) {
    const htmlLine = document.createElement("div");
    htmlLine.append("HTML: ");
    const code = document.createElement("code");
    code.textContent = latest.htmlIndex;
    htmlLine.appendChild(code);
    summary.appendChild(htmlLine);
  }
  const modelSummary = renderModelSummary(latest);
  if (modelSummary) summary.appendChild(modelSummary);
  populateFromVersion(project);
  renderFileTabs();
}

function renderModelSummary(latest) {
  const metadata = parseJsonFile(latest?.files?.["metadata.json"] || latest?.files?.metadata);
  const models = metadata?.models;
  if (!models) return null;
  const box = document.createElement("div");
  box.className = "model-summary";
  const heading = document.createElement("strong");
  heading.textContent = "Model usage";
  box.appendChild(heading);
  const list = document.createElement("ul");
  for (const line of modelUsageLines(models)) {
    const item = document.createElement("li");
    item.textContent = line;
    list.appendChild(item);
  }
  box.appendChild(list);
  return box;
}

function modelUsageLines(models) {
  const requested = models.requested || {};
  const used = models.used || {};
  const lines = [];
  for (const role of ["plan", "draft", "review", "revision", "score"]) {
    const requestedLine = (requested[role] || []).join(", ") || "default";
    const usedValue = used[role] || (role === "review" ? used.reviews : null);
    lines.push(`${role}: requested ${requestedLine}; ${formatUsedModel(usedValue)}`);
  }
  return lines;
}

function formatUsedModel(value) {
  if (!value) return "not run";
  if (Array.isArray(value)) {
    if (!value.length) return "not run";
    return value.map((item) => formatSingleModel(item)).join(" | ");
  }
  if (typeof value === "object" && !("provider" in value) && !("model" in value)) {
    const entries = Object.entries(value);
    if (!entries.length) return "not run";
    return entries.map(([name, item]) => `${name} ${formatSingleModel(item)}`).join(" | ");
  }
  return formatSingleModel(value);
}

function formatSingleModel(item) {
  if (!item || typeof item !== "object") return "not run";
  const provider = item.provider || "unknown";
  const model = item.model || "unknown";
  const attempts = Array.isArray(item.attempts) && item.attempts.length
    ? `; attempts: ${item.attempts.join(" ; ")}`
    : "";
  const verdict = item.verdict ? `; verdict: ${item.verdict}` : "";
  return `used ${provider}:${model}${verdict}${attempts}`;
}

function parseJsonFile(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function renderPendingProject(projectDir) {
  state.latestFiles = {};
  const summary = $("projectSummary");
  summary.innerHTML = "";
  for (const text of [
    "New project",
    projectDir,
    "Will be created automatically when you click Run.",
  ]) {
    const line = document.createElement("div");
    if (text === "New project") {
      const strong = document.createElement("strong");
      strong.textContent = text;
      line.appendChild(strong);
    } else {
      line.textContent = text;
    }
    summary.appendChild(line);
  }
  renderFileTabs();
}

function isMissingProjectError(error) {
  const message = error?.message || String(error);
  return message.includes("Paper project not found") || message.includes("Paper project manifest is missing");
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
  const mode = button.dataset.mode || "any";
  state.browser = {
    target,
    mode,
    append: button.dataset.append === "true",
    history: [],
    historyIndex: -1,
  };
  const titleByMode = {
    file: "Choose File",
    dir: "Choose Folder",
    any: "Choose Path",
  };
  $("browserTitle").textContent = titleByMode[mode] || "Choose Path";
  $("browserUseCurrent").textContent = state.browser.append ? "Add Current" : "Choose Current";
  $("browserModal").hidden = false;
  await browseTo(fieldPathValue(target, state.browser.append));
}

function pushBrowserHistory(path) {
  if (!state.browser) state.browser = {};
  const history = state.browser.history || [];
  const index = Number.isInteger(state.browser.historyIndex) ? state.browser.historyIndex : history.length - 1;
  const nextHistory = history.slice(0, index + 1);
  if (nextHistory[nextHistory.length - 1] !== path) nextHistory.push(path);
  state.browser.history = nextHistory;
  state.browser.historyIndex = nextHistory.length - 1;
}

async function fetchBrowserPath(path) {
  return api(`/api/browse?path=${encodeURIComponent(path || state.catalog.cwd)}`);
}

async function browseTo(path, options = {}) {
  const data = await fetchBrowserPath(path);
  if (!state.browser) state.browser = {};
  state.browser.current = data;
  if (options.record !== false) pushBrowserHistory(data.path);
  renderBrowser(data);
}

async function browseHistory(offset) {
  const history = state.browser?.history || [];
  const index = Number.isInteger(state.browser?.historyIndex) ? state.browser.historyIndex : -1;
  const nextIndex = index + offset;
  if (nextIndex < 0 || nextIndex >= history.length) return;
  const data = await fetchBrowserPath(history[nextIndex]);
  state.browser.current = data;
  state.browser.historyIndex = nextIndex;
  renderBrowser(data);
}

function renderBrowser(data) {
  $("browserPath").value = data.path;
  $("browserBack").disabled = (state.browser?.historyIndex || 0) <= 0;
  $("browserForward").disabled = (state.browser?.historyIndex || 0) >= (state.browser?.history || []).length - 1;
  $("browserUp").disabled = !data.parent;
  $("browserUseCurrent").disabled = state.browser?.mode === "file";
  const entries = $("browserEntries");
  entries.innerHTML = "";
  if (data.parent) {
    appendBrowserEntry(entries, {
      name: "..",
      path: data.parent,
      type: "directory",
    }, { kind: "Parent", special: "parent" });
  }
  for (const entry of data.entries) {
    appendBrowserEntry(entries, entry);
  }
  if (data.entries.length === 0) {
    const empty = document.createElement("div");
    empty.className = "browser-empty";
    empty.textContent = "No files or folders";
    entries.appendChild(empty);
  }
}

function appendBrowserEntry(container, entry, options = {}) {
  const row = document.createElement("div");
  row.className = "browser-entry";
  row.dataset.type = entry.type;
  row.dataset.name = entry.name;
  if (options.special) row.dataset.special = options.special;
  const kind = document.createElement("span");
  kind.className = "entry-kind";
  kind.textContent = options.kind || (entry.type === "directory" ? "Folder" : "File");
  const name = document.createElement("button");
  name.type = "button";
  name.className = "entry-name";
  name.textContent = entry.type === "directory" && entry.name !== ".." ? `${entry.name}/` : entry.name;
  if (entry.type === "directory") {
    name.classList.add("can-open");
    name.addEventListener("click", () => browseTo(entry.path).catch(showError));
  } else if (canSelectEntry(entry.type)) {
    name.classList.add("can-select");
    name.addEventListener("click", () => selectBrowserPath(entry.path));
  }
  const action = document.createElement("button");
  action.type = "button";
  action.className = "entry-action";
  action.textContent = "Choose";
  const canChoose = !options.special && canSelectEntry(entry.type);
  action.hidden = !canChoose;
  action.addEventListener("click", () => selectBrowserPath(entry.path));
  row.append(kind, name, action);
  container.appendChild(row);
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
  pushBrowserHistory(data.path);
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
  stopRunPolling();
  setRunControls(true);
  setStatus("Queued");
  const payload = {
    projectDir: $("runProjectDir").value,
    cycles: $("cycles").value,
    startMode: $("runStartMode").value,
    seedDraftFile: $("runSeedDraft").value,
    fromVersion: $("fromVersion").value,
    additionalContext: $("focusGuidance").value,
    maxPromptChars: $("maxPromptChars").value,
    referenceContext: {
      strategy: $("referenceContextStrategy").value,
      chars: $("referenceContextChars").value,
      fullCount: $("referenceContextFull").value,
    },
    offline: $("offline").checked,
    allowAgentTools: $("allowAgentTools").checked,
    allowLocalAgents: $("allowLocalAgents").checked,
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
    webResearch: {
      enabled: $("webResearch").checked,
      maxQueries: $("webResearchMaxQueries").value,
      maxResultsPerQuery: $("webResearchMaxResults").value,
    },
    referenceSearch: {
      enabled: $("referenceSearch").checked,
      maxResults: $("referenceSearchMaxResults").value,
    },
    models: collectRoutes("runModelRoutes"),
  };
  try {
    const result = await api("/api/run", { method: "POST", body: JSON.stringify(payload) });
    state.activeRunJobId = result.jobId;
    renderRunJob(result.job);
    setStatus(result.reused ? "Already running" : "Running");
    await pollRunJob(result.jobId);
  } catch (error) {
    setRunControls(false);
    throw error;
  }
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
  $("browserCancel").addEventListener("click", closeBrowser);
  $("browserHome").addEventListener("click", () => browseTo(state.catalog.home).catch(showError));
  $("browserWorkspace").addEventListener("click", () => browseTo(state.catalog.cwd).catch(showError));
  $("browserBack").addEventListener("click", () => browseHistory(-1).catch(showError));
  $("browserForward").addEventListener("click", () => browseHistory(1).catch(showError));
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
