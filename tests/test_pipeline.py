import json
import sys
import subprocess
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import pytest

from asl.catalog import catalog_payload
from asl.cli import main
from asl.html_render import render_version_html
from asl.local_providers import cc_switch_settings_for_ref
from asl.llm import LLMClient, LLMResult, parse_model_chain
from asl.pipeline import ModelUnavailableError, PaperPipeline, TopicSelectionPending, init_project
from asl.reference_search import ReferenceCandidate, ReferenceSearchSettings
from asl.smart_loader import SmartLoader
from asl.templates import (
    draft_prompt,
    offline_draft,
    offline_plan,
    offline_review,
    offline_revision,
    plan_prompt,
)
from asl.ui import (
    _APP_JS,
    _INDEX_HTML,
    _browse_payload,
    _create_directory,
    _create_project,
    _handler_factory,
    _project_payload,
    _run_project,
    _start_run_job,
)
from asl.web_research import WebResearchSettings, WebSource
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
    assert (project / "v1" / "html" / "index.html").exists()
    assert (project / "v1" / "html" / "draft.html").exists()
    assert (project / "v1" / "html" / "reviews_methods.html").exists()
    assert (project / "v2" / "revision_plan.md").exists()
    metadata = read_json(project / "v1" / "metadata.json")
    assert "html/" in metadata["outputs"]
    assert metadata["input_loader"]["settings"]["pdf_render_pages"] is True


def test_pipeline_emits_progress_events(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="progress",
        title="Progress",
        topic="visible pipeline progress",
        brief="Show status while running.",
    )
    events = []

    created = PaperPipeline(
        project,
        client=LLMClient(offline=True),
        progress_callback=events.append,
    ).run(cycles=1)

    assert created[0].name == "v1"
    stages = [event["stage"] for event in events]
    assert stages[0] == "cycle_start"
    assert "plan" in stages
    assert "draft" in stages
    assert "review" in stages
    assert stages[-1] == "cycle_complete"
    assert events[-1]["cycle"] == 1
    assert events[-1]["total_cycles"] == 1


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


def test_smart_loader_context_is_loaded_for_data_and_references(tmp_path: Path) -> None:
    (tmp_path / "data.csv").write_text("unit,value\nalpha,1\n", encoding="utf-8")
    (tmp_path / "refs.md").write_text("# Reference Note\nVerified reference text.\n", encoding="utf-8")
    fake_loader = _write_fake_smart_loader(tmp_path / "fake-smart-loader")

    code = main(
        [
            "init",
            "--root",
            str(tmp_path),
            "--slug",
            "with-inputs",
            "--title",
            "With Inputs",
            "--topic",
            "documented evidence",
            "--brief",
            "Use attached materials.",
            "--data",
            "data.csv",
            "--references",
            "refs.md",
        ]
    )
    assert code == 0

    project = tmp_path / "papers" / "with-inputs"
    code = main(["run", str(project), "--offline", "--smart-loader", str(fake_loader)])

    assert code == 0
    assert (project / "v1" / "inputs" / "data.md").exists()
    assert (project / "v1" / "inputs" / "references.md").exists()
    prompt = (project / "v1" / "prompt.md").read_text(encoding="utf-8")
    assert "Loaded Data And References" in prompt
    assert "sample from data.csv" in prompt
    assert "sample from refs.md" in prompt

    metadata = read_json(project / "v1" / "metadata.json")
    assert "inputs/" in metadata["outputs"]
    assert metadata["loaded_inputs"][0]["label"] == "data"
    assert metadata["loaded_inputs"][0]["summary"]["loadedFiles"] == 1
    assert (project / "v1" / "html" / "inputs_data.html").exists()
    assert (project / "v1" / "html" / "inputs_references.html").exists()


def test_smart_loader_defaults_to_bundled_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASL_SMART_LOADER", raising=False)

    loader = SmartLoader()

    assert loader.cli_path.as_posix().endswith("asl/_vendor/smart-loader/dist/cli.js")


def test_rewrite_seed_draft_pdf_is_loaded_through_smart_loader(tmp_path: Path) -> None:
    seed = tmp_path / "draft.pdf"
    seed.write_text("PDF-like draft body.", encoding="utf-8")
    fake_loader = _write_fake_smart_loader(tmp_path / "fake-smart-loader")

    code = main(
        [
            "init",
            "--root",
            str(tmp_path),
            "--slug",
            "rewrite-pdf",
            "--title",
            "Rewrite PDF",
            "--topic",
            "documented evidence",
            "--start-mode",
            "rewrite",
            "--seed-draft-file",
            str(seed),
        ]
    )
    assert code == 0

    project = tmp_path / "papers" / "rewrite-pdf"
    code = main(["run", str(project), "--offline", "--smart-loader", str(fake_loader)])

    assert code == 0
    seed_markdown = (project / "v1" / "inputs" / "seed_draft.md").read_text(encoding="utf-8")
    assert "Loaded Seed Draft" in seed_markdown
    assert "sample from draft.pdf" in seed_markdown
    baseline_draft = (project / "v1" / "draft.md").read_text(encoding="utf-8")
    assert "sample from draft.pdf" in baseline_draft
    prompt = (project / "v2" / "prompt.md").read_text(encoding="utf-8")
    assert "Previous version: v1" in prompt
    assert (project / "v1" / "html" / "inputs_seed_draft.html").exists()
    assert (project / "v2" / "html" / "draft.html").exists()
    baseline_metadata = read_json(project / "v1" / "metadata.json")
    assert baseline_metadata["imported_seed_baseline"] is True
    assert baseline_metadata["previous_draft_source"] == "seed_draft"
    assert baseline_metadata["loaded_seed_draft"]["summary"]["loadedFiles"] == 1
    generated_metadata = read_json(project / "v2" / "metadata.json")
    assert generated_metadata["previous_draft_source"] == "accepted_version"
    assert generated_metadata["previous_accepted_version"] == "v1"


def test_web_research_outputs_are_saved_and_injected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_search(query: str, max_results: int) -> list[WebSource]:
        return [
            WebSource(
                query=query,
                title="Evidence source",
                url="https://example.test/source",
                snippet="Verified source lead.",
                provider="duckduckgo",
            )
        ]

    monkeypatch.setattr("asl.web_research._search_duckduckgo", fake_search)
    project = init_project(
        root=tmp_path,
        slug="web-research",
        title="Web Research",
        topic="public program evidence",
        brief="Find source leads before drafting.",
    )

    created = PaperPipeline(
        project,
        client=LLMClient(offline=True),
        web_research_settings=WebResearchSettings(enabled=True, max_queries=1, max_results_per_query=2),
    ).run()[0]

    assert (created / "web_research.md").exists()
    assert (created / "web_research.json").exists()
    assert (created / "html" / "web_research.html").exists()
    assert "Web Research Leads" in (created / "prompt.md").read_text(encoding="utf-8")
    metadata = read_json(created / "metadata.json")
    assert metadata["web_research"]["enabled"] is True
    assert metadata["web_research"]["sources"][0]["url"] == "https://example.test/source"
    sources = read_json(project / "sources.json")
    assert sources[0]["kind"] == "web"
    assert sources[0]["version"] == "v1"


