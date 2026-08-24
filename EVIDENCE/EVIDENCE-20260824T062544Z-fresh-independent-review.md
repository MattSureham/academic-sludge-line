# EVIDENCE-20260824T062544Z: Fresh Independent Review of the Governance-Repair Baseline

## Metadata

- **ID:** `EVIDENCE-20260824T062544Z-fresh-independent-review`
- **Title:** Fresh independent review of the containing governance-repair commit
- **Captured UTC:** `2026-08-24T06:25:44Z`
- **Recorded by:** `agent:claude-code-independent-review`
- **Claim supported or challenged:** The containing governance-repair commit `113b8b015e70de7d7f0903d81b9300adeb060811` resolves all three `R1`–`R3` material findings from the first independent review of `e9ef291`, preserves the authorized governance-only scope, and is ready to exit protocol adoption/recovery.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§4.4, 4.10, and 10–13
- **Related ADRs/issues:** [`ADR-20260824T024051Z-protocol-adoption`](../ADR/ADR-20260824T024051Z-protocol-adoption.md), [`ISSUE-20260824T024051Z-protocol-adoption-recovery`](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md), [`ISSUE-20260824T024051Z-review-routing-guidance`](../ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md), [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md)
- **Repository revision/state:** Reviewed target `113b8b015e70de7d7f0903d81b9300adeb060811`, direct parent `e9ef291a0be124a1ea1ad782c6bb307a486f2b18`, grandparent `387bffe632ba2d53c14aa59de93bd645935d9a94`; tracked tree clean with exactly the four recorded unrelated untracked JavaScript files; sibling protocol at `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`.
- **Environment:** Darwin `25.3.0` arm64; system Python 3; Node/npm via the bundled smart-loader; Git (Apple Git). Secrets and `.env` contents were not inspected.

## Method

- **Procedure:** Read [`BOOTSTRAP.md`](../BOOTSTRAP.md), the accepted specification, the accepted adoption ADR, all three prior evidence records, all six issue records, the checkpoint, and the handoff before inspecting code; verified the commit chain and remote refs directly; reran proportionate executable, integrity, structural, and scope checks; independently traced the code behind the corrected §4.4/§4.10 classifications and the recorded pointer/score limitations; checked every `R1`–`R3` resolution condition against the artifacts.
- **Exact command/input:** `git rev-parse HEAD HEAD^ HEAD^^ origin/main`, `git ls-remote origin refs/heads/main` (both repositories), `git status --porcelain`, `git diff --quiet`, `git show e9ef291 --stat`, `git diff e9ef291 113b8b0 --stat` and path-scoped diffs, `git diff --check`, seven explicit `cmp` calls against `git -C ../agentic-engineering-protocol show 58fa281:protocol/...`, `git show 387bffe:HANDOFF.md | shasum -a 256`, `shasum -a 256` on the four untracked JavaScript files, `lsof -nP -iTCP:8765 -sTCP:LISTEN`, `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`, `.venv/bin/python -m pytest -q -p no:cacheprovider`, `npm test` and `npm run typecheck` in `asl/_vendor/smart-loader`, `python3 scripts/validate_protocol.py` in the sibling source, a standard-library Markdown/local-link/HANDOFF structure checker, and direct reads of `asl/workspace.py::accepted_version`, `asl/pipeline.py::_score_metadata`, `asl/templates.py::review_prompt`/`revision_prompt`, `asl/catalog.py`, `asl/local_providers.py`, and `asl/llm.py::ModelSpec`/`ModelRoutes`.
- **Exit status:** All checks succeeded except the two explicitly recorded expected nonzero results below.
- **Repeatability:** Check out `113b8b0`, leave the four untracked files and ignored paths untouched, and repeat the cited commands.

## Raw observation

