## 1. Rename layout and chart metadata

- [x] 1.1 Rename `template/` to `helm/` (preserve `chart/`, `src/`, `tests/` structure).
- [x] 1.2 In `helm/chart/Chart.yaml`, set `type: library` and update `description` so it describes a reusable library chart (not a standalone install). *(**Done:** **`type: library`**; parent charts render the bundle via `templates/agent.yaml` using `include "declarative-agent.system"` (tunables under `.Values.agent`). Kubernetes YAML comes only from named `define` templates (e.g. `declarative-agent-library-chart.manifest.*`) wired by `declarative-agent-library-chart.systemBundled` / `declarative-agent.system`, matching [library chart](https://helm.sh/docs/topics/library_charts/) semantics—do not `helm install` `helm/chart` alone.)*
- [x] 1.3 Regenerate or hand-edit `helm/chart` artifacts if Helm warns (for example `values.schema.json` or comments referencing "application" only where inaccurate).

## 2. Application example and lockfile

- [x] 2.1 Update `examples/hello-world/Chart.yaml`: dependency `repository` to `file://../../helm/chart`; refresh description/comments that say "template chart".
- [x] 2.2 Run `helm dependency update` in `examples/hello-world/` and commit updated `Chart.lock` (and `charts/` tarball if the repo tracks it per `.gitignore`).
- [x] 2.3 Adjust `examples/hello-world/values.yaml` comments to reference `helm/chart` and subchart values keys as needed.

## 3. Docs, CI, and ancillary paths

- [x] 3.1 Update `README.md` table and prose: `helm/` instead of `template/`, library chart wording, install path via example chart.
- [x] 3.2 **`ci.sh` was removed;** parity lives in **`.github/workflows/ci.yml`** and **`ct.yaml`** (`helm dependency build`, **`helm unittest`** per example, **`ct lint --all`**). Confirm those jobs still cover **`examples/hello-world`** via the **`examples/*`** loop.
- [x] 3.3 Update `.dockerignore` and any other path literals (`helm/tests` vs `template/tests`).
- [x] 3.4 Update `helm/src/README.md`, `helm/tests/chart/README.md`, and template files under `helm/chart/templates/` only where paths or wording still say `template/`.

## 4. Verification

- [x] 4.1 From repo root or project dir, run **`helm lint`** / **`helm template`** on **`examples/hello-world`** after **`helm dependency update`**, or rely on the same stages in **`.github/workflows/ci.yml`** / **`ct lint`** (broader than hello-world alone).
- [x] 4.2 Search the repository for `template/` string references and fix stragglers.
