## Context

Today, `trigger_graph.py` runs a **single `pipeline` node** and dispatches to `_run_subagent_text` when **`TriggerBody.subagent`** is set. Root behavior otherwise uses **`trigger_reply_text(system_prompt)`** from env. The OpenSpec change **`cfha-langgraph-native-subagents`** originally proposed a **router node** and optional **`subagent` override**; that direction is **replaced** by the **LangChain subagents** architecture: **supervisor = main agent**, **subagents = tools** ([docs](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)).

## Goals / Non-Goals

**Goals:**

- **Single entry**: Every **`POST /api/v1/trigger`** run invokes **one main agent** configured from **root** `systemPrompt` (values → ConfigMap → `HOSTED_AGENT_SYSTEM_PROMPT`), analogous to `examples/hello-world/values.yaml` lines 3–4.
- **Subagents as tools**: Each configured subagent becomes a **tool** the main agent can call (sync tool calls that return a string result to the supervisor, unless async job pattern is explicitly chosen later).
- **Native graph structure**: LangGraph compiles a graph where the **main agent** is the orchestration surface and **subagent work** runs inside **tool execution** (which may invoke a **subgraph** or dedicated runnable per subagent).
- **No explicit router**: Do **not** add a separate classification/router node; **routing** is **the main agent’s tool selection** (distinct from LangChain’s [router](https://docs.langchain.com/oss/python/langchain/multi-agent/router) pattern).
- **Metrics**: **`agent_runtime_subagent_*`** when a subagent tool body runs; trigger-level metrics unchanged.

**Non-Goals:**

- Subagents conversing **directly** with the end user (they return to the main agent; matches LangChain doc).
- Full **checkpoint resume** / HITL for v1 unless already required elsewhere.
- **HTTP** per-subagent endpoints (remain removed per `cfha-trigger-langgraph-entrypoint`).

## Decisions

1. **Remove `subagent` from `TriggerBody`**  
   **Decision:** **Delete** the field; validation rejects unknown keys if using strict mode, or simply stop documenting/accepting it. **BREAKING.**  
   **Alternatives:** Keep deprecated and ignored (noisy); rejected.

2. **Tool pattern**  
   **Decision:** Default **tool per subagent** (`@tool(name, description)` wrapping invoke of subagent runnable) for clear schemas; optional **single dispatch** `task(agent_name, description)` only if we need registry scale (document in tasks if chosen).  
   **Rationale:** Matches LangChain “Tool per agent” section; descriptions from config drive supervisor behavior.

3. **Main agent implementation**  
   **Decision:** Use **`langchain.agents.create_agent`** (or equivalent in pinned stack) with **system prompt** = root `HOSTED_AGENT_SYSTEM_PROMPT` **plus** an appended short section listing available subagent tools (names + descriptions from config), unless tool schemas are self-describing enough.  
   **Alternatives:** Raw chat model without agent loop (rejected—no tool calling).

4. **Subagent implementation per `role`**  
   **Decision:** **`metrics`**, **`rag`**, **`default`** remain **stateless workers**: tool wrapper passes **query string** (or structured args for RAG) into existing `_run_subagent_text`-style logic; return **final string** to main agent.  
   **Note:** `metrics` returning Prometheus text is odd for a chat supervisor—either document “for ops only” or exclude from default tool list for chat models (open as config flag `exposeAsTool: false`).

5. **Trigger body for user message**  
   **Decision:** **`TriggerBody`** carries **`message`** (or reuse a single **`user`** / **`input`** field) as the **user** turn to the main agent; empty body uses a documented default (e.g. single empty turn or static prompt from env). Exact field in tasks.  
   **Alternatives:** Only plain-text body without JSON—would **BREAKING** change trigger content-type; prefer JSON with `message`.

6. **Graph vs agent**  
   **Decision:** Outer **`StateGraph`** may be minimal: **one node** that runs **`main_agent.invoke`** with checkpointer optional later, **or** use **`create_agent`**’s compiled graph as the runnable. Subagent “nodes” exist **inside** tool calls (subgraphs), satisfying “assembled as nodes” without a separate router vertex.

7. **Skills / MCP tools**  
   **Decision:** **`load_skill`** / **`tool`** on trigger either (a) run **before** main agent to mutate allowlists, or (b) merge **MCP tools** into the **main agent’s** tool list; pick one in implementation and document.

## Risks / Trade-offs

- **[Risk]** **LLM** required for main agent where today **deterministic** `trigger_reply_text` sufficed → **Mitigation:** support **no subagents** mode: if `HOSTED_AGENT_SUBAGENTS_JSON` empty, keep **deterministic** path or a thin model config for hello-world cost.
- **[Risk]** **`metrics` / `rag`** roles as tools confuse the model → **Mitigation:** **`toolDescription`** / **`exposeAsTool`** in config; default **hide** `metrics` from tool list.
- **[Risk]** Token / latency vs old single-shot reply → **Mitigation:** document; cap turns; env **max tool calls**.

## Migration Plan

1. Implement new graph + **remove `subagent`**; update all tests.
2. Document **BREAKING** in README and changelog-style note in development log.
3. Rollback: revert commit series restoring `trigger_graph` + `TriggerBody.subagent`.

## Open Questions

- **Hello-world** without API keys: use **mock** / **no-op** model, or **structured output** path that doesn’t call remote LLM when `subagents` empty?
- Exact **`message`** vs **`query`** naming on **`TriggerBody`**.
- Whether **`rag`** subagent tool accepts **flat args** mirroring current RAG JSON vs freeform string only.
