# Synthetic Minimal Initialization Example

This example is fictitious and exists only to demonstrate initialization. It is not live project state, owner approval, or executed verification. The example deliberately records unavailable tests as `NOT RUN` rather than inventing a passing result.

## Scenario

`LabelKey` is a hypothetical, language-neutral library that converts a user-visible label into a stable lowercase key. Its owner has approved only two observable rules: trim outer whitespace and replace each run of internal whitespace with one hyphen. Empty-input behavior remains undecided.

After copying this package into the fictional repository, its protocol-related tree would be:

```text
BOOTSTRAP.md
PROJECT_SPEC.md
HANDOFF.md
HUMAN_CHECKPOINT.md
PROMPTS.md
ADR/
  TEMPLATE.md
ISSUES/
  TEMPLATE.md
  ISSUE-20300101T090000Z-empty-input-contract.md
EVIDENCE/
  TEMPLATE.md
```

No ADR or evidence record exists yet because no durable architecture decision or substantial observation has been made.

## Filled `PROJECT_SPEC.md` excerpt

```markdown
## Authority and status

- **Status:** `ACCEPTED`
- **Human technical owner:** `human:technical-owner`
- **Accepted by:** `human:technical-owner` (synthetic example)
- **Acceptance date:** `2030-01-01T08:30:00Z` (synthetic example)

### REQ-KEY-001 — Normalize whitespace

- **Requirement:** The library MUST trim outer whitespace and replace every non-empty run of internal whitespace with one hyphen.
- **Acceptance evidence:** Executable examples cover no whitespace, outer whitespace, and multiple internal whitespace characters.

## Assumptions and open decisions

| Certainty | Statement | Evidence or decision needed | Owner |
|---|---|---|---|
| `UNKNOWN` | Behavior for an empty or whitespace-only input is not specified. | Human owner defines the public contract. | `human:technical-owner` |
```

The accepted rule authorizes implementation of whitespace normalization. It does not authorize an agent to invent empty-input behavior.

## Initialized `HANDOFF.md` excerpt

```markdown
## Current State

- **CONFIRMED — Specification:** REQ-KEY-001 is accepted; empty-input behavior remains UNKNOWN.
- **CONFIRMED — Implementation:** No source implementation was found during repository inspection.
- **CONFIRMED — Verification:** No executable test entry point exists yet; no tests were run.
- **CONFIRMED — Background tasks:** None were recorded or observed.

## Active Issues

| Issue | Status | Severity | Owner | Authority | Review | Summary | Evidence or unblock condition |
|---|---|---|---|---|---|---|---|
| `ISSUE-20300101T090000Z-empty-input-contract` | `BLOCKED` | `MEDIUM` | `UNASSIGNED` | `HUMAN` | `INDEPENDENT` | Define empty-input public behavior. | Owner accepts an update to PROJECT_SPEC. |

## Next Action

Inspect the repository for owner-authorized runtime and test tooling; if none exists, prepare a tooling decision request without adding a dependency.
```

That Next Action is safe because it gathers evidence without choosing a runtime, framework, dependency, or unresolved product behavior.

## Issue excerpt

```markdown
- **ID:** `ISSUE-20300101T090000Z-empty-input-contract`
- **Status:** `BLOCKED`
- **Authority:** `HUMAN`
- **Review:** `INDEPENDENT`

## Problem

The public result for empty or whitespace-only input is UNKNOWN. Choosing an error, empty key, or sentinel would create a public contract without owner authority.

## Blocker

- **Blocked from:** `INVESTIGATING`
- **Blocker:** No accepted requirement defines empty-input behavior.
- **Unblock owner:** `human:technical-owner`
- **Unblock condition:** The owner accepts the behavior in PROJECT_SPEC. An ADR alone cannot resolve this product-contract gap.

## Verification

| UTC time | Participant | Command or procedure | Result and exit status | Evidence | Limitations |
|---|---|---|---|---|---|
| `2030-01-01T09:00:00Z` | `agent:example` | `NOT RUN` | No implementation or test entry point exists. | Repository inspection only. | No behavioral claim is verified. |
```

## First participant invocation

The owner supplies the Fresh implementor prompt from [`PROMPTS.md`](PROMPTS.md), scoped to REQ-KEY-001. The participant still reads [`BOOTSTRAP.md`](BOOTSTRAP.md), inspects the real repository, and replaces all synthetic facts with evidence. It does not copy this example's approvals, timestamps, or issue IDs into a live project.
