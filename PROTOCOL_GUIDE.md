# Agent-Native Software Engineering Protocol

This package is a lightweight, repository-native operating system for long-running software work performed by replaceable coding-agent instances under a human technical owner. It makes work resumable, auditable, evidence-driven, independently reviewable, and resistant to architecture drift without requiring an orchestrator, service, database, or hidden conversation history.

> **Agent continuity without agent identity.**
>
> **Agents are ephemeral; project state is durable.**
>
> *牲口没有身份，磨盘有记忆。*

Project continuity MUST NOT depend on agent identity or session continuity. Individual coding-agent sessions are replaceable, and no agent instance owns project truth. Durable state belongs in repository artifacts: `PROJECT_SPEC.md`, accepted ADRs, executable tests and contracts, recorded evidence, `HANDOFF.md`, and Git history when available. A fresh participant must be able to resume from those artifacts without prior conversational context. Continuity belongs to the project, not to an agent session.

Participant attribution still matters for auditability, independent-review provenance, and human approvals; it does not confer ownership of project truth. Git history preserves provenance and recovery context, but it does not create a new source-of-truth tier or change the precedence defined by this protocol.

## The problem it solves

Agent throughput can exceed a human owner's ability to read every diff. Sequential agents can also amplify an unsupported assumption until an internally consistent implementation diverges from the actual requirement. Chat transcripts, agent memory, and code alone are poor continuity mechanisms.

This protocol keeps authority and evidence in the repository. It gives agents enough operational state to continue safely while reserving durable product and architecture decisions for explicit human authority.

## Philosophy

- Requirements and accepted decisions outrank whatever code happens to exist.
- Evidence is more useful than confidence or polished summaries.
- Agents are temporary peer participants, not permanent supervisors or trusted narrators.
- Local reversible implementation can move quickly; durable commitments cross a human authority boundary.
- Review is proportionate to risk: low-risk local work records self-review, while contract, architecture, security, state, dependency, concurrency, coupling, and material-complexity changes require an independent participant.
- Complexity without contract, test, or evidence coverage remains visible debt.
- A coherent handoff is more valuable than squeezing one more change into a failing session.

The exact operational rules and truth hierarchy live in [`BOOTSTRAP.md`](BOOTSTRAP.md).

## Package contents

| Artifact | Purpose |
|---|---|
| [`BOOTSTRAP.md`](BOOTSTRAP.md) | Normative instructions for starting, working, verifying, reviewing, escalating, and handing off. |
| [`PROJECT_SPEC.md`](PROJECT_SPEC.md) | Human-owned requirements and acceptance template. |
| [`HANDOFF.md`](HANDOFF.md) | Compact current operational state and resumability record. |
| [`HUMAN_CHECKPOINT.md`](HUMAN_CHECKPOINT.md) | Low-bandwidth architecture and decision synchronization for the owner. |
| [`ADR/`](ADR/) | Durable architectural decisions and rationale. |
| [`ISSUES/`](ISSUES/) | Detailed lifecycle records for meaningful work and uncertainty. |
| [`EVIDENCE/`](EVIDENCE/) | Reproducible proof and provenance for important claims. |
| [`PROMPTS.md`](PROMPTS.md) | Fresh, resume, review, drift, and checkpoint prompts. |
| [`EXAMPLE.md`](EXAMPLE.md) | A synthetic minimal initialization walkthrough. |

## Quick start

1. Inventory existing specifications, architecture records, agent instructions, handoff history, issues, evidence, and application documentation. Do not migrate concurrently with another writer.
2. Resolve the complete destination manifest before writing anything:

   | Source package path | Collision-free destination | Sole-README-collision destination |
   |---|---|---|
   | `README.md` | `README.md` | `PROTOCOL_GUIDE.md` |
   | `BOOTSTRAP.md` | `BOOTSTRAP.md` | `BOOTSTRAP.md` |
   | `PROJECT_SPEC.md` | `PROJECT_SPEC.md` | `PROJECT_SPEC.md` |
   | `HANDOFF.md` | `HANDOFF.md` | `HANDOFF.md` |
   | `HUMAN_CHECKPOINT.md` | `HUMAN_CHECKPOINT.md` | `HUMAN_CHECKPOINT.md` |
   | `ADR/TEMPLATE.md` | `ADR/TEMPLATE.md` | `ADR/TEMPLATE.md` |
   | `EVIDENCE/TEMPLATE.md` | `EVIDENCE/TEMPLATE.md` | `EVIDENCE/TEMPLATE.md` |
   | `ISSUES/TEMPLATE.md` | `ISSUES/TEMPLATE.md` | `ISSUES/TEMPLATE.md` |
   | `PROMPTS.md` | `PROMPTS.md` | `PROMPTS.md` |
   | `EXAMPLE.md` | `EXAMPLE.md` | `EXAMPLE.md` |

   Treat every existing filesystem entry, including a dangling symlink, as a collision. `PROTOCOL_GUIDE.md` is a reserved destination even though it is not a source-package path.
