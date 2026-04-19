## Context

`this repository` ships a reusable Helm chart today as **`type: application`** under `template/chart/` (`hosted-agent`). `examples/hello-world` is an application chart that lists it as a `file://` dependency. That layout predates an explicit decision to model the shared chart as a **library**: operators should install a **parent application release** (the example or a user chart), not `helm install` the shared chart alone.

## Goals / Non-Goals

**Goals:**

- Move shared packaging to `helm/` (rename from `template/`) and set the shared chart `Chart.yaml` to **`type: library`**.
- Keep **hello-world** (and CI) validating the same rendered manifests and runtime behavior: `helm dependency update` + `helm template`/`helm install` on an **application** chart that depends on the library.
- Update docs and path references (`README`, `ci.sh`, `.dockerignore`, example `Chart.yaml` / lock, inline comments) consistently.

**Non-Goals:**

- Changing runtime behavior, image build, or the HTTP trigger contract.
- Publishing the chart to an OCI or HTTP repository (still `file://` for the prototype).
- Splitting the library into multiple subcharts.

## Decisions

1. **Library chart for the shared `hosted-agent` chart**  
   **Rationale:** Matches Helm semantics: the shared package supplies templates and values schema consumed by dependents; it is not a standalone installable unit.  
   **Alternative considered:** Keep `type: application` and document “do not install directly” — weaker guardrail than `type: library`.

2. **Rename `template/` → `helm/`**  
   **Rationale:** “Template” overloads Helm template files, OpenSpec “template” layout, and English usage; `helm/` states the purpose.  
   **Alternative considered:** `charts/` only — acceptable but less explicit about “Helm-only tree”; user asked for `helm/`.

3. **Examples remain `type: application`**  
   **Rationale:** `helm install` and CI target the example chart; the library is pulled in as a dependency. No change to the success path beyond path and dependency metadata.

4. **Preserve inner layout** (`chart/`, `src/`, `tests/chart/`) under `helm/`  
   **Rationale:** Minimizes churn; only the top-level directory name changes.

## Risks / Trade-offs

- **[Risk] Contributors follow old paths** → **Mitigation:** README table, grep-friendly rename, and tasks checklist for `template/` references.
- **[Risk] Helm version without library-chart support** → **Mitigation:** Document minimum Helm 3.x (library charts are standard in maintained Helm 3); CI uses whatever the repo already assumes.

## Migration Plan

1. Rename `template/` → `helm/` (git mv or equivalent).
2. Edit shared `Chart.yaml`: `type: library`; adjust `description` if it still says “deploy” as the primary action.
3. In `examples/hello-world`, update dependency `repository` to `file://../../helm/chart`, run `helm dependency update`, commit `Chart.lock`.
4. Replace `template/` string references across the project (README, ci.sh, comments, test docs).
5. Run existing chart CI (`ci.sh` or local `helm lint` / `helm template` on the example).

## Open Questions

- None for the scoped rename + library type; chart **name** (`hosted-agent`) and **version** stay as today unless a future change renames for OCI publishing.
