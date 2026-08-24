# EVIDENCE-20260824T033159Z: Independent Governance and Recovery Review

## Metadata

- **ID:** `EVIDENCE-20260824T033159Z-governance-independent-review`
- **Title:** Independently review and repair the first-adoption governance/recovery baseline
- **Captured UTC:** `2026-08-24T03:31:59Z`
- **Recorded by:** `agent:codex-governance-review`
- **Claim supported or challenged:** Candidate baseline `e9ef291a0be124a1ea1ad782c6bb307a486f2b18` correctly installs the sibling protocol and preserves tracked history, but its requirement reconciliation, issue escalation, and pre-adoption specification-provenance confidence require three material governance corrections before approval.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§4.3–4.4, 4.9–4.10, and 10–13
- **Related ADRs/issues:** [`ADR-20260824T024051Z-protocol-adoption`](../ADR/ADR-20260824T024051Z-protocol-adoption.md), [`ISSUE-20260824T024051Z-protocol-adoption-recovery`](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md), [`ISSUE-20260824T024051Z-review-routing-guidance`](../ISSUES/ISSUE-20260824T024051Z-review-routing-guidance.md), and [`ISSUE-20260824T024051Z-normalization-capability-coverage`](../ISSUES/ISSUE-20260824T024051Z-normalization-capability-coverage.md)
- **Repository revision/state:** Immutable reviewed target `e9ef291a0be124a1ea1ad782c6bb307a486f2b18`, direct parent `387bffe632ba2d53c14aa59de93bd645935d9a94`, with exactly four preserved unrelated untracked JavaScript files; sibling protocol revision `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`.
- **Environment:** Darwin `25.3.0` arm64; Python `3.9.6`; Node `v22.22.0`; npm `10.9.4`; Git `2.50.1 (Apple Git-155)`. Secrets and `.env` contents were not inspected.

## Method

- **Procedure:** Read the immutable sibling package and normative protocol; inspect the accepted specification before implementation; review every candidate governance path and the complete parent-to-target diff; independently trace reviewer guidance, capability metadata/execution, version acceptance, scoring, evidence loading, and discovery; reproduce critical diagnostics; rerun executable and structural checks; verify remote refs, file digests, ignored samples, and historical Git objects; actively search for unsupported authority, provenance, and escalation claims.
- **Exact command/input:** Principal commands included `git status --short --branch`, `git log/show/diff/diff-tree`, `git ls-remote`, `git ls-tree`, `git fsck --full --no-reflogs --unreachable`, `rg -n`, `sed -n`, `shasum -a 256`, explicit `cmp` calls against `git show 58fa281:protocol/...`, `find`, `lsof`, `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`, `.venv/bin/python -m pytest -q -p no:cacheprovider`, `npm test`, `npm run typecheck`, the sibling `scripts/validate_protocol.py`, a standard-library Markdown/link/HANDOFF checker, isolated `accepted_version()` and `_score_metadata()` calls, and direct `catalog_payload()` inspection.
- **Exit status:** Successful except the explicitly recorded unavailable or corrected invocations below.
- **Repeatability:** Check out `e9ef291`, leave ignored/untracked state untouched, compare product behavior at parent `387bffe`, read `PROJECT_SPEC.md` before implementation, and repeat the cited commands. The original untracked pre-adoption specification is not present as a repository object, so its exact historical bytes are not independently reproducible from this repository.

## Raw observation

### Protocol adoption and scope

- Target `e9ef291` is a direct child of `387bffe`; its twenty changed paths are governance/documentation paths only. No `asl/`, executable test, generated paper, environment, secret, or unrelated JavaScript path is in the commit.
- The sibling repository and its remote-tracking `main` resolve to `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`; its immutable `protocol/` tree contains exactly ten regular Markdown files and no symlinks. The source validator reports `PASS structural protocol validation (package_files=10 handoffs=2)`.
- Explicit immutable comparisons pass for `BOOTSTRAP.md`, source `README.md` to `PROTOCOL_GUIDE.md`, `PROMPTS.md`, `EXAMPLE.md`, and the ADR/ISSUES/EVIDENCE templates. The application README retains its parent bytes plus the required navigation links.
- The target Markdown/link check reports no missing local targets, and `HANDOFF.md` contains exactly the five ordered operational sections with one nonempty Next Action.
- The project-owned `PROJECT_SPEC.md`, `HANDOFF.md`, and `HUMAN_CHECKPOINT.md` are deliberate owner-approved collision merges rather than byte-identical templates. The accepted adoption ADR records that authority; repository participant labels are attributable but not cryptographically authenticated.

### Recovery and historical preservation

