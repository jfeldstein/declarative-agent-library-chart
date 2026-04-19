## Context

Consuming **application charts** wrap **`declarative-agent-library-chart`** (dependency alias **`agent`**, values under **`agent:`**) and typically use the published runtime image. Today, **tools** are dispatched from `hosted_agents.tools.dispatch` against a **fixed registry** plus Jira ids; **triggers** and **scraper CronJobs** are rendered from library templates with fixed **`python -m hosted_agents...`** entrypoints. Teams need to ship **domain-specific** Python without maintaining a fork of the library repo, while preserving **upgrade safety**, **secret handling**, and **observability** conventions.

## Goals / Non-Goals

**Goals:**

- Establish a **documented contract** for where custom Python lives (image layers, optional ConfigMap/volume mounts for dev), how tool ids join **`mcp.enabledTools`** / supervisor allowlists, and how **CronJobs** reuse **`RAG_SERVICE_URL`**, scraper metrics env, and optional cursor-store settings.
- Provide **runtime hooks** so custom tool ids resolve through the **same** `invoke_tool` / LangChain binding paths as built-ins (no parallel “shadow” RPC unless explicitly chosen).
- Add **`examples/with_custom_components/`** as the canonical **copy-paste** starting point (Chart.yaml, `templates/agent.yaml` including `declarative-agent.system`, `values.yaml`, README).

**Non-Goals:**

- Arbitrary remote plugin installation from the network at pod start (**no** unchecked `pip install` in chart hooks).
- Changing default **security posture**: custom tools remain subject to **allowlisting** and skill-unlock rules already enforced by the trigger API.
- Mandating a specific cloud registry or CI—only repository-local Helm patterns.

## Decisions

1. **Packaging model** — **Custom code ships in the consumer image** (multi-stage build `FROM` the library runtime image **or** equivalent digest) **and/or** optional read-only mounted packages for inner-loop dev.  
   **Rationale:** Matches Kubernetes immutable image practice and keeps production identical to CI builds.  
   **Alternatives:** Fork library and edit `hosted_agents` in-tree (high merge cost); ConfigMap-only Python for prod (size/secret risks).

2. **Tool registration** — Introduce a **single documented registration path** (for example **`importlib` loading of a named module** referenced by env such as **`HOSTED_AGENT_CUSTOM_TOOLS_INIT`** or setuptools **entry points** merged at process start) that extends `REGISTERED_MCP_TOOL_IDS` and dispatch maps **before** the HTTP server accepts traffic.  
   **Rationale:** Keeps one dispatch implementation and typed LangChain bindings.  
   **Alternatives:** Separate microservice for tools (operational overhead); dynamic `eval` of code from ConfigMaps (rejected on security grounds).

3. **Triggers** — Application charts that need **custom inbound behavior** SHOULD prefer **additional Kubernetes resources** in the **parent chart** (extra Deployment/Service, or HTTPRoute) that call the **existing** agent `/api/v1/trigger` contract **or** use **`extraEnv`** / sidecars only when necessary; **library-rendered** trigger Deployments remain the default path for Slack/Jira as today.  
   **Rationale:** Avoids embedding unreviewed webhook code inside the library templates.  
   **Alternatives:** UPstream new first-class triggers in the library per integration (slow for one-off teams).

4. **Scrapers** — Custom batch work SHOULD run as **user-owned `CronJob` manifests** in the application chart, reusing **`RAG_SERVICE_URL`** (same internal URL pattern as library scrapers) and, when embeddings are produced, **`hosted_agents.scrapers.base`** helpers for **`/v1/embed`**. Integration label / metrics env SHOULD follow existing **`SCRAPER_*`** conventions for consistent Prometheus behavior.  
   **Rationale:** Scrapers are already “script + env + CronJob”; duplication of the chart’s Jira/Slack job templates is acceptable if documented.  
   **Alternatives:** Generic Helm sub-template for arbitrary commands (possible follow-up).

5. **Helm surface** — Use existing **`extraEnv`**, **`image`** overrides on the dependency, and (if added) **`extraVolumes` / `volumeMounts`** on the library chart only with **narrow, schema-documented keys** so values contract tests stay tractable.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Registration hook loads untrusted code | Document that only **built image** paths and **explicit module names** are supported; forbid auto-load from mutable ConfigMaps in prod guidance. |
| Typo in custom tool id breaks deploy | Helm unittest / chart test asserts **enabledTools** ⊆ **registered ids** once custom registration is wired. |
| Duplicate metrics or RAG URLs | Example README stresses **same** `agent` dependency URL helpers as other examples. |
| Scope creep into “plugin marketplace” | Non-goal; one init hook and app-owned CronJobs only. |

## Migration Plan

1. Implement registration hook + any minimal Helm values schema updates behind **backward-compatible defaults** (no env → current behavior).
2. Land **`examples/with_custom_components`** and CI validation mirroring **`with-scrapers`** / **`hello-world`** patterns.
3. Document upgrade note: consumers on **extraEnv-only** hacks should migrate to the documented module path when available.

**Rollback:** Remove env wiring and revert to static registry; application charts retain their own manifests independently.

## Open Questions

- Exact env name(s) for the tool-registration module (`HOSTED_AGENT_*`) — finalize during implementation to avoid conflicting with existing chart keys.
- Whether typed LangChain bindings for **dynamic** tools use generated wrappers vs. JSON escape hatch for rarely used ids — may follow existing **skill-unlocked** behavior for unknown ids until typed bindings exist.
