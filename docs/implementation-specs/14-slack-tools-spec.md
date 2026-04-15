# Step 14: slack-tools

`````
# Downstream LLM implementation brief: `slack-tools`

## 0. Context (read first)

- **Linear checklist:** Step **14** in `docs/openspec-implementation-order.md` — **Slack path:** **LLM-time** Slack **Web API** tools (reactions, posts, updates, bounded history); pairs with **`slack-trigger`** (step **13**) for “mention → run → reply” (`STR -.-> STO` in the DAG).
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) … [`13-slack-trigger-spec.md`](13-slack-trigger-spec.md) — especially **step 9** ([`09-slack-scraper-spec.md`](09-slack-scraper-spec.md)): **`scrapers.slack.*`** / **`slack_job`** are **CronJob RAG ingestion**, **not** interactive tools; **step 13**: trigger path **must not** call **`chat.*`**; **slack-tools** owns outbound Web API during **`run_tool_json`** / graph execution.
- **Authoritative change bundle:** `openspec/changes/slack-tools/` — `proposal.md`, `design.md`, `tasks.md`, normative delta **`specs/slack-tools/spec.md`** (`[DALC-REQ-SLACK-TOOLS-001]` … **`[DALC-REQ-SLACK-TOOLS-006]`**).
- **Design locks:** (1) **`slack_sdk.WebClient`** with timeouts and structured errors (`design.md`). (2) **Env prefix** for tools (illustrative **`HOSTED_AGENT_SLACK_TOOLS_*`**) **disjoint** from **`scrapers.slack.*`** auth env and from **`slack-trigger`** signing secret / Socket Mode app token (**`[DALC-REQ-SLACK-TOOLS-002]`**; coordinate `openspec/changes/slack-trigger/` Helm keys). (3) **Simulation vs real:** when bot token absent, keep **simulated** **`slack.post_message`** (or equivalent) for CI; when present, call Slack (**`[DALC-REQ-SLACK-TOOLS-001]`** / `tasks.md` 2.3). (4) **Non-goal:** Slack event subscription / **`app_mention`** ingress — **`slack-trigger`** only.
- **Traceability:** On promotion of `### Requirement:` rows to `openspec/specs/*/spec.md`, stable **`[DALC-REQ-…]`** per **`openspec/specs/dalc-requirement-verification/spec.md`** and **ADR 0003** / **DALC-VER-005**; update **`docs/spec-test-traceability.md`**; cite IDs in **pytest** docstrings and/or **helm unittest `#`** comments; **`python3 scripts/check_spec_traceability.py`** exit **0**.
- **Related runtime:** Correlation / side-effect checkpoints for real Slack posts may touch stores documented in **step 7** ([`07-postgres-agent-persistence-spec.md`](07-postgres-agent-persistence-spec.md)) — wire **without** breaking memory-mode defaults.

## 1. Goal

1. **Allowlisted tools:** Implement (or extend) **`hosted_agents.tools_impl`** modules for **reactions** (add/remove), **post** (channel + optional **`thread_ts`**), **`chat.update`**, and **bounded** **`conversations.history`** / thread replies per **`[DALC-REQ-SLACK-TOOLS-003]`** / **`[DALC-REQ-SLACK-TOOLS-004]`** — caps and clear errors on rate limits (`design.md` risks).
2. **Dispatch:** Register tool ids in **`dispatch`** + document in **`tools_impl/README.md`** (`tasks.md` 2.3); gate real **`WebClient`** vs simulation on **tools-specific** token presence (**`[DALC-REQ-SLACK-TOOLS-001]`**).
3. **Helm:** Values/env for Slack tools **only** via documented keys **non-overlapping** with scraper CronJob and trigger secrets (**`[DALC-REQ-SLACK-TOOLS-002]`**); **`secretKeyRef`** for tokens — never ConfigMap plaintext.
4. **Observability:** Structured logging / metrics on real calls **without** secrets in log fields or Prometheus labels (**`[DALC-REQ-SLACK-TOOLS-006]`**).
5. **OAuth scopes:** Document required scopes for chat, reactions, history in chart README or operator doc (`tasks.md` 1.2).

## 2. Entities and interfaces (signatures only; no bodies)

### 2.1 WebClient factory (tools path)

