# Architecture Decision Record: NFFH Marketplace

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-01 |
| Decision owners | NFFH project team |
| Scope | Initial architecture for the NFFH farmer-to-consumer marketplace |

## Context

NFFH connects local farmers with consumers. Farmers manage their companies and produce inventory. Consumers discover companies and products, reserve produce, select a pickup day, and review their order history. The system also needs client, farmer, and administrator accounts; persistent login/logout; company and area browsing with map directions; and administrative maintenance of users, orders, areas, companies, and products.

The requirements describe 41 user stories but do not establish expected traffic, team size, deployment constraints, payment processing, notification requirements, or regulatory obligations. In particular, inventory and checkout consistency matter, but the requirements do not justify the operational cost of independently deployed services.

## Decision

Begin with a **modular monolith with layered internals**, exposed through an HTTP API to a web client. Use a relational database as the transactional source of truth for marketplace, inventory, cart, and order data.

Keep one deployable application and enforce business-capability boundaries in its code. Each module owns its rules and data access; modules interact through small, explicit in-process interfaces rather than importing one another's repositories or writing one another's tables.

### Logical structure

```text
Consumer / Farmer / Admin web clients
                 |
            HTTP API
                 |
       Application use cases
                 |
  +--------------+----------------------------+
  | Identity & Access | Companies & Areas     |
  | Catalog           | Inventory             |
  | Cart              | Orders & Pickup       |
  | Administration (role-aware use cases)     |
  +--------------+----------------------------+
                 |
      Relational database
        (transactional source of truth)
```

Within the application, use the following layers:

1. **Presentation/API:** request handling, authentication context, input validation, and response mapping.
2. **Application:** use cases that coordinate business operations and module interfaces.
3. **Domain:** business rules and invariants owned by each module.
4. **Persistence/infrastructure:** database access and external integrations.

| Module | Owns |
|---|---|
| Identity & Access | Accounts, authentication integration, roles, and authorization rules |
| Companies & Areas | Farmer/company profiles, service areas, and location information |
| Catalog | Product descriptions and published product information |
| Inventory | Available quantities and stock reservation rules |
| Cart | A consumer's in-progress selections |
| Orders & Pickup | Checkout coordination, order lifecycle, pickup-day selection, and order history |
| Administration | Administrative use cases and views over the owning modules; not a separate copy of their data |

## Implementation-level design

The following is a technology-neutral starting point. The requirements do not select a programming language, web framework, database vendor, or hosting provider, so this ADR defines responsibilities and consistency rules rather than prescribing a specific stack.

### Code organization and API

Organize the application by capability, then by layer within each capability. For example:

```text
src/
  identity/
    api/ application/ domain/ infrastructure/
  inventory/
    api/ application/ domain/ infrastructure/
  orders/
    api/ application/ domain/ infrastructure/
  companies/  catalog/  cart/  administration/
  shared/                 # stable primitives and technical infrastructure only
```

Module APIs are internal interfaces, not direct access to another module's repositories. Expose a versioned HTTP/JSON API to clients, with resource-oriented operations such as:

| Area | Example operations |
|---|---|
| Discovery | `GET /api/v1/companies`, `GET /api/v1/products?area=...` |
| Farmer management | `POST /api/v1/products`, `PATCH /api/v1/inventory/{productId}` |
| Cart and checkout | `GET/POST /api/v1/cart/items`, `POST /api/v1/checkout` |
| Orders | `GET /api/v1/orders`, `GET /api/v1/orders/{orderId}` |
| Administration | Explicit admin-only operations on the relevant owning resources |

Validate request shape and business rules at the API/application boundary. Return consistent client errors for invalid input, unauthenticated requests, and forbidden actions. Enforce roles and resource ownership on the server for every operation; hiding controls in the user interface is not authorization. Keep pagination and filtering bounded.

### Relational data and ownership

Use relational tables with foreign keys and constraints for transactional entities. A conceptual starting set is `accounts` (or an external identity reference), `companies`, `areas`, `products`, `inventory`, `carts`, `cart_items`, `orders`, and `order_lines`. Keep each table's writes behind its owning module even though the modules share one database.

