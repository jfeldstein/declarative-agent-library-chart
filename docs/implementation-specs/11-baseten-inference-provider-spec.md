# Step 11: baseten-inference-provider

`````
# Downstream LLM implementation brief: `baseten-inference-provider`

## 0. Context (read first)

- **Linear checklist:** Step **11** in `docs/openspec-implementation-order.md` — **parallel / leaf** with `declarative-langgraph-hitl`; mostly **additive** (inference provider subtree + runtime client). Per caveats §4, may land **after** `consolidate-naming` (step **2**) / `consolidate-helm-tests` (step **3**) with careful rebases; linear order places it after platform/scraper work for narrative only.
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) through [`10-scraper-cursors-durable-store-spec.md`](10-scraper-cursors-durable-store-spec.md) — respect stable **`HOSTED_AGENT_*`** env naming and chart values layout from **dedupe** + **naming**; avoid fighting post-move **`helm/tests/`** layout from **consolidate-helm-tests**.
- **Authoritative change bundle:** `openspec/changes/baseten-inference-provider/` — `proposal.md`, `design.md`, `tasks.md`, delta **`specs/baseten-inference/spec.md`** (requirements as written there; assign stable **`[DALC-REQ-…]`** / matrix rows on promotion per **ADR 0003** / **DALC-VER-005**).
- **Non-goals (explicit):** No live BaseTen in CI; no logging of API keys; do not mandate replacing **`resolve_chat_model` / LangGraph supervisor** in v1 unless tasks explicitly expand—**primary hook** is the **default-role subagent** path that today calls **`trigger_reply_text`**.

## 1. Goal

1. **Declarative inference provider:** Helm values + schema for **`inference.provider`** (`none` | `baseten`), BaseTen **`baseUrl`**, **`model`** (deployment id string), and **Secret-backed** API token via **`secretKeyRef`** (name + key)—matching `design.md` decision 1.
2. **Runtime:** When provider is **`baseten`** and required env is present, perform **OpenAI-compatible** `chat.completions` against configured **`baseUrl`** with auth from the Secret; return assistant text to the caller. When **`none`** or unset, preserve **deterministic** behavior (`trigger_reply_text` semantics unchanged).
3. **Helm:** Wire agent **Deployment** env from values + **`secretKeyRef`** for credentials only—never plain values for the token.
4. **Tests:** Mocked HTTP or patched client—**no** external network or credentials in CI (`spec.md` automated-tests requirement).
5. **Docs:** Operator onboarding (Secret, values, URL shape, 401/timeout troubleshooting) in **existing** README/chart README per `tasks.md` 5.1—no new markdown file unless repo convention already expects one.

## 2. Runtime integration points (read before coding)

| Location | Role today | BaseTen v1 intent |
|----------|------------|-------------------|
| `hosted_agents.subagent_exec._run_subagent_text` | For **`role`** not `metrics` / `rag`, builds prompt then **`trigger_reply_text(prompt)`** | **Branch:** when inference enabled, call **inference client** instead of **`trigger_reply_text`** for the default path; keep **`metrics` / `rag`** behavior unchanged. |
| `hosted_agents.reply.trigger_reply_text` | Deterministic body from system prompt (`Respond, "..."` pattern) | Remain **fallback** when provider `none` or misconfigured per **`spec.md`** “Inference disabled by default”. |
| `hosted_agents.trigger_graph._execute_trigger` / `_node_reply` | No subagents → **`trigger_reply_text(ctx.system_prompt)`** | **Out of scope** unless an explicit task adds it—document if product later wants single-agent remote completion without LangGraph. |
| `hosted_agents.chat_model.resolve_chat_model` | **`HOSTED_AGENT_CHAT_MODEL`** + LangChain **`init_chat_model`** for supervisor | **Parallel** configuration surface: supervisor may still use LangChain provider packages; BaseTen slice is the **declarative Helm `inference.*`** contract per `design.md` non-goals. Avoid duplicating auth secrets in two places without documenting precedence. |

## 3. Entities and interfaces (maximum leverage)

### 3.1 Configuration (Helm → env)

```yaml
# Illustrative LibraryChartValues fragment — exact keys follow tasks.md + schema
inference:
  provider: none   # | baseten
  baseten:
    baseUrl: str
    model: str
    apiKeySecret:
      name: str
      key: str
    # optional: httpTimeoutSeconds, path override — only if design open questions resolve
```

```python
# hosted_agents.runtime_config or dedicated module — signatures only

@dataclass(frozen=True)
class InferenceSettings:
    provider: Literal["none", "baseten"]
    baseten_base_url: str
    baseten_model: str
    # api key read from os.environ populated by secretKeyRef — not stored in values

def inference_settings_from_env() -> InferenceSettings: ...

def validate_inference_env(settings: InferenceSettings) -> None:
    """Raise ValueError with operator-actionable message when baseten selected but URL/model/token missing."""
```

**Contract:** When **`provider == "baseten"`**, runtime **SHALL** fail fast at call site or startup (pick one strategy; document) if **`baseUrl` / `model` / token env** are incomplete—map to **`TriggerHttpError`** (502/503) where appropriate for HTTP responses, without echoing secrets.

### 3.2 Inference client (OpenAI-compatible)

```python
class BasetenChatClient(Protocol):
    def complete(self, *, messages: list[dict[str, str]], request_id: str) -> str: ...
    """Returns assistant message content only; raises domain-specific errors for HTTP/payload failures."""


