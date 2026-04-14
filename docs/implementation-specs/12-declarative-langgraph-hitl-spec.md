# Step 12: declarative-langgraph-hitl

`````
# Downstream LLM implementation brief: `declarative-langgraph-hitl`

## 0. Context (read first)

- **Linear checklist:** Step **12** in `docs/openspec-implementation-order.md` — **parallel / leaf** with `baseten-inference-provider` (step **11**); **additive** declarative **human-in-the-loop (HITL)** using LangGraph **functional API** (`interrupt`, `Command`); foundation checklist notes **checkpointing** is already complete in OpenSpec—this change expresses **pause/resume** in config and HTTP contracts.
- **Upstream alignment (mandatory):**
  - Step **1** ([`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md)): checkpoints env / values semantics (`checkpoints.*`, `HOSTED_AGENT_POSTGRES_URL`, `HOSTED_AGENT_CHECKPOINTS_*`)—HITL **requires** a LangGraph-compatible checkpointer; do not re-nest checkpoints under `observability`.
  - Step **2** ([`02-consolidate-naming-spec.md`](02-consolidate-naming-spec.md)): example parent values under **`agent:`**; keep chart/runtime naming consistent with promoted DALC conventions.
  - Step **7** ([`07-postgres-agent-persistence-spec.md`](07-postgres-agent-persistence-spec.md)): **production** durable pause/resume **SHOULD** target the same Postgres checkpointer story when operators enable HITL in cluster environments; reconcile dual checkpoint env gates documented in that brief so HITL docs do not describe a dead configuration path.
- **Authoritative change bundle:** `openspec/changes/declarative-langgraph-hitl/` — `proposal.md`, `design.md`, `tasks.md`, normative delta **`specs/declarative-langgraph-hitl/spec.md`**.
- **Terminology (from `design.md`):** **HITL** = LangGraph **`interrupt()` / `Command(resume=…)`** pre-continuation gates. **Post-hoc human feedback** (e.g. Slack emoji after the assistant replied) is **not** this change—reserve **human feedback** / **reaction correlation** for `tool-feedback-slack` and related stores.
- **Traceability:** When promoting **`### Requirement:`** rows to `openspec/specs/*/spec.md`, assign stable **`[DALC-REQ-…]`** (or **`[DALC-VER-…]`** if verification meta) per **`openspec/specs/dalc-requirement-verification/spec.md`** and **ADR 0003** / **DALC-VER-005**; update **`docs/spec-test-traceability.md`**; add requirement ID strings to **pytest docstrings** and/or **helm unittest `#`** comments; run **`python3 scripts/check_spec_traceability.py`** until exit **0**.
- **Non-goals:** No full approval UI; no mandatory replacement of every non-functional-API graph; no cross-tenant **authorization** for “who may resume” beyond documenting hooks (`design.md`).

## 1. Goal

1. **Declarative schema:** Pydantic models and/or JSON Schema + Helm values fragments for **named HITL pause points**, **interrupt kinds** (`simple_feedback`, `tool_call_review`), **ordering** relative to named automated steps, and **expected resume JSON** shapes.
2. **Runtime compiler:** Build an **`@entrypoint`** workflow from validated config using **`@task`**, **`interrupt()`**, and injected **checkpointer**—**no** `eval` of arbitrary Python (`design.md` decision 2).
3. **Semantics:** On resume, **tasks completed before the interrupt MUST NOT re-execute** for the same **`thread_id`**; resume maps to **`Command(resume=...)`** internally (`spec.md` + LangGraph docs).
4. **HTTP / operator contract:** JSON-serializable **interrupt descriptor** on pause (kind, human-readable or structured payload, **`thread_id`**); **resume** endpoint accepts JSON validated per interrupt kind → **`Command(resume=...)`** (`spec.md`).
5. **Ops:** Feature-flag or values-gate so default single-shot triggers unchanged when HITL is disabled (`tasks.md` 4.2); document **`thread_id`** generation for clients (`tasks.md` 3.3).
6. **Helm (optional in v1 scope):** If values wire HITL, follow post–step 1/2 layout under library / **`agent:`** examples; never put secrets in ConfigMap.

