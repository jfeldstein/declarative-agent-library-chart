# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

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