Represent inventory quantity with an integer unit count where appropriate. If the domain later supports fractional weights, define and validate a suitable fixed-precision quantity representation. Use database constraints for invariants that can be expressed there, including non-negative stock, unique identity references, and valid foreign keys. Add indexes for observed access paths such as company/area discovery and a consumer's order history; validate indexes against actual queries rather than adding them indiscriminately.

Store order-line snapshots for fields needed to understand the historical order after a product changes or is removed. If prices are introduced, store the agreed price and currency on the order line rather than deriving past totals from the current catalog. Define retention and deletion behavior after privacy requirements are known.

### Checkout transaction

Implement checkout as one application use case in the Orders module. In one database transaction:

1. Authenticate the consumer and verify that the cart belongs to them; validate product availability and pickup-day rules.
2. Reserve quantities with a conditional write (for example, decrement only when the available quantity is at least the requested quantity) and verify that every requested row was updated.
3. Create the order and immutable order-line snapshots, then mark the cart as checked out.
4. Commit all writes together; on any validation or database failure, roll the transaction back.

Use suitable row-level locking or conditional updates so concurrent checkouts cannot oversell stock. Add a unique client idempotency key to checkout requests and enforce uniqueness in the database, allowing a safe retry after a timeout without creating a duplicate order. Test the behavior with concurrent requests against the real database engine used by the application.

Because payment and reservation expiry are not specified, do not introduce a payment workflow or long-lived stock holds in this initial decision. Clarify whether “reserve” means immediate order placement or a temporary hold before finalizing that lifecycle.

### Identity, external integrations, and operations

Keep identity implementation replaceable behind the Identity & Access module. Select a managed identity provider or a framework-supported solution during technology selection; avoid inventing a custom password protocol. Use secure session handling, least-privilege roles, and server-side authorization checks. Record security-relevant administrative changes with actor, action, target, and timestamp, subject to the eventual privacy and retention policy.

Treat map directions as a link or integration to a mapping provider, not as a reason to couple core checkout to that provider. Isolate provider-specific APIs and credentials behind infrastructure adapters.

Deploy the application as one stateless service so additional instances can be added if needed; keep durable state in the database. Use environment-specific configuration and secret storage, automated database migrations, health checks, and backups with a tested restore procedure. Apply migrations in a backward-compatible sequence when the deployed application and database may temporarily be on different versions.

At minimum, test module rules with unit tests; API, authorization, migrations, and checkout with integration tests; and key user journeys with a small end-to-end suite. Include duplicate checkout, concurrent last-item purchases, invalid pickup selections, and permission failures. Log structured request/order correlation IDs without logging passwords, tokens, or unnecessary personal data. Monitor request errors/latency, database health, and checkout outcomes.

## Checkout consistency summary

The initial design treats checkout as an atomic operation: stock changes and order creation either commit together or roll back together. Subsequent cancellation/restocking behavior belongs to the order lifecycle and must be specified before implementation. Payment remains out of scope until requirements establish otherwise.

## Consequences

### Benefits

- One application and database are simpler to deploy, test, debug, and operate than a distributed system.
- Relational transactions provide a straightforward way to protect inventory and order consistency.
- Capability boundaries make ownership explicit and allow internal implementations to change with less cross-module impact.
- The architecture leaves room to add infrastructure or extract a module if measurable needs emerge.

### Costs and safeguards

- A modular monolith does not provide independent service deployment or scaling.
- Module boundaries rely on code organization and team discipline; a single database can otherwise encourage coupling.
- Checkout coordination still needs clear order states, authorization checks, and tests for competing stock updates.

Use feature-oriented folders, keep shared code to stable primitives and technical infrastructure, and test module rules independently. Add end-to-end coverage for checkout and permissions. If cross-module imports begin to erode boundaries, introduce a dependency check in CI.

## Alternatives considered

### Domain microservices

