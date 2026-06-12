"""Command-line interface for Academic Sludge Line."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .llm import LLMClient
from .pipeline import DEFAULT_REVIEWERS, START_MODES, PaperPipeline, init_project
from .smart_loader import SmartLoaderSettings
from .web_research import WebResearchSettings
from .workspace import read_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asl",
        description="Versioned academic drafting pipeline with review-and-revision loops.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a new paper workspace")
    init.add_argument("--root", default=".", help="repository root")
    init.add_argument("--slug", help="paper slug")
    init.add_argument("--title", required=True, help="paper title")
    init.add_argument("--topic", help="short topic description")
    init.add_argument("--research-question", help="custom research question")
    init.add_argument(
        "--start-mode",
        choices=START_MODES,
        default="from-scratch",
        help="paper starting mode",
    )
    init.add_argument("--seed-draft-file", type=Path, help="existing draft to rewrite")
    init.add_argument("--brief-file", type=Path, help="markdown topic brief")
    init.add_argument("--brief", help="inline topic brief")
    init.add_argument("--model", help="default model route to store for this paper")
    init.add_argument("--data", action="append", type=Path, default=[], help="data file or directory to load")
    _add_model_route_args(init, persist=True)
    init.add_argument(
        "--references",
        "--reference",
        action="append",
        type=Path,
        default=[],
        help="reference file or directory to load",
    )

    run = sub.add_parser("run", help="run one or more drafting cycles")
    run.add_argument("project_dir", type=Path, help="path to papers/<slug>")
    run.add_argument("--cycles", type=int, default=1, help="number of versions to create")
    run.add_argument("--offline", action="store_true", help="force template-only mode")
    run.add_argument(
        "--allow-agent-tools",
        action="store_true",
        help="allow Claude Code/Codex local providers to use configured tools such as web search",
    )
    run.add_argument(
        "--web-research",
        action="store_true",
        help="run an auditable web-research stage before planning and drafting",
    )
    run.add_argument("--web-research-max-queries", type=int, default=3, help="maximum generated web research queries")
    run.add_argument("--web-research-max-results", type=int, default=5, help="maximum web research results per query")
    run.add_argument("--start-mode", choices=START_MODES, help="override paper starting mode")
    run.add_argument("--seed-draft-file", type=Path, help="existing draft to rewrite")
    run.add_argument("--model", help="default model route for this run")
    _add_model_route_args(run, persist=False)
    run.add_argument("--data", action="append", type=Path, default=[], help="additional data file or directory to load")
    run.add_argument(
        "--references",
        "--reference",
        action="append",
        type=Path,
        default=[],
        help="additional reference file or directory to load",
    )
    run.add_argument(
        "--smart-loader",
        type=Path,
        help="path to smart-loader CLI, dist/cli.js, or repository",
    )
    _add_loader_args(run)
    run.add_argument(
        "--reviewers",
        default=",".join(DEFAULT_REVIEWERS),
        help="comma-separated reviewer personas",
    )

    ui = sub.add_parser("ui", help="start the local web UI")
    ui.add_argument("--host", default="127.0.0.1", help="host to bind")
    ui.add_argument("--port", type=int, default=8765, help="port to bind")
    ui.add_argument("--open", action="store_true", help="open the UI in the default browser")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        if args.start_mode != "discover-topic" and not args.topic:
            parser.error("--topic is required unless --start-mode discover-topic is used")
        brief = _load_brief(args.brief_file, args.brief)
        project_dir = init_project(
            root=Path(args.root),
            title=args.title,
            topic=args.topic,
            brief=brief,
            slug=args.slug,
            research_question=args.research_question,
            data_paths=tuple(args.data),
            reference_paths=tuple(args.references),
            model_routes=_model_routes_from_args(args),
            start_mode=args.start_mode,
            seed_draft_path=args.seed_draft_file,
        )
        print(project_dir)
        return 0

    if args.command == "run":
        reviewers = tuple(r.strip() for r in args.reviewers.split(",") if r.strip())
        pipeline = PaperPipeline(
            args.project_dir,
            client=LLMClient(offline=args.offline, model=args.model, allow_agent_tools=args.allow_agent_tools),
            data_paths=tuple(args.data),
            reference_paths=tuple(args.references),
            smart_loader_path=args.smart_loader,
            smart_loader_settings=_loader_settings_from_args(args),
            model_routes=_model_routes_from_args(args),
            start_mode=args.start_mode,
            seed_draft_path=args.seed_draft_file,
            web_research_settings=_web_research_settings_from_args(args),
        )
        created = pipeline.run(cycles=args.cycles, reviewers=reviewers)
        for path in created:
            print(path)
        return 0

    if args.command == "ui":
        from .ui import run_ui

        run_ui(host=args.host, port=args.port, open_browser=args.open)
        return 0

    parser.error("unknown command")
    return 2


def _load_brief(brief_file: Path | None, inline: str | None) -> str:
    if brief_file:
        return read_text(brief_file)
    if inline:
        return inline
    return "No brief provided yet. Add sources, scope, and intended evidence before drafting."


def _add_model_route_args(parser: argparse.ArgumentParser, persist: bool) -> None:
    scope = "store project default" if persist else "override this run"
    parser.add_argument("--plan-model", help=f"model route for research planning ({scope})")
    parser.add_argument("--draft-model", help=f"model route for drafting ({scope})")
    parser.add_argument("--review-model", help=f"model route for reviewer reports ({scope})")
    parser.add_argument("--revision-model", help=f"model route for revision planning ({scope})")
    parser.add_argument("--score-model", help=f"model route(s) for quality scoring ({scope})")


def _add_loader_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-pdf-render-pages", action="store_true", help="disable PDF page image extraction")
    parser.add_argument("--pdf-max-pages", type=int, default=25, help="maximum PDF pages to render as images")
    parser.add_argument("--pdf-dpi", type=int, default=180, help="DPI for rendered PDF page images")
    parser.add_argument("--no-ocr-assets", action="store_true", help="disable OCR for extracted images when tesseract is available")
    parser.add_argument("--ocr-language", default="eng", help="tesseract OCR language")


def _model_routes_from_args(args: argparse.Namespace) -> dict[str, str]:
    routes = {}
    if getattr(args, "model", None):
        routes["default"] = args.model
    for role in ("plan", "draft", "review", "revision", "score"):
        value = getattr(args, f"{role}_model", None)
        if value:
            routes[role] = value
    return routes


def _loader_settings_from_args(args: argparse.Namespace) -> SmartLoaderSettings:
    return SmartLoaderSettings(
        pdf_render_pages=not getattr(args, "no_pdf_render_pages", False),
        pdf_max_pages=getattr(args, "pdf_max_pages", 25),
        pdf_dpi=getattr(args, "pdf_dpi", 180),
        ocr_assets=not getattr(args, "no_ocr_assets", False),
        ocr_language=getattr(args, "ocr_language", "eng"),
    )


def _web_research_settings_from_args(args: argparse.Namespace) -> WebResearchSettings:
    return WebResearchSettings(
        enabled=bool(getattr(args, "web_research", False)),
        max_queries=getattr(args, "web_research_max_queries", 3),
        max_results_per_query=getattr(args, "web_research_max_results", 5),
    )


if __name__ == "__main__":
    raise SystemExit(main())
