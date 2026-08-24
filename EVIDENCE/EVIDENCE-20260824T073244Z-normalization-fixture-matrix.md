# EVIDENCE-20260824T073244Z: Normalization Fixture Matrix

## Metadata

- **ID:** `EVIDENCE-20260824T073244Z-normalization-fixture-matrix`
- **Title:** Representative normalization fixture matrix and warning-propagation trace
- **Captured UTC:** `2026-08-24T07:32:44Z`
- **Recorded by:** `agent:codex-normalization-evidence`
- **Claim supported or challenged:** The current Smart Loader is an explicit heterogeneous-input boundary, but preservation and failure reporting vary materially by format; representative fixtures establish which structures survive, which known degradations are reported, and which are currently silent.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8, 6.1, 11 invariants 12–13, and §12
- **Related ADRs/issues:** [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md); no new ADR
- **Repository revision/state:** Product and test state at `e68f80656843f8bc82f8bdda0803398a668e21c7` on `main`; at capture, `HEAD`, cached `origin/main`, and direct remote `main` had been reconciled to that revision. The only task changes were this evidence-only diagnostic, the owning issue, and later governance records. Four unrelated untracked JavaScript files retained their recorded digests and were not read or modified.
- **Environment:** macOS `26.3` / Darwin `25.3.0` arm64; Python `3.9.6`; Node `22.22.0`; npm `10.9.4`; Pandoc `3.9`; Poppler `26.06.0`; Tesseract `5.5.2`; macOS `textutil`; and locally installed `caj2pdf`. Bundled loader dependencies and executable `dist` output were used. No secrets, generated paper content, or live provider was read.

## Method

- **Procedure:** Read the accepted requirements, owning issue, prior reconciliation evidence, TypeScript loader types/registry/all format loaders/chunker/tests, Python adapter, pipeline persistence path, and current HANDOFF. Confirmed that no tracked heterogeneous fixture corpus exists. Added the non-product [`normalization_fixture_probe.mjs`](diagnostics/normalization_fixture_probe.mjs), which generates controlled fixtures only in a temporary directory, invokes the current bundled `loadPath()` with ASL-equivalent PDF rendering settings, invokes the current Python `SmartLoader` with OCR enabled, and emits raw plus curated JSON observations. Independently validated the generated Word/PDF fixture types, DOCX media/OMML presence, and the image-only PDF's lack of text/fonts.
- **Exact command/input:** `node EVIDENCE/diagnostics/normalization_fixture_probe.mjs /private/tmp/asl-normalization-probe-20260824T073600Z`; `jq` projections over `probe-report.json`, `raw-loader-result.json`, and `python-adapter-result.json`; `file` on DOC/DOCX/PDF fixtures; `unzip -l`, `unzip -p ... word/document.xml`, `pdftotext`, `pdffonts`, and `pdfimages -list`; static trace of `asl/pipeline.py::_load_inputs`, `_write_smart_loader_manifest`, and `LoadedInputGroup.metadata()`; final `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`, bundled `npm test`, `npm run typecheck`, and sibling `python3 scripts/validate_protocol.py`.
- **Exit status:** Corrected probe and all fixture-validation commands exited `0`. `pdffonts` intentionally showed no font rows for the image-only PDF, and `pdftotext` produced only form-feed byte `0c`. Final validation passed `76` Python tests in `9.69s`, `4` loader tests in `575ms`, loader typecheck, and protocol structural validation.
- **Repeatability:** With bundled loader dependencies installed, run the exact probe command with a fresh temporary output directory. Pandoc, Poppler, Tesseract, `textutil`, and `caj2pdf` affect DOCX/PDF/DOC/CAJ observations; the report records their availability. The script does not assert future behavior or modify product files.

## Raw observation

### Corpus and result totals

- The generator created `22` fixture files: `19` with advertised extensions and `3` deliberately unsupported directory entries (`.tex`, `.rtf`, `.png`). The advertised set covers Markdown, text, JSON, CSV, HTML, PDF, DOCX, DOC, and CAJ, including controlled malformed or fidelity-stressing variants.
- Directory loading reported `19` discovered, `17` loaded, `2` failed, `0` skipped, `17` chunks, and `3` assets. Malformed PDF and DOCX were the two `load_failed` errors. The malformed DOC loaded as five characters of gibberish.
- The `17` loaded documents carried `16` warning strings: nine on the structured DOCX, one each on valid/malformed DOC and malformed JSON, and two each on the HN-outline and unknown CAJ fixtures. Valid HTML/Markdown/PDF/text/JSON/CSV, malformed HTML, duplicate-key JSON, ragged CSV, invalid-UTF-8 text, and the image-only PDF carried no warnings.
- Every loaded fixture was small enough to produce one chunk. Chunk metadata always contained file source/relative path, format, token estimate, and character offsets. No chunk contained a section, table, reference, page, or extraction-confidence field.

