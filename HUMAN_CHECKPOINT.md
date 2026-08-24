# Human Checkpoint

This file is a low-bandwidth synchronization point for the human technical owner. It summarizes current understanding and pending authority decisions; it does not override [`PROJECT_SPEC.md`](PROJECT_SPEC.md), accepted ADRs, executable contracts, or evidence.

## Checkpoint metadata

- **Generated UTC:** `2026-08-24T02:59:54Z`
- **Prepared by:** `agent:codex-recovery`
- **Period covered:** Target revision `387bffe632ba2d53c14aa59de93bd645935d9a94` through the first protocol-adoption governance change
- **Specification status reviewed:** [`PROJECT_SPEC.md`](PROJECT_SPEC.md) v0.1, `ACCEPTED` by `human:technical-owner`
- **Implementation/reference state:** Product code and tests at `387bffe`; recovery records in the containing governance commit
- **Prior checkpoint:** `NONE`

## System mental model

**CONFIRMED:** ASL is a local-first Python workflow that stores each paper run in a `vN` workspace. It normalizes local data/references through a bundled TypeScript smart-loader, optionally gathers Crossref/web leads, builds a research plan and candidate draft, runs a configurable reviewer panel and revision planner, then compares the candidate with the accepted baseline. Versions preserve prompts, model-route metadata, reviews, focus, research traces, score output, and rendered artifacts. Remote APIs, OpenAI-compatible/local endpoints, Ollama, and agent CLIs are available per-role execution routes; offline fallbacks keep the workflow locally runnable.

**CONFIRMED:** Healthy projects distinguish chronological candidates from the accepted pointer and retain rejected candidates. Reviewer prose and revision plans feed later prompts; a parsed `Underused references` signal plus anchor/history rotation changes later evidence focus. “Evidence resolution” is currently character-budget selection, not semantic metadata/abstract/excerpt/full-text state. Search leads carry provenance but no explicit verified/candidate status.

**CONFIRMED:** Two fail-open boundaries materially limit trust: a missing/invalid accepted pointer resolves to chronological latest, and malformed judge output becomes a `same` vote with default scores. Capability-aware execution is absent. These are implementation facts, not authorized product semantics.

## Material changes since the prior checkpoint

| Change | Why | Product/architecture effect | Evidence and review |
|---|---|---|---|
| Accepted owner-authored specification v0.1 and adopted protocol source hierarchy | Establish product intent and durable continuity before refactoring | Governance-only; no runtime/API/persistence behavior changed | [Accepted adoption ADR](ADR/ADR-20260824T024051Z-protocol-adoption.md); independent review pending |
| Replaced the historical handoff with an evidence-backed operational snapshot | Prevent legacy implementation claims from becoming requirements | Historical bytes remain in Git; current handoff points to active records | [Repository recovery evidence](EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md) |
| Classified current behavior against requirements and all fifteen initial invariants | Bound later refactoring to observed gaps | No product code or tests changed | [Reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md) |

## Architecture decisions

### Accepted, rejected, or superseded

| ADR | Status | Decision and consequence | Owner authority evidence |
|---|---|---|---|
| [Protocol adoption](ADR/ADR-20260824T024051Z-protocol-adoption.md) | `ACCEPTED` | Install protocol entry/templates, preserve application README/specification, replace handoff through a recorded merge, and keep the pass governance-only | `human:technical-owner`, `2026-08-24T02:40:51Z` in the ADR and specification change record |

### Proposed or disputed

| ADR or issue | Decision needed | Alternatives and tradeoff | Deadline/blocking impact |
|---|---|---|---|
| [Accepted-baseline ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) | Define behavior for missing/malformed/dangling accepted pointers | Fail closed with explicit repair (recommended); reconstruct from explicit per-version acceptance; or retain legacy latest fallback | Blocks any pointer-semantics refactor |
| [Review routing/guidance](ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) | Define minimum structured reviewer signals and persona-to-model semantics | Small validated signal contract versus continued prose parsing; explicit persona routes versus optional overrides | Needed before that subsystem's contract changes |
| [Evidence resolution/provenance](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) | Define minimum representation and candidate/verified states | Small file-backed state model first; defer retrieval technology versus broader evidence platform | Needed before persistent evidence-boundary design |
| [Normalization/capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) | Set fidelity evidence threshold and minimum capability representation | Evidence-first fixture matrix; static capability declarations versus runtime negotiation | Evidence gathering can proceed; architecture choice remains owner-gated |

## Complexity and architecture drift

### New or retired complexity

