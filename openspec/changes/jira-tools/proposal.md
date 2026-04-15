## Why

When a run is started (including from `openspec/changes/jira-trigger/`), the agent needs Jira REST operations to inspect and update work items during that run. That is LLM-time tool dispatch via `tools_impl`, not scheduled scraper ingestion and not trigger ingress verification.

## What Changes

- Allowlisted Jira tool ids backed by documented Jira Cloud REST calls (search/read/comment/transition/create-update within configured scope).
- Credentials and Helm keys for tools documented as distinct from `scrapers.jira` and from `jira-trigger` verification keys.
- Non-goal: webhook/event ingress and verification (that belongs to `jira-trigger`).

## Capabilities

### New Capabilities

- `jira-tools`: runtime Jira tools for read/write actions during an agent invocation; no default `/v1/embed`.

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level.)_

## Impact

- Runtime: `hosted_agents.tools_impl` modules + `dispatch` registration + structured error handling.
- Helm/docs: tools-only env/values and operator scope guidance.
- Related change: `openspec/changes/jira-trigger/` consumes these tools in webhook-triggered runs; tools should land first or in lock-step.
