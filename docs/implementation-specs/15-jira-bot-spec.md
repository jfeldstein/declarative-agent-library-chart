# Step 15: jira-bot

`````
# Downstream LLM implementation brief: `jira-bot`

## 0. Context (read first)

- **Linear checklist:** Step **15** in `docs/openspec-implementation-order.md` — **Jira path:** **webhook trigger** + **Jira REST tools**; **separate** from Slack (**steps 13–14**) and from **scheduled RAG scrapers** (**step 8** `jira-scraper`, CronJob → **`/v1/embed`**).
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) … [`14-slack-tools-spec.md`](14-slack-tools-spec.md) — especially **step 8** ([`08-jira-scraper-spec.md`](08-jira-scraper-spec.md)): **`scrapers.jira.*`** env and **`jira_job`** are **ingestion**, not webhook ingress or LLM-time REST; **steps 13–14**: mirror **trigger** (verify → `run_trigger_graph`, no embed) vs **tools** (`tools_impl`, simulation when no creds, disjoint secrets).
- **Authoritative change bundle:** `openspec/changes/jira-bot/` — `proposal.md`, `design.md`, `tasks.md`, normative deltas **`specs/jira-trigger/spec.md`** (`[DALC-REQ-JIRA-TRIGGER-001]` … **`[DALC-REQ-JIRA-TRIGGER-005]`**), **`specs/jira-tools/spec.md`** (`[DALC-REQ-JIRA-TOOLS-001]` … **`[DALC-REQ-JIRA-TOOLS-006]`**).
- **Design locks:** (1) **Trigger** — Jira Cloud webhooks POST to runtime; **documented verification** before **`run_trigger_graph`**; prefer **direct** internal call over loopback HTTP unless explicitly documented. (2) **Trigger SHALL NOT** call Jira mutating REST except what verification needs; **no** **`POST /v1/embed`** on the trigger forwarding step (**`[DALC-REQ-JIRA-TRIGGER-002]`**). (3) **Tools** — allowlisted ids in **`hosted_agents.tools_impl.dispatch`**, **`httpx`** (or thin wrapper) to Jira Cloud REST v3 (**`[DALC-REQ-JIRA-TOOLS-005]`**); **simulation** when credentials absent, matching **Slack tools** pattern (**`[DALC-REQ-JIRA-TOOLS-001]`** / `design.md`). (4) **Helm** — **non-overlapping** keys/env for **`scrapers.jira`** vs **trigger** vs **tools** (**`[DALC-REQ-JIRA-TRIGGER-004]`**, **`[DALC-REQ-JIRA-TOOLS-002]`**).
- **Traceability:** On promotion of `### Requirement:` rows to `openspec/specs/*/spec.md`, stable **`[DALC-REQ-…]`** per **`openspec/specs/dalc-requirement-verification/spec.md`** and **ADR 0003** / **DALC-VER-005**; update **`docs/spec-test-traceability.md`**; cite IDs in **pytest** docstrings and/or **helm unittest `#`** comments; **`python3 scripts/check_spec_traceability.py`** exit **0**.
- **Non-goals:** No default **`/v1/embed`** from Jira tools or trigger (**proposal**); **v1** targets **Jira Cloud** REST v3 — Data Center differences are follow-up (`design.md`).

## 1. Goal

1. **`jira-trigger`:** HTTP route (or documented ingress path) accepts Jira webhook JSON; **verify** per topology; map accepted payload → **`TriggerBody`** (or equivalent) + **`run_trigger_graph`** with **issue key**, **project key**, **event type**, **plain text** for **`TriggerBody.message`**, **stable issue URL** when available (**`[DALC-REQ-JIRA-TRIGGER-001]`**).
2. **`jira-tools`:** Allowlisted **`tools_impl`** tools for bounded **search/read**, **comment**, **transition**, **scoped create/update`** per configured scopes (**`[DALC-REQ-JIRA-TOOLS-003]`**, **`[DALC-REQ-JIRA-TOOLS-004]`**); structured errors, 429 backoff / bounded batches on tools path (`design.md`).
3. **Helm / values:** Extend **`values.schema.json`** / **`values.yaml`** (or documented subtrees) for trigger + tools; reconcile draft **`tools.jira`** in chart when implementing (**`tasks.md` 1.2**); **secrets only** via **`secretKeyRef`** — never ConfigMap literals for tokens.
4. **Observability:** Correlation + side-effect checkpoint patterns for real Jira calls (**`[DALC-REQ-JIRA-TOOLS-006]`**); trigger + tools paths **never** log signing secrets / **`Authorization`** / tokens or put them on metric labels (**`[DALC-REQ-JIRA-TRIGGER-005]`**, **`[DALC-REQ-JIRA-TOOLS-006]`**).
5. **CI / docs:** Unit tests for verification, mapping, REST tool paths; operator docs for webhook setup + required OAuth/scopes vs scraper CronJob (**`tasks.md`**).

## 2. Entities and interfaces (signatures only; no bodies)

### 2.1 Runtime: Jira webhook → trigger bridge

```python
# Conceptual module layout — align with helm/src/hosted_agents/ tree

