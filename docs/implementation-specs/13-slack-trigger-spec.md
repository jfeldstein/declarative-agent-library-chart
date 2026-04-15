# Step 13: slack-trigger

`````
# Downstream LLM implementation brief: `slack-trigger`

## 0. Context (read first)

- **Linear checklist:** Step **13** in `docs/openspec-implementation-order.md` — **Slack path:** inbound **Slack → hosted trigger** bridge; **precedes** **`slack-tools`** (step **14**) in the checklist—**counterpart** / **pairs with** tools for end-to-end “mention → run → reply” (DAG: **`STR -.-> STO`** — trigger first, then tools).
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) … [`12-declarative-langgraph-hitl-spec.md`](12-declarative-langgraph-hitl-spec.md) — especially **step 9** ([`09-slack-scraper-spec.md`](09-slack-scraper-spec.md)): CronJob **`scrapers.slack.*`** tokens and **`slack_job`** are **not** the trigger; **step 1/2** for post-dedupe **`agent:`** / values layout and naming.
- **Authoritative change bundle:** `openspec/changes/slack-trigger/` — `proposal.md`, `design.md`, `tasks.md`, normative delta **`specs/slack-trigger/spec.md`** (`[DALC-REQ-SLACK-TRIGGER-001]` … **`[DALC-REQ-SLACK-TRIGGER-005]`**).
- **Design locks:** (1) **Topology** — Socket Mode when no stable public URL; **HTTP Events API** when ingress exists. (2) **Invocation** — prefer **direct** `run_trigger_graph(TriggerContext(...))` over loopback `POST /api/v1/trigger` (document if HTTP is chosen). (3) **Idempotency** — optional **`event_id`** dedupe for Slack retries (`tasks.md` §3.2). (4) **Outbound** — trigger path **never** calls Slack **`chat.*`**; user-visible replies belong in **`slack-tools`**.
- **Traceability:** On promotion of `### Requirement:` rows to `openspec/specs/*/spec.md`, stable **`[DALC-REQ-…]`** / **`[DALC-VER-…]`** per **`openspec/specs/dalc-requirement-verification/spec.md`** and **ADR 0003** / **DALC-VER-005**; update **`docs/spec-test-traceability.md`**; cite IDs in **pytest** docstrings and/or **helm unittest `#`** comments; **`python3 scripts/check_spec_traceability.py`** exit **0**.
- **Non-goals:** **`slack_sdk.WebClient`** “tools” surface for posting; **RAG** / **`POST /v1/embed`** on this path; scraper schedules or **`SCRAPER_JOB_CONFIG`**.

## 1. Goal

1. **Inbound delivery:** Accept Slack **`app_mention`** (v1 scope per open question: DMs optional) via **HTTP Events** (URL challenge + signing secret) and/or **Socket Mode** (app-level token), per operator configuration.
2. **Trigger equivalence:** Each verified mention **SHALL** enter the same **trigger pipeline** as **`POST /api/v1/trigger`** — i.e. build **`TriggerContext`** and call **`run_trigger_graph`** — with **plain text** in **`TriggerBody.message`** plus **structured Slack identifiers** available to downstream runtime (so step **14** `slack-tools` does not guess channel/thread).
3. **Config isolation:** Helm/env keys for the trigger **SHALL** be **disjoint** from **`scrapers.slack.*`** per **`[DALC-REQ-SLACK-TRIGGER-004]`** (trigger vs **scraper** only). Trigger vs **Slack tools** credentials **SHALL** stay distinct under **`[DALC-REQ-SLACK-TOOLS-002]`** when step **14** lands; coordinate `openspec/changes/slack-tools/`.
4. **Safety:** No **`/v1/embed`** on the trigger forwarding step (`[DALC-REQ-SLACK-TRIGGER-002]`); signing secrets / app tokens **never** in logs or metric labels (`[DALC-REQ-SLACK-TRIGGER-005]`).

## 2. Entities and interfaces (signatures only; no bodies)

### 2.1 Runtime: Slack → trigger bridge

```python
# Conceptual module layout — align with helm/src/hosted_agents/ tree

from collections.abc import Awaitable, Callable
from typing import Any

from hosted_agents.agent_models import TriggerBody
from hosted_agents.trigger_context import TriggerContext
from hosted_agents.trigger_graph import run_trigger_graph

# Option A (preferred if spec requires JSON-serializable HTTP contract parity):
class SlackTriggerMetadata(BaseModel):
    """Optional extension to TriggerBody — requires relaxing extra= or nested model."""

    team_id: str | None = None
    channel_id: str
    thread_ts: str | None = None  # root ts for thread, else None
    message_ts: str | None = None
    event_id: str | None = None

# Option B: pass Slack fields only on TriggerContext — only if supervisor/tools can read ctx
# (today TriggerContext is internal; prefer Option A or explicit env/header contract documented in design.)

def slack_text_from_app_mention(event: dict[str, Any]) -> str: ...
"""Strip bot mention prefix; return user text for TriggerBody.message."""

def build_trigger_context_for_slack(
    *,
    cfg: Any,  # RuntimeConfig
    body: TriggerBody,
    system_prompt: str,
    request_id: str,
    run_id: str,
    thread_id: str,
    observability: Any | None,
) -> TriggerContext: ...
"""Mirror create_app post_trigger defaults (tenant, ephemeral, etc.)."""

def dispatch_slack_event_to_trigger(
    envelope: dict[str, Any],
    *,
    verify: Callable[..., Awaitable[None] | None],
) -> None: ...
"""After verify: route app_mention → run_trigger_graph; ignore unsupported types."""
```

