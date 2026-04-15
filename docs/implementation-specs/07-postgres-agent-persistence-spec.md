# Step 7: postgres-agent-persistence

`````
# Downstream LLM implementation brief: `postgres-agent-persistence`

## 0. Context (read first)

- **Linear checklist:** Step **7** in `docs/openspec-implementation-order.md` — **after** `dedupe-helm-values-observability` (step **1**) so `HOSTED_AGENT_POSTGRES_URL` / chart **`checkpoints.postgresUrl`** wiring matches the tier-1 contract; coordinate with **step 2** naming if Grafana/docs paths still say legacy product strings.
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) (checkpoints values + env), [`02-consolidate-naming-spec.md`](02-consolidate-naming-spec.md), [`03-consolidate-helm-tests-spec.md`](03-consolidate-helm-tests-spec.md), [`04-examples-distinct-values-readmes-spec.md`](04-examples-distinct-values-readmes-spec.md), [`05-observability-automatic-enabled-components-spec.md`](05-observability-automatic-enabled-components-spec.md), [`06-token-metrics-dashboard-spec.md`](06-token-metrics-dashboard-spec.md).
- **Authoritative change bundle:** `openspec/changes/postgres-agent-persistence/` — `proposal.md`, `design.md`, `tasks.md`, delta spec `specs/dalc-postgres-agent-persistence/spec.md`.
- **Traceability gap (delta today):** The change-local delta uses bare **`### Requirement:`** headings **without** **`[DALC-REQ-…]`** bracket IDs on the same line. **Before promotion / merge** (per **DALC-VER-005**), every promoted **`### Requirement:`** **SHALL** carry a stable **`[DALC-REQ-…]`**, plus **`docs/spec-test-traceability.md`** rows and test citations.
- **Naming:** Proposal lists capability `cfha-postgres-agent-persistence`; on promotion use **`dalc-*`** folder/slug conventions consistent with other `openspec/specs/dalc-*` capabilities. Wire **ADR 0003** / **DALC-VER-005** traceability before merge.
- **Critical runtime nuance — two checkpoint gates:** `hosted_agents.trigger_graph._resolve_checkpointer` uses **`build_checkpointer(obs)`** only when `ObservabilitySettings.checkpoints_enabled` is true; otherwise it falls back to **`hosted_agents.checkpointing.resolve_checkpointer()`**, which keys off **`HOSTED_AGENT_CHECKPOINT_STORE`** (`memory` / `none` / reserved `postgres`/`redis`). A Postgres LangGraph saver must be reachable in the **obs-settings path** when operators enable checkpointing via **`HOSTED_AGENT_CHECKPOINTS_ENABLED`** + **`HOSTED_AGENT_CHECKPOINT_BACKEND=postgres`**. If `checkpoints_enabled` is false, **`HOSTED_AGENT_CHECKPOINT_STORE=postgres`** still raises from `resolve_checkpointer` today — **document and/or unify** so operators cannot configure a dead half-path (acceptable outcomes: single env story, or explicit validation error at startup).

## 1. Goal

1. **LangGraph Postgres checkpointer:** When checkpointing is enabled with backend **`postgres`** and a valid DSN (**`HOSTED_AGENT_POSTGRES_URL`** via `hosted_agents.observability.postgres_env.postgres_url`), **`build_checkpointer`** returns a working saver — **no** “image only bundles memory saver” `RuntimeError` (**delta: Postgres LangGraph checkpointer integration**).
2. **Durable app stores:** Correlation (**`SlackMessageRef` → `ToolCorrelation`**), human feedback (**`HumanFeedbackEvent`** / orphans), **side-effect checkpoints** (**`SideEffectCheckpoint`**), and optional **tool span summaries** — behind **repository protocols** with **Memory** and **Postgres** implementations; default remains process-local when store mode is **`memory`** or unset (**delta: durable application persistence; memory mode**).
3. **Migrations:** Versioned SQL (or agreed tool) under repo control; documented apply order for Helm / operators (**delta: schema versioning**).
4. **Helm:** Secret / URL refs, optional migration Job toggle, env for **`HOSTED_AGENT_OBSERVABILITY_STORE`** (per `design.md` / `tasks.md`) aligned with post-dedupe **`checkpoints.*`** / secrets patterns.
5. **Non-goals:** Per `design.md` — no W&B replacement, no multi-region active-active design, no Redis saver in this change.

## 2. Entities and interfaces

### 2.1 Checkpointer construction

```python
# hosted_agents/observability/settings.py — extend (signatures only; bodies omitted)
@dataclass(frozen=True)
class ObservabilitySettings:
    checkpoints_enabled: bool
    checkpoint_backend: str
    checkpoint_postgres_url: str | None
    observability_store: str  # memory | postgres — new per design/tasks
    # ... existing fields ...

    @classmethod
    def from_env(cls) -> "ObservabilitySettings": ...
```

```python
# hosted_agents/observability/checkpointer.py
def build_checkpointer(settings: ObservabilitySettings) -> Any | None:
    """SHALL return Postgres saver when backend postgres + URL present; SHALL fail fast with clear msg when misconfigured."""
```