- **Commit chain and remotes (refreshed `2026-08-24T06:25:44Z`):** `HEAD=113b8b0` → `e9ef291` → `387bffe`; `origin/main` and direct remote `main` both remain `387bffe`. Sibling local/tracking/direct remote `main` all remain `58fa281`; sibling worktree clean.
- **Scope:** The adoption commit `e9ef291` changed exactly twenty governance/documentation paths; the repair commit `113b8b0` changed exactly nine governance/recovery paths. Path-scoped diff of the repair against `asl/`, `tests/`, and `PROJECT_SPEC.md` is empty. `git diff --check` is clean and the tracked tree has zero unstaged changes.
- **Byte integrity:** All seven approved source-to-target `cmp` mappings match (`BOOTSTRAP.md`, source `README.md`→`PROTOCOL_GUIDE.md`, `PROMPTS.md`, `EXAMPLE.md`, three templates). `git show 387bffe:HANDOFF.md` reproduces SHA-256 `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`. The four unrelated untracked files reproduce their recorded SHA-256 values (`b3647d38…`, `6f644792…`, `99bbbdcb…`, `086e35d1…`).
- **Executable baseline:** System-Python suite `66 passed in 8.61s`; bundled smart-loader one file/four tests passed in `382ms`; loader typecheck passed; sibling validator reports `PASS structural protocol validation (package_files=10 handoffs=2)`. `.venv/bin/python -m pytest` still reports `No module named pytest` — an unavailable check, not a product failure.
- **Structure:** The target contains exactly the five ordered HANDOFF sections with one nonempty Next Action; a Markdown/local-link walk found zero missing local link targets. This reviewer's walk counted `26` files/`147` links versus the repair record's `25`/`145` because it also traversed the untracked generated `pytest_cache/README.md`; the tracked set is `25` files and the substantive result (zero missing) agrees.
- **Code-level spot checks:** `accepted_version()` returns `latest_version()` when the marker is missing/invalid; `_score_metadata()` on non-JSON yields `same`/`5`/`5` with empty rationale; `review_prompt()` requests five named output fields and `revision_prompt()` accepts `list[str]` reviews and requests five plan sections; `ModelPreset`/`LocalModelPreset` carry `capabilities` tuples and `catalog_payload()` exposes them, while `ModelSpec`/`ModelRoutes` carry no capability descriptor and no stage negotiates one.
- **Background state:** No TCP listener on port `8765` at the refreshed check (`lsof` exit `1`, expected absence); no `QUEUED`/`RUNNING` background task has a durable reference.
- **Resolution conditions:** `R1` — §4.4 corrected to implemented in the reconciliation corrections table, the review-routing/guidance issue is `CLOSED` with a complete `APPROVED` round, and it is absent from the HANDOFF active index and checkpoint decision queue. `R2` — §4.10 corrected to partially implemented with the descriptive-metadata/execution-consumption distinction in the reconciliation corrections, the normalization/capability issue, the checkpoint, and the handoff. `R3` — exact pre-adoption specification bytes/authorship downgraded to implementor-recorded, independently unreproducible provenance in the recovery-evidence corrections table, the adoption-issue assumptions, the checkpoint, and the handoff, while current accepted authority is retained.

## Interpretation

- **CONFIRMED:** The repair commit is governance-only and within the authority granted by the accepted adoption ADR and the first review's resolution conditions; no product code, test, specification behavioral wording, generated paper, environment, or unrelated file changed.
- **CONFIRMED:** All three `R1`–`R3` material findings are resolved additively without rewriting prior evidence, and current-state records (HANDOFF, checkpoint, issue index) are internally consistent with the corrections.
- **CONFIRMED:** Historical-state preservation holds: legacy handoff digest, parent README relationship, untracked-file digests, and additive correction history are all intact.
- **CONFIRMED:** The recorded executable and structural verification baseline reproduces under this fresh participant.
- **UNKNOWN:** Full specification §§10–12 compatibility/completion, live-provider behavior, representative corpus fidelity, and exact pre-adoption specification bytes remain unestablished, as explicitly recorded.

## Limitations and residual uncertainty

- This reviewer ran on the same Darwin host class; participant labels are attributable, not authenticated.
- No live provider/model calls, network research, UI session, or damaged-workspace test ran; those limits are already owned by the focused open issues.
- The link-count difference versus the repair record is a checker-scope artifact (untracked `pytest_cache/README.md`), not missing content.
- Exact pre-adoption specification bytes remain unrecoverable; current accepted authority is unaffected.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record; immutable reviewed revisions are recorded above.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record.
- **External retention risk:** Direct remotes and ignored samples can change after the refreshed capture; immutable Git objects remain the durable boundary.
- **Supersedes / superseded by:** `NONE`

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `NONE` | `agent:claude-code-independent-review` | `NONE` | No correction recorded. |