### Advertised-format matrix

| Format and fixtures | Preserved in this run | Degraded or dropped | Reported by the loader |
|---|---|---|---|
| Markdown — structured academic source | Front matter as text; heading hierarchy; paragraph breaks; Markdown table; figure-caption/link syntax; equation syntax; footnote; references | Metadata is not promoted into normalized metadata; the linked PNG is neither extracted nor validated | No warning |
| Text — structured text plus invalid UTF-8/NUL | Valid lines, paragraph break, table-like tabs, caption/equation/reference text | No semantic hierarchy/table model; invalid bytes became `��`; NUL was removed and its neighboring tokens concatenated | No warning for encoding replacement or NUL loss |
| JSON — nested, malformed, duplicate keys | Well-formed nested objects/arrays were pretty-printed and fenced; malformed bytes were returned raw | Duplicate-key parsing silently discarded `DUPLICATE_FIRST_MARKER`; embedded metadata/sections remain generic JSON, not normalized document fields | Parse warning only for syntactically malformed JSON; no duplicate-key warning |
| CSV — quoted multiline and ragged rows | Row/cell values; Markdown preview table; full raw CSV fenced after the preview; row counts | Preview flattened a quoted multiline cell, while the raw block retained it. Ragged rows were padded into a rectangular table | No warning for ragged column counts because parsing explicitly relaxes them |
| HTML — structured and malformed | Visible title text, headings, paragraphs, figure alt/link and caption, reference text | Citation meta author/DOI were dropped from metadata; table cells were flattened; MathML became linear text `EQUATION_MARKERE=mc2`; no asset was extracted; malformed markup was silently repaired/flattened | No warnings for either fixture |
| PDF — two-page text-native, one-page image-only, malformed | Text-native markers and PDF title/author/subject; total page count; page delimiter text; rendered page images with page numbers. Python OCR appended asset OCR text | Native headings/table/caption/equation/reference semantics became plain text; chunks have no page attribution. Image-only raw text became only `-- 1 of 1 --`, so the content marker was absent from text/chunks. OCR recovered it only into an asset field/Markdown. OCR of the valid PDF also produced a conflicting degraded equation (`E = mc42`) beside correct parsed text, with no confidence | Malformed PDF became `load_failed`; image-only PDF had no extraction warning because parser boilerplate was nonempty; OCR use/confidence was not warned |
| DOCX — Pandoc academic document with real table, embedded image, OMML equation, footnote | Heading hierarchy; paragraph text; caption; footnote text/link; references | Table cells were flattened; OMML equation was absent; embedded image was present in `word/media` but no asset was extracted; title/author were text only, not normalized metadata | Explicit Mammoth warnings for ignored OMML/styles and `error: The "buffer" encoding is not supported`; malformed DOCX became `load_failed` |
| DOC — valid legacy Word plus five-byte malformed file | Valid text and one paragraph boundary | Heading/table formatting, metadata, pages, and assets were flattened/absent; malformed bytes were accepted as gibberish | Generic warning that formatting/images may be lost on both files; no malformed/incomplete warning |
| CAJ — synthetic HN outline plus unknown bytes | HN outline titles and inline page numbers | Full document content was unavailable; unknown bytes became empty text plus a placeholder | Explicit converter/fallback warnings on both. Real CAJ, KDH, converted-PDF, and image-based HN fidelity remain unverified |

### Structure, provenance, and unsupported inputs

