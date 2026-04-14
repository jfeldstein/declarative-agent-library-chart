## 1. Promoted spec folders and requirement text

- [x] 1.1 `git mv` each `openspec/specs/cfha-*` directory to `openspec/specs/dalc-*` per the mapping in `design.md`
- [x] 1.2 Apply delta content: ensure each `openspec/specs/dalc-*/spec.md` matches the **MODIFIED** blocks in this change (IDs **`DALC-REQ-*`** / **`DALC-VER-*`**, updated cross-references such as **`dalc-agent-o11y-scrape`** in logs-dashboards)
- [x] 1.3 Preserve each file’s **Reader note** / non-normative preamble where present; update any **CFHA** mentions in prose to **DALC** where appropriate

## 2. Traceability checker and CI

- [x] 2.1 Update `scripts/check_spec_traceability.py`: docstring, **`ID_PATTERN`**, matrix row regex, comments, and traceability self-reference (e.g. `[DALC-VER-001]`) to accept only **`DALC-`** IDs (or document a temporary dual pattern if maintainers choose a phased cutover)
- [x] 2.2 Rename **`CFHA_TRACEABILITY_STRICT`** to **`DALC_TRACEABILITY_STRICT`** or implement deprecated alias with warning per `design.md` open question
- [x] 2.3 Update `.github/workflows/*.yml`, `ct.yaml`, `README.md`, and any CI comments that reference **`CFHA-`** IDs or `openspec/specs/cfha-` paths

## 3. Matrix, ADRs, and contributor docs

- [x] 3.1 Rewrite **`docs/spec-test-traceability.md`**: **ID** column and **Spec** paths (`dalc-*/spec.md`); keep evidence paths accurate
- [x] 3.2 Update **`docs/adrs/0003-spec-test-traceability.md`**, **`AGENTS.md`**, **`docs/AGENTS.md`**, **`.cursor/rules/spec-traceability.mdc`** (or equivalent) for **`DALC-REQ`** / **`DALC-VER`** and DALC spec paths
- [x] 3.3 Update **`helm/chart/values.schema.json`** title comment and any schema lines that cite **`CFHA-REQ`**

## 4. Tests and examples

- [x] 4.1 Update **pytest** docstrings and **`runtime/tests/**`** files that embed **`CFHA-REQ`** / **`CFHA-VER`**
- [x] 4.2 Update **`examples/*/tests/*.yaml`** Helm unittest **`#`** comments and traceability headers
- [x] 4.3 Update **`grafana/*.json`** or docs only if they embed a requirement ID string (unusual but grep-driven)

## 5. Active OpenSpec changes and repo-wide sweep

- [x] 5.1 `rg` from repo root: **`CFHA-REQ`**, **`CFHA-VER`**, **`openspec/specs/cfha-`**, **`cfha-requirement-verification`** path references; fix hits in **active** `openspec/changes/*` (skip or batch-update **archive** per proposal)
- [x] 5.2 Run **`python3 scripts/check_spec_traceability.py`** until exit **0**
- [x] 5.3 Run **`uv run pytest`** (runtime), **`helm unittest`**, **`ct lint`** as in CI; fix failures

## 6. Close-out

- [x] 6.1 Add a short entry to **`docs/development-log.md`** describing the migration and **BREAKING** ID/path churn for forks
- [x] 6.2 When promoting this change to `openspec/specs/` on disk, archive per project workflow and confirm no duplicate **`cfha-*`** promoted folders remain
