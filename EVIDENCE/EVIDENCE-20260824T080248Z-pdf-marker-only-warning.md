# EVIDENCE-20260824T080248Z: Page-Marker-Only PDF Warning Correction

## Metadata

- **ID:** `EVIDENCE-20260824T080248Z-pdf-marker-only-warning`
- **Title:** Marker-only PDF extraction now follows existing no-text warning semantics
- **Captured UTC:** `2026-08-24T08:02:48Z`
- **Recorded by:** `agent:codex-pdf-marker-warning`
- **Claim supported or challenged:** A private PDF-text classifier can make the evidenced `-- n of m --`-only case emit the existing no-extractable-text warning without rewriting parser output, changing the output schema, or changing meaningful-PDF and unrelated-format observations.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariant 13, and §12
- **Related ADRs/issues:** [`ISSUE-20260824T075708Z-pdf-marker-only-warning`](../ISSUES/ISSUE-20260824T075708Z-pdf-marker-only-warning.md), parent [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md), and prior [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md); no new ADR
- **Repository revision/state:** Candidate implementation tree based directly on published `2f5e1ad5a16bd1f1a3c1922575898bc99cd8f0bb`; the containing implementation/governance commit is the intended immutable review target. Product/test file hashes are recorded below. Four unrelated untracked JavaScript files remained outside the task and untouched.
- **Environment:** macOS `26.3` / Darwin `25.3.0` arm64; Python `3.9.6`; Node `22.22.0`; npm `10.9.4`; Vitest `4.1.8`; Pandoc `3.9`; Poppler `26.06.0`; Tesseract `5.5.2`; macOS `textutil`; locally installed `caj2pdf`; bundled dependency/runtime paths.

## Method

- **Procedure:** Reproduced both the controlled image-only and meaningful two-page PDFs through the published compiled CLI before editing. Changed only the warning predicate in the PDF loader, generated compiled output, and added an embedded-raster PDF test plus a no-warning assertion to the existing meaningful-PDF test. Re-ran the same fixtures through compiled output and the Python adapter. Re-ran the complete normalization probe and mechanically compared its curated document observations with the pre-change report after removing only path/time/fingerprint generation entropy and, for the scanned PDF comparison, its warning list. Ran focused/full loader tests, typecheck/build, the full Python suite, protocol validation, and whitespace checks.
- **Exact command/input:** `node asl/_vendor/smart-loader/dist/cli.js <scanned-or-academic-fixture.pdf> --format json | jq ...`; `./node_modules/.bin/vitest run tests/basic.test.ts -t PDF`; `npm run build`; the inline `PYTHONDONTWRITEBYTECODE=1 python3` adapter probe recorded below; `node EVIDENCE/diagnostics/normalization_fixture_probe.mjs /private/tmp/asl-pdf-marker-verification-20260824T080201Z`; two `diff -u <(jq -S ...)` comparisons against `/private/tmp/asl-normalization-probe-20260824T073600Z/probe-report.json`; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`; `npm test`; `npm run typecheck`; `npm run build`; sibling `python3 scripts/validate_protocol.py`; `git diff --check`; standard-library Markdown/local-link/HANDOFF validation; seven `cmp` checks against protocol source revision `58fa281`; symlink, port `8765`, protected-scope, and four-file digest checks.
- **Exit status:** Published-state CLI reproductions exited `0`. The first focused test attempt exited `1` because the embedded test PNG had invalid compressed data and produced a timeout plus `Z_DATA_ERROR`; replacing only that test constant with an independently accepted PNG buffer corrected the fixture. The corrected focused run, compiled CLI/adapter probes, complete normalization probe/comparisons, all final suites/builds, protocol validation, and whitespace check exited `0`.
- **Repeatability:** At the containing commit, run the loader tests/build commands from `asl/_vendor/smart-loader`, the Python and protocol commands from their recorded repository roots, and regenerate the probe at any fresh absolute temporary path. The checked-in test creates its own image-only PDF and does not require Poppler or OCR; the complete probe's environment-sensitive tools remain listed above.

## Raw observation

### Before and after

- At published `2f5e1ad`, the validated image-only fixture loaded with no errors as one PDF document and one chunk. `text` was exactly `-- 1 of 1 --`; Markdown was `# Scanned fixture` plus that marker; warnings contained only the default images-not-extracted warning when page rendering was disabled. The no-extractable-text warning was absent.
- In the candidate tree, the same compiled CLI invocation returns the same document count, chunk count, `text`, Markdown, and chunk text, but warnings now contain `No extractable PDF text was found. The PDF may be scanned or image-heavy.` followed by the unchanged images-not-extracted warning.
- Before and after, the meaningful two-page fixture contains the same academic markers and `-- 1 of 2 --` / `-- 2 of 2 --` delimiters, loads as one document and one chunk, and does not receive the no-extractable-text warning.
- A direct Python `SmartLoader` probe with page rendering and OCR disabled returned `loadedFiles: 1`, `failedFiles: 0`, `text: "-- 1 of 1 --"`, `chunkCount: 1`, `warningPresent: true`, and `warningInGroupMarkdown: true`. This confirms the unchanged downstream envelope and propagation path.

