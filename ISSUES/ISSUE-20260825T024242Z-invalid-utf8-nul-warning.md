# ISSUE-20260825T024242Z: Surface Invalid UTF-8 and NUL Text Degradation

## Metadata

- **ID:** `ISSUE-20260825T024242Z-invalid-utf8-nul-warning`
- **Title:** Surface invalid UTF-8 replacement and NUL removal in text normalization
- **Status:** `REVIEW`
- **Severity:** `MEDIUM`
- **Owner:** `agent:codex-utf8-nul-warning`
- **Authority:** `AGENT`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-25T02:42:42Z`
- **Updated UTC:** `2026-08-25T02:54:44Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariant 13, and §12
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](../EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md) and [`EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning`](../EVIDENCE/EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning.md)
- **Milestone:** `NONE`

## Problem

The plain-text loader decodes malformed UTF-8 with replacement characters and removes NUL characters during normalization, but returns no warning. At published baseline `5345bc1`, known source degradation is therefore presented through the same warning-free shape as valid text.

## Evidence or reproduction

The published fixture matrix records a text fixture containing bytes `FF FE` and a NUL between attributable marker strings. Running the compiled loader at `5345bc1131157fcaea90287519db1f6b068be5bf` returns `INVALID_UTF8_LEFT��INVALID_UTF8_RIGHT\nCONTROL_LEFTCONTROL_RIGHT\n`, one document and chunk, no load errors, and `warnings: []`. Thus the non-fatal UTF-8 decoder inserts two replacement characters and `stripControlCharacters()` removes the NUL, concatenating its neighbors. The matrix's valid UTF-8 text fixture also returns with no warnings.

## Expected behavior

Under accepted §§2.5 and 4.8 and invariant 13, when the plain-text normalization path knows that malformed UTF-8 was replaced or NUL content was removed, the loaded document MUST expose attributable degradation through the existing warning list. The current decoded/normalized text, Markdown, chunks, schema, and valid-text behavior MUST otherwise remain unchanged.

## Assumptions

- **CONFIRMED:** The package requires Node `>=20`; the current Node `v22.22.0` provides `node:buffer.isUtf8()`, which distinguishes malformed source bytes from a valid UTF-8 encoding of the replacement character.
- **CONFIRMED:** Only `loadText` is in scope. Markdown, JSON, CSV, HTML, PDF, DOCX, DOC, and CAJ behavior is excluded even where they share low-level decoding helpers.
- **CONFIRMED:** Per-document warning strings already propagate through the TypeScript result and Python-rendered group Markdown without a schema change.
- **INFERRED:** Inspecting the original text buffer before the existing non-fatal decode and NUL stripping is the smallest reversible way to report both known losses while preserving output bytes after normalization.
- **UNKNOWN:** Encoding detection or recovery beyond strict UTF-8 validity, and whether NUL has intentional domain meaning in any owner corpus; neither is required to report this evidenced degradation.

## Investigation and decision

Keep the existing non-fatal UTF-8 decode and `stripControlCharacters()` result unchanged. In the plain-text loader only, inspect the original bytes for invalid UTF-8 and NUL before those transformations, then append one stable warning for each observed degradation. Add focused tests for the controlled malformed/NUL fixture and for valid Unicode text, including a legitimately encoded replacement character. This is a routine correction under accepted warning behavior, not a normalization architecture decision.

## Change

