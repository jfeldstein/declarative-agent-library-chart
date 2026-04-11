## Context

The prototype lives under `this repository`. The target audience is teams that want Slack-adjacent or internal “agent” behaviors without assembling Kubernetes, embeddings, tool auth, and CI themselves. The **Helm library chart** under `helm/chart/` is the reusable “platform” (not installed alone); **application** **examples** compose it with `values.yaml` (and later, richer config). The first vertical slice is **hello-world**: deploy, hit a stable HTTP trigger, observe a deterministic greeting derived from `system-prompt` (or equivalent config), proving wiring before Slack-specific work.

## Goals / Non-Goals

**Goals:**

- Establish directory layout: `helm/chart/` (**`type: library`** — Chart.yaml, `templates/*.yaml`), `helm/src/` (services or workers reading ConfigMap/env, or docs pointing at `runtime/`), `helm/tests/<pkg>/` aligned with `src` plus chart tests.
- Provide a **parent/child Helm pattern**: `examples/*` **application** charts declare the **library** chart as a **dependency** (or subchart) and override values.
- Expose `**POST /api/v1/trigger` (or documented equivalent)** on a NodePort/forwarded port (e.g. `8088`) that runs the agent path once per request and returns a response body suitable for `curl` verification.
- Support **Skaffold and/or DevSpace** alongside raw `helm upgrade` for the hello-world example so iterative dev is practical.
- Capture **draft YAML shape** for future tools (`slack`, `jira`, `drive`) in proposal/specs; v1 implementation may ignore or no-op non-essential keys as long as hello-world values validate and deploy.

**Non-Goals:**

- Creating a real Slack App, public URL, or end-to-end Slack message flow in this change.
- Full RAG, LangGraph, or production-grade secret management (beyond basic K8s Secret/External Secrets placeholders if any).
- Multi-tenant SaaS billing or org-wide RBAC productization (document as future work only).

## Decisions

1. **Helm as the packaging spine**
  - **Rationale**: Fits “hosted on infra” and matches user’s `Chart.yaml` / `values.yaml` mental model.  
  - **Alternatives**: Raw Kustomize-only, Terraform-only, or Compose-only — rejected for this repo direction because the user explicitly asked for chart template + examples.
2. **Single generic trigger HTTP surface first**
  - **Rationale**: Slack and other webhooks can normalize to “invoke agent with context” later; one endpoint keeps the hello-world acceptance test simple.  
  - **Alternatives**: Per-integration Deployment — heavier for v1.
3. **Config via ConfigMap (and optional Secret refs)**
  - **Rationale**: Standard K8s pattern; workload source is documented under `helm/src` with implementation in `runtime/`.  
  - **Alternatives**: Sidecar fetching from a control plane — out of scope for prototype.
4. **kind for local proof**
  - **Rationale**: Reproducible CI/local parity; user success criteria name kind explicitly.  
  - **Alternatives**: minikube/k3d — acceptable variants but document kind as canonical in tasks.
5. **Defer Slack webhook listener to a follow-up**
  - **Rationale**: Avoids external Slack dependency while still reserving path naming (e.g. future `webhooks/slack`) in design comments or chart templates if useful.

## Risks / Trade-offs

- **[Risk] “Agent” is stubbed** — First slice may use a minimal runtime (echo prompt / fixed LLM placeholder) → **Mitigation**: Specs require observable behavior matching hello-world values; swap implementation behind the same trigger contract later.
- **[Risk] Port forwarding vs NodePort drift** — Docs and tests must pin one approach (e.g. `8088`) → **Mitigation**: Chart values document `service.type` and `nodePort` or Skaffold port-forward mapping explicitly.
- **[Risk] Chart dependency versioning** — Library chart updates could break examples → **Mitigation**: Use chart version or file:// dependency during dev; document bump process in tasks.

## Migration Plan

- **Deploy**: Document `kind create cluster`, `helm dependency update` for example charts, `helm install` or Skaffold/DevSpace run.
- **Rollback**: Standard `helm rollback` or reinstall prior chart version; no data migration in v1.
- **CI (future)**: Add chart lint + optional integration job that spins kind and curls trigger (tasks can list as follow-up).

## Open Questions

- Exact runtime stack for workloads documented under `helm/src` (e.g. Python/uv vs Node) — pick one consistent with repo conventions during implementation.
- Whether `/api/v1/trigger` accepts JSON body with optional `message` or is empty-body for hello-world only.
- How strictly to validate the full multi-tool YAML schema in v1 vs progressive validation.

