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
- **Updated UTC:** `2026-08-24T02:59:54Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§10–13
- **ADRs:** [`ADR-20260824T024051Z-protocol-adoption`](../ADR/ADR-20260824T024051Z-protocol-adoption.md) (`ACCEPTED`)
- **Evidence:** [`EVIDENCE-20260824T024051Z-repository-recovery`](../EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md), [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md)
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
- **UNKNOWN:** Whether a fresh independent reviewer will find material errors or omissions in the containing commit.

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
| Governance records and an independent-review gate | Preserve authority and recovery context across replaceable participants | Protocol validator, structural checks, evidence records, and Git history | Independent review remains pending in this issue |

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

No review round has been recorded. A fresh participant must inspect the containing commit directly.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Independent review of the containing governance commit is pending.
- Compatibility and initial-completion claims remain uncertain until later refactoring evidence closes the gaps inventoried in the reconciliation record.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Created the first-adoption recovery record after inventorying protocol collisions. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `OPEN` | `INVESTIGATING` | Inspected authority artifacts, Git state/history, implementation, tests, and ignored runtime traces. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `INVESTIGATING` | `IMPLEMENTING` | Began the owner-approved governance-only collision merge and recovery records. |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | `IMPLEMENTING` | `VERIFYING` | Completed the governance records and began final tests, integrity, link, structure, and scope checks. |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | `VERIFYING` | `REVIEW` | Final staged scope, integrity, remote, test, link, and structural checks passed; independent review is now the only adoption gate. |

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
