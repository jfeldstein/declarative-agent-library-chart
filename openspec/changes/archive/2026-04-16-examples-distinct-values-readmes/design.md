## Context

The **library chart** is the product; **example application charts** exist to show how to wire it. For consumers, the **API is values-shaped**: the contract is what Helm values enable which rendered resources and runtime behavior. Strong **DX** here means: **one file per configuration you want people to adopt**, clear README guidance, and **helm-unittest** that proves templates do what that file claims—otherwise the library’s surface area is easy to misunderstand or break silently.

Example charts under `examples/<name>/` depend on `helm/chart`. Maintainers often use comments inside a single `values.yaml` to explain options, but that can mix **orthogonal stories** (for example multiple scraper job shapes, or observability toggles), which hurts copy-paste installs and review. **Helm Test File Consolidation** (`openspec/changes/consolidate-helm-tests/`) moves helm-unittest suites to `helm/tests/` and loads example values via `values:` paths; this change builds on that layout so each **documented** setup has its own file and explicit unittest cases.

## Goals / Non-Goals

**Goals:**

- Treat **values files as the primary integration surface** for the library: every **materially distinct** configuration we want users to learn from is **demonstrated in its own file**, not buried as a comment block in a mega-`values.yaml`.
- Split **materially distinct** user-facing setups into **separate committed values files** when an example is meant to demonstrate more than one.
- Document every such file in **`examples/<name>/README.md`**: what it shows, key fields, and how to install with it (`helm upgrade --install ... -f <file>` when not using default `values.yaml` alone).
- Ensure **`helm/tests/<suite>_test.yaml`** includes coverage **per documented values file** for examples that have multiple files (assertions match what the README promises for that file).
- Keep **test-to-spec traceability**: new or moved **SHALL** rows get IDs and matrix rows per `docs/AGENTS.md`.

**Non-Goals:**

- Changing the **library chart** API or default library `values.yaml` semantics.
- Mandating multiple values files for **hello-world** or any example that truly has a **single** story (the new requirements are cardinality-aware).
- Replacing **integration** tests (kind, PromQL) — only clarifying example layout + helm-unittest.

## Decisions

1. **When to split values files**  
   **Decision:** Apply split when the example README (or inline comments) would otherwise describe **multiple independent “use this if…”** paths (for example `with-scrapers`: jobs that enable RAG vs metrics-only stub vs disabled job list).  
   **Alternatives:** Keep one file with heavy comments only — rejected because it does not improve `helm install -f` ergonomics or unittest targeting.

2. **Naming**  
   **Decision:** Prefer **`values.yaml`** as the **default / primary** story; additional files use a clear prefix, e.g. **`values.<setup>.yaml`** (kebab-case setup slug), such as `values.stub-only.yaml`.  
   **Alternatives:** Only `values-*.yaml` — acceptable if team prefers hyphen; document the chosen pattern in `examples/README.md` once.

3. **Unittest mapping**  
   **Decision:** For each non-default values file, add a **`values:`** block in the suite under `helm/tests/` that points at `../examples/<dir>/<file>.yaml` (same relative pattern as consolidation), or duplicate inline values only when necessary for clarity. Each block gets at least one **`it:`** with assertions tied to that setup (and **`# [DALC-REQ-…]`** comments).

4. **Ordering vs `consolidate-helm-tests`**  
   **Decision:** Land **Helm Test File Consolidation** first; this change only adds/edits files under `examples/*/`, `helm/tests/`, specs, and `docs/spec-test-traceability.md` as needed.

## Risks / Trade-offs

- **[Risk] README drift** — Files renamed without updating README or tests. **Mitigation:** Checklist in `tasks.md`; CI fails if unittest references a missing path.
- **[Risk] Longer Helm CI** — More `it:` blocks per example. **Mitigation:** Keep assertions focused; share document snapshots where safe.
- **[Trade-off] More files to maintain** — Acceptable for examples that are documentation-first.

## Migration Plan

1. Apply **`consolidate-helm-tests`** and confirm CI green.
2. Per affected example: add split values files, update README, extend `helm/tests/` suite.
3. Promote OpenSpec deltas, update traceability matrix, run `python3 scripts/check_spec_traceability.py` and Helm job locally.

## Open Questions

- **Which examples split first:** Implementation should prioritize examples where **comments already describe** multiple modes (**with-scrapers** is a strong candidate). **with-observability** may stay single-file until a second setup is product-important.
- **Exact assertion per file:** Left to implementation — must match README claims (e.g. RAG absent vs present).