```python
# LangGraph — illustrative dependency surface (pin exact package per langgraph version in helm/src/pyproject.toml)
# PyPI distribution name may use hyphens (e.g. langgraph-checkpoint-postgres); Python import/module typically uses
# underscores — resolve both from the landed dependency entry in pyproject.toml (TBD until the package is pinned).
# from <resolved_module> import ...  # noqa: illustrative
def make_postgres_checkpointer(dsn: str, *, pool_settings: ...) -> Any: ...
```

**Contract:** Checkpointer instance **SHALL** satisfy LangGraph compile/`get_state` / `get_state_history` semantics used by `trigger_graph` and checkpoint read helpers in the same module.

### 2.2 Dual resolution (must reconcile in code + docs)

```python
# hosted_agents/trigger_graph.py — existing selection (do not ignore when wiring Postgres)
def _resolve_checkpointer(ctx: TriggerContext, obs: ObservabilitySettings) -> Any | None: ...
```

**Contract:** After this change, **documented** operator configuration **SHALL** enable Postgres checkpoints without relying on undefined precedence between **`HOSTED_AGENT_CHECKPOINT_STORE`** and **`HOSTED_AGENT_CHECKPOINTS_ENABLED` / `HOSTED_AGENT_CHECKPOINT_BACKEND`**.

### 2.3 Repository protocols (replace module-level singletons for DI where practical)

```python
# New module e.g. hosted_agents/observability/repositories.py — Protocol sketches
class CorrelationRepository(Protocol):
    def put_slack_message(self, ref: SlackMessageRef, corr: ToolCorrelation) -> None: ...
    def get_by_slack(self, ref: SlackMessageRef) -> ToolCorrelation | None: ...

class FeedbackRepository(Protocol):
    def record_human(self, ev: HumanFeedbackEvent) -> HumanFeedbackEvent | None: ...
    def record_orphan_reaction(self, ev: OrphanReactionEvent) -> None: ...
    def human_events(self) -> list[HumanFeedbackEvent]: ...
    def orphans(self) -> list[OrphanReactionEvent]: ...

class SideEffectRepository(Protocol):
    def add(self, rec: SideEffectCheckpoint) -> None: ...
    def by_thread(self, thread_id: str) -> list[SideEffectCheckpoint]: ...

# Naming: design.md uses RunSpanRepository; this brief uses RunSpanSummaryRepository for the same protocol.
class RunSpanSummaryRepository(Protocol):
    def record_tool_span(self, row: ToolSpanSummary) -> None: ...
    def list_by_run(self, run_id: str) -> list[ToolSpanSummary]: ...
```

```python
@dataclass(frozen=True)
class ToolSpanSummary:
    tool_call_id: str
    run_id: str
    thread_id: str
    duration_ms: int
    outcome: str
    args_hash: str | None
    # ... bounded fields per design — no raw prompts by default
```

**Existing in-memory implementations to refactor toward protocols:**

- `hosted_agents.observability.correlation.CorrelationStore` / `correlation_store`
- `hosted_agents.observability.feedback.FeedbackStore` / `feedback_store`
- `hosted_agents.observability.side_effects.SideEffectCheckpointStore` / `side_effect_checkpoints`

**Call sites (non-exhaustive):** `slack_ingest.handle_slack_reaction_event`, `tools_impl/slack_post.py`, `app.py` routes reading side effects, any code that registers Slack message correlation after tool replies.

### 2.4 Migrations

**Target (after step 7):** versioned SQL (or agreed tool) under repo control — the tree may not yet contain this directory until the change lands.

```text
helm/src/migrations/   # planned / agreed path from design — SQL files only for v1
  V001__hosted_agents_schema.sql
  V002__correlation_feedback_side_effects.sql
  ...
```

**Contract:** Fresh DB + documented apply sequence **SHALL** create all **application-owned** tables and indexes from §2.3; LangGraph checkpointer tables **SHALL** be either owned by the pinned checkpointer package’s migration story **or** explicitly included in this repo’s migration set — pick one and document (no silent dual ownership).

### 2.5 Helm ↔ runtime env

```yaml
# Illustrative library values (exact keys after step 1); wire to Deployment env
checkpoints:
  postgresUrl: str
  enabled: bool
  backend: str
# Optional nested flags per tasks.md for migration Job / observability store
```

Map to **`HOSTED_AGENT_POSTGRES_URL`**, **`HOSTED_AGENT_CHECKPOINTS_ENABLED`**, **`HOSTED_AGENT_CHECKPOINT_BACKEND`**, **`HOSTED_AGENT_OBSERVABILITY_STORE`**, and any new secretKeyRef names consistent with chart README.

## 3. Dependencies and versions

- Pin **`langgraph`**-compatible Postgres checkpointer package + **`psycopg`** (v3) per `design.md`; document worker/pool sizing in `docs/runbook-checkpointing-wandb.md`.
- **CI:** default PR path = unit tests with mocks; optional integration tests behind a **`pytest` marker** — **`@pytest.mark.postgres`** only after adding a **`postgres`** entry to **`helm/src/pyproject.toml`** **`[tool.pytest.ini_options].markers`** (today the project defines **`integration`** and **`pglite`**, not **`postgres`**); or reuse an existing marker and document it. Optional job or local **testcontainers** / `docker run postgres` — follow repo CI budget conventions.

