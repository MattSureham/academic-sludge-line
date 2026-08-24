# Agent-Native Engineering Protocol

This is the normative entry point for every participant working in this repository. Read it before relying on `HANDOFF.md` or changing project files. Participants are peer-capable and replaceable; repository state and protocol records, not prior chat, must be sufficient to continue safely.

Project continuity MUST NOT depend on agent identity or session continuity. No agent instance owns project truth. Persist every fact needed for safe resumption in `PROJECT_SPEC.md`, accepted ADRs, executable contracts/tests, recorded evidence, `HANDOFF.md`, and version-control history when available. A fresh participant must be able to continue without access to prior conversational context. Version-control history provides provenance and recovery context; it does not add or reorder a project-truth tier.

Higher-priority platform, safety, legal, and explicit human instructions remain binding. If they conflict with repository instructions, stop the conflicting action and record the constraint.

## Project truth

Resolve claims about intended product behavior in this order:

1. Explicit project requirements, including [`PROJECT_SPEC.md`](PROJECT_SPEC.md)
2. Accepted records in [`ADR/`](ADR/)
3. Executable contracts and tests
4. Recorded evidence in [`EVIDENCE/`](EVIDENCE/)
5. [`HANDOFF.md`](HANDOFF.md)
6. Current implementation
7. Agent inference

Only accepted ADRs occupy level 2. Proposed, rejected, and superseded ADRs are historical or pending records, not current authority. `HUMAN_CHECKPOINT.md`, issue narratives, README files, prompts, comments, and chat summaries are navigation or coordination aids; they do not override the hierarchy.

When sources conflict, do not choose the convenient interpretation or silently make them consistent. Record the contradiction as an issue, cite both sources, classify its impact, and escalate if resolving it crosses the Human Authority Boundary.

Use these certainty labels for material claims:

- `CONFIRMED`: directly supported by an identified authoritative source or reproducible evidence.
- `INFERRED`: a reasoned conclusion whose supporting facts and interpretation are recorded.
- `UNKNOWN`: not established; state what would resolve it.

## Artifact ownership

- `PROJECT_SPEC.md` owns product goals, requirements, contracts, constraints, non-goals, and acceptance criteria.
- `ADR/` owns durable architectural decisions and their rationale.
- Tests, contracts, and `EVIDENCE/` own reproducible observations. Evidence supports claims; it does not make product decisions.
- `ISSUES/` owns detailed lifecycle records for meaningful work, contradictions, defects, risks, and residual uncertainty.
- Machine-readable milestone state, when enabled by an accepted specification and compatible accepted ADR, belongs inside the owning issue. It is operational lifecycle data bound to the authoritative contract digest; it cannot add scope, requirements, architecture, approvals, or a new truth tier.
- `HANDOFF.md` owns the current operational snapshot, compact active-issue index, background-task state, recent activity, and exactly one next action.
- `HUMAN_CHECKPOINT.md` gives the technical owner a low-bandwidth mental-model update and decision queue. Final product decisions belong in `PROJECT_SPEC.md`, final architecture decisions belong in an ADR, and mixed decisions require both.
- The adoption guide explains installation and navigation. It is `README.md` in the source package; when an established repository's application README is the sole destination collision, preserve it and use `PROTOCOL_GUIDE.md` as the canonical guide alias, with application-README links to the byte-verified canonical `BOOTSTRAP.md` and guide. An occupied alias or any other destination collision blocks automatic installation: preserve the target's files and obtain its human technical owner's accepted merge or mapping before modifying records or references. `PROMPTS.md` provides entry prompts. These navigation aids neither restate nor replace this protocol.

## Participant identity and records

Use an attributable participant label in activity, evidence, reviews, and approvals, such as `human:<role>` or `agent:<tool>-<session-label>`. Attribution establishes provenance and review independence; it does not make a participant the owner of project truth or a prerequisite for continuity. Use UTC ISO 8601 timestamps.

Create repository-unique, immutable identifiers in this form:

`TYPE-YYYYMMDDTHHMMSSZ-short-slug`

Use the prefixes `ISSUE`, `ADR`, `EVIDENCE`, and `TASK`. Check for a collision before creating a record; append a short disambiguating suffix if one exists. Renaming a title must not change the ID.

## Start or resume procedure

Before implementation, perform this sequence:

