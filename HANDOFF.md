# Operational Handoff

Read [`BOOTSTRAP.md`](BOOTSTRAP.md) before using this file. This snapshot is operational continuity below the accepted specification, ADRs, executable contracts/tests, and recorded evidence.

## Current State

### Snapshot

- **Snapshot updated UTC:** `2026-08-24T07:10:15Z`
- **Repository state:** This snapshot belongs to the local, unpushed score-validation review-closure commit that is a direct child of `391d73e702bae34ebcdd334d68cdbed27d450fa6` on `main`; `origin/main` is at `391d73e` after the authorized implementation push. After the review-closure commit, the only expected dirty entries are four preserved unrelated untracked JavaScript files: `codex-app-server-agent.js`, `codex-feature-definitions.js`, `provider-model.js`, and `provider-registry.js`.
- **Evidence cutoff:** Product implementation/tests at `391d73e`; governance adoption/review through `ac93c21`; protocol source at `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`; score-validation review observations through `2026-08-24T07:10:15Z`.
- **External checks:** Direct remote `main` matched `origin/main` at `391d73e` at the `2026-08-24T07:10:15Z` review capture; refresh before relying on remote currency. No TCP listener was present on port `8765` at that check; refresh before assuming service state.
- **Stale when:** `HEAD` is not the containing direct child of `391d73e`; `origin/main` moves from `391d73e`; branch/upstream or the four-file dirty set differs; newer evidence or authority changes a claim; a background task appears; or higher authority conflicts with this snapshot.
- **CONFIRMED — Authority:** [`PROJECT_SPEC.md`](PROJECT_SPEC.md) v0.1 is `ACCEPTED` product intent. [`ADR-20260824T024051Z-protocol-adoption`](ADR/ADR-20260824T024051Z-protocol-adoption.md) is the accepted collision/adoption decision. Code, README history, ignored workspaces, and the archived handoff are implementation evidence, not requirements.
- **CONFIRMED — Current slice:** The bounded score-validation implementation changes only `asl/pipeline.py`, focused tests, and governance/evidence records. It does not alter accepted-pointer recovery, the scoring policy/aggregation rule for valid votes, reviewer behavior, provider routing, generated papers, environments, or unrelated JavaScript files.
- **CONFIRMED — Reconciliation:** Implemented requirements include reviewer panel §4.3, revision guidance §4.4, focus/rotation §4.5, role-based bindings §4.9, human-directed iteration §4.13, and local-first §7. Capability-aware execution §4.10 is partial: descriptive preset/catalog capability metadata exists, but stages and execution do not consume it. Additive corrections are in the [reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md) and [independent review](EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md).
- **CONFIRMED — Critical limitations:** Missing/invalid accepted pointers still resolve to latest; evidence “resolution” remains character slicing; discovered leads lack explicit verified/candidate state; capability tags do not drive execution. Score output now fails closed for malformed, incomplete, schema-invalid, and fallback results, and the containing implementation commit `391d73e` received fresh independent `APPROVED`. Exact pre-adoption untracked specification bytes/authorship cannot be independently reconstructed, although the current accepted specification and ADR remain authority.
- **CONFIRMED — Verification baseline:** The fresh review rerun passed `76` Python tests in `10.25s`; `4` bundled smart-loader tests passed in `401ms`, loader typecheck passed, and the sibling protocol validator passed. Eleven independent edge probes all failed closed, and an independent end-to-end run confirmed a valid `better` vote still accepts and advances the pointer with identical `quality_scores.json`/`metadata.json` gate records. `.venv` still lacks pytest. Exact commands, probes, and limitations are in [score-validation review evidence](EVIDENCE/EVIDENCE-20260824T071015Z-score-validation-review.md).
- **UNKNOWN — Completion:** Full compatibility and specification §§10–12 completion are not established. Adoption/recovery and the score-validation slice are independently approved and closed; the remaining focused issues are unchanged.

