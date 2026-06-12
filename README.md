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
- Loads optional data and reference files through `smart-loader` when paths are provided.
- Writes static HTML views for every generated version.
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
  --research-question "What evidence would make this policy evaluation credible?" \
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
    html/
      index.html
      draft.html
      ...
    metadata.json
  v2/
    ...
```

## Data And References

If the adjacent `../smart-loader` project is available, ASL can load mixed
document folders into the draft context:

```bash
asl init \
  --slug demo-policy-paper \
  --title "Demo Policy Paper" \
  --topic "a policy question that still needs verified evidence" \
  --brief-file examples/topic_brief.md \
  --data data/ \
  --references references/

asl run papers/demo-policy-paper --offline
```

You can also add one-off inputs during a run:

```bash
asl run papers/demo-policy-paper \
  --data new_dataset.csv \
  --references notes/literature.md \
  --offline
```

Loaded material is written under each version's `inputs/` folder and injected
into the research plan and draft prompts. Set `ASL_SMART_LOADER` or pass
`--smart-loader` if the loader lives somewhere other than `../smart-loader`.

The loader accepts files or folders and supports Markdown, text, CSV, JSON,
HTML, PDF, DOCX, and legacy DOC through the adjacent `smart-loader` project.
PDF text is extracted directly when possible. For scanned or image-heavy PDFs,
ASL asks `smart-loader` to render PDF pages into image assets, then optionally
runs OCR over extracted image assets when `tesseract` is installed. DOCX files
are converted to Markdown and embedded images are extracted into the version's
`inputs/assets/` folder.

Useful loader options:

```bash
asl run papers/demo-policy-paper \
  --data data/ \
  --references references/ \
  --pdf-max-pages 40 \
  --pdf-dpi 220 \
  --ocr-language eng \
  --offline
```

Use `--no-pdf-render-pages` to skip PDF page images, or `--no-ocr-assets` to
skip local OCR. Missing Poppler (`pdftoppm`) or `tesseract` is recorded as a
warning in the generated input Markdown rather than silently ignored.

Every version also gets a static HTML bundle under `vN/html/`. Open
`vN/html/index.html` to read the prompt record, loaded inputs, draft, reviews,
revision plan, quality scores, metadata, and extracted image assets in a
browser-friendly format.

## Web UI

Start the local UI:

```bash
asl ui
```

Then open:

```text
http://127.0.0.1:8765
```

The UI can create paper workspaces, select models for each pipeline stage, add
data/reference paths, run cycles, and preview generated outputs. It uses the same
provider/model catalog as the CLI and defaults the local OpenAI-compatible vLLM
preset to `http://127.0.0.1:8000/v1`.

In the New Paper tab, `Workspace root` is the parent directory where ASL creates
`papers/<slug>/`. The Run tab's `Project path` points to one existing
`papers/<slug>/` project directory. Path fields include a local browser for
choosing files or folders and creating new folders before selecting a path.

## Starting Modes And Quality Gate

ASL can start a writing task in three modes:

```bash
# Start from a fixed topic.
asl init \
  --slug fixed-topic \
  --title "Fixed Topic Paper" \
  --topic "local public-program evaluation" \
  --brief-file examples/topic_brief.md

# Discover a topic from supplied data and references.
asl init \
  --slug discovered-topic \
  --title "Evidence-Led Paper" \
  --start-mode discover-topic \
  --data data/ \
  --references references/ \
  --brief "Find a responsible research question from the materials."

# Rewrite from an existing draft.
asl init \
  --slug rewrite-paper \
  --title "Rewrite Paper" \
  --topic "local public-program evaluation" \
  --start-mode rewrite \
  --seed-draft-file old_draft.md
```

`discover-topic` writes `topic_proposal.md` into each generated version before
planning and drafting. `rewrite` uses the previous accepted draft, or the seed
draft if there is no accepted version yet.

Every run still writes a candidate `vN/` directory, but ASL now maintains an
`accepted_version.txt` pointer. If the score gate judges the candidate worse
than the previous accepted draft, the candidate is kept as a rejected version and
the accepted pointer does not move.

