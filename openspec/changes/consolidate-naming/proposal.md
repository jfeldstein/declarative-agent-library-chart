## Why

The repository still carries **deprecated “config-first hosted agents” (CFHA)** naming in Helm defaults, Grafana assets, runtime constants, and docs, while the product is the **Declarative Agent Library Chart (DALC)**. Aligning identifiers reduces confusion for operators and keeps examples consistent with how the library chart is described.

## What Changes

- **BREAKING**: Helm library chart **`name`** becomes **`declarative-agent-library-chart`** (from `declarative-agent-library`); Helm template helpers and rendered resource names derived from the chart name will change accordingly.
- **BREAKING**: Parent `values.yaml` in examples (and documentation) nest subchart values under **`agent:`** instead of `declarative-agent-library:` — implemented via **`alias: agent`** on the dependency so the library chart’s internal value schema stays conventional.
- **BREAKING**: Default container **`image.repository`** uses **`declarative-agent-library-chart`** instead of deprecated **`config-first-hosted-agents`** (aligns “library chart” image name with the product).
- Rename **`grafana/cfha-agent-overview.json`** → **`grafana/dalc-overview.json`**; replace **`cfha`** product tags/UIDs in that dashboard with **`dalc`** where they denote the product (not OpenSpec requirement IDs).
- Update **`grafana/README.md`**, **`docs/observability.md`**, integration scripts, and tests that reference the old filenames, image repo, or `declarative-agent-library` values key / release name strings.
- **Out of scope for this change**: Renaming promoted OpenSpec **requirement ID prefixes** (`[CFHA-REQ-…]`, capability folder names under `openspec/specs/`) — that is a separate traceability-wide migration.

## Capabilities

### New Capabilities

- `dalc-library-chart-packaging`: Normative naming for the Helm library chart (`Chart.yaml` `name`), parent values key (`agent` via dependency alias), and default image repository string.

### Modified Capabilities

- `cfha-agent-o11y-logs-dashboards`: Update the documented **`service`** example and the **starter Grafana dashboard** path/name to **DALC** naming (`dalc-overview.json`, `declarative-agent-library-chart`).

## Impact

- **Helm**: `helm/chart/Chart.yaml`, `_helpers.tpl`, all templates referencing the chart name; `helm/chart/values.yaml`; example charts’ `Chart.yaml`, `Chart.lock`, `values.yaml`, and `tests/`.
- **Runtime**: `SERVICE_NAME` / OpenAPI titles / any user-visible string still saying `config-first-hosted-agents` or `cfha-*` where meant as product labels.
- **Observability**: Grafana JSON + README; Prometheus kind scripts (`job_name`, cluster suffixes) where they encode the old acronym for **product** context; docs and traceability matrix rows that point at dashboard file paths.
- **Tests**: Python tests, helm-unittest YAML, integration scripts; **`docs/spec-test-traceability.md`** and test docstrings that cite dashboard paths under **[CFHA-REQ-O11Y-LOGS-003]**.
- **Consumers**: Anyone depending on the chart by name or nesting values under the old key must update.
