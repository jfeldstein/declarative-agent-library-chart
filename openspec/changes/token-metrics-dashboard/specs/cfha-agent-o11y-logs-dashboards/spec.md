## ADDED Requirements

### Requirement: [CFHA-REQ-O11Y-LOGS-005] Grafana dashboard for token and cost metrics

The repository SHALL include at least one **additional** Grafana dashboard JSON file (distinct path from existing starter dashboards or an explicitly versioned replacement documented in **`grafana/README.md`**) whose panels query the **Prometheus** metrics defined under **`cfha-runtime-token-metrics`**, including at minimum: **output token rate**, **time-to-first-token** (p50/p95), **request/response payload size** distribution, and **estimated cost** rate or cumulative panel with clear panel title indicating **estimate**.

#### Scenario: Maintainer finds token dashboard

- **WHEN** a maintainer reads **`grafana/README.md`**
- **THEN** they SHALL find the import path for the token metrics dashboard JSON and the **Prometheus** datasource assumption consistent with **[CFHA-REQ-O11Y-LOGS-003]**

#### Scenario: Dashboard uses documented metric names

- **WHEN** an operator imports the dashboard into Grafana with a working **Prometheus** datasource
- **THEN** each panel’s PromQL SHALL reference only metric names documented for **`cfha-runtime-token-metrics`** (no placeholder fake series)
