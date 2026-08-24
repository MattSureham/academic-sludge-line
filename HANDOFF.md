# Operational Handoff

Read [`BOOTSTRAP.md`](BOOTSTRAP.md) before using this file. This snapshot is operational continuity below the accepted specification, ADRs, executable contracts/tests, and recorded evidence.

## Current State

### Snapshot

- **Snapshot updated UTC:** `2026-08-24T02:59:54Z`
- **Repository state:** This snapshot belongs to the local, unpushed governance commit that is a direct child of `387bffe632ba2d53c14aa59de93bd645935d9a94` on `main`; `origin/main` remains at `387bffe`. After that commit, the only expected dirty entries are four preserved unrelated untracked JavaScript files: `codex-app-server-agent.js`, `codex-feature-definitions.js`, `provider-model.js`, and `provider-registry.js`.
- **Evidence cutoff:** Product implementation/tests at `387bffe`; protocol source at `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`; recovery observations captured from `2026-08-24T02:40:51Z` through `2026-08-24T02:59:54Z`.
- **External checks:** Direct remote `main` refs for both repositories matched their local remote-tracking refs at `2026-08-24T02:59:54Z`; refresh before relying on remote currency. No TCP listener was present on port `8765` at the earlier recovery check; refresh before assuming service state.
- **Stale when:** `HEAD` is not the containing direct child of `387bffe`; branch/upstream or the four-file dirty set differs; either recorded remote ref moves; newer evidence or authority changes a claim; a background task appears; or higher authority conflicts with this snapshot.
- **CONFIRMED — Authority:** [`PROJECT_SPEC.md`](PROJECT_SPEC.md) v0.1 is `ACCEPTED` product intent. [`ADR-20260824T024051Z-protocol-adoption`](ADR/ADR-20260824T024051Z-protocol-adoption.md) is the accepted collision/adoption decision. Code, README history, ignored workspaces, and the archived handoff are implementation evidence, not requirements.
- **CONFIRMED — Adoption scope:** Protocol entry/navigation/templates, governance records, the specification acceptance metadata, checkpoint, and this handoff are the only intended changes. No `asl/` or test behavior is authorized or changed.
- **CONFIRMED — Reconciliation:** Implemented requirements are reviewer panel §4.3, focus/rotation §4.5, role-based bindings §4.9, human-directed iteration §4.13, and local-first §7. Partial, absent, and unknown classifications are in the [reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md).
- **CONFIRMED — Critical limitations:** Missing/invalid accepted pointers resolve to latest; malformed scorer output becomes `same` with scores `5`/`5`; evidence “resolution” is character slicing; discovered leads lack explicit verified/candidate state; general capability-aware execution is absent.
- **CONFIRMED — Verification baseline:** Final reruns passed `66` Python tests in `7.48s`, `4` bundled smart-loader tests in `491ms`, and loader typecheck. The protocol source validator, seven byte comparisons, target manifest/symlink checks, and target Markdown/link/HANDOFF validation also passed. `.venv` lacks pytest; corrected failed invocations are preserved in [recovery evidence](EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md).
- **UNKNOWN — Completion:** Full compatibility and specification §§10–12 completion are not established. Independent review of the containing governance commit is pending.

### Constraints

- Preserve the four unrelated untracked JavaScript files, ignored `papers/`, `.env`, and local environments; do not stage or rewrite them.
- Do not treat the old handoff, README claims, local generated projects, or current implementation as product authority.
- Do not start the post-review refactor until a fresh independent participant records `APPROVED` on the adoption issue with no unresolved material finding.
- Accepted-pointer recovery remains owner-gated and separate from score validation.

### Unverified complexity

| Cost | Coverage | Residual record |
|---|---|---|
| Governance hierarchy and independent-review gate | Protocol validation, byte/link/structure checks, evidence, and Git history | [Adoption/recovery issue](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) in `REVIEW` after verification |
| Accepted-state recovery semantics | Isolated reproduction only | [Owner-gated ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) |
| Reviewer/evidence/normalization/capability contracts | Static recovery and narrow existing tests | Focused active issues below |

