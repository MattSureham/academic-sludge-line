# EVIDENCE-20260824T024051Z: Specification-to-Implementation Reconciliation

## Metadata

- **ID:** `EVIDENCE-20260824T024051Z-spec-reconciliation`
- **Title:** Reconcile accepted PROJECT_SPEC v0.1 with current implementation and tests
- **Captured UTC:** `2026-08-24T02:40:51Z`
- **Recorded by:** `agent:codex-recovery`
- **Claim supported or challenged:** Current implementation satisfies some accepted requirements, partially satisfies others, lacks capability-aware execution, and cannot yet support full compatibility/completion claims.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§4, 7–8, and 10–12
- **Related ADRs/issues:** [`ADR-20260824T024051Z-protocol-adoption`](../ADR/ADR-20260824T024051Z-protocol-adoption.md); all active recovery issues in [`ISSUES/`](../ISSUES/)
- **Repository revision/state:** Implementation and tests at `387bffe632ba2d53c14aa59de93bd645935d9a94`; owner-authored specification v0.1 accepted with governance metadata only.
- **Environment:** Static inspection plus isolated diagnostics and the executable baseline recorded in [`EVIDENCE-20260824T024051Z-repository-recovery`](EVIDENCE-20260824T024051Z-repository-recovery.md).

## Method

- **Procedure:** Derive expected behavior from accepted `PROJECT_SPEC.md`, then trace relevant workspace, pipeline, prompt, provider, loader, discovery, renderer/UI, and test paths. Classify each requirement as `implemented`, `partially implemented`, `absent`, or `uncertain / insufficient evidence`; do not infer product intent from code or historical documents.
- **Exact command/input:** `rg -n`, `sed -n`, `git log/show`, Python and npm tests, and isolated calls to `accepted_version()` and `_score_metadata()`; see the repository-recovery evidence for command-level detail.
- **Exit status:** Static inspection `0`; diagnostics `0`; baseline checks as separately recorded.
- **Repeatability:** Check out revision `387bffe`, read the accepted specification first, inspect the named functions/tests, and repeat diagnostics without using ignored paper artifacts as authority.

## Raw observation

### Functional and cross-cutting requirement matrix

