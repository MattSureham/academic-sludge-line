# Claude Code Handoff

Current repo: `/Users/matthew/Projects/academic-sludge-line`

## Pipeline overview

- Versioned drafting pipeline: draft → review → revision → quality gate (score).
- Papers live under ignored `papers/`. Seed drafts are imported as accepted `v1`.
- Fallback or lower-quality candidates are kept but do not replace `accepted_version.txt`.
- Web UI at `http://127.0.0.1:8765`.

## Model routing

cc-switch profiles are discovered from local JSON/SQLite config. Routes available:

| Pattern | Example | Notes |
|---------|---------|-------|
| `claude-code:MODEL@cc-switch:PROFILE` | `claude-code:glm-5.1@cc-switch:zhipu-glm` | Terminal subprocess |
| `anthropic:MODEL@cc-switch:PROFILE` | `anthropic:deepseek-v4-pro@cc-switch:deepseek` | Anthropic Messages API |
| `openai-compat:MODEL@cc-switch:PROFILE` | `openai-compat:glm-5.1@cc-switch:zhipu-glm` | OpenAI chat completions API |
| `deepseek:MODEL@cc-switch:PROFILE` | `deepseek:deepseek-v4-pro@cc-switch:deepseek` | Native provider via cc-switch creds |
| `minimax:MODEL` | `minimax:minimax-m3,minimax:minimax-m2.7` | Direct API |

Key routing details:
- cc-switch profiles that set `OPENAI_BASE_URL` in env also expose `openai-compat:` (and native provider if `ASL_PROVIDER` is set) routes alongside the `anthropic:` route.
- The `openai-compat` route is needed for Zhipu GLM because its Anthropic-compatible endpoint (`/api/anthropic`) returns 404; the OpenAI-compatible endpoint (`/api/paas/v4`) works.
- `_cc_switch_api_key_for` falls back to `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY` for non-anthropic providers, so native provider routes (e.g. `deepseek:`) work with cc-switch credentials.
- Model chains with `,` separator try each model in order (fallback on failure).

## Iterative improvement mechanism

Starting from the second cycle, the pipeline detects that a previous version has reviews and switches to `iterative_draft_prompt`:
- Preserves content reviewers did not flag; focuses improvement on review findings and revision checklist.
- Previous draft excerpt increases from 8K → 16K chars for iterative cycles.
- Reference context is compressed (the model already has it in the previous draft).
- Iterative cycles get a larger total prompt budget (`prompt_budget + review_cost + 8K`).

## Human-directed intervention

- `--from VERSION` — start from any checkpoint version instead of the accepted version. The quality gate still compares against the accepted version.
- `--focus "guidance"` — inject additional context/prompt into the draft step.
- `--references PATH` — add new reference files for this run.
- Metadata records both `previous_version` (baseline for the draft) and `previous_accepted_version` (baseline for quality gate).

## Prompt budget

- `--max-prompt-chars N` (default 20000) controls the total draft prompt size.
- Reference context is trimmed first when the budget is exceeded, preserving plan and previous draft.
- For iterative cycles the effective budget is larger to accommodate review/revision content.

## Network resilience

- `_generate_with_spec` retries up to `ASL_MAX_RETRIES` (default 2) with exponential backoff on transient errors (`RemoteDisconnected`, `IncompleteRead`, `ConnectionReset`, etc.).
- `_GENERATION_ERRORS` includes `IncompleteRead`, `ConnectionError`, `ConnectionResetError`, `BrokenPipeError` so the pipeline never crashes on network failures.

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
```

Do not print or commit cc-switch API keys. The catalog and metadata should expose routes but not secrets.