### Background tasks

No `QUEUED` or `RUNNING` background task has a durable reference. No listener was found on port `8765` at the recorded check.

## Active Issues

| Issue | Status | Severity | Owner | Authority | Review | Summary | Evidence or unblock condition |
|---|---|---|---|---|---|---|---|
| [Protocol adoption/recovery](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) | `REVIEW` | `HIGH` | `agent:codex-recovery` | `HUMAN` | `INDEPENDENT` | Governance baseline verified; adoption remains open | Fresh independent review of containing commit |
| [Accepted-baseline ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) | `BLOCKED` | `HIGH` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Missing/invalid pointer silently resolves to latest | Owner must define recovery behavior in the specification; ADR if architectural |
| [Quality-gate validation](ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md) | `OPEN` | `HIGH` | `agent:unassigned` | `AGENT` | `INDEPENDENT` | Malformed score output can count as an accepting vote | First bounded post-review implementation slice |
| [Reviewer routing/guidance](ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md) | `OPEN` | `MEDIUM` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Reviewer personas share one route and guidance is mostly unstructured prose | Owner direction before contract changes |
| [Evidence resolution/provenance](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) | `OPEN` | `HIGH` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Character slicing and prompt warnings do not establish semantic resolution or verification state | Owner direction before persistent boundary design |
| [Normalization/capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) | `OPEN` | `MEDIUM` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Loader fidelity coverage is narrow; capability-aware execution is absent | Gather fixtures first; owner-gate later architecture |

## Next Action

A fresh independent participant must inspect the containing governance commit against [`BOOTSTRAP.md`](BOOTSTRAP.md), the accepted [adoption ADR](ADR/ADR-20260824T024051Z-protocol-adoption.md), and both evidence records, rerun proportionate structural checks, then append one complete review round with exactly one disposition to the [adoption/recovery issue](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md); do not begin the score-validation refactor during that review.

## Recent Activity

### 2026-08-24T02:59:54Z — agent:codex-recovery — first-adoption implementor

- **Task:** Adopt the sibling protocol and recover a trustworthy governance/current-state baseline without changing product behavior.
- **Context inspected:** Protocol source/remote, accepted owner specification, README/docs, tracked legacy handoff, Git history/status/ignore rules, relevant implementation/tests, and read-only ignored workspace metadata.
- **Actions performed:** Installed byte-identical reusable artifacts under the owner-approved mapping; added specification acceptance metadata; recorded an accepted ADR, six active issues, two evidence records, this checkpoint, and the five-section handoff.
- **Files modified:** Governance/documentation paths only; see the containing commit. Product code, tests, ignored artifacts, secrets, and four unrelated untracked JavaScript files were not modified.
- **Findings:** **CONFIRMED** classifications and reproduced limitations are in [spec reconciliation](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md). **UNKNOWN** full compatibility and initial completion remain open.
- **Verification performed:** `66` Python tests, `4` bundled loader tests, loader typecheck, protocol source validation, seven byte comparisons, target manifest/symlink/link/HANDOFF checks, staged-diff/scope checks, original-byte reconstruction, and direct remote checks passed. Corrected failed invocations are recorded in recovery evidence.
- **Issues created or updated:** All six records indexed above.
- **Remaining uncertainty:** Independent review is pending; accepted-pointer policy and later architecture contracts remain owner-gated.
- **Recommended next action:** Perform the single independent review described above.

## Archived Summary

The pre-protocol handoff is preserved immutably at Git object `387bffe:HANDOFF.md` with SHA-256 `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`. It described a long implementation history including versioned drafting, quality gating, reviewer iteration, reference focus/rotation, smart-loader integration, role/provider routes, research stages, UI work, and CAJ/RTF support. Verified behavior was carried into [recovery evidence](EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md) and [reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md); unverified claims and implementation choices were not converted into product requirements. Git history remains the source for detailed historical commits.