- **Document structure:** The common normalized object has text/Markdown/chunks/assets/warnings plus general metadata, but no semantic section, paragraph, table, figure, equation, or reference collection. Markdown/HTML/DOCX heading syntax survives for the controlled fixtures; PDF/DOC/text headings do not become hierarchy. HTML and DOCX tables demonstrably flatten even though their cell values survive.
- **Figures and captions:** Caption text survived where supplied. PDF rendering produced whole-page assets, not figure assets. Markdown/HTML image references remained textual links without extraction or warning. The DOCX contained `word/media/rId9.png`, but the current image callback returned zero assets and a warning.
- **Equations:** Markdown, plain text, JSON, PDF text, and DOC retained literal equation text where the source exposed it as text. HTML MathML lost structure/superscript semantics. DOCX OMML was dropped with an explicit warning.
- **References:** Reference marker/DOI text survived in the principal Markdown/text/JSON/HTML/PDF/DOCX/DOC fixtures, but no loader produced a normalized reference boundary or citation metadata object. CAJ preserved only its References outline entry.
- **Source/location metadata:** Every loaded document retained absolute/relative file paths, format, size, modification time, loader name, and character-offset chunks. PDF additionally retained document info and page count; PDF page assets had page numbers; CAJ page numbers survived only inside outline text. No normalized content or chunk was attributable to a page/section/table/reference location.
- **Unsupported academic/material formats:** When `.tex`, `.rtf`, and `.png` were present inside the scanned directory, none was discovered, warned, errored, or counted as skipped (`skippedFiles: 0`). Supplying each path directly instead produced `failedFiles: 1`, code `load_failed`, and `Unsupported file extension`. Directory and direct-path absence/failure semantics therefore differ.

### Downstream warning and evidence propagation

- The Python adapter's rendered group Markdown contained load errors, all per-document warnings, extracted-asset paths, and OCR text. With this `7,789`-character corpus, default prompt budgeting did not remove them.
- The image-only PDF's OCR marker was present in `asset.ocrText` and group Markdown, but the raw document text and chunk remained parser boilerplate and the document still had no warning that OCR was required. The OCR path exposes no confidence value.
- `LoadedInputGroup.metadata()` returned only label, input paths, aggregate summary, and file-level errors. It omitted all `16` document warning strings, assets, OCR text, and normalized content. `PaperPipeline._write_smart_loader_manifest()` writes only these summaries to `inputs/smart_loader.json`, and version metadata uses the same summary. Per-document warnings are therefore persisted in `inputs/<group>.md` and can enter prompts, but not in the structured Smart Loader/version metadata manifests.

### Requirement classification

| Classification | PROJECT_SPEC normalization/fidelity facet | Evidence basis |
|---|---|---|
| **Supported** | §4.8 retains an explicit ingestion layer; §11 invariant 12 | Python adapter → bundled CLI → registry routes all nine advertised formats into the common `LoadedDocument` boundary; every supported-extension fixture took that path |
| **Supported** | Basic file provenance at the normalization boundary | Every loaded document/chunk retained source/relative path and format; file size, modification time, and loader were present |
| **Partially supported** | §2.5 and §6.1 preserve meaning rather than merely extract text | Strong preservation for text-native Markdown/JSON/CSV and some headings/paragraphs, but multiple semantic structures flatten or disappear by format |
| **Partially supported** | §4.8 document metadata, hierarchy, paragraphs, tables, captions, references, equations, and page/location | Each facet survives in some routes; none is represented consistently, and the matrix demonstrates table/equation/image/metadata/location loss |
| **Partially supported** | §4.8 data sources preserve meaningful structure | Nested JSON and CSV rows remain inspectable, but duplicate JSON keys are lost and ragged CSV is normalized without warning |
| **Partially supported** | §4.8 adapter/backend handling for unusual formats | DOC and CAJ have dedicated environment-aware routes and degradation warnings, but malformed DOC is accepted as gibberish and real CAJ variants remain unverified |
| **Partially supported** | §4.8 extraction uncertainty; §11 invariant 13 | JSON syntax errors, corrupt PDF/DOCX, DOC conversion loss, DOCX OMML/image loss, and CAJ fallback are surfaced. Image-only PDF, invalid encoding/NUL, duplicate JSON key, ragged CSV, malformed HTML, and directory-ignored formats are silent |
| **Partially supported** | §4.8 downstream distinction between source absence and extraction failure; §12 warning propagation | Direct load failures and document warnings reach group Markdown/prompts, but directory-ignored files are indistinguishable from absence and structured manifests omit document warnings/OCR/fidelity state |
| **Partially supported** | §12 explicit normalization contract | The TypeScript `LoadedDocument` shape is explicit, but it has no semantic structure/fidelity status and the Python boundary consumes unvalidated dictionaries |
| **Unsupported in observed paths** | DOCX OMML equation preservation; DOCX embedded-image extraction; structured HTML/DOCX/PDF/DOC table preservation; image-only-PDF extraction warning; reporting directory-ignored unsupported files | Controlled fixtures directly demonstrate absence or flattening; warnings exist only for the DOCX losses |
| **Still unverified** | Full §10–12 compatibility/completion and representative real-corpus fidelity | No owner corpus, real CAJ/KDH conversion, non-macOS DOC fallback, OCR confidence/accuracy study, large-document chunk-boundary study, encrypted PDF, complex/nested table, tracked formula semantics, or broad accessibility corpus was exercised |

