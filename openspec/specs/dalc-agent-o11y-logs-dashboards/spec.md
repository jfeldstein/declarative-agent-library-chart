## ADDED Requirements

### Requirement: [DALC-REQ-O11Y-LOGS-001] Structured application logs to stdout

The agent process SHALL emit **structured logs** to **standard output** in **JSON** format (one JSON object per line) when running in the container image default configuration, including at minimum the fields: **`level`** (severity), **`message`** (human-readable summary), and **`service`** (static application identifier, e.g. `declarative-agent-library-chart` or documented constant).

#### Scenario: Log line is machine-parseable

- **WHEN** the agent handles a request or startup event in production configuration
- **THEN** each corresponding log line written to stdout SHALL be a single JSON object containing `level`, `message`, and `service` keys with string values

### Requirement: [DALC-REQ-O11Y-LOGS-002] Request correlation fields on trigger handling

For each **`POST /api/v1/trigger`** invocation, the structured log for that request SHALL include a **correlation identifier** field (for example **`request_id`** or **`trace_id`**) generated or propagated per request so centralized log systems can group related log lines.

#### Scenario: Two successive triggers have distinct correlation ids

- **WHEN** two `POST /api/v1/trigger` requests are processed sequentially
- **THEN** their primary request log records SHALL NOT reuse the same correlation identifier value across the two requests

### Requirement: [DALC-REQ-O11Y-LOGS-003] Starter Grafana dashboard artifact

The repository SHALL include at least one **Grafana dashboard JSON** file (importable via Grafana UI or provisioning) that visualizes the **metrics** defined in the `dalc-agent-o11y-scrape` capability (for example request rate and latency panels tied to the documented metric names), and documentation SHALL state the **import path** and any **datasource** assumptions (for example a Prometheus datasource named `Prometheus`). **Panels or grouped sections that apply only when an optional chart component is deployed** (for example RAG HTTP metrics) SHALL be **visually or logically optional** so operators who deploy **only** the agent are not presented with dashboard sections that imply an always-on second target—using a mechanism documented in `grafana/README.md` (for example dashboard variables, repeated rows, or clearly separated sections with titles stating the dependency).

#### Scenario: Maintainer locates dashboard

- **WHEN** a maintainer follows the documentation for observability artifacts
- **THEN** they SHALL find a committed JSON dashboard file and instructions to import it into Grafana

#### Scenario: Operator without an optional metrics service sees agent-focused defaults

- **WHEN** an operator imports the starter dashboard for a deployment that does not include an optional metrics **`Service`** (for example no managed RAG)
- **THEN** the default view SHALL remain usable for agent metrics **without** implying failing queries for absent optional components, per the documented optional-section behavior

### Requirement: [DALC-REQ-O11Y-LOGS-005] Grafana README describes scrape targets generically

The Grafana documentation (`grafana/README.md` or documented successor) SHALL describe how to ensure **Prometheus scrapes every metrics endpoint the chart exposes for enabled components** (for example matching rendered `ServiceMonitor` resources or equivalent static scrape jobs). It SHALL **not** state a fixed number of targets that implies a specific optional component is always deployed (for example “scrape **both** targets” as if RAG were mandatory). It MAY reference example values files and **list** example optional services when they are enabled.

#### Scenario: Operator reads scrape instructions for agent-only

- **WHEN** an operator reads `grafana/README.md` to connect Prometheus to the chart
- **THEN** they SHALL understand how to scrape the agent and **how additional scrape targets appear when optional chart components are enabled**, without documentation that incorrectly assumes an optional component is always present

### Requirement: [DALC-REQ-O11Y-LOGS-004] Logging documentation for centralized pipelines

Project documentation (for example `README.md` or a short `docs/observability.md`) SHALL describe how **stdout JSON logs** map to common collectors (for example **Fluent Bit**, **Promtail**, **Vector**) at a high level—file paths or values snippets only as needed—so operators can ship logs to **Loki** or equivalent without reverse-engineering the container.

#### Scenario: Operator configures log shipping

- **WHEN** an operator reads the documented observability section
- **THEN** they SHALL understand that logs are JSON on stdout and which field names to use for severity and service labels in their pipeline
