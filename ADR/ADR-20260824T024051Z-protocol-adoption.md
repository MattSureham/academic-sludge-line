# ADR-20260824T024051Z: Adopt the Agent-Native Engineering Protocol with an Owner-Approved Collision Merge

## Metadata

- **ID:** `ADR-20260824T024051Z-protocol-adoption`
- **Title:** Adopt the Agent-Native Engineering Protocol with an owner-approved collision merge
- **Status:** `ACCEPTED`
- **Created UTC:** `2026-08-24T02:40:51Z`
- **Author:** `agent:codex-recovery`
- **Human technical owner:** `human:technical-owner`
- **Owner approval:** `APPROVED` at `2026-08-24T02:40:51Z`; this record durably persists the owner's first-adoption instruction and explicit approval of the merge mapping.
- **Related specification:** [`PROJECT_SPEC.md`](../PROJECT_SPEC.md), especially authority/status, §10, and §13
- **Related issues:** [`ISSUE-20260824T024051Z-protocol-adoption-recovery`](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md)
- **Supersedes / superseded by:** `NONE`

## Context

The repository predates the protocol. At the adoption boundary, the application [`README.md`](../README.md) and tracked historical [`HANDOFF.md`](../HANDOFF.md) already existed, and the owner-authored [`PROJECT_SPEC.md`](../PROJECT_SPEC.md) was an untracked target artifact. The reusable protocol's automatic installation path therefore stopped on collisions and required a human-approved mapping or merge decision.

The protocol source is the clean, remote-current sibling repository `../agentic-engineering-protocol` at revision `58fa281ee6cb93abc2fea81dd46f8ddef2d8612b`. The target authority boundary before adoption is clean tracked revision `387bffe632ba2d53c14aa59de93bd645935d9a94` plus the owner specification and four unrelated untracked JavaScript files. Existing code, README claims, generated paper workspaces, and the legacy handoff are evidence of implementation state, not product-intent authority over the new specification.

## Decision

1. Adopt the reusable protocol's authority hierarchy and artifact ownership through a byte-identical root [`BOOTSTRAP.md`](../BOOTSTRAP.md) from source revision `58fa281`.
2. Preserve the application README and install the reusable source guide as byte-identical [`PROTOCOL_GUIDE.md`](../PROTOCOL_GUIDE.md), with navigation from the application README to both protocol entry points.
3. Retain the owner-authored specification at canonical [`PROJECT_SPEC.md`](../PROJECT_SPEC.md), add only protocol authority/acceptance metadata and a change record, and do not alter its behavioral wording to match the implementation.
4. Replace the legacy handoff at canonical [`HANDOFF.md`](../HANDOFF.md) with the protocol's five-section operational form. Preserve the legacy bytes and provenance through Git object `387bffe:HANDOFF.md`, SHA-256 `43200c484281fcb25dd8a128096a21ee05d87d4200a95f29a342bd137c5c2ede`, and the recovery evidence. Verified historical facts may be summarized; implementation notes do not become requirements.
5. Install byte-identical reusable `PROMPTS.md`, `EXAMPLE.md`, and the templates under `ADR/`, `ISSUES/`, and `EVIDENCE/`. Fill project-owned `HUMAN_CHECKPOINT.md` from its template rather than retaining placeholders.
6. Keep protocol records in version control. Do not commit generated paper workspaces, secrets, local environments, build residue, or the four unrelated untracked JavaScript files.
7. Treat this adoption as governance-only. It changes no product API, persistence behavior, model route, loader, pipeline behavior, or executable test.

## Human Authority Boundary assessment

- **Boundary crossed:** `YES`
- **Reason:** The decision establishes root source precedence, record ownership, required review gates, and an owner-approved collision merge.
- **Existing authorization:** The owner's first-adoption instruction, accepted v0.1 [`PROJECT_SPEC.md`](../PROJECT_SPEC.md), and explicit approval of this canonical mapping.
- **Approval evidence:** `human:technical-owner`, recorded `2026-08-24T02:40:51Z`; this accepted ADR is the durable authority reference.

## Alternatives considered

### Overwrite every collision with reusable templates

- **Benefits:** Byte identity with the source package at every mapped path.
- **Costs and risks:** Destroys the owner-authored specification and useful historical continuity; violates the protocol's collision rule and the owner's authority instruction.
- **Reason not selected:** It would erase higher-value project truth and provenance.

### Keep the existing files and install only non-conflicting artifacts

