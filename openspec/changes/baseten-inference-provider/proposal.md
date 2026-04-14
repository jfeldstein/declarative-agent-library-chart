## Why

Operators want **managed LLM inference** for hosted agents without bespoke integration per environment. **BaseTen** hosts models behind HTTP APIs (often **OpenAI-compatible**), which fits a **declarative** Helm values + secrets model. Today the runtime’s non-RAG subagent path is largely **deterministic** (`trigger_reply_text`); adding BaseTen as a supported inference provider closes the loop for real chat models while keeping configuration in values and Kubernetes secrets.

## What Changes

- Introduce an **inference provider** concept (at minimum **BaseTen**) with **declarative configuration**: endpoint base URL, model or deployment identifier, and **credentials from a Secret** (not plain values).
- **Runtime**: when BaseTen (or configured provider) is selected, perform chat/completions (or equivalent) against BaseTen’s API using the configured model; preserve existing behavior when inference is disabled or not configured.
- **Helm chart**: new values subtree (and schema) mapping to env vars or secret-backed env; optional example snippet in README or example chart.
- **Documentation**: how to obtain BaseTen URL and API key, and how to wire `Secret` + values.
- **Tests**: runtime tests with **mocked HTTP** (no live BaseTen calls in CI).

## Capabilities

### New Capabilities

- `baseten-inference`: Configuration, secrets wiring, and runtime behavior for **BaseTen-backed** agent/subagent inference (OpenAI-compatible client assumptions unless spec explicitly allows otherwise).

### Modified Capabilities

- (none — no published `openspec/specs/` capability today defines chat/inference requirements for this runtime)

## Impact

- **Runtime** (`helm/src/src/hosted_agents/…`): new or extended config loading, HTTP client for inference, possible dependency additions in `pyproject.toml`.
- **Helm** (`helm/chart/`): `values.yaml`, `values.schema.json`, `templates/deployment.yaml` (and related) for env + optional secret volume/mount or `secretKeyRef`.
- **Examples / docs**: align hello-world or README only where needed to document the new path.
- **Risk**: mishandled secrets in logs or error messages — mitigations belong in design/tasks (never log API keys; validate URLs).