Use multiple scoring models with `--score-model`:

```bash
asl run papers/fixed-topic \
  --cycles 3 \
  --draft-model openai-compat:local-model@http://127.0.0.1:8000/v1 \
  --review-model deepseek:deepseek-chat \
  --score-model deepseek:deepseek-reasoner,openai:gpt-4.1-mini
```

Score details are written to `quality_scores.json` and `metadata.json`.

## LLM Mode And Model Routing

Offline mode is the default safest path for tests and demos. To use an LLM:

```bash
export OPENAI_API_KEY="..."
export ASL_MODEL="your-model"
asl run papers/demo-policy-paper --cycles 1
```

If the API call fails, the pipeline falls back to the offline template and
records that in the generated text.

ASL also supports teamagents-style model routes:

```text
provider:model
```

Examples:

```bash
asl run papers/demo-policy-paper \
  --draft-model anthropic:claude-sonnet-4-20250514 \
  --review-model deepseek:deepseek-chat \
  --revision-model openai:gpt-4.1-mini
```

Each stage can have its own route:

- `--plan-model` for the research plan
- `--draft-model` for paper drafting
- `--review-model` for reviewer reports
- `--revision-model` for the revision plan
- `--score-model` for accepted/rejected quality scoring

Routes can include alternatives, tried left to right:

```bash
asl run papers/demo-policy-paper \
  --draft-model openai:gpt-4.1,anthropic:claude-sonnet-4-20250514 \
  --review-model deepseek:deepseek-chat,openai:gpt-4.1-mini
```

Bare model names default to OpenAI, so `--draft-model gpt-4.1-mini` is the same
as `--draft-model openai:gpt-4.1-mini`. `openai-compat` and `ollama` can target
local or custom endpoints:

```bash
asl run papers/demo-policy-paper \
  --draft-model openai-compat:local-model@http://127.0.0.1:8000/v1 \
  --review-model ollama:llama3.1
```

The provider catalog follows the adjacent teamagents setup. Presets include
DeepSeek (`deepseek-chat`, `deepseek-reasoner`, `deepseek-v4-pro`,
`deepseek-v4-flash`), MiniMax (`minimax-m2.7`, `minimax-m2.5`,
`minimax-m2.1`, `minimax-m1`, `abab6.5s-chat`), Qwen, Kimi, Kimi Code, vLLM,
LM Studio, Ollama, OpenAI, Anthropic, and Gemini.

Supported providers include `openai`, `anthropic`, `gemini`, `deepseek`,
`minimax`, `qwen`, `kimi`, `kimi-code`, `openai-compat`, `ollama`,
`claude-code`, and `codex`. API keys are read from the usual environment variables such as `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `MINIMAX_API_KEY`,
`QWEN_API_KEY`, `MOONSHOT_API_KEY`, and `KIMI_API_KEY`. Stage choices and actual
models used are recorded in each version's `metadata.json`.

Local CLI providers use your already configured tools:

```bash
asl run papers/demo-policy-paper \
  --draft-model claude-code:default \
  --review-model codex:default
```

`claude-code:<model>` calls the local `claude` CLI in print mode. `codex:<model>`
calls `codex exec` with a read-only sandbox and writes the agent's final message
back into the pipeline. Use `default` to let the local CLI choose its configured
model, or pass an explicit model:

```bash
asl run papers/demo-policy-paper \
  --draft-model claude-code:sonnet \
  --review-model codex:gpt-5.5
```

ASL also discovers cc-switch Claude providers from `~/.cc-switch/cc-switch.db`
and common `.cc-switch` JSON config paths. Those appear as routes like:

```text
claude-code:deepseek-v4-pro@cc-switch:deepseek
```

When such a route is used, ASL passes that cc-switch profile to Claude Code via a
temporary settings payload. Secrets are not written to paper metadata or the UI
catalog. Codex still uses its own local Codex CLI configuration.

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
