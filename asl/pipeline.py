"""Versioned drafting pipeline."""

from __future__ import annotations

from pathlib import Path

from .llm import LLMClient
from .templates import (
    draft_prompt,
    offline_draft,
    offline_plan,
    offline_review,
    offline_revision,
    plan_prompt,
    review_prompt,
    revision_prompt,
)
from .workspace import latest_version, next_version, read_json, read_text, slugify, utc_now, write_json, write_text


DEFAULT_REVIEWERS = ("methods", "evidence", "style")


def init_project(root: Path, title: str, topic: str, brief: str, slug: str | None = None) -> Path:
    project_slug = slugify(slug or title)
    project_dir = root / "papers" / project_slug
    if project_dir.exists():
        raise FileExistsError(f"paper project already exists: {project_dir}")

    manifest = {
        "schema": "academic-sludge-line.paper.v1",
        "title": title,
        "topic": topic,
        "research_question": f"How should researchers evaluate {topic}?",
        "created_at": utc_now(),
        "policies": {
            "no_fake_citations": True,
            "no_fabricated_results": True,
            "todo_for_missing_evidence": True,
        },
    }
    write_json(project_dir / "project.json", manifest)
    write_text(project_dir / "topic_brief.md", brief)
    write_json(project_dir / "sources.json", [])
    return project_dir


class PaperPipeline:
    def __init__(self, project_dir: Path, client: LLMClient | None = None) -> None:
        self.project_dir = project_dir
        self.client = client or LLMClient()
        self.manifest = read_json(project_dir / "project.json")
        self.brief = read_text(project_dir / "topic_brief.md")

    def run(self, cycles: int = 1, reviewers: tuple[str, ...] = DEFAULT_REVIEWERS) -> list[Path]:
        created: list[Path] = []
        for _ in range(cycles):
            created.append(self._run_one_cycle(reviewers))
        return created

    def _run_one_cycle(self, reviewers: tuple[str, ...]) -> Path:
        version = next_version(self.project_dir)
        version_dir = self.project_dir / f"v{version}"
        previous_dir = latest_version(self.project_dir)
        previous_draft = None
        if previous_dir and previous_dir != version_dir and (previous_dir / "draft.md").exists():
            previous_draft = read_text(previous_dir / "draft.md")

        write_text(
            version_dir / "prompt.md",
            _prompt_record(self.manifest, self.brief, previous_dir.name if previous_dir else None),
        )

        plan = self.client.generate(
            plan_prompt(self.manifest, self.brief, previous_draft),
            offline_plan(self.manifest, self.brief, previous_draft),
        )
        write_text(version_dir / "research_plan.md", plan.text)

        draft = self.client.generate(
            draft_prompt(self.manifest, plan.text, self.brief, previous_draft),
            offline_draft(self.manifest, plan.text, self.brief, previous_draft),
        )
        write_text(version_dir / "draft.md", draft.text)

        review_texts = []
        for reviewer in reviewers:
            review = self.client.generate(
                review_prompt(self.manifest, draft.text, reviewer),
                offline_review(self.manifest, draft.text, reviewer),
            )
            review_texts.append(review.text)
            write_text(version_dir / "reviews" / f"{reviewer}.md", review.text)

        revision = self.client.generate(
            revision_prompt(self.manifest, draft.text, review_texts),
            offline_revision(self.manifest, draft.text, review_texts),
        )
        write_text(version_dir / "revision_plan.md", revision.text)

        write_json(
            version_dir / "metadata.json",
            {
                "schema": "academic-sludge-line.version.v1",
                "version": version,
                "created_at": utc_now(),
                "previous_version": previous_dir.name if previous_dir else None,
                "provider": draft.provider,
                "model": draft.model,
                "reviewers": list(reviewers),
                "outputs": [
                    "prompt.md",
                    "research_plan.md",
                    "draft.md",
                    "reviews/",
                    "revision_plan.md",
                ],
            },
        )
        return version_dir


def _prompt_record(manifest: dict, brief: str, previous_version: str | None) -> str:
    previous = previous_version or "none"
    return f"""# Prompt Record

Title: {manifest["title"]}

Topic: {manifest["topic"]}

Previous version: {previous}

## Guardrails
- Do not fabricate citations.
- Do not fabricate data or results.
- Mark unsupported claims as TODO.

## Topic Brief
{brief}
"""

