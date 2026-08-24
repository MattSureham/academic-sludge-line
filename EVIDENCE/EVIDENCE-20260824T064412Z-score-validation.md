# EVIDENCE-20260824T064412Z: Fail-Closed Score-Validation Implementation

## Metadata

- **ID:** `EVIDENCE-20260824T064412Z-score-validation`
- **Title:** Fail-closed score validation, aggregation, and persistence
- **Captured UTC:** `2026-08-24T06:44:12Z` through `2026-08-24T06:55:10Z`
- **Recorded by:** `agent:codex-score-validation`
- **Claim supported or challenged:** Malformed, missing-field, schema-invalid, and fallback scorer outputs are no longer eligible quality-gate votes; invalid records and their errors remain auditable; a candidate cannot be accepted without at least one valid score.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.1, 4.2, 8, 11 invariant 3, and §12
- **Related ADRs/issues:** [`ISSUE-20260824T024051Z-quality-gate-validation`](../ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md); no new ADR
- **Repository revision/state:** Implementation worktree based on `ac93c21881ab3ddedf709a3baaa1703d3d189666`; intended review target is the containing implementation commit. Four pre-existing unrelated untracked JavaScript files remain outside the change.
- **Environment:** Darwin arm64; Python `3.9.6`; Node `v22.22.0`; npm `10.9.4`; secrets and ignored paper workspaces not inspected or modified.

## Method

- **Procedure:** Recover the accepted specification, approved governance baseline, issue scope, pre-change implementation, and existing gate tests; reproduce each scoped invalid case; add a strict result-schema boundary; aggregate only eligible votes; add unit and integration tests for validation, persistence, no-valid-vote rejection, mixed invalid/fallback exclusion, and unchanged valid-score behavior; run targeted and full validation.
- **Exact command/input:** Pre/post isolated `_score_metadata()` calls using malformed text, missing rationale, invalid verdict, string score, score `11`, and provider `offline`; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_pipeline.py -k 'score or worse_candidate or fallback_candidate'`; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`; `.venv/bin/python -m pytest -q -p no:cacheprovider`; `npm test` and `npm run typecheck` in `asl/_vendor/smart-loader`; `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_protocol.py` in the sibling protocol repository.
- **Exit status:** All supported checks passed. The repository `.venv` check remained unavailable (`No module named pytest`), and the first targeted test invocation had one test-assertion failure corrected as recorded below.
- **Repeatability:** Check out the containing implementation commit, leave unrelated/ignored files untouched, and repeat the commands above. The integration tests create only pytest-managed temporary paper workspaces.

## Raw observation

### Before

The six isolated cases all produced valid-looking score metadata: malformed output became `same`/`5`/`5`; missing rationale became an empty string; invalid verdict became `same`; a numeric string was coerced to an integer; `11` was clamped to `10`; and structurally valid fallback output retained an eligible-looking `better` vote. Existing focused gate tests passed `3` tests but did not cover these paths.

### After

```text
malformed: valid=False verdict=None scores=None/None errors=['score output does not contain a JSON object']
missing: valid=False verdict=None scores=None/None errors=['missing required field: rationale']
invalid_verdict: valid=False verdict=None scores=None/None errors=['verdict must be one of: better, same, worse']
invalid_type: valid=False verdict=None scores=None/None errors=['previous_score must be an integer from 1 to 10']
invalid_range: valid=False verdict=None scores=None/None errors=['candidate_score must be an integer from 1 to 10']
fallback: valid=False verdict=None scores=None/None errors=['fallback scorer output is not eligible for quality-gate voting']
```

- The targeted selection passed `11` tests with `65` deselected after correcting the test assertion.
- The complete Python suite passed `76` tests in `9.86s`.
- A final staged-tree rerun passed the same `76` tests in `7.80s`.
- Bundled smart-loader tests passed one file/four tests in `511ms`; its typecheck passed.
- The sibling protocol validator reported `PASS structural protocol validation (package_files=10 handoffs=2)`.
- Seven protocol-source byte comparisons, target manifest/symlink checks, Markdown/local-link/HANDOFF checks (`28` Markdown files, one Next Action), `git diff --check`, the exact six-path slice assertion, accepted-pointer/specification exclusion, and the four unrelated-file digest checks passed.
- `.venv/bin/python -m pytest` reported `No module named pytest` and did not run tests.
- Integration assertions confirm: `quality_scores.json` and `metadata.json` persist identical invalid-score metadata/errors; the accepted pointer remains unchanged when no valid vote exists; and an invalid or fallback nominally favorable result cannot offset a valid `worse` vote.

## Interpretation

- **CONFIRMED:** Every score result is validated before aggregation, and only records with `valid: true` participate.
- **CONFIRMED:** A no-valid-vote gate records `rejected`, retains the prior accepted pointer, and persists why each result was ineligible.
- **CONFIRMED:** Invalid and fallback votes are excluded even when a separate real valid score exists; this closes the former tie-based acceptance path.
- **CONFIRMED:** Valid non-fallback JSON with all four prompted fields retains case-insensitive verdict normalization, original scores/rationale, and the existing majority/tie aggregation policy.
- **INFERRED:** Additive `valid`/`validation_errors` fields and `null` invalid vote fields are the smallest auditable persistence change compatible with the accepted specification and issue scope.
- **UNKNOWN:** The broader configurable quality-policy design in specification §14 remains intentionally unresolved.

## Limitations and residual uncertainty

- No live model/provider call was made; deterministic fake result objects exercise the provider-independent boundary used by all routes.
- This slice does not change or test missing/invalid accepted-pointer recovery, reviewer aggregation, scoring rubric choice, or migrations for previously written score records.
- Independent review of the containing implementation commit is still required before issue closure.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record; implementation and executable tests are in the containing commit.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record.
- **External retention risk:** `NONE` beyond ordinary Git remote retention; no external artifact is required.
- **Supersedes / superseded by:** Extends the score observation in [`EVIDENCE-20260824T024051Z-spec-reconciliation`](EVIDENCE-20260824T024051Z-spec-reconciliation.md); superseded by `NONE`.

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T06:48:17Z` | `agent:codex-score-validation` | Changed one integration assertion from direct list membership to substring inspection of each persisted error string. | First targeted run was `10 passed, 1 failed`; the product output contained the intended full error text, and the corrected targeted run passed `11` tests. |
