# EVIDENCE-20260826T033558Z: Attributable Unsupported Directory Inputs

## Metadata

- **ID:** `EVIDENCE-20260826T033558Z-directory-unsupported-reporting`
- **Title:** Unsupported files encountered during directory loading are reported as non-failing skips
- **Captured UTC:** `2026-08-26T03:35:58Z`
- **Recorded by:** `agent:codex-directory-unsupported-reporting`
- **Claim supported or challenged:** Files enumerated inside a supplied directory but unsupported by the current registry can be made attributable through the existing error/summary contract without adding format support, changing supported normalized content, treating skips as failures, or changing direct unsupported-file behavior.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.5, 4.8 extraction uncertainty, 6.1, 11 invariants 12–13, and §12
- **Related ADRs/issues:** Focused [`ISSUE-20260826T032834Z-directory-unsupported-reporting`](../ISSUES/ISSUE-20260826T032834Z-directory-unsupported-reporting.md), parent [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md), and prior [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md); no new ADR
- **Repository revision/state:** Candidate implementation tree based directly on published and independently approved governance-closure revision `a763528d2c26509a7dcd9cdf4d37a1e6698187bc`; the containing implementation/governance commit is the intended immutable review target. Before editing, `a763528` was the sole local-ahead governance-only closure, was published, and local `HEAD`, cached `origin/main`, and direct remote `main` were reconciled at that revision with ahead/behind `0/0`. Four unrelated untracked JavaScript files remained outside the task and unchanged.
- **Environment:** macOS `26.3` / Darwin `25.3.0` arm64; Python `3.9.6`; Node `22.22.0`; npm `10.9.4`; Vitest `4.1.8`; Pandoc `3.9`; Poppler, Tesseract, `textutil`, and `caj2pdf` available to the complete diagnostic; bundled dependency/runtime paths.

## Method

- **Procedure:** Read protocol, specification, current handoff, parent normalization issue, fixture evidence, loader registry/types/source/compiled output/tests, Python adapter, Git history/status/remotes, and the independently approved closure. Published that closure only after confirming its scope and review disposition. Reproduced a mixed Markdown/TeX/RTF/PNG directory before editing, contrasted it with direct TeX loading, and traced the omission to `scanDirectory()` filtering after `fast-glob` enumeration. Partitioned that existing enumeration into supported paths and existing-shape `LoadError` diagnostics, counted unsupported entries as discovered/skipped rather than failed, and made `--fail-on-error` consult `failedFiles`. Added focused TypeScript and Python downstream regressions, rebuilt `dist`, repeated the exact controlled probes, regenerated the established `22`-fixture matrix, mechanically compared supported observations and direct unsupported semantics to the previously approved candidate report, and ran full validation.
- **Exact command/input:** `node asl/_vendor/smart-loader/dist/cli.js /private/tmp/asl-unsupported-directory-before-20260826T032000Z --format json` with and without `--fail-on-error`; direct `unsupported.tex --fail-on-error`; direct Python `SmartLoader` probe with OCR/page rendering disabled; bundled `npm test`, `npm run typecheck`, and `npm run build`; `python3 -m pytest -q -p no:cacheprovider tests/test_pipeline.py::test_smart_loader_reports_unsupported_directory_inputs_downstream`; `node EVIDENCE/diagnostics/normalization_fixture_probe.mjs /private/tmp/asl-normalization-probe-20260826T033400Z`; a Node normalized comparison against `/private/tmp/asl-normalization-probe-20260825T024600Z/probe-report.json`; `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`; sibling `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_protocol.py`; `git diff --check`.
- **Exit status:** Corrected product/evidence commands exited `0`, except the deliberate direct unsupported-file `--fail-on-error` probe, which retained exit `1`. The focused Python test passed `1`; the full Python suite passed `77`; the loader suite passed `7`; typecheck/build and protocol validation passed. Two failed instrumentation invocations are preserved under Corrections and were not used as product conclusions.
- **Repeatability:** The checked-in tests generate their own fixtures. With bundled dependencies installed, run the complete diagnostic at a fresh absolute temporary path. External DOC/PDF/CAJ tools can affect unrelated matrix observations but not the focused Markdown/TeX/RTF/PNG tests.

## Raw observation

### Published behavior and bounded change

