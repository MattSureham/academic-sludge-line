# EVIDENCE-20260824T071015Z: Fresh Independent Review of Fail-Closed Score Validation

## Metadata

- **ID:** `EVIDENCE-20260824T071015Z-score-validation-review`
- **Title:** Fresh independent review of the fail-closed score-validation commit
- **Captured UTC:** `2026-08-24T07:10:15Z`
- **Recorded by:** `agent:claude-code-independent-review`
- **Claim supported or challenged:** The containing score-validation commit `391d73e702bae34ebcdd334d68cdbed27d450fa6` implements the authorized bounded fail-closed slice correctly: invalid/fallback scorer output cannot vote, a no-valid-vote gate rejects and preserves the accepted pointer, valid-vote aggregation semantics are unchanged, invalid records persist with attributable errors, and the change is contained to the declared scope.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.1, 4.2, 8, 11 invariant 3, and §12
- **Related ADRs/issues:** [`ISSUE-20260824T024051Z-quality-gate-validation`](../ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md); no new ADR
- **Repository revision/state:** Reviewed target `391d73e702bae34ebcdd334d68cdbed27d450fa6`, direct parent `ac93c21881ab3ddedf709a3baaa1703d3d189666`; `origin/main` and direct remote `main` both at the reviewed target (refreshed `2026-08-24T07:10:15Z`, consistent with the authorized push recorded in HANDOFF); tracked tree clean with exactly the four recorded unrelated untracked JavaScript files.
- **Environment:** Darwin `25.3.0` arm64; system Python 3; Node/npm via the bundled smart-loader; Git (Apple Git). Secrets and `.env` contents were not inspected.

## Method

- **Procedure:** Read the accepted specification sections, the owning issue, the implementation evidence, the checkpoint, and the handoff before inspecting code; read the complete `ac93c21..391d73e` diff of `asl/pipeline.py` and `tests/test_pipeline.py`; traced every producer and consumer of score records (`_quality_gate`, `_score_metadata`, `_parse_score_json`, `_invalid_score`, `_is_fallback_result`, `_result_metadata`, `metadata.json` embedding, `html_render.py`, `ui.py`, `score_prompt`); reran the full and targeted suites; ran independent unit-level edge probes beyond the committed tests and an independent end-to-end positive-path pipeline run; verified scope containment, digests, remotes, and structure.
- **Exact command/input:** `git log/show/diff` (including `--stat` and path-scoped exclusion diffs), `git ls-remote origin refs/heads/main`, `shasum -a 256` on the four untracked files, `lsof -nP -iTCP:8765 -sTCP:LISTEN`, `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`, `npm test` and `npm run typecheck` in `asl/_vendor/smart-loader`, `python3 scripts/validate_protocol.py` in the sibling source, a standard-library Markdown/local-link/HANDOFF checker, an eleven-case direct `_score_metadata()` probe script, and a temporary-directory two-version pipeline run with a fake client returning a valid `better` vote.
- **Exit status:** All checks succeeded except the expected `lsof` absence result (exit `1`).
- **Repeatability:** Check out `391d73e`, leave the four untracked files and ignored paths untouched, and repeat the cited commands; the probe scripts create only temporary workspaces.

## Raw observation

