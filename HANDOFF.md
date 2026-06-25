# Claude Code Handoff

Current repo: `/Users/matthew/Projects/academic-sludge-line`

## Pipeline overview

- Versioned drafting pipeline: draft → review → revision → quality gate (score).
- Papers live under ignored `papers/`. Seed drafts are imported as accepted `v1`.
- Fallback or lower-quality candidates are kept but do not replace `accepted_version.txt`.
- Web UI at `http://127.0.0.1:8765`.

## Source files

| File | Purpose |
|------|---------|
| `asl/cli.py` | CLI argument parsing, wires args to `PaperPipeline` |
| `asl/pipeline.py` | Core orchestration: cycles, versioning, quality gate, prompt budget |
| `asl/templates.py` | All LLM prompt templates (plan, draft, iterative draft, review, revision, score) |
| `asl/llm.py` | LLM client: routing, retry, cc-switch key lookup, anthropic/openai-compat/deepseek/minimax/claude-code backends |
| `asl/catalog.py` | Provider/model discovery from cc-switch profiles and local agents |
| `asl/local_providers.py` | cc-switch SQLite profile parsing, Claude Code/Codex binary discovery |
| `asl/workspace.py` | File I/O helpers (read/write JSON, text), timestamp utils |
| `asl/ui.py` | Web UI: HTTP server, HTML/CSS/JS, project listing, file browser, run job tracking |
| `asl/smart_loader.py` | Adapter for the bundled smart-loader CLI (PDF/DOCX/XLSX → markdown) |
| `asl/reference_search.py` | Auditable Crossref literature search from title/topic/research question |
| `asl/web_research.py` | Auditable web search stage: generates queries, fetches results, writes to version dir |
| `asl/html_render.py` | Markdown → HTML rendering for version HTML preview |

## Model routing

cc-switch profiles are discovered from local `~/.cc-switch/cc-switch.db` (SQLite). Routes available:

| Pattern | Example | Notes |
|---------|---------|-------|
| `claude-code:MODEL@cc-switch:PROFILE` | `claude-code:glm-5.1@cc-switch:zhipu-glm` | Terminal subprocess |
| `codex:MODEL@cc-switch:PROFILE` | `codex:MODEL@cc-switch:PROFILE` | OpenAI Codex CLI subprocess |
| `anthropic:MODEL@cc-switch:PROFILE` | `anthropic:deepseek-v4-pro@cc-switch:deepseek` | Anthropic Messages API |
| `openai-compat:MODEL@cc-switch:PROFILE` | `openai-compat:glm-5.1@cc-switch:zhipu-glm` | OpenAI chat completions API |
| `deepseek:MODEL@cc-switch:PROFILE` | `deepseek:deepseek-v4-pro@cc-switch:deepseek` | Native provider via cc-switch creds |
| `minimax:MODEL` | `minimax:minimax-m3,minimax:minimax-m2.7` | Direct API |

Key routing details:
- cc-switch profiles that set `OPENAI_BASE_URL` in env also expose `openai-compat:` (and native provider if `ASL_PROVIDER` is set) routes alongside the `anthropic:` route.
- The `openai-compat` route is needed for Zhipu GLM because its Anthropic-compatible endpoint (`/api/anthropic`) returns 404; the OpenAI-compatible endpoint (`/api/paas/v4`) works.
- `_cc_switch_api_key_for` falls back to `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY` for non-anthropic providers, so native provider routes (e.g. `deepseek:`) work with cc-switch credentials.
- Model chains with `,` separator try each model in order (fallback on failure).
- `--no-local-agents` disables Claude Code/Codex terminal subprocess providers.
- `--allow-agent-tools` lets terminal providers use tools like web search.

## Start modes

Three ways to begin a paper:

| Mode | Behaviour |
|------|-----------|
| `from-scratch` | Draft from topic + brief + references. Default. |
| `discover-topic` | Surveys ALL references (balanced survey, every paper gets a short excerpt) and proposes `--topic-count` candidate topics, each with anchor papers. `--topic-mode auto` (default) locks the top proposal and drafts; `--topic-mode manual` writes the proposals (`topic_proposals.md` / `topic_candidates.json`) and stops until you re-run with `--topic-choice N`. The chosen topic and its `topic_anchors` are persisted to `project.json`. |
| `rewrite` | Takes a seed draft file (PDF/DOCX/markdown), extracts text via smart-loader, and rewrites it with evidence discipline. |

## Iterative improvement mechanism

Starting from the second cycle, the pipeline detects that a previous version has reviews and switches to `iterative_draft_prompt`:
- Preserves content reviewers did not flag; focuses improvement on review findings and revision checklist.
- Previous draft excerpt increases from 8K → 16K chars for iterative cycles.
- Reference context is compressed (the model already has it in the previous draft).
- Iterative cycles get a larger total prompt budget (`prompt_budget + review_cost + 8K`).

## Human-directed intervention

CLI:
- `--from VERSION` — start from any checkpoint version instead of the accepted version. The quality gate still compares against the accepted version.
- `--focus "guidance"` — inject additional context/prompt into the draft step.
- `--references PATH` — add new reference files for this run.
- `--reference-search` — search Crossref for candidate references based on the paper topic/research question.
- `--reference-search-max-results N` (default 8) — controls the Crossref reference search size.
- `--max-prompt-chars N` (default 20000) — controls total draft prompt size.
- `--reference-context-strategy {select,balanced,full}` (default `select`) — how loaded reference text is fitted into the prompt budget (see Prompt budget).
- `--reference-context-chars N` (default 24000) — max chars of loaded reference context; raise it for the `full` strategy.
- `--reference-context-full N` (default 6) — for `select`, how many top references to include at full length.