- `git show 387bffe:HANDOFF.md` reproduces SHA-256 `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`; `git show 387bffe:README.md` reproduces `c7986af3a9475a371a4f17d0cb30bc623cf25256c146770ad088c8e14e8dc514`.
- The four unrelated untracked files reproduce their recorded SHA-256 values: `b3647d38...` (`codex-app-server-agent.js`), `6f644792...` (`codex-feature-definitions.js`), `99bbbdcb...` (`provider-model.js`), and `086e35d1...` (`provider-registry.js`). Inspection confirms they belong to a different provider/agent codebase, not ASL.
- The ignored `papers/` sample still contains five immediate projects and sixteen `vN` directories; all five accepted pointers resolve, and three projects have a later chronological candidate than the accepted pointer. This remains mutable local evidence only.
- The current accepted specification is complete repository authority. Its adoption record says it preserves the behavioral text presented at adoption; that pre-adoption equality and its claimed SHA-256 `3717cd4727b1eba17aa35c6605b80ba071095eb64b6da5994dff1468ff324033` cannot be independently reproduced: `387bffe` contains no `PROJECT_SPEC.md`, no reachable or unreachable Git blob matches that SHA-256, and the earlier evidence does not record the exact removed metadata bytes/order needed for its inverse transformation. Exact pre-adoption bytes and authorship therefore remain implementor-recorded provenance, not independently confirmed history.

### Requirement classification and escalation

- **§4.4 revision guidance is implemented.** `review_prompt()` requests five named fields; each reviewer output is stored separately; `revision_prompt()` accepts a `list[str]` and requests five actionable plan sections; the next iterative draft receives both prior review findings and the revision checklist; `Underused references` additionally drives the next focus set. The specification does not require a validated schema, and per-reviewer model/provider bindings are explicitly optional (`MAY`). Richer schemas, aggregation, or persona routes are possible future scope, not a current requirement gap or owner decision queue.
- **§4.10 capability-aware execution is partially implemented.** `ModelPreset` and `LocalModelPreset` carry provider-independent `capabilities` tuples, and `catalog_payload()` exposes a capability list for every discovered model preset. `ModelSpec`/`ModelRoutes` do not carry those descriptors into execution, stages declare no capability requirements, and selection still uses routes/provider/tool flags. Capability representation exists; capability-aware workflow negotiation/execution does not.
- The remaining classifications and escalations are supported: damaged accepted pointers and persistent recovery policy remain owner-gated; malformed scorer validation is a bounded agent-authorized fail-closed defect slice requiring independent review; semantic evidence/verification state and durable normalization/capability architectures cross owner boundaries; §§4.6–4.8, 4.11–4.12, and §8 remain partial; §§10–12 completion remains unknown.

### Executable and diagnostic observations

- System Python: `66 passed in 7.62s`; bundled smart-loader: one file and four tests passed in `578ms`; loader typecheck passed. Repository `.venv` still reports `No module named pytest`, an unavailable check rather than a product failure.
- Isolated diagnostics reproduce `missing_pointer_resolves_to=v2`, `invalid_pointer_resolves_to=v2`, and malformed score metadata with verdict `same`, scores `5`/`5`, and empty rationale.
- Direct catalog inspection reports capability lists on all discovered model presets (`all_have_capabilities=True`), while code search finds no pipeline-stage capability requirements or route negotiation.
- No TCP listener was found on port `8765` at review time; this is a timestamped observation only.

## Material findings and resolution conditions

| ID | Severity | Finding | Impact | Resolution condition |
|---|---|---|---|---|
| `R1` | `MEDIUM` | §4.4 was classified partial and an optional reviewer-schema/persona-routing decision was escalated to the owner. | Misstates accepted requirements and manufactures an active owner decision that is not needed for v0.1. | Correct §4.4 to implemented, close the optional routing/guidance issue without product work, and remove it from current owner/active queues while preserving its history. |
| `R2` | `MEDIUM` | §4.10 and its issue state that no capability descriptor exists despite catalog/local preset capability metadata. | Makes the recovery model factually incomplete and obscures reusable implementation evidence. | Correct §4.10 to partially implemented and state precisely that descriptive capability metadata exists but is not consumed by execution. |
| `R3` | `MEDIUM` | Exact pre-adoption specification-byte preservation/authorship is presented as independently confirmed without a retained artifact or repeatable inverse procedure. | Overstates historical provenance at the adoption authority boundary. | Preserve current accepted authority, downgrade the exact historical claim to implementor-recorded/independently unreproducible, and carry the limitation explicitly without guessing missing bytes. |

## Interpretation

- **CONFIRMED:** The sibling protocol installation, collision mapping, governance-only change scope, tracked legacy handoff/README recovery, executable baseline, and four-file dirty-state preservation are sound at `e9ef291`.
- **CONFIRMED:** §4.4 is implemented and §4.10 is partially implemented at product revision `387bffe`.
- **CONFIRMED:** The current `PROJECT_SPEC.md` and accepted ADR are repository authority; the exact original untracked specification bytes are not independently recoverable from repository state.
- **INFERRED:** All three material findings can be repaired in governance/recovery artifacts without changing accepted product behavior or architecture.
- **UNKNOWN:** A fresh independent reviewer has not yet assessed the containing repair commit; real providers, live research, representative document fidelity, damaged external workspaces, and full §§10–12 compatibility remain unverified.

