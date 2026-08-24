# Human Checkpoint

This file is a low-bandwidth synchronization point for the human technical owner. It summarizes current understanding and pending authority decisions; it does not override [`PROJECT_SPEC.md`](PROJECT_SPEC.md), accepted ADRs, executable contracts, or evidence.

## Checkpoint metadata

- **Generated UTC:** `2026-08-24T06:55:10Z`
- **Prepared by:** `agent:codex-score-validation`
- **Period covered:** Product revision `387bffe632ba2d53c14aa59de93bd645935d9a94` through the approved governance baseline at `ac93c21` and the containing fail-closed score-validation review target
- **Specification status reviewed:** [`PROJECT_SPEC.md`](PROJECT_SPEC.md) v0.1, `ACCEPTED` by `human:technical-owner`
- **Implementation/reference state:** Governance baseline `ac93c21`; fail-closed score validation in the containing implementation commit with `76` passing Python tests; quality-gate issue pending independent review
- **Prior checkpoint:** Fresh governance-review checkpoint at `2026-08-24T06:25:44Z`

## System mental model

**CONFIRMED:** ASL is a local-first Python workflow that stores each paper run in a `vN` workspace. It normalizes local data/references through a bundled TypeScript smart-loader, optionally gathers Crossref/web leads, builds a research plan and candidate draft, runs a configurable reviewer panel and revision planner, then compares the candidate with the accepted baseline. Versions preserve prompts, model-route metadata, reviews, focus, research traces, score output, and rendered artifacts. Remote APIs, OpenAI-compatible/local endpoints, Ollama, and agent CLIs are available per-role execution routes; offline fallbacks keep the workflow locally runnable.

**CONFIRMED:** Healthy projects distinguish chronological candidates from the accepted pointer and retain rejected candidates. Structured review prompts produce separately persisted reports; revision planning requests named actionable sections and feeds both the findings and checklist into later iteration. A parsed `Underused references` signal plus anchor/history rotation changes later evidence focus. “Evidence resolution” is currently character-budget selection, not semantic metadata/abstract/excerpt/full-text state. Search leads carry provenance but no explicit verified/candidate status.

**CONFIRMED:** A missing/invalid accepted pointer still resolves to chronological latest and remains owner-gated. The bounded score-validation slice now requires all prompted fields and a non-fallback provider, persists invalid results with errors and `null` vote fields, aggregates only valid votes, and rejects when none remain. Model presets and the catalog expose descriptive capability tags, but workflow stages and execution do not consume them for requirement negotiation. The score change is verified but awaits independent review.

## Material changes since the prior checkpoint

| Change | Why | Product/architecture effect | Evidence and review |
|---|---|---|---|
| Accepted specification v0.1 attributed to the technical owner and adopted protocol source hierarchy | Establish current product intent and durable continuity before refactoring | Governance-only; no runtime/API/persistence behavior changed; attribution is recorded but not authenticated | [Accepted adoption ADR](ADR/ADR-20260824T024051Z-protocol-adoption.md); first review returned `CHANGES_REQUIRED`, repair approved by fresh independent review |
| Replaced the historical handoff with an evidence-backed operational snapshot | Prevent legacy implementation claims from becoming requirements | Historical bytes remain in Git; current handoff points to active records | [Repository recovery evidence](EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md) |
| Classified current behavior against requirements and all fifteen initial invariants | Bound later refactoring to observed gaps | No product code or tests changed | [Reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md) |
| Independently reviewed `e9ef291` and repaired three material governance findings | Correct §4.4/§4.10 classifications, remove an optional owner escalation, and qualify unreproducible pre-adoption provenance | Governance/recovery records only; accepted authority and product behavior unchanged | [`CHANGES_REQUIRED` review evidence](EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md); repair was subsequently approved in the next row |
| Fresh independent review approved the repair commit `113b8b0` and closed adoption/recovery | Satisfy the protocol's independent-review gate and exit adoption/recovery | None; governance records only | [`APPROVED` fresh review evidence](EVIDENCE/EVIDENCE-20260824T062544Z-fresh-independent-review.md); adoption issue `CLOSED` |
| Implemented bounded fail-closed score validation | Prevent malformed, missing, invalid, or fallback scorer output from authorizing candidate acceptance | Additive score validity/error fields; invalid records persist but do not vote; valid aggregation policy unchanged | [Implementation evidence](EVIDENCE/EVIDENCE-20260824T064412Z-score-validation.md); independent review pending |

