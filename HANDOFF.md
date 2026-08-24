# Operational Handoff

Read [`BOOTSTRAP.md`](BOOTSTRAP.md) before using this file. This snapshot is operational continuity below the accepted specification, ADRs, executable contracts/tests, and recorded evidence.

## Current State

### Snapshot

- **Snapshot updated UTC:** `2026-08-24T07:47:00Z`
- **Repository state:** This snapshot belongs to the containing local normalization-evidence commit, expected to be a direct child of published review-closure commit `e68f80656843f8bc82f8bdda0803398a668e21c7` on `main`. The evidence commit is intentionally not authorized for push in this pass; `origin/main` remains at `e68f806`. Its tracked changes are evidence/governance/diagnostic paths only. The only expected dirty entries after commit are four preserved unrelated untracked JavaScript files: `codex-app-server-agent.js`, `codex-feature-definitions.js`, `provider-model.js`, and `provider-registry.js`.
- **Evidence cutoff:** Product implementation/tests at independently approved `391d73e`; score-review governance closure published at `e68f806`; protocol source at `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`; corrected normalization observations and post-commit checks through `2026-08-24T07:47:00Z`.
- **External checks:** At `2026-08-24T07:45:09Z`, after the authorized closure push and before the local evidence commit, `HEAD`, cached `origin/main`, and direct remote `main` all equaled `e68f806` with ahead/behind `0/0`. At `2026-08-24T07:47:00Z`, the containing local commit was confirmed as a direct child of `e68f806`; cached/direct remote remained `e68f806`, so local ahead/behind was intentionally `1/0`. The four preserved untracked digests matched their recovery values, and no TCP listener was present on port `8765` (`lsof` exit `1`). Refresh before relying on remote or service state; no external background task was started.
- **Stale when:** `HEAD` is not the containing direct child of `e68f806`; `origin/main` moves from `e68f806`; branch/upstream or the four-file dirty set differs; product/test paths differ from `e68f806`; newer evidence or authority changes a claim; a background task appears; or higher authority conflicts with this snapshot.
- **CONFIRMED — Authority:** [`PROJECT_SPEC.md`](PROJECT_SPEC.md) v0.1 is `ACCEPTED` product intent. [`ADR-20260824T024051Z-protocol-adoption`](ADR/ADR-20260824T024051Z-protocol-adoption.md) is the accepted collision/adoption decision. Code, README history, ignored workspaces, and the archived handoff are implementation evidence, not requirements.
- **CONFIRMED — Current slice:** The completed slice added a temporary-fixture generator under `EVIDENCE/diagnostics/` and updated evidence/governance records only. It did not modify `PROJECT_SPEC.md`, `asl/`, tests, loader dependencies/dist, generated papers, environments, provider/capability code, or unrelated JavaScript files.
- **CONFIRMED — Reconciliation:** Implemented requirements include reviewer panel §4.3, revision guidance §4.4, focus/rotation §4.5, role-based bindings §4.9, human-directed iteration §4.13, local-first §7, and normalization-layer invariant 12. Capability-aware execution §4.10 is partial. Representative evidence corrects extraction-degradation invariant 13 from implemented to partial; the additive correction is in [reconciliation evidence](EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md) and the [fixture matrix](EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md).
- **CONFIRMED — Critical limitations:** Missing/invalid accepted pointers still resolve to latest; evidence “resolution” remains character slicing; discovered leads lack explicit verified/candidate state; capability tags do not drive execution. Normalization silently degrades controlled image-only PDF, invalid UTF-8/NUL, duplicate-key JSON, ragged CSV, malformed HTML, and directory-ignored TeX/RTF/image cases; DOCX OMML/image loss is warned. Per-document warnings/OCR reach group Markdown but not structured Smart Loader/version metadata. Exact pre-adoption specification bytes/authorship remain independently unrecoverable.
- **CONFIRMED — Verification baseline:** Corrected fixture run at `e68f806` exited `0` with `19` advertised-extension discoveries, `17` loaded, `2` failed, `16` document warnings, and `3` assets; DOC/DOCX/PDF fixture validity checks passed. Final regression checks passed `76` Python tests in `9.69s`, `4` loader tests in `575ms`, loader typecheck, and the sibling protocol validator. Post-commit scope/whitespace checks passed; `30` tracked/task Markdown files contained `180` local links with `0` missing, and HANDOFF retained exactly five ordered sections plus one nonempty Next Action. The durable [fixture evidence](EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md) records hashes, exact commands, the corrected diagnostic attempt, and limitations. `.venv` still historically lacks pytest and was not retried.
- **UNKNOWN — Completion:** Full compatibility and specification §§10–12 completion remain unestablished. Adoption/recovery and score validation are independently approved/closed; normalization/capability coverage remains `INVESTIGATING`, and the two high-severity issues remain owner-gated.

### Constraints

- Preserve the four unrelated untracked JavaScript files, ignored `papers/`, `.env`, and local environments; do not stage or rewrite them.
- Do not treat the old handoff, README claims, local generated projects, or current implementation as product authority.
- The adoption/recovery and score-validation independent-review gates are satisfied. Normalization fixture evidence is complete; no future normalization schema, parser strategy, fidelity threshold, or capability architecture was selected.
- Accepted-pointer recovery remains owner-gated and separate from any evidence or normalization work.

### Unverified complexity

