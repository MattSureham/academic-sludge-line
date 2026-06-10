# Academic Sludge Line

Academic Sludge Line is a satirical name for a serious workflow: a transparent,
versioned pipeline for drafting, reviewing, and revising research papers.

It is not a paper mill. The framework deliberately marks missing evidence as
TODO, refuses fake citations, and separates drafts from verified research.

## What It Does

- Creates versioned paper workspaces under `papers/<slug>/v1`, `v2`, etc.
- Generates a research plan, draft, reviewer reports, and revision plan.
- Supports an offline template mode that runs with no dependencies.
- Optionally calls an LLM when `OPENAI_API_KEY` is available.
- Keeps a `sources.json` placeholder so claims can be audited later.

## Install

Recommended:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

No-install local run:

```bash
python -m asl.cli --version
```

If your system Python has a writable user site, this also works:

```bash
python -m pip install -e .
```

## Quick Start

```bash
asl init \
  --slug demo-policy-paper \
  --title "Demo Policy Paper" \
  --topic "a policy question that still needs verified evidence" \
  --brief-file examples/topic_brief.md

asl run papers/demo-policy-paper --cycles 2 --offline
```

You will get:

```text
papers/demo-policy-paper/
  project.json
  topic_brief.md
  sources.json
  v1/
    prompt.md
    research_plan.md
    draft.md
    reviews/
    revision_plan.md
    metadata.json
  v2/
    ...
```

## LLM Mode

Offline mode is the default safest path for tests and demos. To use an LLM:

```bash
export OPENAI_API_KEY="..."
export ASL_MODEL="your-model"
asl run papers/demo-policy-paper --cycles 1
```

If the API call fails, the pipeline falls back to the offline template and
records that in the generated text.

## Design

The framework mirrors the useful parts of large working-paper archives:

1. A paper is a folder.
2. A paper can have multiple versions.
3. Each version contains inputs, draft output, review output, and revision plans.
4. Every version has metadata.
5. Evidence and citations are tracked separately from prose.

## Guardrails

- Do not fabricate data.
- Do not fabricate citations.
- Do not fabricate empirical results.
- Use `[TODO: citation]` and `[TODO: evidence]` until claims are checked.
- Treat generated drafts as scaffolding, not publishable scholarship.

See [docs/ethics.md](docs/ethics.md) for the project stance.
