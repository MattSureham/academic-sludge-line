# ISSUE-20260826T032834Z: Report Unsupported Files Encountered During Directory Loading

## Metadata

- **ID:** `ISSUE-20260826T032834Z-directory-unsupported-reporting`
- **Title:** Report unsupported files encountered during directory loading
- **Status:** `REVIEW`
- **Severity:** `MEDIUM`
- **Owner:** `agent:codex-directory-unsupported-reporting`
- **Authority:** `AGENT`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-26T03:28:34Z`
- **Updated UTC:** `2026-08-26T03:45:51Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariants 12–13, and §12
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](../EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md) and [`EVIDENCE-20260826T033558Z-directory-unsupported-reporting`](../EVIDENCE/EVIDENCE-20260826T033558Z-directory-unsupported-reporting.md)
- **Milestone:** `NONE`

## Problem

Directory loading enumerates non-ignored files and then silently filters out every extension absent from the loader registry. Supplied TeX, RTF, image, extensionless, or other unsupported files therefore do not appear in documents, errors, or summary counts, so downstream consumers cannot tell that material was skipped.

## Evidence or reproduction

At published baseline `a763528d2c26509a7dcd9cdf4d37a1e6698187bc`, a controlled directory containing `supported.md`, `unsupported.tex`, `unsupported.rtf`, and `figure.png` returns one discovered/loaded file, zero skipped/failed files, no errors, and only the supported document/chunk. The Python adapter likewise renders the supported marker but no unsupported filename or reason. Loading `unsupported.tex` directly returns one `load_failed` error with `Unsupported file extension: .tex`, establishing that direct-path and directory semantics differ. The published `22`-fixture matrix independently records the same silent directory omission for TeX, RTF, and PNG.

## Expected behavior

Under accepted §§2.5 and 4.8 and invariant 13, every non-ignored regular file enumerated inside a supplied directory MUST be attributable as either supported input or an explicit unsupported/skipped diagnostic. Unsupported entries MUST identify their source path and reason through the existing result contract, increment discovered/skipped counts, and MUST NOT prevent valid supported files from loading or count as failed files. Existing direct-file failure behavior, supported-file output, ignore policy, and result schema MUST remain compatible.

## Assumptions

- **CONFIRMED:** `fast-glob` already enumerates candidate regular files before `scanDirectory()` filters by `EXTENSION_TO_FORMAT`; no directory-traversal redesign is required.
- **CONFIRMED:** `LoadResult` already contains `errors` plus `discoveredFiles`, `skippedFiles`, and `failedFiles`; no new result field or dependency is required.
- **CONFIRMED:** The Python adapter already retains result errors in `LoadedInputGroup.errors`/metadata and renders each error's source path and reason into group Markdown.
- **INFERRED:** A distinct `unsupported_file` code in the existing error list, combined with separate skipped/failed counters, is the smallest attributable diagnostic compatible with the current contract.
- **INFERRED:** `--fail-on-error` should continue to mean actual load failure, so it should use `summary.failedFiles` after skipped diagnostics begin sharing the error list. This is equivalent to the current condition for all pre-change results because every current error is counted as failed.
- **UNKNOWN:** Whether intentionally ignored globs, hidden files excluded by options, or symlinks should ever be reported. This child covers only non-ignored regular files actually enumerated by the existing scan.

## Investigation and decision

Partition the existing directory enumeration into supported file paths and unsupported diagnostics. Preserve supported-path loading unchanged. Return unsupported entries through the existing `LoadError` shape with absolute `sourcePath`, reason `Unsupported file extension: <extension>`, and code `unsupported_file`; count them in `discoveredFiles` and `skippedFiles`, not `failedFiles`. Keep direct unsupported-path behavior unchanged. Make `--fail-on-error` consult `failedFiles`, preventing directory skips from becoming process failures while retaining failure for actual load errors. Add focused mixed-directory coverage. No parser, format support, schema, dependency, traversal, or canonical resource-model decision is introduced.

## Change

