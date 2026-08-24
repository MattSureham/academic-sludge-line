# ISSUE-20260824T024051Z: Make Quality-Gate Score Validation Fail Closed

## Metadata

- **ID:** `ISSUE-20260824T024051Z-quality-gate-validation`
- **Title:** Make quality-gate score-output validation fail closed
- **Status:** `CLOSED`
- **Severity:** `HIGH`
- **Owner:** `agent:codex-score-validation`
- **Authority:** `AGENT`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T07:10:15Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.1, 4.2, 8, 11 invariant 3, and §12
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md), [`EVIDENCE-20260824T064412Z-score-validation`](../EVIDENCE/EVIDENCE-20260824T064412Z-score-validation.md), [`EVIDENCE-20260824T071015Z-score-validation-review`](../EVIDENCE/EVIDENCE-20260824T071015Z-score-validation-review.md)
- **Milestone:** `NONE`

## Problem

Malformed or non-JSON judge output is converted into a valid-looking `same` vote with both scores set to `5`. The aggregation counts `same` as non-worse, so invalid output can contribute to candidate acceptance instead of being rejected or marked unevaluable.

## Evidence or reproduction

Calling `_score_metadata()` with a fake result whose text is not JSON produced `{'provider': 'fake', 'model': 'judge', 'attempts': [], 'verdict': 'same', 'previous_score': 5, 'candidate_score': 5, 'rationale': ''}`. Inspection of [`asl/pipeline.py`](../asl/pipeline.py) confirms parse failure returns an empty object and downstream defaults synthesize these fields.

## Expected behavior

Invalid, fallback, or schema-nonconforming judge outputs do not become valid votes. If no valid evaluation remains, the candidate is rejected or left unaccepted, and validation errors are persisted for auditability.

## Assumptions

- **CONFIRMED:** Current aggregation evaluates against the accepted baseline and persists score metadata.
- **CONFIRMED:** Malformed output can currently count as `same`.
- **INFERRED:** Excluding invalid votes and refusing acceptance without a valid score is a local defect fix consistent with the accepted gate invariant.
- **UNKNOWN:** Whether the eventual configurable policy contract will distinguish `REJECTED` from `UNEVALUABLE`; this first slice need not establish that broader policy.

## Investigation and decision

Smallest evidence-backed post-review slice: add tests for malformed, missing-field, invalid-verdict, invalid-score-type/range, and fallback judge output; validate each result before aggregation; exclude invalid or fallback votes; reject when no valid score remains; and persist validation errors. Keep accepted-pointer recovery out of this slice because it requires separate owner authority.

For this slice, a vote is eligible only when it comes from a non-fallback provider and the extracted JSON object contains all four prompted fields: a supported string verdict, integer (non-boolean) scores within `1`–`10`, and a non-empty string rationale. Existing case-insensitive verdict normalization and extraction of a JSON object from surrounding model text remain compatible. Invalid records retain provider/model/attempt metadata, carry `null` vote fields plus attributable `validation_errors`, and remain persisted but excluded from aggregation.

## Change

