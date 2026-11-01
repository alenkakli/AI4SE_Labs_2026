---
name: architecture-design-skill
description: "Use when turning software requirements into architecture proposals, comparing architectural styles and trade-offs, selecting a justified design, or creating/revising an Architecture Decision Record (ADR)."
argument-hint: "Describe the system, requirements, and desired output or ADR path."
---

# Requirements-to-Architecture and ADR

## Purpose

Guide a requirements-led architecture discussion from source material to distinct proposals, a justified recommendation, and a reviewable ADR. Keep decisions traceable to evidence, explain implementation-level consequences, and avoid presenting assumptions or architecture patterns as facts.

## Workflow

### 1. Establish scope and evidence

1. Read the actual requirements and any relevant task instructions, prior discussion notes, existing architecture documents, and repository conventions before proposing a design.
2. Identify the system boundary, users, principal use cases, data and external systems, constraints, and quality attributes. Note which requirements are explicit, inferred, or unknown.
3. If an unknown could materially change the recommendation, ask focused clarifying questions. Otherwise proceed with clearly stated assumptions and record open questions.
4. If the task expects a discussion record, keep concise notes as the conversation progresses. Record proposals, user preferences, trade-offs, unresolved questions, and decisions; do not fabricate approval or claim an unrecorded review.

### 2. Propose genuinely distinct alternatives

1. Present at least three meaningfully different candidate architectures when the request or assignment calls for three. Select candidates that fit the system; explain when a candidate is unsuitable rather than treating it as a straw man.
2. Distinguish application structure from deployment/runtime choices. For example, layered or client-server describes structure, while modular monolith, microservices, and serverless describe different boundaries or operating models; these patterns can be combined.
3. Describe each proposal concretely: components or modules, responsibilities and ownership, interactions, data stores, deployment shape, and a representative end-to-end workflow.
4. Compare alternatives against the same criteria, including fit to requirements, consistency and failure behavior, scalability, security, testability, delivery/operational effort, cost, and reversibility. Make trade-offs and painful low-level implementation work explicit.
5. For workflows involving competing updates or multiple components (such as checkout and inventory), explain the consistency model, transaction or reservation approach, concurrency behavior, retries, idempotency, compensation, and failure cases appropriate to each proposal.
6. Explain commonly used patterns only when useful to the decision. Avoid unsupported popularity or universal-best claims; state whether patterns are composable and why they fit this system.

### 3. Facilitate and converge

1. Invite the user to challenge proposals, request implementation detail, or state priorities. Incorporate their feedback and update comparisons rather than repeating generic descriptions.
2. Recommend one option using explicit requirement-to-decision reasoning. State conditions that would make another alternative preferable and how the design could evolve.
3. Keep the decision proportionate to known needs. Prefer the least complex option that meets the requirements, without obscuring material risks or operational costs.

### 4. Create or revise the ADR

1. Use the repository's existing ADR format if one exists; otherwise start from [ADR_TEMPLATE.md](./ADR_TEMPLATE.md).
2. Write the ADR as a standalone decision record, not a transcript. Include a descriptive title, status, date when appropriate, decision owners if known, and scope.
3. Capture context and requirements, the decision and its rationale, a logical diagram, component/module responsibilities, important data ownership and interaction rules, and implementation guidance relevant to the decision.
4. Include alternatives considered with their benefits, costs, and reasons for rejection or deferral. Explain consequences, safeguards, operational/evolution guidance, and unresolved questions.
5. Make implementation advice specific enough to act on but do not invent frameworks, providers, traffic targets, regulatory obligations, or business rules absent from the source. Label examples and assumptions.
6. Mark a recommendation as **Proposed** unless the discussion records formal acceptance. Do not imply stakeholder approval that did not occur.
7. Revise the ADR in response to review requests (for example, add a comparison table, diagram, or deeper implementation detail) while preserving the original decision evidence and avoiding unrelated scope.

### 5. Verify the deliverable

- Check that every major requirement is addressed by the selected architecture or explicitly left open.
- Ensure alternatives are distinct, fairly represented, and compared on consistent criteria.
- Trace the recommendation to stated requirements, constraints, and user priorities.
- Check diagrams, terminology, and examples against the prose; ensure transactional and failure claims are technically consistent.
- Confirm status, assumptions, open questions, and unresolved decisions are explicit.
- Save deliverables at the requested paths. Report what was created and any remaining uncertainty; do not claim tests, approval, or validation that did not happen.

## Expected output

Depending on the request, produce:

- concise discussion notes that preserve the key proposals and decisions;
- an alternatives comparison and a justified recommendation; and
- a standalone ADR with a diagram and actionable design guidance.

Do not automatically create a comparison report or implementation plan unless requested.