Web UI:
- **Start from version** dropdown — populated from project versions with quality scores. Overrides the baseline draft.
- **Focus guidance** textarea — equivalent to `--focus`.
- **Max prompt chars** input — equivalent to `--max-prompt-chars`.
- **Reference strategy** dropdown + **Reference context chars** + **Full references** inputs — equivalent to `--reference-context-*`.
- **Reference search** checkbox + **Max references** input — equivalent to `--reference-search`.
- These are collected in the JS `runProject()` payload and passed to `PaperPipeline` via `_run_project()`.

Metadata records both `previous_version` (baseline for the draft) and `previous_accepted_version` (baseline for quality gate).

## Prompt budget

- `--max-prompt-chars N` (default 20000) controls the total draft prompt size.
- Reference context is trimmed first when the budget is exceeded, preserving plan and previous draft.
- For iterative cycles the effective budget is larger to accommodate review/revision content.

### Reference context strategy

Loaded references are concatenated per document (`## <file>` blocks) and fitted to the budget by `budget_reference_context` (`asl/smart_loader.py`), applied both at context build and at the draft-budget trim so the choice survives both cuts:

- `select` (default) — rank documents by keyword overlap with the research question/topic; give the top `full_count` a full slice and the rest a short excerpt, so every relevant document is represented.
- `balanced` — split the budget evenly across all documents (every document gets a short excerpt).
- `full` — include every document at full length up to `--reference-context-chars`; the draft-budget trim does **not** shrink it, so raising that limit is the lever (at the cost of a larger, more expensive prompt).

Without this, a folder of N references was head-truncated to the first ~3 documents regardless of relevance, which is why earlier drafts cited only the first files and marked everything else TODO.

PDF text extraction itself uses pure-JS `pdf-parse` (no Poppler needed). Poppler (`pdftoppm`) + `tesseract` are only required for the OCR fallback on scanned/image-only PDFs.

## smart-loader

Bundled Node.js CLI (`smart-loader/`) that extracts structured text from input files:
- PDF: renders pages as images, OCRs via tesseract, extracts text with metadata.
- DOCX: converts to markdown with document structure.
- XLSX/CSV: converts to markdown tables.
- Plain text/markdown: passes through.

Settings (configurable via CLI flags and Web UI):
- `pdf_render_pages` (default true), `pdf_max_pages` (25), `pdf_dpi` (180)
- `ocr_assets` (default true), `ocr_language` ("eng")

## Reference search

Optional bibliography-discovery stage (`--reference-search`) that:
- Builds a Crossref query from `research_question`, topic, title, or brief.
- Fetches candidate works from Crossref.
- Writes `reference_search.md` and `reference_search.json` to the version directory.
- Appends candidates to `sources.json` with `kind: "reference"`.
- Injects `Reference Search Leads` into the draft prompt.

Configure with `--reference-search-max-results` (default 8). These are leads only; verify metadata, relevance, and full text before citing.
Set `ASL_CONTACT_EMAIL` to include a contact email in the Crossref User-Agent.

## Web research

Optional pre-draft stage (`--web-research`) that:
- Generates search queries from the topic and research plan.
- Fetches results via DuckDuckGo (no API key needed).
- Writes `web_research.md` and `web_research.json` to the version directory.
- Results feed into the draft prompt as additional context.

Configure with `--web-research-max-queries` (default 3) and `--web-research-max-results` (default 5).

## Network resilience

- `_generate_with_spec` retries up to `ASL_MAX_RETRIES` (default 2) with exponential backoff on transient errors (`RemoteDisconnected`, `IncompleteRead`, `ConnectionReset`, etc.).
- `_GENERATION_ERRORS` includes `IncompleteRead`, `ConnectionError`, `ConnectionResetError`, `BrokenPipeError` so the pipeline never crashes on network failures.

## Web UI architecture

The UI (`asl/ui.py`) is a single-file HTTP server with embedded HTML/CSS/JS:
- **Backend**: `ThreadingHTTPServer` + `BaseHTTPRequestHandler`. Routes: `/` (index), `/app.css`, `/app.js`, `/api/catalog`, `/api/browse`, `/api/projects`, `/api/project`, `/api/jobs/<id>`, `/api/init`, `/api/run`, `/api/mkdir`.
- **Frontend**: Vanilla JS (no framework). Tabs: Run, New Paper, Providers. File browser modal for path selection. Real-time job progress polling.
- **Run jobs**: Background threads with `_RunJob` state machine (queued → running → succeeded/failed). Progress events streamed via polling `/api/jobs/<id>`.
- **Project auto-creation**: Typing a non-existent `papers/<slug>` path into the Run form auto-creates it on submit (calls `init_project_at`).

## Useful checks

```bash
pytest -q
python3 -m asl.cli ui --host 127.0.0.1 --port 8765
```

## Useful route examples

```bash
# OpenAI-compat route for Zhipu GLM + DeepSeek for review/score
asl run papers/demo \
  --draft-model openai-compat:glm-5.1@cc-switch:zhipu-glm,deepseek:deepseek-v4-pro@cc-switch:deepseek \
  --review-model deepseek:deepseek-v4-pro@cc-switch:deepseek \
  --score-model deepseek:deepseek-v4-pro@cc-switch:deepseek

# Start from v2 with focus guidance
asl run papers/demo --from v2 \
  --focus "Strengthen methods section and address LMIC gaps"

# MiniMax with fallback
asl run papers/demo \
  --draft-model minimax:minimax-m3,minimax:minimax-m2.7 \
  --no-local-agents

# Web research + iterative cycles
asl run papers/demo --cycles 3 --web-research \
  --draft-model deepseek:deepseek-v4-pro@cc-switch:deepseek
```

Do not print or commit cc-switch API keys. The catalog and metadata should expose routes but not secrets.
