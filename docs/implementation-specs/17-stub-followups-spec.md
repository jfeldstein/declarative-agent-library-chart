# Step 17: stub follow-ups

`````
# Downstream LLM implementation brief: stub follow-ups (`subagent-reference-system`, `ci-delta-flagging`, `jira-tools`)

## 0. Overall context (read first)

- **Linear checklist:** Step **17** in `docs/openspec-implementation-order.md` — activate or merge **stub** OpenSpec changes after platform work (**steps 1–15**) and optional **`agent-maker-system`** (**step 16**). Stubs are **not** an implementation queue until **`tasks.md`** + normative delta specs exist (or scope is absorbed by a parent change).
- **DAG:** `subagent-reference-system` and `ci-delta-flagging` have **dashed** edges into `agent-maker-system` — **soft coupling**; agent-maker **must not** assume their semantics until promoted (**`docs/implementation-specs/16-agent-maker-system-spec.md`**).
- **Subagent spec location:** A delta file also lives under **`openspec/changes/agent-maker-system/specs/subagent-reference-system/`**; canonical ownership and reconciliation are described in **step 16** (defer to stub change **`openspec/changes/subagent-reference-system/`** when activated). See [**16-agent-maker-system-spec.md**](16-agent-maker-system-spec.md) §0 / §3.2.
- **Authoritative stubs today:**
  - `openspec/changes/subagent-reference-system/proposal.md` (+ `.openspec.yaml` only).
  - `openspec/changes/ci-delta-flagging/proposal.md` (+ `.openspec.yaml` only).
  - `openspec/changes/jira-tools/` — **`.openspec.yaml` only** (no `proposal.md` / `tasks.md`); **normative Jira REST tools** currently live under **`openspec/changes/jira-bot/`** (`specs/jira-tools/spec.md` per step **15** brief).
- **Traceability invariant:** Any new **`### Requirement:`** **SHALL** lines carry stable **`[DALC-REQ-…]`** / **`[DALC-VER-…]`** IDs; update **`docs/spec-test-traceability.md`**; cite IDs in **pytest** docstrings and/or **helm unittest `#`** comments; **`python3 scripts/check_spec_traceability.py`** exits **0** (**ADR 0003** / **DALC-VER-005** / root **`AGENTS.md`**).

---

# Section A — `subagent-reference-system`

## A.0. Context

- **Proposal:** `openspec/changes/subagent-reference-system/proposal.md` — **stub only**: validated **subagent reference** model (existence, **loop depth**, **request-id** forwarding across call chain); **orthogonal** to **`agent-maker-system`**.
- **Additive contract (intended SHALL once promoted):** New runtime/chart fields for subagent references **must not** remove or redefine existing agent config keys incompatibly; behavior is **opt-in** via new fields or explicit flags.

## A.1. Goal

1. **Promote from stub:** Add **`design.md`**, **`tasks.md`**, and delta **`specs/*/spec.md`** with testable **SHALL** rows.
2. **Runtime:** Validate declarative subagent graph references **before** compile/run (cycle detection, max depth, unknown id); propagate **`X-Request-Id`** / internal correlation across nested calls.
3. **Helm / config:** Optional values subtree (name TBD) that enables validation strictness without breaking default installs.
4. **Agent-maker alignment:** Document how generated PRs may **opt into** subagent validation when this capability ships — **no** hard dependency in agent-maker v1.

## A.2. Entities and interfaces (signatures only; no bodies)

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class SubagentRef:
    """Declarative pointer from one agent/step to another agent id."""
    target_agent_id: str
    max_depth: int  # per-edge or per-root cap — pick one model and document

class SubagentGraphSpec:
    """Validated DAG or controlled cyclic model — exact shape follows design.md."""
    root_agent_id: str
    refs: tuple[SubagentRef, ...]

def parse_subagent_graph(raw: dict) -> SubagentGraphSpec: ...
def validate_subagent_graph(spec: SubagentGraphSpec) -> None: ...
"""SHALL raise ValidationError on unknown ids, exceeded depth, disallowed cycles."""

class RequestContext(Protocol):
    request_id: str
    def fork(self, *, suffix: str) -> "RequestContext": ...

