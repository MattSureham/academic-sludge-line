# ISSUE-20260824T024051Z: Establish Normalization Fidelity and Capability-Aware Coverage

## Metadata

- **ID:** `ISSUE-20260824T024051Z-normalization-capability-coverage`
- **Title:** Establish normalization fidelity and capability-aware model coverage
- **Status:** `INVESTIGATING`
- **Severity:** `MEDIUM`
- **Owner:** `human:technical-owner`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Updated UTC:** `2026-08-25T02:47:29Z`
- **Requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§2.4–2.5, 4.8–4.10, 6.1, 6.4, 11 invariants 10–13, and §14
- **ADRs:** `NONE`
- **Evidence:** [`EVIDENCE-20260824T024051Z-spec-reconciliation`](../EVIDENCE/EVIDENCE-20260824T024051Z-spec-reconciliation.md), [`EVIDENCE-20260824T033159Z-governance-independent-review`](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md), [`EVIDENCE-20260824T073244Z-normalization-fixture-matrix`](../EVIDENCE/EVIDENCE-20260824T073244Z-normalization-fixture-matrix.md), [`EVIDENCE-20260824T080248Z-pdf-marker-only-warning`](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md), [`EVIDENCE-20260824T083014Z-pdf-marker-warning-review`](../EVIDENCE/EVIDENCE-20260824T083014Z-pdf-marker-warning-review.md), and candidate [`EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning`](../EVIDENCE/EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning.md)
- **Milestone:** `NONE`

## Problem

The bundled smart-loader is an explicit heterogeneous-input boundary with structured output and warnings, but its narrow test suite and controlled matrix do not establish semantic fidelity or warning propagation across every advertised format. Separately, model presets already carry descriptive capability tags, but stage contracts and route execution do not consume those tags to express or negotiate workflow requirements. Capability representation therefore exists while capability-aware execution remains incomplete.

## Evidence or reproduction

Inspection covered the Python smart-loader adapter, bundled TypeScript registry/loaders/types/tests, provider clients, preset catalog, role routing, CLI configuration, and pipeline branches. The published matrix baseline passed `4` tests and typecheck; the independently approved PDF slice raised this to `5`; the focused invalid-UTF-8/NUL candidate passes `7` tests plus typecheck/build. `ModelPreset` and `LocalModelPreset` contain provider-independent capability tuples, and `catalog_payload()` exposes a list for every discovered model; `ModelSpec`, `ModelRoutes`, and pipeline stages neither carry stage requirements nor negotiate execution from those tags.

The evidence-only fixture matrix covers all nine advertised formats plus controlled malformed/unsupported cases. It confirms strong preservation for text-native Markdown/JSON/CSV, mixed structural preservation for HTML/PDF/DOCX/DOC/CAJ, and both reported and silent degradation. The page-marker-only PDF gap is independently fixed. The current focused candidate adds attributable warnings when the plain-text route replaces invalid UTF-8 or removes NUL while retaining its normalized content. DOCX OMML and its embedded image are dropped with warnings; HTML/DOCX tables flatten; duplicate JSON keys, ragged CSV, malformed HTML, and directory-ignored TeX/RTF/image inputs still lose information or reporting silently. Python group Markdown carries warnings/errors/OCR, while structured Smart Loader/version metadata retains only aggregate errors and omits per-document warnings.

## Expected behavior

The normalization boundary preserves useful structure and exposes known degradation, while workflow stages request relevant model capabilities rather than depending on provider names where practical. The specification leaves parser strategy and static-versus-runtime capability discovery open.

## Assumptions

- **CONFIRMED:** Markdown/text/JSON/CSV/HTML/PDF/CAJ/DOCX/DOC routes exist through the explicit loader boundary.
- **CONFIRMED:** At the published matrix baseline, a controlled `22`-file fixture corpus produced `19` advertised-extension discoveries, `17` loaded documents, `2` load errors, `16` per-document warning strings, and `3` PDF page assets. The approved PDF warning raised warning strings to `17`; the current candidate preserves all other totals and raises warnings to `19` only by attributing invalid-UTF-8 replacement and NUL removal.
- **CONFIRMED:** Provider-independent role selection and local endpoint support exist independently of capability modeling.
- **CONFIRMED:** Model preset/catalog records already expose descriptive capability metadata.
- **CONFIRMED:** Existing warning/error fields are a useful contract seed but do not satisfy invariant 13 across the observed paths; the reconciliation classification is corrected to partially implemented.
- **UNKNOWN:** Required fidelity thresholds, canonical normalized structure, and whether existing static tags should remain descriptive or participate in runtime requirement negotiation.

## Investigation and decision

