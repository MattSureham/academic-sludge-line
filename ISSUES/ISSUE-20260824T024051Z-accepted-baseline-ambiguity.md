# ISSUE-20260824T024051Z: Resolve Accepted-Baseline Recovery Semantics

## Metadata

- **ID:** `ISSUE-20260824T024051Z-accepted-baseline-ambiguity`
- **Title:** Resolve accepted-baseline recovery semantics for a missing or invalid pointer
- **Status:** `BLOCKED`
- **Severity:** `HIGH`
- **Owner:** `human:technical-owner`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T02:40:51Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.1, 4.1–4.2, 8, 11 invariants 1–4, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md)
- **Milestone:** `NONE`

## Problem

`accepted_version()` treats a missing or invalid accepted pointer as chronological latest. That makes accepted state ambiguous precisely when its explicit marker is damaged or absent and risks collapsing accepted and latest semantics contrary to the specification.

## Evidence or reproduction

An isolated temporary workspace with `v1` and `v2` returns `v2` both when `accepted` is missing and when it contains an invalid target. The behavior follows [`asl/workspace.py`](../asl/workspace.py), and the exact reproduction is recorded in the reconciliation evidence.

## Expected behavior

The accepted baseline and chronological latest remain distinct and auditable. The specification requires that candidates not replace the accepted version merely by being newer, but §14 intentionally leaves persistence details open and does not state a corruption-recovery policy.

## Assumptions

- **CONFIRMED:** Healthy accepted pointers preserve the intended candidate-versus-accepted distinction and rejected candidates remain on disk.
- **CONFIRMED:** Missing and invalid pointers currently resolve to latest.
- **INFERRED:** Silently selecting latest is fail-open behavior and can promote an unevaluated candidate.
- **UNKNOWN:** Whether legacy projects intentionally rely on this fallback and which explicit recovery contract the owner wants.

## Investigation and decision

Owner decision requested: define the product behavior for absent, malformed, or dangling accepted pointers. Recommendation: fail closed, treat accepted state as unknown, and require a separate explicit repair/migration operation. Alternatives are reconstructing acceptance only from explicit immutable per-version acceptance metadata, or retaining latest fallback for legacy compatibility. No alternative is adopted by this issue.

## Change

- **Files or components:** Future `asl/workspace.py`, persistence contracts, migration/recovery command, and tests; none changed in this pass.
- **Behavior changed:** `NONE` — evidence and decision request only.
- **Out-of-scope work deliberately excluded:** Implementing or testing a pointer policy before owner authorization.
- **Rollback or recovery:** `NOT APPLICABLE`

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Potential explicit recovery/migration path | Avoid silent baseline promotion while retaining recoverability | No contract exists yet | This issue owns the decision and later coverage |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Isolated Python reproduction invoking `accepted_version()` with missing and invalid pointers | Both cases resolved to `v2`; exit `0` | Reconciliation evidence | Does not measure prevalence in external projects |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-recovery`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** `NOT APPLICABLE`
- **Checks and evidence reviewed:** `NOT APPLICABLE`
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** Owner decision and later independent implementation review are required
- **Residual risks:** Silent accepted-baseline promotion remains in current behavior
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — the eventual resolution affects persistent state and candidate acceptance semantics.

No review round has been recorded.

## Blocker

- **Blocked from:** `INVESTIGATING`
- **Blocker:** The accepted specification does not choose a damaged-pointer recovery policy.
- **Unblock owner:** `human:technical-owner`
- **Unblock condition:** Record explicit product wording in `PROJECT_SPEC.md`; record an ADR as well if the choice commits to a persistent-state architecture or migration design.

## Residual uncertainty

- Legacy compatibility impact is unknown because only local ignored workspaces were sampled and they all had valid accepted pointers.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded the recovered mismatch between explicit accepted semantics and latest fallback. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `OPEN` | `INVESTIGATING` | Reproduced missing- and invalid-pointer behavior in an isolated workspace. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `INVESTIGATING` | `BLOCKED` | A product and likely persistence-policy decision requires owner authority. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [x] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [ ] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [ ] HANDOFF reflects the resulting current state and exactly one next action.
