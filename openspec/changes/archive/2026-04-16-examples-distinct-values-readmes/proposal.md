## Why

The **center of gravity** in this repository is the **library chart** (`helm/chart`); the **primary developer experience and API surface** for consumers is **values-driven**—what you put under `declarative-agent-library:` in an application chart’s values is how you compose behavior. That makes **examples** first-class documentation: each **meaningful configuration** should be **demonstrated in its own committed values file**, explained in that example’s README, and **locked in with helm-unittest** so regressions in template behavior are caught.

Today, several “stories” (toggles, optional integrations) can still live in one `values.yaml`, which obscures copy-paste installs and which knobs belong to which scenario. After **Helm Test File Consolidation** (`openspec/changes/consolidate-helm-tests/`), unittest suites will live under `helm/tests/`; we align example layout with the values-as-API model so each demonstrated configuration is a distinct file, documented, and unittest-covered.

## What Changes

- For examples that showcase **multiple important configuration setups**, split into **one `values*.yaml` per setup** (naming convention TBD in design), keeping a clear default for `helm upgrade --install .` where that remains ergonomic.
- Add or extend each affected example’s **README.md** so it **indexes and explains** every values file: purpose, when to use it, and how it differs from others.
- Extend **helm-unittest** so each example’s suite includes **at least one test path (or `values:` block) per values file** that matters for the demonstration, asserting the config-specific rendering or labels the README promises.
- **Dependency**: Implement after **`consolidate-helm-tests`** is applied (central `helm/tests/` suites and CI `helm unittest -f`); this change assumes unittest YAML is not colocated under `examples/*/tests/`.

## Capabilities

### New Capabilities

- `cfha-example-values-files`: Normative expectations for how example charts structure multiple values files and document them in per-example READMEs (naming, defaults, discoverability).

### Modified Capabilities

- `cfha-helm-unittest`: Extend requirements so example chart unittest coverage explicitly includes **each documented values file** for examples with multiple setups (not only “default example values”), without weakening existing assertions.

## Impact

- **`examples/*/`**: New or renamed `values*.yaml` files; README updates; possible small Chart/CI notes if default install path changes.
- **`helm/tests/`** (post-consolidation): Additional `values:` entries or `it:` cases per values file; traceability comments updated per `docs/spec-test-traceability.md`.
- **`docs/spec-test-traceability.md`**: New or updated rows if new **SHALL** IDs are added.
- **`.github/workflows/ci.yml`**: Unchanged in principle if CI already runs `helm unittest -f` per example; verify after adding suites.