### Constraints

- Preserve the four unrelated untracked JavaScript files, ignored `papers/`, `.env`, and local environments; do not stage or rewrite them.
- Do not treat the old handoff, README claims, local generated projects, or current implementation as product authority.
- The adoption/recovery and score-validation independent-review gates are both satisfied; the remaining slices are owner-gated decisions or evidence gathering.
- Accepted-pointer recovery remains owner-gated and separate from any evidence or normalization work.

### Unverified complexity

| Cost | Coverage | Residual record |
|---|---|---|
| Governance hierarchy and independent-review gate | Protocol validation, byte/link/structure checks, evidence, and Git history | [Adoption/recovery issue](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) `CLOSED` after fresh independent `APPROVED` |
| Additive score validity/error state | Unit and integration coverage plus persisted `quality_scores.json`/metadata assertions | [Quality-gate validation](ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md) `CLOSED` after fresh independent `APPROVED`; broader configurable policy remains §14 scope |
| Accepted-state recovery semantics | Isolated reproduction only | [Owner-gated ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) |
| Evidence/normalization/capability contracts | Static recovery and narrow existing tests | Focused active issues below; reviewer schema/persona routing is optional future §14 scope, not an active required gap |

### Background tasks

No `QUEUED` or `RUNNING` background task has a durable reference. No listener was found on port `8765` at the recorded check.

## Active Issues

| Issue | Status | Severity | Owner | Authority | Review | Summary | Evidence or unblock condition |
|---|---|---|---|---|---|---|---|
| [Accepted-baseline ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) | `BLOCKED` | `HIGH` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Missing/invalid pointer silently resolves to latest | Owner must define recovery behavior in the specification; ADR if architectural |
| [Evidence resolution/provenance](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) | `OPEN` | `HIGH` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Character slicing and prompt warnings do not establish semantic resolution or verification state | Owner direction before persistent boundary design |
| [Normalization/capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) | `OPEN` | `MEDIUM` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Loader fidelity coverage is narrow; descriptive capability tags exist but execution does not consume them | Gather fixtures first; owner-gate later architecture |

## Next Action

Gather representative format fixtures and warning/fidelity evidence for [normalization/capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md): build a fixture matrix across the advertised loader formats, record which structures and warnings survive each, and store the results as evidence only — no loader contract change, new dependency, or capability-negotiation architecture. The two `HIGH` issues remain owner-gated decisions in [`HUMAN_CHECKPOINT.md`](HUMAN_CHECKPOINT.md); do not start accepted-pointer recovery.

## Recent Activity

### 2026-08-24T07:10:15Z — agent:claude-code-independent-review — fresh independent reviewer

- **Task:** Perform the fresh independent review of score-validation commit `391d73e` and record one disposition on the quality-gate issue.
- **Context inspected:** Accepted specification §§2.1/4.2/8/11/12, the quality-gate issue, implementation evidence, checkpoint, handoff, the complete `ac93c21..391d73e` diff, all score-record producers/consumers (gate, parser, persistence, renderer, UI, prompt), Git refs/remotes (refreshed), and the preserved dirty set.
- **Actions performed:** Recorded one complete review round with disposition `APPROVED` and zero open material findings; closed the quality-gate issue; reconciled the checkpoint and this handoff. No accepted-pointer or later refactoring work was started.
- **Files modified:** Governance/recovery paths only: one new evidence record, the quality-gate issue, `HUMAN_CHECKPOINT.md`, and this handoff. No product code, tests, specification wording, generated papers, environments, or unrelated JavaScript files were modified.
- **Findings:** The slice is contained and correct: strict four-field validation fails closed on every probed edge case; fallback results are ineligible; valid-vote aggregation and verdict normalization are unchanged; no-valid-vote gates reject and preserve the accepted pointer; gate records persist identically in `quality_scores.json` and `metadata.json`; zero existing test lines were removed. Non-material observations only (unreachable non-dict guard; unstripped verdict whitespace rejected conservatively).
- **Verification performed:** Recorded in [score-validation review evidence](EVIDENCE/EVIDENCE-20260824T071015Z-score-validation-review.md): `76` Python tests, `4` loader tests plus typecheck, protocol validator, eleven independent edge probes, an independent positive-path pipeline run, structure/link checks, refreshed remote/digest/port checks; `.venv` pytest remains unavailable.
- **Issues created or updated:** Quality-gate validation `REVIEW` → `CLOSED`. The three remaining focused issues are unchanged.
- **Remaining uncertainty:** §§10–12 completion remains `UNKNOWN`; live-provider behavior unverified; legacy score records are not migrated (declared out of scope); two owner decisions remain pending.
- **Recommended next action:** The normalization fixture-gathering evidence slice described above; do not start accepted-pointer recovery.

