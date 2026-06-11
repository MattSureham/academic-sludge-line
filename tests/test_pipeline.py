import sys
import urllib.error
from pathlib import Path

import pytest

from asl.catalog import catalog_payload
from asl.cli import main
from asl.llm import LLMClient, parse_model_chain
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