| Cost | Why introduced/removed | Coverage | Residual debt |
|---|---|---|---|
| Protocol governance records and independent-review gate | Preserve authority and continuity across replaceable participants | Source validator, byte/link/structure checks, evidence records, Git history | Adoption review remains open |
| Product/runtime complexity | None introduced in this pass | Product files and tests remain byte-unchanged | Existing gaps are indexed in active issues |

### Drift assessment

- **Last independent drift review:** `NOT PERFORMED`
- **Classification:** `UNKNOWN`
- **Owner-relevant differences:** Reconciliation found a missing-pointer fallback, fail-open score parsing, character-slice resolution, missing verification state, incomplete normalization evidence, and absent capability-aware execution. See the four focused owner issues and the agent-owned quality-gate issue.

## Assumptions and uncertainty that changed

| Certainty | Earlier understanding | Current understanding | Consequence and evidence |
|---|---|---|---|
| `CONFIRMED` | README/legacy handoff described a mature versioned pipeline | Significant behavior is real and tested, but those documents are evidence rather than product authority | [Reconciliation](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md) separates implemented, partial, absent, and unknown claims |
| `CONFIRMED` | Newer versions were described as candidates | Normal flow retains rejected candidates, but damaged accepted state falls back to latest | Owner recovery policy is required before changing [accepted-baseline semantics](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) |
| `CONFIRMED` | Quality scoring was described as a gate | The gate exists, but malformed output is normalized into an accepting `same` vote | First bounded post-review fix is [fail-closed score validation](ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md) |
| `UNKNOWN` | Supported formats/routes imply complete compatibility | Existing suites do not prove representative fidelity or live-provider behavior | §12 completion is not claimed |

## Confidence and verification

- **What is directly verified:** Target/source refs and status, copied-artifact bytes, target manifest/symlink/link/HANDOFF structure, legacy/unrelated-file digests, current code paths, isolated pointer/scorer diagnostics, `66` Python tests, `4` loader tests, and loader typecheck; see [recovery evidence](EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md).
- **What was independently reviewed:** `NONE`; the containing governance commit still requires a fresh independent review.
- **What was not run or remains unverified:** `.venv` pytest was unavailable; no real provider credentials, live model endpoint, network research, representative format corpus, OCR-fidelity study, or externally configured CI was verified.
- **Known regressions or unresolved risks:** No regression was observed; unresolved risks are the five focused issues plus pending adoption review.

## Human attention required

| Decision ID | Decision requested | Recommendation and rationale | Alternatives | Needed by | Response | Responder | Decision UTC | Durable authority reference |
|---|---|---|---|---|---|---|---|---|---|
| `DECISION-ACCEPTED-POINTER-RECOVERY-v1` | What must happen when the accepted pointer is missing, malformed, or dangling? | Fail closed, report accepted state as unknown, and require an explicit repair/migration; this prevents a newer unevaluated candidate from becoming authoritative | Reconstruct only from explicit per-version acceptance metadata; retain latest fallback for legacy compatibility | Before any accepted-pointer refactor | `PENDING` | `PENDING` | `PENDING` | [Owning issue](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) pending a specification update and, if architectural, an ADR |
| `DECISION-REVIEW-SIGNALS-v1` | What minimum structured reviewer signals and per-persona routing contract should be product-visible? | Define a small validated signal envelope and optional persona-specific binding, preserving prose as an artifact | Continue prose-only parsing; adopt a larger aggregation schema | Before review-contract refactoring | `PENDING` | `PENDING` | `PENDING` | [Owning issue](ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) |
| `DECISION-EVIDENCE-STATE-v1` | What minimum availability/resolution/verification states must persist? | Define small explicit states before selecting retrieval technology | Keep prompt-only discipline; design a broader evidence platform immediately | Before persistent evidence-boundary refactoring | `PENDING` | `PENDING` | `PENDING` | [Owning issue](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |

## No human attention required

- Fresh independent review of the containing governance commit is the immediate operational gate.
- After that review approves the baseline, the accepted specification already authorizes the bounded fail-closed score-validation slice; it does not need routine reapproval.
- Normalization fixture gathering may proceed later without choosing a new architecture or dependency.

## Next checkpoint trigger

- **Trigger:** Independent disposition on the protocol-adoption commit, any owner response above, or a proposed evidence/reviewer/capability ADR.
- **Expected owner action before then:** Decide only `DECISION-ACCEPTED-POINTER-RECOVERY-v1` if pointer semantics are to enter implementation; other decisions may wait until their issues become the selected work.
