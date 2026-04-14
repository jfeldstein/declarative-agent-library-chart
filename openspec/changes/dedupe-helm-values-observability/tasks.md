## 1. Helm chart values and templates

- [ ] 1.1 Rename **`o11y`** to **`observability`** in `helm/chart/values.yaml` and all templates (`deployment`, `service`, `servicemonitor`, `rag-*`, `scraper-cronjobs`).
- [ ] 1.2 Replace the old mixed **`observability`** block with top-level **`checkpoints`** and **`wandb`**; move Slack feedback and feedback label registry under **`scrapers.slack.feedback`** (including `postgresUrl` under **`checkpoints`**).
- [ ] 1.3 Remove **`atifExport`**, **`shadow`**, and related template branches; drop **`shadow-allow-tenants.json`** from ConfigMap when shadow is removed.
- [ ] 1.4 Update **`helm/chart/values.schema.json`** to match the new shape and remove deleted keys.

## 2. Examples and tests

- [ ] 2.1 Update **`examples/with-observability`** (and any other examples) to use the new keys; refresh **`tests/*.yaml`** assertions.
- [ ] 2.2 Update **`helm/tests/chart`** if present; run **`helm unittest`** for affected charts.
- [ ] 2.3 Run **`ct lint`** / chart-testing if part of CI.

## 3. Runtime and removal of ATIF / shadow

- [ ] 3.1 Remove or stub **ATIF export** and **shadow** code paths (`atif`, `shadow`, `export_atif_batch`, trigger graph branches, W&B trace shadow tags if solely for shadow).
- [ ] 3.2 Simplify **`ObservabilitySettings`** (or rename per design) and **`app.py`** payloads that expose `shadow_*` / ATIF flags.
- [ ] 3.3 Delete or rewrite tests that only covered removed features; run **`uv run pytest`** for `runtime/tests`.

## 4. Documentation and spec traceability

- [ ] 4.1 Update **`docs/runbook-checkpointing-wandb.md`**, **`docs/observability.md`**, chart README, and any scripts referencing old value keys.
- [ ] 4.2 Document **`labelRegistry`**: feedback label taxonomy for **`HOSTED_AGENT_LABEL_REGISTRY_JSON`**, relocated under **`scrapers.slack.feedback`**.
- [ ] 4.3 Update **`docs/spec-test-traceability.md`** and test comments for new or changed **`[DALC-REQ-*]`** IDs; run **`python3 scripts/check_spec_traceability.py`**.

## 5. OpenSpec promotion (at apply/archive)

- [ ] 5.1 Merge delta specs into **`openspec/specs/`** when implementing or archiving; ensure IDs on promoted **`### Requirement:`** lines match **`dalc-requirement-verification`**.