def test_reference_search_outputs_are_saved_and_injected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_search(query: str, max_results: int) -> list[ReferenceCandidate]:
        assert "public program evidence" in query
        assert max_results == 2
        return [
            ReferenceCandidate(
                query=query,
                title="Reference Evidence Paper",
                authors=("Ada Researcher", "Ben Scholar"),
                year="2024",
                container="Journal of Evidence",
                doi="10.1000/example",
                url="https://doi.org/10.1000/example",
                snippet="A relevant literature lead.",
            )
        ]

    monkeypatch.setattr("asl.reference_search._search_crossref", fake_search)
    project = init_project(
        root=tmp_path,
        slug="reference-search",
        title="Reference Search",
        topic="public program evidence",
        brief="Find literature leads before drafting.",
    )

    created = PaperPipeline(
        project,
        client=LLMClient(offline=True),
        reference_search_settings=ReferenceSearchSettings(enabled=True, max_results=2),
    ).run()[0]

    assert (created / "reference_search.md").exists()
    assert (created / "reference_search.json").exists()
    assert (created / "html" / "reference_search.html").exists()
    assert "Reference Search Leads" in (created / "prompt.md").read_text(encoding="utf-8")
    metadata = read_json(created / "metadata.json")
    assert metadata["reference_search"]["enabled"] is True
    assert metadata["reference_search"]["candidates"][0]["doi"] == "10.1000/example"
    sources = read_json(project / "sources.json")
    assert sources[0]["kind"] == "reference"
    assert sources[0]["title"] == "Reference Evidence Paper"
    assert sources[0]["version"] == "v1"


def test_cli_reference_search_flag_runs_crossref_stage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "asl.reference_search._search_crossref",
        lambda query, max_results: [
            ReferenceCandidate(query=query, title="CLI Reference", url="https://example.test/reference")
        ],
    )
    assert main(
        [
            "init",
            "--root",
            str(tmp_path),
            "--slug",
            "cli-reference-search",
            "--title",
            "CLI Reference Search",
            "--topic",
            "topic-led references",
            "--brief",
            "Find references.",
        ]
    ) == 0
    project = tmp_path / "papers" / "cli-reference-search"

    assert main(["run", str(project), "--offline", "--reference-search", "--reference-search-max-results", "1"]) == 0

    assert (project / "v1" / "reference_search.md").exists()
    metadata = read_json(project / "v1" / "metadata.json")
    assert metadata["reference_search"]["candidates"][0]["title"] == "CLI Reference"


def test_from_version_focus_and_iterative_prompt_are_recorded(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="intervention",
        title="Intervention",
        topic="human directed revision",
        brief="Use a careful evidence trail.",
    )
    PaperPipeline(project, client=_CapturingBetterClient()).run(cycles=2)
    assert (project / "accepted_version.txt").read_text(encoding="utf-8").strip() == "v2"

    client = _CapturingBetterClient()
    created = PaperPipeline(
        project,
        client=client,
        from_version="v1",
        additional_context="Tighten the methods section and preserve the framing.",
        prompt_budget=6_000,
    ).run()[0]

    metadata = read_json(created / "metadata.json")
    assert metadata["previous_version"] == "v1"
    assert metadata["previous_accepted_version"] == "v2"
    assert metadata["previous_draft_source"] == "version_v1"
    assert metadata["quality_gate"]["previous_version"] == "v2"

    draft_prompt_text = client.prompt_for_role("draft")
    assert "iteration cycle" in draft_prompt_text
    assert "Review findings:" in draft_prompt_text
    assert "Revision checklist:" in draft_prompt_text
    assert "Tighten the methods section" in draft_prompt_text
    assert "Additional Guidance" in (created / "prompt.md").read_text(encoding="utf-8")


def test_prompt_budget_trims_loaded_context_before_drafting(tmp_path: Path) -> None:
    long_reference_context = "REFERENCE CONTEXT " * 900
    project = init_project(
        root=tmp_path,
        slug="prompt-budget",
        title="Prompt Budget",
        topic="bounded prompts",
        brief=f"Base brief.\n\n## Loaded Data And References\n{long_reference_context}",
    )
    client = _CapturingBetterClient()

    PaperPipeline(project, client=client, prompt_budget=5_000).run()

    draft_prompt_text = client.prompt_for_role("draft")
    assert "[TRUNCATED:" in draft_prompt_text
    assert len(draft_prompt_text) < len(long_reference_context) + 3_000


def _reference_markdown(count: int, body_word: str = "body") -> str:
    preamble = "# Loaded References\n\nSummary:\n- Loaded files: {n}\n".format(n=count)
    docs = [f"## {i}.pdf\n\nFormat: pdf\n\n" + (f"{body_word} " * 300).strip() for i in range(1, count + 1)]
    return preamble + "\n\n" + "\n\n".join(docs)


def _distinct_pdfs(text: str) -> set[int]:
    import re

    return {int(match) for match in re.findall(r"(\d+)\.pdf", text)}


def test_reference_context_strategies_distribute_budget() -> None:
    from asl.smart_loader import ReferenceContextSettings, budget_reference_context

    combined = _reference_markdown(12)
    limit = 6_000

    full = budget_reference_context(combined, ReferenceContextSettings("full", limit))
    balanced = budget_reference_context(combined, ReferenceContextSettings("balanced", limit))

    # At a tight limit, "full" head-truncates (few docs); balanced shows them all.
    assert len(_distinct_pdfs(full)) < 12
    assert _distinct_pdfs(balanced) == set(range(1, 13))
    assert len(balanced) <= limit + 200

    # Raising the limit lets "full" include every document at full length.
    raised = budget_reference_context(combined, ReferenceContextSettings("full", len(combined) + 100))
    assert _distinct_pdfs(raised) == set(range(1, 13))


def test_reference_context_select_prioritizes_relevant_docs() -> None:
    from asl.smart_loader import ReferenceContextSettings, budget_reference_context

    preamble = "# Loaded References\n\nSummary:\n- Loaded files: 10\n"
    docs = []
    for i in range(1, 11):
        word = "sustainability" if i == 7 else "filler"
        docs.append(f"## {i}.pdf\n\nFormat: pdf\n\n" + (f"{word} " * 300).strip())
    combined = preamble + "\n\n" + "\n\n".join(docs)

    out = budget_reference_context(
        combined, ReferenceContextSettings("select", 5_000, full_count=1), query="sustainability"
    )
    # The relevant document is included at length even though it is far down the list.
    assert out.count("sustainability") > 50


def test_trim_brief_honors_reference_strategy() -> None:
    from asl.pipeline import _trim_brief_for_budget
    from asl.smart_loader import ReferenceContextSettings

    brief = "Base brief.\n\n## Loaded Data And References\n\n" + _reference_markdown(10)

    balanced = _trim_brief_for_budget(
        brief, plan="", previous_draft=None, budget=4_000,
        ref_settings=ReferenceContextSettings("balanced", 24_000),
    )
    select = _trim_brief_for_budget(
        brief, plan="", previous_draft=None, budget=4_000,
        ref_settings=ReferenceContextSettings("select", 24_000, full_count=1),
    )
    # The strategy survives the draft-budget trim, not just the initial context build.
    assert len(_distinct_pdfs(balanced)) > len(_distinct_pdfs(select))


