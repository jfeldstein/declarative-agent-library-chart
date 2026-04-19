# Spec ↔ code validation: Helm unittest, packaging, example values, Python complexity CI, Slack tools/trigger

**Repo segment:** Helm packaging/unittest, example values conventions, Python complexity gates, Slack tools and Slack trigger.  
**Sources:** promoted specs under `openspec/specs/<slug>/spec.md`, authoritative matrix rows in `docs/spec-test-traceability.md`.  
**Worktree:** validated in this clone at authoring time (`wt/agent-k5m7`).  
**Checks performed:** All evidence paths listed in the matrix for these capabilities were verified to exist on disk. Representative requirements were spot-checked against SHALL text, Helm unittest YAML, pytest docstrings/comments, CI, and chart values/schema.

---

## Verification commands (evidence)

- `python3 scripts/check_spec_traceability.py` — exit 0 (83 promoted requirements, strict matrix aligned).
- `uv run pytest tests/` from `helm/src/` — **200 passed**, coverage gate satisfied (≥85%).

---

## `dalc-helm-unittest`

| ID | Evidence paths exist | Spot-check vs SHALL |
| --- | --- | --- |
| [DALC-REQ-HELM-UNITTEST-001] | Yes (`helm/tests/*`, `examples/with-observability/values-observability-no-rag.yaml`, `ci.yml`) | `helm/tests/hello_world_test.yaml` exercises no CronJob/RAG baseline; `with_scrapers_test.yaml` asserts CronJobs + `app.kubernetes.io/component: rag`; `with_observability_test.yaml` asserts scrape annotations and `ServiceMonitor` documents for agent + optional RAG, plus **no** RAG `ServiceMonitor` when using `values-observability-no-rag.yaml`. Matches scenario intent. CI runs `helm unittest -f ../../helm/tests/${suite}` per `examples/*/`. |
| [DALC-REQ-HELM-UNITTEST-002] | Yes (`hello_world_test.yaml`, `checkpointing_test.yaml`, `ct.yaml`, `ci.yml`) | Library chart behaviors are exercised via example parent charts; `ct lint --config ct.yaml --all` follows unittest in CI. Aligns with “unittest or ct lint without weakening thresholds.” |
| [DALC-REQ-HELM-UNITTEST-003] | Paths exist (`ci.yml`, `README.md`) | **GAP (traceability granularity):** `.github/workflows/ci.yml` documents the official plugin URL via `helm plugin install https://github.com/helm-unittest/helm-unittest.git`. Root `README.md` carries a traceability banner for this ID but **does not** spell out `helm plugin install …`; **`docs/local-ci.md`** repeats pinned Helm/`ct`/helm-unittest parity (including unittest invocation) but is **not** listed as matrix evidence for this row. Satisfies SHALL via CI + parity doc; listing `README.md` alone oversells that file’s install-step content. |
| [DALC-REQ-HELM-UNITTEST-004] | Yes (`with_scrapers_test.yaml`, `examples/with-scrapers/README.md`) | README indexes `values.yaml`, `values.jira-only.yaml`, `values.slack-only.yaml`. Suite loads default `values:` plus per-`it:` overrides for **jira-only** and **slack-only** setups with assertions matching distinct workload counts. Matches SHALL. |

---

## `dalc-library-chart-packaging`

| ID | Evidence paths exist | Spot-check vs SHALL |
| --- | --- | --- |
| [DALC-REQ-DALC-PKG-001] | Yes (`helm/chart/Chart.yaml`, `helm/src/tests/test_chart_values_contract.py::test_library_chart_name_is_dalc_packaging`) | `Chart.yaml` `name: declarative-agent-library-chart`; pytest asserts same. |
| [DALC-REQ-DALC-PKG-002] | Yes (`examples/hello-world/Chart.yaml`, `examples/hello-world/values.yaml`, `helm/tests/hello_world_test.yaml`) | Dependency uses `alias: agent`; values nest under `agent:`; unittest + contract test enforce alias and forbidden deprecated top-level keys. |
| [DALC-REQ-DALC-PKG-003] | Yes (`helm/chart/values.yaml`, `test_chart_values_contract.py::test_library_image_repository_default_is_dalc_packaging`) | Default `image.repository` is `declarative-agent-library-chart`. |

---

## `dalc-example-values-files`

| ID | Evidence paths exist | Spot-check vs SHALL |
| --- | --- | --- |
| [DALC-REQ-EXAMPLE-VALUES-FILES-001] | Yes (`examples/with-scrapers/README.md`, `with_scrapers_test.yaml`) | Multi-setup example documents one file per distinct setup with purpose table; unittest covers each committed file. |
| [DALC-REQ-EXAMPLE-VALUES-FILES-002] | Yes (`examples/with-scrapers/README.md`) | README marks **`values.yaml`** as default quick start and documents `-f values.jira-only.yaml` / `values.slack-only.yaml` for non-default installs. |