### Complete matrix delta

- The post-change `22`-fixture probe exited `0` with the unchanged directory summary: `19` advertised files discovered, `17` loaded, `2` failed, `0` skipped, `17` chunks, and `3` assets.
- A sorted comparison of all curated observations for the other `16` loaded documents produced no diff after removing absolute source path, modification time, and generated PDF fingerprint fields.
- A sorted comparison of the scanned document produced no diff after additionally removing only its warning list. Its post-change warning list contains exactly the existing no-extractable-text warning; the meaningful `academic.pdf` warning list remains empty when page rendering succeeds.
- Raw per-document warning count changed only from `16` to `17`. Python group Markdown length changed from `7,789` to `7,900` characters because the warning now propagates; discovery/load/failure/chunk/asset totals, error behavior, OCR-marker presence, and the structured-summary omission of per-document warnings remain unchanged.

### Executable verification

- Corrected focused PDF run: one file passed, `2` PDF tests passed, `3` unrelated tests skipped, duration `357ms`.
- Full bundled loader: one file and `5` tests passed in `384ms`; typecheck and build passed.
- Full Python suite: `76 passed in 8.10s`.
- Sibling protocol validator: `PASS structural protocol validation (package_files=10 handoffs=2)`.
- `git diff --check` emitted no output and exited `0` at the candidate state.
- Repository audit: `31` tracked/task Markdown files, `205` local links, `0` missing; exactly five ordered HANDOFF sections and one nonempty Next Action; seven adopted protocol byte mappings matched; no governance symlink; no port `8765` listener (expected `lsof` exit `1`); protected specification/dependency/Python product/test paths had no diff; four unrelated untracked file digests matched their recovery values.

## Interpretation

- **CONFIRMED:** Marker-only `pdf-parse` output no longer suppresses the existing extraction warning.
- **CONFIRMED:** The fix does not delete or rewrite page markers, document content, Markdown, chunks, assets, metadata, error behavior, or output types; downstream consumers receive the same shape plus the intended warning.
- **CONFIRMED:** Meaningful text interleaved with parser page markers remains meaningful and does not receive the no-text warning.
- **CONFIRMED:** The complete controlled matrix shows no observed change to other documents or formats. The parent normalization requirement and invariant 13 remain only partially implemented because every other previously recorded silent case remains out of scope.
- **INFERRED:** A line-level private predicate is proportionate to the evidenced parser behavior and adds no durable normalization architecture.
- **UNKNOWN:** Other parser-generated boilerplate families and future parser output conventions remain unverified.

## Limitations and residual uncertainty

- The focused checked-in fixture is a one-page PDF with an embedded one-pixel PNG. The prior larger scanned fixture and complete probe corroborate the same marker-only behavior, but neither is a representative accessibility corpus.
- The matcher deliberately covers only lines matching the evidenced `-- n of m --` family. It does not classify arbitrary punctuation, headers/footers, OCR quality, or other low-information extraction.
- The complete probe uses environment-sensitive DOC/CAJ/PDF rendering and OCR routes. The semantic comparison removes explicitly identified generation entropy; it is not a general byte-for-byte corpus proof.
- Independent review of the containing commit remains required before the focused issue can close.

## Integrity and provenance

- **Artifact location:** Product/tests in the containing commit; ephemeral post-change report at `/private/tmp/asl-pdf-marker-verification-20260824T080201Z/`; durable generator at [`EVIDENCE/diagnostics/normalization_fixture_probe.mjs`](diagnostics/normalization_fixture_probe.mjs).
- **Artifact digest:** SHA-256 `6e62c6e2ac037b95b18a9aaa8d500f2ad1147b9600bf31fb05cbbca9b90657a3` (`src/loaders/pdf.ts`); `6e0499ff67ff8549d3f1a84f7966aca81637b6add3703803e0cd87c9de77ba6a` (`dist/loaders/pdf.js`); `d15511a8d291454e6dd8c7002f663bb34cef1c74c998bc1cd793a16d3bd3c8e5` (`tests/basic.test.ts`); `dbc108df1064343aa09212abbf7167eb3d764de561f213524b441cdd5960072e` (`probe-report.json`); `6c54fc90d2cb1a0643cb60adb0e9d7a759e4c8581766afcaa577a973349fef59` (`raw-loader-result.json`); `ae15b3b7306fb080d36e4963e29724902ad4598af2e1a7a15a5fd2a38bb8de5c` (`python-adapter-result.json`).
- **External retention risk:** `HIGH` for temporary generated reports/fixtures; all are synthetic, and the committed test/generator plus inline observations are the durable reproduction paths.
- **Supersedes / superseded by:** Supersedes only the prior matrix's current-state claim that the image-only PDF receives no extraction warning; that observation remains valid at its recorded revision. It does not supersede any other normalization finding.

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T08:00:20Z` | `agent:codex-pdf-marker-warning` | The first embedded one-pixel PNG constant was discarded and is not used as behavior evidence. | The first focused run timed out with an uncaught zlib `incorrect data check` / `Z_DATA_ERROR`; an in-memory PDFKit probe accepted the replacement PNG, after which the same focused test passed. No product logic changed in response. |
