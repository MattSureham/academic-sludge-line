import urllib.error
from pathlib import Path

import pytest

from asl.cli import main
from asl.llm import LLMClient
from asl.pipeline import PaperPipeline, init_project
from asl.templates import (
    draft_prompt,
    offline_draft,
    offline_plan,
    offline_review,
    offline_revision,
    plan_prompt,
)
from asl.workspace import read_json


def test_pipeline_creates_versioned_outputs(tmp_path: Path) -> None:
    root = tmp_path
    code = main(
        [
            "init",
            "--root",
            str(root),
            "--slug",
            "demo",
            "--title",
            "Demo Paper",
            "--topic",
            "demo policy",
            "--brief",
            "Use only verified sources.",
        ]
    )
    assert code == 0

    project = root / "papers" / "demo"
    code = main(["run", str(project), "--cycles", "2", "--offline"])
    assert code == 0

    assert (project / "v1" / "draft.md").exists()
    assert (project / "v1" / "reviews" / "methods.md").exists()
    assert (project / "v2" / "revision_plan.md").exists()


def test_offline_templates_dedent_multiline_inputs() -> None:
    manifest = {
        "title": "Demo Paper",
        "topic": "transparent evaluation of a public program",
        "research_question": "What evidence supports transparent public-program evaluation?",
    }
    plan = "First plan line\nSecond plan line"
    brief = "First brief line\nSecond brief line"

    research_plan = offline_plan(manifest, brief)
    assert "\n        ##" not in research_plan
    assert "\n        First brief line" not in research_plan

    draft = offline_draft(manifest, plan, brief)
    assert "\n        ##" not in draft
    assert "\n        First brief line" not in draft
    assert "\n        First plan line" not in draft

    review = offline_review(manifest, "Draft line\nSecond draft line", "methods")
    assert "\n        ##" not in review
    assert "\n        Draft line" not in review

    revision = offline_revision(manifest, "Draft line\nSecond draft line", ["Review line\nSecond review line"])
    assert "\n        ##" not in revision
    assert "\n        Draft line" not in revision
    assert "\n        Review line" not in revision


def test_prompts_dedent_multiline_inputs() -> None:
    manifest = {
        "title": "Demo Paper",
        "topic": "transparent evaluation of a public program",
        "research_question": "What evidence supports transparent public-program evaluation?",
    }

    plan = plan_prompt(manifest, "First brief line\nSecond brief line", "Previous line\nSecond previous line")
    assert "\n        Return sections:" not in plan
    assert "\n        First brief line" not in plan
    assert "\n        Previous line" not in plan

    draft = draft_prompt(manifest, "First plan line\nSecond plan line", "First brief line\nSecond brief line")
    assert "\n        Research plan:" not in draft
    assert "\n        First brief line" not in draft
    assert "\n        First plan line" not in draft


def test_init_allows_custom_research_question(tmp_path: Path) -> None:
    code = main(
        [
            "init",
            "--root",
            str(tmp_path),
            "--slug",
            "custom-question",
            "--title",
            "Custom Question",
            "--topic",
            "transparent evaluation of a public program",
            "--research-question",
            "What evidence makes a public-program evaluation transparent?",
            "--brief",
            "Use verified sources.",
        ]
    )

    assert code == 0
    manifest = read_json(tmp_path / "papers" / "custom-question" / "project.json")
    assert manifest["research_question"] == "What evidence makes a public-program evaluation transparent?"


def test_llm_failure_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise urllib.error.URLError("network unavailable")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)

    result = LLMClient().generate("prompt", "fallback text")

    assert result.provider == "offline-after-error"
    assert result.text.startswith("fallback text")
    assert "offline fallback used" in result.text


def test_empty_brief_can_run_offline(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="empty-brief",
        title="Empty Brief",
        topic="demo policy",
        brief="",
    )

    created = PaperPipeline(project, client=LLMClient(offline=True)).run()

    assert len(created) == 1
    assert (project / "v1" / "draft.md").exists()


def test_duplicate_init_is_rejected(tmp_path: Path) -> None:
    args = [
        "init",
        "--root",
        str(tmp_path),
        "--slug",
        "duplicate",
        "--title",
        "Duplicate",
        "--topic",
        "demo policy",
        "--brief",
        "Use verified sources.",
    ]

    assert main(args) == 0
    with pytest.raises(FileExistsError):
        main(args)
