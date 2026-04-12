# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-12

**PR branch merge with `main` (conflict resolution)** — Reconciled divergent LangGraph wiring: **`HOSTED_AGENT_CHECKPOINT_STORE`** (default-on memory; `none` disables persistence) drives the compiled checkpointer when **`HOSTED_AGENT_CHECKPOINTS_ENABLED`** is unset; operator **`GET /api/v1/runtime/threads/...`** routes still require the explicit checkpoints flag. Helm **`deployment.yaml`** keeps the observability env block and adds **`extraEnv`**. Example dependency **`.tgz`** files repackaged from **`helm/chart`**. Tool calls use **`run_context.next_tool_call_id`** alongside observability trajectory / W&B spans.

**CI / local Helm** — GitHub Actions Helm job pins **Helm v3.20.2** and **helm-unittest v1.0.3** (`HELM_UNITTEST_VERSION`); `ci.sh` documents the same install line. **Helm 3.18.10+** is required for `helm-unittest` plugin `platformHooks` (v3.14.x fails with `unknown field "platformHooks"`).

**OpenSpec `agent-checkpointing-wandb-feedback` (partial apply)** — LangGraph **`MemorySaver`** checkpointer (default-on; `HOSTED_AGENT_CHECKPOINT_STORE=none` to disable); **`pre` + `pipeline`** nodes; **`GET /api/v1/trigger/threads/{id}/state|checkpoints`**; trigger **`thread_id`** / **`X-Thread-Id`** / **`ephemeral`**. **`run_context`** (`run_id`, `thread_id`, **`tool_call_id`** on MCP tools). **`wandb_session`** per-invocation init/finish when env ready; **`trace_meta`** on graph state. Bundled **`feedback_registry.v1.json`** + **`feedback_registry`**. Docs: **`docs/checkpointing-and-traces.md`**, **`docs/runbooks/checkpoints-wandb.md`**, observability updates. Helm **`extraEnv`**. Dockerfile **`uv sync --extra wandb`**. **`wandb`** optional extra + dev dep. Tasks **12/22** done; Slack mapping, durable feedback persistence, full LLM spans, interrupt/resume E2E remain.

**Observability doc + W&B/checkpoint stubs** — **`docs/observability.md`**: OpenSpec-aligned section for checkpointer SOT, W&B automatic tracing, tag cardinality, server-side Slack correlation, env table. Runtime: **`hosted_agents.agent_tracing`**, **`GET /api/v1/runtime/summary`** → **`observability`**. OpenSpec **`wandb-agent-traces`**: new **Operator documentation and runtime stubs** requirement; task **2.5** marked done.

**OpenSpec: `agent-checkpointing-wandb-feedback` scope trim** — Removed **ATIF export** and **shadow rollout** from this change (checkpointer + W&B automatic tracing + Slack feedback only); simplified **explicit human feedback** model; **server-side** Slack correlation; **`tasks.md`** now uses OpenSpec checkbox items (**21** tasks). **Shadow** requirements live in new change **`shadow-rollout-evaluation`** (**9** tasks).

## 2026-04-11

**ADR collision check + agent docs** — CI job `docs` runs `scripts/check_adr_numbers.sh`; `./ci.sh` runs the same check. Added `docs/AGENTS.md` for assistant orientation and `.claude/rules/adr-number-collisions.md` for Claude Code.

**Scraper Prometheus metrics (`agent_runtime_scraper_*`)** — completes OpenSpec **`agent-runtime-components`** task 3.4 (`runtime-scrapers`).

- Runtime: dedicated **`SCRAPER_REGISTRY`** so scraper CronJob **`GET /metrics`** lists only **`agent_runtime_scraper_*`** (not agent/RAG series); **`reference_job`** embeds to RAG; **`stub_job`** for other Helm job names; **`parse_scraper_metrics_addr`** supports **`[ipv6]:port`**.
- Helm: every enabled scraper gets **`containerPort` 9091**, **`SCRAPER_METRICS_ADDR` / `SCRAPER_METRICS_GRACE_SECONDS`**, and **`python -m hosted_agents.scrapers.stub_job`** when the job name is not **`reference`**; **`prometheus.io/*`** pod annotations for **all** scraper jobs when **`o11y.prometheusAnnotations.enabled`**.
- Docs: **`docs/observability.md`** (incl. **`SCRAPER_INTEGRATION`**); tests use **`generate_latest(SCRAPER_REGISTRY)`**.

## 2026-04-11

**ATIF v1.4 export pin** ([ADR 0003](adrs/0003-pin-atif-v1-4-trajectory-export.md)).

- Trajectory exports use Harbor **ATIF-v1.4** shape (`session_id`, `agent`, `steps`, `final_metrics`, `extra.hosted_agents` provenance); internal steps remain `hosted-agents-canonical-v1` until merged. See [Harbor ATIF](https://www.harborframework.com/docs/agents/trajectory-format).

## 2026-04-11

**Checkpointing, Slack feedback, W&B hooks, ATIF export, shadow flags** (OpenSpec `agent-checkpointing-wandb-feedback`).

- Runtime: optional LangGraph `MemorySaver` multi-node trigger graph when `HOSTED_AGENT_CHECKPOINTS_ENABLED=1`; `thread_id` / `ephemeral` on trigger body or `X-Agent-Thread-Id`; operator routes for checkpoint reads, Slack reaction ingest, human feedback listing, and ATIF-shaped export; `slack.post_message` tool records correlation + side-effect metadata; `hosted_agents/observability/*` (coverage omitted in `pyproject.toml` until integration hardens).
- Helm: `values.yaml` → `observability.*` maps feature flags and optional WANDB/Slack/Postgres wiring; ConfigMap keys for label registry + emoji map JSON.
- Docs: [docs/runbook-checkpointing-wandb.md](runbook-checkpointing-wandb.md).

## 2026-04-11

**LangChain supervisor + subagent tools** ([`1ffcc4b`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/1ffcc4b)).

- Runtime: root agent uses LangChain `create_agent`; configured subagents are tools backed by LangGraph subgraphs (`supervisor.py`, `subagent_exec.py`, and related modules).
- **Breaking:** JSON field `subagent` on `POST /api/v1/trigger` returns **400**; clients send `message` for supervisor turns. RAG flows use the `rag` specialist’s tool arguments when the model invokes that tool.
- Helm: optional `chatModel` → `HOSTED_AGENT_CHAT_MODEL`; `values.schema.json` adds `description` and `exposeAsTool` on subagent items.
- Portable upstream diff and apply steps: [patches/](../patches/README.md).

## 2026-04-11

**Initial import** ([`b7aeb06`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/b7aeb06)).

- Standalone repo: Helm library chart, examples, Python runtime (`hosted_agents`), RAG module, scrapers, CI (`./ci.sh`).
