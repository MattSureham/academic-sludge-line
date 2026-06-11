"""Versioned drafting pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .llm import LLMClient
from .smart_loader import (
    LoadedInputGroup,
    append_context_to_brief,
    load_input_groups,
    resolve_input_paths,
)
from .templates import (
    draft_prompt,
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
    if start_mode not in START_MODES:
        raise ValueError(f"unknown start mode: {start_mode}")
    if start_mode != "discover-topic" and not topic:
        raise ValueError("topic is required unless start_mode is discover-topic")
    input_root = root.resolve()
    project_slug = slugify(slug or title)
    project_dir = root / "papers" / project_slug
    if project_dir.exists():
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
        model_routes: dict[str, str] | None = None,
        start_mode: str | None = None,
        seed_draft_path: Path | None = None,
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

    def run(self, cycles: int = 1, reviewers: tuple[str, ...] = DEFAULT_REVIEWERS) -> list[Path]:
        created: list[Path] = []
        for _ in range(cycles):
            created.append(self._run_one_cycle(reviewers))
        return created

    def _run_one_cycle(self, reviewers: tuple[str, ...]) -> Path:
        version = next_version(self.project_dir)
        version_dir = self.project_dir / f"v{version}"
        previous_dir = accepted_version(self.project_dir)
        previous_draft = None
        if previous_dir and previous_dir != version_dir and (previous_dir / "draft.md").exists():
            previous_draft = read_text(previous_dir / "draft.md")
        elif self.start_mode == "rewrite" and self.seed_draft_path and self.seed_draft_path.exists():
            previous_draft = read_text(self.seed_draft_path)

        loaded_inputs = self._load_inputs(version_dir)
        brief = append_context_to_brief(self.brief, loaded_inputs)
        working_manifest = dict(self.manifest)
        discovery = self._discover_topic_if_needed(version_dir, working_manifest, brief)
        if discovery:
            brief = f"{brief.strip() or 'TODO'}\n\n## Topic Discovery\n\n{discovery.text}"

        write_text(
            version_dir / "prompt.md",
            _prompt_record(
                working_manifest,
                brief,
                previous_dir.name if previous_dir else None,
                loaded_inputs,
                self.start_mode,
            ),
        )

        plan = _generate(
            self.client,
            plan_prompt(working_manifest, brief, previous_draft),
            offline_plan(working_manifest, brief, previous_draft),
            role="plan",
        )
        write_text(version_dir / "research_plan.md", plan.text)

        draft = _generate(
            self.client,
            draft_prompt(working_manifest, plan.text, brief, previous_draft),
            offline_draft(working_manifest, plan.text, brief, previous_draft),
            role="draft",
        )
        write_text(version_dir / "draft.md", draft.text)

        review_texts = []
        review_models = {}
        for reviewer in reviewers:
            review = _generate(
                self.client,
                review_prompt(working_manifest, draft.text, reviewer),
                offline_review(working_manifest, draft.text, reviewer),
                role="review",
            )
            review_texts.append(review.text)
            review_models[reviewer] = _result_metadata(review)
            write_text(version_dir / "reviews" / f"{reviewer}.md", review.text)

        revision = _generate(
            self.client,
            revision_prompt(working_manifest, draft.text, review_texts),
            offline_revision(working_manifest, draft.text, review_texts),
            role="revision",
        )
        write_text(version_dir / "revision_plan.md", revision.text)
        quality_gate = self._quality_gate(working_manifest, previous_dir, previous_draft, draft.text, version_dir)
        if quality_gate["accepted"]:
            write_accepted_version(self.project_dir, version_dir)

        write_json(
            version_dir / "metadata.json",
            {
                "schema": "academic-sludge-line.version.v1",
                "version": version,
                "created_at": utc_now(),
                "previous_version": previous_dir.name if previous_dir else None,
                "previous_accepted_version": previous_dir.name if previous_dir else None,
                "start_mode": self.start_mode,
                "accepted": quality_gate["accepted"],
                "quality_gate": quality_gate,
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
                    },
                },
                "loaded_inputs": [group.metadata() for group in loaded_inputs],
                "outputs": [
                    "prompt.md",
                    *(["inputs/"] if loaded_inputs else []),
                    "research_plan.md",
                    "draft.md",
                    "reviews/",
                    "revision_plan.md",
                ],
            },
        )
        return version_dir

    def _load_inputs(self, version_dir: Path) -> list[LoadedInputGroup]:
        groups = load_input_groups(
            self.data_paths,
            self.reference_paths,
            version_dir / "inputs",
            cli_path=self.smart_loader_path,
        )
        if not groups:
            return []

        for group in groups:
            write_text(version_dir / "inputs" / f"{group.label}.md", group.markdown)
        write_json(version_dir / "inputs" / "smart_loader.json", [group.metadata() for group in groups])
        return groups

    def _discover_topic_if_needed(self, version_dir: Path, manifest: dict, brief: str) -> object | None:
        if self.start_mode != "discover-topic":
            return None

        discovery = _generate(
            self.client,
            topic_discovery_prompt(manifest, brief),
            offline_topic_discovery(manifest, brief),
            role="plan",
        )
        write_text(version_dir / "topic_proposal.md", discovery.text)
        topic = _extract_prefixed_line(discovery.text, "Topic")
        research_question = _extract_prefixed_line(discovery.text, "Research question")
        if topic:
            manifest["topic"] = topic
        if research_question:
            manifest["research_question"] = research_question
        return discovery

    def _quality_gate(
        self,
        manifest: dict,
        previous_dir: Path | None,
        previous_draft: str | None,
        candidate_draft: str,
        version_dir: Path,
    ) -> dict:
        if not previous_draft:
            return {
                "accepted": True,
                "decision": "accepted",
                "reason": "no previous accepted draft",
                "previous_version": previous_dir.name if previous_dir else None,
                "scores": [],
            }

        prompt = score_prompt(manifest, previous_draft, candidate_draft)
        fallback = offline_score(manifest, previous_draft, candidate_draft)
        results = _generate_all(self.client, prompt, fallback, role="score")
        scores = [_score_metadata(result) for result in results]
        better_or_same = sum(1 for score in scores if score["verdict"] in {"better", "same"})
        worse = sum(1 for score in scores if score["verdict"] == "worse")
        accepted = better_or_same >= worse
        decision = "accepted" if accepted else "rejected"
        gate = {
            "accepted": accepted,
            "decision": decision,
            "reason": "candidate is not worse than previous accepted draft" if accepted else "candidate scored worse than previous accepted draft",
            "previous_version": previous_dir.name if previous_dir else None,
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
