# ISSUE-20260824T024051Z: Adopt Protocol and Recover the Repository Baseline

## Metadata

- **ID:** `ISSUE-20260824T024051Z-protocol-adoption-recovery`
- **Title:** Adopt the protocol and recover a trustworthy repository baseline
- **Status:** `REVIEW`
- **Severity:** `HIGH`
- **Owner:** `agent:codex-recovery`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-24T03:46:47Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§10–13
- **ADRs:** [`ADR-20260824T024051Z-protocol-adoption`](../ADR/ADR-20260824T024051Z-protocol-adoption.md) (`ACCEPTED`)
- **Evidence:** [`EVIDENCE-20260824T024051Z-repository-recovery`](../EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md), [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md), [`EVIDENCE-20260824T033159Z-governance-independent-review`](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md)
- **Milestone:** `NONE`

## Problem

The application predates both the accepted owner specification and the engineering protocol. Its tracked README, legacy handoff, implementation, tests, and ignored runtime artifacts contain useful implementation history, but they do not establish intended behavior. Without an adopted authority hierarchy, durable recovery evidence, and an explicit reconciliation, a later refactor could mistake accidental behavior or old claims for requirements.

## Evidence or reproduction

The target `main`, `origin/main`, and direct remote `main` resolved to `387bffe632ba2d53c14aa59de93bd645935d9a94` before adoption. The clean, remote-current sibling protocol source resolved to `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`. The recovery evidence inventories the dirty tree, implementation behavior, tests, ignored traces, unavailable checks, and copied-artifact integrity. The reconciliation evidence compares the implementation with every material §4 requirement and all fifteen §11 invariants.

## Expected behavior

The repository follows [`BOOTSTRAP.md`](../BOOTSTRAP.md), retains the accepted owner specification as product authority, records conflicts rather than resolving them by inference, and exposes a compact current-state handoff with exactly one next action. This pass changes governance and documentation only and leaves product behavior untouched.

## Assumptions

- **CONFIRMED:** `human:technical-owner` accepted v0.1 without behavioral edits, approved the collision mapping, and authorized one local unpushed governance commit.
- **CONFIRMED:** Existing implementation, tests, README statements, the legacy handoff, and generated paper workspaces are evidence below the accepted specification in the adopted truth hierarchy.
- **INFERRED:** A byte-verified canonical installation plus explicit project-owned merges is the least ambiguous recovery boundary.
- **CONFIRMED:** The accepted specification and adoption ADR remain current repository authority; repository participant/owner labels are attributable records, not authenticated identities.
- **UNKNOWN:** The exact bytes and authorship of the untracked pre-adoption specification cannot be independently reconstructed from repository evidence.
- **UNKNOWN:** Whether a fresh independent reviewer will approve the containing governance-repair commit.

## Investigation and decision

The accepted adoption ADR owns the collision mapping and source revisions. The old handoff is preserved by immutable Git object and digest, while only verified facts are carried forward. Material discrepancies are split into focused issues so no implementation note silently becomes a new requirement. No open design decision in specification §14 is resolved here.

## Change

