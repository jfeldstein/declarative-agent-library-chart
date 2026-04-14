# Step 6: token-metrics-dashboard

`````
# Downstream LLM implementation brief: `token-metrics-dashboard`

## 0. Context (read first)

- **Linear checklist:** Step **6** in `docs/openspec-implementation-order.md` — **Prometheus** token / cost / streaming health metrics on the existing agent **`/metrics`** scrape path, plus a **Grafana** dashboard and docs; keep paths and naming aligned with **step 2** ([`02-consolidate-naming-spec.md`](02-consolidate-naming-spec.md): starter dashboard **`grafana/dalc-overview.json`**, **`agent:`** parent values, chart **`charts/declarative-agent-library-chart/`**) and **step 5** ([`05-observability-automatic-enabled-components-spec.md`](05-observability-automatic-enabled-components-spec.md): **[DALC-REQ-O11Y-LOGS-003]** optional panels, **[DALC-REQ-O11Y-LOGS-005]** generic scrape guidance — do not imply fixed optional target counts).
- **Coordination:** `docs/openspec-implementation-order.md` notes steps **5** and **6** can swap if Grafana ownership is serialized; avoid parallel PRs that both rewrite **`grafana/README.md`** / dashboard set without agreement.
- **Authoritative change bundle:** `openspec/changes/token-metrics-dashboard/` — `proposal.md`, `design.md`, `tasks.md`, delta specs under `specs/*/spec.md`.
- **Naming hygiene:** Proposal/tasks may say **`cfha-*`**; promoted capability folders are **`dalc-runtime-token-metrics`** and **`dalc-agent-o11y-logs-dashboards`**. New dashboard file: prefer **`grafana/dalc-token-metrics.json`** (not `cfha-token-metrics.json` / not `dalc-agent-overview.json`).
- **ID collision (must fix before promotion):** Delta `openspec/changes/token-metrics-dashboard/specs/dalc-agent-o11y-logs-dashboards/spec.md` labels an ADDED requirement **`[DALC-REQ-O11Y-LOGS-005]`**, but promoted `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` already defines **005** for README scrape targets. **Rename** the token-dashboard requirement to the next free ID (e.g. **`[DALC-REQ-O11Y-LOGS-006]`**) in the delta + matrix + tests **before** merge, per **ADR 0003** / **DALC-VER-005**.

## 1. Goal

1. **Runtime:** Register and emit **additive** `agent_runtime_*` metrics per **`dalc-runtime-token-metrics`**: input/output token counters, missing-usage counter, TTFT histogram, trigger request/response **byte-size** histograms (serialized lengths only, clamped), estimated USD cost counter (only when rates configured), HELP strings per **[DALC-REQ-TOKEN-MET-006]**.
2. **Instrumentation:** Hook at **primary `POST /api/v1/trigger` LLM** boundary (LangChain/LangGraph callbacks or thin wrapper) per `design.md`; bounded labels only (`agent_id`, `model_id`, `route` / hashed equivalents — **never** raw prompts or URLs).
3. **Grafana:** Commit **distinct** JSON (e.g. **`grafana/dalc-token-metrics.json`**) with panels for output token **rate**, TTFT **quantiles**, payload histograms, estimated cost (titles state **estimate**); **`grafana/README.md`** import path + Prometheus datasource assumptions consistent with **[DALC-REQ-O11Y-LOGS-003]**.
4. **Docs:** `docs/observability.md` — metric names, cardinality rules, pricing env vars (no secrets in values).
5. **Helm:** Optional **comments** or env wiring for cost-estimation only if needed; chart defaults unchanged when unset (`design.md`).
6. **Traceability:** On promotion, **`docs/spec-test-traceability.md`** rows + pytest docstrings / **`#`** comments per **ADR 0003**; **`python3 scripts/check_spec_traceability.py`** exits **0**.

## 2. Entities and interfaces

### 2.1 Prometheus metrics module (`helm/src/hosted_agents/metrics.py`)

Extend existing pattern (`Counter` / `Histogram`, `agent_runtime_*` prefix, `observe_*` helpers):

```python
from prometheus_client import Counter, Histogram

# New collectors (names and labelnames SHALL match delta spec; bodies omitted)
LLM_OUTPUT_TOKENS: Counter          # agent_runtime_llm_output_tokens_total
LLM_INPUT_TOKENS: Counter           # agent_runtime_llm_input_tokens_total
LLM_USAGE_MISSING: Counter         # agent_runtime_llm_usage_missing_total
LLM_TIME_TO_FIRST_TOKEN: Histogram  # agent_runtime_llm_time_to_first_token_seconds
HTTP_TRIGGER_REQUEST_BYTES: Histogram   # agent_runtime_http_trigger_request_bytes
HTTP_TRIGGER_RESPONSE_BYTES: Histogram  # agent_runtime_http_trigger_response_bytes
LLM_ESTIMATED_COST_USD: Counter    # agent_runtime_llm_estimated_cost_usd_total

def observe_llm_tokens(
    *,
    agent_id: str,
    model_id: str,
    result: str,
    input_tokens: int | None,
    output_tokens: int | None,
    streaming: bool,
    # ... other bounded dimensions per design
) -> None: ...

def observe_llm_time_to_first_token(
    *,
    seconds: float,
    streaming: bool,
    # same bounded label set as counters (+ streaming per [DALC-REQ-TOKEN-MET-003])
) -> None: ...

def observe_trigger_payload_bytes(*, request_len: int, response_len: int) -> None: ...

def observe_llm_estimated_cost_usd(*, usd_delta: float, ...) -> None: ...
```

**Contracts:**

- **Cardinality:** label values from allowlisted / hashed sources only (`design.md`).
- **Missing usage:** increment **`agent_runtime_llm_usage_missing_total`** when provider omits counts; **do not** increment input/output token counters for that completion (**[DALC-REQ-TOKEN-MET-001]**).
- **Cost:** increment **`agent_runtime_llm_estimated_cost_usd_total`** only when both rates configured **and** token counts known (**[DALC-REQ-TOKEN-MET-005]**).
- **Payload histograms:** one observation per trigger for request and response byte lengths; oversize clamped to **+Inf** bucket (**[DALC-REQ-TOKEN-MET-004]**).

### 2.2 HTTP trigger boundary (FastAPI)

```python
# Illustrative — locate actual route / middleware in hosted_agents app
async def trigger_endpoint(request: Request) -> Response: ...
# SHALL observe request body byte length after full read; response serialized size without logging raw content
```

### 2.3 LLM invocation layer

```python
# Pseudointerface — align with real graph/chat model call site
class LlmInstrumentationContext:
    call_started_monotonic: float
    first_token_observed: bool

def on_llm_end(usage: dict | None, labels: BoundedLabels) -> None: ...
def on_llm_stream_chunk(is_first_text_delta: bool, ctx: LlmInstrumentationContext) -> None: ...
```

### 2.4 Configuration (env / settings)

```python
@dataclass(frozen=True)
class LlmPricingConfig:
    input_rate_usd_per_token: float | None
    output_rate_usd_per_token: float | None

    @classmethod
    def from_env(cls) -> "LlmPricingConfig": ...
```

### 2.5 Grafana artifact

```json
// grafana/dalc-token-metrics.json — conceptual
{
  "uid": "string",
  "title": "string",
  "panels": [ "PromQL uses only documented agent_runtime_* names" ]
}
```

**Contract:** Distinct path from **`grafana/dalc-overview.json`**; import documented in **`grafana/README.md`** (renamed token-dashboard requirement ID after collision fix, e.g. **[DALC-REQ-O11Y-LOGS-006]**).

## 3. Normative specs

### 3.1 Delta specs (this change — implement against)

| Path |
|------|
| `openspec/changes/token-metrics-dashboard/specs/dalc-runtime-token-metrics/spec.md` |
| `openspec/changes/token-metrics-dashboard/specs/dalc-agent-o11y-logs-dashboards/spec.md` |

**Requirement IDs (token metrics):** **`[DALC-REQ-TOKEN-MET-001]`** … **`[DALC-REQ-TOKEN-MET-006]`** — scenarios in delta are acceptance tests.

**Grafana delta:** Fix **duplicate 005** → use **`[DALC-REQ-O11Y-LOGS-006]`** (or next free) for the **token dashboard** ADDED block; cross-reference **[DALC-REQ-O11Y-LOGS-003]** for datasource / optional UX patterns.

### 3.2 Promoted specs to reconcile on merge

| Path | Notes |
|------|--------|
| `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | Merge MODIFIED/ADDED prose; preserve existing **005** (README scrape) unless intentionally superseded — prefer **new ID** for token dashboard file obligation. |
| `openspec/specs/dalc-agent-o11y-scrape/spec.md` | No new scrape path if metrics stay on agent **`/metrics`**; verify wording still true. |

### 3.3 Related implementation specs

| Path |
|------|
| `docs/implementation-specs/01-dedupe-helm-values-observability-spec.md` |
| `docs/implementation-specs/02-consolidate-naming-spec.md` |
| `docs/implementation-specs/05-observability-automatic-enabled-components-spec.md` |

## 4. Tests and assertions (TDD; all must end green)

**Rule:** For each stage, **write or adjust failing tests first**, then implementation until listed commands pass. Test-writing is not a separate “stage” from implementation.

### 4.1 Pytest (`helm/src/tests/`)

| Test intent | Assertion |
|-------------|-----------|
| Metrics with usage | Mocked LLM completion with usage metadata → **`agent_runtime_llm_input_tokens_total`** / **`agent_runtime_llm_output_tokens_total`** increase by reported amounts (labels bounded). |
| Missing usage | No token counts → **`agent_runtime_llm_usage_missing_total`** increments; token counters for that completion unchanged (**[DALC-REQ-TOKEN-MET-001]**). |
| TTFT | Streaming (or non-streaming) path fires first token / first content → exactly **one** observation on **`agent_runtime_llm_time_to_first_token_seconds`** (**[DALC-REQ-TOKEN-MET-003]**); use mock clock or deterministic callback order. |
| Payload sizes | Trigger request/response → **`agent_runtime_http_trigger_request_bytes`** / **`agent_runtime_http_trigger_response_bytes`** each receive one observation (**[DALC-REQ-TOKEN-MET-004]**). |
| Cost | With env rates set and known tokens → **`agent_runtime_llm_estimated_cost_usd_total`** increases; with rates unset → no increment (**[DALC-REQ-TOKEN-MET-005]**). |
| HELP | **`/metrics`** or registry export: HELP substrings for each new family match **provider-reported** / **estimate** semantics (**[DALC-REQ-TOKEN-MET-006]**). |

```bash
cd helm/src && uv sync --all-groups && uv run pytest tests/ -v --tb=short
```

Add requirement ID strings to **docstrings** of tests used as matrix evidence (**DALC-VER-005**).

### 4.2 Helm

**Default:** No template change if scrape unchanged. If integration scripts or values snippets document new env vars, update them and any **`helm/tests/`** only if rendered manifests change.

### 4.3 Spec traceability

```bash
python3 scripts/check_spec_traceability.py
```

Update **`docs/spec-test-traceability.md`** for **`[DALC-REQ-TOKEN-MET-001]`**–**`[006]`** and the **renamed** Grafana requirement ID (e.g. **`[DALC-REQ-O11Y-LOGS-006]`**).

### 4.4 Grafana JSON (manual)

Import **`grafana/dalc-token-metrics.json`** per **`grafana/README.md`**; panels query only documented series (delta **“Maintainer finds token dashboard”** scenario).

## 5. Staged execution (each stage ends with listed tests green)

### Stage A — Metrics registration + HELP

**Tests first:** pytest that scrapes registry or exported text for **presence** of new metric names + HELP substrings → **red**.

**Implement:** `helm/src/hosted_agents/metrics.py` (+ small `observe_*` API).

**Green when:** HELP-focused pytest passes; full **`uv run pytest tests/`** still green.

### Stage B — Instrumentation (tokens, missing, TTFT, cost)

**Tests first:** mocked LLM with/without usage; TTFT callback order test; cost env on/off → **red**.

**Implement:** Callbacks/wrapper at trigger LLM site; bounded label helpers; pricing from env.

**Green when:** §4.1 token + TTFT + cost tests pass.

### Stage C — HTTP payload histograms

**Tests first:** trigger endpoint test asserting histogram observations for request/response sizes → **red**.

**Implement:** Middleware or endpoint hooks measuring serialized byte lengths (clamp per `design.md`).

**Green when:** payload tests + full pytest green.

### Stage D — Grafana + docs + OpenSpec promotion

**Tests first:** None automated for JSON; optional snapshot test **skipped** unless project adds one.

**Implement:** **`grafana/dalc-token-metrics.json`**, **`grafana/README.md`**, **`docs/observability.md`**; promote deltas to **`openspec/specs/`**; fix **LOGS-005** collision (**006** or agreed ID); matrix + comments.

**Green when:** **`python3 scripts/check_spec_traceability.py`** exits **0**; pytest green.

## 6. Acceptance checklist

- [ ] All **`[DALC-REQ-TOKEN-MET-001]`**–**`[006]`** behaviors evidenced by pytest (or waived per maintainer process — not default).
- [ ] **`grafana/dalc-token-metrics.json`** exists; PromQL uses real **`agent_runtime_*`** names from spec.
- [ ] **`grafana/README.md`** documents import path + Prometheus datasource assumption; consistent with **[DALC-REQ-O11Y-LOGS-003]** / **[DALC-REQ-O11Y-LOGS-005]** (scrape guidance remains generic).
- [ ] No high-cardinality labels; no raw prompts/bodies in metrics.
- [ ] Token-dashboard requirement uses **non-colliding** ID vs promoted **005**.
- [ ] **`python3 scripts/check_spec_traceability.py`** passes.

## 7. Commands summary

```bash
cd helm/src && uv run pytest tests/ -v --tb=short
python3 scripts/check_spec_traceability.py
# Optional: full example helm unittest loop from docs/implementation-specs/03-*.md if Helm touched
```

## 8. Open questions (from `design.md` — resolve in PR or defer explicitly)

- Subagent LLM calls: separate label **`invocation=root|subagent`** vs share root labels only.
- RAG **embed** token usage: in v1 vs follow-up capability.

`````
