# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-11

**Spec–test traceability** (OpenSpec change `traceability`).

- Promoted **`openspec/specs/cfha-requirement-verification/spec.md`**; added **`[CFHA-REQ-…]`** IDs across existing promoted specs; **`docs/spec-test-traceability.md`** matrix; **`scripts/check_spec_traceability.py`** run from **`ci.sh`** (strict by default, `CFHA_TRACEABILITY_STRICT=0` to relax YAML/py content checks).
- **`runtime-tools-mcp`** change-local spec updated for LangGraph / in-process tool exposure; **`cfha-agent-o11y-scrape`** wording aligned.
- **`.github/workflows/scheduled-o11y-integration.yml`** runs **`RUN_KIND_O11Y_INTEGRATION=1`** on a daily cron; **`AGENTS.md`** and **`.cursor/rules/spec-traceability.mdc`** document contributor obligations.

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