## 2. Entities and interfaces (signatures only; no bodies)

### 2.1 Declarative configuration (conceptual)

```python
# hosted_agents.hitl.config — illustrative names; align with repo module layout

from enum import Enum
from typing import Literal

class InterruptKind(str, Enum):
    SIMPLE_FEEDBACK = "simple_feedback"
    TOOL_CALL_REVIEW = "tool_call_review"

class SimpleFeedbackInterruptSpec:
    id: str
    after_step_id: str
    prompt_template: str  # may reference upstream outputs per proposal

class ToolCallReviewInterruptSpec:
    id: str
    # declarative mapping surface for continue / update / feedback outcomes

class HitlWorkflowSpec:
    steps: list[str]  # or richer StepRef — pick one ordered model and document
    interrupts: list[SimpleFeedbackInterruptSpec | ToolCallReviewInterruptSpec]

def parse_hitl_spec(raw: dict) -> HitlWorkflowSpec: ...
def validate_hitl_spec(spec: HitlWorkflowSpec) -> None: ...
```

**Contract:** Support **at least** the two patterns from LangGraph docs referenced in `proposal.md` / `design.md`: (a) **simple feedback**—string or small JSON resume merged into downstream task input; (b) **tool-call review**—resume actions **`continue`**, **`update`** (args patch), **`feedback`** (synthetic `ToolMessage`) (`design.md` decision 1).

### 2.2 Graph builder (functional API)

```python
# hosted_agents.hitl.builder — conceptual

from typing import Any, Callable

def compile_hitl_entrypoint(
    spec: HitlWorkflowSpec,
    *,
    checkpointer: Any,
    tool_registry: dict[str, Callable[..., Any]] | None = None,
) -> Callable[..., Any]:
    """Returns a LangGraph functional API entrypoint callable (decorated upstream)."""
```

**Contract:** Implementation **SHALL** use **`@entrypoint`**, **`@task`**, **`interrupt`**, and **`Command`** for resume per **`specs/declarative-langgraph-hitl/spec.md`** “Functional API and checkpointing” requirement.

### 2.3 Thread identity

```python
# Request / resume correlation

def assert_thread_id_present(headers_or_body: dict) -> str: ...
"""SHALL raise domain/HTTP 4xx with operator-actionable message when missing/invalid."""
```

**Contract:** Every HITL-capable invocation **SHALL** accept a stable **`thread_id`** (or configurable key name via env) on **invoke** and **resume**; mismatch → clear error (`tasks.md` 3.2, `spec.md` “Thread identity and correlation”).

### 2.4 HTTP surface (JSON contracts)

```typescript
// Interrupt descriptor — externally visible when paused
interface InterruptDescriptor {
  kind: "simple_feedback" | "tool_call_review";
  thread_id: string;
  interrupt_id: string;
  message: string;
  payload?: Record<string, unknown>;  // e.g. tool call snapshot for review
}

// Resume request — maps internally to Command(resume=...)
interface SimpleFeedbackResumeBody {
  thread_id: string;
  interrupt_id: string;
  value: string | Record<string, unknown>;
}

type ToolCallReviewAction = "continue" | "update" | "feedback";

interface ToolCallReviewResumeBody {
  thread_id: string;
  interrupt_id: string;
  action: ToolCallReviewAction;
  tool_call_id?: string;
  args_patch?: Record<string, unknown>;
  feedback_text?: string;
}
```

```python
# hosted_agents.app — illustrative route names only; align with existing FastAPI style

async def invoke_until_interrupt(request: Request) -> Response: ...
async def resume_run(request: Request) -> Response: ...
```

**Contract:** Callers **SHALL NOT** be required to send raw LangGraph Python objects at the HTTP boundary (`spec.md` “JSON-friendly interrupt and resume contract”).

### 2.5 Streaming / discovery