- At published `a763528`, a directory containing `supported.md`, `unsupported.tex`, `unsupported.rtf`, and `figure.png` returned `1` discovered, `1` loaded, `0` skipped, `0` failed, and no error. The supported document/chunk was present; all three unsupported names were absent. Adding `--fail-on-error` still exited `0`. The JSON SHA-256 was `8b0a1983aeab4c811dae1659deaeb6104621a82ccd043007e2b7768bffe0b131`.
- At the same baseline, loading `unsupported.tex` directly with `--fail-on-error` exited `1`, returned one `load_failed` diagnostic with exact source path and `Unsupported file extension: .tex`, and had JSON SHA-256 `ef2e7e8db44957c3eddac17588df533579bb64784ba2a4c8fadf9a8b6c505995`. The Python mixed-directory adapter returned `1/1/0/0`, no errors, preserved the supported marker, and omitted all unsupported names.
- The candidate keeps registry and traversal options unchanged. For each non-ignored regular file already enumerated by the existing scan, a supported extension follows the prior load path; an unsupported extension produces code `unsupported_file`, the absolute `sourcePath`, and reason `Unsupported file extension: <extension>`. Unsupported entries contribute to `discoveredFiles` and `skippedFiles`, not `failedFiles`.
- The same mixed directory now exits `0` with or without `--fail-on-error`, returns `4/1/3/0`, and reports exact diagnostics for PNG, RTF, and TeX. Its JSON SHA-256 is `7dbcf4d3ee2f529a26b23dbd8bcf28248b56c92f09eca9fa93544984cb582552`; its supported document/chunk payload SHA-256 is `4a5c15554f3a0b43c793a297475193eaf2bf00f231ed76fc3f9f1dccb076f935`. The direct TeX result remains byte-identical at SHA-256 `ef2e7e8d...` and exit `1`.
- The Python adapter now aggregates `4/1/3/0`, exposes all three diagnostics in metadata, and renders every skipped source path and reason while preserving the supported marker. No Python product change was required; one integration test makes that downstream propagation executable.

### Complete fixture-matrix delta

- The regenerated corpus contains the same `22` fixtures and now reports `22` discovered, `17` loaded, `3` skipped, `2` failed, `17` chunks, and `3` assets. The error list contains exactly three `unsupported_file` skips plus the existing malformed-DOCX and malformed-PDF `load_failed` records.
- All `17` supported curated document observations compare equal to the prior post-UTF-8/NUL report after removing only absolute source paths and modification timestamps. Both normalized sets have SHA-256 `8ce4d9fe0e0ae9f2326508d5d73d152e3f9b91b145f4c808c5e0d0ca2aba3496`.
- Direct unsupported-file summaries, reasons, and codes also compare equal after removing absolute paths; both normalized sets have SHA-256 `1842078ea6c1ed5b887fca57574bb4d668c80ab1f6df5fe3f78ed3636e2e6d3c`.
- Existing document warning count remains `19`. Python adapter metadata carries the new `22/17/3/2` summary and five attributable records; rendered Markdown still contains warnings, load diagnostics, and OCR text.

### Executable verification

- Focused downstream Python regression: `1 passed in 0.32s`.
- Full bundled loader initially passed one file and `7` tests in `555ms`; after tightening exact-path assertions and adding compiled-CLI exit/direct-file regression assertions, the final rerun passed the same `7` tests in `890ms`; typecheck passed.
- Full Python suite: `77 passed in 8.06s`.
- Rebuilding compiled output retained SHA-256 `bfbef3fc5f3e572a196138d5b8bd2cea2e7626c89bada7df521ef3264eea92be` for `dist/index.js` and `92bac7105ad23ae9b2afc53dfc9ed64b69b4157052394a94a7213f26822820b9` for `dist/cli.js` before and after the repeat build.
- Sibling protocol validator returned `PASS structural protocol validation (package_files=10 handoffs=2)`. `git diff --check` emitted no output and exited `0` before governance reconciliation.
- Final pre-commit audit found `37` Markdown files, `272` local links, and `0` missing; exactly five ordered HANDOFF sections and one nonempty Next Action; all seven adopted protocol byte mappings matched source revision `58fa281`; no governance symlink; exactly `12` authorized task paths (`6` product/test and `6` governance/evidence); protected specification/dependency/unrelated product scope clean; historical handoff SHA-256 `43200c...`; no port `8765` listener (expected `lsof` exit `1`); and all four unrelated untracked digests unchanged.

## Interpretation

