# Academic Sludge Line — Project Specification

**Version:** 0.1
**Project:** Academic Sludge Line (ASL)

## Authority and status

- **Status:** `ACCEPTED`
- **Human technical owner:** `human:technical-owner`
- **Accepted by:** `human:technical-owner`
- **Acceptance date:** `2026-08-24T02:40:51Z`
- **Supersedes:** `NONE`
- **Last material change:** `2026-08-24T02:40:51Z` — the owner-authored v0.1 specification was accepted unchanged in behavioral meaning during the first protocol adoption.
- **Authority record:** [`ADR-20260824T024051Z-protocol-adoption`](ADR/ADR-20260824T024051Z-protocol-adoption.md) and [`ISSUE-20260824T024051Z-protocol-adoption-recovery`](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md)

---

## 1. Purpose

Academic Sludge Line is a local-first, model-agnostic workflow for producing and iteratively improving research-paper drafts from heterogeneous research materials.

Its core purpose is not merely to generate text. It is to manage a traceable research-writing iteration loop in which:

1. source material is made reliably accessible to the models performing the work;
2. a writer produces a candidate draft;
3. one or more reviewers identify weaknesses and improvement priorities;
4. those findings influence both the next revision and the evidence emphasized in the next iteration;
5. a quality gate determines whether the candidate actually improves upon the currently accepted version;
6. weaker candidates remain auditable but do not automatically replace a stronger accepted version.

The system MUST NOT assume that a later iteration is better simply because it is newer.

---

## 2. Product Principles

### 2.1 Iteration is not improvement

A generated revision is a **candidate**, not an automatic successor.

Every candidate that is eligible to replace the current accepted draft MUST pass an explicit evaluation process.

The system therefore distinguishes:

- chronological version order;
- candidate lineage;
- accepted version;
- evaluation outcome.

These concepts MUST NOT be collapsed into a single "`latest version`" concept.

### 2.2 Evidence should remain accessible without overwhelming the working context

ASL may operate over more research material than can or should be included verbatim in a single model prompt.

The system MUST therefore distinguish:

- whether evidence is available;
- whether it is selected for the current task;
- the resolution at which it is exposed to a model.

A source may, for example, be available to the project while being represented in one iteration by metadata or an abstract and in another iteration by relevant excerpts or full text.

### 2.3 Review should drive subsequent attention

Reviewer findings are not merely prose appended after a draft.

They are signals that SHOULD influence:

- revision priorities;
- evidence selection;
- evidence resolution;
- subsequent reviewer attention.

The resulting loop is intentionally review-driven:

**draft → review → identify weaknesses → refocus evidence → revise → evaluate**

### 2.4 Model choice belongs to roles, not to the pipeline

Writer, reviewer, scorer, planner, researcher, or other roles MUST NOT be permanently coupled to a specific model provider or invocation mechanism.

A workflow role defines **what work must be performed**.

A model binding defines **who performs it**.

### 2.5 Input normalization must preserve meaning and uncertainty

Research material arrives in heterogeneous formats.

Successful extraction of text is not equivalent to successful understanding of a document.

ASL MUST preserve useful document structure and MUST surface extraction uncertainty or information loss instead of silently presenting degraded representations as authoritative source content.

### 2.6 Research provenance matters

Material discovered, loaded, extracted, transformed, summarized, or cited by the pipeline SHOULD remain traceable to its origin.

ASL MUST NOT fabricate references or represent unverified search results as verified evidence.

---

# 3. Core Product Model

A paper project consists conceptually of:

```text
Project
├── project intent
├── research materials
├── normalized evidence
├── model/role configuration
├── iteration history
│   ├── candidate drafts
│   ├── reviewer outputs
│   ├── revision plans
│   ├── evidence focus
│   └── evaluation results
└── accepted version
```

The exact persistence format is an implementation decision unless specified elsewhere.

---

# 4. Functional Requirements