## Limitations and residual uncertainty

- The review ran on the same Darwin host class as the recovery implementor and did not authenticate participant identities.
- No live provider credentials, model endpoints, network research, browser/UI workflow, citation-verification process, OCR corpus, or external project compatibility test ran.
- Git can preserve the accepted current specification and future corrections, but cannot recover untracked pre-adoption bytes that were never stored as an object.
- Approval of a repaired target requires a fresh participant because this reviewer also implements the governance corrections.

## Governance repair verification

At `2026-08-24T03:44:24Z`, after applying only the authorized additive corrections, the reviewer/repair implementor reran the following checks against the repair worktree rooted at `e9ef291`:

| Check | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` | `66 passed in 7.55s`; exit `0` |
| `.venv/bin/python -m pytest -q -p no:cacheprovider` | Unavailable: `.venv` reported `No module named pytest`; exit `1`; not a product-test failure |
| `npm test` and `npm run typecheck` in `asl/_vendor/smart-loader` | One file/four tests passed in `376ms`; typecheck passed; both exit `0` |
| Sibling `scripts/validate_protocol.py` at `58fa281` | `PASS structural protocol validation (package_files=10 handoffs=2)`; exit `0` |
| Seven explicit immutable source-to-target `cmp` calls | All seven approved mappings matched; exit `0` |
| Target Markdown/local-link/HANDOFF checker | `markdown_files=25`, `local_links=145`, `missing=0`; exactly five ordered sections and a nonempty Next Action; exit `0` |
| Governance-path allowlist plus regular-file/symlink boundary | Exactly nine repair paths, all allowed regular files, no symlinks, no `PROJECT_SPEC.md`/product/test path, and all four unrelated untracked files present; exit `0` |
| Local and direct remote revisions | Target `HEAD=e9ef291`, `origin/main` and direct remote `main=387bffe`; sibling local/tracking/direct remote `main=58fa281`; exit `0` |
| Legacy and dirty-state SHA-256 checks | Legacy HANDOFF `43200c...`, parent README `c7986a...`, and all four unrelated JavaScript hashes reproduced; exit `0` |
| Ignored `papers/` observation | Five projects, sixteen `vN` directories, five valid accepted pointers, and three projects with a later candidate; exit `0`; mutable local evidence only |
| Pre-adoption specification object search | Parent contains no `PROJECT_SPEC.md`; all `439` Git blobs, including unreachable objects, produced no SHA-256 match for `3717cd...`; exit `0` |
| Pointer and malformed-score diagnostics | Reproduced `v2`, `v2`, and `same`/`5`/`5` with empty rationale; exit `0` |
| Capability and reviewer-guidance diagnostics | `35` catalog models all exposed capability lists; preset types carried `capabilities` while execution route types did not; both prompt schemas, multi-review synthesis, next-iteration findings/checklist, and underused-reference extraction reproduced; exit `0` |
| `lsof -nP -iTCP:8765 -sTCP:LISTEN` | No output/listener; exit `1`, the expected timestamped absence result |
| `git diff --check` and repair-scope inspection | Passed; exactly nine governance/recovery repair paths and zero product, runtime, test, specification, generated-paper, environment, or unrelated-file changes |

These checks verify the repair content and preservation boundary; they do not convert this implementor into the fresh independent reviewer required to approve the containing commit.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record; immutable reviewed target and source revisions are recorded above.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record.
- **External retention risk:** Direct remotes and ignored samples can change; immutable Git objects remain the durable boundary for tracked history.
- **Supersedes / superseded by:** Supersedes the §4.4 and §4.10 classifications in [`EVIDENCE-20260824T024051Z-spec-reconciliation`](EVIDENCE-20260824T024051Z-spec-reconciliation.md) and qualifies the original-specification reconstruction claim in [`EVIDENCE-20260824T024051Z-repository-recovery`](EVIDENCE-20260824T024051Z-repository-recovery.md); otherwise `NONE`.

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | Discarded an initial compact zsh `cmp` loop whose pair strings did not split and reran seven explicit immutable comparisons; all passed. | The failed loop emitted combined source paths; explicit one-pair commands produced seven `MATCH` results. |
| `2026-08-24T03:31:59Z` | `agent:codex-governance-review` | Discarded the final status of a combined target checker because it assigned zsh's read-only `status` parameter after its Markdown/HANDOFF checks; reran the path-set and regular-file/symlink boundary separately, which passed. | The first checker printed `markdown_files=25 local_links=123 missing=0` and correct HANDOFF sections before the shell error; the separate corrected boundary command exited `0`. |
