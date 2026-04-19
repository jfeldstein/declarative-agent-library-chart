## Tasks

- [x] Regenerate Grafana JSON under `grafana/` for `dalc_*` PromQL.
- [x] Sync **`helm/chart/files/grafana/`** vendored copies for Helm packaging.
- [x] Implement **`manifest.grafanaDashboards`** template + **`systemBundled`** wiring.
- [x] Extend **`helm/tests/hello_world_test.yaml`** for optional ConfigMap.
- [x] Update **`grafana/README.md`**, **`docs/observability.md`**, **ADR 0011**, promoted specs as needed.
- [x] Run **`uv run pytest`** (`helm/src`) and Helm unittest examples loop; **`python3 scripts/check_spec_traceability.py`**.
