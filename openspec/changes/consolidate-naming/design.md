## Context

The repo previously standardized chart naming to `declarative-agent-library` (see archived change `declarative-agent-library-chart`). The desired **product line** is **Declarative Agent Library Chart**, abbreviated **DALC** in dashboards and informal identifiers. The legacy image/repo name **`config-first-hosted-agents`** and Grafana file **`dalc-agent-overview.json`** still imply the old **CFHA** acronym.

## Goals / Non-Goals

**Goals:**

- Set the Helm library chart **`name`** to **`declarative-agent-library-chart`** and rename Helm **helper** prefixes (`declarative-agent-library.*` → `declarative-agent-library-chart.*`) consistently in `helm/chart`.
- Use **`agent`** as the **parent values key** in example charts via **`dependencies[].alias: agent`** while keeping **`dependencies[].name: declarative-agent-library-chart`** matching the packaged chart name.
- Replace deprecated **`config-first-hosted-agents`** with **`declarative-agent-library-chart`** for the default **`image.repository`** segment and for the runtime **`service`** / `SERVICE_NAME` constant where it represents the same product identifier.
- Ship **`grafana/dalc-overview.json`** (rename from `dalc-agent-overview.json`), update **`uid`/tags/titles** in the JSON to **dalc** where they denote the product, and refresh **`grafana/README.md`**.
- Grep and update **docs**, **scripts**, and **tests** that still reference old strings (including `declarative-agent-library` as a values key or release name fragment in examples).

**Non-Goals:**

- Renaming **`[DALC-REQ-…]`** requirement IDs or **`openspec/specs/dalc-*`** folder names (traceability and CI tooling assume stable IDs/paths).
- Changing **behavior** of the HTTP API, metrics **names**, or LangGraph checkpoints beyond identifier strings visible to operators.
- Renaming unrelated historical assets (e.g. patch filenames under `patches/`) unless needed for broken references—prefer leaving filenames and adding a one-line note.

## Decisions

1. **Chart `name`: `declarative-agent-library-chart`**  
   **Rationale:** Matches the user-facing “library chart” title and distinguishes the package from generic “declarative-agent-library” wording.  
   **Alternative:** Keep `declarative-agent-library` — less churn but diverges from requested naming.

2. **Parent key `agent` via `alias`, not nested `agent:` inside the library’s own `values.yaml`**  
   **Rationale:** Helm merges parent `agent:` into the subchart root; the library chart keeps flat keys (`image`, `service`, …) in `values.yaml`. Examples show `agent:\n  image: …`.  
   **Alternative:** Nested `agent` inside library values — would require `Values.agent.*` everywhere in templates; rejected.

3. **Rename all `declarative-agent-library` helper/template identifiers to `declarative-agent-library-chart`**  
   **Rationale:** `include` names must match the chart `name` convention used today (`define "<chart>.name"`).  
   **Trade-off:** Large diff; mitigated by mechanical search-replace and `helm unittest` / `ct lint`.

4. **DALC vs CFHA in user-visible strings**  
   **Rationale:** Replace **product** acronym **cfha** with **dalc** in Grafana and operator-facing scripts/docs. **Do not** rename OpenSpec **CFHA-** requirement IDs.

5. **Integration script identifiers (`job_name`, default cluster name)**  
   **Rationale:** Rename **cfha-**-prefixed **job** names and optional cluster/release names to **dalc-** for consistency when they are human-facing labels (update any assertions in tests that match those strings).

## Risks / Trade-offs

- **[Risk] Missed string in CI or docs** → **Mitigation:** `rg` for `config-first-hosted-agents`, `cfha-agent-overview`, `declarative-agent-library:` (values key), and old helper prefix; run **`python3 scripts/check_spec_traceability.py`** after matrix edits.
- **[Risk] Breaking downstream forks** → **Trade-off:** Document **BREAKING** in changelog/PR; migration: bump dependency name, add `alias: agent`, rename values key, retag images if they relied on old repository name.
- **[Risk] Grafana import UID change** → **Mitigation:** Note in README that existing imports may need re-import or UID update.

## Migration Plan

1. Rename chart and helpers; update `Chart.lock` in examples via `helm dependency update`.
2. Add `alias: agent` to example dependencies; move values under `agent:`.
3. Rename Grafana file and update README + observability docs + traceability matrix.
4. Update runtime constant and any OpenAPI title strings.
5. Run **helm unittest**, **pytest**, **`check_spec_traceability.py`**, and CI-equivalent scripts.

## Open Questions

- None for the naming itself; confirm with maintainers before a **future** change that re-prefixes OpenSpec IDs from **CFHA** to **DALC**.
