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
- **Updated UTC:** `2026-08-24T03:31:59Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.4–2.5, 4.8–4.10, 6.1, 6.4, 11 invariants 10–13, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md), [`EVIDENCE-20260824T033159Z-governance-independent-review`](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md)
- **Milestone:** `NONE`

## Problem

The bundled smart-loader is an explicit heterogeneous-input boundary with structured output and warnings, but its four-test suite does not establish semantic fidelity or warning propagation across every advertised format. Separately, model presets already carry descriptive capability tags, but stage contracts and route execution do not consume those tags to express or negotiate workflow requirements. Capability representation therefore exists while capability-aware execution remains incomplete.

## Evidence or reproduction

Inspection covered the Python smart-loader adapter, bundled TypeScript registry/loaders/types/tests, provider clients, preset catalog, role routing, CLI configuration, and pipeline branches. The bundled checks pass (`4` tests and typecheck). `ModelPreset` and `LocalModelPreset` contain provider-independent capability tuples, and `catalog_payload()` exposes a list for every discovered model; `ModelSpec`, `ModelRoutes`, and pipeline stages neither carry stage requirements nor negotiate execution from those tags. Format-specific fidelity evidence also remains sparse.

## Expected behavior

The normalization boundary preserves useful structure and exposes known degradation, while workflow stages request relevant model capabilities rather than depending on provider names where practical. The specification leaves parser strategy and static-versus-runtime capability discovery open.

## Assumptions

- **CONFIRMED:** Markdown/text/JSON/CSV/HTML/PDF/CAJ/DOCX/DOC routes exist through the explicit loader boundary.
- **CONFIRMED:** Provider-independent role selection and local endpoint support exist independently of capability modeling.
- **CONFIRMED:** Model preset/catalog records already expose descriptive capability metadata.
- **INFERRED:** Current warning fields are a useful contract seed but are not enough to claim invariant 13 across supported formats.
- **UNKNOWN:** Required fidelity thresholds, canonical normalized structure, and whether existing static tags should remain descriptive or participate in runtime requirement negotiation.

## Investigation and decision

Split later execution into evidence-first slices: build representative format fixtures and warning/fidelity assertions before changing the loader contract; separately use the existing preset tags as evidence and propose the minimum stage-requirement/execution contract needed by one demonstrated workflow branch. Owner acceptance is needed before committing to either a new normalization schema or a durable capability-negotiation architecture.

## Change

- **Files or components:** Future smart-loader contracts/fixtures/adapters and model-binding capability interfaces/tests; none changed in this pass.
- **Behavior changed:** `NONE`.
- **Out-of-scope work deliberately excluded:** New parser dependencies, loader rewrite, capability negotiation, or provider refactor during recovery.
- **Rollback or recovery:** `NOT APPLICABLE`

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Potential normalized-evidence contract and capability-requirement/execution contract | Address two explicit but currently incomplete boundaries | Existing tests and descriptive tags prove only a narrow baseline | This issue owns evidence gathering and later authority decisions |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm test` in `asl/_vendor/smart-loader` | One file and four tests passed; exit `0` | Repository-recovery evidence | Small suite; not a format-fidelity matrix |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm run typecheck` in `asl/_vendor/smart-loader` | Passed; exit `0` | Repository-recovery evidence | Type correctness does not prove extraction fidelity |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Static provider/capability trace | Initially recorded no general capability representation | Reconciliation evidence | Superseded by the independent catalog/preset trace below |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | Direct `catalog_payload()` inspection plus static trace through preset, route, and pipeline types | Capability lists exist for all discovered presets; no stage requirement or execution negotiation consumes them; exit `0` | Independent review evidence | Static/descriptive coverage does not establish real-provider capability behavior |

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
- Existing preset capability tags are descriptive only; no concrete workflow stage states or negotiates capability requirements independently of provider configuration.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded partial normalization evidence and absent capability-aware execution. |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | `OPEN` | `OPEN` | Corrected capability coverage: descriptive preset/catalog metadata exists, while capability-requirement negotiation and execution remain missing. |

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
