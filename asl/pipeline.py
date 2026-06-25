"""Versioned drafting pipeline."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from .html_render import render_version_html
from .llm import LLMClient
from .reference_search import (
    ReferenceSearchResult,
    ReferenceSearchSettings,
    append_reference_search_to_brief,
    run_reference_search,
    update_reference_sources_ledger,
)
from .smart_loader import (
    LoadedInputGroup,
    ReferenceContextSettings,
    SmartLoader,
    SmartLoaderSettings,
    append_context_to_brief,
    budget_reference_context,
    render_context_for_prompt,
    resolve_input_paths,
)
from .templates import (
    draft_prompt,
    iterative_draft_prompt,
    offline_draft,
    offline_plan,
    offline_review,
    offline_revision,
    offline_score,
    offline_topic_discovery,
    plan_prompt,
    review_prompt,
    revision_prompt,
    score_prompt,
    topic_discovery_prompt,
)
from .web_research import (
    WebResearchResult,
    WebResearchSettings,
    append_web_research_to_brief,
    run_web_research,
    update_sources_ledger,
)
from .workspace import (
    accepted_version,
    latest_version,
    next_version,
    read_json,
    read_text,
    slugify,
    utc_now,
    write_accepted_version,
    write_json,
    write_text,
)


DEFAULT_REVIEWERS = ("methods", "evidence", "style")
START_MODES = ("from-scratch", "discover-topic", "rewrite")
TEXT_SEED_DRAFT_SUFFIXES = {".md", ".markdown", ".txt", ".tex", ".rst"}
DRAFT_PROMPT_BUDGET = 20_000
PIPELINE_ROLES = ("plan", "draft", "review", "revision", "score")


class ModelUnavailableError(RuntimeError):
    """A configured model for a pipeline role cannot run (e.g. missing credentials)."""


class TopicSelectionPending(RuntimeError):
    """Manual topic mode discovered candidates and is waiting for a --topic-choice."""

    def __init__(self, candidates: list[dict], proposal_path: Path) -> None:
        self.candidates = candidates
        self.proposal_path = proposal_path
        lines = [
            f"  {index}. {candidate.get('topic', '(untitled)')}"
            for index, candidate in enumerate(candidates, start=1)
        ]
        super().__init__(
            "Manual topic mode: review the proposed topics and re-run with --topic-choice N.\n"
            f"Proposals written to {proposal_path}\n" + "\n".join(lines)
        )


def init_project(
    root: Path,
    title: str,
    topic: str | None,
    brief: str,
    slug: str | None = None,
    research_question: str | None = None,
    data_paths: tuple[Path, ...] = (),
    reference_paths: tuple[Path, ...] = (),
    model_routes: dict[str, str] | None = None,
    start_mode: str = "from-scratch",
    seed_draft_path: Path | None = None,
) -> Path:
    project_slug = slugify(slug or title)
    project_dir = root / "papers" / project_slug
    return init_project_at(
        project_dir,
        title=title,
        topic=topic,
        brief=brief,
        research_question=research_question,
        data_paths=data_paths,
        reference_paths=reference_paths,
        model_routes=model_routes,
        start_mode=start_mode,
        seed_draft_path=seed_draft_path,
        input_root=root.resolve(),
    )


def init_project_at(
    project_dir: Path,
    title: str,
    topic: str | None,
    brief: str,
    research_question: str | None = None,
    data_paths: tuple[Path, ...] = (),
    reference_paths: tuple[Path, ...] = (),
    model_routes: dict[str, str] | None = None,
    start_mode: str = "from-scratch",
    seed_draft_path: Path | None = None,
    input_root: Path | None = None,
    allow_existing_empty: bool = False,
) -> Path:
    if start_mode not in START_MODES:
        raise ValueError(f"unknown start mode: {start_mode}")
    if start_mode != "discover-topic" and not topic:
        raise ValueError("topic is required unless start_mode is discover-topic")
    project_dir = project_dir.resolve()
    input_root = (input_root or _project_root(project_dir)).resolve()
    if project_dir.exists():
        if not project_dir.is_dir():
            raise FileExistsError(f"paper project path is not a directory: {project_dir}")
        if not allow_existing_empty or any(project_dir.iterdir()):
            raise FileExistsError(f"paper project already exists: {project_dir}")

    manifest = {
        "schema": "academic-sludge-line.paper.v1",
        "title": title,
        "topic": topic or "TODO: discover topic from supplied data and references",
        "research_question": research_question or _default_research_question(topic, start_mode),
        "created_at": utc_now(),
        "policies": {
            "no_fake_citations": True,
            "no_fabricated_results": True,
            "todo_for_missing_evidence": True,
        },
        "inputs": {
            "data": [str(path) for path in resolve_input_paths(data_paths, input_root)],
            "references": [str(path) for path in resolve_input_paths(reference_paths, input_root)],
        },
        "task": {
            "start_mode": start_mode,
            "topic_locked": start_mode != "discover-topic",
            "seed_draft": str(resolve_input_paths([seed_draft_path], input_root)[0]) if seed_draft_path else None,
        },
    }
    if model_routes:
        manifest["models"] = model_routes
    write_json(project_dir / "project.json", manifest)
    write_text(project_dir / "topic_brief.md", brief)
    write_json(project_dir / "sources.json", [])
    return project_dir


class PaperPipeline:
    def __init__(
        self,
        project_dir: Path,
        client: LLMClient | None = None,
        data_paths: tuple[Path, ...] = (),
        reference_paths: tuple[Path, ...] = (),
        smart_loader_path: Path | None = None,
        smart_loader_settings: SmartLoaderSettings | None = None,
        reference_context_settings: ReferenceContextSettings | None = None,
        model_routes: dict[str, str] | None = None,
        start_mode: str | None = None,
        seed_draft_path: Path | None = None,
        web_research_settings: WebResearchSettings | None = None,
        reference_search_settings: ReferenceSearchSettings | None = None,
        progress_callback: Callable[[dict[str, object]], None] | None = None,
        prompt_budget: int = DRAFT_PROMPT_BUDGET,
        from_version: str | None = None,
        additional_context: str | None = None,
        topic_mode: str = "auto",
        topic_choice: int | None = None,
        topic_count: int = 3,
    ) -> None:
        self.project_dir = project_dir.resolve()
        self.client = client or LLMClient()
        self.manifest = read_json(self.project_dir / "project.json")
        self.brief = read_text(self.project_dir / "topic_brief.md")
        manifest_models = self.manifest.get("models", {})
        if not isinstance(manifest_models, dict):
            manifest_models = {}
        merged_model_routes = {**manifest_models, **(model_routes or {})}
        if merged_model_routes and hasattr(self.client, "with_model_routes"):
            self.client = self.client.with_model_routes(merged_model_routes)
        task = self.manifest.get("task", {})
        if not isinstance(task, dict):
            task = {}
        self.start_mode = start_mode or task.get("start_mode") or "from-scratch"
        if self.start_mode not in START_MODES:
            raise ValueError(f"unknown start mode: {self.start_mode}")
        manifest_seed = task.get("seed_draft")
        self.seed_draft_path = seed_draft_path or (Path(manifest_seed) if manifest_seed else None)
        manifest_inputs = self.manifest.get("inputs", {})
        if not isinstance(manifest_inputs, dict):
            manifest_inputs = {}
        project_root = _project_root(self.project_dir)
        self.data_paths = tuple(
            [
                *resolve_input_paths(manifest_inputs.get("data", []), project_root),
                *resolve_input_paths(data_paths, Path.cwd()),
            ]
        )
        self.reference_paths = tuple(
            [
                *resolve_input_paths(manifest_inputs.get("references", []), project_root),
                *resolve_input_paths(reference_paths, Path.cwd()),
            ]
        )
        self.smart_loader_path = smart_loader_path
        self.smart_loader_settings = smart_loader_settings or SmartLoaderSettings()
        self.reference_context_settings = reference_context_settings or ReferenceContextSettings()
        self.resolved_smart_loader_path: Path | None = None
        self.web_research_settings = web_research_settings or WebResearchSettings()
        self.reference_search_settings = reference_search_settings or ReferenceSearchSettings()
        self.progress_callback = progress_callback
        self.prompt_budget = prompt_budget
        self.from_version = from_version
        self.additional_context = additional_context
        self.topic_mode = topic_mode if topic_mode in {"auto", "manual"} else "auto"
        self.topic_choice = topic_choice
        self.topic_count = max(1, topic_count)
        self.discovery_survey_chars = 30_000

    def run(self, cycles: int = 1, reviewers: tuple[str, ...] = DEFAULT_REVIEWERS) -> list[Path]:
        created: list[Path] = []
        self._preflight_models()
        self._ensure_seed_baseline()
        total_cycles = max(1, cycles)
        baseline_override = _resolve_from_version(self.project_dir, self.from_version)
        for index in range(total_cycles):
            self._emit_progress(
                "cycle_start",
                f"Starting iteration {index + 1} of {total_cycles}",
                cycle=index + 1,
                total_cycles=total_cycles,
            )
            created.append(self._run_one_cycle(
                reviewers, cycle=index + 1, total_cycles=total_cycles,
                override_baseline_dir=baseline_override if index == 0 else None,
            ))
        return created

    def _preflight_models(self) -> None:
        checker = getattr(self.client, "unavailable_roles", None)
        if checker is None:
            return
        problems = checker(PIPELINE_ROLES)
        if not problems:
            return
        lines = [
            f"  - {role}: {'; '.join(reasons) if reasons else 'no available model'}"
            for role, reasons in problems.items()
        ]
        raise ModelUnavailableError(
            "Configured models are unavailable for these pipeline roles, so they would "
            "silently fall back to the offline template. Fix the credentials/routes "
            "(e.g. add the cc-switch profile suffix) or pass --offline to accept template "
            "output:\n" + "\n".join(lines)
        )

    def _run_one_cycle(self, reviewers: tuple[str, ...], cycle: int = 1, total_cycles: int = 1, override_baseline_dir: Path | None = None) -> Path:
        version = next_version(self.project_dir)
        version_dir = self.project_dir / f"v{version}"
        self._emit_progress(
            "version_prepare",
            f"Preparing {version_dir.name}",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        accepted_dir = accepted_version(self.project_dir)
        accepted_draft = read_text(accepted_dir / "draft.md") if accepted_dir and (accepted_dir / "draft.md").exists() else None
        baseline_dir = override_baseline_dir or accepted_dir
        previous_draft = None
        loaded_seed_draft = None
        previous_draft_source = None
        if baseline_dir and baseline_dir != version_dir and (baseline_dir / "draft.md").exists():
            self._emit_progress(
                "previous_draft",
                f"Reading baseline draft from {baseline_dir.name}",
                cycle=cycle,
                total_cycles=total_cycles,
                version=version_dir.name,
            )
            previous_draft = read_text(baseline_dir / "draft.md")
            previous_draft_source = "accepted_version" if baseline_dir == accepted_dir else f"version_{baseline_dir.name}"
        elif self.start_mode == "rewrite" and self.seed_draft_path and self.seed_draft_path.exists():
            self._emit_progress(
                "seed_draft",
                f"Loading seed draft: {self.seed_draft_path.name}",
                cycle=cycle,
                total_cycles=total_cycles,
                version=version_dir.name,
            )
            previous_draft, loaded_seed_draft = self._load_seed_draft(version_dir)
            previous_draft_source = "seed_draft"

        self._emit_progress(
            "inputs",
            "Loading data and references",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        loaded_inputs = self._load_inputs(version_dir)
        self._write_smart_loader_manifest(version_dir, loaded_seed_draft, loaded_inputs)
        working_manifest = dict(self.manifest)
        self._emit_progress(
            "topic_discovery",
            "Checking topic discovery",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        # Discover the topic first so its anchor papers can seed this cycle's focus set.
        discovery = self._discover_topic_if_needed(version_dir, working_manifest, loaded_inputs)
        reference_focus = self._focus_set(baseline_dir, working_manifest, loaded_inputs)
        reference_query = _reference_query(working_manifest)
        brief = append_context_to_brief(
            self.brief, loaded_inputs, self.reference_context_settings,
            query=reference_query, featured=reference_focus,
        )
        if self.additional_context:
            brief = f"{brief}\n\n## Additional Guidance\n\n{self.additional_context.strip()}"
        brief = _sanitize_local_paths(brief, self.reference_paths + self.data_paths)
        if discovery:
            brief = f"{brief.strip() or 'TODO'}\n\n## Topic Discovery\n\n{discovery.text}"
        self._emit_progress(
            "reference_search",
            "Searching reference candidates" if self.reference_search_settings.enabled else "Skipping reference search",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        reference_search = self._run_reference_search(version_dir, working_manifest, brief)
        brief = append_reference_search_to_brief(brief, reference_search)
        self._emit_progress(
            "web_research",
            "Running web research" if self.web_research_settings.enabled else "Skipping web research",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        web_research = self._run_web_research(version_dir, working_manifest, brief)
        brief = append_web_research_to_brief(brief, web_research)

        self._emit_progress(
            "prompt_record",
            "Writing prompt record",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        write_text(
            version_dir / "prompt.md",
            _prompt_record(
                working_manifest,
                brief,
                baseline_dir.name if baseline_dir else None,
                loaded_inputs,
                self.start_mode,
            ),
        )

        self._emit_progress(
            "plan",
            "Generating research plan",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        plan = _generate(
            self.client,
            plan_prompt(working_manifest, brief, previous_draft),
            offline_plan(working_manifest, brief, previous_draft),
            role="plan",
        )
        plan_text = _sanitize_local_paths(plan.text, self.reference_paths + self.data_paths)
        write_text(version_dir / "research_plan.md", plan_text)

        self._emit_progress(
            "draft",
            "Generating draft",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        is_iterative = _is_iterative_cycle(baseline_dir)
        if is_iterative:
            review_summary = _read_previous_reviews(baseline_dir)
            revision_plan_text = _read_previous_revision_plan(baseline_dir)
            review_cost = min(len(review_summary), 4000) + min(len(revision_plan_text), 3000)
            iterative_budget = self.prompt_budget + review_cost + 8000
            draft_brief = _trim_brief_for_budget(
                brief, plan_text, previous_draft, iterative_budget,
                previous_draft_budget=16000, extra_costs=review_cost,
                ref_settings=self.reference_context_settings,
                ref_query=_reference_query(working_manifest),
                ref_featured=reference_focus,
            )
            draft = _generate(
                self.client,
                iterative_draft_prompt(
                    working_manifest, plan_text, draft_brief, previous_draft,
                    review_summary, revision_plan_text,
                ),
                offline_draft(working_manifest, plan_text, brief, previous_draft),
                role="draft",
            )
        else:
            draft_brief = _trim_brief_for_budget(
                brief, plan_text, previous_draft, self.prompt_budget,
                ref_settings=self.reference_context_settings,
                ref_query=_reference_query(working_manifest),
                ref_featured=reference_focus,
            )
            draft = _generate(
                self.client,
                draft_prompt(working_manifest, plan_text, draft_brief, previous_draft),
                offline_draft(working_manifest, plan_text, brief, previous_draft),
                role="draft",
            )
        write_text(version_dir / "draft.md", draft.text)

        review_texts = []
        review_models = {}
        for reviewer in reviewers:
            self._emit_progress(
                "review",
                f"Running {reviewer} reviewer",
                cycle=cycle,
                total_cycles=total_cycles,
                version=version_dir.name,
                reviewer=reviewer,
            )
            review = _generate(
                self.client,
                review_prompt(working_manifest, draft.text, reviewer),
                offline_review(working_manifest, draft.text, reviewer),
                role="review",
            )
            review_texts.append(review.text)
            review_models[reviewer] = _result_metadata(review)
            write_text(version_dir / "reviews" / f"{reviewer}.md", review.text)

        self._emit_progress(
            "revision",
            "Generating revision plan",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        revision = _generate(
            self.client,
            revision_prompt(working_manifest, draft.text, review_texts),
            offline_revision(working_manifest, draft.text, review_texts),
            role="revision",
        )
        write_text(version_dir / "revision_plan.md", revision.text)
        self._emit_progress(
            "quality_gate",
            "Scoring candidate draft",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        quality_gate = self._quality_gate(working_manifest, accepted_dir, accepted_draft, draft, version_dir)
        if quality_gate["accepted"]:
            write_accepted_version(self.project_dir, version_dir)

        self._emit_progress(
            "metadata",
            "Writing metadata and HTML",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        metadata = {
            "schema": "academic-sludge-line.version.v1",
            "version": version,
            "created_at": utc_now(),
            "previous_version": baseline_dir.name if baseline_dir else None,
            "previous_accepted_version": accepted_dir.name if accepted_dir else None,
            "previous_draft_source": previous_draft_source,
            "start_mode": self.start_mode,
            "accepted": quality_gate["accepted"],
            "quality_gate": quality_gate,
            "reference_focus": reference_focus,
            "provider": draft.provider,
            "model": draft.model,
            "reviewers": list(reviewers),
            "models": {
                "requested": _route_metadata(self.client),
                "used": {
                    "plan": _result_metadata(plan),
                    "draft": _result_metadata(draft),
                    "reviews": review_models,
                    "revision": _result_metadata(revision),
                    "score": quality_gate.get("scores", []),
                },
            },
            "input_loader": {
                "smart_loader": str(self.resolved_smart_loader_path) if self.resolved_smart_loader_path else None,
                "requested_smart_loader": str(self.smart_loader_path) if self.smart_loader_path else None,
                "settings": asdict(self.smart_loader_settings),
            },
            "web_research": web_research.metadata(),
            "reference_search": reference_search.metadata(),
            "loaded_seed_draft": loaded_seed_draft.metadata() if loaded_seed_draft else None,
            "loaded_inputs": [group.metadata() for group in loaded_inputs],
            "outputs": [
                "prompt.md",
                *(["inputs/"] if loaded_inputs or loaded_seed_draft or previous_draft_source == "seed_draft" else []),
                *(["reference_search.md", "reference_search.json"] if reference_search.enabled else []),
                *(["web_research.md", "web_research.json"] if web_research.enabled else []),
                "research_plan.md",
                "draft.md",
                "reviews/",
                "revision_plan.md",
                "html/",
            ],
        }
        write_json(version_dir / "metadata.json", metadata)
        render_version_html(version_dir)
        self._emit_progress(
            "cycle_complete",
            f"Finished {version_dir.name}",
            cycle=cycle,
            total_cycles=total_cycles,
            version=version_dir.name,
        )
        return version_dir

    def _ensure_seed_baseline(self) -> Path | None:
        if self.start_mode != "rewrite" or not self.seed_draft_path or not self.seed_draft_path.exists():
            return None
        if latest_version(self.project_dir):
            return None

        version_dir = self.project_dir / "v1"
        self._emit_progress(
            "seed_baseline",
            f"Importing seed draft as {version_dir.name}",
            version=version_dir.name,
        )
        seed_text, loaded_seed_draft = self._load_seed_draft(version_dir)
        self._write_smart_loader_manifest(version_dir, loaded_seed_draft, [])
        write_text(version_dir / "draft.md", seed_text)
        write_text(
            version_dir / "prompt.md",
            _seed_baseline_prompt_record(self.manifest, self.seed_draft_path, loaded_seed_draft),
        )
        metadata = {
            "schema": "academic-sludge-line.version.v1",
            "version": 1,
            "created_at": utc_now(),
            "previous_version": None,
            "previous_accepted_version": None,
            "previous_draft_source": "seed_draft",
            "start_mode": self.start_mode,
            "accepted": True,
            "imported_seed_baseline": True,
            "quality_gate": {
                "accepted": True,
                "decision": "accepted",
                "reason": "seed draft imported as rewrite baseline",
                "previous_version": None,
                "scores": [],
            },
            "provider": "seed-draft",
            "model": "imported",
            "reviewers": [],
            "models": {
                "requested": _route_metadata(self.client),
                "used": {},
            },
            "input_loader": {
                "smart_loader": str(self.resolved_smart_loader_path) if self.resolved_smart_loader_path else None,
                "requested_smart_loader": str(self.smart_loader_path) if self.smart_loader_path else None,
                "settings": asdict(self.smart_loader_settings),
            },
            "web_research": WebResearchResult(
                enabled=False,
                provider=self.web_research_settings.provider,
            ).metadata(),
            "reference_search": ReferenceSearchResult(
                enabled=False,
                provider=self.reference_search_settings.provider,
            ).metadata(),
            "loaded_seed_draft": loaded_seed_draft.metadata() if loaded_seed_draft else None,
            "loaded_inputs": [],
            "outputs": [
                "prompt.md",
                "inputs/",
                "draft.md",
                "metadata.json",
                "html/",
            ],
        }
        write_json(version_dir / "metadata.json", metadata)
        write_accepted_version(self.project_dir, version_dir)
        render_version_html(version_dir)
        self._emit_progress(
            "seed_baseline_complete",
            f"Imported seed draft as {version_dir.name}",
            version=version_dir.name,
        )
        return version_dir

    def _emit_progress(self, stage: str, message: str, **details: object) -> None:
        if not self.progress_callback:
            return
        event: dict[str, object] = {"stage": stage, "message": message, **details}
        self.progress_callback(event)

    def _run_web_research(self, version_dir: Path, manifest: dict, brief: str) -> WebResearchResult:
        result = run_web_research(manifest, brief, version_dir, self.web_research_settings)
        update_sources_ledger(self.project_dir, version_dir.name, result)
        return result

    def _run_reference_search(self, version_dir: Path, manifest: dict, brief: str) -> ReferenceSearchResult:
        result = run_reference_search(manifest, brief, version_dir, self.reference_search_settings)
        update_reference_sources_ledger(self.project_dir, version_dir.name, result)
        return result

    def _load_inputs(self, version_dir: Path) -> list[LoadedInputGroup]:
        if not self.data_paths and not self.reference_paths:
            return []

        loader = SmartLoader(self.smart_loader_path, settings=self.smart_loader_settings)
        self.resolved_smart_loader_path = loader.cli_path
        output_dir = version_dir / "inputs"
        groups = [
            loader.load_group("data", self.data_paths, output_dir),
            loader.load_group("references", self.reference_paths, output_dir),
        ]
        groups = [group for group in groups if group.has_inputs]
        if not groups:
            return []

        for group in groups:
            write_text(version_dir / "inputs" / f"{group.label}.md", group.markdown)
        return groups

    def _load_seed_draft(self, version_dir: Path) -> tuple[str, LoadedInputGroup | None]:
        if not self.seed_draft_path:
            return "", None

        if self.seed_draft_path.suffix.lower() in TEXT_SEED_DRAFT_SUFFIXES:
            try:
                text = read_text(self.seed_draft_path)
            except UnicodeDecodeError:
                pass
            else:
                write_text(version_dir / "inputs" / "seed_draft.md", _seed_draft_markdown(self.seed_draft_path, text))
                return text, None

        loader = SmartLoader(self.smart_loader_path, settings=self.smart_loader_settings)
        self.resolved_smart_loader_path = loader.cli_path
        group = loader.load_group(
            "seed_draft",
            [self.seed_draft_path],
            version_dir / "inputs",
        )
        write_text(version_dir / "inputs" / "seed_draft.md", group.markdown)
        return _loaded_seed_draft_text(group), group

    def _write_smart_loader_manifest(
        self,
        version_dir: Path,
        loaded_seed_draft: LoadedInputGroup | None,
        loaded_inputs: list[LoadedInputGroup],
    ) -> None:
        groups = [*([loaded_seed_draft] if loaded_seed_draft else []), *loaded_inputs]
        if groups:
            write_json(version_dir / "inputs" / "smart_loader.json", [group.metadata() for group in groups])

    def _discover_topic_if_needed(self, version_dir: Path, manifest: dict, loaded_inputs: list) -> object | None:
        if self.start_mode != "discover-topic":
            return None
        # Discover once: later cycles reuse the persisted topic so versions don't drift.
        if not _topic_is_placeholder(manifest.get("topic")):
            return None

        candidates_path = self.project_dir / "topic_candidates.json"
        discovery = None
        candidates = _read_json_or_none(candidates_path)
        if not candidates:
            # Survey ALL references (every paper gets a short excerpt) so discovery
            # is not biased to whichever few the draft strategy would feature.
            survey = render_context_for_prompt(
                loaded_inputs, ReferenceContextSettings("balanced", limit=self.discovery_survey_chars)
            )
            survey = _sanitize_local_paths(survey, self.reference_paths + self.data_paths)
            discovery = _generate(
                self.client,
                topic_discovery_prompt(manifest, survey, self.topic_count),
                offline_topic_discovery(manifest, survey, self.topic_count),
                role="plan",
            )
            write_text(version_dir / "topic_proposal.md", discovery.text)
            write_text(self.project_dir / "topic_proposals.md", discovery.text)
            candidates = _parse_topic_candidates(discovery.text)
            write_json(candidates_path, candidates)

        if not candidates:
            return discovery

        choice = self.topic_choice
        if choice is None:
            if self.topic_mode == "manual":
                # Don't leave a half-built version dir; the chosen-topic re-run
                # should start cleanly at the same version number.
                shutil.rmtree(version_dir, ignore_errors=True)
                raise TopicSelectionPending(candidates, self.project_dir / "topic_proposals.md")
            choice = 1
        index = min(max(int(choice), 1), len(candidates)) - 1
        selected = candidates[index]

        topic = selected.get("topic")
        research_question = selected.get("research_question")
        anchors = selected.get("anchors") or []
        if topic:
            manifest["topic"] = topic
            if _title_is_placeholder(manifest.get("title")):
                manifest["title"] = topic
        if research_question:
            manifest["research_question"] = research_question
        manifest["topic_anchors"] = anchors
        if topic or research_question:
            self._persist_topic_discovery(manifest)
        return discovery

    def _persist_topic_discovery(self, manifest: dict) -> None:
        for key in ("title", "topic", "research_question", "topic_anchors"):
            if key in manifest:
                self.manifest[key] = manifest[key]
        task = self.manifest.get("task")
        if isinstance(task, dict) and not _topic_is_placeholder(self.manifest.get("topic")):
            task["topic_locked"] = True
        write_json(self.project_dir / "project.json", self.manifest)

    def _focus_set(self, baseline_dir: Path | None, manifest: dict, loaded_inputs: list) -> list[str]:
        """Pick which reference files this cycle should feature at full length.

        Combines (1) the topic's anchor papers, (2) reviewer-flagged underused
        references from the baseline, and (3) a rotating batch of papers not yet
        featured in earlier versions, so each iteration deepens different sources.
        """
        all_files = _all_reference_filenames(loaded_inputs)
        if not all_files:
            return []

        focus: list[str] = []

        def add(name: str) -> None:
            base = Path(str(name)).name
            if base in all_files and base not in focus:
                focus.append(base)

        for anchor in manifest.get("topic_anchors") or []:
            add(anchor)
        if baseline_dir is not None:
            for name in self._underused_from_reviews(baseline_dir):
                add(name)

        batch = max(1, self.reference_context_settings.full_count)
        featured_before = self._featured_history()
        pool = [f for f in all_files if f not in focus]
        fresh = [f for f in pool if f not in featured_before]
        if fresh:
            rotation = fresh
        elif pool:
            # Everything has been featured once; keep rotating via a version offset.
            version_count = sum(1 for _ in self.project_dir.glob("v*"))
            offset = (version_count * batch) % len(pool)
            rotation = pool[offset:] + pool[:offset]
        else:
            rotation = []
        focus.extend(rotation[:batch])
        return focus

    def _featured_history(self) -> set[str]:
        featured: set[str] = set()
        for version_dir in self.project_dir.glob("v*"):
            metadata = _read_json_or_none(version_dir / "metadata.json")
            if isinstance(metadata, dict):
                for name in metadata.get("reference_focus") or []:
                    featured.add(str(name))
        return featured

    def _underused_from_reviews(self, baseline_dir: Path) -> list[str]:
        names: list[str] = []
        reviews_dir = baseline_dir / "reviews"
        if not reviews_dir.exists():
            return names
        for review_path in sorted(reviews_dir.glob("*.md")):
            for line in read_text(review_path).splitlines():
                match = re.match(r"(?i)\s*underused references?\s*:\s*(.+)", line)
                if not match:
                    continue
                for name in re.findall(r"[\w.\-]+\.(?:pdf|docx?|md|txt|csv|xlsx?)", match.group(1)):
                    if name not in names:
                        names.append(name)
        return names

    def _quality_gate(
        self,
        manifest: dict,
        previous_dir: Path | None,
        previous_draft: str | None,
        candidate: object,
        version_dir: Path,
    ) -> dict:
        candidate_draft = getattr(candidate, "text", "")
        if not previous_draft:
            return {
                "accepted": True,
                "decision": "accepted",
                "reason": "no previous accepted draft",
                "previous_version": previous_dir.name if previous_dir else None,
                "scores": [],
            }

        candidate_model = _result_metadata(candidate)
        if _is_fallback_result(candidate_model):
            gate = {
                "accepted": False,
                "decision": "rejected",
                "reason": "candidate draft used an offline fallback after model failure; preserving previous accepted draft",
                "previous_version": previous_dir.name if previous_dir else None,
                "candidate_model": candidate_model,
                "scores": [],
            }
            write_json(version_dir / "quality_scores.json", gate)
            return gate

        prompt = score_prompt(manifest, previous_draft, candidate_draft)
        fallback = offline_score(manifest, previous_draft, candidate_draft)
        results = _generate_all(self.client, prompt, fallback, role="score")
        scores = [_score_metadata(result) for result in results]
        if not any(not _is_fallback_result(score) for score in scores):
            gate = {
                "accepted": False,
                "decision": "rejected",
                "reason": "no configured scoring model completed; preserving previous accepted draft",
                "previous_version": previous_dir.name if previous_dir else None,
                "candidate_model": candidate_model,
                "scores": scores,
            }
            write_json(version_dir / "quality_scores.json", gate)
            return gate

        better_or_same = sum(1 for score in scores if score["verdict"] in {"better", "same"})
        worse = sum(1 for score in scores if score["verdict"] == "worse")
        accepted = better_or_same >= worse
        decision = "accepted" if accepted else "rejected"
        gate = {
            "accepted": accepted,
            "decision": decision,
            "reason": "candidate is not worse than previous accepted draft" if accepted else "candidate scored worse than previous accepted draft",
            "previous_version": previous_dir.name if previous_dir else None,
            "candidate_model": candidate_model,
            "scores": scores,
        }
        write_json(version_dir / "quality_scores.json", gate)
        return gate


def _prompt_record(
    manifest: dict,
    brief: str,
    previous_version: str | None,
    loaded_inputs: list[LoadedInputGroup] | None = None,
    start_mode: str = "from-scratch",
) -> str:
    previous = previous_version or "none"
    input_summary = ""
    if loaded_inputs:
        lines = ["", "## Loaded Input Summary"]
        for group in loaded_inputs:
            summary = group.summary
            lines.append(
                f"- {group.label}: {summary['loadedFiles']} loaded, "
                f"{summary['failedFiles']} failed, {summary['chunks']} chunks"
            )
        input_summary = "\n".join(lines)

    return f"""# Prompt Record