3. Choose exactly one automatic path:

   **Collision-free target.** This includes an established repository with no application README and none of the resolved destinations above. Confirm that both conventional guide names and every other destination are absent, then use the quoted bulk-copy command:

   ```sh
   protocol_source="/path/to/agentic-engineering-protocol/protocol"
   repository_target="/path/to/your-repository"

   if [ ! -d "$protocol_source" ] || [ ! -d "$repository_target" ]; then
     printf 'source or target directory is absent\n' >&2
     exit 1
   fi

   for relative_path in \
     README.md PROTOCOL_GUIDE.md BOOTSTRAP.md PROJECT_SPEC.md HANDOFF.md \
     HUMAN_CHECKPOINT.md PROMPTS.md EXAMPLE.md ADR EVIDENCE ISSUES
   do
     if [ -e "$repository_target/$relative_path" ] || [ -L "$repository_target/$relative_path" ]; then
       printf 'collision: %s\n' "$repository_target/$relative_path" >&2
       exit 1
     fi
   done

   cp -R "$protocol_source/." "$repository_target/"
   ```

   **Application README as the sole collision.** Use this path only when the repository's `README.md` is an existing regular file, is not a symlink, and every other resolved destination is absent. Run this complete preflight before any copy:

   ```sh
   protocol_source="/path/to/agentic-engineering-protocol/protocol"
   repository_target="/path/to/your-repository"

   if [ ! -d "$protocol_source" ] || [ ! -d "$repository_target" ]; then
     printf 'source or target directory is absent\n' >&2
     exit 1
   fi

   if [ ! -f "$repository_target/README.md" ] || [ -L "$repository_target/README.md" ]; then
     printf 'application README is absent, non-regular, or a symlink\n' >&2
     exit 1
   fi

   for relative_path in \
     PROTOCOL_GUIDE.md BOOTSTRAP.md PROJECT_SPEC.md HANDOFF.md \
     HUMAN_CHECKPOINT.md PROMPTS.md EXAMPLE.md ADR EVIDENCE ISSUES
   do
     if [ -e "$repository_target/$relative_path" ] || [ -L "$repository_target/$relative_path" ]; then
       printf 'collision: %s\n' "$repository_target/$relative_path" >&2
       exit 1
     fi
   done
   ```

   After the preflight exits successfully, install every canonical artifact with quoted operands:

   ```sh
   protocol_source="/path/to/agentic-engineering-protocol/protocol"
   repository_target="/path/to/your-repository"

   cp \
     "$protocol_source/BOOTSTRAP.md" \
     "$protocol_source/PROJECT_SPEC.md" \
     "$protocol_source/HANDOFF.md" \
     "$protocol_source/HUMAN_CHECKPOINT.md" \
     "$protocol_source/PROMPTS.md" \
     "$protocol_source/EXAMPLE.md" \
     "$repository_target/"
   cp -R \
     "$protocol_source/ADR" \
     "$protocol_source/EVIDENCE" \
     "$protocol_source/ISSUES" \
     "$repository_target/"
   cp "$protocol_source/README.md" "$repository_target/PROTOCOL_GUIDE.md"

   cmp "$protocol_source/BOOTSTRAP.md" "$repository_target/BOOTSTRAP.md"
   cmp "$protocol_source/README.md" "$repository_target/PROTOCOL_GUIDE.md"
   ```

   Only after both comparisons succeed, append this navigation section to the application README without removing its existing content:

   ```markdown
   ## Agent-Native Engineering Protocol

   Participants must read [BOOTSTRAP.md](BOOTSTRAP.md) before working in this repository. Adoption guidance is in [PROTOCOL_GUIDE.md](PROTOCOL_GUIDE.md).
   ```

   Verify the complete installed manifest against the source, confirm that the application README still contains its prior content plus both navigation links, and resolve every guide-relative link from the repository root.

4. If any destination other than the application `README.md` exists, stop before copying or editing anything. Do not install a non-conflicting subset. Preserve the existing files, authorship, and history; record the collision and contradiction under the target repository's current process; and obtain its human technical owner's accepted mapping or merge decision. A non-canonical mapping is not valid merely because links resolve: update every affected guide, prompt, template, and entry-point reference, and verify that each canonical role points to the owner-approved content before resuming installation.
5. Replace the placeholders in `PROJECT_SPEC.md`. The human technical owner records acceptance before agents implement affected product behavior.
6. Give a fresh participant the **Fresh implementor or onboarding** prompt from `PROMPTS.md`.
7. The participant inspects the repository, replaces the template HANDOFF snapshot with evidence-backed state, identifies active work, and begins from one bounded safe action.
8. Keep the protocol files in version control when available. Git is useful but not required; record hashes or other durable file state when commits are unavailable.