---

## `dalc-python-complexity-ci`

| ID | Evidence paths exist | Spot-check vs SHALL |
| --- | --- | --- |
| [DALC-REQ-PYTHON-COMPLEXITY-CI-001] | Yes (`helm/src/pyproject.toml`, `test_python_complexity_ci_contract.py::test_ruff_config_enables_c901_with_mccabe_cap`, `ci.yml`) | `extend-select` includes `C901`; `[tool.ruff.lint.mccabe] max-complexity = 10`. CI runs `uv run ruff check hosted_agents tests`. |
| [DALC-REQ-PYTHON-COMPLEXITY-CI-002] | Yes (`pyproject.toml`, `test_python_complexity_ci_contract.py::test_complexipy_config_targets_package_paths`, `ci.yml`) | `[tool.complexipy]` sets `paths` including `hosted_agents` and `tests`, `max-complexity-allowed = 15`. CI runs `uv run complexipy`. |

---

## `dalc-slack-tools`

| ID | Evidence paths exist | Spot-check vs SHALL |
| --- | --- | --- |
| [DALC-REQ-SLACK-TOOLS-001] | Yes (`test_slack_tools_impl.py` tests cited in matrix) | Tests guard against importing embed client and cover simulated paths without HTTP. **Residual gap:** SHALL “invocable only during an active agent run” is not isolated as a single pytest; largely enforced by tool wiring/dispatch rather than this file alone. |
| [DALC-REQ-SLACK-TOOLS-002] | Yes (`hello_world_test.yaml`, `helm/chart/values.yaml`) | Unittest explicitly wires `HOSTED_AGENT_SLACK_TOOLS_*` vs scraper/env paths (`scrapers.slack.feedback` separate); distinct Helm surface area. |
| [DALC-REQ-SLACK-TOOLS-003] | Yes (pytest entries in matrix) | Docstrings cite `[DALC-REQ-SLACK-TOOLS-003]` for reactions/posts/updates with mocked Slack client. |
| [DALC-REQ-SLACK-TOOLS-004] | Yes (pytest entries in matrix) | History/simulated + real-path coverage cited. |
| [DALC-REQ-SLACK-TOOLS-005] | Yes (`helm/src/pyproject.toml`) | Declares `slack-sdk` dependency with comment tying to this requirement. |
| [DALC-REQ-SLACK-TOOLS-006] | Yes (`test_slack_tools_impl.py`, `hosted_agents/metrics.py`) | Tests cover redaction/safe headers; metrics module cited for label hygiene. |

---

## `dalc-slack-trigger`

| ID | Evidence paths exist | Spot-check vs SHALL |
| --- | --- | --- |
| [DALC-REQ-SLACK-TRIGGER-001] | Yes (`test_slack_trigger.py` entries) | Tests cover `app_mention` → trigger pipeline and dedupe by `event_id`. |
| [DALC-REQ-SLACK-TRIGGER-002] | Yes (`test_slack_trigger.py`) | Test documents no embed/RAG ingestion on trigger bridge path. |
| [DALC-REQ-SLACK-TRIGGER-003] | Yes (`test_slack_trigger.py`) | Bad signature and URL verification cases avoid `run_trigger_graph`. |
| [DALC-REQ-SLACK-TRIGGER-004] | Yes (`hello_world_test.yaml`, `values.yaml`, `values.schema.json`) | Helm unittest sets distinct `slackTrigger.*` secret refs (`HOSTED_AGENT_SLACK_TRIGGER_*`); schema describes `slackTrigger` separately from scrapers/`slackTools` ([DALC-REQ-SLACK-TRIGGER-004] in description). |
| [DALC-REQ-SLACK-TRIGGER-005] | Yes (`test_slack_trigger.py`, `metrics.py`) | Tests assert Prometheus labels are fixed strings; aligns with “no secrets in metric labels.” |

---

## GAP summary (actionable)

1. **[DALC-REQ-HELM-UNITTEST-003] matrix vs README:** Root `README.md` is listed as evidence but does not contain the canonical `helm plugin install …` line; **`docs/local-ci.md`** does, alongside **`ci.yml`**. Consider aligning the matrix evidence list with files that actually carry the install instruction, or add a short README subsection pointing at the official install URL (mirror `ci.yml`).

2. **[DALC-REQ-SLACK-TOOLS-001] lifecycle SHALL:** Automated tests strongly evidence “no embed by default” and safe simulation; explicit proof that tools **cannot** run outside an active agent invocation is thinner (would live in dispatch/runtime integration if tightened).

---

## Sign-off

Promoted specs in this segment match the repository as of validation: filesystem evidence complete, Helm unittest + pytest citations align with SHALL scenarios for all listed IDs except the documentation nuance noted for **[DALC-REQ-HELM-UNITTEST-003]** / `README.md`, and the optional tightening note for **[DALC-REQ-SLACK-TOOLS-001]** runtime scoping.