### 2026-08-24T06:55:10Z — agent:codex-score-validation — bounded-slice implementor

- **Task:** Make malformed, missing, schema-invalid, and fallback scorer output fail closed without changing accepted-pointer or valid-vote policy.
- **Context inspected:** Accepted specification §§2.1/4.2/8/11/12, adoption ADR/reviews, quality-gate issue and reconciliation evidence, current HANDOFF, score prompt, parser/aggregation/persistence paths, existing quality tests, Git/remotes/dirty state.
- **Actions performed:** Added strict four-field score validation, explicit `valid`/`validation_errors` persistence, invalid/fallback exclusion, no-valid-vote rejection, and focused unit/integration tests. Created reusable implementation evidence and moved the issue toward independent review.
- **Files modified:** `asl/pipeline.py`, `tests/test_pipeline.py`, quality-gate issue, score-validation evidence, checkpoint, and this handoff. Accepted-pointer code, specification wording, other product subsystems, ignored artifacts, and unrelated untracked files were not modified.
- **Findings:** **CONFIRMED** all six pre-change invalid/fallback cases produced eligible-looking metadata. **CONFIRMED** after the change each is ineligible with attributable errors; mixed invalid/fallback favorable votes cannot offset a valid `worse` vote; valid score behavior is preserved.
- **Verification performed:** Targeted `11 passed`; final full Python `76 passed in 7.80s`; bundled loader `4 passed in 511ms`; loader typecheck and sibling protocol validator passed. `.venv` pytest remains unavailable; one corrected test-assertion failure is recorded in evidence.
- **Issues created or updated:** [Quality-gate validation](ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md) moved `OPEN` → `INVESTIGATING` → `IMPLEMENTING` → `VERIFYING` → `REVIEW`; no independent round has yet been recorded.
- **Remaining uncertainty:** Independent review is pending; configurable scoring policy remains open §14 scope; accepted-pointer recovery remains owner-gated.
- **Recommended next action:** Perform only the independent review specified above.

### 2026-08-24T06:25:44Z — agent:claude-code-independent-review — fresh independent reviewer

