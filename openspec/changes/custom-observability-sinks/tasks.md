## 1. Phase 1 — Runtime loader and hook protocol

- [x] 1.1 Define **`ConsumerPluginsSettings`** (or equivalent) on **`ObservabilityPluginsConfig`** with **`enabled=false`** default; extend **`plugins_config_from_env`** with **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_*`** keys (master toggle, entry-point allowlist, strict mode, optional opaque JSON pointer).
- [x] 1.2 Implement **`importlib.metadata`** discovery for **`declarative_agent.observability_plugins`** (exact group string matches **`pyproject.toml`**); resolve each entry to an object exposing optional **`enqueue`** / **`attach`** methods matching **`design.md`**.
- [x] 1.3 Invoke **`enqueue_consumer_plugins`** immediately after **`enqueue_plugins_from_config`** and **`attach_consumer_plugins`** immediately after **`attach_plugins_from_config`** inside **`build_event_bus`** (or refactor **`wiring.py`** to delegate without duplicating provider imports).
- [x] 1.4 Default **non-strict**: catch exceptions per entry point, **`structlog`** warning, continue; honor strict env for fail-fast.
- [x] 1.5 Pytest: disabled-by-default (no entry-point imports); enabled loads a test entry point from **`conftest`** / **`importlib.metadata`** overrides; malformed entry raises only under strict mode.

## 2. Phase 2 — Packaging and Helm wiring

- [x] 2.1 Document and add **`[project.entry-points."declarative_agent.observability_plugins"]`** to **`helm/src/pyproject.toml`** (implementation may ship a **no-op** sample entry for docs/tests).
- [x] 2.2 Helm: add **`observability.plugins.consumerPlugins`** to **`helm/chart/values.yaml`** with **`enabled: false`**, optional **`entryPoints`**, optional **`configJson`** / Secret ref fields per **`design.md`**.
- [x] 2.3 Update **`helm/chart/values.schema.json`** **`observability.plugins`** — extend **`properties`** (respect **`additionalProperties: false`**) with **`consumerPlugins`** object; keep all new fields optional with safe defaults.
- [x] 2.4 Templates: inject env into **agent Deployment**, **scraper CronJobs**, and **RAG Deployment** only when **`consumerPlugins.enabled`** is true (follow existing patterns in **`_manifest_deployment.tpl`**, **`_manifest_scraper_cronjobs.tpl`**, **`_manifest_rag_deployment.tpl`**).
- [x] 2.5 Helm unittest (recommended): assert env keys absent when disabled; present when enabled using representative **`examples/*`** values.

## 3. Phase 3 — Examples, docs, traceability prep

- [x] 3.1 Add or extend an **`examples/*`** chart: depend on library chart, enable **`consumerPlugins`** in a **commented or opt-in** values snippet, and include a trivial local package or documented “install wheel” path that registers a **no-op** bus subscriber (proves registration without vendor SDKs).
- [x] 3.2 Update **`docs/observability.md`** with extension instructions, ADR **0014** / **0015** cross-links, PII/cardinality pointers (**ADR 0011**, Langfuse trace docs), and explicit **non-goals** (no ConfigMap code loading).
- [x] 3.3 On implementation PR: promote draft requirement IDs into **`openspec/specs/`**, add pytest/Helm evidence per root **`AGENTS.md`**, update **`docs/spec-test-traceability.md`**, run **`python3 scripts/check_spec_traceability.py`**.

## 4. Verification gates

- [x] 4.1 **`uv run pytest`** in **`helm/src`** passes with coverage floor; **`ruff`** / **`complexipy`** clean per project conventions.
- [x] 4.2 Helm validation: **`helm lint`** / project **`ct`** workflow parity as in **`docs/local-ci.md`** for touched charts.