```python
# Reuse existing streaming hooks where present; document interrupt boundaries

async def stream_run_events(...) -> AsyncIterator[dict]: ...
"""SHALL yield or terminate in a way clients can detect 'interrupted' vs 'completed' per spec."""
```

**Contract:** When a run pauses, clients **SHALL** be able to observe **waiting for human input** and receive data sufficient to build a resume request (`spec.md` “Discovery of paused state”).

### 2.6 Settings and feature gate

```python
@dataclass(frozen=True)
class HitlSettings:
    enabled: bool
    # optional: path to mounted YAML, inline env JSON, or agent id → spec lookup

def hitl_settings_from_env() -> HitlSettings: ...
```

**Contract:** When **`enabled`** is false, existing trigger / single-shot paths **SHALL** behave as today (`tasks.md` 4.2).

## 3. Normative specs (implement against)

### 3.1 Delta spec (this change)

| Path |
|------|
| `openspec/changes/declarative-langgraph-hitl/specs/declarative-langgraph-hitl/spec.md` |

**Requirement headings (assign `[DALC-REQ-…]` on promotion):**

| Section | Intent |
|---------|--------|
| Declarative HITL configuration | Config-driven interrupt kinds + ordering; scenarios: simple feedback; tool-call review |
| Functional API and checkpointing | `@entrypoint` / `@task` / `interrupt` / `Command`; checkpointer mandatory; scenario: no duplicate side effects for task A after resume |
| Thread identity and correlation | Stable `thread_id` on invoke + resume; scenario: same thread resumes |
| JSON-friendly interrupt and resume contract | HTTP JSON → internal `Command(resume=...)` |
| Discovery of paused state | Streaming or status exposes interrupt kind + payload |

### 3.2 Related promoted specs (verify no contradiction after merge)

| Path | Notes |
|------|--------|
| `openspec/specs/dalc-postgres-agent-persistence/spec.md` | If promoted—Postgres checkpointer + env gates must align with HITL production story |
| Checkpoint / trigger specs already in `openspec/specs/` | Grep for `thread_id`, `checkpointer`, `trigger` language—update prose only if this change narrows contracts |

## 4. Tests and assertions (TDD; all must end green)

**Rule:** Write **failing pytest first** for each behavior below, then implementation until **`uv run pytest`** is green. Test-writing is **not** a separate stage from implementation.

### 4.1 Integration-style pytest (preferred evidence for `spec.md`)

| Test intent | Assertion |
|-------------|-------------|
| No re-run after resume | Instrument **task A** with a side-effect counter (module-level or dependency-injected); run until interrupt after A; resume; **counter for A does not increment** again for same **`thread_id`** (`spec.md` “Resume after interrupt does not repeat prior tasks”). |
| `thread_id` correlation | Mismatched or missing `thread_id` on resume → **4xx** with stable error code / message; no state corruption on disk/memory checkpointer fixture. |
| Simple feedback happy path | Declarative **`simple_feedback`** interrupt; resume string merges into downstream task input observable in result or captured messages. |
| Tool-call review branches | For each **`continue` / `update` / `feedback`**, assert resulting tool execution or synthetic **`ToolMessage`** matches LangGraph-documented pattern (mock LLM tool call emission). |
| Invalid resume shape | Wrong JSON for active interrupt kind → **4xx**; no partial graph mutation (`design.md` risk mitigation). |
| Feature gate off | `HITL` disabled → existing trigger path **unchanged** (golden / snapshot tests against current behavior). |
| Interrupt discovery | Streaming or final response payload includes **`kind`**, **`thread_id`**, and presentation payload (`spec.md` “Stream or status reflects interrupt”). |

```bash
cd helm/src && uv sync --all-groups --project . 2>/dev/null || uv sync --all-groups
cd helm/src && uv run pytest tests/ -v --tb=short
```

Add **`[DALC-REQ-…]`** strings to test **docstrings** used as matrix evidence after IDs are minted.

### 4.2 Helm (only if values/templates added)