Title: {manifest["title"]}

Topic: {manifest["topic"]}

Previous version: {previous}

Start mode: {start_mode}

## Guardrails
- Do not fabricate citations.
- Do not fabricate data or results.
- Mark unsupported claims as TODO.

## Topic Brief
{brief}
{input_summary}
"""


def _seed_baseline_prompt_record(
    manifest: dict,
    seed_draft_path: Path,
    loaded_seed_draft: LoadedInputGroup | None,
) -> str:
    loaded_summary = ""
    if loaded_seed_draft:
        summary = loaded_seed_draft.summary
        loaded_summary = (
            "\n\n## Loaded Seed Draft Summary\n"
            f"- Loaded files: {summary['loadedFiles']}\n"
            f"- Failed files: {summary['failedFiles']}\n"
            f"- Chunks: {summary['chunks']}\n"
            f"- Assets: {summary['assets']}\n"
        )
    return f"""# Seed Draft Baseline

Title: {manifest["title"]}

Topic: {manifest["topic"]}

Start mode: rewrite

Seed draft: {seed_draft_path}

This version was imported as the accepted baseline before model rewriting. It is not a generated draft.
{loaded_summary}
"""


def _seed_draft_markdown(path: Path, text: str) -> str:
    return f"""# Seed Draft

Source path: {path}

