# ISSUE-20260824T075708Z: Warn When PDF Extraction Contains Only Page Markers

## Metadata

- **ID:** `ISSUE-20260824T075708Z-pdf-marker-only-warning`
- **Title:** Warn when PDF extraction contains only parser page markers
- **Status:** `CLOSED`
- **Severity:** `MEDIUM`
- **Owner:** `agent:codex-pdf-marker-warning`
- **Authority:** `AGENT`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T07:57:08Z`
- **Updated UTC:** `2026-08-24T08:30:14Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariant 13, and §12
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](../EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md), [`EVIDENCE-20260824T080248Z-pdf-marker-only-warning`](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md), and [`EVIDENCE-20260824T083014Z-pdf-marker-warning-review`](../EVIDENCE/EVIDENCE-20260824T083014Z-pdf-marker-warning-review.md)
- **Milestone:** `NONE`

## Problem

The PDF parser can return page-marker boilerplate such as `-- 1 of 1 --` for an image-only PDF. At published baseline `2f5e1ad`, the loader checked only whether the normalized parser string was empty, so marker-only extraction suppressed the existing `No extractable PDF text was found` warning and presented boilerplate as though meaningful source text was extracted.

## Evidence or reproduction

The normalization fixture matrix independently validates a one-page image-only PDF with no text or fonts. At published baseline `2f5e1ad5a16bd1f1a3c1922575898bc99cd8f0bb`, running the bundled CLI on that fixture returns `text: "-- 1 of 1 --"`, one document/chunk, no load error, and only the default images-not-extracted warning. The no-extractable-text warning is absent. Running the same CLI on the two-page text-native fixture returns meaningful academic markers plus `-- 1 of 2 --` and `-- 2 of 2 --`, also without the no-text warning.

## Expected behavior

Under accepted §§2.5 and 4.8 and invariant 13, a PDF extraction made solely of parser-generated `-- n of m --` marker lines is not meaningful extracted text and MUST follow the loader's existing no-extractable-text warning semantics. Meaningful PDF text, including text interleaved with those page markers, MUST remain unaffected. The existing document, text, Markdown, chunk, warning, and metadata schema remains unchanged.

## Assumptions

- **CONFIRMED:** The observed `pdf-parse` marker syntax is a line containing `--`, a decimal page number, `of`, a decimal total, and `--`; the controlled one-page output is exactly `-- 1 of 1 --`.
- **CONFIRMED:** At published baseline `2f5e1ad`, the warning was emitted only when `normalizePdfText(textResult.text).trim()` was empty.
- **CONFIRMED:** The accepted specification requires known extraction loss to be surfaced and leaves parser strategy open.
- **INFERRED:** Testing for at least one nonblank, non-marker line is the smallest reversible correction because it reuses the warning contract and does not alter parser output or downstream schemas.
- **UNKNOWN:** Whether future `pdf-parse` versions emit other boilerplate forms; this slice covers only the evidenced `-- n of m --` lines.

## Investigation and decision

Use a private predicate in the existing PDF loader to classify normalized output as meaningful when at least one nonblank line is not an evidenced page marker. Keep `text` and `markdown` byte-compatible with current valid parser output, including retained page markers, and change only the condition that emits the existing warning. Add a generated image-only-PDF regression and strengthen the existing text-native-PDF test. This is a routine defect fix within accepted behavior and does not select a new normalization schema or parser architecture.

## Change

