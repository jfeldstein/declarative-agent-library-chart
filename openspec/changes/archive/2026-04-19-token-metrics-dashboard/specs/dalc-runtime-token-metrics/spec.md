## ADDED Requirements

### Requirement: [DALC-REQ-TOKEN-MET-001] LLM output token counter

The agent process SHALL increment a **Prometheus counter** named **`agent_runtime_llm_output_tokens_total`** (suffix `_total` per naming convention) for **completed** LLM generations, labeled only with **bounded** dimensions documented in this change’s `design.md` (for example `agent_id`, `model_id`, `result`).

#### Scenario: Successful generation records tokens

- **WHEN** an LLM completion returns a positive **output token** count to the runtime instrumentation layer
- **THEN** the counter **`agent_runtime_llm_output_tokens_total`** SHALL increase by that integer amount for the matching label set

#### Scenario: Unknown token count does not invent data

- **WHEN** the provider returns no output token count
- **THEN** the runtime SHALL NOT increment **`agent_runtime_llm_output_tokens_total`** for that completion and SHALL increment a separate counter **`agent_runtime_llm_usage_missing_total`** with the same bounded labels

### Requirement: [DALC-REQ-TOKEN-MET-002] LLM input token counter

The agent process SHALL increment **`agent_runtime_llm_input_tokens_total`** for **input** (prompt) tokens reported by the provider for each completed generation, with the **same bounded label set** as **[DALC-REQ-TOKEN-MET-001]**.

#### Scenario: Provider reports prompt tokens

- **WHEN** the provider returns a non-negative **input token** count
- **THEN** **`agent_runtime_llm_input_tokens_total`** SHALL increase by that amount

### Requirement: [DALC-REQ-TOKEN-MET-003] Time-to-first-token histogram

The agent process SHALL observe **time to first streamed output token** (or first non-empty model content for non-streaming completions) in a **Prometheus histogram** named **`agent_runtime_llm_time_to_first_token_seconds`** with buckets suitable for sub-second to multi-second LLM latency, using the **same bounded labels** as token counters (plus `streaming` ∈ `{true,false}` if both paths exist).

#### Scenario: Streaming completion emits TTFT sample

- **WHEN** a streaming LLM call emits the first text delta to the client path instrumented by the runtime
- **THEN** the histogram **`agent_runtime_llm_time_to_first_token_seconds`** SHALL record one observation equal to elapsed wall time since the provider call began

### Requirement: [DALC-REQ-TOKEN-MET-004] Trigger payload size histograms

The agent process SHALL observe **serialized byte lengths** (not raw content) for **`POST /api/v1/trigger`** JSON bodies in a histogram **`agent_runtime_http_trigger_request_bytes`** and response bodies in **`agent_runtime_http_trigger_response_bytes`**, each with **bounded** buckets up to a documented maximum representable value; values above the maximum representable bound SHALL be clamped into the **+Inf** bucket without logging raw payloads.

#### Scenario: Request size recorded on trigger

- **WHEN** a valid trigger request body is fully received
- **THEN** **`agent_runtime_http_trigger_request_bytes`** SHALL record exactly one observation for that invocation

### Requirement: [DALC-REQ-TOKEN-MET-005] Estimated cost counter

The agent process SHALL increment **`agent_runtime_llm_estimated_cost_usd_total`** by **`input_tokens * configured_input_rate_usd + output_tokens * configured_output_rate_usd`** when both rates are configured as finite non-negative numbers; when rates are **not** configured, the runtime SHALL NOT increment this counter for that completion.

#### Scenario: Cost increments when pricing env is set

- **WHEN** configured rates are present and token counts are known
- **THEN** **`agent_runtime_llm_estimated_cost_usd_total`** SHALL increase by the computed non-negative amount

#### Scenario: No pricing configuration yields no cost signal

- **WHEN** pricing rates are unset
- **THEN** **`agent_runtime_llm_estimated_cost_usd_total`** SHALL remain unchanged for that completion

### Requirement: [DALC-REQ-TOKEN-MET-006] Metric help text states estimate semantics

Each new metric in **[DALC-REQ-TOKEN-MET-001]** through **[DALC-REQ-TOKEN-MET-005]** SHALL include **Prometheus HELP** text stating whether values are **provider-reported**, **runtime-estimated**, or **byte-size approximations**, and **`agent_runtime_llm_estimated_cost_usd_total`** HELP text SHALL explicitly include the word **estimate**.

#### Scenario: Operator inspects HELP

- **WHEN** an operator runs **`curl`** on **`/metrics`** and reads HELP lines for the new series
- **THEN** each HELP string SHALL match the semantics above for that metric family
