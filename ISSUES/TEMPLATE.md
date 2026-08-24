# Issue Template — Not an Active Issue

Copy this file to `ISSUE-YYYYMMDDTHHMMSSZ-short-slug.md`, replace every bracketed field, and preserve its ID and history. Meaningful work, contradictions, blocked work, and uncertainty that can outlive a run require an issue file.

## Metadata

- **ID:** `ISSUE-[UTC timestamp]-[short-slug]`
- **Title:** `[short title]`
- **Status:** `OPEN`
- **Severity:** `[LOW/MEDIUM/HIGH/CRITICAL]`
- **Owner:** `[participant or UNASSIGNED]`
- **Authority:** `[AGENT/HUMAN]`
- **Review:** `[SELF/INDEPENDENT]`
- **Created UTC:** `[timestamp]`
- **Updated UTC:** `[timestamp]`
- **Requirements:** `[PROJECT_SPEC references]`
- **ADRs:** `[accepted/proposed ADR links or NONE]`
- **Evidence:** `[evidence links or NONE YET]`
- **Milestone:** `[accepted PROJECT_SPEC milestone ID or NONE]`

Primary states are `OPEN`, `INVESTIGATING`, `IMPLEMENTING`, `VERIFYING`, `REVIEW`, and `CLOSED`. `BLOCKED` records a temporary side state. Code written is not closure.

## Problem

`[Observed gap, contradiction, defect, risk, or decision needed. Describe impact without assuming the cause.]`

## Evidence or reproduction

`[Exact reproduction, observed behavior, source conflict, or evidence links. Label unsupported parts UNKNOWN.]`

## Expected behavior

`[Requirement, accepted ADR, or contract that defines the expected result.]`

## Assumptions

- **CONFIRMED:** `[claim and source]`
- **INFERRED:** `[claim, facts, and reasoning]`
- **UNKNOWN:** `[claim and resolution path]`

## Investigation and decision

`[Findings, alternatives, chosen approach, and authority basis. Link a proposed ADR rather than embedding a durable architectural decision here.]`

## Change

- **Files or components:** `[paths/components]`
- **Behavior changed:** `[before/after]`
- **Out-of-scope work deliberately excluded:** `[items or NONE]`
- **Rollback or recovery:** `[procedure or NOT APPLICABLE]`

## Unverified complexity

| Cost | Justification | Coverage | Residual issue |
|---|---|---|---|
| `[category or NONE]` | `[why required]` | `[contract/test/evidence]` | `[link or NONE]` |

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `[time]` | `[participant]` | `[exact command/procedure or NOT RUN]` | `[result]` | `[link/concise output]` | `[limitations]` |

## Pipeline state (optional)

Use this section only when an accepted specification and compatible accepted ADR define an executable milestone schema. The machine block is operational lifecycle state inside this owning issue; it cannot authorize or restate scope. Ordinary issues write `NOT APPLICABLE` and omit the markers.

Required state fields and transitions come from the accepted milestone contract/ADR. Preserve the event array append-only. A tool must refuse missing, duplicate, malformed, unsupported, or authority-digest-mismatched state instead of inferring it.

`[A pipeline-managed issue replaces this paragraph with its exact AEP-PIPELINE-STATE markers and schema-valid JSON block. Otherwise: NOT APPLICABLE.]`

## Self-review

Complete this section when metadata says `Review: SELF`. It may also prepare an independently reviewed issue, but it never substitutes for required independent review.

- **Participant:** `[implementor]`
- **Reviewed UTC:** `[timestamp]`
- **Reviewed repository state:** `[commit, hashes, files, or other durable reference]`
- **Scope and authority references:** `[changed files/behavior plus requirements and accepted ADRs]`
- **Checks and evidence reviewed:** `[verification rows/evidence links]`
- **Findings and corrections:** `[findings and changes made, or NONE]`
- **Limitations:** `[what was not reviewed or verified]`
- **Residual risks:** `[remaining risks or NONE]`
- **Outcome:** `[COMPLETE/REWORK_REQUIRED/NOT_APPLICABLE]`

`COMPLETE` satisfies only a `SELF` review gate. Use `NOT_APPLICABLE` when the issue requires independent review and no preparatory self-review was recorded.

## Independent review rounds

- **Required:** `[YES/NO and reason]`

Append one complete subsection per review round. Never replace an earlier finding or disposition.

### [UTC timestamp] — [reviewer]

- **Reviewed repository state:** `[commit, hashes, files, or other durable reference]`
- **Reviewed target:** `[exact immutable target; required for pipeline-managed milestones]`
- **Open material findings:** `[nonnegative integer; required for pipeline-managed milestones]`
- **Scope:** `[requirements, ADRs, implementation, tests, and evidence inspected]`
- **Commands or procedures:** `[exact checks performed]`
- **Specification compliance:** `[findings and references]`
- **Correctness and regression findings:** `[findings]`
- **Architecture and complexity findings:** `[findings]`
- **Material findings and resolution conditions:** `[severity-ranked findings or NONE]`
- **Limitations:** `[what could not be checked]`
- **Residual risks:** `[risks remaining after this review]`
- **Evidence:** `[links or inline observations]`
- **Disposition:** `[APPROVED/CHANGES_REQUIRED/BLOCKED]`
- **Prior-round resolution:** `[how earlier findings were resolved, or FIRST ROUND]`

The disposition value must be exactly one of the three values above in both session-facing and durable reports. Put qualifiers and non-blocking findings in the finding/residual-risk fields; do not invent a fourth disposition. For pipeline-managed milestones, the recorded reviewer label must differ from the implementor label, but this comparison does not authenticate identity.

## Blocker

- **Blocked from:** `[prior state or NOT BLOCKED]`
- **Blocker:** `[specific condition or NONE]`
- **Unblock owner:** `[participant/role or UNKNOWN]`
- **Unblock condition:** `[observable condition or NONE]`

## Residual uncertainty

- `[Remaining uncertainty, consequence, and owner, or NONE.]`

## Activity history

Append meaningful transitions and corrections; do not replace prior findings.

| UTC time | Participant | From | To | Action, evidence, and reason |
|---|---|---|---|---|
| `[time]` | `[participant]` | `NONE` | `OPEN` | `[creation reason]` |

## Closure checklist

- [ ] Expected behavior is tied to a higher-authority source.
- [ ] The change or resolution is recorded.
- [ ] Required verification ran and evidence is linked; unavailable checks remain explicit.
- [ ] If `Review: SELF`, the Self-review outcome is `COMPLETE` and no independent-review risk category applies.
- [ ] If `Review: INDEPENDENT`, the latest review round is `APPROVED` and shows that prior material findings are resolved.
- [ ] Required human authority is recorded in the owning artifact: product/contract in `PROJECT_SPEC.md`, architecture in an accepted ADR, or both for a mixed decision.
- [ ] New complexity is covered, removed, or linked to an explicitly accepted open debt issue.
- [ ] Residual uncertainty is absent or explicitly owned.
- [ ] HANDOFF reflects the resulting current state and exactly one next action.
