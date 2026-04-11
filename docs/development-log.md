# Development log

Chronological notes on **notable** chart and runtime changes—especially breaking behavior, new env vars, and Helm value shifts. ADRs stay in [docs/adrs/](adrs/README.md); this file is a lightweight running journal.

**How to add an entry:** prepend a new dated section (newest first), one tight paragraph plus bullets if needed, and link the commit or PR.

---

## 2026-04-11

**LangChain supervisor + subagent tools** ([`1ffcc4b`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/1ffcc4b)).

- Runtime: root agent uses LangChain `create_agent`; configured subagents are tools backed by LangGraph subgraphs (`supervisor.py`, `subagent_exec.py`, and related modules).
- **Breaking:** JSON field `subagent` on `POST /api/v1/trigger` returns **400**; clients send `message` for supervisor turns. RAG flows use the `rag` specialist’s tool arguments when the model invokes that tool.
- Helm: optional `chatModel` → `HOSTED_AGENT_CHAT_MODEL`; `values.schema.json` adds `description` and `exposeAsTool` on subagent items.
- Portable upstream diff and apply steps: [patches/](../patches/README.md).

## 2026-04-11

**Initial import** ([`b7aeb06`](https://github.com/jfeldstein/declarative-agent-library-chart/commit/b7aeb06)).

- Standalone repo: Helm library chart, examples, Python runtime (`hosted_agents`), RAG module, scrapers, CI (`./ci.sh`).
