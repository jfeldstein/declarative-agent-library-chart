# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-14

**DALC traceability migration (OpenSpec `dalc-traceability-migration`)** — **Breaking for forks/automation:** promoted capabilities under **`openspec/specs/`** are now **`dalc-*`** (was **`cfha-*`**); requirement IDs use **`[DALC-REQ-…]`** / **`[DALC-VER-…]`** (was **`CFHA-`**). Matrix (**`docs/spec-test-traceability.md`**), ADR 0003, contributor rules, CI comments, pytest/Helm unittest annotations, Grafana import path (**`grafana/dalc-agent-overview.json`**), and active (non-archive) OpenSpec change spec folders were updated. **`scripts/check_spec_traceability.py`**: **`DALC_TRACEABILITY_STRICT`** (default strict on); **`CFHA_TRACEABILITY_STRICT`** remains a deprecated alias with a stderr warning.

**ARCHITECTURE.md** — New repository-root doc: user application charts vs `helm/chart` library chart, Kubernetes resources, observability (Prometheus `/metrics`, annotations, ServiceMonitors, structured logs), W&B and related `observability.*` wiring, scraper CronJobs and RAG deploy gate, `POST /api/v1/trigger` / LangGraph, agents (prompt, subagents), tools (MCP allowlist, skills); compact Helm ↔ runtime env table; links to promoted specs in `openspec/specs/`.

**OpenSpec `slack-trigger` + `slack-tools`** — Two changes (no **`slack-bot`** umbrella): **`openspec/changes/slack-trigger/`** (inbound **`app_mention`** → **`run_trigger_graph`**, URL challenge / signing or Socket Mode, **`[DALC-REQ-SLACK-TRIGGER-*]`**, no **`/v1/embed`** on trigger path) and **`openspec/changes/slack-tools/`** (**`slack_sdk`** tools for ack/reply/history, **`[DALC-REQ-SLACK-TOOLS-*]`**, keys disjoint from scraper and from trigger). Each has proposal, design, **`tasks.md`**, **`specs/<name>/spec.md`**. Implementation pending apply workflow.

**OpenSpec `jira-bot`** — Same pattern under **`openspec/changes/jira-bot/`**: **`jira-trigger`** (`specs/jira-trigger/spec.md`, **`[DALC-REQ-JIRA-TRIGGER-*]`**, webhooks → **`run_trigger_graph`**, verification, no default **`/v1/embed`**, config disjoint from **`scrapers.jira`**) and **`jira-tools`** (`specs/jira-tools/spec.md`, **`[DALC-REQ-JIRA-TOOLS-*]`**, **`httpx`** REST, scoped search/mutate, no default RAG ingest). Stub **`openspec/changes/jira-tools/.openspec.yaml`** parallels **`slack-tools`**. Implementation pending apply workflow.

## 2026-04-13

**OpenSpec `slack-scraper`** — Added change at **`openspec/changes/slack-scraper/`** (proposal, design, **`specs/slack-scraper/spec.md`** with **`[DALC-REQ-SLACK-SCRAPER-*]`** requirements, **`tasks.md`**) for a scheduled Slack scraper: operator-defined search list per run, **`slack_sdk`/`slack-bolt`** (bolt-python stack) for Web API calls, **`POST /v1/embed`** for new/updated messages, Helm dispatch by **`SCRAPER_INTEGRATION`**, bounded metrics. Implementation pending **`/opsx:apply`** / **`openspec-apply-change`**.

**RAG smoke** — In-process RAG smoke script moved from **`runtime/scripts/smoke_rag.py`** to **`runtime/tests/integration/smoke_rag.py`**; CI (**`.github/workflows/ci.yml`**) and docs (README, **`docs/rag-http-api.md`**, **`docs/spec-test-traceability.md`**) now reference the new path.

**Cursor / OpenSpec workflow** — `.cursor/commands/opsx-apply.md` and `opsx-archive.md`, plus **`openspec-apply-change`** / **`openspec-archive-change`** skills, now tell agents to implement **in a git worktree** (see **`AGENTS.md`** and **`parallel-agents-in-local-worktrees`**), finish apply with **push + PR** (base **`main`** by default), and after archive run **worktree cleanup** (`git worktree remove`, `git branch -d`, `git worktree prune`, `rm -rf wt/<path>` when needed). Landed with runtime work in **`d98f195`**.