1. Read this file completely.
2. Inspect the repository structure, version-control or working-tree state if available, local execution instructions, build/test entry points, and relevant subsystem boundaries.
3. Read `PROJECT_SPEC.md`, relevant accepted ADRs, relevant executable contracts/tests, referenced evidence, and then `HANDOFF.md`, in truth-precedence order.
4. Inspect HANDOFF snapshot metadata and apply every recorded staleness trigger. If the revision/branch differs, dirty files are not represented, newer evidence changes a claim, an external reference changed or exceeded its refresh condition, a live task is unreconciled, or higher authority conflicts with the snapshot, mark affected claims `UNKNOWN` until reconciled. Do not refresh only the timestamp.
5. Reconcile every `QUEUED` or `RUNNING` background task in HANDOFF. Query its durable reference. Mark a missing process or remote reference `ORPHANED`; do not assume it is alive.
6. Independently inspect the code and files relevant to the proposed work. Verify important HANDOFF claims where feasible instead of inheriting them.
7. Identify contradictions, unsupported assumptions, uncommitted or partial work, unavailable tools, and dirty files that may belong to another participant.
8. Confirm that `PROJECT_SPEC.md` is sufficiently complete and accepted for the proposed behavior. An explicit current milestone in an accepted specification is prior human authorization for its declared scope; no new approval is needed merely to enter its next implementation, verification, review, or within-scope fix stage. If authority is draft, stale, missing, or ambiguous, limit work to investigation, specification, evidence gathering, or a reversible proposal.
9. Select the highest-priority safe action. Treat HANDOFF's Next Action as a continuity pointer, not an instruction that outranks current evidence.
10. Classify authority and review requirements before changing implementation. If an accepted milestone contract and local pipeline exist, reconcile its machine state from the owning issue and use it only for supported transitions.
11. Update the active issue or create one when the work is meaningful, will span a run, is blocked, or carries uncertainty.

Never discard, overwrite, or reformat unrelated user or participant changes merely to obtain a clean working tree.

## Selecting and scoping work

Prefer small, reversible changes that satisfy an explicit requirement or close a demonstrated gap. Do not broaden a task because adjacent cleanup is attractive.

An external task prompt, implementation momentum, participant preference, or an inferred useful next step does not create product scope. Conversely, do not ask the owner to reapprove a milestone already explicit in the accepted specification. Continue autonomously through deterministic gates and independent review while scope and authority remain intact; stop at a real authority boundary, not at a routine lifecycle boundary.

A routine change may remain inline in HANDOFF when it is local, reversible, contract-preserving, verified within one run, and introduces none of the complexity categories below. Promote it to an issue record if it becomes blocked, disputed, unverified, review-gated, or likely to cross participant sessions.

Every meaningful unit of work uses [`ISSUES/TEMPLATE.md`](ISSUES/TEMPLATE.md) and follows this primary lifecycle:

`OPEN → INVESTIGATING → IMPLEMENTING → VERIFYING → REVIEW → CLOSED`

`BLOCKED` may replace any non-terminal state. Record the prior state, blocker, owner of the unblock action if known, and exact unblock condition. After unblocking, restore the appropriate lifecycle state. Reopen a closed issue by returning it to `OPEN` and preserving the prior closure history.

Code written is not completion. `CLOSED` requires recorded verification evidence and every required review or approval.

## Human Authority Boundary

Agents may autonomously make local, reversible decisions that preserve external contracts and accepted architecture, including function decomposition, routine defect fixes, test organization, and small behavior-preserving refactors.

Explicit, current requirements can constitute prior human authorization for product behavior. A compatible accepted ADR can constitute prior authorization only for the architecture it decides. Otherwise, obtain human technical-owner approval before adopting a durable commitment involving any of the following:

- a major abstraction or material long-term complexity;
- a significant dependency;
- a public API, external contract, or cross-module contract;
- a core data model, persistence model, migration, or state ownership change;
- a new background service or process;
- deletion of an existing capability;
- a security, privacy, permission, or trust-boundary change;
- contradiction of an accepted ADR or requirement.

Put each decision in the artifact that owns its kind of truth:

- Product behavior, scope, capabilities, public APIs, and external contracts require an accepted update to `PROJECT_SPEC.md`. An ADR alone cannot add, delete, contradict, or resolve an `UNKNOWN` product requirement.
- Architectural structure and durable implementation constraints use a `PROPOSED` ADR from [`ADR/TEMPLATE.md`](ADR/TEMPLATE.md), provided the proposal is compatible with the specification.
- A decision affecting both product contract and architecture requires both an accepted specification update and an accepted ADR. If they differ, the specification wins and the conflict remains unresolved.

For a boundary-crossing decision:

1. Gather evidence and identify the requirement, architecture question, or contradiction.
2. Record exact proposed requirement wording in the issue for a product decision, create a `PROPOSED` ADR for an architecture decision, or do both when required.
3. Explain alternatives, consequences, compatibility, complexity, and residual uncertainty.
4. Add a concise decision request to `HUMAN_CHECKPOINT.md` and link every proposed authoritative change.
5. Do not insert unapproved behavior into an `ACCEPTED` specification or treat a proposed ADR as adopted. Continue only unrelated safe work or a clearly isolated, disposable experiment.
6. Record the issue as `BLOCKED` if no safe implementation can continue.
7. After an explicit owner decision, persist the accepted requirement and its change record in `PROJECT_SPEC.md`, the accepted architectural decision and approval in the ADR, or both. Only then may later participants rely on it. Chat alone is not durable authority.

Protocol amendments that alter authority, source precedence, record compatibility, or required gates also cross this boundary.

When `PROJECT_SPEC.md` defines an accepted milestone, it authorizes execution only within that milestone's recorded scope and constraints. Deterministic verification proves only the checks it ran. Independent review supplies a separate disposition but cannot expand the milestone. Human escalation remains required when specification text must change, scope or accepted architecture would change, a human-gated blocker must be resolved, evidence cannot establish authority, review exposes a material unresolved ambiguity, or a high-impact external action lacks prior authorization.

If independent review returns material findings whose resolution remains inside the accepted milestone, return to implementation and repeat verification/review without seeking another routine owner approval. After `APPROVED` and every acceptance gate, the next dependency-satisfied milestone already present in the accepted specification may begin without a new prompt. If none exists, stop; never manufacture work in runtime state.

## Review requirements

Set both `authority` and `review` on meaningful issues; they answer different questions.

- `authority: AGENT` or `HUMAN` identifies who may approve the decision.
- `review: SELF` or `INDEPENDENT` identifies who must validate the resulting work.

Use `SELF` only when the work remains local and reversible, preserves external behavior, contracts, and accepted architecture, introduces none of the independent-review risk categories below, and has no material dispute or uncertainty that benefits from another perspective. After implementation and verification, the implementor completes the issue's Self-review record with reviewed state, scope, authority references, checks, findings, limitations, residual risks, and outcome `COMPLETE` or `REWORK_REQUIRED`. `COMPLETE` is attributable self-verification, not independent-review evidence. If scope or risk grows, change the issue to `INDEPENDENT` before closure.

Independent review is required before closing changes that affect external behavior or contracts, introduce a dependency or persistent state, alter security or trust, add concurrency or a background process, create cross-module coupling, or materially increase long-term complexity. A human who did not implement the change may perform the independent review.

An independent reviewer must be a different participant or fresh agent instance that did not implement the change. It must inspect the specification, accepted ADRs, contracts/tests, implementation, and evidence directly—not merely validate the implementor's narrative. The reviewer should actively search for unsupported assumptions, alternative interpretations, regressions, unnecessary complexity, and architecture drift.

Append a separate review round containing reviewer identity, reviewed repository state, scope, findings, commands or procedures, limitations, residual risks, evidence, and exactly one disposition: `APPROVED`, `CHANGES_REQUIRED`, or `BLOCKED`. Use that exact vocabulary in session-facing verdicts as well as durable records; put qualifiers such as non-blocking findings in findings and residual risks, not in a fourth disposition. Never replace an earlier round. Unresolved material findings return the issue to the appropriate earlier state; a later approval must show how prior findings were resolved. If an independent reviewer is unavailable, leave the issue in `REVIEW` or `BLOCKED`; do not self-certify it as closed.

For a pipeline-managed milestone, also record the exact reviewed target and the nonnegative count of open material findings in the owning issue. Recorded implementor and reviewer labels must differ, but label inequality is not authenticated identity. `APPROVED` requires zero open material findings. `CHANGES_REQUIRED` prevents acceptance and returns within-scope work to implementation. `BLOCKED` never maps to approval and must identify what authority or evidence is missing.

## Evidence and verification

For meaningful work, preserve this chain:

`Problem → Evidence or reproduction → Change → Verification → Residual uncertainty`

Evidence should include, as applicable:

- the exact command, input, or reproduction procedure;
- UTC time, environment, relevant revision or file state;
- exit status and concise raw output or a durable artifact reference;
- before/after behavior;
- interpretation and claim supported;
- limitations, skipped checks, and remaining uncertainty.

Use [`EVIDENCE/TEMPLATE.md`](EVIDENCE/TEMPLATE.md) for substantial, reusable, externally stored, or review-critical evidence. Small routine evidence may stay in the issue or HANDOFF. Do not paste secrets, personal data, credentials, or unnecessarily large generated logs into the repository; preserve a safe excerpt and durable location instead.

If a test cannot run, record `NOT RUN`, the attempted command if any, the reason, and the consequence. A skipped, unavailable, flaky, or partially executed check is not a pass. Never claim success from visual confidence, code inspection alone, or another participant's unverified summary.

