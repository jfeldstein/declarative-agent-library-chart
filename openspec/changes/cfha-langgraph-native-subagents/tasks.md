## 1. Contracts and breaking changes

- [x] 1.1 Remove **`subagent`** from **`TriggerBody`**; add **`message`** (or agreed user-input field); document **400** on legacy `subagent` if extra fields forbidden
- [x] 1.2 Extend **subagent JSON** + **`values.schema.json`**: require or recommend **`description`** for tool schema; optional **`exposeAsTool`** (default true) to omit **`metrics`** from default tool list
- [x] 1.3 Document **root `systemPrompt`** as **supervisor** instructions; append or merge **available subagents** list per LangChain **system prompt enumeration** guidance

## 2. Main agent and tools

- [x] 2.1 Implement **main agent** with **`create_agent`** (or pinned equivalent) using **`HOSTED_AGENT_SYSTEM_PROMPT`** from root values / env
- [x] 2.2 For each configured subagent, register a **LangChain tool** that wraps invocation of the subagent unit (sync return string to supervisor)
- [x] 2.3 Implement subagent units using **LangGraph subgraphs** or dedicated runnables per **`role`**, reusing **`_run_subagent_text`** logic inside tool bodies where possible
- [x] 2.4 Ensure **no router node**: outer graph is **invoke main agent** (single node or minimal wrapper), not **classify → branch**

## 3. Trigger path and observability

- [x] 3.1 Map **`POST /api/v1/trigger`** to **`main_agent.invoke`** with user message from JSON (and **`request_id`** in configurable / headers for RAG inside tools)
- [x] 3.2 Preserve **`observe_http_trigger`** and **`agent_runtime_subagent_*`** inside subagent tool execution
- [x] 3.3 Resolve **hello-world** without remote LLM: e.g. **empty subagents** → keep deterministic **`trigger_reply_text`** path, or document required model env

## 4. Skills, MCP, RAG

- [x] 4.1 Integrate **`load_skill`** / allowlisted **`tool`** with **main agent** tool list (merge order documented)
- [x] 4.2 Keep **`POST /api/v1/rag/query`** as non-launch utility; RAG **subagent tool** still uses **`X-Request-Id`** on outbound HTTP

## 5. Tests and docs

- [x] 5.1 Replace tests that POST **`subagent`** with **message**-only trigger + mocked model or deterministic stub asserting **tool** routing
- [x] 5.2 Add tests: **legacy `subagent` key** rejected or no-op per spec; **subagent tool** increments **`agent_runtime_subagent_*`**
- [x] 5.3 Update **README**, **observability**, link **LangChain subagents** doc; run **`pytest`** + **`ruff`**