def test_agent_prompt_disables_tools_when_not_allowed() -> None:
    from asl.llm import _agent_prompt

    no_tools = _agent_prompt("DELIVERABLE", allow_tools=False)
    with_tools = _agent_prompt("DELIVERABLE", allow_tools=True)
    # Without tools, the local agentic CLI is told to emit the deliverable inline
    # instead of narrating file/shell tool calls.
    assert "NO tools" in no_tools
    assert "NO tools" not in with_tools


def test_sanitize_local_paths_strips_absolute_paths() -> None:
    from asl.pipeline import _sanitize_local_paths

    dirs = (Path("/Users/me/Projects/testruns/6/references"),)
    plan = (
        "CFIR [17.pdf](/Users/me/Projects/testruns/6/references/17.pdf) and "
        "[9.pdf](/Users/me/Projects/testruns/6/references/sub/9.pdf)\n"
        "Input paths:\n- /Users/me/Projects/testruns/6/references"
    )
    out = _sanitize_local_paths(plan, dirs)
    # Absolute paths become bare basenames so agentic CLIs don't try to open files.
    assert "/Users/me/Projects" not in out
    assert "(17.pdf)" in out
    assert "9.pdf" in out
    assert "`1.pdf`" == _sanitize_local_paths("`1.pdf`", dirs)


def test_full_strategy_bypasses_draft_budget_trim() -> None:
    from asl.pipeline import _trim_brief_for_budget
    from asl.smart_loader import ReferenceContextSettings

    references = _reference_markdown(10)
    brief = "Base brief.\n\n## Loaded Data And References\n\n" + references

    # "full" keeps every reference even though the draft budget is far smaller,
    # so raising --reference-context-chars is the only lever that bounds it.
    out = _trim_brief_for_budget(
        brief, plan="", previous_draft=None, budget=4_000,
        ref_settings=ReferenceContextSettings("full", 100_000),
    )
    assert out == brief
    assert _distinct_pdfs(out) == set(range(1, 11))


def test_html_renderer_includes_dynamic_reviews_and_assets(tmp_path: Path) -> None:
    version = tmp_path / "v1"
    reviews = version / "reviews"
    assets = version / "inputs" / "assets" / "references" / "input-1"
    reviews.mkdir(parents=True)
    assets.mkdir(parents=True)
    (version / "draft.md").write_text("# Draft\n\nText.", encoding="utf-8")
    (reviews / "domain.md").write_text("# Domain Review\n\nLooks plausible.", encoding="utf-8")
    (assets / "page-1.png").write_bytes(b"not a real png")
    (version / "metadata.json").write_text('{"version": 1}', encoding="utf-8")

    render_version_html(version)

    assert (version / "html" / "reviews_domain.html").exists()
    asset_html = (version / "html" / "assets.html").read_text(encoding="utf-8")
    assert "../inputs/assets/references/input-1/page-1.png" in asset_html


def test_ui_browse_payload_and_create_directory(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("source", encoding="utf-8")
    (tmp_path / "inputs").mkdir()

    payload = _browse_payload(tmp_path, tmp_path)

    entries = {entry["name"]: entry for entry in payload["entries"]}
    assert payload["parent"] == str(tmp_path.parent)
    assert entries["inputs"]["type"] == "directory"
    assert entries["source.txt"]["type"] == "file"

    created = _create_directory({"path": str(tmp_path), "name": "new-folder"}, tmp_path)

    assert (tmp_path / "new-folder").is_dir()
    assert created["path"] == str(tmp_path / "new-folder")
    with pytest.raises(ValueError):
        _create_directory({"path": str(tmp_path), "name": "../bad"}, tmp_path)


def test_ui_create_project_allows_blank_title(tmp_path: Path) -> None:
    result = _create_project(
        {
            "root": str(tmp_path),
            "slug": "",
            "title": "",
            "topic": "transparent public program evaluation",
            "researchQuestion": "",
            "brief": "",
            "data": "",
            "references": "",
            "models": {},
            "startMode": "from-scratch",
            "seedDraftFile": "",
        },
        tmp_path,
    )

    project = Path(result["projectDir"])
    manifest = read_json(project / "project.json")

    assert project.name == "transparent-public-program-evaluation"
    assert manifest["title"] == "transparent public program evaluation"


def test_ui_run_missing_project_auto_creates(tmp_path: Path) -> None:
    missing = tmp_path / "papers" / "test2"

    result = _run_project({"projectDir": str(missing), "offline": True, "cycles": "1"}, tmp_path)

    manifest = read_json(missing / "project.json")
    assert manifest["title"] == "Test2"
    assert manifest["topic"] == "Test2"
    assert (missing / "v1" / "draft.md").exists()
    assert result["project"]["path"] == str(missing.resolve())


def test_ui_auto_create_with_seed_defaults_to_rewrite_baseline(tmp_path: Path) -> None:
    seed = tmp_path / "seed.md"
    seed.write_text("# Seed Draft Title\n\nOriginal seed body.", encoding="utf-8")
    project = tmp_path / "papers" / "auto-rewrite"

    result = _run_project(
        {"projectDir": str(project), "offline": True, "cycles": "1", "seedDraftFile": str(seed)},
        tmp_path,
    )

    manifest = read_json(project / "project.json")
    assert manifest["title"] == "Seed Draft Title"
    assert manifest["topic"] == "Seed Draft Title"
    assert manifest["task"]["start_mode"] == "rewrite"
    assert read_json(project / "v1" / "metadata.json")["imported_seed_baseline"] is True
    assert "Original seed body." in (project / "v1" / "draft.md").read_text(encoding="utf-8")
    assert (project / "v2" / "draft.md").exists()
    assert [Path(path).name for path in result["created"]] == ["v2"]


def test_ui_auto_create_uses_loader_title_for_pdf_seed(tmp_path: Path) -> None:
    seed = tmp_path / "draft.pdf"
    seed.write_text(
        "Adaptability, Scalability and Sustainability (ASaS) of complex health interventions\n\nPDF body.",
        encoding="utf-8",
    )
    fake_loader = _write_fake_smart_loader(tmp_path / "fake-smart-loader")
    project = tmp_path / "papers" / "test2"

    _run_project(
        {
            "projectDir": str(project),
            "offline": True,
            "cycles": "1",
            "seedDraftFile": str(seed),
            "smartLoader": str(fake_loader),
        },
        tmp_path,
    )

    manifest = read_json(project / "project.json")
    assert manifest["title"] == "Adaptability, Scalability and Sustainability (ASaS) of complex health interventions"
    assert manifest["topic"] == manifest["title"]
    assert manifest["task"]["start_mode"] == "rewrite"


def test_ui_offline_checkbox_defaults_unchecked() -> None:
    offline_input = _INDEX_HTML.split('id="offline"', 1)[1].split(">", 1)[0]

    assert "checked" not in offline_input


def test_ui_terminal_provider_checkbox_defaults_checked() -> None:
    terminal_input = _INDEX_HTML.split('id="allowLocalAgents"', 1)[1].split(">", 1)[0]

    assert "checked" in terminal_input


def test_ui_exposes_human_intervention_controls() -> None:
    assert 'id="fromVersion"' in _INDEX_HTML
    assert 'id="focusGuidance"' in _INDEX_HTML
    assert 'id="maxPromptChars"' in _INDEX_HTML
    assert 'id="referenceSearch"' in _INDEX_HTML
    assert 'id="referenceSearchMaxResults"' in _INDEX_HTML
    assert 'fromVersion: $("fromVersion").value' in _APP_JS
    assert 'additionalContext: $("focusGuidance").value' in _APP_JS
    assert 'maxPromptChars: $("maxPromptChars").value' in _APP_JS
    assert 'referenceSearch: {' in _APP_JS
    assert 'enabled: $("referenceSearch").checked' in _APP_JS
    assert 'maxResults: $("referenceSearchMaxResults").value' in _APP_JS


def test_ui_run_rejects_non_project_directory_with_files(tmp_path: Path) -> None:
    existing = tmp_path / "papers" / "not-a-project"
    existing.mkdir(parents=True)
    (existing / "notes.md").write_text("not a manifest", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="new or empty project folder"):
        _run_project({"projectDir": str(existing), "offline": True}, tmp_path)


def test_ui_project_payload_missing_project_has_helpful_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="project.json"):
        _project_payload(tmp_path)


