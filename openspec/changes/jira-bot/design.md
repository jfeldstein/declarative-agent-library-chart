## Context

The chart already sketches a draft **`tools.jira`** object (**projects**, **scopes** like create/modify/transition). **`jira-scraper`** targets **CronJob → RAG**. Interactive Jira needs two pieces: **something that turns “something changed in Jira” into a trigger run**, and **something that lets the running graph read and write Jira** during that run.

## Goals / Non-Goals

**Goals:**

- **`jira-trigger`**: **Only** “external Jira event starts a run”: receive **webhooks** (Jira Cloud documented mechanism), satisfy **verification** (shared secret, optional JWT/Connect rules as documented for the chosen topology), and **invoke the same trigger pipeline** as **`POST /api/v1/trigger`** with a normalized **message + Jira context** payload (issue key, event, URLs as appropriate).
- **`jira-tools`**: **Only** what a **triggered** agent uses to **act on Jira**: bounded search, issue read, comment add, transition, and scoped create/update via **documented REST v3** (or successor), registered like other **`tools_impl`** tools.
- Keep **Helm/env names** for **trigger**, **tools**, and **scraper** separable so operators do not route interactive traffic into RAG jobs or confuse tokens.

**Non-Goals:**

- **No** default path from **Jira tools** or **Jira trigger** body text into **`POST /v1/embed`**.
- **No** mandate to use two different Jira **OAuth clients** if one credential set is sufficient; the split is **logical** (trigger vs tools), not necessarily two apps.

## Decisions

### A. Jira Trigger

1. **Topology**: **Jira Cloud webhooks** POSTing to the runtime (operator exposes **Ingress** or equivalent); document **secret** validation (query param or header scheme per Jira docs for the chosen webhook type).
2. **Invocation**: On a **documented** set of webhook events (for example issue updated, comment created—exact list in implementation), build **`TriggerBody`** (or equivalent internal call) and call **`run_trigger_graph`** (prefer **direct** internal call over loopback HTTP unless design explicitly chooses HTTP).
3. **Scope**: Trigger layer **SHALL NOT** call Jira REST **mutating** APIs itself except what verification requires; user-visible Jira writes go through **`jira-tools`**.

### B. Jira Tools

1. **Surface**: Explicit tool ids in **`hosted_agents.tools_impl.dispatch`**, backed by **`httpx`** (or thin wrapper), env prefix e.g. **`HOSTED_AGENT_JIRA_TOOLS_*`** (illustrative).
2. **Simulation**: Keep CI behavior by gating real HTTP on presence of configured credentials (**design default**: match Slack tools pattern).
3. **Observability**: Reuse correlation / side-effect checkpoint patterns for real calls.

### C. Cross-cutting

- **Scraper disjointness**: Scraper CronJob env continues to use **`scrapers.jira`**; **trigger** and **tools** use keys documented in this change only.
- **IDs in prompts**: Trigger passes **issue key**, **project key**, **webhook event type**, and **stable issue URL** when available so the model can call tools without guessing.

## Risks / Trade-offs

- **[Risk] Webhook replay or duplicate delivery** → **Mitigation**: document **idempotency** (webhook id / event time + issue key dedupe) optional in v1.
- **[Risk] Jira Cloud vs Data Center** → **Mitigation**: v1 spec targets **Jira Cloud REST v3**; DC differences documented as follow-up.
- **[Risk] Rate limits (429)** → **Mitigation**: backoff and bounded batch sizes on the tools path; trigger path stays read-only toward Jira if possible.

## Migration Plan

1. Ship **Jira trigger** behind feature flag; verify signature and **one** **`run_trigger_graph`** per accepted webhook.
2. Ship **Jira tools** with mocks; then enable real token in staging; verify comment + transition.
3. Production rollout; monitor Jira API errors and trigger latency.

**Rollback**: disable webhook in Jira admin or env flags; tools fall back to simulation.

## Open Questions

- **Automation triggers**: parity for **Jira Automation** outbound webhooks vs native **Jira webhooks** only in v1.
- **Helm layout**: nested `jira.trigger` / `jira.tools` vs flat keys—align with **`dedupe-helm-values-observability`** and draft **`tools.jira`** when implemented.
- **JWT (Connect)**: required for marketplace apps; optional path if the repo only supports API token + webhooks initially.
