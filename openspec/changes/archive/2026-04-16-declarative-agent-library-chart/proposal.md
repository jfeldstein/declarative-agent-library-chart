## Why

The shared Helm library is easier to explain and position when its name matches how we describe it: **declarative** (values-driven desired configuration) rather than overlapping terms like “config-first” or generic “hosted-agent.” Renaming branding and chart metadata to **Declarative Agent Library Chart** (and a consistent technical chart name) reduces ambiguity for operators and readers of the OpenSpec and repo docs.

## What Changes

- Align **Helm chart metadata** (`Chart.yaml`): `description` (and related fields) SHALL reflect “Declarative Agent Library Chart” / declarative-agent positioning.
- Rename the library chart **`name`** from `hosted-agent` to **`declarative-agent-library`** (Helm identifier; “Chart” is implied by context) so dependencies and docs use one vocabulary — **BREAKING** for any chart that depended on `name: hosted-agent` and for values nested under that dependency key.
- Update **application** consumers (e.g. `examples/hello-world`): `dependencies[].name`, `helm dependency update` / lockfile, and **values** keys that target the subchart.
- Update **documentation**, **comments**, and **OpenSpec** text that still say “hosted-agent,” “config-first chart,” or “template chart” where they mean this library.

## Capabilities

### New Capabilities

- `declarative-agent-library-chart`: Naming and metadata for the shared Helm library chart (human-facing title “Declarative Agent Library Chart,” technical chart name `declarative-agent-library`, descriptions, and consistency across repo docs and specs that refer to this chart).

### Modified Capabilities

- (none — no published requirements under `openspec/specs/` for this chart today; related work may exist in other in-flight changes such as `cfha-helm-library`.)

## Impact

- **Breaking**: Parent charts and values files that reference the dependency as `hosted-agent` must switch to `declarative-agent-library` (dependency name and subchart values key).
- **Docs / CI**: Any string match on `hosted-agent` as the chart name, README titles, and example descriptions need updates.
- **Forks / copies**: External clones using the old dependency name must follow the migration notes in `design.md`.
