## Context

The **declarative-agent-library** chart is the center of the repo; **examples/** are the primary **values-file-driven** API for integrators. Maintainers SHOULD treat **example + unittest** as the contract for library capabilities: new or changed Helm behavior should show up in an appropriate example and gain or extend **helm-unittest** assertions so template output stays aligned with documented `values`.

Today each example application chart under `examples/<name>/` may include `tests/<name>_test.yaml` (with underscores in the filename, e.g. `hello_world_test.yaml` for `hello-world`). CI runs `helm dependency build` then `helm unittest .` from that chart directory, so the plugin loads `tests/*_test.yaml` next to `Chart.yaml`. Template paths inside suites (for example `charts/declarative-agent-library/templates/deployment.yaml`) are resolved relative to the **example chart** being tested.

The library chart at `helm/chart/` already uses `templates/tests/` for `helm test` hook Jobs—distinct from **helm-unittest** YAML.

## Goals / Non-Goals

**Goals:**

- Reinforce the repo norm: **values-driven DX** → **examples demonstrate components** → **each example has a strong helm-unittest suite** (centralized under `helm/tests/` after this change).
- Single directory `helm/tests/` holding one `*_test.yaml` per example that today has helm-unittest coverage, each file declaring `values:` entries that load **`../examples/<example-dir>/values.yaml`** (paths relative to the suite file under `helm/tests/`).
- Keep each example directory as the home for **`values.yaml`**, **`Chart.yaml`**, and **`Chart.lock`** only (no per-example `tests/` trees for helm-unittest).
- CI and contributor docs invoke **`helm unittest -f <repo-relative path> .`** from inside each example chart after `helm dependency build`, so rendering context remains the example chart (subchart in `charts/`).
- Discoverable documentation at **`examples/AGENTS.md`**, **`helm/tests/AGENTS.md`**, and **`examples/README.md`** describing the contract for future changes.

**Non-Goals:**

- Moving or merging **`helm/chart/templates/tests/`** (install-time `helm test` hooks).
- Changing assertion semantics or traceability IDs inside suites beyond path/header edits required for relocation.
- Adding new example charts or new unittest scenarios (only relocate and wire CI/docs/specs).

## Decisions

1. **Central location: `helm/tests/*.yaml`**  
   Rationale: groups “Helm-side automated checks that are not the library chart itself” next to `helm/chart/`; avoids scattering unittest YAML across four example trees.

2. **Use `helm unittest -f` from each example chart directory**  
   Rationale: [helm-unittest](https://github.com/helm-unittest/helm-unittest) supports `helm unittest -f 'glob' CHART`. The chart argument stays `examples/<name>` (current working directory `.` after `cd`), so `template:` paths in suites stay unchanged.  
   Filename convention: **`${chart//-/_}_test.yaml`** where `chart` is the directory basename (`hello-world` → `hello_world_test.yaml`), matching existing filenames.

3. **`values:` paths relative to the suite file**  
   Each suite lives at `helm/tests/<suite>_test.yaml` and lists:

   ```yaml
   values:
     - ../examples/<example-dir>/values.yaml
   ```

   From `helm/tests/`, `../examples/...` resolves to the repository’s `examples/` tree. This matches the user requirement and avoids duplicating values inside the suite.

4. **`examples/AGENTS.md` supersedes `examples/AGENT.md`**  
   Rationale: user asked for discoverable **`AGENTS.md`** (plural, consistent with repo **`AGENTS.md`** / **`docs/AGENTS.md`**). Migrate content from **`examples/AGENT.md`**, update **`examples/README.md`** link, remove **`examples/AGENT.md`** to avoid two sources of truth.

## Risks / Trade-offs

- **[Risk] Wrong `-f` mapping breaks CI** → Mitigation: keep a single naming rule documented in **`helm/tests/AGENTS.md`** and assert in CI loop with `basename` + bash parameter expansion; run full Helm job locally before merge.
- **[Risk] `values:` path resolution differs by helm-unittest version** → Mitigation: pin remains **v1.0.3** in CI; verify with `helm unittest -f …` from an example directory after the move.
- **[Trade-off] Suites are no longer co-located with the example** → Mitigation: README + AGENTS files and matrix evidence paths explicitly point to **`helm/tests/`**; adding an example requires registering a suite file and CI `-f` (documented).

## Migration Plan

1. Add `helm/tests/<suite>_test.yaml` with `values:` blocks and copy existing test bodies.
2. Delete `examples/*/tests/` files (and directories).
3. Update `.github/workflows/ci.yml` Helm step to pass `-f "../../helm/tests/<derived-name>_test.yaml"` only when that file exists (or maintain explicit list—prefer derived rule + doc).
4. Update **`docs/spec-test-traceability.md`** (and **`.cursor/rules/spec-traceability.mdc`**, **`docs/AGENTS.md`** if they mention `examples/*/tests/`) plus promoted spec deltas in this change.
5. Run `helm unittest` per example and `python3 scripts/check_spec_traceability.py`.

## Open Questions

- None for the propose phase; if `checkpointing` (or any example) lacks a matrix row today, implementation should add evidence paths when those IDs appear in the suite header (grep matrix vs suite traceability comments during apply).