## 4.1 Versioned Iteration

ASL MUST maintain an explicit history of generated paper versions.

Each iteration MUST preserve enough metadata to determine:

- which version or checkpoint it was derived from;
- which version was accepted when the iteration began;
- what evidence context was emphasized;
- what reviewer feedback informed it;
- what model bindings performed major roles;
- whether the candidate was accepted or rejected.

Rejected candidates MUST remain inspectable.

Generating a rejected candidate MUST NOT destroy or overwrite the accepted version.

---

## 4.2 Quality Gate

ASL MUST implement an explicit quality gate between candidate generation and accepted-version replacement.

The gate MUST evaluate a candidate against the relevant accepted baseline rather than assuming chronological progress.

Conceptually:

```text
accepted baseline
      │
      ▼
candidate revision
      │
      ▼
evaluation
   ┌──┴──┐
accept  reject
   │      │
   ▼      ▼
candidate previous accepted
becomes   remains authoritative
accepted
```

The evaluation mechanism MAY evolve, but the presence of the gate is a product invariant.

Evaluation results MUST be persisted with sufficient rationale or structured output to make the decision auditable.

The gate SHOULD support configurable evaluation policies rather than embedding one permanent scoring implementation.

Possible policies may include:

- rubric scoring;
- pairwise comparison;
- reviewer consensus;
- judge-model evaluation;
- composite evaluation.

This list is non-exhaustive and does not mandate a specific implementation.

---

## 4.3 Reviewer Panel

ASL MUST support review as a first-class stage of the iteration process.

The architecture MUST NOT assume exactly one reviewer.

A project or workflow MUST be capable of using multiple independent reviewers, including at least a three-reviewer configuration.

Reviewers MAY:

- use different models;
- use different providers;
- evaluate different dimensions;
- share a rubric;
- use role-specific instructions.

Reviewer execution and reviewer-result aggregation SHOULD remain separable concerns.

A lightweight single-reviewer configuration MAY remain available for lower-cost or fast runs.

Support for lightweight operation MUST NOT structurally prevent richer reviewer-panel configurations.

---

## 4.4 Revision Guidance

Reviewer findings MUST be usable as structured input to subsequent iterations.

The system SHOULD identify actionable revision priorities rather than treating reviewer reports only as human-facing prose.

Useful signals may include:

- unsupported claims;
- methodological weaknesses;
- missing analysis;
- unclear reasoning;
- insufficient discussion;
- underused references;
- contradictory evidence;
- writing or structure problems.

A revision stage MAY synthesize findings from multiple reviewers into a revision plan.

---

## 4.5 Evidence Focus and Rotation

ASL MUST preserve the ability to vary the amount of attention given to individual references across iterations.

The mechanism MUST support both:

### Review-driven focus

Evidence relevant to weaknesses identified by reviewers SHOULD receive increased attention in subsequent iterations.

### Coverage-driven rotation

Sources that have received little detailed attention SHOULD progressively receive opportunities for higher-resolution inspection so that the workflow does not repeatedly privilege only the same early or highly ranked references.

Persistent anchor references MAY remain emphasized across multiple iterations when appropriate.

The system SHOULD record focus history so that evidence allocation decisions are auditable.

---

## 4.6 Evidence Resolution

Evidence exposure MUST support multiple levels of representation.

Examples include:

```text
metadata only
abstract / summary
selected excerpts or chunks
structured tables / extracted assets
full text
```

The specific levels MAY vary by source type.

The system SHOULD choose evidence resolution according to:

- current revision focus;
- relevance;
- available context budget;
- source importance;
- coverage history;
- model capabilities.

The system MUST NOT equate "not included in the current prompt" with "not available to the project."

---

## 4.7 Evidence Accessibility

Local and externally discovered research material SHOULD be exposed through a common conceptual evidence-access boundary.

Evidence may originate from:

- local files;
- local folders;
- academic papers;
- seed drafts;
- datasets;
- structured tables;
- academic metadata/search services;
- web research;
- other explicitly configured sources.

The architecture SHOULD permit future roles or tool-capable models to locate and inspect available project evidence on demand instead of requiring all usable material to be permanently embedded into every prompt.

This requirement does not mandate a database, vector database, RAG framework, or any specific retrieval implementation.

---

## 4.8 Smart Loading and Normalization

ASL MUST retain a document-ingestion layer for converting heterogeneous source formats into model-usable representations.

The loader MUST be treated as a semantic normalization boundary rather than a simple "`file to string`" converter.

Where applicable, normalization SHOULD preserve:

- document metadata;
- section hierarchy;
- paragraphs;
- tables;
- figure captions;
- references;
- page or location information;
- other useful structural boundaries.

Data-oriented sources SHOULD preserve meaningful structure rather than unnecessarily flattening everything into prose.

The loader SHOULD support adapter- or backend-specific handling for unusual formats, including sources whose layout or encoding is not handled correctly by generic document parsers.

### Extraction uncertainty

The loader MUST NOT silently hide known extraction failures.

When meaningful information may be lost or degraded, it SHOULD expose warnings such as:

- OCR required or low-confidence OCR;
- unreadable pages;
- malformed tables;
- lost equations;
- failed figure extraction;
- uncertain reading order;
- incomplete document parsing;
- unsupported format features.

Downstream models SHOULD be able to distinguish source absence from extraction failure where practical.

---

## 4.9 Role-Based Model Binding

Every major model-driven role SHOULD be independently configurable.

Potential roles include:

- research planner;
- researcher;
- writer;
- reviewer;
- revision planner;
- evaluator / scorer / judge.

The architecture MUST allow different roles to use different models.

A role binding SHOULD support, where practical:

1. remote API providers using API credentials;
2. OpenAI-compatible or equivalent HTTP endpoints, including locally hosted inference servers;
3. local or remote model endpoints;
4. agent/CLI subprocess backends where the invoked agent itself may possess tools.

The pipeline MUST NOT require all roles to share one provider.

Example conceptual configuration:

```text
writer
  → local model endpoint

reviewer-methodology
  → provider A

reviewer-literature
  → provider B

reviewer-writing
  → local model

quality judge
  → stronger remote model
```

Provider-specific details MUST remain below the workflow-role abstraction where practical.

Fallback model chains MAY be supported.

Secrets MUST NOT be written into normal project artifacts or committed configuration.

---

## 4.10 Capability-Aware Execution

Different model bindings may provide different capabilities.

The system SHOULD be able to represent relevant capabilities such as:

- normal text generation;
- structured output;
- tool use;
- local file/tool access;
- web access;
- context capacity.

Workflow logic SHOULD depend on required capabilities rather than on hard-coded provider names wherever practical.

---

## 4.11 Research Discovery

ASL MAY discover candidate evidence through academic metadata services, web research, tool-capable agents, or other configured research mechanisms.

Discovered material MUST retain provenance.

The system MUST distinguish candidate research leads from verified sources.

A search result or bibliographic lead MUST NOT automatically become authoritative evidence merely because it was returned by a search service.

---

## 4.12 Grounding and Citation Discipline

ASL MUST NOT knowingly fabricate citations.

When evidence is missing, incomplete, inaccessible, or unverified, the workflow SHOULD preserve explicit uncertainty rather than invent supporting material.

Depending on the stage, this may take forms such as:

- TODO markers;
- unresolved evidence requirements;
- citation verification warnings;
- reviewer findings;
- source-status metadata.

Draft generation and evidence verification are related but MUST NOT be treated as identical operations.

---

## 4.13 Human-Directed Iteration

A user SHOULD be able to influence an iteration without discarding project history.

Useful interventions include:

- selecting an earlier checkpoint as the revision starting point;
- adding references or data;
- supplying revision focus;
- changing model bindings;
- changing reviewer configuration;
- changing evidence-allocation strategy.