The normalization evidence-first slice is complete. It selected no schema, parser strategy, dependency, fidelity threshold, or capability architecture. Focused child [`ISSUE-20260824T075708Z-pdf-marker-only-warning`](ISSUE-20260824T075708Z-pdf-marker-only-warning.md) reused the existing warning shape and is `CLOSED` after fresh independent `APPROVED`. User-selected child [`ISSUE-20260825T024242Z-invalid-utf8-nul-warning`](ISSUE-20260825T024242Z-invalid-utf8-nul-warning.md) now has the smallest warning-only candidate for the matrix's plain-text encoding/NUL case and is in independent `REVIEW`. DOCX assets, unsupported directory entries, duplicate JSON/CSV/HTML cases, canonical normalization structure, and capability negotiation remain separate and unchanged.

Separately, later capability work may use the existing preset tags as evidence and propose the minimum stage-requirement/execution contract needed by one demonstrated workflow branch. Owner acceptance is still needed before committing to a new normalization schema or durable capability-negotiation architecture.

## Change

- **Files or components:** This parent issue owns the diagnostic [`normalization_fixture_probe.mjs`](../EVIDENCE/diagnostics/normalization_fixture_probe.mjs) and broader governance evidence. Focused children own their bounded loader source/build output, tests, and implementation evidence.
- **Behavior changed:** Parent evidence gathering changed none. The approved PDF child surfaces marker-only extraction; the current plain-text child candidate surfaces invalid-UTF-8 replacement and NUL removal through existing warnings without changing normalized content or schema.
- **Out-of-scope work deliberately excluded:** Input repair; new parser dependencies; loader/schema redesign; DOCX assets/equations; unsupported-directory reporting; duplicate JSON, ragged CSV, malformed HTML, other silent cases; capability negotiation; provider refactor; or generated paper changes.
- **Rollback or recovery:** Revert the relevant focused child's containing commit; neither requires data or dependency migration. The prior evidence/governance commit remains independently reversible.

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| Potential normalized-evidence contract and capability-requirement/execution contract | Address two explicit but currently incomplete boundaries | Existing tests and descriptive tags prove only a narrow baseline | This issue owns evidence gathering and later authority decisions |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm test` in `asl/_vendor/smart-loader` | One file and four tests passed; exit `0` | Repository-recovery evidence | Small suite; not a format-fidelity matrix |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `npm run typecheck` in `asl/_vendor/smart-loader` | Passed; exit `0` | Repository-recovery evidence | Type correctness does not prove extraction fidelity |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Static provider/capability trace | Initially recorded no general capability representation | Reconciliation evidence | Superseded by the independent catalog/preset trace below |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | Direct `catalog_payload()` inspection plus static trace through preset, route, and pipeline types | Capability lists exist for all discovered presets; no stage requirement or execution negotiation consumes them; exit `0` | Independent review evidence | Static/descriptive coverage does not establish real-provider capability behavior |
| `2026-08-24T07:32:44Z` | `agent:codex-normalization-evidence` | `node EVIDENCE/diagnostics/normalization_fixture_probe.mjs /private/tmp/asl-normalization-probe-20260824T073600Z` | Exit `0`; `19` advertised-extension fixtures discovered, `17` loaded, `2` failed, `16` document warnings, `3` assets; raw and Python-adapter observations recorded | Normalization fixture evidence | Controlled corpus; real CAJ/KDH, non-macOS DOC, large documents, and OCR confidence remain unverified |
| `2026-08-24T07:38:18Z` | `agent:codex-normalization-evidence` | `file`, DOCX `unzip`/XML probes, `pdftotext`, `pdffonts`, and `pdfimages -list` against generated fixtures | Exit `0`; valid legacy DOC/DOCX/PDF types confirmed; DOCX contains media and OMML; scan PDF contains one image, no fonts, and no extractable text | Normalization fixture evidence | Validates fixture construction, not real-corpus representativeness |
| `2026-08-24T07:41:59Z` | `agent:codex-normalization-evidence` | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`; bundled `npm test`; `npm run typecheck`; sibling `python3 scripts/validate_protocol.py` | Exit `0`: `76 passed in 9.69s`; one loader file/`4` tests passed in `575ms`; typecheck passed; protocol validator `PASS` | This issue, HANDOFF, and fixture evidence | Suites do not assert the new observations because this slice deliberately did not change product tests/contracts |
| `2026-08-24T07:47:00Z` | `agent:codex-normalization-evidence` | Post-commit `git show --check`, scoped product/spec/test diff, refs/status/digests/port check, and standard-library Markdown/HANDOFF validation | Exit `0` except expected no-listener `lsof` exit `1`; six evidence/governance/diagnostic paths only, no product/spec/test diff; `30` Markdown files/`180` local links/`0` missing; five HANDOFF sections/one Next Action; four unrelated digests unchanged | Containing evidence commit and HANDOFF | Direct remote remains at published parent; local evidence commit intentionally unpushed |
| `2026-08-24T08:02:48Z` | `agent:codex-pdf-marker-warning` | Focused PDF regression, compiled CLI/Python adapter probes, full `22`-fixture rerun and normalized before/after comparison, `76` Python tests, `5` loader tests, typecheck/build, protocol validator, and `git diff --check` | Exit `0` after correcting only an invalid embedded test PNG: marker-only warning added; meaningful PDF and all other curated document observations unchanged | [Focused implementation evidence](../EVIDENCE/EVIDENCE-20260824T080248Z-pdf-marker-only-warning.md) | Focused child is independently approved and closed; broader known silent cases remain open |
| `2026-08-25T02:47:29Z` | `agent:codex-utf8-nul-warning` | Published-baseline reproduction; focused regressions; compiled CLI/Python probes; complete `22`-fixture rerun and normalized comparison; `76` Python tests; `7` loader tests; typecheck/build; protocol validator; `git diff --check` | Exit `0`: invalid-UTF-8/NUL content unchanged plus exactly two warnings; valid text and all `16` other curated documents unchanged; totals `19/17/2/17/3`, warnings `17` → `19` | [Focused implementation evidence](../EVIDENCE/EVIDENCE-20260825T024729Z-invalid-utf8-nul-warning.md) | Focused child remains in independent `REVIEW`; other known silent cases remain open |

