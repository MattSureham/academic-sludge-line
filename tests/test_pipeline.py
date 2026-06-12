import sys
import subprocess
import sqlite3
import urllib.error
from pathlib import Path
from typing import Optional

import pytest

from asl.catalog import catalog_payload
from asl.cli import main
from asl.html_render import render_version_html
from asl.local_providers import cc_switch_settings_for_ref
from asl.llm import LLMClient, LLMResult, parse_model_chain
from asl.pipeline import PaperPipeline, init_project
from asl.templates import (
    draft_prompt,
    offline_draft,
    offline_plan,
    offline_review,
    offline_revision,
    plan_prompt,
)
from asl.ui import _browse_payload, _create_directory, _create_project
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
    assert providers["claude-code"]["configured"] is True
    assert providers["codex"]["configured"] is True

    settings = cc_switch_settings_for_ref("cc-switch:deepseek", cwd=tmp_path)
    assert settings and settings["env"]["ANTHROPIC_MODEL"] == "deepseek-v4-pro"


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
    assert calls[0][1]["input"].startswith("You are assisting with transparent academic drafting")


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
    assert command[:2] == ["codex", "exec"]
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
    assert command[:3] == ["codex", "--search", "exec"]
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
sample = f"sample from {{input_path.name}}: {{text.strip()}}"
result = {{
    "rootPath": str(input_path.parent),
    "documents": [
        {{
            "id": input_path.stem,
            "sourcePath": str(input_path),
            "relativePath": input_path.name,
            "format": "markdown",
            "text": sample,
            "markdown": sample,
            "chunks": [],
            "assets": [],
            "warnings": [],
            "metadata": {{"sizeBytes": input_path.stat().st_size, "loader": "fake"}},
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
