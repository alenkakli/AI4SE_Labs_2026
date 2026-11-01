# Architecture Decision Record: <decision title>

| Field | Value |
|---|---|
| Status | Proposed / Accepted / Superseded |
| Date | <YYYY-MM-DD or unknown> |
| Decision owners | <names/roles or unknown> |
| Scope | <system or decision boundary> |

## Context and requirements

Describe the system, its relevant requirements, constraints, quality attributes, and the problem this decision addresses. Distinguish documented facts from assumptions. Link or identify the source requirements.

## Decision

State the selected architecture and the reasons it best meets the known requirements. Explain important boundaries, responsibilities, data ownership, and interaction choices.

### Logical architecture

```text
<Clients / users>
        |
<Interfaces and application components>
        |
<Data stores / external systems>
```

### Important workflows and implementation guidance

Describe the critical use cases, consistency requirements, failure behavior, security/authorization boundaries, and operational concerns that materially affect the decision. Keep technology choices conditional when the requirements do not specify them.

## Alternatives considered

| Alternative | Fit and benefits | Costs, risks, or reason deferred |
|---|---|---|
| <Option A> | <...> | <...> |
| <Option B> | <...> | <...> |
| <Option C> | <...> | <...> |

Explain why the selected option is preferred and under what conditions an alternative would become preferable.

## Consequences

### Benefits

- <...>

### Costs and safeguards

- <...>

## Evolution and operational guidance

Describe monitoring signals or changed requirements that should trigger revisiting this decision, and any safe incremental evolution path.

## Open questions

- <Unresolved requirement or decision; owner if known>

## References

- <Requirements, discussion notes, or related decisions>
