"""Command-line interface for Academic Sludge Line."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .llm import LLMClient
from .pipeline import DEFAULT_REVIEWERS, PaperPipeline, init_project
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
    init.add_argument("--topic", required=True, help="short topic description")
    init.add_argument("--research-question", help="custom research question")
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
        )
        print(project_dir)
        return 0

    if args.command == "run":
        reviewers = tuple(r.strip() for r in args.reviewers.split(",") if r.strip())
        pipeline = PaperPipeline(
            args.project_dir,
            client=LLMClient(offline=args.offline, model=args.model),
            data_paths=tuple(args.data),
            reference_paths=tuple(args.references),
            smart_loader_path=args.smart_loader,
            model_routes=_model_routes_from_args(args),
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


def _model_routes_from_args(args: argparse.Namespace) -> dict[str, str]:
    routes = {}
    if getattr(args, "model", None):
        routes["default"] = args.model
    for role in ("plan", "draft", "review", "revision"):
        value = getattr(args, f"{role}_model", None)
        if value:
            routes[role] = value
    return routes


if __name__ == "__main__":
    raise SystemExit(main())
