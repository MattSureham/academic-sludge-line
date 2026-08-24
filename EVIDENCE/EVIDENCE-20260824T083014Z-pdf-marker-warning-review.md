# EVIDENCE-20260824T083014Z: Fresh Independent Review of the Page-Marker-Only PDF Warning

## Metadata

- **ID:** `EVIDENCE-20260824T083014Z-pdf-marker-warning-review`
- **Title:** Fresh independent review of the marker-only PDF warning commit
- **Captured UTC:** `2026-08-24T08:30:14Z`
- **Recorded by:** `agent:claude-code-independent-review`
- **Claim supported or challenged:** Commit `e9c503b4ccc65c0907c554bd1c5fc349d2b2474b` correctly classifies parser-generated marker-only PDF output as having no meaningful extracted text and emits the existing no-extractable-text warning, while preserving extracted text, Markdown, chunks, meaningful-PDF behavior, and unrelated normalization behavior.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariant 13, and §12
- **Related ADRs/issues:** [`ISSUE-20260824T075708Z-pdf-marker-only-warning`](../ISSUES/ISSUE-20260824T075708Z-pdf-marker-only-warning.md) and parent [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md); no new ADR
- **Repository revision/state:** Reviewed target `e9c503b4ccc65c0907c554bd1c5fc349d2b2474b`, direct parent `2f5e1ad5a16bd1f1a3c1922575898bc99cd8f0bb`; `HEAD`, `origin/main`, and direct remote `main` all equal the reviewed target at capture; tracked tree clean with exactly the four recorded unrelated untracked JavaScript files.
- **Environment:** Darwin `25.3.0` arm64; system Python 3; Node `22.22.0`; npm `10.9.4`; bundled `pdfkit`/`pdf-parse` from the vendored loader. Secrets and `.env` contents were not inspected.

## Method

- **Procedure:** Read the accepted specification sections, the focused issue, the implementation evidence, the parent issue, the fixture-matrix delta, the checkpoint, and the handoff before inspecting code; read the complete `2f5e1ad..e9c503b` diff of the three product/test paths and all governance deltas; verified source/compiled parity by rebuilding; reran the loader and Python suites; probed the compiled private classifier directly against eleven edge strings; generated independent image-only and two-page text-native PDF fixtures and ran the compiled CLI and the Python adapter on them; verified scope containment, digests, remotes, and structure.
- **Exact command/input:** `git log/show/diff` including path-scoped exclusion diffs and `git diff --check`; `git ls-remote origin refs/heads/main`; `npm test`, `npm run typecheck`, `npm run build` plus `git diff --exit-code` on `dist/` in `asl/_vendor/smart-loader`; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` from the repository root; sibling `python3 scripts/validate_protocol.py`; a standard-library Markdown/local-link/HANDOFF checker; a Node probe that extracts `PDF_PAGE_MARKER` and `hasMeaningfulPdfText` from the compiled `dist/loaders/pdf.js` and evaluates eleven edge strings; `node dist/cli.js <fixture>.pdf --format json` on two freshly generated fixtures; a direct `SmartLoader().load_group(...)` Python probe; `shasum -a 256` on the four untracked files; `lsof -nP -iTCP:8765 -sTCP:LISTEN`.
- **Exit status:** All checks succeeded except the expected `lsof` absence result (exit `1`).
- **Repeatability:** Check out `e9c503b`, leave the four untracked files and ignored paths untouched, and repeat the cited commands; the probes create only temporary fixtures.

## Raw observation

- **Scope containment:** The commit changes exactly three product/test paths (`src/loaders/pdf.ts`, `dist/loaders/pdf.js`, `tests/basic.test.ts`) plus governance records. Path-scoped diffs against `PROJECT_SPEC.md`, all other `asl/` paths, `tests/test_pipeline.py`, and the loader `package.json` are empty. A fresh `npm run build` produces zero diff against the committed `dist/`, confirming source/compiled parity.
- **Classifier semantics (probed against the compiled artifact):** empty, whitespace-only, single-marker, multi-marker, markers-with-blank-lines, indented-marker, and wide-spacing-marker (`--  12  of  300  --`) inputs are all classified as not meaningful and receive the warning; meaningful text interleaved with markers is classified meaningful; unrecognized near-marker forms (`--1 of 1--`, `-- 1 of 1 -- page`, `-- 1.5 of 2 --`) are conservatively classified meaningful, matching the issue's declared narrow matcher scope and avoiding false warnings.
- **Independent end-to-end probes (freshly generated fixtures, not the implementor's):** the image-only PDF returns `text` exactly `-- 1 of 1 --`, one chunk, no errors, and warnings containing the no-extractable-text warning followed by the unchanged images-not-extracted warning; the two-page text-native PDF retains both paragraphs and both interleaved page markers with one chunk and no no-text warning. The Python `SmartLoader` probe on the image-only fixture returns the unchanged text and propagates the warning into the group Markdown.
- **Regression:** Loader suite one file/`5` tests passed in `417ms`; typecheck passed; full Python suite `76 passed in 8.71s`; sibling validator `PASS structural protocol validation (package_files=10 handoffs=2)`; `git diff --check` clean; `31` tracked Markdown files/`206` local links/`0` missing (this reviewer's regex counts one more link than the implementor's checker; the substantive result agrees); HANDOFF has exactly the five ordered sections with one nonempty Next Action; the four untracked digests match their recovery values; no port `8765` listener.
- **Record consistency:** The focused issue, implementation evidence, parent issue, matrix supersedes note, checkpoint, and handoff agree on scope, observations, and the review gate; the matrix correction is additive and preserves the prior observation's validity at its recorded revision.

## Interpretation

- **CONFIRMED:** Marker-only extraction now follows the existing no-extractable-text warning semantics, and meaningful PDF extraction — including text interleaved with page markers — is unaffected.
- **CONFIRMED:** Extracted text, Markdown, chunks, assets, metadata shape, and error behavior are preserved; the only externally observable change is the intended additional warning on the marker-only path, which propagates through the Python adapter into group Markdown.
- **CONFIRMED:** Scope is contained to the authorized slice; compiled output is genuinely derived from the committed source; no dependency, schema, parser-strategy, or other-format change occurred.
- **INFERRED:** Treating unrecognized near-marker lines as meaningful is the conservative direction for this defect class and matches the recorded matcher scope; broader boilerplate families remain owned by the parent issue.
- **UNKNOWN:** Other parser boilerplate families, real-corpus representativeness, and CAJ-family fidelity remain unverified, as already recorded.

## Limitations and residual uncertainty

- This reviewer ran on the same Darwin host class; participant labels are attributable, not authenticated.
- Independent fixtures are synthetic one-pixel-PNG and two-page text PDFs; they corroborate but do not replace representative-corpus evidence.
- `.venv` pytest remains historically unavailable and was not retried; the system-Python suite passed.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record; the immutable reviewed revision is recorded above; temporary fixtures under the system temp directory are synthetic and disposable.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record.
- **External retention risk:** `LOW`; the reviewed target is published on `origin/main`, and the checked-in tests plus generator are the durable reproduction path.
- **Supersedes / superseded by:** `NONE`

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T08:30:14Z` | `agent:claude-code-independent-review` | Reran the Python suite and digest checks after a first invocation inherited the smart-loader or sibling-repository working directory; the corrected invocations from the repository root passed. | `no tests ran` and `No such file or directory` outputs followed by `76 passed` and matching digests. |