| Cost | Coverage | Residual record |
|---|---|---|
| Governance hierarchy and independent-review gate | Protocol validation, byte/link/structure checks, evidence, and Git history | [Adoption/recovery issue](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) `CLOSED` after fresh independent `APPROVED` |
| Additive score validity/error state | Unit and integration coverage plus persisted `quality_scores.json`/metadata assertions | [Quality-gate validation](ISSUES/ISSUE-20260824T024051Z-quality-gate-validation.md) `CLOSED` after fresh independent `APPROVED`; broader configurable policy remains §14 scope |
| Accepted-state recovery semantics | Isolated reproduction only | [Owner-gated ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) |
| Evidence/normalization/capability contracts | Static recovery, controlled `22`-file fixture generator, raw/Python traces, and narrow existing tests | Focused active issues below; the probe is evidence support, not a product contract, and real-corpus/architecture decisions remain open |

### Background tasks

No `QUEUED` or `RUNNING` background task has a durable reference. No listener was found on port `8765` at the recorded check.

## Active Issues

| Issue | Status | Severity | Owner | Authority | Review | Summary | Evidence or unblock condition |
|---|---|---|---|---|---|---|---|
| [Accepted-baseline ambiguity](ISSUES/ISSUE-20260824T024051Z-accepted-baseline-ambiguity.md) | `BLOCKED` | `HIGH` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Missing/invalid pointer silently resolves to latest | Owner must define recovery behavior in the specification; ADR if architectural |
| [Evidence resolution/provenance](ISSUES/ISSUE-20260824T024051Z-evidence-resolution-provenance.md) | `OPEN` | `HIGH` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Character slicing and prompt warnings do not establish semantic resolution or verification state | Owner direction before persistent boundary design |
| [Normalization/capability coverage](ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md) | `INVESTIGATING` | `MEDIUM` | `human:technical-owner` | `HUMAN` | `INDEPENDENT` | Controlled format/warning matrix is complete; invariant 13 is partial; descriptive capability tags remain unconsumed | Use the matrix for one bounded existing-warning-field fix; owner-gate any new semantic schema/capability architecture |

## Next Action

Create a focused agent-authority/independent-review issue for only the page-marker-only PDF warning gap proven by the [normalization fixture matrix](EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md), then add regression coverage and make the existing PDF loader treat `pdf-parse` output consisting only of `-- n of m --` markers as no extractable text so its existing OCR/image-heavy warning fires. Preserve valid text-PDF behavior and the current output schema; do not combine DOCX assets/equations, unsupported-directory reporting, a normalization redesign, capability negotiation, or either `HIGH` owner-gated issue.

## Recent Activity

### 2026-08-24T07:41:59Z — agent:codex-normalization-evidence — evidence-only normalization investigator

- **Task:** Publish the already-approved score-review closure, reconcile remote refs, then execute only the HANDOFF normalization fixture evidence slice.
- **Context inspected:** Protocol entry and truth hierarchy; accepted specification §§2.5/4.8/6.1/11–12/14; accepted adoption ADR; owning issue and prior recovery/review evidence; all Smart Loader types, registry, loaders, chunking, tests, Python adapter, pipeline persistence, repository history/status, checkpoint, and HANDOFF.
- **Actions performed:** Verified `e68f806` was a governance-only closure with fresh independent `APPROVED`/zero findings, pushed it, and confirmed `HEAD`/cached/direct remote equality. Added a diagnostic-only temporary fixture generator; ran and corrected its instrumentation; recorded the format, structure, provenance, warning, OCR, malformed, and unsupported-input matrix; appended the invariant 13 correction; reconciled this issue/checkpoint/HANDOFF. No subsequent loader change was started.
- **Files modified:** Evidence/governance/diagnostic paths only: one new evidence record, one diagnostic generator, prior reconciliation corrections, the normalization issue, checkpoint, and HANDOFF. No specification behavioral text, `asl/`, tests, dependencies, generated papers, environments, ignored files, or unrelated JavaScript files changed.
- **Findings:** Explicit normalization invariant 12 remains supported. Invariant 13 is partial: some corrupt/fallback/DOCX losses are explicit, while image-only PDF boilerplate, encoding/NUL loss, duplicate JSON keys, ragged CSV, malformed HTML, and directory-ignored formats are silent. Common structural fidelity is format-specific; warnings/OCR reach group Markdown but not structured summary manifests.
- **Verification performed:** Corrected generator exit `0`; generated legacy DOC/DOCX/PDF types and DOCX media/OMML/image-only-PDF properties independently validated; `76` Python tests passed in `9.69s`; `4` loader tests passed in `575ms`; loader typecheck and protocol validator passed. Post-commit diff/scope, ref, digest, port, Markdown-link, HANDOFF-structure, and whitespace checks passed. Exact report/harness hashes and first-run corrections are in the fixture evidence.
- **Issues created or updated:** Normalization/capability coverage `OPEN` → `INVESTIGATING`; no new product issue or ADR created. The two `HIGH` owner-gated issues and capability-execution gap were not entered.
- **Remaining uncertainty:** Owner-corpus thresholds, real CAJ/KDH and non-macOS DOC behavior, OCR confidence/accuracy, large-document section-aware chunks, canonical normalized structure, and capability execution remain unverified/open.
- **Recommended next action:** Perform only the bounded page-marker-only PDF warning slice above; do not begin any adjacent normalization or owner-gated work.

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