## Interpretation

- **CONFIRMED:** §4.8 remains **partially implemented**, and §11 invariant 12 remains **implemented/supported**: heterogeneous advertised formats do pass through an explicit normalization layer.
- **CONFIRMED:** §11 invariant 13 must be corrected from the earlier **implemented** classification to **partially implemented**. Warning fields and several real failure paths work, but known controlled degradation is also silently discarded or presented as content.
- **CONFIRMED:** §12's explicit semantic-normalization and downstream-fidelity-warning completion criteria are not satisfied by the current evidence. The existing envelope is useful but not a consistent semantic/fidelity contract.
- **CONFIRMED:** The smallest directly evidenced fail-silent product gap is the image-only PDF path: `pdf-parse` page-marker boilerplate defeats the empty-text check even though ASL's later OCR recovers text only into an asset annotation.
- **INFERRED:** Reusing the existing warning field to detect page-marker-only PDF extraction is a smaller next slice than selecting a canonical normalized-evidence schema, redesigning assets, or changing capability negotiation. This inference authorizes no code change in this evidence pass.
- **UNKNOWN:** Which broader fidelity thresholds, normalized structures, parser strategies, or figure/equation guarantees the owner wants remains an open §14 decision.

## Limitations and residual uncertainty

- Fixtures are controlled and academic-shaped, not a statistically representative owner corpus. Their markers make preservation/loss observable but do not measure semantic usefulness or OCR accuracy at scale.
- DOC behavior is macOS `textutil`-specific. CAJ evidence covers an HN outline fallback and unknown input only; installed converter/library behavior and real documents can differ.
- All loaded documents fit one chunk, so source-level structure and metadata were assessed, but long-document section-aware chunking remains unverified.
- Tesseract recovered the scanned marker in this high-contrast fixture. No confidence is exposed, and OCR produced a wrong equation on a text-native rendered page (`mc42`), so OCR correctness is not established.
- Temporary JSON artifacts are subject to ordinary `/private/tmp` cleanup. The durable diagnostic source and inline observations allow regeneration; the report hashes below identify this run.
- The diagnostic is evidence support, not an executable product contract. No loader expectation or future architecture was added to the test suite.

## Integrity and provenance

- **Artifact location:** Durable generator at [`EVIDENCE/diagnostics/normalization_fixture_probe.mjs`](diagnostics/normalization_fixture_probe.mjs); ephemeral corrected run at `/private/tmp/asl-normalization-probe-20260824T073600Z/`.
- **Artifact digest:** SHA-256 `873c3c9d662cfc46956ddfb211e8e1d459066f2dc5aed15156232bb878d9998d` for the generator; `5274dde711b98173c3cccbfa36c89ed20256a1be481ff4b430b19ea0d5cab08e` for `probe-report.json`; `968c56510d96c90cc72ca469113d4791950529b66491a4082a677679cefa638f` for `raw-loader-result.json`; `68c041f70e783a64c61d96a8290b4952f354b4911c805d563346018f34981849` for `python-adapter-result.json`.
- **External retention risk:** `HIGH` for temporary JSON/binary fixtures; no unique owner data is present. The committed generator and this evidence record are the durable reproduction path.
- **Supersedes / superseded by:** Adds representative evidence to [`EVIDENCE-20260824T024051Z-spec-reconciliation`](EVIDENCE-20260824T024051Z-spec-reconciliation.md); it does not supersede its unrelated classifications.

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T07:32:44Z` | `agent:codex-normalization-evidence` | The initial `2026-08-24T07:31:18Z` diagnostic run was not used for HTML/DOCX marker or Python OCR conclusions. The checker treated Turndown's escaped underscores as missing markers, and the installed Tesseract could not open rendered images through macOS's `/tmp` symlink alias. The diagnostic now compares unescaped marker text and canonicalizes the output path with `realpath`; the corrected `/private/tmp` run passed and is the evidence identified above. | Direct raw Markdown showed the markers with `\_`; direct Tesseract invocation failed through `/tmp` but succeeded through `/private/tmp`; the corrected run reports preserved HTML/DOCX markers and `markdownHasOcrText: true`. Product files were unchanged. |