Preserve original evidence. Append a correction with attribution when an observation was wrong; do not silently rewrite it.

## Unverified complexity

Treat every new abstraction, dependency, persistent state element, configuration dimension, background process, concurrency mechanism, and cross-module coupling as a cost requiring justification.

Do not assign a decorative score. For each cost, record:

- why simpler alternatives are insufficient;
- which requirement requires it;
- its ownership and failure modes;
- its contract, test, or evidence coverage;
- what remains unverified.

Complexity lacking coverage is technical debt. It must be removed, covered, or remain linked to an open issue explicitly accepted by the human owner; it must not disappear when the originating issue closes.

## Architecture drift review

At releases, subsystem milestones, significant ADRs, accumulations of new complexity, or owner request, arrange an independent architecture review.

The reviewer first derives the expected architecture primarily from `PROJECT_SPEC.md`, accepted ADRs, and executable contracts/tests, without using the current implementation as the design source. It then compares that expectation with the implementation and classifies each material difference:

- `ALIGNED`: implementation matches the expected architecture.
- `JUSTIFIED_DEVIATION`: a documented, evidence-backed difference remains compatible with higher authority.
- `UNJUSTIFIED_DRIFT`: no adequate authority or evidence supports the difference.
- `UNKNOWN`: evidence is insufficient to classify it.

Record differences as evidence and issues. Do not automatically rewrite the system; remediation or acceptance follows normal authority and review rules.

## Background and asynchronous work

Do not start a task that can outlive the current session unless another participant can query and reconcile it without that session.

Before yielding, record in HANDOFF: task ID, purpose, owner, start time, process ID or durable remote reference, query/recovery command, last observation time, state, and terminal evidence location. Use `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, or `ORPHANED`.

Observe foreground work to completion when practical. For recorded background work, poll to a terminal state when within scope and update HANDOFF whether it succeeds, fails, or is cancelled. A takeover participant must query the recorded reference before treating it as active.

## Failure and interruption handling

When context, quota, time, or tool limits approach, stop early enough to leave a coherent repository. Record:

- what is complete and partial;
- exact files and relevant local state;
- commands run and results;
- failed or unavailable checks;
- active issue state and residual uncertainty;
- all background-task lifecycle data;
- exactly one bounded next action.

For terminal or network interruption, tool failure, partial implementation, inconsistent repository state, missing evidence, or an incomplete prior HANDOFF, preserve what can be verified and label the rest `UNKNOWN`. Do not repair by guessing. Do not mark an issue closed merely to make the handoff tidy.

## HANDOFF maintenance

Keep the five top-level operational sections in [`HANDOFF.md`](HANDOFF.md):

1. Current State
2. Active Issues
3. Next Action
4. Recent Activity
5. Archived Summary

Current State is a concise present-tense snapshot with evidence references, verification actually performed, unverified complexity, constraints, and non-terminal background tasks. Start it with the snapshot's updated UTC, repository revision/branch/upstream and dirty state when available, evidence cutoff, timestamped external checks that affect current claims, and explicit staleness triggers. Active Issues is a compact index of unresolved records only; meaningful detail and closed history belong in `ISSUES/`. Next Action contains exactly one bounded action. If work is terminal or waiting, use one explicit terminal or unblock instruction instead of inventing work. Recent Activity is newest first and attributable.

Participants may reconcile shared Current State and the active index when new evidence changes reality, but must add their own activity entry and must not rewrite another participant's activity or evidence. Disagreement is a new record, not an erasure.

When HANDOFF approaches 1,000 lines or becomes hard to scan, compact it. Retain at least the ten newest detailed entries plus every entry needed by unresolved issues, disputes, unverified claims, or non-terminal background tasks. Move closed issue bodies, long evidence narratives, and terminal-task ledgers to their owning durable records or immutable version-control history. Preserve links to ADRs, issues, evidence, rejected approaches, major reasoning, and the pre-compaction revision/digest in Archived Summary. Log the compaction as new activity.

## Before stopping

1. Re-read the diff or changed files and remove accidental scope.
2. Run proportionate verification and record exact results.
3. Obtain any required independent review and human authority.
4. Update issue, evidence, ADR, and human-checkpoint records at their source of ownership.
5. Reconcile background tasks.
6. Reconcile any accepted milestone's issue-embedded machine state with its human-readable issue lifecycle and HANDOFF pointer; a conflict is a failure, not permission to choose the convenient record.
7. Update HANDOFF's snapshot, active index, verification, activity, and exactly one next action.
8. Report what changed, what was verified, and what remains uncertain without overstating completion.