from typing import Any

from hosted_agents.agent_models import TriggerBody
from hosted_agents.trigger_context import TriggerContext
from hosted_agents.trigger_graph import run_trigger_graph

class JiraTriggerContextFields(BaseModel):
    """Where these live (TriggerBody extension vs TriggerContext) is an open choice — pick one and satisfy slack-tools-style downstream consumption for tool defaults."""

    issue_key: str
    project_key: str
    webhook_event_type: str
    issue_url: str | None = None

def jira_plaintext_for_trigger_message(payload: dict[str, Any]) -> str: ...
"""Derive human-readable message from summary, comment body, changelog as available."""

def verify_jira_webhook(
    *,
    raw_body: bytes,
    headers: Mapping[str, str],
    cfg: Any,
) -> None: ...
"""SHALL raise on failure — caller returns 4xx without invoking run_trigger_graph ([DALC-REQ-JIRA-TRIGGER-003])."""

def build_trigger_body_from_jira_webhook(payload: dict[str, Any]) -> TriggerBody: ...

def dispatch_jira_webhook_to_trigger(
    payload: dict[str, Any],
    *,
    request_id: str,
    run_id: str,
    thread_id: str,
) -> None: ...
"""After verify: map → TriggerBody / TriggerContext; call run_trigger_graph exactly once per accepted delivery unless documented dedupe ([DALC-REQ-JIRA-TRIGGER-001])."""
```

**HTTP surface (when webhooks enabled):**

```python
async def handle_jira_webhook(request: Request) -> Response: ...
"""Content-Type JSON; parse envelope; on structural failure reject without run_trigger_graph ([DALC-REQ-JIRA-TRIGGER-003] unsupported content-type scenario)."""
```

### 2.2 Runtime: Jira REST tools (`tools_impl`)

```python
import httpx

@dataclass(frozen=True)
class JiraToolsSettings:
    """Load from HOSTED_AGENT_JIRA_TOOLS_* (exact prefix follows implementation + Helm)."""
    enabled: bool
    site_base_url: str
    email: str | None
    api_token: str | None  # from secretKeyRef-injected env — not from Helm values literals
    # scopes: read, comment, transition, create — booleans or enum set per chart contract

def jira_tools_settings_from_env() -> JiraToolsSettings: ...

def build_jira_tools_http_client(settings: JiraToolsSettings) -> httpx.Client | None: ...
"""Return None when simulation path required ([DALC-REQ-JIRA-TOOLS-001])."""

def jira_search_issues(client: httpx.Client, jql: str, *, max_results: int) -> list[dict[str, Any]]: ...
def jira_get_issue(client: httpx.Client, issue_key: str, fields: list[str] | None) -> dict[str, Any]: ...
def jira_add_comment(client: httpx.Client, issue_key: str, body: str) -> dict[str, Any]: ...
def jira_transition_issue(client: httpx.Client, issue_key: str, transition_id: str) -> None: ...
def jira_create_issue(client: httpx.Client, project_key: str, fields: dict[str, Any]) -> dict[str, Any]: ...
"""Each SHALL enforce configured scope before mutating ([DALC-REQ-JIRA-TOOLS-003])."""
```

```python
# hosted_agents.tools_impl.dispatch — conceptual

def invoke_tool(tool_id: str, arguments: dict[str, Any]) -> dict[str, Any]: ...
"""Route allowlisted jira.* tool ids; no /v1/embed in default configuration ([DALC-REQ-JIRA-TOOLS-001])."""
```

### 2.3 Helm / env (disjoint keys — exact names TBD; must satisfy 004 / 002)

```yaml
# Illustrative — wire to chart schema + docs; SHALL NOT require scrapers.jira auth fields for trigger/tools-only installs.

jiraTrigger:
  enabled: bool
  webhookSecretSecretRef: { name: str, key: str }
  # optional: connect/jwt settings if v1 implements Connect path (design open question)

jiraTools:
  enabled: bool
  siteUrl: str
  auth:
    emailSecretRef: { name: str, key: str }
    apiTokenSecretRef: { name: str, key: str }
  scopes: { read: bool, comment: bool, transition: bool, create: bool }
  allowedProjects: [str]  # illustrative — exact shape follows tasks.md / schema