- **Task:** Perform the fresh independent review of the containing governance-repair commit `113b8b0` and record one disposition on the adoption/recovery issue.
- **Context inspected:** [`BOOTSTRAP.md`](BOOTSTRAP.md), accepted specification and adoption ADR, all three prior evidence records, all six issue records, checkpoint, handoff, the full adoption and repair diffs, Git history/refs/remotes (refreshed), and the product code behind the corrected classifications.
- **Actions performed:** Recorded one complete review round with disposition `APPROVED` and zero open material findings; verified all three `R1`–`R3` resolution conditions resolved; closed the adoption/recovery issue; appended an ADR review clarification; reconciled the checkpoint and this handoff. No product/refactoring work was started.
- **Files modified:** Governance/recovery paths only: one new evidence record, the adoption issue, the adoption ADR clarification, `HUMAN_CHECKPOINT.md`, and this handoff. No `PROJECT_SPEC.md` behavioral wording, `asl/`, tests, generated papers, environments, or unrelated JavaScript files were modified.
- **Findings:** The repair is governance-only and within existing authority; historical-state preservation, byte integrity, remotes, digests, executable baseline, and record consistency all verified. No material findings.
- **Verification performed:** Recorded in [fresh review evidence](EVIDENCE/EVIDENCE-20260824T062544Z-fresh-independent-review.md): `66` Python tests, `4` loader tests plus typecheck, protocol validator, seven `cmp` mappings, legacy/untracked digests, structure/link checks, refreshed remote and port `8765` checks, and direct code traces; `.venv` pytest remains unavailable.
- **Issues created or updated:** Adoption/recovery `REVIEW` → `CLOSED`. The four focused issues are unchanged.
- **Remaining uncertainty:** §§10–12 completion remains `UNKNOWN`; exact pre-adoption specification bytes remain unrecoverable; live-provider and corpus behavior unverified.
- **Recommended next action:** The bounded fail-closed score-validation slice described above; do not fold accepted-pointer recovery into it.

### 2026-08-24T03:46:47Z — agent:codex-governance-review — independent reviewer and governance-repair implementor

- **Task:** Independently assess candidate baseline `e9ef291`, record its disposition, and repair only authorized governance/recovery artifacts.
- **Context inspected:** Accepted specification and ADR, sibling protocol at `58fa281`, the entire adoption diff, evidence/issues/checkpoint/handoff, relevant prompts/routes/pipeline/tests, Git history/objects/remotes, ignored workspace metadata, and the preserved dirty set.
- **Actions performed:** Recorded `CHANGES_REQUIRED` with three material findings; corrected §4.4 to implemented and §4.10 to partial; qualified unreproducible pre-adoption provenance; closed reviewer-routing/guidance as no current required gap; reconciled current-state records. No product scope or §14 architecture was selected.
- **Files modified:** Governance/recovery paths only. `PROJECT_SPEC.md` behavioral wording, runtime/product code, tests, generated papers, environments, and the four unrelated untracked JavaScript files were not modified.
- **Findings:** Protocol adoption, tracked legacy preservation, and dirty-state preservation were sound. The baseline underclassified review guidance, omitted descriptive capability metadata, and overstated independent historical provenance.
- **Verification performed:** Full repair verification is recorded in the [adoption/recovery issue](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) and [independent review evidence](EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md), including explicit unavailable/corrected invocations.
- **Issues created or updated:** Adoption/recovery remains `REVIEW`; reviewer routing/guidance is `CLOSED`; normalization/capability coverage is corrected and remains `OPEN`.
- **Remaining uncertainty:** The same participant reviewed `e9ef291` and applied its governance corrections, so the repair commit is not independently approved. Exact original untracked specification bytes/authorship remain unrecoverable.
- **Recommended next action:** Perform the single fresh independent re-review described above; do not start score validation.

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

The pre-protocol handoff is preserved immutably at Git object `387bffe:HANDOFF.md` with SHA-256 `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`. It described a long implementation history including versioned drafting, quality gating, reviewer iteration, reference focus/rotation, smart-loader integration, role/provider routes, research stages, UI work, and CAJ/RTF support. Verified behavior was carried into [recovery evidence](EVIDENCE/EVIDENCE-20260824T024051Z-repository-recovery.md) and [reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md); unverified claims and implementation choices were not converted into product requirements. The review-routing/guidance issue was later closed because current mandatory behavior is implemented; richer schemas and persona routes remain optional future §14 scope. The adoption/recovery issue closed at `2026-08-24T06:25:44Z` after a fresh independent `APPROVED` of repair commit `113b8b0` resolved the first round's three findings. The quality-gate validation issue closed at `2026-08-24T07:10:15Z` after a fresh independent `APPROVED` of implementation commit `391d73e`. Git history remains the source for detailed historical commits.