- **Benefits:** Minimal editing.
- **Costs and risks:** Creates a partial, internally inconsistent protocol installation and leaves no canonical entry hierarchy.
- **Reason not selected:** The reusable guide explicitly prohibits subset installation after a collision.

### Rename the specification or handoff

- **Benefits:** Avoids editing existing files.
- **Costs and risks:** Breaks canonical protocol roles and requires pervasive reference changes without improving authority clarity.
- **Reason not selected:** The owner approved canonical paths with explicit merges.

## Consequences

### Positive

- Fresh participants have one canonical entry point, explicit source precedence, durable issue/evidence mechanisms, and a compact operational handoff.
- The owner specification remains product-intent authority rather than being rewritten from implementation claims.
- Historical implementation knowledge remains recoverable without occupying a higher truth tier.

### Negative and tradeoffs

- The installed target is intentionally not byte-identical to the reusable package at `PROJECT_SPEC.md`, `HANDOFF.md`, and `HUMAN_CHECKPOINT.md`; this ADR owns those approved deviations.
- Governance adoption requires independent review before the recovery issue can close.
- The worktree remains dirty after the local commit because four unrelated untracked JavaScript files are deliberately preserved.

### Compatibility and migration

- Application behavior and generated project formats are unchanged.
- The prior handoff remains available through immutable Git history and its recorded digest.
- A rollback may revert the containing governance commit while retaining this decision and recovery evidence through Git history; product artifacts need no migration.

## Unverified complexity

| Cost introduced | Why necessary | Contract/test/evidence coverage | Residual gap and linked issue |
|---|---|---|---|
| Repository governance records and review gate | Make authority, recovery, and independent review durable | Byte comparisons, link/manifest checks, recovery evidence, and the adopted BOOTSTRAP | Independent review remains pending in the adoption issue |

## Evidence and assumptions

- **CONFIRMED:** Both repositories were locally clean at their tracked revisions and direct remote `main` refs matched at `2026-08-24T02:40:51Z`.
- **CONFIRMED:** `PROJECT_SPEC.md` and `HANDOFF.md` were target collisions; the application README was not the sole collision.
- **CONFIRMED:** The owner approved acceptance of v0.1, this adoption mapping, the label `human:technical-owner`, and a local unpushed review commit.
- **INFERRED:** A canonical merge is safer than a parallel protocol namespace because every participant role and relative link continues to resolve conventionally.
- **UNKNOWN:** Independent review has not yet assessed the containing adoption commit.

## Independent review rounds

- **Required:** `YES` — source precedence and governance architecture changed.

No independent review round has been recorded. The adoption issue remains in `REVIEW`; a fresh participant must inspect the containing commit directly.

### Review clarification — 2026-08-24T03:31:59Z

The statement above records the adoption implementor's original handoff state and is preserved as history. A first independent round has since reviewed immutable target `e9ef291a0be124a1ea1ad782c6bb307a486f2b18` and returned `CHANGES_REQUIRED` with three material governance findings: §4.4 was underclassified, §4.10 omitted existing descriptive capability metadata, and exact pre-adoption specification provenance was overclaimed.

Those findings do not invalidate this ADR's accepted protocol mapping or the current specification's authority. They authorize additive governance/recovery corrections only; they select no new product behavior or architecture. The containing repair commit must receive a fresh independent review before the adoption issue can close. The complete round and resolution conditions are recorded in the [adoption/recovery issue](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) and [independent review evidence](../EVIDENCE/EVIDENCE-20260824T033159Z-governance-independent-review.md).

### Review clarification — 2026-08-24T06:25:44Z

A fresh independent participant (`agent:claude-code-independent-review`) reviewed the containing governance-repair commit `113b8b015e70de7d7f0903d81b9300adeb060811`, confirmed all three `R1`–`R3` conditions resolved, and recorded `APPROVED` with zero open material findings. The adoption/recovery issue is now `CLOSED`; this ADR's accepted mapping is unchanged. The round is recorded in the [adoption/recovery issue](../ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) and [fresh review evidence](../EVIDENCE/EVIDENCE-20260824T062544Z-fresh-independent-review.md).

## Status history

| UTC time | From | To | Actor | Reason and authority evidence |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | `NONE` | `PROPOSED` | `agent:codex-recovery` | Reusable protocol collision inventory required a durable merge decision. |
| `2026-08-24T02:40:51Z` | `PROPOSED` | `ACCEPTED` | `human:technical-owner` | Owner approved the canonical merge and v0.1 acceptance for the first adoption pass. |
