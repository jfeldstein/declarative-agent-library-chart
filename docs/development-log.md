# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-12

**CI** — Removed root **`ci.sh`**; **`.github/workflows/ci.yml`** is the single source of truth. Local parity documented in **README** (Python via **uv**, Helm + **ct** + **helm-unittest**, ADR script). Python job uses **`python-version-file: runtime/.python-version`** on **`setup-uv`**.

**Dependabot batch merge** — Merged open Dependabot PRs **#1–#3, #5–#10** into `main` (GitHub Actions: checkout v6, upload-artifact v7, setup-uv v7, chart-testing-action 2.8.0; runtime: pytest-cov, coverage, uvicorn, httpx bumps). **PR #7** (pytest 9.x) conflicted with other pip PRs after sequential merges; resolved on [`dependabot/pip/runtime/pytest-gte-9.0.3`](https://github.com/jfeldstein/declarative-agent-library-chart/pull/7) by merging `main` and aligning **`[dependency-groups].dev`** to **`coverage[toml]>=7.13.5`**, **`pytest>=9.0.3`**, **`pytest-cov>=7.1.0`**, then **`uv lock`**, push, and merge.

**PR #10 (Dependabot httpx)** — Merged `main` into [`dependabot/pip/runtime/httpx-gte-0.28.1`](https://github.com/jfeldstein/declarative-agent-library-chart/pull/10) so the PR’s CI workflow matches current **Helm 3.20.2** + **helm-unittest v1.0.3** pins (the branch had been based on pre-fix `main` and failed Helm with `unknown field "platformHooks"`). Runtime change remains **`httpx>=0.28.1`**.

**CI / local Helm** — GitHub Actions Helm job pins **Helm v3.20.2** and **helm-unittest v1.0.3** (`HELM_UNITTEST_VERSION`); the root **README** documents the same pins for local runs. **Helm 3.18.10+** is required for `helm-unittest` plugin `platformHooks` (v3.14.x fails with `unknown field "platformHooks"`).

**OpenSpec `agent-checkpointing-wandb-feedback` (partial apply)** — LangGraph **`MemorySaver`** checkpointer (default-on; `HOSTED_AGENT_CHECKPOINT_STORE=none` to disable); **`pre` + `pipeline`** nodes; **`GET /api/v1/trigger/threads/{id}/state|checkpoints`**; trigger **`thread_id`** / **`X-Thread-Id`** / **`ephemeral`**. **`run_context`** (`run_id`, `thread_id`, **`tool_call_id`** on MCP tools). **`wandb_session`** per-invocation init/finish when env ready; **`trace_meta`** on graph state. Bundled **`feedback_registry.v1.json`** + **`feedback_registry`**. Docs: **`docs/checkpointing-and-traces.md`**, **`docs/runbooks/checkpoints-wandb.md`**, observability updates. Helm **`extraEnv`**. Dockerfile **`uv sync --extra wandb`**. **`wandb`** optional extra + dev dep. Tasks **12/22** done; Slack mapping, durable feedback persistence, full LLM spans, interrupt/resume E2E remain.

**Observability doc + W&B/checkpoint stubs** — **`docs/observability.md`**: OpenSpec-aligned section for checkpointer SOT, W&B automatic tracing, tag cardinality, server-side Slack correlation, env table. Runtime: **`hosted_agents.agent_tracing`**, **`GET /api/v1/runtime/summary`** → **`observability`**. OpenSpec **`wandb-agent-traces`**: new **Operator documentation and runtime stubs** requirement; task **2.5** marked done.

**OpenSpec: `agent-checkpointing-wandb-feedback` scope trim** — Removed **ATIF export** and **shadow rollout** from this change (checkpointer + W&B automatic tracing + Slack feedback only); simplified **explicit human feedback** model; **server-side** Slack correlation; **`tasks.md`** now uses OpenSpec checkbox items (**21** tasks). **Shadow** requirements live in new change **`shadow-rollout-evaluation`** (**9** tasks).

## 2026-04-11

**ADR collision check + agent docs** — CI job `docs` runs `scripts/check_adr_numbers.sh`. Added `docs/AGENTS.md` for assistant orientation and `.claude/rules/adr-number-collisions.md` for Claude Code.

**Scraper Prometheus metrics (`agent_runtime_scraper_*`)** — completes OpenSpec **`agent-runtime-components`** task 3.4 (`runtime-scrapers`).

- Runtime: dedicated **`SCRAPER_REGISTRY`** so scraper CronJob **`GET /metrics`** lists only **`agent_runtime_scraper_*`** (not agent/RAG series); **`reference_job`** embeds to RAG; **`stub_job`** for other Helm job names; **`parse_scraper_metrics_addr`** supports **`[ipv6]:port`**.
- Helm: every enabled scraper gets **`containerPort` 9091**, **`SCRAPER_METRICS_ADDR` / `SCRAPER_METRICS_GRACE_SECONDS`**, and **`python -m hosted_agents.scrapers.stub_job`** when the job name is not **`reference`**; **`prometheus.io/*`** pod annotations for **all** scraper jobs when **`o11y.prometheusAnnotations.enabled`**.
- Docs: **`docs/observability.md`** (incl. **`SCRAPER_INTEGRATION`**); tests use **`generate_latest(SCRAPER_REGISTRY)`**.

## 2026-04-11

**LangChain supervisor + subagent tools** ([`1ffcc4b`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/1ffcc4b)).

- Runtime: root agent uses LangChain `create_agent`; configured subagents are tools backed by LangGraph subgraphs (`supervisor.py`, `subagent_exec.py`, and related modules).
- **Breaking:** JSON field `subagent` on `POST /api/v1/trigger` returns **400**; clients send `message` for supervisor turns. RAG flows use the `rag` specialist’s tool arguments when the model invokes that tool.
- Helm: optional `chatModel` → `HOSTED_AGENT_CHAT_MODEL`; `values.schema.json` adds `description` and `exposeAsTool` on subagent items.
- Portable upstream diff and apply steps: [patches/](../patches/README.md).

## 2026-04-11

**Initial import** ([`b7aeb06`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/b7aeb06)).

- Standalone repo: Helm library chart, examples, Python runtime (`hosted_agents`), RAG module, scrapers, CI (`.github/workflows/ci.yml`).
