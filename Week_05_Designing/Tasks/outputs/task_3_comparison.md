# NFFH architecture comparison

## Comparison

| Topic | After the skill | Before the skill |
|---|---|---|
| Alternatives | Modular monolith, domain microservices, and serverless functions; compared consistency, scalability, and operational cost. | [task_1_record.md](./task_1_record.md) covers the same three options and adds detailed follow-up discussion about their implementation and failure modes. It also distinguishes application structure from deployment style. |
| Recommendation | A modular monolith with a web UI/API, capability modules, relational persistence, and transactional checkout. | [architecture_decision_record.md](./architecture_decision_record.md) makes the same recommendation, explicitly combining layered internals with modular boundaries and assigning data/rules to specific modules. |
| Checkout and risks | Revalidate stock at checkout, update stock and create the order atomically, make retries idempotent, and clarify pickup and reservation rules. | The ADR is more actionable: conditional stock writes, transaction steps, order-line snapshots, example API operations, authorization safeguards, monitoring, and targeted tests. [task_2_record.md](./task_2_record.md) summarizes these additions and the ADR review iterations. |
| Open scope | Flagged payment, company onboarding, pickup capacity, multi-company carts, and reservation/cancellation behavior as unresolved. | The records also call out traffic, identity/privacy, notifications, and operational constraints, while avoiding unsupported assumptions. |

## Assessment

The solutions agree on the key decision and its rationale: keep inventory and order consistency within one transaction, and avoid distributed-system complexity until requirements justify it. After the skill was a sound high-level answer, but the before the skill recorded ADR is more complete as an implementation reference and more explicit about module ownership, operating guidance, and verification. The discussion records also contain useful design exploration that my concise proposals did not reproduce.

The skill provided a useful structure for requirements-led alternatives, trade-offs, assumptions, and an ADR. In the after the skill attempt, the skill-guided structure was sufficient to prepare both answers without iterative back-and-forth about the architecture or ADR, unlike the multiple review iterations recorded for Task 2 before the skill. Avoiding that discussion likely saved time, though no exact time savings were measured.
