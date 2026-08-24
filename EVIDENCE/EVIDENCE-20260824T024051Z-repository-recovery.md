# EVIDENCE-20260824T024051Z: Repository Recovery and Test Inventory

## Metadata

- **ID:** `EVIDENCE-20260824T024051Z-repository-recovery`
- **Title:** First-adoption repository recovery and executable-test inventory
- **Captured UTC:** `2026-08-24T02:40:51Z`
- **Recorded by:** `agent:codex-recovery`
- **Claim supported or challenged:** The target's actual pre-adoption state, historical provenance, executable baseline, local traces, and protocol source can be recovered without treating implementation artifacts as product authority.
- **Related requirements:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) §§10–13
- **Related ADRs/issues:** [`ADR-20260824T024051Z-protocol-adoption`](../ADR/ADR-20260824T024051Z-protocol-adoption.md), [`ISSUE-20260824T024051Z-protocol-adoption-recovery`](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md)
- **Repository revision/state:** Target `main`, `origin/main`, and direct remote `main` at `387bffe632ba2d53c14aa59de93bd645935d9a94` before the containing governance commit; protocol source local/remote `main` at `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`; dirty files inventoried below.
- **Environment:** Darwin `25.3.0` arm64; Python `3.9.6`; Node `v22.22.0`; npm `10.9.4`; Git `2.50.1 (Apple Git-155)`. Secrets and `.env` contents were not inspected.

## Method

- **Procedure:** Read the sibling protocol entry and reusable guide; verify local and direct remote refs; inventory target files/status/history/ignore rules; read the accepted-intent candidate, README/docs, legacy handoff, relevant implementation and tests; sample ignored paper metadata read-only; reproduce two critical state paths in a temporary directory; run available suites and structural/integrity checks.
- **Exact command/input:** Principal commands were `git status --short --branch`, `git rev-parse HEAD main origin/main`, `git ls-remote origin refs/heads/main`, `git log --oneline`, `git check-ignore -v`, `rg --files`, `rg -n`, `shasum -a 256`, `lsof -nP -iTCP:8765 -sTCP:LISTEN`, `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`, `npm test`, `npm run typecheck`, and `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_protocol.py` in the sibling source. The isolated Python diagnostic called `accepted_version()` and `_score_metadata()` only inside a `TemporaryDirectory`.
- **Exit status:** Successful except the explicitly recorded unavailable/incorrect invocations below.
- **Repeatability:** Start from target revision `387bffe`, leave ignored and unrelated untracked files untouched, use the recorded commands, and inspect the cited source/test paths. Ignored paper artifacts are mutable samples and may no longer match this capture.

## Raw observation

### Version-control and dirty-state boundary

- The target's tracked `HEAD`, local `main`, remote-tracking `origin/main`, and direct remote `refs/heads/main` all resolved to `387bffe632ba2d53c14aa59de93bd645935d9a94`.
- The sibling protocol repository was clean; its corresponding refs all resolved to `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`.
- Pre-adoption target status contained the owner-authored untracked `PROJECT_SPEC.md` plus four unrelated untracked JavaScript files. Their preserved SHA-256 digests were:

| Path | SHA-256 |
|---|---|
| `PROJECT_SPEC.md` before governance metadata | `3717cd4727b1eba17aa35c6605b80ba071095eb64b6da5994dff1468ff324033` |
| `codex-app-server-agent.js` | `b3647d38f0f920602e77d5235da19e57422ad4d141e08ca598d8545eb0b06281` |
| `codex-feature-definitions.js` | `6f644792b484011e2e4718ef90e0705607d6c6d08d4b086abfb6f74132ab32f6` |
| `provider-model.js` | `99bbbdcb3fbd541d51b77265e19b5d71502c2b216a39189b61e81851317ea80f` |
| `provider-registry.js` | `086e35d1299f5839ce7eaa8c1e4a1e74ee10d1dda265cf9dcc5c6da09471b167` |

- `.env`, `.venv/`, and `papers/` are ignored. `.env` was not read. No CI workflow or configuration was found in the repository inventory.
- At capture time, `lsof` reported no TCP listener on port `8765`; no durable background-task reference existed. This establishes only the timestamped observation, not a permanent service state.

### Protocol provenance and collision integrity

- The reusable source package contained ten Markdown artifacts and no symlinks. Its validator reported `PASS structural protocol validation (package_files=10 handoffs=2)`.
- Source SHA-256 included `BOOTSTRAP.md` = `b98ea213caf614dfa778fe416fb0b1fe3d31b2342ae3d38aea8a9b44c52e87da` and source `README.md` = `36b7503560e4775d25c1ca0e14a6c217f50501671f68e7b6ab6d2c47d5a90042`.
- Explicit byte comparisons passed for source-to-target mappings `BOOTSTRAP.md`, `README.md` → `PROTOCOL_GUIDE.md`, `PROMPTS.md`, `EXAMPLE.md`, and the three templates. The first compact zsh loop incorrectly supplied combined path strings to `cmp`; explicit one-pair commands corrected the invocation and all seven comparisons passed.

### Historical handoff and generated traces

- The legacy handoff is recoverable as Git object `387bffe:HANDOFF.md`; its SHA-256 is `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`.
- It described implementation work and commands but predates the accepted specification/protocol. Its claims were checked selectively and treated as evidence, never promoted to requirements.
- The ignored `papers/` tree contained five immediate project workspaces and sixteen `vN` directories at capture time. All five sampled accepted pointers were valid; three workspaces retained chronologically later rejected candidates. These mutable local artifacts support only that current behavior has been exercised locally. They are not committed evidence, not exhaustive, and not product authority.

