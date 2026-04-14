## 1. Helm library chart rename

- [ ] 1.1 Set `helm/chart/Chart.yaml` `name` to `declarative-agent-library-chart` and align `description` if needed
- [ ] 1.2 Rename all `declarative-agent-library` helper definitions and `include` references in `helm/chart/templates/**` and `_helpers.tpl` to `declarative-agent-library-chart`
- [ ] 1.3 Update `helm/chart/values.yaml` default `image.repository` to `declarative-agent-library-chart`
- [ ] 1.4 Update `helm/chart/values.schema.json` title and any schema text that names the chart

## 2. Example charts and locks

- [ ] 2.1 For each `examples/*/Chart.yaml`, set dependency `name: declarative-agent-library-chart`, add `alias: agent`, and run `helm dependency update` to refresh `Chart.lock`
- [ ] 2.2 Move subchart values under `agent:` in each example `values.yaml` (remove top-level `declarative-agent-library:`)
- [ ] 2.3 Update `examples/*/tests/*.yaml` and any `helm unittest` assertions that reference old release name fragments or values keys

## 3. Grafana and observability docs

- [ ] 3.1 `git mv` `grafana/dalc-agent-overview.json` → `grafana/dalc-overview.json`; update dashboard `uid`, `tags`, and titles that used **cfha** / **config-first-hosted-agents** to **dalc** / **declarative-agent-library-chart** as appropriate
- [ ] 3.2 Update `grafana/README.md` to document `dalc-overview.json` and import steps
- [ ] 3.3 Update `docs/observability.md` (and root `README.md` if applicable) for new image name, dashboard path, and `agent.*` Helm paths

## 4. Runtime and scripts

- [ ] 4.1 Set `SERVICE_NAME` (and similar) in `helm/src/hosted_agents/o11y_logging.py` to `declarative-agent-library-chart`
- [ ] 4.2 Update OpenAPI titles or other user-visible **cfha** strings (e.g. RAG app) to **dalc** or full product name where intended
- [ ] 4.3 Update `helm/src/tests/scripts/prometheus-kind-o11y-values.yaml`, `integration_kind_o11y_prometheus.sh`, and related tests to use **dalc-** job/cluster names and new image tag; fix `rg` hits for `config-first-hosted-agents` in scripts

## 5. Spec traceability and verification

- [ ] 5.1 Archive this change’s deltas into `openspec/specs/` per workflow (promote `dalc-library-chart-packaging`, apply MODIFIED blocks to `cfha-agent-o11y-logs-dashboards`) when implementing
- [ ] 5.2 Update `docs/spec-test-traceability.md` rows for **[DALC-REQ-O11Y-LOGS-001]**, **[DALC-REQ-O11Y-LOGS-003]**, and new **[DALC-REQ-DALC-PKG-***]** evidence paths
- [ ] 5.3 Add requirement ID strings to pytest docstrings / helm unittest comments per ADR 0003
- [ ] 5.4 Run `python3 scripts/check_spec_traceability.py` and fix any drift

## 6. Quality gate

- [ ] 6.1 Run `helm unittest` on `helm/chart` and all example charts; run `ct lint` if part of CI
- [ ] 6.2 Run `uv run pytest` (or project test entrypoint) for runtime and integration tests touched
- [ ] 6.3 `rg` for remaining `config-first-hosted-agents`, `cfha-agent-overview`, `declarative-agent-library:` (as a values root key), and stale `declarative-agent-library` helper prefix in active paths; resolve or document intentional leftovers (e.g. OpenSpec **CFHA-** IDs)