- **Files or components:** [`asl/_vendor/smart-loader/src/loaders/pdf.ts`](../asl/_vendor/smart-loader/src/loaders/pdf.ts), compiled [`dist/loaders/pdf.js`](../asl/_vendor/smart-loader/dist/loaders/pdf.js), focused [`tests/basic.test.ts`](../asl/_vendor/smart-loader/tests/basic.test.ts), and governance/evidence records.
- **Behavior changed:** Normalized PDF output is now considered meaningful only when it contains at least one nonblank line other than an evidenced `-- n of m --` page marker. Marker-only extraction receives the unchanged no-extractable-text warning; returned text/Markdown/chunks and meaningful text-PDF output are not rewritten.
- **Out-of-scope work deliberately excluded:** PDF extraction redesign; Smart Loader or normalization-schema redesign; DOCX assets/equations; unsupported-directory reporting; encoding, JSON, CSV, HTML, or DOC behavior; warning-schema changes; OCR confidence; capability negotiation; either owner-gated `HIGH` issue.
- **Rollback or recovery:** Revert the containing implementation commit; no data migration or dependency rollback is required.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| One private PDF-text classification predicate | Distinguish evidenced parser boilerplate from meaningful text without changing parser output | Focused marker-only and meaningful-text loader tests | Other known silent normalization cases remain in the parent issue |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T07:57:08Z` | `agent:codex-pdf-marker-warning` | Run bundled `dist/cli.js --format json` against the matrix's image-only and two-page text-native PDF fixtures at published `2f5e1ad` | Exit `0` for both: marker-only text was `-- 1 of 1 --` without the no-text warning; meaningful fixture retained academic text plus both page markers without the no-text warning | Normalization fixture matrix and inline reproduction above | Reuses the controlled temporary fixture; implementation tests are not yet added |
| `2026-08-24T07:59:30Z` | `agent:codex-pdf-marker-warning` | `./node_modules/.bin/vitest run tests/basic.test.ts -t PDF` | Exit `1`: the new test timed out and Vitest reported uncaught zlib `incorrect data check` / `Z_DATA_ERROR` | [Implementation evidence correction](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md) | Test-fixture defect only; the invalid PNG was discarded and no product conclusion was drawn |
| `2026-08-24T08:00:20Z` | `agent:codex-pdf-marker-warning` | In-memory PDFKit validation of replacement PNG, then corrected focused Vitest command | Exit `0`: replacement image accepted; one file passed with `2` PDF tests passed and `3` skipped | Focused tests and implementation evidence | Source tests; compiled runtime separately probed below |
| `2026-08-24T08:01:08Z` | `agent:codex-pdf-marker-warning` | `npm run build`; compiled CLI before/after probes; direct Python `SmartLoader` probe | Exit `0`: scanned text/Markdown/chunk unchanged plus warning; meaningful PDF warning absent; Python loaded `1`, failed `0`, retained one chunk, and propagated warning into group Markdown | [Implementation evidence](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md) | Controlled fixtures; no representative corpus claim |
| `2026-08-24T08:02:07Z` | `agent:codex-pdf-marker-warning` | Complete normalization probe plus normalized `jq`/`diff` comparison to the prior report | Exit `0`: unchanged `19/17/2/17/3` discovery/load/failure/chunk/asset totals; all non-scanned curated documents equal; scanned document equal except intended warning; warnings `16` → `17` | [Implementation evidence](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md) | Generation path/time/fingerprint entropy excluded explicitly |
| `2026-08-24T08:02:48Z` | `agent:codex-pdf-marker-warning` | Full Python suite; full loader tests; loader typecheck/build; sibling protocol validator; `git diff --check` | Exit `0`: `76 passed in 8.10s`; `5 passed in 384ms`; typecheck/build passed; protocol validator passed; whitespace clean | [Implementation evidence](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md) | `.venv` pytest historically unavailable and not retried; system Python suite passed |
| `2026-08-24T08:10:19Z` | `agent:codex-pdf-marker-warning` | Markdown/local-link/HANDOFF checker; seven protocol byte comparisons; symlink/port/protected-scope/four-file digest audit | Exit `0` except expected no-listener `lsof` exit `1`: `31` Markdown files, `205` local links, none missing; five sections/one action; `7/7` mappings; no symlinks; protected scope clean; four hashes unchanged | [Implementation evidence](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md) | Direct remote agreement is checked again after commit publication |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-pdf-marker-warning`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** `NOT APPLICABLE`
- **Checks and evidence reviewed:** `NOT APPLICABLE`
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** Independent review is required because warning behavior changes externally observable loader output.
- **Residual risks:** `NOT APPLICABLE`
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — this defect fix changes externally observable warning behavior.

### 2026-08-24T08:30:14Z — agent:claude-code-independent-review