**OpenSpec proposals (naming + traceability migration)** — Checked in **`openspec/changes/consolidate-naming`** (library chart identity, `agent` values alias, `dalc-overview` / image repo naming) and **`openspec/changes/dalc-traceability-migration`** (promoted spec folders **`dalc-*`**, IDs **`DALC-REQ`/`DALC-VER`**); traceability migration applied same day (see top of this section).

**with-scrapers example + Grafana** — **`examples/with-scrapers/`** documents every **`scrapers`** Helm key (shared **`resources`**, **`ragService`**, **`jobs`** with **`scope`**, **`extraEnv`**, and a disabled job), both built-in modules (**`reference_job`** vs **`stub_job`**), and **`helm unittest`** asserts the dispatch. **`grafana/dalc-agent-overview.json`** adds **`agent_runtime_scraper_*`** panels; **`hosted_agents.scrapers`** / **`metrics.py`** note the same maintainer checklist (Helm branch, example, dashboard, registry).

**Unified Postgres env + checkpointing example** — **`HOSTED_AGENT_POSTGRES_URL`** only (**`hosted_agents.observability.postgres_env`**). Helm **`observability.postgresUrl`**. Example **`examples/checkpointing/`** enables **`observability.checkpoints`** with **memory** while the library default stays off.

**PGlite** — Optional **`[pglite]`**; **`HOSTED_AGENT_USE_PGLITE=1`** starts TCP-mode PGlite and sets **`HOSTED_AGENT_POSTGRES_URL`** when unset. Runbook: **`docs/runbook-checkpointing-wandb.md`**.

**OpenSpec `postgres-agent-persistence` (worktree `openspec/postgres-agent-persistence`)** — Pinned **`langgraph-checkpoint-postgres==3.0.5`** + **`psycopg[binary]==3.3.3`** as optional **`[postgres]`** (also in dev for CI). **`build_checkpointer`** now uses a per-process **`ConnectionPool`** + **`PostgresSaver.setup()`** with URL validation and actionable errors. **`HOSTED_AGENT_OBSERVABILITY_STORE`** (`memory`|`postgres`), **`HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL`**, pool envs, and **`hosted_agents/migrations`** DDL + **`postgres_repos`** + **`stores`** context wiring for FastAPI, Slack ingest, **`run_trigger_graph`**, and tool span summaries. Checkpoint Postgres may use **`HOSTED_AGENT_CHECKPOINT_POSTGRES_URL`** or fall back to **`HOSTED_AGENT_POSTGRES_URL`**. Helm: **`observability.store`**, Postgres URL / **`secretKeyRef`**, checkpoint URL secret, legacy **`observability.postgresUrl`**, optional post-install **`psql`** migration Job (**`observability.postgres.migrations.enabled`**), duplicated SQL under **`helm/chart/files/observability/`**. Dockerfile **`--extra postgres`**. Tests: mocked checkpointer + repo + schema; **`ct lint`**, **`helm unittest`**.

**Coverage** — Removed **`*/observability/*`** from **`runtime/pyproject.toml`** `[tool.coverage.run] omit` so **`hosted_agents/observability/`** is included in the **`pytest-cov`** denominator (aggregate still **≥85%**). Deleted OpenSpec change **`observability-package-coverage`**; **`agent-checkpointing-wandb-feedback`** and **`agent-runtime-components`** proposals now state the same rule explicitly.

**OpenSpec** — Earlier today: deleted **`shadow-rollout-evaluation`** and **`shadow-non-mutating-twin-execution`**; **`agent-checkpointing-wandb-feedback`** no longer defers to those paths. Later: **`agent-maker-system`** rescoped (prefix policy, bot MVP, eval reuse); stubs **`subagent-reference-system`**, **`ci-delta-flagging`**; **`traceability`** proposal/design updated for **test-to-spec** vocabulary, proposed-vs-promoted matrix rules, and **`runtime-tools-mcp` contract vs wire**.

**OpenSpec `traceability` (tasks closure)** — Implementation was already on **`main`** (IDs, matrix, **`scripts/check_spec_traceability.py`**, CI job, scheduled o11y workflow, **`AGENTS.md`** / **`.cursor/rules/spec-traceability.mdc`**). Marked **`openspec/changes/traceability/tasks.md`** **15/15** complete; aligned **`openspec/changes/agent-runtime-components/specs/runtime-tools-mcp/spec.md`** section title with the **`traceability`** copy (**`## MODIFIED Requirements`**).