**HTTP Events surface (when enabled):**

```python
def verify_slack_http_signature(
    signing_secret: str,
    *,
    timestamp_header: str,
    signature_header: str,
    raw_body: bytes,
) -> None: ...
"""SHALL raise on failure — caller returns 401/403 without invoking run_trigger_graph."""

def handle_slack_url_verification(body: dict[str, Any]) -> dict[str, str]: ...
"""Return { 'challenge': ... } — SHALL NOT call run_trigger_graph."""
```

**Socket Mode (when enabled):**

```python
async def run_slack_socket_mode_listener(
    app_token: str,
    *,
    on_app_mention: Callable[[dict[str, Any]], Awaitable[None]],
) -> None: ...
"""Long-lived task — chart implications: Deployment vs scale-to-zero (design.md)."""
```

### 2.2 Helm / env (disjoint keys — exact names TBD; must satisfy 004)

```yaml
# Illustrative only — wire to chart schema + docs; MUST NOT reuse scrapers.slack.auth for signing secret/socket token unless explicitly documented as shared secret (prefer separate secretKeyRefs).

slackTrigger:
  enabled: bool
  transport: str  # e.g. http_events | socket_mode
  signingSecretSecretRef: ...   # HTTP path
  appTokenSecretRef: ...        # Socket Mode path
  # bot token NOT required for trigger-only verification in many setups; document
```

**Contract:** Document operator setup: **Event Subscriptions** / **Socket Mode**, **`app_mention`** bot scope (`tasks.md` 1.2).

### 2.3 Prometheus / logs

- Reuse existing HTTP metrics patterns where the new route is HTTP; **do not** put secrets in label values (`[DALC-REQ-SLACK-TRIGGER-005]`).

## 3. Normative requirements → evidence (TDD)

**Write/adjust tests first** (red), then implementation (green). Each row maps to **`openspec/changes/slack-trigger/specs/slack-trigger/spec.md`**.

| ID | Behavior | Pytest / integration (suggested) |
|----|----------|-----------------------------------|
| `[DALC-REQ-SLACK-TRIGGER-001]` | `app_mention` → exactly one `run_trigger_graph` call with message + Slack ids | Mock `run_trigger_graph`: assert call count + `TriggerBody.message` + channel/thread fields |
| `[DALC-REQ-SLACK-TRIGGER-002]` | Trigger handler never calls embed client / `POST /v1/embed` | Spy on `httpx` / RAG client: assert no embed URL when only mention path exercised |
| `[DALC-REQ-SLACK-TRIGGER-003]` | Bad signature → no trigger; URL challenge → challenge JSON, no trigger | Parameterized HTTP tests with fixed bodies + headers |
| `[DALC-REQ-SLACK-TRIGGER-004]` | Values/env keys for trigger ≠ scraper job auth keys | Helm unittest: when both enabled, distinct secretKeyRef paths (or documented exception) |
| `[DALC-REQ-SLACK-TRIGGER-005]` | Malformed JSON / bad signature paths do not log raw `Authorization` / signature headers | Caplog / structured log assertions |

**Optional (`tasks.md` 3.2):** duplicate **`event_id`** delivery → **at most one** trigger (in-memory or pluggable store; document limitation for multi-replica).

**Helm:** If templates add routes/listeners, extend **`helm/tests/`** with values fixtures citing **`[DALC-REQ-SLACK-TRIGGER-004]`** where appropriate.

## 4. Stages (implementation order; tests are not deferred to a later stage)

1. **HTTP verification + URL challenge** — tests for **003**; route registration behind flag.
2. **Payload mapping + `run_trigger_graph` wire-up** — tests for **001**, **002**, **005**.
3. **Socket Mode dispatcher** — tests with mocked Slack SDK / websocket client as applicable for **001**.
4. **Helm + docs** — **004**, operator runbook (`tasks.md` 1.2); CI green including **`python3 scripts/check_spec_traceability.py`** after any promoted SHALL.

## 5. Clarifying questions (resolve before merge if ambiguous)

1. **Slack metadata on `TriggerBody`:** nested model vs top-level optional fields vs **`TriggerContext` extension** — which does **`slack-tools`** (step 14) expect?
2. **`thread_id` for checkpoints:** derive from **`thread_ts`** / **`channel_id`** composite vs random UUID vs Slack-provided id — align with step **12** HITL resume story if mentions are conversational threads.
3. **Single process vs worker:** Socket Mode + HTTP both enabled in one Deployment or mutually exclusive values validation?
`````
