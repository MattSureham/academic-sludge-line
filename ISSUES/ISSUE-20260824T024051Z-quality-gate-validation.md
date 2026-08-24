# ISSUE-20260824T024051Z: Make Quality-Gate Score Validation Fail Closed

## Metadata

- **ID:** `ISSUE-20260824T024051Z-quality-gate-validation`
- **Title:** Make quality-gate score-output validation fail closed
- **Status:** `OPEN`
- **Severity:** `HIGH`
- **Owner:** `agent:unassigned`
- **Authority:** `AGENT`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T02:40:51Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.1, 4.2, 8, 11 invariant 3, and §12
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md)
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

## Change

- **Files or components:** Future focused changes in quality-gate code and tests; none changed in this recovery pass.
- **Behavior changed:** `NONE` in this pass.
- **Out-of-scope work deliberately excluded:** New scoring policy, rubric redesign, reviewer consensus, accepted-pointer behavior, provider routing, or persistence migration.
- **Rollback or recovery:** Later implementation should remain one isolated, test-backed commit that can be reverted without changing stored candidates.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Explicit score validation state | Prevent invalid model output from silently authorizing acceptance | Planned unit and integration tests plus persisted errors | Broader policy configurability remains open under specification §14 |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Isolated call to `_score_metadata()` with non-JSON scorer text | Produced default `same`, `5`, `5`; exit `0` | Reconciliation evidence | Diagnostic only; no fix or new test was added |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-recovery`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** `NOT APPLICABLE`
- **Checks and evidence reviewed:** `NOT APPLICABLE`
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** No implementation exists to review
- **Residual risks:** Current fail-open behavior remains
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — the eventual change controls candidate acceptance and persisted evaluation evidence.

No review round has been recorded.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; execution is deliberately sequenced after independent review of the adoption baseline.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Existing tests do not cover malformed score output or a no-valid-votes branch.
- The broader configurable evaluation policy remains an intentional open design decision.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded the reproduced fail-open score-validation defect and bounded the first post-review slice. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [ ] The change or resolution is recorded.
- [ ] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [x] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [ ] HANDOFF reflects the resulting current state and exactly one next action.