| Requirement | Classification | Current evidence | Principal limitation / mismatch | Owning issue |
|---|---|---|---|---|
| §4.1 Versioned iteration | **partially implemented** | `vN` directories, `accepted_version.txt`, per-version metadata, quality records, retained rejected candidates, and tests for rejection/checkpoint flow | `accepted_version()` falls back to chronological latest when the pointer is missing or invalid; lineage/audit fields are not a fully explicit state model | [accepted-baseline ambiguity](../ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) |
| §4.2 Quality gate | **partially implemented** | Candidate is compared with the accepted baseline; results/reasons are persisted; rejection/fallback tests exist | Malformed/invalid scorer output becomes a valid-looking `same`/`5`/`5` vote; invalid/fallback votes can participate when any real scorer exists; no configurable policy boundary | [quality-gate validation](../ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md) |
| §4.3 Reviewer panel | **implemented** | First-class reviewer loop, configurable reviewer names, persisted independent reports, default three-persona configuration, and dynamic rendering/tests | All personas share the generic review route; richer per-reviewer routing is optional under this section but tracked with §4.9 guidance | [review routing/guidance](../ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) |
| §4.4 Revision guidance | **partially implemented** | Reports feed a revision-plan stage; prior reports/plan feed the next iterative draft; `Underused references` influences focus | Outputs are free-form Markdown and only one narrow signal has programmatic parsing; no validated actionable-signal contract | [review routing/guidance](../ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) |
| §4.5 Evidence focus and rotation | **implemented** | Anchors, review-driven underused references, fresh/rotating batches, and persisted `reference_focus`; focused tests cover rotation and anchors | Allocation rationale/settings are not fully persisted, but the required focus/rotation behaviors exist | [evidence resolution/provenance](../ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |
| §4.6 Evidence resolution | **partially implemented** | `select`, `balanced`, and `full` strategies vary per-source character budgets and keep non-focused sources represented | “Full” is still head truncation at a raised character limit; `3500`/`600` slices are not semantic metadata/abstract/chunk/table/full-text representations | [evidence resolution/provenance](../ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |
| §4.7 Evidence accessibility | **partially implemented** | Local data/references, seed drafts, search leads, and generated assets enter pipeline context through explicit helpers | No common evidence-resource/access contract or on-demand evidence inspection boundary exists | [evidence resolution/provenance](../ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |
| §4.8 Smart loading/normalization | **partially implemented** | Explicit Python-to-bundled-loader boundary; adapters for Markdown/text/JSON/CSV/HTML/PDF/CAJ/DOCX/DOC; structured chunks/assets/errors/warnings | Four loader tests do not establish structure/fidelity/warning propagation across formats; some representations remain flattened or fallback-only | [normalization/capability coverage](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) |
| §4.9 Role-based model binding | **implemented** | Independent routes for plan/draft/review/revision/score; multiple providers and fallback chains; OpenAI-compatible/HTTP/local Ollama/agent-CLI routes; route metadata/tests | Reviewer personas cannot be assigned distinct role keys, a tracked enrichment rather than a failure of the section's mandatory role independence | [review routing/guidance](../ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) |
| §4.10 Capability-aware execution | **absent** | No general capability descriptor or stage requirement negotiation found | Workflow uses provider-specific checks and global tool/web booleans rather than capability-based selection | [normalization/capability coverage](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) |
| §4.11 Research discovery | **partially implemented** | Crossref and DuckDuckGo stages plus optional tool-capable CLI research; query/provider/URL/version/timestamp traces | `sources.json` has no explicit candidate/verified state or verification transition; agent search is less structured | [evidence resolution/provenance](../ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |
| §4.12 Grounding/citation discipline | **partially implemented** | Prompts label discovery results as leads, demand verification, preserve TODOs, and forbid fabricated citations | Discipline is mainly prompt-level; no durable verification-state boundary prevents silent promotion downstream | [evidence resolution/provenance](../ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |
| §4.13 Human-directed iteration | **implemented** | `--from`, focus/reference/data inputs, per-role model options, reviewer configuration, context strategy, and UI controls preserve version history | Interface breadth is evidenced locally; no claim is made for every combination with live providers | [protocol adoption/recovery](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) |
| §7 Local-first operation | **implemented** | Offline templates, local files, Ollama/OpenAI-compatible local endpoints, and local CLI execution require no hosted ASL service/database/queue | Optional network/provider paths were not exercised and are not required for this classification | [protocol adoption/recovery](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) |
| §8 Auditability | **partially implemented** | Per-version inputs, prompts, drafts, reviews, revision plan, focus, route metadata, research traces, score records, and rendered inspection output | Accepted-state corruption fallback, validation errors, semantic evidence resolution, verification status, and complete allocation rationale are not reconstructible | [accepted baseline](../ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md), [quality gate](../ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md), [evidence boundary](../ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) |
| §§10–12 Full compatibility and initial completion | **uncertain / insufficient evidence** | This record performs the required first reconciliation and identifies substantial validated behavior | Open defects/contracts and missing executable coverage prevent a full compatibility or completion claim; independent review is also pending | [protocol adoption/recovery](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) |

### §11 initial behavioral invariants

| # | Invariant classification | Evidence and boundary |
|---:|---|---|
| 1 | **partially implemented** | Normal candidate writes create a new `vN` and do not overwrite prior bytes, but missing/invalid accepted pointers can silently reinterpret latest as accepted. |
| 2 | **implemented** | Rejected candidates remain in their `vN` directories; `test_worse_candidate_is_kept_but_not_accepted` verifies inspection and unchanged accepted pointer. |
| 3 | **partially implemented** | The gate receives the accepted baseline in normal operation, but damaged-pointer fallback and malformed-score defaults weaken the guarantee. |
| 4 | **implemented** | Alternate `--from`/checkpoint content can seed drafting while quality comparison retains the accepted baseline; focused test coverage exists. |
| 5 | **implemented** | Previous reviewer reports and revision plan are included in the next iterative draft prompt. |
| 6 | **implemented** | Reviewer `Underused references` signals are parsed into the next focus set; focused test coverage exists. |
| 7 | **implemented** | Persisted focus history drives fresh-source selection and later rotation; focused test coverage exists. |
| 8 | **partially implemented** | Strategies vary character allocation, but they do not represent semantic evidence-resolution states and “full” may still truncate. |
| 9 | **implemented** | The reviewer list is configurable and the default three-persona workflow runs through the same loop without redesign. |
| 10 | **implemented** | Major pipeline roles independently select model chains/backends, with route metadata and tests. |
| 11 | **implemented** | Ollama and configurable OpenAI-compatible endpoints are first-class model routes, with provider catalog/parser tests. |
| 12 | **implemented** | Heterogeneous input paths enter through the explicit `SmartLoader` adapter and bundled registry rather than direct pipeline reads. |
| 13 | **implemented** | The normalization result carries errors/warnings and PDF/CAJ degradation paths surface fallback/OCR information; broader fidelity coverage remains debt under §4.8. |
| 14 | **partially implemented** | Loaded and discovered artifacts retain meaningful path/query/provider/URL/version provenance, but transformations and verification state are incomplete. |
| 15 | **partially implemented** | Lead-only and anti-fabrication prompts preserve explicit uncertainty, but no persisted verified/candidate boundary enforces it. |

### Principal reproduced limitations

```text
missing_pointer_resolves_to=v2
invalid_pointer_resolves_to=v2
malformed_score_metadata={'provider': 'fake', 'model': 'judge', 'attempts': [], 'verdict': 'same', 'previous_score': 5, 'candidate_score': 5, 'rationale': ''}
```

The first two observations come from `accepted_version()` in an isolated two-version workspace. The third comes from `_score_metadata()` receiving non-JSON output. No production or ignored project was mutated.

## Interpretation

- **CONFIRMED:** Candidate/accepted semantics, a quality gate, reviewer panels, focus rotation, role routes, local endpoints, heterogeneous loading, and research traces all have real implementation rather than documentation-only claims.
- **CONFIRMED:** Accepted-state recovery and score-output validation contain fail-open behavior that conflicts with or weakens explicit specification invariants.
- **CONFIRMED:** Evidence resolution is currently allocation by character slice, not the richer semantic resolution model described by the specification.
- **CONFIRMED:** Search provenance exists, while durable candidate/verified evidence state does not.
- **CONFIRMED:** No provider-independent capability abstraction was found.
- **INFERRED:** The score-validation defect is the smallest implementation slice after governance review because it is reproducible, safety-relevant, locally bounded, and does not require choosing an open §14 architecture.
- **UNKNOWN:** Full existing-workflow compatibility, representative normalization fidelity, real-provider behavior, and satisfaction of §12 completion criteria require later tests and independent review.

## Limitations and residual uncertainty

- This is a recovery audit, not an independent architecture-drift review and not a product-code change.
- Static inspection may miss behavior supplied only by undocumented external provider services or environment-specific tooling; such behavior would still need durable evidence.
- Tests prove covered examples, not all model, reviewer, format, research, or corruption combinations.
- Classification `implemented` means the important mandatory behavior was evidenced at this revision; it does not declare an open design choice settled or §12 complete.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record, supported by immutable implementation revision `387bffe632ba2d53c14aa59de93bd645935d9a94`.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record.
- **External retention risk:** Ignored samples and live providers are not part of this record; source revision and committed evidence are durable.
- **Supersedes / superseded by:** `NONE`

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `NONE` | `agent:codex-recovery` | `NONE` | No correction recorded. |