- **Files or components:** [`asl/_vendor/smart-loader/src/loaders/text.ts`](../asl/_vendor/smart-loader/src/loaders/text.ts), compiled [`dist/loaders/text.js`](../asl/_vendor/smart-loader/dist/loaders/text.js), focused [`tests/basic.test.ts`](../asl/_vendor/smart-loader/tests/basic.test.ts), and governance/evidence records.
- **Behavior changed:** The plain-text loader now adds one warning when source bytes are not valid UTF-8 and one warning when source bytes contain NUL. It retains the same non-fatal decoder and NUL-stripping normalization, so document text, Markdown, and chunks are unchanged.
- **Out-of-scope work deliberately excluded:** Input repair; encoding inference/transcoding; preservation of NUL; Smart Loader/schema redesign; new dependencies; Markdown/JSON/CSV/HTML/PDF/DOCX/DOC/CAJ behavior; duplicate-key JSON, ragged CSV, malformed HTML, unsupported directory inputs, OCR/capability work, and owner-gated architecture.
- **Rollback or recovery:** Revert the containing implementation commit; no data or dependency migration is anticipated.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Two byte-level predicates and two existing-shape warning strings in the text loader | Attribute the two transformations demonstrated by the controlled fixture without changing normalized content | Focused invalid/NUL and valid Unicode tests plus compiled and downstream probes | Other matrix cases and any broader fidelity contract remain in the parent issue |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-25T02:42:42Z` | `agent:codex-utf8-nul-warning` | Run compiled `dist/cli.js --format json` against published matrix fixtures `invalid-utf8.txt` and `academic.txt` at `5345bc1` | Exit `0` for both: degraded fixture returned `��`, removed NUL, and no warnings; valid fixture was warning-free | Inline reproduction above; pre-change JSON SHA-256 `5d7b6033ce464e73f6218b98a5e26ae4000250823e42096aeba5ff51ef67195d` and `c36e36e8c95f44c9377ac79ff30c8fb7b13f7597fa2bb03badfda2571229c7ce` | Controlled synthetic fixtures; implementation not yet changed |
| `2026-08-25T02:44:44Z` | `agent:codex-utf8-nul-warning` | `./node_modules/.bin/vitest run tests/basic.test.ts -t "UTF-8"` | Exit `0`: one file; `2` focused tests passed and `5` skipped | Focused source regressions | Synthetic inputs; full suite pending |
| `2026-08-25T02:45:00Z` | `agent:codex-utf8-nul-warning` | Bundled `npm run build` and `npm run typecheck` | Exit `0` for both | Compiled distribution and source/test type contract | Full runtime matrix pending |
| `2026-08-25T02:45:24Z` | `agent:codex-utf8-nul-warning` | Compiled CLI before/after comparison on invalid/NUL and valid fixtures; direct Python `SmartLoader` propagation probe | Exit `0`: degraded content/result unchanged after removing warning fields; exactly two attributable warnings added and rendered in group Markdown; valid JSON output remained byte-identical with SHA-256 `c36e36...`; no errors | [Implementation evidence](../EVIDENCE/EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning.md) | Controlled fixtures; complete matrix and full suites recorded in the next row |
| `2026-08-25T02:47:29Z` | `agent:codex-utf8-nul-warning` | Complete normalization probe and normalized comparison to approved post-PDF baseline; full Python/loader suites; loader typecheck/build; sibling protocol validator; `git diff --check` | Exit `0`: all `16` other documents equal; selected document equal except warnings; totals `19/17/2/17/3`; warnings `17` → `19`; `76` Python and `7` loader tests passed; remaining checks passed | [Implementation evidence](../EVIDENCE/EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning.md) | Controlled corpus; fresh independent review pending |
| `2026-08-25T02:54:44Z` | `agent:codex-utf8-nul-warning` | Final protocol byte/link/HANDOFF/symlink/scope/digest/listener audit and `git diff --check` | Exit `0` except expected no-listener `lsof` exit `1`: `34` Markdown files/`238` local links/none missing; five sections/one action; `7/7` byte mappings; nine authorized paths; four digests unchanged | [Implementation evidence](../EVIDENCE/EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning.md) | Direct remote agreement is checked again after commit publication |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-utf8-nul-warning`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** `NOT APPLICABLE`
- **Checks and evidence reviewed:** `NOT APPLICABLE`
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** Independent review is required because warning behavior is externally observable.
- **Residual risks:** `NOT APPLICABLE`
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — this slice changes externally observable warning behavior.

No independent review round has been recorded yet.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Independent review of the eventual immutable implementation target is pending.
- Other recorded silent-degradation cases and any broader semantic-normalization contract remain outside this focused child and owned by [`ISSUE-20260824T024051Z-normalization-capability-coverage`](ISSUE-20260824T024051Z-normalization-capability-coverage.md).

## Activity history

Append meaningful transitions and corrections; do not replace prior findings.

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-25T02:42:42Z` | `agent:codex-utf8-nul-warning` | `NONE` | `OPEN` | Created the focused child selected by the user and current HANDOFF from the published normalization fixture evidence. |
| `2026-08-25T02:42:42Z` | `agent:codex-utf8-nul-warning` | `OPEN` | `INVESTIGATING` | Reproduced the warning-free compiled behavior at the published baseline and traced it to non-fatal UTF-8 decoding followed by NUL stripping in the plain-text route. |
| `2026-08-25T02:44:06Z` | `agent:codex-utf8-nul-warning` | `INVESTIGATING` | `IMPLEMENTING` | Selected two byte-level predicates and existing-shape document warnings as the smallest content-preserving correction; no parser, schema, dependency, or unrelated-format change is authorized. |
| `2026-08-25T02:45:24Z` | `agent:codex-utf8-nul-warning` | `IMPLEMENTING` | `VERIFYING` | Added warning-only byte diagnostics in the plain-text route plus degraded and valid regressions; focused tests, build/typecheck, compiled output comparison, and downstream propagation probe pass. |
| `2026-08-25T02:47:29Z` | `agent:codex-utf8-nul-warning` | `VERIFYING` | `REVIEW` | Complete matrix comparison and full validation passed; recorded implementation evidence and left the externally observable warning change for fresh independent review. |
| `2026-08-25T02:54:44Z` | `agent:codex-utf8-nul-warning` | `REVIEW` | `REVIEW` | Final governance, scope, integrity, dirty-set, and HANDOFF checks passed; the issue remains open solely for fresh independent review. |

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
