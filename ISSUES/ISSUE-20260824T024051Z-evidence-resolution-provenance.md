# ISSUE-20260824T024051Z: Define Evidence Resolution, Access, and Verification State

## Metadata

- **ID:** `ISSUE-20260824T024051Z-evidence-resolution-provenance`
- **Title:** Define evidence resolution, access, and provenance/verification state
- **Status:** `OPEN`
- **Severity:** `HIGH`
- **Owner:** `human:technical-owner`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T02:40:51Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.2, 2.6, 4.5–4.7, 4.11–4.12, 8, 11 invariants 6–8 and 14–15, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md)
- **Milestone:** `NONE`

## Problem

Current prompt allocation exposes focused references through fixed character slices (`3500` versus `600`) and a `full` strategy through a larger head slice. It does not model semantic states such as metadata, abstract, excerpt, table/assets, or full text, and allocation settings/history are only partially persisted. Search results retain query/provider/URL provenance, but the source boundary has no explicit candidate-versus-verified state, leaving verification discipline primarily in prompt wording.

## Evidence or reproduction

Static tracing of reference loading/allocation, version metadata, Crossref discovery, web research, and source serialization found focus selection and auditable search files but no common evidence-resource schema or verification transition. Generated ignored workspaces were sampled only as mutable traces; none are authority.

## Expected behavior

Evidence availability, selection, resolution, origin, and verification state remain distinct and inspectable. Local and discovered sources share a conceptual access boundary, and unverified leads cannot silently become verified citation support. The specification deliberately does not mandate a database, vector store, or exact retrieval technology.

## Assumptions

- **CONFIRMED:** Focus/rotation and search provenance are useful implemented behavior that should be preserved.
- **CONFIRMED:** Current “resolution” is character-budget allocation rather than a semantic representation contract.
- **INFERRED:** Prompt warnings reduce risk but cannot substitute for durable verification state.
- **UNKNOWN:** The canonical evidence-resource schema, verification actor/workflow, retrieval mechanism, and compatibility requirements for existing paper workspaces.

## Investigation and decision

The owner should first accept the minimum product-visible states and transitions for evidence availability, representation/resolution, and candidate/verified status. A later ADR can choose a small internal boundary and compatibility strategy. Avoid selecting embeddings, a vector database, or a tool protocol until evidence demonstrates that the accepted contract requires one.

## Change

- **Files or components:** Future evidence model/access boundary, allocation persistence, research records, prompts, migrations, and tests; none changed in this pass.
- **Behavior changed:** `NONE`.
- **Out-of-scope work deliberately excluded:** Retrieval implementation, verification policy, migrations, or prompt changes during recovery.
- **Rollback or recovery:** `NOT APPLICABLE`

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Potential common evidence-resource and verification-state boundary | Make resolution and provenance semantics explicit | Current file/provenance behavior is inventoried, not contracted | This issue owns the decision and future compatibility evidence |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Static trace of allocation, source metadata, discovery records, prompts, tests, and a read-only ignored-workspace sample | Partial behavior and missing state boundary recorded | Reconciliation evidence | No network research or citation verification was performed |

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
- **Residual risks:** Resolution semantics and verification state remain implicit
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — the eventual decision affects provenance, persisted state, and citation trust.

No review round has been recorded.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; owner direction is required before implementation but does not block repository recovery.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- No exhaustive corpus test establishes fidelity or resolution behavior across supported formats.
- External source verification policy is not defined.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded partial allocation/provenance behavior and the missing verification-state boundary. |

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