Starting from an exploratory or older checkpoint MUST NOT implicitly redefine the accepted quality baseline.

---

# 5. Pipeline Semantics

The intended high-level workflow is:

```text
research material
       │
       ▼
ingestion / normalization
       │
       ▼
available evidence
       │
       ▼
research / planning
       │
       ▼
evidence allocation
       │
       ▼
writer
       │
       ▼
candidate draft
       │
       ▼
reviewer panel
       │
       ├───────────────┐
       ▼               ▼
revision signals   quality evidence
       │               │
       ▼               ▼
future evidence    quality gate
focus                  │
                  ┌────┴────┐
                  ▼         ▼
                accept    reject
                  │
                  ▼
            next baseline
```

Individual stages MAY be combined or split by an implementation, but doing so MUST preserve the observable semantics defined by this specification.

---

# 6. Logical Architecture Boundaries

The following conceptual responsibilities SHOULD remain separable even if early implementations colocate them.

## 6.1 Ingestion / Normalization

Responsible for understanding heterogeneous input formats and producing reliable model-usable representations.

## 6.2 Evidence Management

Responsible for provenance, availability, selection, resolution, and evidence-access history.

## 6.3 Workflow Orchestration

Responsible for iteration lifecycle, stage execution, lineage, checkpoints, and artifact production.

## 6.4 Model Execution

Responsible for invoking configured models or agents without embedding provider semantics into research-workflow logic.

## 6.5 Review and Evaluation

Responsible for critique, revision signals, quality evidence, aggregation, and acceptance decisions.

These boundaries describe responsibilities, not mandatory Python modules or classes.

---

# 7. Local-First Operation

ASL SHOULD remain usable as a local workflow.

Core operation MUST NOT require a hosted ASL service.

The use of remote model providers, academic APIs, or web research MAY require network access, but local models and local evidence MUST remain valid first-class execution paths.

The project MUST NOT require a cloud database, queue, container platform, or distributed service merely to run the core paper-iteration workflow.

Such infrastructure may be introduced only when justified by a future requirement.

---

# 8. Auditability

For each materially significant iteration, ASL SHOULD preserve enough information to reconstruct:

- the starting draft;
- the accepted baseline;
- model bindings;
- reviewer outputs;
- revision guidance;
- evidence focus;
- relevant evidence provenance;
- evaluation outcome;
- generated candidate.

The goal is not perfect deterministic replay of stochastic model generation.

The goal is to make the reasoning and evidence path behind a version inspectable.

---

# 9. Non-Goals

ASL is not intended to:

- assume every generated revision is an improvement;
- permanently bind the workflow to one model vendor;
- require all references to fit into one prompt;
- reduce every document or dataset to unstructured plain text;
- hide ingestion failures;
- fabricate evidence or citations;
- treat search results as automatically verified facts;
- replace human scientific judgment;
- guarantee scientific correctness solely because multiple models agree;
- mandate a particular RAG framework, vector store, orchestration framework, database, or model-serving stack;
- rewrite the entire existing implementation merely to satisfy a preferred architecture style.

---

# 10. Compatibility and Refactoring Requirements

The current ASL implementation predates this specification.

Therefore, the first protocol-driven refactor MUST begin with reconciliation rather than assumption.

Existing behavior SHOULD be classified as one of:

1. behavior required by this specification;
2. useful behavior compatible with this specification;
3. implementation detail that may change;
4. accidental behavior that should not become a requirement;
5. behavior that conflicts with this specification and requires explicit resolution.

The refactor MUST preferentially preserve validated behavior while improving architecture around it.

A code rewrite is not itself a project objective.

Implementation convenience MUST NOT silently redefine this specification.

---

# 11. Initial Behavioral Invariants

The first refactoring phase MUST preserve or establish automated evidence for the following invariants:

1. A candidate version cannot silently overwrite the accepted version.
2. A lower-quality or rejected candidate remains available for inspection.
3. Quality evaluation compares against the accepted baseline.
4. An iteration may begin from a checkpoint other than the accepted baseline without changing the quality-gate baseline.
5. Reviewer findings can influence the next revision.
6. Reviewer findings can influence subsequent evidence focus.
7. Evidence focus can rotate to improve reference coverage over multiple iterations.
8. Evidence can be exposed at different resolutions instead of using an all-or-nothing full-text policy.
9. At least three independent reviewers can be configured without redesigning the pipeline.
10. Individual workflow roles can bind independently to different models or backends.
11. Local model endpoints are first-class model bindings.
12. Heterogeneous source formats pass through an explicit normalization layer.
13. Known extraction degradation is surfaced rather than silently discarded.
14. Evidence and discovered research leads retain provenance.
15. Unverified evidence is not silently promoted to verified citation support.

---

# 12. Initial Completion Criteria

ASL satisfies the initial architecture objective of this specification when all of the following are true:

- the core iteration lifecycle is explicitly represented and tested;
- accepted-version and candidate-version semantics are unambiguous;
- quality-gate behavior is protected by executable tests;
- review is represented as a configurable panel rather than a single hard-wired invocation;
- a three-reviewer workflow can run;
- review output can drive subsequent revision focus;
- review output can influence evidence allocation;
- evidence focus and coverage history are preserved;
- evidence exposure supports multiple resolutions;
- smart loading is behind an explicit normalization contract;
- normalization failures or fidelity warnings can propagate downstream;
- major workflow roles use a provider-independent model-binding boundary;
- API providers and local model endpoints can be selected per role;
- existing supported paper workflows continue to function unless an intentional, authorized change is recorded;
- repository evidence demonstrates the above behavior.

---

# 13. Specification Authority and Evolution

This file defines product intent, required behavior, and completion criteria for Academic Sludge Line.

It does **not** describe current implementation merely because current implementation exists.

Implementation behavior alone MUST NOT redefine project requirements.

If implementation and this specification disagree, the disagreement MUST be surfaced rather than silently rationalized.

Requirements may evolve when there is explicit owner authorization or other accepted evidence establishing that the intended product behavior has changed.

Such changes SHOULD be traceable through the project's engineering-governance artifacts.

Architecture decisions that refine *how* these requirements are implemented belong in ADRs rather than being retroactively inferred from code.

---

# 14. Open Design Decisions

The following questions are intentionally not resolved by this first specification:

- the exact reviewer-aggregation algorithm;
- whether three reviewers become the default or remain an explicit configuration;
- the exact scoring rubric used by the quality gate;
- whether the final gate uses reviewer consensus, a dedicated judge, deterministic metrics, or a composite;
- the canonical internal evidence-resource schema;
- the exact retrieval/search implementation;
- whether embeddings or vector search are useful;
- whether resource access is implemented through tools, APIs, direct filesystem access, or multiple mechanisms;
- the preferred local inference server;
- the exact parser strategy for unusual academic-document formats;
- the degree to which figures, equations, and multimodal material are preserved;
- whether model capability discovery is static configuration or runtime negotiation.

These decisions require implementation recovery, experiments, or owner decisions and MUST NOT be invented merely to begin the refactor.

---

# 15. Specification Change Record

| UTC time | Change | Reason | Approved by | References |
|---|---|---|---|---|
| `2026-08-24T02:40:51Z` | Accepted owner-authored v0.1 without changing its behavioral wording | Establish durable product-intent authority for the first protocol-governed recovery and later refactoring | `human:technical-owner` | [`ADR-20260824T024051Z-protocol-adoption`](ADR/ADR-20260824T024051Z-protocol-adoption.md), [`ISSUE-20260824T024051Z-protocol-adoption-recovery`](ISSUES/ISSUE-20260824T024051Z-protocol-adoption-recovery.md) |