- **Files or components:** `asl/pipeline.py`, `tests/test_pipeline.py`, this issue, the linked implementation evidence, and the operational handoff.
- **Behavior changed:** Score results now carry explicit validity/errors; malformed, incomplete, schema-invalid, and fallback results are persisted but excluded from aggregation; no-valid-vote gates reject. Valid non-fallback votes retain the existing verdict normalization and aggregation policy.
- **Out-of-scope work deliberately excluded:** New scoring policy, rubric redesign, reviewer consensus, accepted-pointer behavior, provider routing, or persistence migration.
- **Rollback or recovery:** Revert the containing implementation commit. Existing stored candidates are not migrated; newly written score records use additive `valid` and `validation_errors` fields and `null` vote fields when invalid.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Explicit additive score validity/error fields | Prevent invalid model output from silently authorizing acceptance | Unit schema cases, no-valid-vote integration, mixed invalid/fallback aggregation tests, and persisted `quality_scores.json`/metadata assertions | Broader policy configurability remains open under specification §14 |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Isolated call to `_score_metadata()` with non-JSON scorer text | Produced default `same`, `5`, `5`; exit `0` | Reconciliation evidence | Diagnostic only; no fix or new test was added |
| `2026-08-24T06:44:12Z` | `agent:codex-score-validation` | Six isolated `_score_metadata()` calls covering malformed, missing-rationale, invalid-verdict, string-score, out-of-range-score, and fallback-provider output | Every case produced a valid-looking vote; type was coerced, range clamped, malformed/verdict defaulted, missing rationale became empty, and fallback remained eligible metadata; exit `0` | New score-validation evidence | Pre-change diagnostic; aggregation/persistence exercised separately by implementation tests |
| `2026-08-24T06:44:12Z` | `agent:codex-score-validation` | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_pipeline.py -k 'worse_candidate or fallback_candidate or missing_score_model'` | `3 passed, 63 deselected`; exit `0` | Existing quality-gate baseline | Does not cover malformed/schema-invalid output or mixed valid/invalid votes |
| `2026-08-24T06:48:17Z` | `agent:codex-score-validation` | First targeted post-change run: `... tests/test_pipeline.py -k 'score or worse_candidate or fallback_candidate'` | `10 passed, 1 failed, 65 deselected`; exit `1` | Test assertion compared a substring directly with a list of full error strings | Product behavior passed through the failing point; test assertion was corrected to inspect each persisted error |
| `2026-08-24T06:48:17Z` | `agent:codex-score-validation` | Corrected targeted post-change run: `... tests/test_pipeline.py -k 'score or worse_candidate or fallback_candidate'` | `11 passed, 65 deselected`; exit `0` | Unit and integration coverage for the bounded slice | Full regression and protocol checks pending |
| `2026-08-24T06:53:18Z` | `agent:codex-score-validation` | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | `76 passed in 9.86s`; exit `0` | [Implementation evidence](../EVIDENCE/EVIDENCE-20260824T064412Z-score-validation.md) | Deterministic local/fake-provider coverage; no live model calls |
| `2026-08-24T06:53:18Z` | `agent:codex-score-validation` | `npm test` then `npm run typecheck` in `asl/_vendor/smart-loader` | One file/four tests passed in `511ms`; typecheck passed; exit `0` | Implementation evidence | Loader regression checks are unchanged and narrow |
| `2026-08-24T06:53:18Z` | `agent:codex-score-validation` | `.venv/bin/python -m pytest -q -p no:cacheprovider` | `No module named pytest`; exit `1`, tests not run | Implementation evidence | Known repository-local environment limitation; system-Python suite passed |
| `2026-08-24T06:53:18Z` | `agent:codex-score-validation` | Sibling protocol validator, seven source byte comparisons, target manifest/symlink/link/HANDOFF checks, `git diff --check`, six-path scope assertion, pointer/spec exclusion, and unrelated-file digest checks | Passed; exit `0` | Implementation evidence and final scope output | Independent review of the containing commit remains pending |
| `2026-08-24T06:55:10Z` | `agent:codex-score-validation` | Final staged-tree rerun: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | `76 passed in 7.80s`; exit `0` | Implementation evidence | Governance-only timestamp/result updates followed; product/test bytes did not change |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-score-validation`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** Accepted specification §§2.1/4.2/8/11/12 and the bounded issue scope
- **Checks and evidence reviewed:** Recorded implementation verification is preparatory only
- **Findings and corrections:** One test-assertion correction is recorded in implementation evidence
- **Limitations:** Implementor verification cannot satisfy the required independent review gate
- **Residual risks:** Independent correctness/architecture review remains pending
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — the eventual change controls candidate acceptance and persisted evaluation evidence.

### 2026-08-24T07:10:15Z — agent:claude-code-independent-review