- **Files or components:** Root protocol/navigation/specification/handoff/checkpoint documents and records under `ADR/`, `EVIDENCE/`, and `ISSUES/`.
- **Behavior changed:** Repository governance changes from undocumented legacy practice to the accepted protocol hierarchy; application runtime behavior does not change.
- **Out-of-scope work deliberately excluded:** All files under `asl/`, executable tests, generated `papers/`, `.env`, local environments, provider contracts, persistence formats, and the four unrelated untracked JavaScript files.
- **Rollback or recovery:** Revert the containing governance commit. The legacy handoff remains recoverable at `387bffe:HANDOFF.md` with SHA-256 `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Governance records and an independent-review gate | Preserve authority and recovery context across replaceable participants | Protocol validator, structural checks, evidence records, and Git history | First review returned `CHANGES_REQUIRED`; fresh review of the containing repair remains pending |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_protocol.py` in the protocol source | `PASS structural protocol validation (package_files=10 handoffs=2)`; exit `0` | Recovery evidence | Validates the reusable source, not the merged target |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `.venv/bin/python -m pytest -q -p no:cacheprovider` | Failed: `No module named pytest`; nonzero exit | Recovery evidence | Repository virtual environment cannot run the suite |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | `66 passed in 8.33s`; exit `0` | Recovery evidence | Uses system Python rather than `.venv` |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm test -- --runInBand` in `asl/_vendor/smart-loader` | Failed: Vitest `Unknown option --runInBand`; nonzero exit | Recovery evidence | Unsupported invocation; not a test failure |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm test` in `asl/_vendor/smart-loader` | One file and four tests passed; exit `0` | Recovery evidence | Bundled loader suite is small |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm run typecheck` in `asl/_vendor/smart-loader` | Passed; exit `0` | Recovery evidence | Static typecheck only |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | `66 passed in 7.48s`; exit `0` | Final recovery-pass rerun | Uses system Python rather than `.venv` |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | `npm test` then `npm run typecheck` in `asl/_vendor/smart-loader` | One file/four tests passed in `491ms`; typecheck passed; exit `0` | Final recovery-pass rerun | Small loader suite; no corpus-fidelity claim |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_protocol.py` in source | `PASS structural protocol validation (package_files=10 handoffs=2)`; exit `0` | Protocol source at `58fa281` | Source-package validation only |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | Seven explicit `cmp` calls plus target manifest/regular-file/symlink checks | Passed; exit `0` | Approved source-to-target mapping | Project-owned merged artifacts intentionally differ from templates |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | Protocol Markdown/link checker over target files plus HANDOFF structure check | `PASS target Markdown/link/HANDOFF validation (files=25)`; exit `0` | Target governance/application Markdown | Checks local targets and structure, not semantic correctness |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | `git diff --cached --check`, explicit staged-path set comparison, `git diff --quiet`, and product/test path comparison | Passed: `20` approved governance paths, zero staged product/test paths, zero unstaged tracked changes; exit `0` | Staged review target | Independent semantic review remains pending |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | Inverse-transform SHA-256 checks for owner specification and application README; `git show 387bffe:HANDOFF.md` digest check | All matched recorded pre-adoption digests; exit `0` | Original digests in recovery evidence | Proves scoped byte preservation, not requirement correctness |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | Direct `git ls-remote` checks for target and protocol `main` | Target remained `387bffe`; protocol remained `58fa281`; exit `0` | Timestamped external check | Remote refs can move after capture |
| `2026-08-24T03:44:24Z` | `agent:codex-governance-review` | System-Python suite; `.venv` invocation; loader tests and typecheck | System Python: `66 passed in 7.55s`; loader: one file/four tests in `376ms`; typecheck passed; `.venv` unavailable with `No module named pytest` | Independent review evidence, Governance repair verification | System Python substitutes for the incomplete repository environment; loader suite remains small |
| `2026-08-24T03:44:24Z` | `agent:codex-governance-review` | Sibling validator, seven immutable `cmp` calls, target Markdown/link/HANDOFF checker, and regular-file/symlink boundary | Validator passed; all mappings matched; `25` Markdown files/`145` local links/zero missing; five ordered HANDOFF sections; nine-path governance allowlist passed; exit `0` | Independent review evidence, Governance repair verification | Project-owned merge artifacts intentionally differ from templates |
| `2026-08-24T03:44:24Z` | `agent:codex-governance-review` | Direct remote checks, legacy/README/untracked digests, ignored-paper sampling, and all-Git-blob provenance search | Refs/digests reproduced; `5` projects/`16` versions/`5` valid pointers/`3` later candidates; parent lacks the specification and none of `439` blobs matches its recorded pre-adoption SHA-256; exit `0` | Independent review evidence, Governance repair verification | Remotes and ignored files are timestamped; missing historical bytes remain unrecoverable |
| `2026-08-24T03:44:24Z` | `agent:codex-governance-review` | Pointer/score reproduction plus capability-payload and reviewer-guidance traces | Reproduced pointer fallback and malformed `same`/`5`/`5`; `35` models exposed capability lists while execution types did not consume them; structured review/revision/next-iteration traces passed; exit `0` | Independent review evidence, Governance repair verification | Static/isolated checks; no live model/provider call |
| `2026-08-24T03:44:24Z` | `agent:codex-governance-review` | `git diff --check`, explicit repair-path allowlist, forbidden-path comparison, and `lsof` listener observation | Diff/scope checks passed with exactly nine governance paths and zero product/test/specification paths; all four untracked hashes remained; no `8765` listener (`lsof` exit `1`) | Independent review evidence, Governance repair verification | Listener absence is timestamped; final staged/committed status checked separately |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-recovery`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** Accepted adoption ADR and owner-approved pass scope
- **Checks and evidence reviewed:** Preparatory inspection and verification are recorded above
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** Self-review cannot satisfy the required independent gate
- **Residual risks:** Recovery omissions or authority mistakes may remain
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — the pass changes source precedence, governance architecture, and the durable recovery baseline.

### 2026-08-24T03:31:59Z — agent:codex-governance-review

- **Reviewed repository state:** Candidate governance baseline `e9ef291a0be124a1ea1ad782c6bb307a486f2b18`, direct parent `387bffe632ba2d53c14aa59de93bd645935d9a94`, with exactly four preserved unrelated untracked JavaScript files; sibling protocol `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`.
- **Reviewed target:** `e9ef291a0be124a1ea1ad782c6bb307a486f2b18`
- **Open material findings:** `3`
- **Scope:** Protocol adoption integrity, source/target provenance, recovery observations, tracked and untracked historical preservation, accepted-specification requirement classifications, issue escalation/authority, ADR/checkpoint/handoff consistency, executable tests, diagnostics, and dirty-state preservation.
- **Commands or procedures:** Read the immutable sibling protocol and accepted specification; inspected the full parent-to-target diff and every changed path; ran protocol validation, seven explicit byte comparisons, target link/HANDOFF and regular-file/symlink checks, Python/loader tests and typecheck, remote and digest checks, ignored-workspace sampling, Git-object search, pointer/score diagnostics, capability payload inspection, reviewer-guidance data-flow tracing, and scope/status checks. Exact commands and corrected invocations are recorded in the linked evidence.
- **Specification compliance:** Protocol installation and tracked recovery are sound. §4.4 is implemented, not partial; §4.10 is partial, not absent. Current accepted specification authority is sound, but exact pre-adoption bytes/authorship are not independently reproducible.
- **Correctness and regression findings:** No product/runtime regression or unauthorized product/test change was found. Three governance statements materially misclassified or overclaimed repository evidence.
- **Architecture and complexity findings:** The baseline unnecessarily escalated optional reviewer schemas/persona routes as a required owner decision and missed reusable descriptive capability metadata. Both can be corrected without selecting new architecture.
- **Material findings and resolution conditions:** `R1 MEDIUM` — correct §4.4 to implemented, close reviewer-routing/guidance as no current required gap, and remove it from active/owner queues; `R2 MEDIUM` — correct §4.10 to partially implemented and distinguish preset/catalog metadata from missing execution negotiation; `R3 MEDIUM` — retain accepted authority but qualify exact pre-adoption bytes/authorship as implementor-recorded and independently unreproducible. All three conditions must be recorded additively in governance/recovery artifacts.
- **Limitations:** Participant identity is not authenticated; no live provider/research/UI/corpus/external-workspace validation ran; the missing pre-adoption untracked bytes cannot be recovered by review.
- **Residual risks:** The repair commit will require a fresh participant because this reviewer is also applying the governance corrections; §§10–12 completion and focused product gaps remain open.
- **Evidence:** [`EVIDENCE-20260824T033159Z-governance-independent-review`](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md)
- **Disposition:** `CHANGES_REQUIRED`
- **Prior-round resolution:** `FIRST ROUND`

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- The candidate `e9ef291` review returned `CHANGES_REQUIRED`; a fresh independent participant must review the containing governance-repair commit and confirm all three findings are resolved.
- Exact pre-adoption specification bytes/authorship remain implementor-recorded provenance and cannot be independently reconstructed from repository evidence; current accepted authority is unaffected.
- Compatibility and initial-completion claims remain uncertain until later refactoring evidence closes the gaps inventoried in the reconciliation record.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Created the first-adoption recovery record after inventorying protocol collisions. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `OPEN` | `INVESTIGATING` | Inspected authority artifacts, Git state/history, implementation, tests, and ignored runtime traces. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `INVESTIGATING` | `IMPLEMENTING` | Began the owner-approved governance-only collision merge and recovery records. |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | `IMPLEMENTING` | `VERIFYING` | Completed the governance records and began final tests, integrity, link, structure, and scope checks. |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | `VERIFYING` | `REVIEW` | Final staged scope, integrity, remote, test, link, and structural checks passed; independent review is now the only adoption gate. |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | `REVIEW` | `IMPLEMENTING` | Independent review of immutable target `e9ef291` recorded `CHANGES_REQUIRED` with three material governance findings; began the authorized governance/recovery-only corrections. |
| `2026-08-24T03:37:13Z` | `agent:codex-governance-review` | `IMPLEMENTING` | `VERIFYING` | Completed additive evidence, classification, issue, ADR, checkpoint, and handoff corrections; began the approved full verification matrix. |
| `2026-08-24T03:46:47Z` | `agent:codex-governance-review` | `VERIFYING` | `REVIEW` | Full executable, structural, source-integrity, history/provenance, diagnostic, remote, dirty-state, and governance-scope checks passed or reproduced their explicitly recorded unavailable observation; fresh independent review is the only adoption gate. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [x] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [x] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [x] HANDOFF reflects the resulting current state and exactly one next action.