Separate Identity & Access, Marketplace (companies, areas, catalog, and seller inventory), and Orders into independently deployed services, each owning its data. This can support independent scaling and team ownership, but adds network failures, observability and deployment overhead, eventual consistency, and distributed checkout coordination. A reservation workflow would need idempotent commands, timeouts, retries, and compensation. The current requirements provide no evidence that these costs are warranted. If independent scaling or release ownership becomes necessary, extract services incrementally along the established module boundaries.

### Serverless and event-driven architecture

Use managed identity, an API gateway, functions, managed data services, and events or workflows. This can suit variable demand and reduce server operations, but does not remove the need for transactional inventory reservation. It also introduces provider-specific behavior, delivery duplication, retries, event schema evolution, connection and quota limits, and more difficult end-to-end tracing. Use this selectively if demand or operational constraints justify it; do not make core checkout asynchronous merely to adopt events.

### Layered client-server application without explicit modules

This is a familiar structure, but layers alone do not define business ownership. The selected design combines layered internals with capability modules to make dependencies and data ownership clearer.

## Market patterns and fit

There is no single architecture that can responsibly be called “the most common” for all marketplaces: systems vary greatly in scale, team structure, and operating constraints, and no market-frequency study was part of this decision. The following are widely used patterns and are **composable**, not mutually exclusive choices:

| Pattern | What it describes | Typical fit for marketplace/e-commerce |
|---|---|---|
| Client-server / web API | Clients call a backend over HTTP or another network protocol | Standard way to support browser, mobile, and administrative clients |
| Layered application | Separates API/presentation, use cases, domain rules, and persistence | Common internal organization that helps keep concerns testable |
| Modular monolith | One deployable application with business-capability boundaries | Practical starting point for a small or medium product with one team and transactional workflows |
| Microservices | Independently deployed services with explicit data ownership | Useful when independent scaling, team autonomy, or release cadence justifies distributed-system costs |
| Event-driven processing | Events/queues trigger asynchronous work | Useful for secondary work such as notifications, search indexing, and analytics; requires idempotency and failure handling |
| Serverless/managed cloud services | Provider-managed runtime and infrastructure | Can reduce server operations or handle bursty workloads, but is a deployment choice with provider and runtime trade-offs |

The baseline frequently used for a new marketplace is a web/mobile client calling an API, a layered application (often initially a modular monolith), and a relational database for orders and inventory. Teams add a cache, search index, or queue when a measured access pattern or background-work need justifies it. Larger or more mature systems may use a hybrid of independently deployed services and managed/serverless components; that does not make those choices necessary for this project.

```text
Common starting combination

 Browser / mobile / admin client
              |
          HTTP API                 client-server interaction
              |
   Layered modular application     application structure
              |
       Relational database         orders and inventory source of truth
          /           \
 optional cache     optional queue ---> notifications / analytics

 Evolution when supported by evidence:
 selected modules --> independently deployed services
 bursty/background work --> managed or serverless components
```

For NFFH, the modular-monolith baseline fits the known requirements: it preserves database transactions for stock and orders, provides capability boundaries, and avoids assuming scale or team needs that have not been stated. Treat caches, search services, asynchronous events, and service extraction as later decisions backed by observed requirements.

## Evolution and operating guidance

- Keep core browsing and checkout request/response behavior synchronous where the user needs an immediate result.
- Add a managed queue only when there is a concrete need for non-critical background work, such as notifications or analytics. If events must reliably accompany database changes, use a transactional outbox or equivalent.
- Avoid a message broker, Kubernetes, service mesh, and separate service databases until actual requirements justify their complexity.
- Monitor real traffic, team ownership, deployment friction, and module coupling. Revisit this decision if independent scaling, release cadence, or organizational ownership becomes a demonstrated requirement.

## Open questions

Resolve these through requirements work before treating the design as final:

- Expected usage, peak checkout concurrency, and availability targets.
- Whether payment is in scope and, if so, its provider and order/payment lifecycle.
- Whether inventory holds expire, and the rules for failed or abandoned checkouts.
- Required notification channels and timing.
- Authentication, privacy, retention, and regulatory constraints.
- Pickup-day availability rules and whether farmers must approve orders.

## References

- Task 1 discussion record: `task_1_record.md`
- NFFH requirements and architecture alternatives summarized in that discussion.
