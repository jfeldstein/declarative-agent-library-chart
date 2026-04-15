# ADR 0006: Config surface during alpha (Helm values and env contract)

## Status

Accepted

## Context

The Declarative Agent Library chart and hosted-agents runtime are **alpha**: operators and contributors should expect **breaking changes** while the project converges on clear names and shapes. Recent refactors (for example reserved `observability.*` for Prometheus scrape wiring, split of checkpoints/W&B/feedback keys, scraper `job.json` patterns) were driven by **reducing ambiguity** (“aislop misunderstandings”) rather than by a long-term stability guarantee.

Without an explicit stance, reviewers may treat every Helm or env rename as a policy failure, or conversely assume semantic versioning guarantees the repo does not yet provide.

## Decision

1. **Alpha posture:** Until a future ADR declares a stable **v1** config contract, **breaking changes to Helm `values.yaml` keys, `values.schema.json`, and runtime environment variables are allowed without a deprecation window**, as long as changes are **documented** (development log, chart README, examples, and promoted OpenSpec where applicable).

2. **Single source of truth:** The **chart** and **runtime** stay aligned: template-rendered env vars and mounted files **SHALL** match what `hosted_agents` reads. Ambiguity between “Helm key” and “env name” SHOULD be resolved in docs with a small table or pointer to `ARCHITECTURE.md` rather than duplicate contradictory prose.

3. **Traceability:** Normative **SHALL** requirements that touch config **SHALL** follow **[ADR 0003](0003-spec-test-traceability.md)** (IDs, matrix, test citations) when promoted under `openspec/specs/`.

4. **Not a freeze:** This ADR does **not** require freezing naming; it **permits** continued cleanup until an explicit stability ADR supersedes this one.

## Consequences

**Positive:**

- Faster iteration while the design stabilizes.
- Clear expectation for operators: pin chart versions and read release notes / development log for breaking value or env changes.

**Negative / trade-offs:**

- Upgrades may require values migrations without automated compatibility shims.
- External forks must track changes closely until a v1 stability ADR appears.

**Follow-ups:**

- When the project is ready for stability, add an ADR that defines semver for the chart, deprecation policy for values/env, and optional backward-compatible aliases with sunset dates.