See [`EXAMPLE.md`](EXAMPLE.md) for a small filled-in illustration.

## Expected workflow

1. A participant reads BOOTSTRAP and independently inspects current truth.
2. It selects or creates an issue and classifies authority and review requirements. An explicitly declared milestone in an accepted specification is prior authorization within its exact scope; inferred work and external task pressure are not.
3. It reproduces or establishes the problem before changing behavior.
4. It implements a small scoped change and records proportional verification.
5. Low-risk local work records attributable self-review; the risk categories defined in BOOTSTRAP require independent review, and durable architecture requires prior human authority. Required independent review may be performed by a peer agent whose participant label differs from the implementor's; the protocol does not authenticate that label.
6. Durable facts stay in the specification, ADR, contracts, or evidence. HANDOFF retains only what the next participant needs operationally.
7. Material review findings return already-authorized work to a within-scope fix/re-review loop. Acceptance may expose the next dependency-satisfied milestone already in the accepted specification without another owner prompt; no declared milestone means no authorized work.
8. Before stopping, the participant reconciles background work and leaves exactly one next action.

Temporary roles can include Implementor, Reviewer, Verification Agent, Risk Reviewer, and Architecture Reviewer. They are roles for a task, not a permanent hierarchy.

## Human technical owner

The owner defines requirements, accepts durable architectural commitments, decides major tradeoffs, and periodically checks the system mental model through `HUMAN_CHECKPOINT.md`. The owner should not need to inspect every local refactor or routine defect fix.

The checkpoint concentrates attention on changed boundaries, complexity, assumptions, drift, uncertainty, and explicit decisions. Product decisions are persisted into `PROJECT_SPEC.md`, architecture decisions into an ADR, and mixed decisions into both so later agents do not depend on missing chat.

## Agent participants

Agents handle investigation, routine implementation, tests, evidence capture, issue maintenance, review, and resumable handoff. They may decide local reversible details within accepted contracts. They must surface contradictions and escalate durable commitments rather than treating implementation momentum as authority.

Independent reviewers should challenge the premise of a change, not just its mechanics. Disagreement creates an investigation path; it is neither erased nor automatically treated as an error.

## Adopting in an existing repository

- Use the automatic established-repository path in Quick start only when the application README is the sole collision. Keep that README, the canonical `PROTOCOL_GUIDE.md` alias, and links to both the guide and byte-verified normative `BOOTSTRAP.md`.
- Stop before any write when another destination exists. Resolve normative-record collisions through the target repository's human authority; do not assume that an alternate filename or a resolving link preserves protocol meaning.
- Inventory current specifications, architecture records, issue trackers, agent instructions, and handoff documents before copying anything.
- Preserve authorship and useful history. Map existing authoritative requirements into `PROJECT_SPEC.md` and durable accepted decisions into ADRs.
- Record unresolved contradictions instead of choosing a source silently.
- Start HANDOFF as a present snapshot with links; do not paste an entire historical changelog into it.
- Keep external issue trackers or CI systems if useful, but preserve enough durable repository context that an agent without those sessions can identify and safely resume work.
- Add model- or tool-specific instruction shims only as optional pointers to `BOOTSTRAP.md`; do not fork the normative rules across vendors.

## Limitations

- Markdown cannot enforce compliance; participants and reviewers must follow the protocol.
- Optional project-local tooling may validate deterministic structure or lifecycle gates, but it is not part of this reusable package, cannot create authority, and cannot replace judgment about scope, evidence adequacy, or review quality.
- The protocol improves evidence quality but cannot prove that tests, specifications, or human decisions are themselves correct.
- Independent review reduces correlated error but does not eliminate it.
- Concurrent participants can still create merge conflicts; repository-unique timestamp IDs reduce record allocation collisions but do not coordinate code edits.
- Sensitive or very large evidence may require an external durable store with retention and access controls.
- A human owner remains necessary for product ambiguity, risk acceptance, and durable architectural authority.
- The templates require initial adaptation. An unfilled `DRAFT` specification intentionally blocks unsupported product implementation.

## Evolving the protocol

Treat changes to source precedence, authority boundaries, required records, or review gates as durable architecture changes. Propose them with compatibility and migration consequences, obtain owner approval, and preserve prior records. Local wording improvements that do not change meaning should still be attributable and reviewed for contradiction.