```python
# hosted_agents.tools_impl.slack_client — illustrative module name

from slack_sdk import WebClient

def build_slack_tools_client(*, timeout_seconds: float | None = None) -> WebClient | None:
    """Return None when tools token env unset — callers keep simulation path."""

def slack_tools_settings_from_env() -> SlackToolsSettings: ...
```

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SlackToolsSettings:
    """Load from HOSTED_AGENT_SLACK_TOOLS_* (exact names follow implementation + schema)."""
    enabled: bool
    bot_token: str | None  # from env injected by secretKeyRef — not from Helm values literals
    # optional: max_history_messages, max_history_age_minutes, http_timeout_seconds
```

**Contract:** **Never** read scraper **`SLACK_BOT_TOKEN`** / trigger signing secret as the tools token unless **explicitly** documented as shared with maintainer approval — default story is **separate** secret refs (**`[DALC-REQ-SLACK-TOOLS-002]`**).

### 2.2 Tool implementations (`tools_impl`)

```python
# hosted_agents.tools_impl.slack_post — extend or split modules per open question

def run(arguments: dict) -> dict: ...
"""Simulated post when client is None; else WebClient.chat_postMessage — return structured ids."""

def add_reaction(arguments: dict) -> dict: ...
def remove_reaction(arguments: dict) -> dict: ...
def update_message(arguments: dict) -> dict: ...
def fetch_thread_history(arguments: dict) -> dict: ...
"""Normalized list of messages; enforce caps; no raw Authorization in return payload."""
```

**Contract:** Tool I/O **SHALL NOT** trigger **`POST /v1/embed`** in default configuration (**`[DALC-REQ-SLACK-TOOLS-001]`**).

### 2.3 Dispatch registration

```python
# hosted_agents.tools_impl.dispatch — conceptual

def invoke_tool(tool_id: str, arguments: dict) -> dict: ...
"""Route allowlisted slack.* tool ids to implementations."""
```

### 2.4 Helm / values (illustrative — exact keys in chart PR)

```yaml
# Under library chart root or agent: in examples — align with slack-trigger disjoint naming
slackTools:
  enabled: bool
  botTokenSecretRef:
    name: str
    key: str
  # optional knobs: timeouts, history caps — non-secret only in values
