## Context

The shared Helm package for the config-first hosted agents prototype is identified in charts and docs as **`hosted-agent`** with descriptions that emphasize “config-first” or “template chart.” The product direction is to standardize on **declarative** language and a clear library title: **Declarative Agent Library Chart**, with a Helm chart **`name`** that matches (`declarative-agent-library`).

## Goals / Non-Goals

**Goals:**

- Set human-facing descriptions (and README/spec language) to the Declarative Agent Library Chart positioning.
- Rename the library chart’s Helm **`name`** to `declarative-agent-library` and update every in-repo consumer (`dependencies`, values nesting, generated release names where documented).

**Non-Goals:**

- Changing runtime behavior, HTTP contract, image names, or Kubernetes resource naming conventions beyond what Helm derives from the chart name (if any).
- Publishing to an OCI/HTTP chart repo (still `file://` where used today).
- Renaming the example application chart `hello-world` or changing acceptance ports/curl steps.

## Decisions

1. **Technical chart `name`: `declarative-agent-library`**  
   **Rationale:** Helm chart names are lowercase kebab-case identifiers; “Chart” belongs in prose (`description`, docs), not necessarily in the `name` field.  
   **Alternative considered:** Keep `name: hosted-agent` and only change descriptions — less churn but leaves two vocabularies (“hosted-agent” vs “Declarative Agent Library”).

2. **`description` references “Declarative Agent Library Chart”**  
   **Rationale:** Operators reading `helm show chart` or the registry UI (future) see the full title.  
   **Alternative considered:** Shorter “Declarative agent library” only — acceptable in body text but weaker as a single product line.

3. **Parent chart values move under `declarative-agent-library:`**  
   **Rationale:** Helm nests subchart values by dependency `name`; renaming the dependency renames the values key. Example and docs must show the new key.  
   **Alternative considered:** Alias tricks to keep old key — adds complexity; rejected for this change.

4. **Grep-driven migration**  
   **Rationale:** After `git mv` is unnecessary for this change (paths may already be `helm/` from a sibling change), the main work is string and metadata updates; tasks should include searching `hosted-agent` in the CFHA project tree.

## Risks / Trade-offs

- **[Risk] Missed references** → **Mitigation:** `rg 'hosted-agent'` across `this repository` and OpenSpec change specs; CI `helm lint` / `helm template` on the example chart.
- **[Trade-off] Breaking all existing values.yaml** that nested under `hosted-agent:` → Accepted as part of explicit rename.

## Migration Plan

1. Edit library `Chart.yaml`: `name: declarative-agent-library`, update `description` to Declarative Agent Library Chart wording.
2. In each application chart that depends on the library: set `dependencies[].name: declarative-agent-library`, run `helm dependency update`, commit `Chart.lock`.
3. Rename values keys from `hosted-agent:` to `declarative-agent-library:` (and any documentation snippets).
4. Update README, comments, and OpenSpec text; verify with `helm lint` and `helm template` on the example.

## Open Questions

- None.