## Architecture decisions

### Accepted, rejected, superseded, or closed

| Record | Status | Decision and consequence | Owner authority evidence |
|---|---|---|---|
| [Protocol adoption](ADR/ADR-20260824T024051Z-protocol-adoption.md) | `ACCEPTED` | Install protocol entry/templates, preserve application README/specification, replace handoff through a recorded merge, and keep the pass governance-only | `human:technical-owner`, `2026-08-24T02:40:51Z` in the ADR and specification change record |
| [Review routing/guidance](ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) | `CLOSED` | Current §§4.3, 4.4, and 4.9 requirements are implemented; richer schemas, aggregation, and persona routes are optional §14 work requiring newly selected scope | Accepted specification wording plus independent `APPROVED` issue disposition at `2026-08-24T03:31:59Z` |

### Proposed or disputed

| ADR or issue | Decision needed | Alternatives and tradeoff | Deadline/blocking impact |
|---|---|---|---|
| [Accepted-baseline ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) | Define behavior for missing/malformed/dangling accepted pointers | Fail closed with explicit repair (recommended); reconstruct from explicit per-version acceptance; or retain legacy latest fallback | Blocks any pointer-semantics refactor |
| [Evidence resolution/provenance](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) | Define minimum representation and candidate/verified states | Small file-backed state model first; defer retrieval technology versus broader evidence platform | Needed before persistent evidence-boundary design |
| [Normalization/capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) | Set fidelity evidence threshold and any capability-requirement/execution contract | Evidence-first fixture matrix; reuse descriptive static tags versus add runtime negotiation | Existing tags are evidence only; later architecture choice remains owner-gated |

## Complexity and architecture drift

### New or retired complexity

| Cost | Why introduced/removed | Coverage | Residual debt |
|---|---|---|---|
| Protocol governance records and independent-review gate | Preserve authority and continuity across replaceable participants | Source validator, byte/link/structure checks, evidence records, Git history | Adoption review closed with `APPROVED`; no residual adoption debt |
| Additive score validity/error state | Make vote eligibility and invalid-output causes auditable | Unit schema cases, mixed-vote/no-valid-vote integration tests, identical gate persistence assertions, and `76`-test regression suite | Independent review pending; configurable policy remains open §14 scope |

### Drift assessment

- **Last independent drift review:** Governance/recovery reviews of `e9ef291` (`CHANGES_REQUIRED`, `2026-08-24T03:31:59Z`) and repair commit `113b8b0` (`APPROVED`, `2026-08-24T06:25:44Z`); not a comprehensive live-provider or corpus drift review
- **Classification:** Governance/recovery baseline `APPROVED`; product architecture remains otherwise `UNKNOWN` beyond recorded traces
- **Owner-relevant differences:** Missing-pointer fallback, character-slice resolution, missing evidence-verification state, incomplete normalization evidence, and descriptive capability tags not consumed by execution remain. Fail-open score parsing has a bounded verified fix pending independent review.

## Assumptions and uncertainty that changed