def attach_request_context(ctx: RequestContext) -> None: ...
def current_request_context() -> RequestContext | None: ...

def invoke_subagent(
    *,
    parent_ctx: RequestContext,
    callee_agent_id: str,
    prompt: str,
) -> str: ...
"""SHALL enforce depth + id validation before dispatch."""
```

```yaml
# Illustrative Helm fragment — exact keys follow tasks.md + values.schema.json
subagents:
  validation:
    enabled: bool
    maxDepth: int
    failOnUnknownId: bool
```

## A.3. Normative specs / tests to satisfy (enumeration)

| Artifact | Action |
|----------|--------|
| New delta `openspec/changes/subagent-reference-system/specs/dalc-subagent-reference-system/spec.md` (name illustrative) | Add **`[DALC-REQ-SUBAGENT-*]`** (stable IDs) for validation, depth, correlation |
| `docs/spec-test-traceability.md` | Rows for each new ID with evidence paths + CI tier |
| Pytest under `helm/src/tests/` | Docstrings contain requirement ID strings |
| `python3 scripts/check_spec_traceability.py` | Exit **0** |

**Assertions (conceptual):**

- Unknown **`target_agent_id`** → **validation error** at compile/config load (not first runtime hit).
- **Nested** subagent chain exceeding configured **maxDepth** → error.
- **Request id** visible in structured logs for parent and child spans (bounded label set — no secrets).

## A.4. TDD-style stages (tests first each stage)

**Stage A1 — Parse/validate (no Helm yet):** Write failing pytest for **`validate_subagent_graph`** cases (unknown id, depth, simple cycle). Implement **`parse_*`** + **`validate_*`** until green.

**Stage A2 — Runtime propagation:** Write failing tests that **`invoke_subagent`** forks **`RequestContext`** and child execution logs **correlated** id. Implement contextvar (or existing o11y pattern) until green.

**Stage A3 — Integration with subagent execution path:** If repo uses **`hosted_agents.subagent_exec`** (see step **11** brief), add tests that **enabled** validation rejects bad declarative config before **`_run_subagent_text`**. Wire **opt-in** flag from env.

**Stage A4 — Helm + OpenSpec promotion:** Add values + schema + deployment env when design requires; promote specs per OpenSpec archive workflow; matrix + **`check_spec_traceability`** green.

## A.5. Maintainer clarifications (unblockers)

- **Cycles:** Are **any** controlled cycles allowed (e.g. bounded retry subgraph), or **strict DAG** only?
- **Id namespace:** Subagent ids = **Helm release agent id**, **graph node name**, or **separate registry**?

---

# Section B — `ci-delta-flagging`

## B.0. Context

- **Proposal:** `openspec/changes/ci-delta-flagging/proposal.md` — **stub only**: CI consumes **eval artifacts / metrics**, defines **regression** vs baseline, surfaces failures on PRs; **orthogonal** to agent authoring.
- **Consumer:** **`agent-maker-system`** may require generated PRs to pass checks this capability defines — **workflow + documentation** integration only once both exist.

## B.1. Goal

1. **Promote from stub:** Add **`design.md`**, **`tasks.md`**, delta **`specs/*/spec.md`**, and **one** reference workflow under **`.github/workflows/`** (or extend existing CI) that demonstrates **delta** comparison.
2. **Artifact contract:** Commit (or CI-upload) **baseline** format (JSON/YAML) — thresholds, metric names, suite summaries; **PR job** compares current run output to baseline.
3. **Failure semantics:** Clear **annotations** or job summary: which metric / test summary regressed and by how much (**no** secrets in logs).
4. **Non-network default:** Baseline comparison runs **offline** on checked-in fixtures unless maintainer explicitly adds optional live eval job.

## B.2. Entities and interfaces (signatures only; no bodies)

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class BaselineSpec:
    """Committed contract — exact fields follow design.md."""
    version: int
    metrics: dict[str, float]  # name -> max regression ratio or absolute delta
    suites: dict[str, dict[str, int]]  # suite -> counters (passed/failed/skipped)

@dataclass(frozen=True)
class EvalRunSummary:
    metrics: dict[str, float]
    suites: dict[str, dict[str, int]]

def load_baseline(path: Path) -> BaselineSpec: ...
def load_current_run(path: Path) -> EvalRunSummary: ...

def compare_to_baseline(
    baseline: BaselineSpec,
    current: EvalRunSummary,
) -> list[Regression]: ...

@dataclass(frozen=True)
class Regression:
    kind: str  # "metric" | "suite"
    name: str
    baseline_value: float
    current_value: float
    message: str
```

```yaml
# Illustrative GitHub Actions inputs — concrete job in tasks.md
# on: pull_request
# steps: checkout -> run eval producer -> python scripts/compare_eval_baseline.py
```

```python
# scripts/compare_eval_baseline.py — illustrative CLI surface
def main(argv: list[str]) -> int: ...
"""Exit 1 when any Regression; print human-readable table to stdout."""
```

## B.3. Normative specs / tests to satisfy (enumeration)

| Artifact | Action |
|----------|--------|
| Delta spec `openspec/changes/ci-delta-flagging/specs/dalc-ci-delta-flagging/spec.md` (illustrative) | **`[DALC-REQ-CI-DELTA-*]`** for baseline format, comparison rules, PR visibility |
| `docs/spec-test-traceability.md` | Rows linking workflow + script + pytest (if any) |
| Pytest for **`compare_to_baseline`** | Pure unit tests with fixtures in `tests/fixtures/ci-delta/` |
| `.github/workflows/ci.yml` or new workflow | Job appears in CI tier docs; optional: `workflow_dispatch` for manual baseline refresh |

**Assertions (conceptual):**

- **Strict improvement** (current better than baseline) does not fail unless design chooses “tight band” mode.
- **Missing metric** in current run → **fail** or **warn** per explicit SHALL.
- Comparator is **deterministic** (sorted keys, stable float formatting in messages).

## B.4. TDD-style stages

**Stage B1 — Core comparator:** Pytest fixtures: small `baseline.json`, `current.json`. Implement **`compare_to_baseline`** until green.

**Stage B2 — CLI script:** Add **`scripts/compare_eval_baseline.py`** with argparse; pytest **subprocess** or **`capsys`** tests for exit codes.

**Stage B3 — Workflow wiring:** Add minimal workflow job that runs script against **checked-in** sample artifacts (no external eval runner required for MVP).

**Stage B4 — OpenSpec promotion + traceability:** Promote capability; matrix rows; **`check_spec_traceability`** green.

## B.5. Maintainer clarifications (unblockers)

- **Baseline source of truth:** Repo-committed files vs **GitHub Actions cache** vs **artifact** on default branch?
- **Scope:** Helm-only regression (e.g. `helm unittest` counts) vs **Python eval** vs **both**?

---

# Section C — `jira-tools` (orphan change vs `jira-bot`)

## C.0. Context

- **Folder:** `openspec/changes/jira-tools/` contains **only** `.openspec.yaml` — **no** `proposal.md`, **`tasks.md`**, or `specs/`.
- **Normative tools work today:** Step **15** — **`openspec/changes/jira-bot/`** includes **`specs/jira-tools/spec.md`** (`[DALC-REQ-JIRA-TOOLS-001]` … **`006]`**) alongside **`jira-trigger`** (**`docs/implementation-specs/15-jira-bot-spec.md`**).
- **Ordering doc:** Step **17** lists **`jira-tools`** with stubs — interpret as **either** flesh out standalone change **or** **close** the empty change dir after confirming **`jira-bot`** owns delivery.

## C.1. Goal (pick one track — maintainer decision)

**Track 1 — Standalone `jira-tools` change (split from `jira-bot`):**

1. Author **`proposal.md`**, **`design.md`**, **`tasks.md`**, and move or duplicate normative **`specs/jira-tools/spec.md`** under **`openspec/changes/jira-tools/specs/`** with stable IDs preserved.
2. **`jira-bot`** change **SHALL** reference **`jira-tools`** as dependency or explicitly delegate tools tasks to avoid double implementation.

**Track 2 — Merge / archive empty `jira-tools`:**

1. Delete or archive **`openspec/changes/jira-tools`** once **`jira-bot`** tasks cover REST tools; update **`docs/openspec-implementation-order.md`** stub row if needed.

## C.2. Entities and interfaces (signatures only; no bodies)

*Reuse step **15** contracts — duplicate here for downstream focus:*

```python
from dataclasses import dataclass
import httpx

@dataclass(frozen=True)
class JiraToolsSettings:
    enabled: bool
    site_base_url: str
    email: str | None
    api_token: str | None

def jira_tools_settings_from_env() -> JiraToolsSettings: ...
def build_jira_tools_http_client(settings: JiraToolsSettings) -> httpx.Client | None: ...

def jira_search_issues(client: httpx.Client, jql: str, *, max_results: int) -> list[dict]: ...
def jira_get_issue(client: httpx.Client, issue_key: str, fields: list[str] | None) -> dict: ...
def jira_add_comment(client: httpx.Client, issue_key: str, body: str) -> dict: ...
def jira_transition_issue(client: httpx.Client, issue_key: str, transition_id: str) -> None: ...
def jira_create_issue(client: httpx.Client, project_key: str, fields: dict) -> dict: ...
```

```python
# tools_impl dispatch surface — illustrative
def dispatch_jira_tool(tool_id: str, arguments: dict) -> dict: ...
```

```yaml
# Helm: disjoint secrets from scrapers.jira — illustrative fragment
tools:
  jira:
    enabled: bool
    siteUrl: str
    auth:
      emailSecretRef: { name: str, key: str }
      apiTokenSecretRef: { name: str, key: str }
    scopes: { read: bool, comment: bool, transition: bool, create: bool }
```

## C.3. Normative specs / tests to satisfy (enumeration)

| Requirement family | Evidence |
|---------------------|----------|
| **`[DALC-REQ-JIRA-TOOLS-001]`** … **`006`** | Pytest for simulation vs live client gating; httpx mocking for REST paths |
| **`[DALC-REQ-JIRA-TOOLS-002]`** | Helm unittest: env var names distinct from **`scrapers.jira.*`** |
| **`[DALC-REQ-JIRA-TOOLS-006]`** | Logs/metrics tests: no **`Authorization`** in log fields |

**Commands (must end green for chosen track):**

```bash
cd helm/src && uv run pytest tests/ -v --tb=short
# per example chart:
helm unittest -f "../../helm/tests/<suite>.yaml" .
python3 scripts/check_spec_traceability.py
```

## C.4. TDD-style stages

**If Track 1:**

**Stage C1 — Spec + tasks only:** Write **`tasks.md`** with checkboxes mirroring step **15** tool scenarios; **no** runtime yet — PR is planning-only **or** accompanied by failing tests.

**Stage C2 — Red tests:** Add pytest for **`dispatch_jira_tool`** simulation paths and scope enforcement (**mutating** calls blocked when scope disabled).

**Stage C3 — Green implementation:** Implement settings, client factory, tools, Helm wiring until pytest + helm unittest green.

**Stage C4 — Traceability + `jira-bot` reconciliation:** Single source of truth for **`[DALC-REQ-JIRA-TOOLS-*]`** IDs; remove duplicate prose from **`jira-bot`** delta if moved.

**If Track 2:**

**Stage C0 — Process:** Confirm **`jira-bot`** owns tools; remove empty **`openspec/changes/jira-tools`** per OpenSpec housekeeping; **no** new code.

## C.5. Maintainer clarifications (unblockers)

- **Which track** (standalone vs absorb) before any implementation?
- If standalone: **dependency edge** in DAG — does **`slack-tools`** / **`jira-trigger`** ordering change?

---

## Cross-stub acceptance (repo health)

- [ ] Each activated stub has **`tasks.md`** + delta **`specs/*/spec.md`** (except **Track 2** for `jira-tools`, which removes the stub).
- [ ] **`openspec list`** shows actionable status (not “proposal only”).
- [ ] **`python3 scripts/check_spec_traceability.py`** passes after any SHALL promotion.
- [ ] Default CI **does not** require live Slack/Jira/GitHub for new jobs unless explicitly optional.

## Commands summary

```bash
python3 scripts/check_spec_traceability.py
cd helm/src && uv run pytest tests/ -v --tb=short
# helm unittest from each examples/* chart per README / CI
```
`````
