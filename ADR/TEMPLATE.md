# ADR Template — Not a Decision Record

Copy this file to `ADR-YYYYMMDDTHHMMSSZ-short-slug.md`, replace every bracketed field, and preserve the ID for the life of the decision. Use ADRs only for durable architectural decisions, not routine implementation choices.

## Metadata

- **ID:** `ADR-[UTC timestamp]-[short-slug]`
- **Title:** `[decision title]`
- **Status:** `PROPOSED`
- **Created UTC:** `[timestamp]`
- **Author:** `[participant]`
- **Human technical owner:** `[role or identity]`
- **Owner approval:** `PENDING`
- **Related specification:** `[requirement links]`
- **Related issues:** `[issue links]`
- **Supersedes / superseded by:** `[ADR links or NONE]`

Allowed statuses are `PROPOSED`, `ACCEPTED`, `REJECTED`, and `SUPERSEDED`. Only `ACCEPTED` ADRs are authoritative. A durable decision that crosses the Human Authority Boundary requires explicit owner approval before acceptance.

## Context

`[Problem, forces, constraints, and why a durable decision is needed.]`

## Decision

`[The chosen architectural rule or structure stated precisely enough to evaluate future implementation.]`

## Human Authority Boundary assessment

- **Boundary crossed:** `[YES/NO]`
- **Reason:** `[public contract, persistence, dependency, security, complexity, etc.]`
- **Existing authorization:** `[clear PROJECT_SPEC/accepted ADR reference or NONE]`
- **Approval evidence:** `[owner, UTC time, durable reference, or PENDING]`

## Alternatives considered

### [Alternative]

- **Benefits:** `[benefits]`
- **Costs and risks:** `[costs]`
- **Reason not selected:** `[reason]`

## Consequences

### Positive

- `[consequence]`

### Negative and tradeoffs

- `[consequence]`

### Compatibility and migration

- `[impact, migration, rollback, or NONE]`

## Unverified complexity

| Cost introduced | Why necessary | Contract/test/evidence coverage | Residual gap and linked issue |
|---|---|---|---|
| `[abstraction/dependency/state/config/process/concurrency/coupling]` | `[reason]` | `[links]` | `[link or NONE]` |

## Evidence and assumptions

- **CONFIRMED:** `[claim and source]`
- **INFERRED:** `[claim, facts, and reasoning]`
- **UNKNOWN:** `[uncertainty and how to resolve it]`

## Independent review rounds

- **Required:** `[YES/NO and reason]`

Append one complete subsection per review round; never overwrite an earlier finding or disposition.

### [UTC timestamp] — [reviewer]

- **Reviewed repository state:** `[commit, hashes, files, or other durable reference]`
- **Scope:** `[requirements, architecture, implementation, contracts/tests, and evidence inspected]`
- **Commands or procedures:** `[exact checks performed]`
- **Findings and resolution conditions:** `[severity-ranked findings or NONE]`
- **Limitations:** `[what could not be checked]`
- **Residual risks:** `[risks remaining]`
- **Evidence:** `[links or inline observations]`
- **Disposition:** `[APPROVED/CHANGES_REQUIRED/BLOCKED]`
- **Prior-round resolution:** `[how earlier findings were resolved, or FIRST ROUND]`

## Status history

Append every status change. Never erase rejected alternatives or prior reasoning.

| UTC time | From | To | Actor | Reason and authority evidence |
|---|---|---|---|---|
| `[time]` | `NONE` | `PROPOSED` | `[participant]` | `[reason]` |