- **CONFIRMED:** Unsupported non-ignored regular files already encountered by directory enumeration no longer disappear silently; existing JSON and Python diagnostics identify each path and reason.
- **CONFIRMED:** Unsupported directory entries are non-failing skips. Supported files continue through the prior code path and `--fail-on-error` remains reserved for actual failures.
- **CONFIRMED:** Direct unsupported-file behavior, supported curated document observations, dependencies, schemas, advertised format support, ignore/hidden/symlink policy, and existing warning behavior are unchanged.
- **CONFIRMED:** The correction closes only the fixture matrix's directory-ignored unsupported-format observation. Invariant 13 and §§10–12 remain partially implemented because other recorded silent degradation and broader semantic-fidelity gaps remain.
- **INFERRED:** Reusing the error list with distinct `unsupported_file` code and skipped/failed counters is the smallest compatible attributable state available in the current result contract.
- **UNKNOWN:** Whether intentionally ignored globs, hidden files, symlinks, or future richer fidelity state should be reported remains outside this child and requires separate authority/evidence.

## Limitations and residual uncertainty

- The focused fixtures are synthetic and cover Markdown plus TeX, RTF, and PNG examples. They do not establish support or extraction quality for those unsupported formats.
- CLI `markdown` serialization continues to emit loaded documents only; the application adapter consumes default JSON and renders the new diagnostics. Redesigning alternate serialization is outside this child.
- The existing shared list is named `errors`, and Python Markdown labels it `Load errors`; code plus separate `skippedFiles`/`failedFiles` counters distinguish the new non-failing diagnostics. A typed fidelity/resource-state redesign remains owner-gated.
- Independent review of the containing commit remains required before the focused issue can close.

## Integrity and provenance

- **Artifact location:** Product/tests in the containing commit; ephemeral exact before/after fixture at `/private/tmp/asl-unsupported-directory-before-20260826T032000Z`; complete candidate run at `/private/tmp/asl-normalization-probe-20260826T033400Z/`; durable generator at [`EVIDENCE/diagnostics/normalization_fixture_probe.mjs`](diagnostics/normalization_fixture_probe.mjs).
- **Artifact digest:** SHA-256 `6db789c718e3b78d0af3aa8e0bb0e0f6f5cae0933a952de42aa6087341c41759` (`src/index.ts`); `bfbef3fc5f3e572a196138d5b8bd2cea2e7626c89bada7df521ef3264eea92be` (`dist/index.js`); `5e9eb33f4964660c13f0ef7354e0a6290b3bbcde98476e9522c6572482256d05` (`src/cli.ts`); `92bac7105ad23ae9b2afc53dfc9ed64b69b4157052394a94a7213f26822820b9` (`dist/cli.js`); `2121f518810277ff06e20703c0ce319c94c4e01f282cf0bf9a3df82544e4ba90` (bundled test); `207952bd6c2cae75e9672fc571c427b58697f5ec8d0114fb4becdc465c681713` (Python test file); `873c3c9d662cfc46956ddfb211e8e1d459066f2dc5aed15156232bb878d9998d` (diagnostic generator); `d04631ccef7e115c45f7afdfc540b7c29213ad6deb4518ab39a8c7fad5326151` (`probe-report.json`); `00d385332fdb9f11e913e0afbfe9e9a526509c8d43d99a020613cb782acc68e7` (`raw-loader-result.json`); `1cd914855782d54a5dfe5f19446179e6fc6c55a1187d78c216cd46f8d0fd20` (`python-adapter-result.json`).
- **External retention risk:** `HIGH` for temporary generated reports/fixtures; all inputs are synthetic, and checked-in tests/generator plus the inline observations provide durable reproduction.
- **Supersedes / superseded by:** Supersedes only the prior matrix's current-state claim that TeX, RTF, and PNG encountered during directory loading disappear without counts or diagnostics. That observation remains valid at its captured revision. It does not supersede any other normalization finding.

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-26T03:27:17Z` | `agent:codex-directory-unsupported-reporting` | The first combined baseline shell probe stopped after its mixed-directory observations because it assigned zsh's read-only `status` parameter. Direct-file and Python observations come only from the corrected invocation. | Corrected probe at `2026-08-26T03:28:34Z` produced the direct JSON SHA-256 and Python summary recorded above; product state was unchanged. |
| `2026-08-26T03:31:36Z` | `agent:codex-directory-unsupported-reporting` | The first post-change test invocation added Jest's unsupported `--runInBand` option to Vitest and failed before collection. | Canonical `npm test` immediately passed all `7` tests; no failed test result was treated as product evidence. |