## 4. Spec ↔ tests (must pass; write tests first)

**Authoritative scenarios:** `openspec/changes/postgres-agent-persistence/specs/dalc-postgres-agent-persistence/spec.md` — each `### Requirement:` needs a promoted **`[DALC-REQ-PG-…]`** (or aligned slug) and matrix rows in **`docs/spec-test-traceability.md`** before merge.

| Requirement topic | Evidence type | Assertions |
|-------------------|---------------|--------------|
| Postgres checkpointer happy path | pytest | With env `HOSTED_AGENT_CHECKPOINTS_ENABLED=1`, `HOSTED_AGENT_CHECKPOINT_BACKEND=postgres`, valid DSN (container or mocked factory), `build_checkpointer` returns non-`None` saver; graph compile does not raise. |
| Postgres checkpointer missing DSN | pytest | Same with empty URL → **clear** `RuntimeError` / `ValueError` before serving (matches delta “fail fast”). |
| Correlation durability | pytest (integration optional) | Write `(channel_id, message_ts)` mapping; new process / new store instance with same DB → `get_by_slack` returns equivalent `ToolCorrelation`. |
| Human feedback durability | pytest | `HumanFeedbackEvent` fields stable across round-trip (`registry_id`, `schema_version`, `label_id`, `tool_call_id`, `checkpoint_id` when present). |
| Tool span summary | pytest | Row retrievable by `run_id` and/or `tool_call_id` with timing + outcome. |
| Migrations / fresh install | pytest or script test | Apply SQL to empty DB → expected tables/indexes exist (can use ephemeral Postgres in optional job). |
| Memory mode default | pytest | No `HOSTED_AGENT_POSTGRES_URL`, store `memory` → app starts; in-memory behavior unchanged for correlation/feedback when Postgres store off. |
| Helm wiring | helm unittest | Deployment env contains expected keys when values set; optional Job gated by values flag. |

**Gate:**

```bash
python3 scripts/check_spec_traceability.py
uv sync --all-groups --project helm/src
cd helm/src && uv run pytest tests/ -v --tb=short
# Helm unittest: see docs/implementation-specs/README.md and examples/with-scrapers + helm/tests/
```

## 5. Staged execution (TDD; tests in each stage, not deferred)

### Stage 1 — Checkpointer package + `build_checkpointer`

**Write first:** pytest that fails today (postgres branch raises); mock or container constructor injection if needed.

**Implement:** `helm/src/pyproject.toml` pins; `build_checkpointer` real Postgres path; connection error messages; reconcile **`_resolve_checkpointer`** / **`HOSTED_AGENT_CHECKPOINT_STORE`** story.

**Green when:** postgres-path pytest + existing checkpoint/memory tests pass.

### Stage 2 — SQL migrations + schema smoke

**Write first:** migration apply test against empty DB (optional marker).

**Implement:** SQL files, README/runbook section for `psql -f` / Job.

**Green when:** migration test passes; checkpointer integration still green.

### Stage 3 — Repositories + wiring

**Write first:** protocol compliance tests on Memory adapters; Postgres adapter tests (container or CI job).

**Implement:** `Postgres*` repos, `ObservabilitySettings.from_env` store switch, inject factories into FastAPI / ingest paths (reduce reliance on global `correlation_store` in new code paths).

**Green when:** durability scenarios in §4 pass; `slack_ingest` + API routes covered.

### Stage 4 — Helm + docs + OpenSpec promotion

**Write first:** helm unittest for env + optional Job.

**Implement:** chart values/templates; `docs/runbook-checkpointing-wandb.md` updates (pooling, PII, retention).

**Promote:** delta spec → `openspec/specs/`, archive change per workflow; traceability matrix + test comments.

**Green when:** **Local CI** parity per repository **[README.md](../../README.md)** (Python, Helm, ADRs) and **`.github/workflows/ci.yml`** pass; **`python3 scripts/check_spec_traceability.py`** exits **0**.

## 6. Acceptance checklist

- [ ] `build_checkpointer` supports **`postgres`** with pinned LangGraph checkpointer dependency.
- [ ] Misconfiguration fails fast with operator-actionable errors.
- [ ] Correlation, feedback, side-effects, (optional) span summaries persist to Postgres when store mode **`postgres`**; **`memory`** path unchanged for default installs.
- [ ] Versioned migrations shipped; apply path documented.
- [ ] Helm can mount URL/secret and toggle migration Job per `tasks.md`.
- [ ] **ADR 0003** / **DALC-VER-005**: requirement IDs + `docs/spec-test-traceability.md` + test citations; `python3 scripts/check_spec_traceability.py` exits **0**.
- [ ] No regression: existing pytest + helm unittest green.

## 7. Commands summary

```bash
python3 scripts/check_spec_traceability.py
uv sync --all-groups --project helm/src
cd helm/src && uv run pytest tests/ -v --tb=short
# Helm: docs/implementation-specs/README.md and .github/workflows/ci.yml
```
`````
