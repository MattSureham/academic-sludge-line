# Claude Code Handoff

Current repo: `/Users/matthew/Projects/academic-sludge-line`

Recent state:
- The pipeline keeps generated papers under ignored `papers/`.
- Rewrite runs import the seed draft as accepted `v1`; the first generated candidate becomes `v2`.
- Fallback or lower-quality candidates are kept but do not replace `accepted_version.txt`.
- The Web UI runs locally at `http://127.0.0.1:8765`.

Provider/model work completed in this handoff:
- cc-switch profiles are discovered from local JSON/SQLite config.
- Claude Code terminal routes can use multiple models from the same cc-switch provider, for example `claude-code:glm-5.2@cc-switch:zhipu-glm` and `claude-code:glm-5.1@cc-switch:zhipu-glm`.
- cc-switch profiles with Anthropic-compatible endpoint/token also expose direct API routes, for example `anthropic:glm-5.2@cc-switch:zhipu-glm`.
- MiniMax M3 is included as a first-class preset, so same-provider alternatives like `minimax:minimax-m3,minimax:minimax-m2.7` are supported.
- Web UI Run tab has a Terminal providers checkbox. It is on by default and controls whether `claude-code:*` and `codex:*` routes may spawn local subprocesses.
- Agent web/tools is separate; it controls web/tool flags for those subprocesses.

Useful checks:

```bash
pytest -q
python3 -m asl.cli ui --host 127.0.0.1 --port 8765
```

Useful route examples:

```bash
asl run papers/demo-policy-paper \
  --draft-model claude-code:glm-5.2@cc-switch:zhipu-glm \
  --review-model codex:default \
  --score-model anthropic:glm-5.2@cc-switch:zhipu-glm,anthropic:glm-5.1@cc-switch:zhipu-glm

asl run papers/demo-policy-paper \
  --draft-model minimax:minimax-m3,minimax:minimax-m2.7 \
  --no-local-agents
```

Do not print or commit cc-switch API keys. The catalog and metadata should expose routes but not secrets.