**Local CI parity (README)** — Ran end-to-end on a dev machine: **`./scripts/check_adr_numbers.sh`**, **`python3 scripts/check_spec_traceability.py`**, **`uv run ruff check`** + **`uv run pytest tests/`** under **`runtime/`**, **`helm dependency build --skip-refresh`** + **`helm unittest .`** for each **`examples/*/`**, **`ct lint --config ct.yaml --all`**, **`uv run python tests/integration/smoke_rag.py`** (from **`runtime/`**). All exited **0** (records **`openspec/changes/traceability/tasks.md`** §6.1 verification, not only Python + OpenSpec).

## 2026-04-12

**PR #11 merge with `main`** — Reconciled divergent LangGraph wiring: **`HOSTED_AGENT_CHECKPOINT_STORE`** (default-on memory; `none` disables persistence) drives the compiled checkpointer when **`HOSTED_AGENT_CHECKPOINTS_ENABLED`** is unset; operator **`GET /api/v1/runtime/threads/...`** routes still require the explicit checkpoints flag. Helm **`deployment.yaml`** keeps the observability env block and adds **`extraEnv`**. Example chart **`charts/*.tgz`** dependencies are **gitignored**; run **`helm dependency build`** under each example. Tool calls use **`run_context.next_tool_call_id`** alongside observability trajectory / W&B spans.

**Spec–test traceability** — See **[ADR 0003](adrs/0003-spec-test-traceability.md)**, **`docs/spec-test-traceability.md`**, and **`scripts/check_spec_traceability.py`** on `main`. **ATIF export ADR** renumbered to **[0004](adrs/0004-pin-atif-v1-4-trajectory-export.md)** so **`0003`** stays traceability-only.

**CI** — **`.github/workflows/ci.yml`** is canonical (no root **`ci.sh`**). Local parity in **README** (Python via **uv**, Helm + **ct** + **helm-unittest**, ADR + traceability checks).

**Dependabot batch merge** — Merged open Dependabot PRs **#1–#3, #5–#10** into `main` (Actions + runtime bumps). **PR #7** (pytest 9.x): resolved via merge into [`dependabot/pip/runtime/pytest-gte-9.0.3`](https://github.com/jfeldstein/declarative-agent-library-chart/pull/7).

**PR #10 (Dependabot httpx)** — Merged `main` into [`dependabot/pip/runtime/httpx-gte-0.28.1`](https://github.com/jfeldstein/declarative-agent-library-chart/pull/10) for current Helm / unittest pins.

**CI / local Helm** — GitHub Actions pins **Helm v3.20.2** and **helm-unittest v1.0.3**; **README** documents the same. **Helm 3.18.10+** required for **`platformHooks`** in the unittest plugin.

**OpenSpec `agent-checkpointing-wandb-feedback` (partial apply)** — LangGraph **`MemorySaver`** checkpointer (default-on; `HOSTED_AGENT_CHECKPOINT_STORE=none` to disable); **`pre` + `pipeline`** nodes; **`GET /api/v1/trigger/threads/{id}/state|checkpoints`**; trigger **`thread_id`** / **`X-Thread-Id`** / **`ephemeral`**. **`run_context`** (`run_id`, `thread_id`, **`tool_call_id`** on MCP tools). **`wandb_session`** per-invocation init/finish when env ready; **`trace_meta`** on graph state. Bundled **`feedback_registry.v1.json`** + **`feedback_registry`**. Docs: **`docs/checkpointing-and-traces.md`**, **`docs/runbooks/checkpoints-wandb.md`**, observability updates. Helm **`extraEnv`**. Dockerfile **`uv sync --extra wandb`**. **`wandb`** optional extra + dev dep. Tasks **12/22** done; Slack mapping, durable feedback persistence, full LLM spans, interrupt/resume E2E remain.

**Observability doc + W&B/checkpoint stubs** — **`docs/observability.md`**: OpenSpec-aligned section for checkpointer SOT, W&B automatic tracing, tag cardinality, server-side Slack correlation, env table. Runtime: **`hosted_agents.agent_tracing`**, **`GET /api/v1/runtime/summary`** → **`observability`**. OpenSpec **`wandb-agent-traces`**: new **Operator documentation and runtime stubs** requirement; task **2.5** marked done.