| Certainty | Earlier understanding | Current understanding | Consequence and evidence |
|---|---|---|---|
| `CONFIRMED` | README/legacy handoff described a mature versioned pipeline | Significant behavior is real and tested, but those documents are evidence rather than product authority | [Reconciliation](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md) separates implemented, partial, absent, and unknown claims |
| `CONFIRMED` | Newer versions were described as candidates | Normal flow retains rejected candidates, but damaged accepted state falls back to latest | Owner recovery policy is required before changing [accepted-baseline semantics](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) |
| `CONFIRMED` | Malformed and invalid score output was normalized into an eligible neutral/favorable vote | The bounded implementation now persists invalidity/errors, excludes invalid/fallback votes, and rejects with no valid score | [Score-validation evidence](EVIDENCE/EVIDENCE-20260824T064412Z-score-validation.md); independent review remains required |
| `CONFIRMED` | Reviewer guidance appeared only partially structured | Named review/revision prompt sections, persisted reports, and next-iteration data flow satisfy §4.4; schema/persona enrichment is optional | [Review routing/guidance](ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) is closed without product work |
| `CONFIRMED` | Capability representation was reported absent | Preset/catalog capability metadata exists, but execution does not consume it | §4.10 is partial; [capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) now owns only the remaining execution gap |
| `UNKNOWN` | Exact pre-adoption specification bytes were reported reconstructed | Repository evidence cannot repeat that reconstruction or authenticate authorship; current accepted authority remains valid | Provenance is explicitly limited in the [independent review evidence](EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md) |
| `UNKNOWN` | Supported formats/routes imply complete compatibility | Existing suites do not prove representative fidelity or live-provider behavior | §12 completion is not claimed |

## Confidence and verification

- **What is directly verified:** Governance integrity from prior evidence plus the score boundary's six invalid/fallback cases, valid-score compatibility, mixed-vote exclusion, persisted errors/no-valid rejection, `76` Python tests, `4` loader tests, and loader typecheck; see [score-validation evidence](EVIDENCE/EVIDENCE-20260824T064412Z-score-validation.md).
- **What was independently reviewed:** Governance baseline through `113b8b0` was approved and adoption closed. The containing score-validation implementation has not yet been independently reviewed.
- **What was not run or remains unverified:** `.venv` pytest was unavailable; no real provider credentials, live model endpoint, network research, representative format corpus, OCR-fidelity study, or externally configured CI was verified.
- **Known regressions or unresolved risks:** No regression was observed in supported checks. Score validation remains review-gated; the other three focused issues and exact pre-adoption provenance limitation remain unchanged.

## Human attention required

| Decision ID | Decision requested | Recommendation and rationale | Alternatives | Needed by | Response | Responder | Decision UTC | Durable authority reference |
|---|---|---|---|---|---|---|---|---|---|
| `DECISION-ACCEPTED-POINTER-RECOVERY-v1` | What must happen when the accepted pointer is missing, malformed, or dangling? | Fail closed, report accepted state as unknown, and require an explicit repair/migration; this prevents a newer unevaluated candidate from becoming authoritative | Reconstruct only from explicit per-version acceptance metadata; retain latest fallback for legacy compatibility | Before any accepted-pointer refactor | `PENDING` | `PENDING` | `PENDING` | [Owning issue](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) pending a specification update and, if architectural, an ADR |
| `DECISION-EVIDENCE-STATE-v1` | What minimum availability/resolution/verification states must persist? | Define small explicit states before selecting retrieval technology | Keep prompt-only discipline; design a broader evidence platform immediately | Before persistent evidence-boundary refactoring | `PENDING` | `PENDING` | `PENDING` | [Owning issue](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |

## No human attention required

- Fresh independent review of the containing governance-repair commit recorded `APPROVED`; the adoption/recovery gate is satisfied and the issue is closed.
- The bounded score-validation slice is implemented and verified without requiring a new owner decision; a fresh independent review is the remaining closure gate.
- Validated reviewer schemas, aggregation, and persona-specific routes are optional §14 work, not a current requirement gap or owner decision.
- Normalization fixture gathering may proceed later without choosing a new architecture or dependency.

## Next checkpoint trigger

- **Trigger:** Independent disposition on the containing score-validation commit, any owner response above, or a proposed evidence/capability ADR.
- **Expected owner action before then:** No action is required for score validation. Decide only `DECISION-ACCEPTED-POINTER-RECOVERY-v1` if pointer semantics are to enter implementation; other decisions may wait until their issues become selected work.
