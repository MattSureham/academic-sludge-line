# EVIDENCE-20260825T024729Z: Invalid UTF-8 and NUL Degradation Warnings

## Metadata

- **ID:** `EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning`
- **Title:** Plain-text invalid UTF-8 replacement and NUL removal now carry attributable warnings
- **Captured UTC:** `2026-08-25T02:47:29Z`
- **Recorded by:** `agent:codex-utf8-nul-warning`
- **Claim supported or challenged:** The evidenced plain-text degradation can be surfaced through the existing document warning list without repairing malformed input, changing normalized content, altering schemas or dependencies, or affecting valid text and unrelated fixture observations.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariant 13, and §12
- **Related ADRs/issues:** Focused [`ISSUE-20260825T024242Z-invalid-utf8-nul-warning`](../ISSUES/ISSUE-20260825T024242Z-invalid-utf8-nul-warning.md), parent [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md), and prior [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md); no new ADR
- **Repository revision/state:** Candidate implementation tree based directly on published and independently approved governance-closure revision `5345bc1131157fcaea90287519db1f6b068be5bf`; the containing implementation/governance commit is the intended immutable review target. Four unrelated untracked JavaScript files remained outside the task and unchanged.
- **Environment:** macOS `26.3` / Darwin `25.3.0` arm64; Python `3.9.6`; Node `22.22.0`; npm `10.9.4`; Vitest `4.1.8`; Pandoc `3.9`; Poppler, Tesseract, `textutil`, and `caj2pdf` available to the complete diagnostic; bundled dependency/runtime paths.

## Method

