## Why

The hosted runtime currently lets callers **pin** a subagent via **`subagent`** on `POST /api/v1/trigger` and uses a **single pipeline node** instead of the **LangChain subagents** pattern: a **central main agent** (from root **`systemPrompt`** / Helm values) that **delegates** to specialists by calling them as **tools** ([Subagents — LangChain](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). Aligning with that pattern removes HTTP-level subagent selection, avoids a separate **router** node (routing is **implicit** in the main agent’s tool-calling decisions), and matches how operators think about **one agent per deployment** configured from **root `values.yaml`**.

## What Changes

- **`POST /api/v1/trigger` always invokes the root agent** instantiated from deployment config (e.g. **`systemPrompt`** in `examples/hello-world/values.yaml` → `HOSTED_AGENT_SYSTEM_PROMPT`). The trigger body MUST **not** offer a **`subagent` override** for direct dispatch (**BREAKING** removal of `TriggerBody.subagent` and any parallel HTTP semantics).
- **Subagents** from `HOSTED_AGENT_SUBAGENTS_JSON` are **assembled as LangGraph/LangChain subgraphs or callables** and **exposed to the main agent as tools** (tool-per-subagent or single dispatch tool—see design), consistent with the **supervisor** pattern (not the separate **router** pattern in LangChain docs).
- **No explicit router node** in the graph: the **main agent** decides which subagent tool to call, if any.
- Preserve **role** implementations (`default`, `metrics`, `rag`) **inside** what each subagent tool invokes; preserve **`agent_runtime_subagent_*`** when a subagent tool runs.
- **BREAKING**: Clients and docs that relied on **`subagent`** in JSON must migrate to **natural-language** (or structured) input to the **main** agent only.
- Update **README**, **observability**, and **values schema** for root-agent + tool-bound subagents.

## Capabilities

### New Capabilities

- `cfha-langgraph-subagent-nodes`: Declarative subagents compiled into **invokable units** (nodes/subgraphs) whose behavior matches existing **role** semantics when called.
- `cfha-supervisor-subagent-tools`: **Root agent** from **`systemPrompt`** only on trigger; subagents **only** reachable as **tools** on that agent; **no** `subagent` trigger field and **no** dedicated router node.

### Modified Capabilities

- _(none — no formal `openspec/specs/` baselines for CFHA yet)_

## Impact

- **Code**: `trigger_graph.py`, `agent_models.py` (**remove `subagent`**), `app.py`, possibly new module for tool wiring + main `create_agent` / LangGraph graph; tests and README.
- **Dependencies**: LangChain **`create_agent`** / tools APIs as already pinned in runtime; possible alignment with **`langgraph-prebuilt`** patterns.
- **Ops**: Subagent **`name`** / **`description`** (and optional **`systemPrompt`**) become **tool schema and discovery** levers for the main agent per LangChain guidance.
