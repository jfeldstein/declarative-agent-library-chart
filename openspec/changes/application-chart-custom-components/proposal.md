## Why

Application teams that embed **declarative-agent-library-chart** need a **supported, repeatable way** to ship **their own** Python implementations of MCP-style tools, inbound triggers, and scraper jobs—not only the built-in Jira/Slack/RAG integrations. Without a clear contract, teams fork the library image, patch package layout, or rely on undocumented env/volume tricks, which breaks upgrades and obscures security boundaries (allowlists, secrets, CronJob wiring).

## What Changes

- Define a **first-class extension model** for **consuming Helm application charts**: how custom code is packaged (image and/or volumes), how it is **discovered** at runtime (module path, registration), and how it interacts with existing allowlists (`mcp.enabledTools`), trigger deployments, and scraper `CronJob` command/entrypoints.
- Document **Helm chart surface** expectations: which values passthrough (`extraEnv`, volumes, image overrides, optional ConfigMaps) applications **SHALL** use for custom components; what the library chart **SHALL** guarantee vs. remain undefined (to avoid implying arbitrary server-side plugin loading without review).
- Add **`examples/with_custom_components/`**: a minimal **application chart** that depends on the library (alias `agent`), demonstrates **one** custom tool id (wired through the normal MCP dispatch path), **one** trigger-side extension pattern or documented stub, and **one** scraper-job pattern (for example `CronJob` invoking a **custom module** alongside shared RAG/env conventions), with **README** describing defaults vs. optional overlays per existing example conventions.

## Capabilities

### New Capabilities

- `application-chart-custom-components`: Normative requirements for **application-chart extension** of tools, triggers, and scrapers when using **declarative-agent-library-chart** as a dependency (packaging, discovery, Helm wiring, and documentation expectations).

### Modified Capabilities

- `dalc-example-values-files`: Extend requirements only where the new example introduces **multiple documented setups** (additional `values*.yaml` files and README listing)—if the example stays single-path, **no delta** is required beyond satisfying existing README/default-file rules.

## Impact

- **Helm**: `helm/chart` templates and `values.yaml` / schema may gain **explicit optional fields** or documented patterns for mounts, command overrides, or registration env vars—scoped to avoid breaking defaults.
- **Python runtime**: `hosted_agents` dispatch/trigger/scraper entrypoints may gain **stable extension hooks** (for example importlib entry points or documented `PYTHONPATH` + module naming) alongside tests.
- **Examples & CI**: New tree under **`examples/with_custom_components/`**, potential **`helm/tests/`** suite and **`.github/workflows/ci.yml`** updates if the example is validated in CI.
- **Docs**: `examples/README.md` (and root README layout table if present) updated to list the new example.