def test_ui_get_project_missing_returns_json_error(tmp_path: Path) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(tmp_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    missing = tmp_path / "papers" / "test2"
    url = f"http://127.0.0.1:{server.server_port}/api/project?projectDir={quote(str(missing))}"

    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(url, timeout=5)
        payload = json.loads(exc_info.value.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert exc_info.value.code == 400
    assert "auto-create" in payload["error"]
    assert "project.json" in payload["error"]


def test_ui_reuses_existing_running_job_for_same_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = init_project(
        root=tmp_path,
        slug="locked-run",
        title="Locked Run",
        topic="prevent duplicate runs",
        brief="Only one job should run per project.",
    )
    started = threading.Event()
    release = threading.Event()
    calls = []

    def fake_run_project(payload: dict, cwd: Path, progress: object = None) -> dict:
        calls.append(payload["projectDir"])
        started.set()
        release.wait(timeout=2)
        return {
            "created": [],
            "project": {
                "path": str(project),
                "manifest": {},
                "versions": [],
                "acceptedVersion": None,
                "latest": {},
            },
            "latest": {},
        }

    monkeypatch.setattr("asl.ui._run_project", fake_run_project)
    jobs = {}
    project_jobs = {}
    lock = threading.Lock()
    payload = {"projectDir": str(project)}

    first = _start_run_job(payload, tmp_path, jobs, project_jobs, lock)
    assert first["reused"] is False
    assert started.wait(timeout=1)

    second = _start_run_job(payload, tmp_path, jobs, project_jobs, lock)
    assert second["reused"] is True
    assert second["jobId"] == first["jobId"]
    assert len(calls) == 1

    release.set()
    for _ in range(20):
        if jobs[first["jobId"]].snapshot()["status"] == "succeeded":
            break
        time.sleep(0.05)

    assert jobs[first["jobId"]].snapshot()["status"] == "succeeded"
    assert project_jobs == {}


def test_llm_failure_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise urllib.error.URLError("network unavailable")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)

    result = LLMClient().generate("prompt", "fallback text")

    assert result.provider == "offline-after-error"
    assert result.text.startswith("fallback text")
    assert "offline fallback used" in result.text


def test_model_chain_parses_provider_model_and_endpoint() -> None:
    specs = parse_model_chain("openai:gpt-4.1,openai-compat:llama@http://127.0.0.1:8000/v1")

    assert specs[0].provider == "openai"
    assert specs[0].model == "gpt-4.1"
    assert specs[1].provider == "openai-compat"
    assert specs[1].model == "llama"
    assert specs[1].endpoint == "http://127.0.0.1:8000/v1"


def test_llm_client_uses_role_specific_model_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = []

    def fake_urlopen(request: object, timeout: int) -> object:
        calls.append(_request_json(request))
        return _JsonResponse({"output_text": "ok"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = LLMClient(
        model_routes={
            "default": "openai:default-model",
            "draft": "openai:draft-model",
            "review": "openai:review-model",
        }
    )

    draft = client.generate("draft prompt", "fallback", role="draft")
    review = client.generate("review prompt", "fallback", role="review")

    assert draft.model == "draft-model"
    assert review.model == "review-model"
    assert [call["model"] for call in calls] == ["draft-model", "review-model"]


def test_llm_client_tries_model_alternatives(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
    urls = []

    def fake_urlopen(request: object, timeout: int) -> object:
        urls.append(getattr(request, "full_url"))
        return _JsonResponse({"choices": [{"message": {"content": "deepseek ok"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = LLMClient(model_routes={"draft": "openai:gpt-missing,deepseek:deepseek-chat"})

    result = client.generate("prompt", "fallback", role="draft")

    assert result.provider == "deepseek"
    assert result.model == "deepseek-chat"
    assert result.text == "deepseek ok"
    assert "missing credentials" in result.attempts[0]
    assert urls == ["https://api.deepseek.com/v1/chat/completions"]


def test_catalog_exposes_teamagents_provider_presets() -> None:
    catalog = catalog_payload()
    routes = {model["id"]: model["route"] for model in catalog["models"]}
    providers = {provider["provider"]: provider for provider in catalog["providers"]}

    assert routes["deepseek-reasoner"] == "deepseek:deepseek-reasoner"
    assert routes["minimax-m3"] == "minimax:minimax-m3"
    assert routes["minimax-m2.7"] == "minimax:minimax-m2.7"
    assert routes["vllm"].endswith("@http://127.0.0.1:8000/v1")
    assert providers["openai-compat"]["requiresApiKey"] is False
    assert providers["anthropic"]["apiKeyEnvs"] == ["ANTHROPIC_API_KEY"]


def test_openai_compat_uses_teamagents_default_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    urls = []

    def fake_urlopen(request: object, timeout: int) -> object:
        urls.append(getattr(request, "full_url"))
        return _JsonResponse({"choices": [{"message": {"content": "local ok"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = LLMClient(model_routes={"draft": "openai-compat:local-model"})

    result = client.generate("prompt", "fallback", role="draft")

    assert result.text == "local ok"
    assert urls == ["http://127.0.0.1:8000/v1/chat/completions"]


def test_catalog_exposes_local_agent_and_cc_switch_presets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cc_switch = tmp_path / "cc-switch.json"
    cc_switch.write_text(
        """
        {
          "providers": {
            "deepseek": {
              "name": "DeepSeek Anthropic",
              "env": {
                "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
                "ANTHROPIC_AUTH_TOKEN": "fake-token",
                "ANTHROPIC_MODEL": "deepseek-v4-pro"
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("ASL_CC_SWITCH_CONFIG", str(cc_switch))
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-test")
    monkeypatch.setenv("CODEX_MODEL", "gpt-test")

    def fake_which(command: str) -> Optional[str]:
        return f"/usr/bin/{command}" if command in {"claude", "codex"} else None

    monkeypatch.setattr("asl.local_providers.shutil.which", fake_which)
    catalog = catalog_payload()
    routes = {model["id"]: model["route"] for model in catalog["models"]}
    providers = {provider["provider"]: provider for provider in catalog["providers"]}

    assert routes["claude-code-local"] == "claude-code:claude-sonnet-test"
    assert routes["codex-local"] == "codex:gpt-test"
    assert routes["cc-switch-deepseek"] == "claude-code:deepseek-v4-pro@cc-switch:deepseek"
    assert routes["cc-switch-api-deepseek-deepseek-v4-pro"] == "anthropic:deepseek-v4-pro@cc-switch:deepseek"
    assert providers["claude-code"]["configured"] is True
    assert providers["codex"]["configured"] is True

    settings = cc_switch_settings_for_ref("cc-switch:deepseek", cwd=tmp_path)
    assert settings and settings["env"]["ANTHROPIC_MODEL"] == "deepseek-v4-pro"


def test_catalog_expands_cc_switch_glm_model_variants(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cc_switch = tmp_path / "cc-switch.json"
    cc_switch.write_text(
        """
        {
          "providers": {
            "zhipu-glm": {
              "name": "Zhipu GLM",
              "env": {
                "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
                "ANTHROPIC_AUTH_TOKEN": "fake-token",
                "ANTHROPIC_MODEL": "glm-5.2"
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("ASL_CC_SWITCH_CONFIG", str(cc_switch))
    monkeypatch.setattr("asl.local_providers.shutil.which", lambda command: "/usr/bin/claude")

    catalog = catalog_payload()
    routes = {model["id"]: model["route"] for model in catalog["models"]}
    route_values = set(routes.values())

    assert routes["cc-switch-zhipu-glm"] == "claude-code:glm-5.2@cc-switch:zhipu-glm"
    assert "claude-code:glm-5.1@cc-switch:zhipu-glm" in route_values
    assert "anthropic:glm-5.2@cc-switch:zhipu-glm" in route_values
    assert "anthropic:glm-5.1@cc-switch:zhipu-glm" in route_values


def test_catalog_exposes_cc_switch_openai_compatible_routes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cc_switch = tmp_path / "cc-switch.json"
    cc_switch.write_text(
        """
        {
          "providers": {
            "zhipu-glm": {
              "name": "Zhipu GLM",
              "env": {
                "OPENAI_BASE_URL": "https://open.bigmodel.cn/api/paas/v4",
                "ANTHROPIC_AUTH_TOKEN": "fake-token",
                "ANTHROPIC_MODEL": "glm-5.2"
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("ASL_CC_SWITCH_CONFIG", str(cc_switch))

    catalog = catalog_payload()
    routes = {model["id"]: model["route"] for model in catalog["models"]}
    route_values = set(routes.values())

    assert "openai-compat:glm-5.2@cc-switch:zhipu-glm" in route_values
    assert "openai-compat:glm-5.1@cc-switch:zhipu-glm" in route_values


def test_cc_switch_sqlite_profiles_are_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "cc-switch.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE providers (
            id TEXT NOT NULL,
            app_type TEXT NOT NULL,
            name TEXT NOT NULL,
            settings_config TEXT NOT NULL,
            sort_index INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO providers (id, app_type, name, settings_config, sort_index) VALUES (?, ?, ?, ?, ?)",
        (
            "deepseek-id",
            "claude",
            "DeepSeek",
            '{"env":{"ANTHROPIC_MODEL":"deepseek-v4-pro","ANTHROPIC_AUTH_TOKEN":"fake-token"}}',
            1,
        ),
    )
    conn.commit()
    conn.close()
    monkeypatch.delenv("ASL_CC_SWITCH_CONFIG", raising=False)
    monkeypatch.setenv("ASL_CC_SWITCH_DB", str(db_path))
    monkeypatch.setattr("asl.local_providers.shutil.which", lambda command: "/usr/bin/claude")

    catalog = catalog_payload()
    routes = {model["id"]: model["route"] for model in catalog["models"]}

    assert routes["cc-switch-deepseek"] == "claude-code:deepseek-v4-pro@cc-switch:deepseek"


def test_llm_client_calls_claude_code_with_cc_switch_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cc_switch = tmp_path / "cc-switch.json"
    cc_switch.write_text(
        '{"providers":{"deepseek":{"env":{"ANTHROPIC_MODEL":"deepseek-v4-pro","ANTHROPIC_AUTH_TOKEN":"fake-token"}}}}',
        encoding="utf-8",
    )
    calls = []
    monkeypatch.setenv("ASL_CC_SWITCH_CONFIG", str(cc_switch))
    monkeypatch.setattr("asl.llm.shutil.which", lambda command: "/usr/bin/claude" if command == "claude" else None)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="claude draft\n", stderr="")

    monkeypatch.setattr("asl.llm.subprocess.run", fake_run)
    client = LLMClient(model_routes={"draft": "claude-code:deepseek-v4-pro@cc-switch:deepseek"})

    result = client.generate("Draft this.", "fallback", role="draft")

    assert result.text == "claude draft"
    command = calls[0][0][0]
    assert command[:2] == ["claude", "-p"]
    assert command[command.index("--tools") + 1] == ""
    assert "--settings" in command
    settings = command[command.index("--settings") + 1]
    assert "fake-token" in settings
    assert json.loads(settings)["env"]["ANTHROPIC_MODEL"] == "deepseek-v4-pro"
    assert calls[0][1]["input"].startswith("You are assisting with transparent academic drafting")


def test_llm_client_calls_cc_switch_anthropic_api_route(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cc_switch = tmp_path / "cc-switch.json"
    cc_switch.write_text(
        """
        {
          "providers": {
            "zhipu-glm": {
              "env": {
                "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
                "ANTHROPIC_AUTH_TOKEN": "fake-token",
                "ANTHROPIC_MODEL": "glm-5.2"
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    captured = {}
    monkeypatch.setenv("ASL_CC_SWITCH_CONFIG", str(cc_switch))

    def fake_urlopen(request: object, timeout: int) -> object:
        captured["url"] = getattr(request, "full_url")
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["payload"] = _request_json(request)
        return _JsonResponse({"content": [{"type": "text", "text": "glm ok"}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = LLMClient(model_routes={"draft": "anthropic:glm-5.1@cc-switch:zhipu-glm"})

    result = client.generate("Draft this.", "fallback", role="draft")

    assert result.text == "glm ok"
    assert result.provider == "anthropic"
    assert captured["url"] == "https://open.bigmodel.cn/api/anthropic/messages"
    assert captured["payload"]["model"] == "glm-5.1"
    assert captured["headers"]["authorization"] == "Bearer fake-token"


def test_llm_client_calls_cc_switch_openai_compatible_route(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cc_switch = tmp_path / "cc-switch.json"
    cc_switch.write_text(
        """
        {
          "providers": {
            "zhipu-glm": {
              "env": {
                "OPENAI_BASE_URL": "https://open.bigmodel.cn/api/paas/v4",
                "ANTHROPIC_AUTH_TOKEN": "fake-token",
                "ANTHROPIC_MODEL": "glm-5.2"
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    captured = {}
    monkeypatch.setenv("ASL_CC_SWITCH_CONFIG", str(cc_switch))

    def fake_urlopen(request: object, timeout: int) -> object:
        captured["url"] = getattr(request, "full_url")
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["payload"] = _request_json(request)
        return _JsonResponse({"choices": [{"message": {"content": "glm ok"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = LLMClient(model_routes={"draft": "openai-compat:glm-5.1@cc-switch:zhipu-glm"})

    result = client.generate("Draft this.", "fallback", role="draft")

    assert result.text == "glm ok"
    assert result.provider == "openai-compat"
    assert captured["url"] == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    assert captured["payload"]["model"] == "glm-5.1"
    assert captured["headers"]["authorization"] == "Bearer fake-token"


def test_llm_client_retries_transient_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = []
    sleeps = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("asl.llm.time.sleep", lambda seconds: sleeps.append(seconds))

    def fake_urlopen(request: object, timeout: int) -> object:
        attempts.append(getattr(request, "full_url"))
        if len(attempts) == 1:
            raise urllib.error.URLError("temporary disconnect")
        return _JsonResponse({"output_text": "retry ok"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = LLMClient(model_routes={"draft": "openai:gpt-retry"})

    result = client.generate("Draft this.", "fallback", role="draft")

    assert result.text == "retry ok"
    assert len(attempts) == 2
    assert sleeps == [1]


def test_llm_client_can_disable_local_terminal_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("asl.llm.shutil.which", lambda command: "/usr/bin/claude")

    def fail_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise AssertionError("local agent subprocess should not run")

    monkeypatch.setattr("asl.llm.subprocess.run", fail_run)
    client = LLMClient(
        model_routes={"draft": "claude-code:default"},
        allow_local_agents=False,
    )

    result = client.generate("Draft this.", "fallback", role="draft")

    assert result.provider == "offline-after-error"
    assert "local terminal providers disabled" in result.attempts[0]


def test_llm_client_can_allow_claude_code_web_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr("asl.llm.shutil.which", lambda command: "/usr/bin/claude" if command == "claude" else None)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="claude web draft\n", stderr="")

    monkeypatch.setattr("asl.llm.subprocess.run", fake_run)
    client = LLMClient(model_routes={"draft": "claude-code:default"}, allow_agent_tools=True)

    result = client.generate("Draft this with sources.", "fallback", role="draft")

    assert result.text == "claude web draft"
    command = calls[0][0][0]
    assert command[command.index("--tools") + 1] == "WebSearch,WebFetch"
    assert "If you use web tools" in calls[0][1]["input"]


def test_llm_client_reads_codex_exec_last_message(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr("asl.llm.shutil.which", lambda command: "/usr/bin/codex" if command == "codex" else None)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        command = args[0]
        calls.append((command, kwargs))
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("codex draft\n", encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("asl.llm.subprocess.run", fake_run)
    client = LLMClient(model_routes={"draft": "codex:gpt-test"})

    result = client.generate("Draft this.", "fallback", role="draft")

    assert result.text == "codex draft"
    command = calls[0][0]
    exec_index = command.index("exec")
    approval_index = command.index("--ask-for-approval")
    assert command[0] == "codex"
    assert approval_index < exec_index
    assert command[approval_index + 1] == "never"
    assert "--ask-for-approval" not in command[exec_index:]
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert "--model" in command
    assert "gpt-test" in command
    assert calls[0][1]["input"].startswith("You are assisting with transparent academic drafting")


def test_llm_client_can_enable_codex_web_search(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr("asl.llm.shutil.which", lambda command: "/usr/bin/codex" if command == "codex" else None)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        command = args[0]
        calls.append((command, kwargs))
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("codex web draft\n", encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("asl.llm.subprocess.run", fake_run)
    client = LLMClient(model_routes={"draft": "codex:gpt-test"}, allow_agent_tools=True)

    result = client.generate("Draft this with sources.", "fallback", role="draft")

    assert result.text == "codex web draft"
    command = calls[0][0]
    exec_index = command.index("exec")
    approval_index = command.index("--ask-for-approval")
    assert command[0] == "codex"
    assert "--search" in command[:exec_index]
    assert approval_index < exec_index
    assert command[approval_index + 1] == "never"
    assert "If you use web tools" in calls[0][1]["input"]


def test_pipeline_records_stage_model_routes(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="models",
        title="Models",
        topic="model routing",
        brief="Use model routing.",
        model_routes={
            "draft": "anthropic:claude-sonnet-4-20250514",
            "review": "deepseek:deepseek-chat",
        },
    )

    created = PaperPipeline(project, client=LLMClient(offline=True)).run()

    metadata = read_json(created[0] / "metadata.json")
    assert metadata["models"]["requested"]["draft"] == ["anthropic:claude-sonnet-4-20250514"]
    assert metadata["models"]["requested"]["review"] == ["deepseek:deepseek-chat"]
    assert metadata["models"]["used"]["draft"]["provider"] == "offline"
    assert metadata["models"]["used"]["reviews"]["methods"]["provider"] == "offline"


def test_discover_topic_mode_can_start_without_fixed_topic(tmp_path: Path) -> None:
    code = main(
        [
            "init",
            "--root",
            str(tmp_path),
            "--slug",
            "discover",
            "--title",
            "Discover",
            "--start-mode",
            "discover-topic",
            "--brief",
            "Dataset: municipal program outcomes. Reference: policy adoption memo.",
        ]
    )

    assert code == 0
    project = tmp_path / "papers" / "discover"
    code = main(["run", str(project), "--offline"])

    assert code == 0
    assert (project / "v1" / "topic_proposal.md").exists()
    metadata = read_json(project / "v1" / "metadata.json")
    assert metadata["start_mode"] == "discover-topic"
    assert metadata["accepted"] is True


def test_discover_topic_writes_back_title_and_persists(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="untitled-paper",
        title="Untitled Paper",
        topic=None,
        start_mode="discover-topic",
        brief="Dataset: municipal program outcomes.",
    )
    PaperPipeline(project, client=LLMClient(offline=True)).run(cycles=2)

    manifest = read_json(project / "project.json")
    assert not manifest["title"].lower().startswith("untitled")
    assert not manifest["topic"].upper().startswith("TODO")
    assert manifest["title"] == manifest["topic"]
    assert manifest["task"]["topic_locked"] is True
    # Topic is discovered once; later cycles reuse it (no re-discovery / drift).
    assert (project / "v1" / "topic_proposal.md").exists()
    assert not (project / "v2" / "topic_proposal.md").exists()
    assert (project / "v1" / "draft.md").read_text().splitlines()[0].lstrip("# ").strip() == manifest["title"]


def test_parse_topic_candidates_handles_blocks_and_fallback() -> None:
    from asl.pipeline import _parse_topic_candidates

    text = (
        "## Topic 1\nTopic: A\nResearch question: A?\nAnchor papers: 10.pdf, 12.pdf\nRationale: r1\n\n"
        "## Topic 2\nTopic: B\nResearch question: B?\nAnchor papers: 24.pdf\nRationale: r2\n\n"
        "Evidence boundary: conceptual only"
    )
    candidates = _parse_topic_candidates(text)
    assert [c["topic"] for c in candidates] == ["A", "B"]
    assert candidates[0]["anchors"] == ["10.pdf", "12.pdf"]
    # Legacy single-topic output still yields one candidate.
    legacy = _parse_topic_candidates("Topic: Solo\nResearch question: Q?")
    assert len(legacy) == 1 and legacy[0]["topic"] == "Solo"


def _discover_project_with_refs(tmp_path: Path, slug: str) -> Path:
    refs = tmp_path / "refs"
    refs.mkdir(exist_ok=True)
    for i in range(1, 5):
        (refs / f"{i}.md").write_text(f"# Reference {i}\n\n" + ("body " * 80), encoding="utf-8")
    return init_project(
        root=tmp_path,
        slug=slug,
        title="Untitled Paper",
        topic=None,
        start_mode="discover-topic",
        brief="Synthesize the references.",
    )


def test_discover_topic_auto_selects_top_candidate_and_records_anchors(tmp_path: Path) -> None:
    project = _discover_project_with_refs(tmp_path, "auto")
    refs = tmp_path / "refs"
    PaperPipeline(
        project, client=LLMClient(offline=True), reference_paths=(refs,),
        topic_mode="auto", topic_count=3,
    ).run()

    manifest = read_json(project / "project.json")
    assert not manifest["topic"].upper().startswith("TODO")
    assert manifest["task"]["topic_locked"] is True
    assert isinstance(manifest.get("topic_anchors"), list) and manifest["topic_anchors"]
    assert len(read_json(project / "topic_candidates.json")) == 3
    assert (project / "v1" / "draft.md").exists()


def test_discover_topic_manual_waits_for_choice(tmp_path: Path) -> None:
    project = _discover_project_with_refs(tmp_path, "manual")
    refs = tmp_path / "refs"

    with pytest.raises(TopicSelectionPending) as exc_info:
        PaperPipeline(
            project, client=LLMClient(offline=True), reference_paths=(refs,),
            topic_mode="manual", topic_count=3,
        ).run()
    assert len(exc_info.value.candidates) == 3
    assert (project / "topic_proposals.md").exists()
    assert not (project / "v1").exists()  # no half-built version left behind

    # The chosen-topic re-run reuses cached candidates and drafts from v1.
    created = PaperPipeline(
        project, client=LLMClient(offline=True), reference_paths=(refs,),
        topic_mode="manual", topic_choice=2, topic_count=3,
    ).run()
    assert created[0].name == "v1"
    assert (project / "v1" / "draft.md").exists()
    assert read_json(project / "project.json")["task"]["topic_locked"] is True


def test_reference_focus_rotates_and_keeps_anchors(tmp_path: Path) -> None:
    refs = tmp_path / "refs"
    refs.mkdir()
    for i in range(1, 13):
        (refs / f"{i}.md").write_text(f"# Reference {i}\n\n" + ("body " * 60), encoding="utf-8")
    project = init_project(
        root=tmp_path, slug="rotate", title="Untitled Paper", topic=None,
        start_mode="discover-topic", brief="Synthesize.",
    )
    PaperPipeline(
        project, client=LLMClient(offline=True), reference_paths=(refs,),
        topic_mode="auto", topic_count=3,
    ).run(cycles=2)

    anchors = read_json(project / "project.json")["topic_anchors"]
    focus1 = read_json(project / "v1" / "metadata.json")["reference_focus"]
    focus2 = read_json(project / "v2" / "metadata.json")["reference_focus"]
    # Anchors are featured every cycle; rotation brings in papers v1 did not feature.
    assert set(anchors).issubset(set(focus1))
    assert set(anchors).issubset(set(focus2))
    assert set(focus2) - set(focus1)


def test_render_draft_doc_writes_word_openable_rtf(tmp_path: Path) -> None:
    from asl.doc_render import markdown_to_rtf, render_draft_doc

    markdown = (
        "# Title\n\nA paragraph with **bold** and *italic* and an em—dash.\n\n"
        "## Section\n\n- a bullet\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    version = tmp_path / "v1"
    version.mkdir()
    (version / "draft.md").write_text(markdown, encoding="utf-8")
    out = render_draft_doc(version)
    assert out is not None and out.name == "draft.rtf"

    rtf = out.read_text(encoding="ascii")
    assert rtf.startswith(r"{\rtf1")
    assert rtf.rstrip().endswith("}")
    assert r"{\b " in rtf  # bold run
    assert r"\trowd" in rtf  # the table became an RTF table
    assert "\\u8212?" in rtf  # the em-dash (U+2014) is unicode-escaped, not raw bytes
    assert "—" not in rtf  # body is pure ASCII
    # Braces are balanced so Word can parse the document.
    assert rtf.count("{") == rtf.count("}")
    # No draft -> no file.
    assert render_draft_doc(tmp_path / "empty") is None


def test_draft_prompt_names_focus_and_forbids_unavailable_excuse() -> None:
    from asl.templates import draft_prompt, iterative_draft_prompt

    manifest = {"title": "T", "topic": "sustainability"}
    direct = draft_prompt(manifest, "plan", "Brief mentioning 4.pdf", focus=["4.pdf", "20.pdf"])
    assert "Focus references for this draft: 4.pdf, 20.pdf" in direct
    assert "never describe a provided reference as unavailable" in direct
    iterative = iterative_draft_prompt(
        manifest, "plan", "brief", "previous", "reviews", "revision", focus=["9.pdf"]
    )
    assert "Focus references for this draft: 9.pdf" in iterative
    assert "text-pending" in iterative


def test_underused_references_parsed_from_reviews(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path, slug="underused", title="U", topic="t", brief="b",
    )
    pipeline = PaperPipeline(project, client=LLMClient(offline=True))
    baseline = project / "v1"
    (baseline / "reviews").mkdir(parents=True)
    (baseline / "reviews" / "evidence.md").write_text(
        "Major issues\nUnderused references: 4.pdf, 19.pdf\n", encoding="utf-8"
    )
    # Real models prefix the line with a list number and markdown bold.
    (baseline / "reviews" / "methods.md").write_text(
        "5. **Underused references:** 27.pdf\n", encoding="utf-8"
    )
    (baseline / "reviews" / "style.md").write_text(
        "Underused references: none\n", encoding="utf-8"
    )
    assert pipeline._underused_from_reviews(baseline) == ["4.pdf", "19.pdf", "27.pdf"]


def test_preflight_raises_when_configured_model_unavailable(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="broken",
        title="Broken",
        topic="quality gates",
        brief="Use quality gates.",
    )
    client = LLMClient(
        offline=False,
        model="offline",
        model_routes={"score": "deepseek:deepseek-v4-flash@cc-switch:__no_such_profile__"},
    )
    with pytest.raises(ModelUnavailableError) as exc_info:
        PaperPipeline(project, client=client).run()
    assert "score" in str(exc_info.value)
    # The run aborts before producing any version.
    assert not (project / "v1").exists()


def test_worse_candidate_is_kept_but_not_accepted(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="quality",
        title="Quality",
        topic="quality gates",
        brief="Use quality gates.",
    )
    first = PaperPipeline(project, client=LLMClient(offline=True)).run()[0]

    second = PaperPipeline(project, client=_WorseCandidateClient()).run()[0]

    assert (project / "accepted_version.txt").read_text(encoding="utf-8").strip() == first.name
    assert (second / "draft.md").exists()
    metadata = read_json(second / "metadata.json")
    assert metadata["accepted"] is False
    assert metadata["quality_gate"]["decision"] == "rejected"
    assert metadata["previous_accepted_version"] == first.name
    assert metadata["models"]["used"]["score"][0]["provider"] == "fake"
    assert metadata["models"]["used"]["score"][0]["model"] == "worse-scorer"


def test_fallback_candidate_never_replaces_previous_accepted(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="fallback-gate",
        title="Fallback Gate",
        topic="fallback candidates",
        brief="Preserve accepted drafts.",
    )
    first = PaperPipeline(project, client=LLMClient(offline=True)).run()[0]

    second = PaperPipeline(project, client=_FallbackCandidateClient()).run()[0]

    assert (project / "accepted_version.txt").read_text(encoding="utf-8").strip() == first.name
    metadata = read_json(second / "metadata.json")
    assert metadata["accepted"] is False
    assert metadata["quality_gate"]["decision"] == "rejected"
    assert "offline fallback" in metadata["quality_gate"]["reason"]


def test_missing_score_model_does_not_replace_previous_accepted(tmp_path: Path) -> None:
    project = init_project(
        root=tmp_path,
        slug="score-gate",
        title="Score Gate",
        topic="score model availability",
        brief="Preserve accepted drafts.",
    )
    first = PaperPipeline(project, client=LLMClient(offline=True)).run()[0]

    second = PaperPipeline(project, client=_MissingScoreClient()).run()[0]

    assert (project / "accepted_version.txt").read_text(encoding="utf-8").strip() == first.name
    metadata = read_json(second / "metadata.json")
    assert metadata["accepted"] is False
    assert metadata["quality_gate"]["decision"] == "rejected"
    assert "scoring model" in metadata["quality_gate"]["reason"]
    assert metadata["models"]["used"]["score"][0]["provider"] == "offline"


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


def _write_fake_smart_loader(path: Path) -> Path:
    script = f"""#!{sys.executable}
import json
import pathlib
import sys

input_path = pathlib.Path(sys.argv[1])
text = input_path.read_text(encoding="utf-8")
title = next((line.strip().lstrip("#").strip() for line in text.splitlines() if line.strip()), input_path.stem)
sample = f"sample from {{input_path.name}}: {{text.strip()}}"
result = {{
    "rootPath": str(input_path.parent),
    "documents": [
        {{
            "id": input_path.stem,
            "sourcePath": str(input_path),
            "relativePath": input_path.name,
            "format": "markdown",
            "title": title,
            "text": sample,
            "markdown": sample,
            "chunks": [],
            "assets": [],
            "warnings": [],
            "metadata": {{"sizeBytes": input_path.stat().st_size, "loader": "fake", "info": {{"Title": title}}}},
        }}
    ],
    "chunks": [
        {{
            "id": f"{{input_path.stem}}_chunk_1",
            "documentId": input_path.stem,
            "text": sample,
            "markdown": sample,
            "index": 0,
            "metadata": {{
                "sourcePath": str(input_path),
                "relativePath": input_path.name,
                "format": "markdown",
                "tokenEstimate": 1,
                "startChar": 0,
                "endChar": len(sample),
            }},
        }}
    ],
    "errors": [],
    "summary": {{
        "discoveredFiles": 1,
        "loadedFiles": 1,
        "skippedFiles": 0,
        "failedFiles": 0,
        "chunks": 1,
        "assets": 0,
    }},
}}
sys.stdout.write(json.dumps(result))
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)
    return path


class _JsonResponse:
    def __init__(self, body: dict) -> None:
        import json

        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self) -> "_JsonResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def _request_json(request: object) -> dict:
    import json

    data = getattr(request, "data")
    return json.loads(data.decode("utf-8"))


class _CapturingBetterClient:
    def __init__(self) -> None:
        self.prompts: list[tuple[str, str]] = []

    def with_model_routes(self, routes: dict[str, str]) -> "_CapturingBetterClient":
        return self

    def route_metadata(self) -> dict[str, list[str]]:
        return {"draft": ["fake:writer"], "score": ["fake:score"]}

    def generate(self, prompt: str, fallback: str, role: str = "default") -> LLMResult:
        self.prompts.append((role, prompt))
        if role == "plan":
            return LLMResult(text="# Research Plan\n\nConcise plan.", provider="fake", model="planner")
        if role == "draft":
            return LLMResult(text="# Model Draft\n\nSupported candidate.", provider="fake", model="writer")
        if role == "review":
            return LLMResult(text="# Review\n\nTighten evidence and methods.", provider="fake", model="reviewer")
        if role == "revision":
            return LLMResult(text="# Revision Plan\n\nAddress review findings.", provider="fake", model="reviser")
        return LLMResult(text=fallback, provider="fake", model=f"{role}-fallback")

    def generate_all(self, prompt: str, fallback: str, role: str) -> list[LLMResult]:
        self.prompts.append((role, prompt))
        if role == "score":
            return [
                LLMResult(
                    text='{"verdict":"better","previous_score":5,"candidate_score":7,"rationale":"More responsive."}',
                    provider="fake",
                    model="score",
                )
            ]
        return [self.generate(prompt, fallback, role=role)]

    def prompt_for_role(self, role: str) -> str:
        for found_role, prompt in reversed(self.prompts):
            if found_role == role:
                return prompt
        raise AssertionError(f"no prompt captured for role {role}")


class _WorseCandidateClient:
    def with_model_routes(self, routes: dict[str, str]) -> "_WorseCandidateClient":
        return self

    def route_metadata(self) -> dict[str, list[str]]:
        return {"score": ["fake:worse-scorer"]}

    def generate(self, prompt: str, fallback: str, role: str = "default") -> LLMResult:
        if role == "draft":
            return LLMResult(text="# Worse Draft\n\nUnsupported claim.", provider="fake", model="worse-writer")
        return LLMResult(text=fallback, provider="fake", model=f"{role}-fallback")

    def generate_all(self, prompt: str, fallback: str, role: str) -> list[LLMResult]:
        if role == "score":
            return [
                LLMResult(
                    text='{"verdict":"worse","previous_score":8,"candidate_score":2,"rationale":"Less complete."}',
                    provider="fake",
                    model="worse-scorer",
                )
            ]
        return [self.generate(prompt, fallback, role=role)]


class _FallbackCandidateClient:
    def with_model_routes(self, routes: dict[str, str]) -> "_FallbackCandidateClient":
        return self

    def route_metadata(self) -> dict[str, list[str]]:
        return {"draft": ["fake:failing-writer"], "score": ["fake:score"]}

    def generate(self, prompt: str, fallback: str, role: str = "default") -> LLMResult:
        if role == "draft":
            return LLMResult(
                text="# Template Draft\n\nThis is fallback.",
                provider="offline-after-error",
                model="template",
                attempts=("fake:failing-writer: ValueError: failed",),
            )
        return LLMResult(text=fallback, provider="fake", model=f"{role}-fallback")

    def generate_all(self, prompt: str, fallback: str, role: str) -> list[LLMResult]:
        if role == "score":
            return [
                LLMResult(
                    text='{"verdict":"better","previous_score":4,"candidate_score":9,"rationale":"Looks structured."}',
                    provider="fake",
                    model="score",
                )
            ]
        return [self.generate(prompt, fallback, role=role)]


class _MissingScoreClient:
    def with_model_routes(self, routes: dict[str, str]) -> "_MissingScoreClient":
        return self

    def route_metadata(self) -> dict[str, list[str]]:
        return {"draft": ["fake:writer"], "score": ["missing:score"]}

    def generate(self, prompt: str, fallback: str, role: str = "default") -> LLMResult:
        if role == "draft":
            return LLMResult(text="# Real Candidate\n\nA real model wrote this.", provider="fake", model="writer")
        return LLMResult(text=fallback, provider="fake", model=f"{role}-fallback")

    def generate_all(self, prompt: str, fallback: str, role: str) -> list[LLMResult]:
        if role == "score":
            return [
                LLMResult(
                    text='{"verdict":"better","previous_score":4,"candidate_score":9,"rationale":"Offline heuristic."}',
                    provider="offline",
                    model="template",
                    attempts=("missing:score: missing credentials or endpoint",),
                )
            ]
        return [self.generate(prompt, fallback, role=role)]