```

**Contract:** When **`scrapers.jira`**, **`jiraTrigger`**, and **`jiraTools`** are all enabled, rendered manifests **SHALL** use **documented non-overlapping** secret field paths — overlap only if **explicitly** documented (e.g. one OAuth app) per **tools 002** / **trigger 004** scenarios.

### 2.4 Prometheus / logs

- Reuse HTTP metrics patterns for the webhook route; **bounded** labels only — **no** secrets (**005** / **006**).

## 3. Normative specs (implement against)

### 3.1 Delta specs (this change)

| Path |
|------|
| `openspec/changes/jira-bot/specs/jira-trigger/spec.md` |
| `openspec/changes/jira-bot/specs/jira-tools/spec.md` |

| ID | Capability | One-line intent |
|----|------------|-----------------|
| **`[DALC-REQ-JIRA-TRIGGER-001]`** | Trigger | Webhook → same outcome as **`POST /api/v1/trigger`** with Jira context + message text |
| **`[DALC-REQ-JIRA-TRIGGER-002]`** | Trigger | **No** **`POST /v1/embed`** as part of trigger forwarding |
| **`[DALC-REQ-JIRA-TRIGGER-003]`** | Trigger | Verify before **`run_trigger_graph`**; reject bad signature / malformed JSON without trigger |
| **`[DALC-REQ-JIRA-TRIGGER-004]`** | Trigger | Config paths **distinct** from **`scrapers.jira`** |
| **`[DALC-REQ-JIRA-TRIGGER-005]`** | Trigger | No secrets in logs or metric labels |
| **`[DALC-REQ-JIRA-TOOLS-001]`** | Tools | Tools only during active run; **no** default RAG embed from tool I/O |
| **`[DALC-REQ-JIRA-TOOLS-002]`** | Tools | Credentials **distinct** from scraper / **`scrapers`** |
| **`[DALC-REQ-JIRA-TOOLS-003]`** | Tools | Read/mutate within configured scopes |
| **`[DALC-REQ-JIRA-TOOLS-004]`** | Tools | Bounded JQL / search; responses exclude bearer material |
| **`[DALC-REQ-JIRA-TOOLS-005]`** | Tools | **`httpx`** (or thin wrapper); public REST v3 only |
| **`[DALC-REQ-JIRA-TOOLS-006]`** | Tools | No tokens in logs/metrics; safe error logging |

### 3.2 Cross-capability coordination

| Path | Why |
|------|-----|
| `openspec/specs/dalc-rag-from-scrapers/spec.md` (if promoted) | Scrapers remain embed pipeline; **do not** conflate CronJob env with interactive Jira |
| **Steps 13–14** delta specs | Parity pattern: trigger vs tools separation, simulation gating, traceability style |

## 4. Tests and assertions (TDD; all must end green)

**Rule:** For each requirement row, **add or adjust failing tests first**, then implementation until commands pass. Test-writing is **not** a separate “stage” from code.

### 4.1 Pytest (`helm/src/tests/`)

| ID | Test intent | Assertion |
|----|-------------|------------|
| **TRIGGER-003** | Invalid secret / signature | No **`run_trigger_graph`** invocation (mock/spy) |
| **TRIGGER-003** | Non-JSON / wrong content type | Reject without trigger |
| **TRIGGER-001** | Happy-path sample webhook payload | Exactly **one** **`run_trigger_graph`** call; **`TriggerBody.message`** non-empty; **issue_key** / **project_key** / **event** present on chosen carrier model |
| **TRIGGER-002** | After trigger-only request | No HTTP POST to **`/v1/embed`** (spy **`httpx`** / embed client) |
| **TRIGGER-005** | Malformed body / verify failure | Logs **exclude** raw signing material and **`Authorization`** echo |
| **TOOLS-001** | Default / token absent | Tool invocation **does not** call **`/v1/embed`**; simulation returns structured dict |
| **TOOLS-001** | Token present (mocked **`httpx`**) | REST path invoked; still **no** `/v1/embed` |
| **TOOLS-002** | Settings / Helm fixture | Tools env var names or **`secretKeyRef`** paths **≠** scraper **`JIRA_*`** auth paths when both enabled |
| **TOOLS-003** | Comment / transition / scoped create | Mock transport: correct REST paths + JSON; permission errors → structured tool error |
| **TOOLS-004** | JQL / search cap | Over-cap or overlong JQL rejected or clamped per spec; response bodies contain **no** bearer token strings |
| **TOOLS-005** | Dependency | **`httpx`** declared in **`pyproject.toml`** with policy-consistent bounds |
| **TOOLS-006** | 401 / 403 from Jira | caplog / log records contain **no** substring of injected token |

**Optional (**`tasks.md` 2.5**):** webhook **idempotency** / dedupe — duplicate delivery → **at most one** trigger; document in-memory vs store limits for multi-replica.

**Invocation:**

```bash
cd helm/src && uv sync --all-groups && uv run pytest tests/ -v --tb=short
```

Add **`[DALC-REQ-JIRA-TRIGGER-00N]`** / **`[DALC-REQ-JIRA-TOOLS-00N]`** strings to docstrings of tests listed as **`docs/spec-test-traceability.md`** evidence.

### 4.2 Helm unittest (`helm/tests/`)

| Intent | Suite / pattern |
|--------|-----------------|
| **TRIGGER-004** / **TOOLS-002** | When example values enable **both** scraper and **jira** trigger/tools, Deployment env lists **distinct** **`secretKeyRef`** name/key paths for scraper vs trigger vs tools (unless documented maintainer exception) |
| **Wiring** | Trigger secret and tools secrets mount as env; **no** API tokens in ConfigMap `data` |

```bash
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
```

Follow **`docs/implementation-specs/03-consolidate-helm-tests-spec.md`** for suite location and **`values:`** paths (**`charts/declarative-agent-library-chart/templates/...`** post–step 2).

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

### 4.4 End-to-end smoke (**`tasks.md` 4.2** — manual or integration harness)

- Webhook → trigger run starts; agent uses tool to **comment** or **transition**; confirm **no** **`/v1/embed`** from tools path (**001**/**002**).

## 5. Staged execution (each stage ends with listed tests green)

1. **Helm keys + schema skeleton** — failing helm unittest for env wiring (**004**/**002**); then templates + `values.schema.json`.
2. **Trigger: verification + rejection paths** — pytest for **003**, **005**; FastAPI route behind feature flag.
3. **Trigger: payload mapping + `run_trigger_graph`** — pytest for **001**, **002**.
4. **Tools: settings + `httpx` factory** — pytest for **005**, **006** partial; simulation default (**001**).
5. **Tools: allowlisted REST operations + dispatch** — pytest for **003**, **004**, **006**; register tools + **`tools_impl/README.md`** (**tasks.md` 3.3**).
6. **Observability + side-effect checkpoints** — extend tests for **TOOLS-006** / correlation (**tasks.md` 3.4**).
7. **OpenSpec promotion** — merge deltas into **`openspec/specs/`** when workflow requires; matrix + **`#`** / docstring IDs; **`check_spec_traceability.py`** **0**.

## 6. Acceptance checklist

- [ ] All **`[DALC-REQ-JIRA-TRIGGER-001]`**–**`[005]`** and **`[DALC-REQ-JIRA-TOOLS-001]`**–**`[006]`** scenarios evidenced by pytest and/or helm unittest (or maintainer-waived per process).
- [ ] **Scraper**, **trigger**, and **tools** use **documented disjoint** configuration keys (**004**, **002**).
- [ ] **No** **`POST /v1/embed`** on trigger forwarding or default tools paths (**002**, **001**).
- [ ] **Jira REST** via **`httpx`**; timeouts + structured errors (**005**).
- [ ] Logs and Prometheus labels free of token / signing secret material (**005**, **006**).
- [ ] **`python3 scripts/check_spec_traceability.py`** passes after any promoted SHALL / matrix updates.

## 7. Commands summary

```bash
cd helm/src && uv run pytest tests/ -v --tb=short
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
python3 scripts/check_spec_traceability.py
```

## 8. Clarifying questions (human / planner)

1. **Webhook topology for v1:** native **Jira Cloud webhooks** only vs **Jira Automation** outbound webhooks parity (**`design.md` open question**)?
2. **Verification mechanism:** shared secret (query/header per Atlassian docs) vs **Connect JWT** path required for first release?
3. **Helm layout:** nested **`jira.trigger` / `jira.tools`** vs flat **`jiraTrigger` / `jiraTools`** — align with **`dedupe-helm-values-observability`** and any existing draft **`tools.jira`** in chart (**`design.md` open question**)?
4. **Jira context on trigger:** extend **`TriggerBody`**, nest a typed model, or pass **only** via **`TriggerContext`** — what do **`jira-tools`** implementations expect for default **issue_key** / **project_key** when the model omits them?
5. **`thread_id` / checkpointing:** composite from **issue key + event id** vs random UUID — align with **step 12** HITL / Slack trigger conventions if Jira threads are conversational.

## 9. Downstream LLM note (plan-for-downstream-llm)

Human reviewer: resolve §8 where possible, then paste this fenced brief to the implementing LLM. Implementer: if §8 unanswered, choose the **smallest consistent** option (prefer **direct `run_trigger_graph`**, **distinct Secret refs**, **TriggerBody fields** only if backward compatible or version-gated), document in PR, and keep **Helm keys stable** for follow-up.
`````