- **Reviewed repository state:** Containing implementation commit `391d73e702bae34ebcdd334d68cdbed27d450fa6`, direct parent `ac93c21881ab3ddedf709a3baaa1703d3d189666`; `origin/main` and direct remote `main` at the reviewed target (refreshed); tracked tree clean with exactly the four recorded unrelated untracked JavaScript files.
- **Reviewed target:** `391d73e702bae34ebcdd334d68cdbed27d450fa6`
- **Open material findings:** `0`
- **Scope:** Behavioral correctness, regression coverage, fail-closed behavior, aggregation semantics, persisted evaluation state, and scope containment of the bounded score-validation slice against the accepted specification and this issue.
- **Commands or procedures:** Read the specification sections, issue, and implementation evidence before code; read the full `asl/pipeline.py` and test diffs; traced all score-record producers/consumers including `metadata.json` embedding and the two render consumers; reran the full suite (`76 passed in 10.25s`), loader tests and typecheck, sibling validator, structure/link checks, digests, remotes, and listener check; ran eleven independent `_score_metadata()` edge probes beyond the committed tests and an independent end-to-end positive-path pipeline run. Full detail is in the linked evidence.
- **Specification compliance:** The change satisfies §4.2 and invariant 3 within the slice's authorized bounds: only valid votes participate, and no valid vote means no acceptance.
- **Correctness and regression findings:** All scoped invalid/fallback cases fail closed with attributable persisted errors; valid-vote aggregation policy, verdict normalization, fallback-candidate rejection, pointer logic, prompts, and routing are unchanged; the entire pre-existing suite passes with zero removed test lines; the positive acceptance path was independently reproduced.
- **Architecture and complexity findings:** The additive `valid`/`validation_errors` fields and `null` invalid vote fields are the minimal auditable state for the defect; no new dependency, process, or cross-module contract was introduced.
- **Material findings and resolution conditions:** `NONE`. Non-material observations: the non-dict JSON guard is practically unreachable given the `{`-anchored extraction, and whitespace-suffixed verdicts are rejected rather than stripped; both fail closed.
- **Limitations:** No live provider calls; `.venv` pytest remains unavailable; same host class as the implementor; labels are attributable, not authenticated.
- **Residual risks:** Previously persisted score records are not migrated (declared out of scope); the broader configurable §14 policy remains intentionally open.
- **Evidence:** [`EVIDENCE-20260824T071015Z-score-validation-review`](../EVIDENCE/EVIDENCE-20260824T071015Z-score-validation-review.md)
- **Disposition:** `APPROVED`
- **Prior-round resolution:** `FIRST ROUND`

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; the issue is closed after independent `APPROVED`.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Resolved: independent review of commit `391d73e` recorded `APPROVED` with zero open material findings at `2026-08-24T07:10:15Z`.
- The broader configurable evaluation policy remains an intentional open design decision under specification §14.
- Previously persisted score records are not migrated; they predate the additive validity fields, as declared in the rollback note.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded the reproduced fail-open score-validation defect and bounded the first post-review slice. |
| `2026-08-24T06:44:12Z` | `agent:codex-score-validation` | `OPEN` | `INVESTIGATING` | Recovered accepted authority and independently reproduced all bounded invalid/fallback score cases before editing. |
| `2026-08-24T06:45:19Z` | `agent:codex-score-validation` | `INVESTIGATING` | `IMPLEMENTING` | Fixed the minimal validation boundary from the existing prompt schema: validate every result, persist invalid records/errors, aggregate eligible votes only, and fail closed when none remain. |
| `2026-08-24T06:48:17Z` | `agent:codex-score-validation` | `IMPLEMENTING` | `VERIFYING` | Product/test implementation completed; targeted tests now pass, and full regression/governance verification began. |
| `2026-08-24T06:53:18Z` | `agent:codex-score-validation` | `VERIFYING` | `REVIEW` | Full executable, protocol, persistence, link, integrity, and scope checks passed; immutable containing commit now requires a fresh independent disposition. |
| `2026-08-24T07:10:15Z` | `agent:claude-code-independent-review` | `REVIEW` | `CLOSED` | Fresh independent review of `391d73e` recorded `APPROVED` with zero open material findings after rerunning the suites and independent edge/positive-path probes; fail-closed behavior, aggregation semantics, persistence, and scope containment verified. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [x] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [x] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [x] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [x] HANDOFF reflects the resulting current state and exactly one next action.
