# ISSUE-20260824T024051Z: Establish Normalization Fidelity and Capability-Aware Coverage

## Metadata

- **ID:** `ISSUE-20260824T024051Z-normalization-capability-coverage`
- **Title:** Establish normalization fidelity and capability-aware model coverage
- **Status:** `OPEN`
- **Severity:** `MEDIUM`
- **Owner:** `human:technical-owner`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T02:40:51Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.4–2.5, 4.8–4.10, 6.1, 6.4, 11 invariants 10–13, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md)
- **Milestone:** `NONE`

## Problem

The bundled smart-loader is an explicit heterogeneous-input boundary with structured output and warnings, but its four-test suite does not establish semantic fidelity or warning propagation across every advertised format. Separately, role bindings support several providers/endpoints, yet workflow behavior branches on hard-coded provider/tool flags rather than a general representation of model capabilities. Capability-aware execution is absent.

## Evidence or reproduction

Inspection covered the Python smart-loader adapter, bundled TypeScript registry/loaders/types/tests, provider clients, role routing, CLI configuration, and pipeline branches. The bundled checks pass (`4` tests and typecheck), but no capability descriptor/requirement negotiation was found and format-specific fidelity evidence is sparse.

## Expected behavior

The normalization boundary preserves useful structure and exposes known degradation, while workflow stages request relevant model capabilities rather than depending on provider names where practical. The specification leaves parser strategy and static-versus-runtime capability discovery open.

## Assumptions

- **CONFIRMED:** Markdown/text/JSON/CSV/HTML/PDF/CAJ/DOCX/DOC routes exist through the explicit loader boundary.
- **CONFIRMED:** Provider-independent role selection and local endpoint support exist independently of capability modeling.
- **INFERRED:** Current warning fields are a useful contract seed but are not enough to claim invariant 13 across supported formats.
- **UNKNOWN:** Required fidelity thresholds, canonical normalized structure, and whether capability discovery should be configuration-based or negotiated at runtime.

## Investigation and decision

Split later execution into evidence-first slices: build representative format fixtures and warning/fidelity assertions before changing the loader contract; separately propose the minimum capability descriptor needed by one demonstrated workflow branch. Owner acceptance is needed before committing to either a new normalization schema or a durable capability architecture.

## Change

- **Files or components:** Future smart-loader contracts/fixtures/adapters and model-binding capability interfaces/tests; none changed in this pass.
- **Behavior changed:** `NONE`.
- **Out-of-scope work deliberately excluded:** New parser dependencies, loader rewrite, capability negotiation, or provider refactor during recovery.
- **Rollback or recovery:** `NOT APPLICABLE`

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Potential normalized-evidence contract and model-capability descriptor | Address two explicit but currently incomplete/absent boundaries | Existing tests prove only a narrow baseline | This issue owns evidence gathering and later authority decisions |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm test` in `asl/_vendor/smart-loader` | One file and four tests passed; exit `0` | Repository-recovery evidence | Small suite; not a format-fidelity matrix |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm run typecheck` in `asl/_vendor/smart-loader` | Passed; exit `0` | Repository-recovery evidence | Type correctness does not prove extraction fidelity |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Static provider/capability trace | No general capability representation found | Reconciliation evidence | Absence based on inspected repository revision |

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
- **Residual risks:** Advertised format coverage and capability behavior remain incompletely evidenced
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — future normalization or capability contracts create cross-module commitments and may add dependencies.

No review round has been recorded.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; evidence gathering can precede any owner-gated architecture proposal.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- No representative fixture matrix establishes which structures or warnings survive each advertised format.
- No concrete workflow currently states capability requirements independently of provider configuration.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded partial normalization evidence and absent capability-aware execution. |

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
