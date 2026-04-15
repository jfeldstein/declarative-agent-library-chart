# ADR 0008: Persistence backend strategy

## Status

Accepted

## Context

The runtime supports multiple ways to hold **execution persistence data** (checkpoints, correlation, feedback, and related durable run-state—see **[ADR 0005](0005-observability-vs-execution-persistence.md)** for the split from Prometheus observability metrics). In-memory and single-process defaults are convenient for velocity but do not meet durability or sharing expectations once workloads run across replicas or survive restarts.

The OpenSpec change **`openspec/changes/postgres-agent-persistence`** describes the intended durable path: Postgres-backed LangGraph checkpoints, relational stores for correlation and feedback (and optional structured span summaries for operators/export), with memory remaining the fallback when no database is configured. That change is the operational elaboration of this ADR’s backend choices.

## Decision

1. **Memory / in-process defaults**  
   Default **MemorySaver**-style and in-process stores **SHALL** be treated as appropriate **only** for **automated tests** and **simple local development**. They are **not** sufficient when **multiple replicas** must share state or when **execution persistence data** must **survive process or pod restarts**.

2. **Execution persistence in non-dev environments**  
   For **any long-running or production-like** deployment where **resume**, **audit**, or **cross-request correlation** must survive **pod churn** or restarts, the deployment **SHALL** use a **durable execution persistence backend** wired for that environment—not reliance on in-process memory alone.

3. **PostgreSQL as system of record**  
   When Postgres is **wired and enabled** (connection URL/secret, checkpointer, and application persistence adapters as applicable), PostgreSQL **SHALL** be the **system of record** for **execution persistence data** for that deployment. **PGlite** (or similar embedded Postgres) **MAY** be documented as an optional **developer** path that approximates production schema and behavior without requiring a shared cluster database, provided limitations are stated explicitly.

4. **Weights & Biases**  
   W&B **SHALL** be treated as a **trace product** (rich trace UI, experiment workflows). It **SHALL NOT** be assumed to substitute for **execution persistence data** as defined in ADR 0005: checkpoints, correlation rows, feedback events, and operator join keys belong in the persistence layer this ADR describes, not in W&B alone.

5. **Alignment with OpenSpec**  
   Implementation and Helm/docs work under **`openspec/changes/postgres-agent-persistence`** **SHOULD** stay aligned with this ADR’s division: durable Postgres for execution persistence, memory for tests and minimal local dev, W&B for traces without conflating roles.

## Consequences

- Operators of shared or production-like clusters **must** provision and operate Postgres (or an explicitly supported equivalent durable store introduced by a future ADR) when they require durable resume/audit/correlation.
- CI and local workflows can remain fast by defaulting to memory; integration tests **should** cover the Postgres path where that change lands.
- Documentation and runbooks **should** call out PGlite (if used) as dev-oriented and spell out differences from a real Postgres service.
- Confusion between “we have traces in W&B” and “we can resume after pod restart” is reduced by keeping terminology and backend responsibilities explicit.