## Pipeline state (optional)

NOT APPLICABLE.

## Self-review

- **Participant:** `agent:codex-recovery`
- **Reviewed UTC:** `NOT APPLICABLE`
- **Reviewed repository state:** `NOT APPLICABLE`
- **Scope and authority references:** `NOT APPLICABLE`
- **Checks and evidence reviewed:** `NOT APPLICABLE`
- **Findings and corrections:** `NOT APPLICABLE`
- **Limitations:** No implementation exists to review
- **Residual risks:** Advertised format coverage and capability behavior remain incompletely evidenced
- **Outcome:** `NOT_APPLICABLE`

## Independent review rounds

- **Required:** `YES` — future normalization or capability contracts create cross-module commitments and may add dependencies.

No review round has been recorded.

## Blocker

- **Blocked from:** `NOT BLOCKED`
- **Blocker:** `NONE`; the evidence slice is complete, and the narrow existing-warning-field child fix was independently approved and closed without selecting the owner-gated semantic schema. Broader normalization/capability architecture remains owner-gated.
- **Unblock owner:** `NONE`
- **Unblock condition:** `NONE`

## Residual uncertainty

- Controlled fixtures establish current behavior, but representative owner-corpus thresholds and real CAJ/KDH/non-macOS DOC fidelity remain unknown.
- Current normalized objects do not consistently preserve semantic structure or fidelity state; which durable schema/threshold to adopt remains owner-gated.
- Per-document warnings/OCR are absent from structured Smart Loader/version metadata even though group Markdown carries them.
- Existing preset capability tags are descriptive only; no concrete workflow stage states or negotiates capability requirements independently of provider configuration.
- The invalid-UTF-8/NUL warning candidate still requires fresh independent review before its focused issue can close.

## Activity history

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | `NONE` | `OPEN` | Recorded partial normalization evidence and absent capability-aware execution. |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | `OPEN` | `OPEN` | Corrected capability coverage: descriptive preset/catalog metadata exists, while capability-requirement negotiation and execution remain missing. |
| `2026-08-24T07:26:24Z` | `agent:codex-normalization-evidence` | `OPEN` | `INVESTIGATING` | Began the HANDOFF-authorized evidence-only fixture matrix. Scope is limited to observing current normalization and warning propagation; no loader, test, dependency, schema, or capability-execution change is authorized. |
| `2026-08-24T07:40:29Z` | `agent:codex-normalization-evidence` | `INVESTIGATING` | `INVESTIGATING` | Completed and recorded the controlled matrix, corrected invariant 13 to partial through additive evidence, and identified page-marker-only PDF warning detection as the smallest later slice. No product/test behavior or architecture changed. |
| `2026-08-24T08:02:48Z` | `agent:codex-pdf-marker-warning` | `INVESTIGATING` | `INVESTIGATING` | Implemented and verified the separately scoped page-marker-only warning candidate under agent authority; the child issue is in independent review. Other normalization/capability evidence, decisions, and behavior remain unchanged. |
| `2026-08-24T08:30:14Z` | `agent:claude-code-independent-review` | `INVESTIGATING` | `INVESTIGATING` | Fresh independent review of the page-marker-only warning commit `e9c503b` recorded `APPROVED` with zero open material findings and closed the focused child issue. The remaining silent normalization cases, canonical schema, and capability negotiation stay open here. |
| `2026-08-25T02:47:29Z` | `agent:codex-utf8-nul-warning` | `INVESTIGATING` | `INVESTIGATING` | Implemented and verified the separately scoped invalid-UTF-8/NUL warning candidate under agent authority; the focused child is in independent review. Parser output, schemas, dependencies, unrelated formats, and other matrix cases remain unchanged. |

## Closure checklist

- [x] Expected behavior is tied to a higher-authority source.
- [ ] The change or resolution is recorded.
- [x] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [x] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies. (Not applicable.)
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [ ] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [x] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [x] Residual uncertainty is absent or explicitly owned.
- [ ] HANDOFF reflects the resulting current state and exactly one next action.