- **Scope containment:** The commit changes exactly six paths: `asl/pipeline.py`, `tests/test_pipeline.py`, and four governance records. Path-scoped diff against `PROJECT_SPEC.md`, `asl/workspace.py` (accepted pointer), `asl/templates.py` (prompts), `asl/catalog.py`, and `asl/llm.py` (routing) is empty. Zero existing test lines were removed; the test change is purely additive (`+190`).
- **Validation boundary:** `_parse_score_json` now requires all four prompted fields; verdict must be a string normalizing case-insensitively into `{better, same, worse}`; scores must satisfy `type(value) is int` (booleans excluded) within `1`–`10`; rationale must be a non-empty string. Any violation yields `valid: False`, `null` vote fields, and attributable `validation_errors`. Fallback providers (`offline`, `offline-after-error`, `template`) are always ineligible, with parse errors preserved alongside the fallback error.
- **Aggregation semantics:** The gate filters to `valid` scores; with none it writes a `rejected` gate and returns without touching `accepted_version.txt` (pointer write confirmed to occur only under `quality_gate["accepted"]`). With valid votes, the pre-existing `better_or_same >= worse` policy (tie accepts) is computed over valid votes only — unchanged for valid votes.
- **Persistence:** The full gate, including invalid score records and their errors, is written to `quality_scores.json` and embedded identically in `metadata.json` (`metadata["quality_gate"]`); both consumers (`html_render.py`, `ui.py`) render the file wholesale and perform no field-level access, so `null` vote fields cannot break them.
- **Prompt contract:** `score_prompt` requests exactly the four validated fields with the same names and value domains.
- **Independent edge probes (all fail closed):** boolean score, float score, whitespace-only rationale, missing verdict, JSON array wrapper, nested-brace truncation, whitespace-suffixed verdict, zero score — each produced `valid=False` with specific errors; uppercase `SAME` normalized and remained valid; extra fields remained valid; a structurally valid fallback-provider result was ineligible.
- **Independent positive path:** A two-version run whose scorer returned a valid `better` vote accepted the candidate, advanced the accepted pointer to `v2`, and persisted identical gate records in both files.
- **Suites:** Full Python suite `76 passed in 10.25s` (66 pre-existing plus 10 new; zero removed test lines); bundled loader one file/four tests passed in `401ms`; loader typecheck passed; sibling validator `PASS structural protocol validation (package_files=10 handoffs=2)`; tracked Markdown `27` files/`166` local links/`0` missing; HANDOFF has exactly the five ordered sections with one nonempty Next Action; `git diff --check` clean; four untracked digests unchanged; no port `8765` listener (expected `lsof` exit `1`).

## Interpretation

- **CONFIRMED:** The implementation satisfies the issue's expected behavior: invalid, fallback, or schema-nonconforming outputs never become votes; a no-valid-vote gate rejects and preserves the accepted pointer; validation errors persist for auditability.
- **CONFIRMED:** Unrelated quality-gate semantics are unchanged: valid-vote aggregation policy, verdict normalization, fallback-candidate rejection, first-version acceptance, prompt wording, pointer logic, routing, and specification text are all untouched.
- **CONFIRMED:** Regression coverage is genuine: the entire pre-existing suite passes unmodified, new unit/integration tests cover the scoped failure modes, and this reviewer independently reproduced both the failure exclusions and the positive acceptance path.
- **INFERRED:** Two cosmetic non-material observations — the non-dict JSON guard is practically unreachable because extraction anchors on `{`, and a whitespace-suffixed verdict is rejected rather than stripped; both fail closed and match the slice's conservative contract.
- **UNKNOWN:** Live provider behavior, the broader configurable §14 policy, and migrations for previously written score records remain outside this slice as recorded.

## Limitations and residual uncertainty

- This reviewer ran on the same Darwin host class; participant labels are attributable, not authenticated.
- No live model/provider call was made; fake result objects exercise the same provider-independent boundary used by all routes.
- `.venv` pytest remains unavailable, as previously recorded; the system-Python suite passed.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record; the immutable reviewed revision is recorded above.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record.
- **External retention risk:** `NONE` beyond ordinary Git remote retention; the reviewed target is present on `origin/main` at capture time.
- **Supersedes / superseded by:** `NONE`

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T07:10:15Z` | `agent:claude-code-independent-review` | Corrected the first positive-path probe invocation, which imported `init_project` from `asl.workspace`; the symbol lives in `asl.pipeline`, and the corrected probe passed. | `ImportError` traceback followed by successful `POSITIVE-PATH-OK` output. |
