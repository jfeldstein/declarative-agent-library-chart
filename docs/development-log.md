# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-12

**CI Helm pin** — GitHub Actions Helm job uses **Helm v3.20.2** so `helm-unittest` (plugin `platformHooks`) loads; v3.14.x fails with `unknown field "platformHooks"`.

**Observability doc + W&B/checkpoint stubs** — **`docs/observability.md`**: OpenSpec-aligned section for checkpointer SOT, W&B automatic tracing, tag cardinality, server-side Slack correlation, env table. Runtime: **`hosted_agents.agent_tracing`**, **`GET /api/v1/runtime/summary`** → **`observability`**. OpenSpec **`wandb-agent-traces`**: new **Operator documentation and runtime stubs** requirement; task **2.5** marked done.

**OpenSpec: `agent-checkpointing-wandb-feedback` scope trim** — Removed **ATIF export** and **shadow rollout** from this change (checkpointer + W&B automatic tracing + Slack feedback only); simplified **explicit human feedback** model; **server-side** Slack correlation; **`tasks.md`** now uses OpenSpec checkbox items (**21** tasks). **Shadow** requirements live in new change **`shadow-rollout-evaluation`** (**9** tasks).

## 2026-04-11

**ADR collision check + agent docs** — CI job `docs` runs `scripts/check_adr_numbers.sh`; `./ci.sh` runs the same check. Added `docs/AGENTS.md` for assistant orientation and `.claude/rules/adr-number-collisions.md` for Claude Code.

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

- Standalone repo: Helm library chart, examples, Python runtime (`hosted_agents`), RAG module, scrapers, CI (`./ci.sh`).
