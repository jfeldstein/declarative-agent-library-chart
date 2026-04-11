## ADDED Requirements

### Requirement: Structured application logs to stdout

The agent process SHALL emit **structured logs** to **standard output** in **JSON** format (one JSON object per line) when running in the container image default configuration, including at minimum the fields: **`level`** (severity), **`message`** (human-readable summary), and **`service`** (static application identifier, e.g. `config-first-hosted-agents` or documented constant).

#### Scenario: Log line is machine-parseable

- **WHEN** the agent handles a request or startup event in production configuration
- **THEN** each corresponding log line written to stdout SHALL be a single JSON object containing `level`, `message`, and `service` keys with string values

### Requirement: Request correlation fields on trigger handling

For each **`POST /api/v1/trigger`** invocation, the structured log for that request SHALL include a **correlation identifier** field (for example **`request_id`** or **`trace_id`**) generated or propagated per request so centralized log systems can group related log lines.

#### Scenario: Two successive triggers have distinct correlation ids

- **WHEN** two `POST /api/v1/trigger` requests are processed sequentially
- **THEN** their primary request log records SHALL NOT reuse the same correlation identifier value across the two requests

### Requirement: Starter Grafana dashboard artifact

The repository SHALL include at least one **Grafana dashboard JSON** file (importable via Grafana UI or provisioning) that visualizes the **metrics** defined in the `cfha-agent-o11y-scrape` capability (for example request rate and latency panels tied to the documented metric names), and documentation SHALL state the **import path** and any **datasource** assumptions (for example a Prometheus datasource named `Prometheus`).

#### Scenario: Maintainer locates dashboard

- **WHEN** a maintainer follows the documentation for observability artifacts
- **THEN** they SHALL find a committed JSON dashboard file and instructions to import it into Grafana

### Requirement: Logging documentation for centralized pipelines

Project documentation (for example `README.md` or a short `docs/observability.md`) SHALL describe how **stdout JSON logs** map to common collectors (for example **Fluent Bit**, **Promtail**, **Vector**) at a high level—file paths or values snippets only as needed—so operators can ship logs to **Loki** or equivalent without reverse-engineering the container.

#### Scenario: Operator configures log shipping

- **WHEN** an operator reads the documented observability section
- **THEN** they SHALL understand that logs are JSON on stdout and which field names to use for severity and service labels in their pipeline
