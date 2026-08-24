# ISSUE-20260824T024051Z: Define Reviewer Routing and Structured Revision Guidance

## Metadata

- **ID:** `ISSUE-20260824T024051Z-review-routing-guidance`
- **Title:** Define reviewer-specific routing and structured revision guidance
- **Status:** `CLOSED`
- **Severity:** `MEDIUM`
- **Owner:** `human:technical-owner`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T03:46:47Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§4.3–4.5, 4.9, 8, 11 invariants 5–7 and 9–10, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md), [`EVIDENCE-20260824T033159Z-governance-independent-review`](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md)
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

## Independent review resolution

Independent review corrected the premise of this issue. The current v0.1 implementation satisfies mandatory §§4.3, 4.4, and 4.9 behavior: configurable independent reviewer reports feed named revision-plan sections and subsequent iteration, while major workflow roles retain independent bindings. The accepted specification does not require a validated output schema and says reviewer-specific model/provider assignments `MAY` be configured.

The issue is therefore closed as **no current required gap**, without product or architecture work. Richer review schemas, aggregation, and per-persona routing remain optional §14 ideas. They require newly selected owner scope before implementation, but they are not a current decision queue or completion blocker.

## Change

- **Files or components:** Future reviewer configuration, prompts/output validation, orchestration, persistence, and tests; none changed in this pass.
- **Behavior changed:** `NONE`.
- **Out-of-scope work deliberately excluded:** Selecting an aggregation algorithm, changing the default reviewer count, or redesigning current prompts during recovery.
- **Rollback or recovery:** `NOT APPLICABLE`
- **Governance correction:** This issue record was closed after independent review established that the cited enrichment is optional and current mandatory behavior is implemented.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Optional future review-signal schema and per-persona routing | Possible enrichment only if the owner later selects new §14 scope | Current structured prompts, persisted flow, tests, and independent trace cover mandatory v0.1 behavior | No current debt or decision is owned by this closed issue |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Static trace of reviewer loop, role dispatch, prompt reuse, and tests | Findings recorded; not an executable behavioral proof | Reconciliation evidence | No live model/provider calls were made |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | Trace `review_prompt()`, `revision_prompt()`, reviewer persistence, next-iteration prompt input, `Underused references` flow, role routes, tests, and §§4.3–4.4/4.9 wording | Mandatory review/revision behavior found implemented; validated schema and persona-specific routes found optional; exit `0` | Independent review evidence | No live provider call; optional enrichment was not designed or selected |

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

- **Required:** `YES` — closure corrects a requirement classification and owner escalation at the governance boundary.

### 2026-08-24T03:31:59Z — agent:codex-governance-review

- **Reviewed repository state:** Candidate governance baseline `e9ef291a0be124a1ea1ad782c6bb307a486f2b18`; product implementation and tests at parent `387bffe632ba2d53c14aa59de93bd645935d9a94`.
- **Reviewed target:** `e9ef291a0be124a1ea1ad782c6bb307a486f2b18`
- **Open material findings:** `0`
- **Scope:** Accepted `PROJECT_SPEC.md` §§4.3–4.5, 4.9, 8, 11 invariants 5–7 and 9–10; issue assertions; prompt construction; reviewer loop and artifacts; revision guidance data flow; model routes; focused tests; and recovery reconciliation.
- **Commands or procedures:** Read the accepted requirement wording before code; used `rg -n` and `sed -n` to trace `review_prompt()`, `revision_prompt()`, review persistence, revision-plan and next-iteration inputs, `Underused references` parsing, and route selection; inspected related tests and reran the executable baseline recorded in the linked evidence.
- **Specification compliance:** §§4.3, 4.4, and 4.9 mandatory behavior is implemented. A validated schema is not required, and persona-specific routing is expressly optional.
- **Correctness and regression findings:** Existing structured prompts and persisted data flow provide usable revision guidance; no product change is needed to close this classification issue.
- **Architecture and complexity findings:** Retaining this issue as a required owner decision would manufacture scope. Richer schemas, aggregation, or persona routes may be proposed later only as newly selected §14 work.
- **Material findings and resolution conditions:** `NONE`
- **Limitations:** No live multi-provider reviewer run was performed; that does not alter the mandatory-versus-optional requirement classification.
- **Residual risks:** Free-form model output may still vary, but no accepted v0.1 requirement makes a validated output envelope or persona route mandatory.
- **Evidence:** [`EVIDENCE-20260824T033159Z-governance-independent-review`](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md)
- **Disposition:** `APPROVED`
- **Prior-round resolution:** `FIRST ROUND`

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; the issue is closed because no current required gap exists.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Live behavior across multiple distinct reviewer backends was not exercised.
- Richer review schemas and persona-specific routes remain optional future scope, not a current required gap.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded partial structured-guidance behavior and the unresolved reviewer-routing contract. |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | `OPEN` | `INVESTIGATING` | Re-read the accepted requirements and traced reviewer prompts, persistence, revision planning, next-iteration inputs, focus extraction, routes, and tests. |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | `INVESTIGATING` | `IMPLEMENTING` | Independent review found §4.4 implemented and persona-specific routing optional; began the authorized governance-only classification/closure correction. |
| `2026-08-24T03:37:13Z` | `agent:codex-governance-review` | `IMPLEMENTING` | `VERIFYING` | Recorded the additive resolution, complete independent round, optional-scope boundary, and current-state reconciliation without product work. |
| `2026-08-24T03:44:24Z` | `agent:codex-governance-review` | `VERIFYING` | `REVIEW` | Reviewer-guidance traces, executable suites, structural checks, and governance-path boundary passed as recorded in the linked evidence. |
| `2026-08-24T03:46:47Z` | `agent:codex-governance-review` | `REVIEW` | `CLOSED` | Latest issue-specific independent disposition is `APPROVED` with zero open material findings; closed the manufactured required gap while retaining optional §14 scope only. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [x] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [x] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [x] Required human authority is recorded in the owning artifact: the accepted specification already distinguishes mandatory behavior from optional reviewer-specific routing.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [x] HANDOFF reflects the resulting current state and exactly one next action.
