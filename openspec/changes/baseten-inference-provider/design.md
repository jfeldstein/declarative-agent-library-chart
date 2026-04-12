## Context

The **declarative-agent** Helm chart injects runtime configuration via env vars (`HOSTED_AGENT_*`). Subagents with roles other than `rag` / `metrics` today resolve text through **`trigger_reply_text`**, which is deterministic and does not call a remote model. Product direction (see in-flight LangGraph work) expects **real LLM calls** for supervisor/subagent flows. **BaseTen** exposes hosted inference, commonly consumed via **OpenAI-compatible** HTTP APIs (`/v1/chat/completions` or deployment-specific paths per BaseTen docs).

## Goals / Non-Goals

**Goals:**

- Let operators select **BaseTen** as the inference backend using **values + Kubernetes Secret** for the API key (or equivalent auth header).
- Keep a **single clear configuration surface** (provider name, base URL, model id) that maps to env vars the runtime reads.
- Use an **OpenAI-compatible client** (e.g. `openai` Python SDK with `base_url` override, or `httpx` to the same shape) so BaseTen URL swaps do not fork protocol logic unnecessarily.
- Add **tests** that mock the HTTP layer; CI must not require BaseTen credentials.

**Non-Goals:**

- Implementing every possible BaseTen deployment mode (custom auth schemes, streaming-only UX, fine-tuning APIs).
- Replacing or mandating LangGraph-specific wiring in this change if that work lives in a parallel change—this design only defines the **inference provider contract** and Helm/runtime wiring.
- Supporting arbitrary third-party providers beyond what is needed for BaseTen in the first slice (extension points MAY be mentioned but not fully generalized).

## Decisions

1. **Configuration shape**  
   - **Decision**: Introduce something like `inference.provider` (`none` | `baseten`), `inference.baseten.baseUrl`, `inference.baseten.model` (or deployment id string per BaseTen naming), and `inference.baseten.apiKeySecret` (name + key) for `secretKeyRef`.  
   - **Rationale**: Matches existing chart patterns (values → env, secrets for credentials).  
   - **Alternatives**: Single opaque `HOSTED_AGENT_OPENAI_BASE_URL` without provider enum (rejected—harder to document BaseTen-specific onboarding).

2. **Runtime API**  
   - **Decision**: Prefer **OpenAI-compatible** `chat.completions` against `baseUrl` with model string from config.  
   - **Rationale**: BaseTen documents OpenAI compatibility for many deployments; minimizes custom JSON.  
   - **Alternatives**: Raw REST only (more code paths); vendor-specific SDK (locks to BaseTen package churn).

3. **When inference runs**  
   - **Decision**: When provider is `baseten` and required env vars are present, subagents (or the main agent path once merged with LangGraph) **SHALL** use the remote model; when provider is `none` or unset, preserve **existing deterministic** behavior.  
   - **Rationale**: Avoid breaking hello-world clusters without secrets.

4. **Observability**  
   - **Decision**: Log **request id** and **model id**; never log API keys or full prompts in error paths without redaction.  
   - **Rationale**: Security and operability baseline.

## Risks / Trade-offs

- **[Risk]** BaseTen URL or path differs per account → **Mitigation**: document required URL shape; allow optional path override in values if real deployments need it.  
- **[Risk]** Latency/timeouts on cold starts → **Mitigation**: configurable HTTP timeout; document in README.  
- **[Risk]** Secret misconfiguration → **Mitigation**: clear 503/401 mapping and startup validation where cheap.  
- **[Trade-off]** OpenAI-compatible assumption may not cover every BaseTen endpoint variant → follow-up change if a second protocol is required.

## Migration Plan

1. Ship chart + runtime with **default `provider: none`** (or absent) so existing releases unchanged.  
2. Operators who want BaseTen: create Secret, set values, rollout Deployment.  
3. **Rollback**: revert values to `none` / remove secret refs; no data migration.

## Open Questions

- Exact **BaseTen** URL and **model identifier** conventions for the team’s standard deployment (document once confirmed).  
- Whether **subagent-level** model overrides are required in v1 or can defer to a single global model env.
