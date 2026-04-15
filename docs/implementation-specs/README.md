# Implementation specs (downstream LLM handoffs)

This directory holds per-step `-spec.md` files aligned with `docs/openspec-implementation-order.md`. When editing them, keep claims consistent with **this repository’s layout** unless a paragraph is explicitly labeled **Target (after step N)**.

## Canonical commands

**Python (pytest)** — the uv project lives under `helm/src/`:

```bash
uv sync --all-groups --project helm/src
cd helm/src && uv run pytest tests/ -v --tb=short
```

Single-file example:

```bash
cd helm/src && uv run pytest tests/test_jira_job.py -v --tb=short
```

**Helm unittest** — run from an **application** chart under `examples/<name>/` after dependencies are built; the suite file lives under `helm/tests/`:

```bash
(cd examples/with-scrapers && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/with_scrapers_test.yaml" .)
```

CI loops `examples/*/` with `suite="${chart//-/_}_test.yaml"` and the same `-f "../../helm/tests/${suite}"` pattern.

**Spec–test traceability** — from the repository root:

```bash
python3 scripts/check_spec_traceability.py
```

## Vendored subchart path in `helm unittest` `template:` keys

After `helm dependency build` in an example chart, Helm unpacks the library dependency under **`charts/declarative-agent-library/`** (see `helm/chart/Chart.yaml` `name`). In unittest suites, reference templates as:

`charts/declarative-agent-library/templates/<file>.yaml`

If OpenSpec **consolidate-naming** renames the chart `name`, update suites and this README in the same change.

## Grafana dashboard filenames

The committed starter dashboard is **`grafana/dalc-agent-overview.json`** until **consolidate-naming** lands the `dalc-overview.json` rename. Specs that mention `dalc-overview.json` should mark that as **target** state unless the file exists on disk.

## Target vs “today”

Do not describe the repository as **today** when meaning **after a prior checklist step**. Use explicit labels:

- **As of this repo (main):** …
- **Target (after step N):** …
