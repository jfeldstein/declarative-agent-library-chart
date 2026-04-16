## MODIFIED Requirements

### Requirement: [DALC-REQ-O11Y-LOGS-001] Structured application logs to stdout

The agent process SHALL emit **structured logs** to **standard output** in **JSON** format (one JSON object per line) when running in the container image default configuration, including at minimum the fields: **`level`** (severity), **`message`** (human-readable summary), and **`service`** (static application identifier, e.g. `declarative-agent-library-chart` or documented constant).

#### Scenario: Log line is machine-parseable

- **WHEN** the agent handles a request or startup event in production configuration
- **THEN** each corresponding log line written to stdout SHALL be a single JSON object containing `level`, `message`, and `service` keys with string values

### Requirement: [DALC-REQ-O11Y-LOGS-003] Starter Grafana dashboard artifact

The repository SHALL include **`grafana/dalc-overview.json`** (importable via Grafana UI or provisioning) that visualizes the **metrics** defined in the `dalc-agent-o11y-scrape` capability (for example request rate and latency panels tied to the documented metric names), and documentation SHALL state the **import path** and any **datasource** assumptions (for example a Prometheus datasource named `Prometheus`).

#### Scenario: Maintainer locates dashboard

- **WHEN** a maintainer follows the documentation for observability artifacts
- **THEN** they SHALL find a committed JSON dashboard file and instructions to import it into Grafana