- **Procedure:** Verified that the sole local-ahead commit was the already-approved governance-only closure, published it, fetched, and reconciled local/cached/direct-remote refs at `5345bc1`. Reproduced the published invalid-UTF-8/NUL and valid-text fixtures through compiled `dist` before editing. Traced the behavior to the plain-text loader's non-fatal `TextDecoder` followed by `stripControlCharacters()`. Added only byte predicates and existing-shape warning strings in that loader, retained the same decode/normalization operations, regenerated `dist`, and added focused source tests. Re-ran compiled invalid and valid fixtures, mechanically compared content before/after, probed Python warning rendering, regenerated the complete normalization matrix, and compared curated observations against the independently approved post-PDF-fix report after removing only documented path/time/PDF-fingerprint entropy and the selected fixture's warning list. Ran focused/full tests, typecheck/build, the Python suite, protocol validation, and whitespace checks.
- **Exact command/input:** Compiled `node asl/_vendor/smart-loader/dist/cli.js <invalid-or-valid-fixture.txt> --format json`; `./node_modules/.bin/vitest run tests/basic.test.ts -t "UTF-8"`; bundled `npm run build`, `npm run typecheck`, and `npm test`; direct `python3 -c` `SmartLoader` probe with OCR/page rendering disabled; `node EVIDENCE/diagnostics/normalization_fixture_probe.mjs /private/tmp/asl-normalization-probe-20260825T024600Z`; sorted `jq`/`diff` comparisons against `/private/tmp/asl-pdf-marker-verification-20260824T080201Z/probe-report.json`; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`; sibling `python3 scripts/validate_protocol.py`; `git diff --check`.
- **Exit status:** All commands exited `0`. Focused tests passed `2` and skipped `5`; the full loader suite passed `7`; loader typecheck/build passed; the full Python suite passed `76`; protocol structural validation passed. No failed or corrected invocation contributed to this evidence.
- **Repeatability:** The two checked-in tests generate their own inputs. With bundled dependencies installed, regenerate the full controlled corpus at a fresh absolute temporary path using the exact diagnostic command above. External DOC/PDF/CAJ tooling affects unrelated matrix observations but not the focused plain-text tests.

## Raw observation

### Published behavior and focused change

- At published `5345bc1`, the compiled loader read source bytes `INVALID_UTF8_LEFT FF FE INVALID_UTF8_RIGHT LF CONTROL_LEFT 00 CONTROL_RIGHT LF` as `INVALID_UTF8_LEFT��INVALID_UTF8_RIGHT\nCONTROL_LEFTCONTROL_RIGHT\n`. It returned one document/chunk, no error, and an empty warning list. The direct JSON artifact had SHA-256 `5d7b6033ce464e73f6218b98a5e26ae4000250823e42096aeba5ff51ef67195d`.
- The candidate compiled loader returns the identical document text and Markdown. Its chunk still contains the same normalized text without the terminal newline. The only result delta is the ordered warning list: `Invalid UTF-8 byte sequences were replaced during text decoding.` and `NUL bytes were removed during text normalization.` Removing warning fields from pre/post JSON produced an empty `diff`.
- The valid academic text fixture's complete compiled JSON remained byte-identical before/after, SHA-256 `c36e36e8c95f44c9377ac79ff30c8fb7b13f7597fa2bb03badfda2571229c7ce`. The focused valid test additionally includes non-ASCII text and a legitimately UTF-8-encoded `�`; it remains warning-free, demonstrating that the predicate examines source-byte validity rather than the decoded glyph.
- A direct Python adapter run loaded one document and chunk with no error, retained the same normalized content, and rendered both warning strings into group Markdown. No Python adapter/schema change was needed.

### Complete matrix delta

- The regenerated `22`-fixture corpus retained directory totals of `19` advertised files discovered, `17` documents loaded, `2` failed, `0` skipped, `17` chunks, and `3` assets.
- A sorted comparison of all `16` other loaded documents produced no diff after removing only absolute source path, modification time, and generated PDF fingerprint fields.
- The selected `invalid-utf8.txt` curated observation also produced no diff after removing only its warning list plus the same generation fields. Its text/Markdown lengths remain `64`, chunk count remains `1`, and all four boundary markers remain present.
- The selected fixture's warning list changed from empty to exactly the two warnings above. Raw document warning count therefore changed only from `17` to `19`; Python group Markdown length changed from `7,900` to `8,006` because those warnings propagate. The approved PDF marker warning remains present, and all other curated warning lists and observations are unchanged.

### Executable verification

- Focused source run: one test file; `2` focused tests passed, `5` skipped, duration `368ms`.
- Full bundled loader: one file and `7` tests passed in `419ms`; typecheck and build passed.
- Full Python suite: `76 passed in 7.53s`.
- Sibling protocol validator: `PASS structural protocol validation (package_files=10 handoffs=2)`.
- `git diff --check` emitted no output and exited `0` before governance reconciliation.
- Final repository audit passed after governance reconciliation: `34` Markdown files, `238` local links, `0` missing; exactly five ordered HANDOFF sections and one nonempty Next Action; all seven adopted protocol byte mappings matched source revision `58fa281`; no governance symlink; exactly nine authorized task paths; protected specification/dependency/Python/other-loader scope clean; no port `8765` listener; and all four unrelated untracked digests unchanged.

## Interpretation

- **CONFIRMED:** The plain-text route now surfaces both known transformations through existing warnings while preserving the established non-fatal replacement and NUL-removal output.
- **CONFIRMED:** Valid UTF-8, including a valid encoding of U+FFFD, remains warning-free; the detection does not infer invalid bytes from decoded text.
- **CONFIRMED:** The correction is local to `.txt` loading. It introduces no dependency, output field, parser strategy, encoding repair, or behavior change in other formats in the controlled matrix.
- **CONFIRMED:** Existing downstream warning propagation remains compatible: warnings reach Python group Markdown, while the known structured-summary omission remains unchanged and outside this slice.
- **CONFIRMED:** Invariant 13 and §§10–12 remain only partially implemented because the other published silent-degradation cases and broader semantic-fidelity gaps are deliberately unresolved.

## Limitations and residual uncertainty

- Fixtures are controlled and synthetic. This evidence detects strict UTF-8 invalidity and byte `00`; it does not infer an intended legacy encoding, repair bytes, preserve NUL, grade semantic usefulness, or claim owner-corpus thresholds.
- Only the plain-text route is changed. Shared low-level decoding remains warning-free for Markdown, JSON, CSV, and HTML, and their behavior was intentionally not reclassified or altered by this focused child.
- The current warning contract is an ordered string list, not a typed fidelity schema. Selecting such a schema remains owner-gated in the parent issue.
- Independent review of the containing commit remains required before the focused issue can close.

## Integrity and provenance

- **Artifact location:** Product/tests in the containing commit; ephemeral pre-change JSON at `/private/tmp/asl-invalid-utf8-nul-before.json` and `/private/tmp/asl-valid-utf8-before.json`; ephemeral post-change JSON at corresponding `*-after.json` paths; complete post-change run at `/private/tmp/asl-normalization-probe-20260825T024600Z/`; durable generator at [`EVIDENCE/diagnostics/normalization_fixture_probe.mjs`](diagnostics/normalization_fixture_probe.mjs).
- **Artifact digest:** SHA-256 `f41a377a82b370e2c3831f9f17b3ae00172807f2ecab97b4bc27ba714eeea823` (`src/loaders/text.ts`); `0ee6ac42733b674d9e95b75cbc186aeec5665f2a90463376ef7a55a92b3aa3af` (`dist/loaders/text.js`); `84dd31039abe69a61c79c742c60ba7545f892b4daf3423314b540c050e5791ba` (`tests/basic.test.ts`); `873c3c9d662cfc46956ddfb211e8e1d459066f2dc5aed15156232bb878d9998d` (diagnostic generator); `78ea62e3981573bd29f0e169e1a4c398592b87066a7dcef59cc534f8dff20395` (`probe-report.json`); `0fbfda1ff190a238e7600b5c1e5d41befe9f31f803a09662384c8e772ad33ac8` (`raw-loader-result.json`); `288dbb95231ec73a0561c3001be0732fe93bd3dc79eb4fd9e56e26ef9cc0258a` (`python-adapter-result.json`).
- **External retention risk:** `HIGH` for temporary generated reports/fixtures; all inputs are synthetic, and checked-in tests/generator plus the inline observations provide durable reproduction.
- **Supersedes / superseded by:** Supersedes only the prior matrix's current-state claim that invalid-UTF-8 replacement and NUL removal carry no warning. That observation remains valid at its captured revision. It does not supersede any other normalization finding.

## Corrections

No corrections were required during this evidence run.
