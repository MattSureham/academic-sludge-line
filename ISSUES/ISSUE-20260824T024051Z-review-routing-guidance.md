# ISSUE-20260824T024051Z: Define Reviewer Routing and Structured Revision Guidance

## Metadata

- **ID:** `ISSUE-20260824T024051Z-review-routing-guidance`
- **Title:** Define reviewer-specific routing and structured revision guidance
- **Status:** `OPEN`
- **Severity:** `MEDIUM`
- **Owner:** `human:technical-owner`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T02:40:51Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§4.3–4.5, 4.9, 8, 11 invariants 5–7 and 9–10, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md)
- **Milestone:** `NONE`

## Problem

The pipeline supports multiple reviewer personas and a three-reviewer default, but every persona invokes the same generic `review` role route. Reviewer outputs and revision plans are free-form Markdown; the only programmatic review-signal extraction found is a tolerant parser for lines labeled `Underused references`. This supports a useful loop but does not establish reviewer-specific model bindings or a reliable structured guidance contract.

## Evidence or reproduction

Inspection of [`asl/pipeline.py`](../asl/pipeline.py), prompt construction, CLI configuration, and [`tests/test_pipeline.py`](../tests/test_pipeline.py) confirms the reviewer loop, configurable names, persisted reports, revision-plan synthesis, next-iteration prompt use, and the `Underused references` parser. All reviewer calls use `role="review"`; no per-persona route or validated review schema was found.

## Expected behavior

Reviewer panels remain configurable and reviewer findings are usable as structured subsequent-iteration input. The specification permits reviewer-specific models/providers and explicitly leaves the exact aggregation algorithm and default panel policy open.

## Assumptions

- **CONFIRMED:** One or at least three reviewer personas can run without redesigning the pipeline.
- **CONFIRMED:** Prose reviews and the revision plan are injected into a subsequent iterative draft prompt.
- **INFERRED:** A single label parser is too narrow to establish the broader structured-signal requirement.
- **UNKNOWN:** The canonical review-signal schema, aggregation contract, and relationship between reviewer persona and model route.

## Investigation and decision

Before implementation, the owner should decide the minimum externally meaningful review-signal contract and whether reviewer personas require explicit model bindings or merely optional overrides. An ADR should then define separation between reviewer execution, validated signal extraction, aggregation, and revision planning without choosing a larger framework by default.

## Change

- **Files or components:** Future reviewer configuration, prompts/output validation, orchestration, persistence, and tests; none changed in this pass.
- **Behavior changed:** `NONE`.
- **Out-of-scope work deliberately excluded:** Selecting an aggregation algorithm, changing the default reviewer count, or redesigning current prompts during recovery.
- **Rollback or recovery:** `NOT APPLICABLE`

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Potential review-signal schema and per-persona routing | Make review guidance reliable while retaining independent model choice | Current prose behavior and tests are recovery evidence only | This issue owns the required decision and later contracts |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Static trace of reviewer loop, role dispatch, prompt reuse, and tests | Findings recorded; not an executable behavioral proof | Reconciliation evidence | No live model/provider calls were made |

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
- **Residual risks:** Prose coupling and same-role routing remain
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — the eventual contract affects model routing and cross-stage persisted data.

No review round has been recorded.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; the issue is open for owner design direction before implementation.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Live behavior across multiple distinct reviewer backends was not exercised.
- Current prose may contain useful signals the narrow parser cannot observe.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded partial structured-guidance behavior and the unresolved reviewer-routing contract. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [ ] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [ ] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [ ] HANDOFF reflects the resulting current state and exactly one next action.