- **Reviewed repository state:** Containing implementation commit `e9c503b4ccc65c0907c554bd1c5fc349d2b2474b`, direct parent `2f5e1ad5a16bd1f1a3c1922575898bc99cd8f0bb`; `HEAD`, `origin/main`, and direct remote `main` all at the reviewed target; tracked tree clean with exactly the four recorded unrelated untracked JavaScript files.
- **Reviewed target:** `e9c503b4ccc65c0907c554bd1c5fc349d2b2474b`
- **Open material findings:** `0`
- **Scope:** Behavioral correctness, focused regression coverage, preservation of extracted text/Markdown/chunks, warning propagation, meaningful-text PDF compatibility, scope containment, and issue/evidence/HANDOFF consistency for the marker-only PDF warning slice.
- **Commands or procedures:** Read the specification sections, focused issue, implementation evidence, parent issue, and matrix delta before code; read the complete product/test diff; rebuilt the loader and confirmed zero drift between source and committed `dist/`; reran the loader suite (`5 passed in 417ms`), typecheck, the full Python suite (`76 passed in 8.71s`), and the sibling protocol validator; probed the compiled private classifier against eleven edge strings; generated independent image-only and two-page text-native PDFs and verified the compiled CLI and Python adapter end to end; checked scope, digests, remotes, links, HANDOFF structure, and port state. Full detail is in the linked evidence.
- **Specification compliance:** The change satisfies the slice's §§2.5/4.8 and invariant-13 obligations: evidenced extraction boilerplate no longer suppresses the degradation warning, and the warning contract itself is unchanged.
- **Correctness and regression findings:** Marker-only output is preserved verbatim in text/Markdown/chunks while gaining the intended warning; meaningful text interleaved with markers remains warning-free; all pre-existing tests pass unmodified; the focused tests cover both directions.
- **Architecture and complexity findings:** One private predicate reusing the existing warning shape; no new dependency, schema, parser strategy, or cross-module contract.
- **Material findings and resolution conditions:** `NONE`. Non-material observation: unrecognized near-marker forms (no spaces, decimal numbers, suffixed text) are conservatively treated as meaningful, matching the declared matcher scope; broader boilerplate remains owned by the parent issue.
- **Limitations:** Synthetic fixtures only; no representative corpus or live OCR; same host class as the implementor; labels are attributable, not authenticated.
- **Residual risks:** Other recorded silent-degradation cases and parser boilerplate families remain open under the parent normalization/capability issue.
- **Evidence:** [`EVIDENCE-20260824T083014Z-pdf-marker-warning-review`](../EVIDENCE/EVIDENCE-20260824T083014Z-pdf-marker-warning-review.md)
- **Disposition:** `APPROVED`
- **Prior-round resolution:** `FIRST ROUND`

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Resolved: fresh independent review of `e9c503b` recorded `APPROVED` with zero open material findings at `2026-08-24T08:30:14Z`.
- Other silent normalization cases in the fixture matrix remain outside this issue and owned by the parent normalization/capability issue.
- The matcher deliberately recognizes only the evidenced page-marker line family; other parser boilerplate remains unverified.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T07:57:08Z` | `agent:codex-pdf-marker-warning` | `NONE` | `OPEN` | Created the focused issue from the published normalization fixture evidence and current HANDOFF. |
| `2026-08-24T07:57:08Z` | `agent:codex-pdf-marker-warning` | `OPEN` | `INVESTIGATING` | Reproduced marker-only warning suppression and confirmed valid text-PDF output at published `2f5e1ad`; bounded the correction to the existing warning condition and focused tests. |
| `2026-08-24T07:57:08Z` | `agent:codex-pdf-marker-warning` | `INVESTIGATING` | `IMPLEMENTING` | Selected the private line classifier and generated fixture tests; no schema, parser, dependency, or non-PDF behavior is in scope. |
| `2026-08-24T08:01:08Z` | `agent:codex-pdf-marker-warning` | `IMPLEMENTING` | `VERIFYING` | Added the private page-marker classifier, compiled runtime output, and focused image-only/meaningful-PDF assertions. Corrected only an invalid embedded test PNG after the first focused run exposed its zlib error; the corrected focused run passed. |
| `2026-08-24T08:07:50Z` | `agent:codex-pdf-marker-warning` | `VERIFYING` | `REVIEW` | Focused/full suites, compiled/downstream probes, complete matrix comparison, governance reconciliation, and scope checks passed; implementation awaits fresh independent review. |
| `2026-08-24T08:30:14Z` | `agent:claude-code-independent-review` | `REVIEW` | `CLOSED` | Fresh independent review of `e9c503b` recorded `APPROVED` with zero open material findings after classifier probes, independent fixture runs, adapter propagation, suites, build parity, and scope checks. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [x] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [x] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [x] Required human authority is recorded in the owning artifact: accepted `PROJECT_SPEC.md` authorizes surfacing extraction loss; no new architecture is selected.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [x] HANDOFF reflects the resulting current state and exactly one next action.