def build_baseten_client_from_env() -> BasetenChatClient | None:
    """Return None when provider is none — callers keep deterministic path."""
```

**Implementation choice (locked in `design.md`):** Prefer **`openai` SDK** with **`base_url`** override **or** **`httpx`** posting OpenAI-shaped JSON—**one** approach per PR; add dependency + lockfile update if needed.

**Security contract:** Log **request id** + **model id** only; **never** log token, full `Authorization` header, or raw prompts on error paths without redaction (`design.md` observability decision).

### 3.3 Subagent text path (branching contract)

```python
# hosted_agents.subagent_exec — conceptual

def _resolve_default_subagent_output(
    *,
    prompt: str,
    cfg: RuntimeConfig,  # or InferenceSettings injected
    request_id: str,
) -> str: ...
"""If baseten enabled and client builds: return client.complete(...). Else trigger_reply_text(prompt)."""
```

**Contract:** Preserve existing **`TriggerHttpError`** status codes for empty prompt / missing RAG URL where applicable; add **502** for upstream HTTP failures, **401** mapping if distinguishable, without leaking vendor response bodies that may contain secrets.

### 3.4 Helm ↔ Kubernetes

| Concern | SHALL |
|--------|--------|
| API key | **`env[].valueFrom.secretKeyRef`** on agent Deployment—**not** ConfigMap |
| Non-secret config | **`valueFrom.configMapKeyRef`** or plain `env` from values—**never** mix token into ConfigMap |
| Schema | `values.schema.json` documents token via **secret name + key** only (`spec.md` Helm scenario) |
| Defaults | **`provider: none`** (or absent) preserves current chart behavior |

## 4. Normative spec ↔ tests (TDD; tests first)

**Source:** `openspec/changes/baseten-inference-provider/specs/baseten-inference/spec.md`

| Requirement / scenario | Evidence (implement first) |
|------------------------|----------------------------|
| BaseTen inference configuration — operator enables with Secret | pytest: with env simulating Secret-injected token + base URL + model, client factory succeeds; without token, validation fails as specified |
| Inference disabled by default | pytest: `provider none` → **`trigger_reply_text`** still used; no HTTP client constructed |
| OpenAI-compatible chat completion — success | pytest: **mock** `httpx` or patch SDK — fixed JSON `choices[0].message.content` → returned string |
| OpenAI-compatible — remote error | pytest: 4xx/5xx or malformed JSON → controlled exception / `TriggerHttpError`; assert logs **exclude** token (caplog / mock logger) |
| Helm chart wiring + schema | helm unittest: when `baseten` selected, Deployment includes `secretKeyRef` for token env; when `none`, **no** inference secret env entries |
| CI without live BaseTen | no network calls: use **`respx`**, **`httpx.MockTransport`**, or patch client class |

**Gate (from repo norms):**

```bash
cd helm/src && uv run pytest tests/ -v --tb=short   # or project-documented path from repo root
helm unittest -f tests/… .                          # agent deployment suite that covers new env
python3 scripts/check_spec_traceability.py          # after promotion + IDs on spec headings
```

## 5. Staged execution (each stage delivers passing tests)

**Stage A — Config + validation:** Implement **`InferenceSettings`** + **`inference_settings_from_env`** + validation; pytest for env matrix (none vs baseten complete vs baseten missing fields).

**Stage B — Client:** Implement **`BasetenChatClient`** with mocked transport; pytest for success + HTTP error + malformed payload.

**Stage C — Wire subagent default role:** Integrate **`_run_subagent_text`** branch; extend existing subagent tests (`test_subagent_roles.py`, `test_agent_extensions.py` patterns) so default-role subagent with baseten env hits mock server; without env keeps deterministic output.

**Stage D — Helm:** Values + schema + `deployment.yaml`; helm unittest assertions on env and absence of secrets in ConfigMap data.

**Stage E — Docs:** README/chart README operator steps; troubleshooting.

## 6. Open questions (resolve with maintainer or document in PR)

- Exact **BaseTen** **`baseUrl`** and **model identifier** conventions for the team’s standard deployment (`design.md`).
- Whether **v1** needs **`inference.baseten`** knobs for **timeout** or **path prefix** override (`design.md` risks).
- Whether **subagent-level** model overrides are required vs single global model (`design.md` open question)—if deferred, document single global only.

## 7. Files likely touched (non-exhaustive)

- `helm/src/hosted_agents/subagent_exec.py`, `helm/src/hosted_agents/runtime_config.py` (or new `inference_settings.py`, `baseten_client.py`)
- `helm/src/hosted_agents/reply.py` — only if extracting shared helpers; avoid behavior change for `none`
- `helm/chart/values.yaml`, `helm/chart/values.schema.json`, `helm/chart/templates/deployment.yaml`
- `helm/src/tests/*.py` — new tests + extend subagent coverage
- `helm/pyproject.toml` / lockfile if adding `openai` or similar

`````