```

**Contract:** When **`scrapers.slack`** and **`slackTools`** (and **`slackTrigger`**) are all enabled, rendered Deployment env **SHALL** use **distinct** `secretKeyRef` name/key paths unless documented maintainer exception (**`[DALC-REQ-SLACK-TOOLS-002]`** scenario).

### 2.5 Dependency surface

```text
helm/src/pyproject.toml  # SHALL list slack_sdk with version policy ([DALC-REQ-SLACK-TOOLS-005])
```

## 3. Normative specs (implement against)

### 3.1 Delta spec (this change)

| Path |
|------|
| `openspec/changes/slack-tools/specs/slack-tools/spec.md` |

| ID | One-line intent |
|----|-----------------|
| **`[DALC-REQ-SLACK-TOOLS-001]`** | Tools only during active run; **no** default RAG **`/v1/embed`** from tool path |
| **`[DALC-REQ-SLACK-TOOLS-002]`** | Credentials **distinct** from **`scrapers`** (and from trigger verification material) |
| **`[DALC-REQ-SLACK-TOOLS-003]`** | Reactions, post (incl. thread), **`chat.update`** |
| **`[DALC-REQ-SLACK-TOOLS-004]`** | Bounded history read(s); normalized records; no bearer token in tool JSON |
| **`[DALC-REQ-SLACK-TOOLS-005]`** | **`slack_sdk`** only; no undocumented private Slack HTTP |
| **`[DALC-REQ-SLACK-TOOLS-006]`** | No tokens in logs/metric labels; safe error logging |

### 3.2 Cross-change coordination

| Path | Why |
|------|-----|
| `openspec/changes/slack-trigger/specs/slack-trigger/spec.md` | **`[DALC-REQ-SLACK-TRIGGER-004]`** — trigger vs **Slack scraper** configuration isolation (not trigger vs tools). Cross-check that **`[DALC-REQ-SLACK-TOOLS-002]`** still covers tools vs scraper/trigger credential separation after both land. |

## 4. Tests and assertions (TDD; all must end green)

**Rule:** For each behavior row, **add or adjust failing tests first**, then implementation until commands pass. Test-writing is **not** a separate “stage” from code.

### 4.1 Pytest (`helm/src/tests/`)

| ID | Test intent | Assertion |
|----|-------------|------------|
| **001** | Default / token absent | Invoking post tool **does not** call embed URL (spy `httpx` / RAG client); simulation path still returns structured shape |
| **001** | Token present (mocked **`WebClient`**) | **`chat_postMessage`** (or patched API) invoked once; still **no** `/v1/embed` |
| **002** | Helm or settings fixture | Parsed config exposes **different** env var names or secret refs for tools vs scraper when both enabled |
| **003** | Reactions / post / update | Mock transport: correct Web API method + args; success + Slack API error → structured error dict |
| **004** | History cap | Request asks above cap → clamped or rejected per spec; response messages lack token fields |
| **005** | Import / metadata | `slack_sdk` importable; version constraint present in **`pyproject.toml`** if policy tests exist |
| **006** | Auth failure | **`SlackApiError`** or 401 path: caplog / log records contain **no** substring of injected token; metrics labels do not include token |

**Invocation:**

```bash
cd helm/src && uv sync --all-groups && uv run pytest tests/ -v --tb=short
```

Add **`[DALC-REQ-SLACK-TOOLS-00N]`** to docstrings of tests used as **`docs/spec-test-traceability.md`** evidence.

### 4.2 Helm unittest (`helm/tests/`)

| Intent | Suite / pattern |
|--------|-----------------|
| **002** / wiring | When example values enable **`slackTools`** (or final key name), Deployment lists **tools** token **`secretKeyRef`** distinct from scraper env; **no** bot token in ConfigMap `data` |
| Optional | New or extended example **`values*.yaml`** only if CI already pattern-matches extra suites — else extend existing example per **`docs/implementation-specs/03-consolidate-helm-tests-spec.md`** |

```bash
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
```

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

## 5. Staged execution (each stage ends with listed tests green)

1. **Settings + factory** — pytest for env matrix (disabled, enabled missing secret, enabled mock); **`build_slack_tools_client`** returns **`None`** vs client (**006** partial).
2. **Post path: simulation vs real** — extend **`slack_post`** / dispatch (**001**, **003** post scenario).
3. **Reactions + update + bounded history** — new tests then implementations (**003**, **004**).
4. **Helm + docs** — failing helm unittest first (**002**); chart `values.yaml` / `values.schema.json` / `deployment.yaml`; README scopes (**tasks.md** 1.2).
5. **OpenSpec promotion** — merge delta into **`openspec/specs/`** when workflow requires; matrix + **`#`** / docstring IDs; **`check_spec_traceability.py`** **0**.

## 6. Acceptance checklist

- [ ] All **`[DALC-REQ-SLACK-TOOLS-001]`**–**`[006]`** scenarios evidenced by pytest and/or helm unittest (or maintainer-waived per process).
- [ ] Tools token and trigger/scraper secrets **disjoint** in documented keys and rendered manifests (**002**).
- [ ] No **`POST /v1/embed`** on default Slack-tools-only paths (**001**).
- [ ] **`slack_sdk.WebClient`** used for real calls; timeouts documented (**005**).
- [ ] Logs and metrics free of token material (**006**).
- [ ] **`python3 scripts/check_spec_traceability.py`** passes after any promoted SHALL / matrix updates.

## 7. Commands summary

```bash
cd helm/src && uv run pytest tests/ -v --tb=short
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
python3 scripts/check_spec_traceability.py
```

## 8. Clarifying questions (human / planner)

1. **Tool id surface:** single **`slack.post_message`** with optional **`thread_ts`** vs separate **`slack.post_thread_reply`** — resolve against `design.md` open question (split vs overload).
2. **Shared Kubernetes Secret:** may operators reuse one Secret object with **different keys** for scraper vs tools, or must Secret **metadata.name** differ?
3. **Correlation with `slack-trigger`:** does **`TriggerBody`** (step 13) already carry **`channel_id` / `thread_ts`** so tools default arguments can be filled without model supplying ids — or must the model always pass explicit ids?

## 9. Downstream LLM note (plan-for-downstream-llm)

Human reviewer: resolve §8 where possible, then paste this fenced brief to the implementing LLM. Implementer: if §8 unanswered, choose the smallest consistent option, document in PR, and keep **Helm keys stable** for follow-up.
`````