- **Files or components:** Smart Loader directory aggregation in [`src/index.ts`](../asl/_vendor/smart-loader/src/index.ts) and compiled [`dist/index.js`](../asl/_vendor/smart-loader/dist/index.js); CLI exit policy in [`src/cli.ts`](../asl/_vendor/smart-loader/src/cli.ts) and compiled [`dist/cli.js`](../asl/_vendor/smart-loader/dist/cli.js); focused bundled-loader and Python downstream tests; governance/evidence records.
- **Behavior changed:** Directory scans now retain unsupported enumerated files as `unsupported_file` diagnostics with exact source paths and extension reasons, count them as discovered/skipped rather than failed, and continue loading supported files. `--fail-on-error` now uses `failedFiles`, preserving exit `0` for skips and exit `1` for actual load failures. Direct unsupported-path behavior is unchanged.
- **Out-of-scope work deliberately excluded:** TeX/RTF/image/OCR support; parser dependencies; asset ingestion; loader/schema/canonical resource redesign; user/default-ignore reporting; hidden-file or symlink policy; duplicate-key JSON; ragged CSV; malformed HTML; other format behavior; Python adapter redesign; capability negotiation; owner-gated architecture.
- **Rollback or recovery:** Revert the containing implementation commit; no data or dependency migration is anticipated.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| One scan partition plus reuse of `LoadError` for skipped diagnostics | Surface already-enumerated unsupported inputs without adding a result type or parser | Focused mixed-directory SDK/CLI/adapter probes, complete fixture matrix, and full suites | Typed fidelity/resource state and ignored-input policy remain in the parent issue |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-26T03:27:17Z` | `agent:codex-directory-unsupported-reporting` | Compiled CLI on a temporary mixed directory containing Markdown, TeX, RTF, and PNG; repeat with `--fail-on-error` | Exit `0`: only Markdown was discovered/loaded; `skippedFiles: 0`, `failedFiles: 0`, `errors: []`; unsupported names absent; `--fail-on-error` also exited `0` | Inline reproduction above; pre-change JSON SHA-256 `8b0a1983aeab4c811dae1659deaeb6104621a82ccd043007e2b7768bffe0b131` | Controlled fixture; implementation not yet changed |
| `2026-08-26T03:27:17Z` | `agent:codex-directory-unsupported-reporting` | First combined shell reproduction for direct-path and Python-adapter comparison | Diagnostic command aborted after the mixed-directory observations because it assigned zsh's read-only `status` parameter; no missing output was treated as evidence | Corrected invocation in the next row | Instrumentation failure only; product state unchanged |
| `2026-08-26T03:28:34Z` | `agent:codex-directory-unsupported-reporting` | Corrected direct unsupported CLI `--fail-on-error` and Python `SmartLoader` mixed-directory probe | Direct TeX exited `1` with one attributable `load_failed`; Python mixed directory reported `1/1/0/0`, no errors, supported marker present, all three unsupported names absent | Inline reproduction; JSON SHA-256 `ef2e7e8d...` and `7c953191...` | Controlled fixture; implementation not yet changed |
| `2026-08-26T03:31:36Z` | `agent:codex-directory-unsupported-reporting` | `npm test -- --runInBand` | Exit `1` before collection because bundled Vitest does not support `--runInBand` | Correct canonical command in the next row | Tooling invocation error; no product conclusion drawn |
| `2026-08-26T03:31:49Z` | `agent:codex-directory-unsupported-reporting` | `npm test`; `npm run typecheck`; then `npm run build` in bundled Smart Loader | Exit `0`: `7` tests passed, typecheck succeeded, compiled artifacts regenerated | Focused TypeScript regression exercises Markdown/JSON/CSV plus skipped PNG/RTF/TeX | Full repository suite pending |
| `2026-08-26T03:32:32Z` | `agent:codex-directory-unsupported-reporting` | Compiled CLI post-change probe on the exact pre-change mixed directory, with and without `--fail-on-error`, plus direct unsupported TeX | Mixed directory exited `0` both ways with `4/1/3/0`, exact path/reason/code for all three skips, and supported marker retained; direct TeX remained exit `1` and byte-identical to pre-change SHA-256 `ef2e7e8d...` | Post-change mixed JSON SHA-256 `7dbcf4d...`; supported document/chunk payload SHA-256 `4a5c1555...` | Controlled fixture only |
| `2026-08-26T03:33:10Z` | `agent:codex-directory-unsupported-reporting` | Python adapter post-change probe on the same mixed directory | Exit `0`: aggregate summary `4/1/3/0`; metadata and rendered Markdown identify all three skipped paths and reasons; supported marker retained | Markdown SHA-256 `e3da958c...` | Controlled fixture only |
| `2026-08-26T03:33:35Z` | `agent:codex-directory-unsupported-reporting` | Focused Python downstream regression | Exit `0`: `1 passed` | `tests/test_pipeline.py::test_smart_loader_reports_unsupported_directory_inputs_downstream` | Full repository suite pending |
| `2026-08-26T03:34:14Z` | `agent:codex-directory-unsupported-reporting` | Complete `22`-fixture normalization probe and normalized comparison with the approved prior candidate report | Exit `0`: totals `19/17/0/2` → `22/17/3/2`; all `17` supported observations, `19` warnings, and direct unsupported semantics equal; adapter carries five exact diagnostics | [Implementation evidence](../EVIDENCE/EVIDENCE-20260826T033558Z-directory-unsupported-reporting.md) | Controlled synthetic corpus; fresh independent review pending |
| `2026-08-26T03:35:10Z` | `agent:codex-directory-unsupported-reporting` | Full Python/loader suites, loader typecheck, and sibling protocol validator | Exit `0`: `77` Python tests; `7` loader tests; typecheck; `PASS structural protocol validation (package_files=10 handoffs=2)` | [Implementation evidence](../EVIDENCE/EVIDENCE-20260826T033558Z-directory-unsupported-reporting.md) | `.venv` historically lacks pytest and was not retried; no live providers or owner corpus |
| `2026-08-26T03:35:58Z` | `agent:codex-directory-unsupported-reporting` | Repeat loader build, compiled digests, and `git diff --check` | Exit `0`: compiled index/CLI digests unchanged across build; whitespace check clean | [Implementation evidence](../EVIDENCE/EVIDENCE-20260826T033558Z-directory-unsupported-reporting.md) | Governance reconciliation and final scope/ref audit pending |
| `2026-08-26T03:43:51Z` | `agent:codex-directory-unsupported-reporting` | Final focused-regression tightening and bundled `npm test`/`npm run typecheck` rerun | Exit `0`: exact absolute source paths, mixed-directory CLI exit `0`, and direct unsupported CLI exit `1` are executable assertions; all `7` tests and typecheck pass | [Implementation evidence](../EVIDENCE/EVIDENCE-20260826T033558Z-directory-unsupported-reporting.md) | Fresh independent review pending |
| `2026-08-26T03:45:51Z` | `agent:codex-directory-unsupported-reporting` | Final protocol byte/link/HANDOFF/symlink/scope/digest/listener audit and `git diff --check` | Exit `0` except expected no-listener `lsof` exit `1`: `37` Markdown files/`272` local links/none missing; five sections/one action; `7/7` byte mappings; `12` authorized task paths; four digests unchanged | [Implementation evidence](../EVIDENCE/EVIDENCE-20260826T033558Z-directory-unsupported-reporting.md) | Direct remote agreement is checked again after commit publication |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-directory-unsupported-reporting`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** `NOT APPLICABLE`
- **Checks and evidence reviewed:** `NOT APPLICABLE`
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** Independent review is required because discovery, diagnostics, counters, and CLI exit behavior are externally observable.
- **Residual risks:** `NOT APPLICABLE`
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — this slice changes externally observable directory-load diagnostics and summary counts.

