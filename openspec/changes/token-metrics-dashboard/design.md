## Context

The runtime already exposes **`agent_runtime_*`** counters and histograms on **`GET /metrics`** (`hosted_agents/metrics.py`) and documents import of **`grafana/cfha-agent-overview.json`** under **[CFHA-REQ-O11Y-LOGS-003]**. LangChain/LangGraph LLM calls return **usage metadata** (token counts) in many providers; streaming callbacks expose **chunk timing** suitable for **time-to-first-token** when the transport is streaming.

## Goals / Non-Goals

**Goals:**

- Emit **Prometheus-native** metrics operators can alert on: **TTFT**, **token counts**, **throughput**, **payload sizes**, **estimated cost**.
- Keep **label cardinality** bounded (reuse patterns from `wandb_trace` / config: `agent_id`, `model_id`, `route` / `skill_id` hashes—not free text).
- Ship a **Grafana dashboard** (new JSON or a second dashboard file) documenting **PromQL** examples and **datasource uid** assumptions consistent with existing **`grafana/README.md`**.
- Instrument the **primary LLM path** used by `POST /api/v1/trigger` (and document whether subagent/RAG paths are in v1 scope).

**Non-Goals:**

- Replacing **W&B** usage logging or billing systems of record.
- **Exact** cloud invoice reconciliation (estimates only, clearly labeled).
- Storing **raw prompts** or bodies in metric labels.
- **Token-level** tracing of every chunk in logs (metrics aggregates only).

## Decisions

1. **Instrumentation hook**  
   - **Decision**: Prefer **LangChain/LangGraph callbacks** or a thin wrapper around the chat-model invocation used by the trigger pipeline so token usage is captured once per logical completion.  
   - **Alternatives**: Parse vendor HTTP bodies in a lower layer (fragile across providers).

2. **Time to first token**  
   - **Decision**: Histogram **`agent_runtime_llm_time_to_first_token_seconds`** (or name finalized in spec) observed at **first streamed text delta** (or first non-empty model message for non-streaming).  
   - **Alternatives**: Gauge updated per request (loses distribution); logs-only (not alertable).

3. **Throughput**  
   - **Decision**: Expose **cumulative output tokens** and **generation interval** so dashboards use **`rate(tokens_total[5m]) / rate(duration_sum[5m])`** or provide a dedicated **histogram of tokens per second** per request if PromQL complexity is too high—pick one in implementation; design default is **counter + wall-clock histogram** for generation duration.  
   - **Alternatives**: Precomputed gauge (race conditions under concurrency).

4. **Payload sizes**  
   - **Decision**: Histograms on **serialized request/response byte lengths** for the trigger JSON and the outbound LLM request payload size **before** redaction, with **upper bounds** on recorded size to mitigate memory (cap at configurable max, e.g. 256KiB bucket overflow).  
   - **Alternatives**: Logs only (rejected: operator wants PromQL).

5. **Cost**  
   - **Decision**: **Counter** `agent_runtime_llm_estimated_cost_usd_total` incremented by **`(input_tokens * rate_in + output_tokens * rate_out)`** from **env or ConfigMap** (default rates documented; zero when unset). Document that multi-tenant **pricing tables** are out of scope for v1.  
   - **Alternatives**: External recording rule only (harder for ad-hoc dashboards).

6. **Dashboard placement**  
   - **Decision**: Add **`grafana/cfha-token-metrics.json`** (name TBD) alongside **`cfha-agent-overview.json`**; link from **`grafana/README.md`**.  
   - **Alternatives**: Collapse all panels into one JSON (file size / ownership blur).

## Risks / Trade-offs

- **[Risk] Provider does not return token counts** → **Mitigation**: emit **unknown** bucket or omit increment with a **`agent_runtime_llm_usage_missing_total`** counter.  
- **[Risk] Label explosion** → **Mitigation**: enforce allowlist; hash high-cardinality fields per ADR patterns.  
- **[Risk] Cost estimate misleading** → **Mitigation**: panel footnotes + metric `_info` help string “estimate only”.  
- **[Trade-off] Streaming vs batch** → document two code paths; tests cover the path implemented first.

## Migration Plan

1. Land metrics + unit tests (no dashboard) behind no-op when LLM not invoked.  
2. Land Grafana JSON + README.  
3. Rollout: scrape config unchanged if same `/metrics` port; operators import new dashboard.

## Open Questions

- Whether **subagent** LLM calls get **separate label** `invocation=subagent|root` or share root labels only.  
- Whether **RAG embed** token usage is included in v1 or a follow-up capability.