| Suite | Role |
|-------|------|
| `helm/tests/*_test.yaml` | Assert optional env / feature flag wiring; **no** secrets in ConfigMap data |

Follow **`docs/implementation-specs/03-consolidate-helm-tests-spec.md`** invocation patterns from example chart directories.

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

## 5. Staged execution (each stage ends with listed tests green)

### Stage A — Schema + validation

**Tests first:** pytest table-driven cases for **invalid** declarative specs (unknown interrupt kind, duplicate ids, resume schema mismatch).

**Implement:** Pydantic models (or equivalent), loaders from env / file; **`validate_hitl_spec`**.

**Green when:** validation tests + full **`uv run pytest tests/`** pass.

### Stage B — Builder + in-memory checkpointer

**Tests first:** counter-based “task A not re-run” test using **`MemorySaver`** (or project-standard in-memory checkpointer).

**Implement:** **`compile_hitl_entrypoint`** for **`simple_feedback`** only.

**Green when:** no-re-run + simple feedback path tests pass.

### Stage C — Tool-call review

**Tests first:** three-branch tests for **`continue` / `update` / `feedback`** with mocked tool calls.

**Implement:** extend builder + resume mapping.

**Green when:** §4.1 tool-call tests pass.

### Stage D — HTTP endpoints + JSON contracts

**Tests first:** `httpx.AsyncClient` against FastAPI app—invoke until interrupt, parse **`InterruptDescriptor`**, POST resume, assert completion and counters.

**Implement:** routes, pydantic request/response models, error mapping.

**Green when:** HTTP tests + existing suite pass.

### Stage E — Postgres checkpointer path (optional sub-stage if bundled)

**Tests first:** marked integration test or containerized Postgres per repo CI policy—**skip** if no CI DB.

**Implement:** wire **`build_checkpointer`** / settings from step 7 so **`backend=postgres`** enables durable HITL.

**Green when:** marked tests pass where environment allows; default CI stays green with skips.

### Stage F — Helm gate + docs + OpenSpec promotion

**Tests first:** helm unittest only if templates change—red until env wired.

**Implement:** values + schema fragments in `tasks.md` 1.2 spirit; runtime README / operator doc for **`thread_id`** client flow (`tasks.md` 3.3); promote delta spec to **`openspec/specs/`** with bracket IDs; matrix rows.

**Green when:** **`python3 scripts/check_spec_traceability.py`** exits **0**; pytest (+ helm if touched) green.

## 6. Acceptance checklist

- [ ] Declarative schema supports **`simple_feedback`** and **`tool_call_review`** with documented resume JSON (`tasks.md` 1.1, 2.2–2.3).
- [ ] Functional API + checkpointer: interrupt/resume matches LangGraph semantics; **pre-interrupt tasks do not re-run** (`spec.md`).
- [ ] **`thread_id`** required and documented for invoke + resume (`spec.md`).
- [ ] HTTP layer uses **JSON** descriptors and resume bodies—no Python-type leakage at boundary (`spec.md`).
- [ ] Invalid resume → **4xx** with clear errors (`design.md`).
- [ ] HITL disabled → no behavior regression (`tasks.md` 4.2).
- [ ] **DALC-VER-005** satisfied on promotion: IDs, matrix, citations, **`check_spec_traceability.py`** **0**.

## 7. Commands summary

```bash
cd helm/src && uv run pytest tests/ -v --tb=short
python3 scripts/check_spec_traceability.py
# Helm (conditional)
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
```

## 8. Open questions (from `design.md` — resolve in PR or defer explicitly)

- Which **production checkpointer** is canonical when both memory and Postgres paths exist in operator docs?
- Should **subagents** inherit parent **`thread_id`** namespace or isolate interrupts per subagent invocation?

## 9. Clarifying questions (human / planner)

1. Should **v1** ship **HTTP only**, or also expose a **gRPC** / internal-only resume surface for future UI?
2. Is **Helm-first** configuration mandatory in the same PR as runtime, or may **v1** be **env-only** with Helm following in a fast follow?
`````
