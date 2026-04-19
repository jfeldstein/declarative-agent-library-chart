# Tasks: observability-plugin-log-shipping

- [x] Promote **`openspec/specs/dalc-plugin-log-shipping/spec.md`** with **`[DALC-REQ-PLUGIN-LOG-SHIPPING-001]`** … **`003`**.
- [x] Wire **`HOSTED_AGENT_LOG_FORMAT=json`** from **`plugins.logShipping.enabled`** in **`helm/chart/templates/_manifest_deployment.tpl`**.
- [x] Extend **`values.yaml`** / **`values.schema.json`** for **`logShipping`**.
- [x] Expand **`docs/observability.md`** (Fluent Bit / Promtail / Vector examples; traceability for **003**).
- [x] **`helm/tests/hello_world_test.yaml`** for **001**; **`helm/src/tests/test_chart_values_contract.py`** for **002**.
- [x] Update **`docs/spec-test-traceability.md`**; run **`uv run pytest`** (helm/src) and **`python3 scripts/check_spec_traceability.py`**.
