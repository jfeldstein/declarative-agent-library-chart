## Why

Hosted agents need an inbound Jira path that starts runs from webhook events, but that path should remain narrowly focused: verify delivery, normalize payload, and forward into the existing trigger pipeline. Jira REST actions used during a run are a separate concern handled by `jira-tools`.

## What Changes

- `jira-trigger`: accept documented Jira webhook deliveries (or operator-configured equivalent), apply verification, and forward accepted events into hosted trigger semantics (`TriggerBody` / `run_trigger_graph`) with issue context.
- Trigger configuration keys remain disjoint from `scrapers.jira` and from `jira-tools` credentials.
- Non-goal: Jira REST write/read tool surface (that belongs to `jira-tools`), and no default `/v1/embed` from the trigger forwarding step.

## Capabilities

### New Capabilities

- `jira-trigger`: inbound Jira webhook bridge into the hosted trigger pipeline.

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level.)_

## Impact

- Runtime: webhook route/listener, verification, payload normalization, one trigger invocation per accepted event (subject to retry/idempotency policy).
- Helm/docs: trigger-only secret/env values and operator setup docs, clearly separated from `jira-tools` and `scrapers.jira`.
- Related change: `openspec/changes/jira-tools/` should land first (or in lock-step) so triggered runs can act on Jira.
