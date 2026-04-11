## 1. Library chart metadata and Helm templates

- [x] 1.1 Set `name: declarative-agent-library` and update `description` in `helm/chart/Chart.yaml`.
- [x] 1.2 Rename Helm helper definitions and includes from `hosted-agent.*` to `declarative-agent-library.*` in `helm/chart/templates/_helpers.tpl` and every template under `helm/chart/templates/` (including chart tests).
- [x] 1.3 Update `helm/chart/values.schema.json` title and any user-facing strings that say `hosted-agent` where they mean the chart.
- [x] 1.4 Run `helm lint` on the library chart directory after template renames.

## 2. Application consumers and tooling

- [x] 2.1 Update `examples/hello-world/Chart.yaml` dependency `name` to `declarative-agent-library`, fix description text, run `helm dependency update`, and commit `Chart.lock`.
- [x] 2.2 Rename subchart values key in `examples/hello-world/values.yaml` from `hosted-agent:` to `declarative-agent-library:`.
- [x] 2.3 Update `skaffold.yaml` setValue paths from `hosted-agent.*` to `declarative-agent-library.*`.
- [x] 2.4 Update `devspace.yaml` selectors or value keys that reference `hosted-agent` if they must match the new chart/template naming.
- [x] 2.5 Run `helm template` / `helm lint` on `examples/hello-world` and execute `ci.sh` if available.

## 3. Documentation and verification

- [x] 3.1 Update `README.md` and `helm/tests/chart/README.md` to describe the **Declarative Agent Library Chart** and `declarative-agent-library` dependency name; fix port-forward and `kubectl` examples that reference old label values if labels changed.
- [x] 3.2 Search `this repository` for `hosted-agent` and resolve remaining chart-identity references (leave Python package / Docker image names unchanged unless explicitly in scope).
- [x] 3.3 Confirm acceptance path still works (kind + curl to **8088** per README) after renames.
