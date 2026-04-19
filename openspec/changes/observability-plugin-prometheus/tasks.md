## Tasks

- [x] Implement `agent.observability.plugins.prometheus` (`dalc_*` metrics + bus wiring).
- [x] Gate `/metrics` (agent + RAG) and scraper metrics HTTP listener on plugin toggle.
- [x] Helm: env + scrape annotation / ServiceMonitor conditions.
- [x] Update promoted specs + traceability matrix + dashboards/docs.
- [x] Run `cd helm/src && uv run pytest` and `python3 scripts/check_spec_traceability.py`.
