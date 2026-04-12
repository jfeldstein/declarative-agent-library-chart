# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-12

**CI Helm pin** — GitHub Actions Helm job uses **Helm v3.20.2** so `helm-unittest` (plugin `platformHooks`) loads; v3.14.x fails with `unknown field "platformHooks"`.

**OpenSpec: `agent-checkpointing-wandb-feedback` scope trim** — Removed **ATIF export** and **shadow rollout** from this change (checkpointer + W&B automatic tracing + Slack feedback only); simplified **explicit human feedback** model; **server-side** Slack correlation; **`tasks.md`** now uses OpenSpec checkbox items (**21** tasks). **Shadow** requirements live in new change **`shadow-rollout-evaluation`** (**9** tasks).

## 2026-04-11

**ADR collision check + agent docs** — CI job `docs` runs `scripts/check_adr_numbers.sh`; `./ci.sh` runs the same check. Added `docs/AGENTS.md` for assistant orientation and `.claude/rules/adr-number-collisions.md` for Claude Code.

**Scraper Prometheus metrics (`agent_runtime_scraper_*`)** — completes OpenSpec **`agent-runtime-components`** task 3.4 (`runtime-scrapers`).

- Runtime: `hosted_agents/scrapers/metrics.py` plus instrumented **`reference_job`**: counters/histogram per spec; optional **`GET /metrics`** when **`SCRAPER_METRICS_ADDR`** is set (Helm sets **`0.0.0.0:9091`** for the reference job, with **`SCRAPER_METRICS_GRACE_SECONDS`** so Job pods stay up briefly for scrapes).
- Helm: reference scraper **`containerPort` 9091**, env vars, and **`prometheus.io/*`** pod annotations when **`o11y.prometheusAnnotations.enabled`**.
- Docs: **`docs/observability.md`** table for scraper metrics; unit tests assert metric text in **`REGISTRY`**.

## 2026-04-11

**LangChain supervisor + subagent tools** ([`1ffcc4b`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/1ffcc4b)).

- Runtime: root agent uses LangChain `create_agent`; configured subagents are tools backed by LangGraph subgraphs (`supervisor.py`, `subagent_exec.py`, and related modules).
- **Breaking:** JSON field `subagent` on `POST /api/v1/trigger` returns **400**; clients send `message` for supervisor turns. RAG flows use the `rag` specialist’s tool arguments when the model invokes that tool.
- Helm: optional `chatModel` → `HOSTED_AGENT_CHAT_MODEL`; `values.schema.json` adds `description` and `exposeAsTool` on subagent items.
- Portable upstream diff and apply steps: [patches/](../patches/README.md).

## 2026-04-11

**Initial import** ([`b7aeb06`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/b7aeb06)).

- Standalone repo: Helm library chart, examples, Python runtime (`hosted_agents`), RAG module, scrapers, CI (`./ci.sh`).