**OpenSpec: `agent-checkpointing-wandb-feedback` scope trim** — Removed **ATIF export** and **shadow rollout** from this change (checkpointer + W&B automatic tracing + Slack feedback only); simplified **explicit human feedback** model; **server-side** Slack correlation; **`tasks.md`** now uses OpenSpec checkbox items (**21** tasks). **Shadow** was later split to **`shadow-rollout-evaluation`** then **removed** with **`shadow-non-mutating-twin-execution`** (2026-04-13).

## 2026-04-11

**ADR collision check + agent docs** — CI job `docs` runs `scripts/check_adr_numbers.sh`. Added `docs/AGENTS.md` for assistant orientation and `.claude/rules/adr-number-collisions.md` for Claude Code.

**ADR 0003: spec–test traceability** — Normative rules (IDs, matrix vs tests, cross-links, agent playbook) live in [docs/adrs/0003-spec-test-traceability.md](adrs/0003-spec-test-traceability.md); [docs/spec-test-traceability.md](spec-test-traceability.md) keeps the CI tier table and parsed matrix.

**Spec–test traceability** (OpenSpec change `traceability`).

- Promoted **`openspec/specs/cfha-requirement-verification/spec.md`**; added **`[CFHA-REQ-…]`** IDs across existing promoted specs; **`docs/spec-test-traceability.md`** matrix; **`scripts/check_spec_traceability.py`** run from **`ci.sh`** (strict by default, `CFHA_TRACEABILITY_STRICT=0` to relax YAML/py content checks). _(IDs and paths later migrated to **`DALC-`** / **`dalc-*`**; see dated entry below.)_
- **`runtime-tools-mcp`** change-local spec updated for LangGraph / in-process tool exposure; **`cfha-agent-o11y-scrape`** wording aligned.
- **`.github/workflows/scheduled-o11y-integration.yml`** runs **`RUN_KIND_O11Y_INTEGRATION=1`** on a daily cron; **`AGENTS.md`** and **`.cursor/rules/spec-traceability.mdc`** document contributor obligations.

**Scraper Prometheus metrics (`agent_runtime_scraper_*`)** — completes OpenSpec **`agent-runtime-components`** task 3.4 (`runtime-scrapers`).

- Runtime: dedicated **`SCRAPER_REGISTRY`** so scraper CronJob **`GET /metrics`** lists only **`agent_runtime_scraper_*`** (not agent/RAG series); **`reference_job`** embeds to RAG; **`stub_job`** for other Helm job names; **`parse_scraper_metrics_addr`** supports **`[ipv6]:port`**.
- Helm: every enabled scraper gets **`containerPort` 9091**, **`SCRAPER_METRICS_ADDR` / `SCRAPER_METRICS_GRACE_SECONDS`**, and **`python -m hosted_agents.scrapers.stub_job`** when the job name is not **`reference`**; **`prometheus.io/*`** pod annotations for **all** scraper jobs when **`o11y.prometheusAnnotations.enabled`**.
- Docs: **`docs/observability.md`** (incl. **`SCRAPER_INTEGRATION`**); tests use **`generate_latest(SCRAPER_REGISTRY)`**.

## 2026-04-11

**ATIF v1.4 export pin** ([ADR 0004](adrs/0004-pin-atif-v1-4-trajectory-export.md)).

- Trajectory exports use Harbor **ATIF-v1.4** shape (`session_id`, `agent`, `steps`, `final_metrics`, `extra.hosted_agents` provenance); internal steps remain `hosted-agents-canonical-v1` until merged. See [Harbor ATIF](https://www.harborframework.com/docs/agents/trajectory-format).

## 2026-04-11

**Checkpointing, Slack feedback, W&B hooks, ATIF export, shadow flags** (OpenSpec `agent-checkpointing-wandb-feedback`).

- Runtime: optional LangGraph `MemorySaver` multi-node trigger graph when `HOSTED_AGENT_CHECKPOINTS_ENABLED=1`; `thread_id` / `ephemeral` on trigger body or `X-Agent-Thread-Id`; operator routes for checkpoint reads, Slack reaction ingest, human feedback listing, and ATIF-shaped export; `slack.post_message` tool records correlation + side-effect metadata; `hosted_agents/observability/*` (**2026-04-13:** observability no longer omitted from `pytest-cov`; see dated section above).
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