No independent review round has been recorded yet.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Independent review of the containing immutable implementation target is pending; no review disposition has been recorded.
- Intentionally ignored paths, broader unsupported-format support, and other silent-degradation cases remain outside this focused child and owned by [`ISSUE-20260824T024051Z-normalization-capability-coverage`](ISSUE-20260824T024051Z-normalization-capability-coverage.md).

## Activity history

Append meaningful transitions and corrections; do not replace prior findings.

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-26T03:28:34Z` | `agent:codex-directory-unsupported-reporting` | `NONE` | `OPEN` | Created the focused child selected by the user and current HANDOFF from the published normalization fixture evidence. |
| `2026-08-26T03:28:34Z` | `agent:codex-directory-unsupported-reporting` | `OPEN` | `INVESTIGATING` | Reproduced silent mixed-directory omission, confirmed direct-file failure remains attributable, and bounded the correction to existing scan/result/CLI contracts. |
| `2026-08-26T03:29:46Z` | `agent:codex-directory-unsupported-reporting` | `INVESTIGATING` | `IMPLEMENTING` | Selected a scan partition, existing-shape `unsupported_file` diagnostics, separate skipped/failed counters, and failed-count CLI policy as the smallest schema- and parser-preserving correction. |
| `2026-08-26T03:33:35Z` | `agent:codex-directory-unsupported-reporting` | `IMPLEMENTING` | `VERIFYING` | Implemented the bounded scan accounting/diagnostic change and focused SDK/CLI/Python regressions; entered full fixture and repository validation. |
| `2026-08-26T03:35:58Z` | `agent:codex-directory-unsupported-reporting` | `VERIFYING` | `REVIEW` | Complete matrix comparison and full validation passed; recorded implementation evidence and left the externally observable diagnostic/counter change for fresh independent review. |
| `2026-08-26T03:43:57Z` | `agent:codex-directory-unsupported-reporting` | `REVIEW` | `REVIEW` | Tightened focused tests to assert exact absolute attribution and compiled CLI exit/direct-file compatibility; final focused reruns pass and review remains the sole gate. |
| `2026-08-26T03:45:51Z` | `agent:codex-directory-unsupported-reporting` | `REVIEW` | `REVIEW` | Final governance, scope, integrity, dirty-set, and HANDOFF checks passed; the issue remains open solely for fresh independent review. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [x] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [ ] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies.
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [x] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [x] HANDOFF reflects the resulting current state and exactly one next action.