## Text

{text.strip() or "TODO"}
"""


def _loaded_seed_draft_text(group: LoadedInputGroup) -> str:
    sections: list[str] = []
    for result in group.results:
        for document in result.get("documents", []):
            if not isinstance(document, dict):
                continue
            relative = document.get("relativePath", document.get("sourcePath", "Seed draft"))
            markdown = str(document.get("markdown") or document.get("text") or "").strip()
            if not markdown:
                continue
            sections.append(f"# {relative}\n\n{markdown}" if not markdown.startswith("#") else markdown)
    return "\n\n---\n\n".join(sections).strip() or group.markdown


def _project_root(project_dir: Path) -> Path:
    if project_dir.parent.name == "papers":
        return project_dir.parent.parent
    return project_dir.parent


def _default_research_question(topic: str | None, start_mode: str) -> str:
    if start_mode == "discover-topic" or not topic:
        return "What research question is best supported by the supplied data and references?"
    return f"What evidence is needed to study {topic}?"


def _route_metadata(client: LLMClient) -> dict[str, list[str]]:
    if hasattr(client, "route_metadata"):
        return client.route_metadata()
    return {}


def _generate(client: LLMClient, prompt: str, fallback: str, role: str) -> object:
    try:
        return client.generate(prompt, fallback, role=role)
    except TypeError:
        return client.generate(prompt, fallback)


def _generate_all(client: LLMClient, prompt: str, fallback: str, role: str) -> list[object]:
    if hasattr(client, "generate_all"):
        return client.generate_all(prompt, fallback, role=role)
    return [_generate(client, prompt, fallback, role)]


def _result_metadata(result: object) -> dict[str, object]:
    return {
        "provider": getattr(result, "provider", "unknown"),
        "model": getattr(result, "model", "unknown"),
        "attempts": list(getattr(result, "attempts", ())),
    }


def _is_fallback_result(result: dict[str, object]) -> bool:
    return str(result.get("provider", "")).lower() in {"offline", "offline-after-error", "template"}


def _score_metadata(result: object) -> dict[str, object]:
    parsed = _parse_score_json(getattr(result, "text", ""))
    return {
        **_result_metadata(result),
        "verdict": parsed.get("verdict", "same"),
        "previous_score": parsed.get("previous_score", 5),
        "candidate_score": parsed.get("candidate_score", 5),
        "rationale": parsed.get("rationale", ""),
    }


def _parse_score_json(text: str) -> dict[str, object]:
    match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    verdict = str(parsed.get("verdict", "same")).lower()
    if verdict not in {"better", "same", "worse"}:
        verdict = "same"
    return {
        "verdict": verdict,
        "previous_score": _bounded_score(parsed.get("previous_score", 5)),
        "candidate_score": _bounded_score(parsed.get("candidate_score", 5)),
        "rationale": str(parsed.get("rationale", "")),
    }


def _bounded_score(value: object) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = 5
    return max(1, min(10, score))


def _extract_prefixed_line(text: str, prefix: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(prefix)}:\s*(.+)$", flags=re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _all_reference_filenames(loaded_inputs: list) -> list[str]:
    names: list[str] = []
    for group in loaded_inputs or []:
        for result in getattr(group, "results", ()) or ():
            if not isinstance(result, dict):
                continue
            for document in result.get("documents", []) or []:
                if not isinstance(document, dict):
                    continue
                relative = document.get("relativePath") or document.get("sourcePath")
                if not relative:
                    continue
                base = Path(str(relative)).name
                if base and base not in names:
                    names.append(base)
    return names


def _read_json_or_none(path: Path) -> object | None:
    if not path.exists():
        return None
    try:
        return read_json(path)
    except (ValueError, OSError):
        return None


def _parse_topic_candidates(text: str) -> list[dict]:
    """Parse the multi-topic discovery output into candidate dicts.

    Falls back to a single candidate built from any top-level Topic/Research
    question lines when the model does not emit the ``## Topic`` block format.
    """
    blocks = re.split(r"(?mi)^\s*##\s*topic\b.*$", text)
    candidates: list[dict] = []
    for block in blocks:
        topic = _extract_prefixed_line(block, "Topic")
        research_question = _extract_prefixed_line(block, "Research question")
        if not topic and not research_question:
            continue
        anchors_line = _extract_prefixed_line(block, "Anchor papers") or ""
        anchors = re.findall(r"[\w.\-]+\.(?:pdf|docx?|md|txt|csv|xlsx?)", anchors_line)
        candidates.append(
            {
                "topic": topic,
                "research_question": research_question,
                "anchors": anchors,
                "rationale": _extract_prefixed_line(block, "Rationale"),
            }
        )
    if not candidates:
        topic = _extract_prefixed_line(text, "Topic")
        research_question = _extract_prefixed_line(text, "Research question")
        if topic or research_question:
            candidates.append(
                {"topic": topic, "research_question": research_question, "anchors": [], "rationale": None}
            )
    return candidates


def _topic_is_placeholder(topic: str | None) -> bool:
    if not topic or not topic.strip():
        return True
    return topic.strip().upper().startswith("TODO")


def _title_is_placeholder(title: str | None) -> bool:
    if not title or not title.strip():
        return True
    return title.strip().lower().startswith("untitled")


def _sanitize_local_paths(text: str, dirs: tuple[Path, ...]) -> str:
    """Replace absolute paths under known input dirs with bare basenames.

    Live local file paths make agentic CLI providers (claude-code/codex) switch
    into file-tool mode and narrate tool calls instead of emitting the draft, so
    references must reach the prompt as bare names like ``17.pdf``.
    """
    if not text or not dirs:
        return text
    for directory in dirs:
        base = str(directory)
        if not base:
            continue
        text = re.sub(re.escape(base) + r"/(?:[^\s)\]]*/)?([^\s/)\]]+)", r"\1", text)
        text = text.replace(base, "the supplied corpus")
    return text


def _reference_query(manifest: dict) -> str:
    research_question = manifest.get("research_question")
    if isinstance(research_question, str) and research_question.strip() and not _topic_is_placeholder(research_question):
        return research_question
    topic = manifest.get("topic")
    if isinstance(topic, str) and not _topic_is_placeholder(topic):
        return topic
    return ""


def _trim_brief_for_budget(
    brief: str, plan: str, previous_draft: str | None, budget: int,
    previous_draft_budget: int = 8000, extra_costs: int = 0,
    ref_settings: ReferenceContextSettings | None = None,
    ref_query: str = "",
    ref_featured: list[str] | tuple[str, ...] = (),
) -> str:
    overhead = 800
    plan_size = len(plan.strip()) if plan else 0
    previous_size = min(len(previous_draft), previous_draft_budget) if previous_draft else 0
    available = budget - overhead - plan_size - previous_size - extra_costs
    if available >= len(brief):
        return brief
    # The "full" strategy treats loaded references as non-negotiable: the prompt
    # grows to fit them (bounded only by the reference-context limit), so raising
    # that limit is the lever instead of clever per-document budgeting.
    if ref_settings is not None and ref_settings.strategy == "full":
        return brief
    available = max(800, available)
    marker = "\n## Loaded Data And References\n"
    parts = brief.split(marker, 1)
    if len(parts) == 2:
        base_brief = parts[0]
        ref_section = parts[1]
        ref_budget = max(400, available - len(base_brief))
        if len(ref_section) <= ref_budget:
            return brief
        clipped = budget_reference_context(
            ref_section, ref_settings, ref_query, limit=ref_budget, featured=ref_featured
        )
        return f"{base_brief}{marker}{clipped}"
    return brief[:available].rstrip()


def _resolve_from_version(project_dir: Path, from_version: str | None) -> Path | None:
    if not from_version:
        return None
    name = from_version.lstrip("vV")
    candidate = project_dir / f"v{name}"
    if candidate.is_dir() and (candidate / "draft.md").exists():
        return candidate
    raise ValueError(f"version {from_version} not found in {project_dir}")


def _is_iterative_cycle(previous_dir: Path | None) -> bool:
    if not previous_dir:
        return False
    reviews_dir = previous_dir / "reviews"
    if not reviews_dir.exists():
        return False
    return any(reviews_dir.glob("*.md"))


def _read_previous_reviews(version_dir: Path) -> str:
    reviews_dir = version_dir / "reviews"
    if not reviews_dir.exists():
        return ""
    sections = []
    for path in sorted(reviews_dir.glob("*.md")):
        content = read_text(path).strip()
        if content:
            sections.append(f"### {path.stem.title()} Review\n\n{content}")
    return "\n\n".join(sections)


def _read_previous_revision_plan(version_dir: Path) -> str:
    path = version_dir / "revision_plan.md"
    if not path.exists():
        return ""
    return read_text(path).strip()