### Executable test inventory

- Python tests: one file, [`tests/test_pipeline.py`](../tests/test_pipeline.py), with 66 collected `test_*` functions. It covers version artifact creation, quality rejection/fallback cases, alternate-checkpoint iteration, focus/rotation, reviewer outputs, search traces, role routes/providers/endpoints, prompts, rendering/UI, and selected loader integration paths.
- Bundled loader tests: one file, [`asl/_vendor/smart-loader/tests/basic.test.ts`](../asl/_vendor/smart-loader/tests/basic.test.ts), with four Vitest cases for text-folder loading, chunk overlap, extractable PDF text, and CAJ discovery/fallback metadata.
- `.venv/bin/python -m pytest -q -p no:cacheprovider` failed because the repository virtual environment has no `pytest` module. This is an unavailable check, not a product test failure.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` passed: `66 passed in 8.33s`.
- The final recovery-pass rerun of the same command passed: `66 passed in 7.48s`.
- The initial `npm test -- --runInBand` attempt failed because this Vitest version does not support `--runInBand`. The corrected `npm test` passed one file/four tests, and `npm run typecheck` passed.
- The final recovery-pass rerun again passed one file/four tests in `491ms`, followed by a successful typecheck.
- No test specifically asserted malformed/non-JSON scorer validation, a no-valid-score decision, damaged accepted-pointer behavior, explicit candidate/verified research state, a semantic evidence-resolution contract, or provider-independent capability requirements.
- Final staged inspection contained exactly twenty approved governance/documentation paths, no `asl/` or test path, and no unstaged tracked change. The four unrelated untracked JavaScript digests still matched the pre-adoption inventory.
- Removing only the accepted authority/change record and restoring the original metadata whitespace/order reconstructed the owner specification at SHA-256 `3717cd4727b1eba17aa35c6605b80ba071095eb64b6da5994dff1468ff324033`. Removing only the appended protocol navigation reconstructed the README at SHA-256 `c7986af3a9475a371a4f17d0cb30bc623cf25256c146770ad088c8e14e8dc514`.

### Diagnostic observations

The isolated reproduction printed:

```text
missing_pointer_resolves_to=v2
invalid_pointer_resolves_to=v2
malformed_score_metadata={'provider': 'fake', 'model': 'judge', 'attempts': [], 'verdict': 'same', 'previous_score': 5, 'candidate_score': 5, 'rationale': ''}
```

## Interpretation

- **CONFIRMED:** The target was synchronized with its remote before adoption, and the protocol source was clean and remote-current at the recorded revisions.
- **CONFIRMED:** The pre-existing executable baseline passed under system Python and the bundled loader's supported npm commands; `.venv` could not run pytest.
- **CONFIRMED:** No product or test file needed modification to adopt the protocol baseline.
- **CONFIRMED:** Useful historical state remains recoverable without retaining the legacy handoff as current authority.
- **INFERRED:** The current tests are substantial implementation evidence but insufficient to prove full specification compatibility because material edge contracts have no executable coverage.
- **UNKNOWN:** Behavior with real remote/local models, live research services, damaged external workspaces, secrets-dependent routes, and a representative heterogeneous-document corpus was not established.

## Limitations and residual uncertainty

- Ignored paper workspaces are mutable, local, non-authoritative samples and were not copied into versioned evidence.
- No network research, provider credential use, live endpoint inference, browser/UI session, citation verification, OCR-quality study, or external-project compatibility test ran.
- “No CI configuration found” is based on the captured repository inventory; externally configured CI outside the repository is unknown.
- No port `8765` listener was present only at the timestamped check.

## Integrity and provenance

- **Artifact location:** `INLINE` in this evidence record; immutable revision and file digests are embedded above.
- **Artifact digest:** `NOT AVAILABLE` for this self-referential record; source artifacts and legacy/unrelated files have explicit SHA-256 values above.
- **External retention risk:** Direct remote refs and ignored local workspaces can change; immutable Git object IDs and committed record history provide the durable boundary.
- **Supersedes / superseded by:** `NONE`

## Corrections

| UTC time | Participant | Correction | Reason and supporting evidence |
|---|---|---|---|
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Replaced the unsupported Vitest `--runInBand` invocation with `npm test`; the supported command passed. | Vitest CLI error followed by successful package-script output. |
| `2026-08-24T02:40:51Z` | `agent:codex-recovery` | Replaced a zsh loop that combined `cmp` paths with seven explicit byte comparisons; all passed. | Explicit `cmp` exit statuses. |
| `2026-08-24T02:54:48Z` | `agent:codex-recovery` | Discarded a target-manifest check whose loop variable `path` shadowed zsh's special `PATH` array, causing `find` and `grep` to be unavailable; reran with `entry` and absolute utility paths, and the corrected check passed. | Failed diagnostic output followed by the corrected manifest/regular-file/symlink and byte-comparison check. |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | Discarded an inverse specification check that restored the historical status line in the wrong position; the corrected inverse transformation matched the recorded original SHA-256 exactly. | Original pre-adoption byte capture and corrected digest check. |
| `2026-08-24T02:59:54Z` | `agent:codex-recovery` | Discarded a combined README diagnostic that added an extra newline and allowed a later command to mask its nonzero Python status; a strict `set -e` rerun without the extra newline matched the recorded README digest. | Mismatched intermediate digest followed by strict successful reconstruction and immutable legacy-handoff digest check. |
