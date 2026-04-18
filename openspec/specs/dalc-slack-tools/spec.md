## ADDED Requirements

### Requirement: [DALC-REQ-SLACK-TOOLS-001] Slack tools operate during agent invocation and do not ingest tool I/O into managed RAG by default

Slack tools **SHALL** be invocable **only** during an active agent run (for example via **`run_tool_json`** while handling a trigger), and **SHALL NOT** automatically submit tool payloads or returned Slack message bodies to **`POST /v1/embed`** or the managed RAG index **unless** a separate capability explicitly enables that.

#### Scenario: Default configuration

- **WHEN** Slack tools are enabled with only the settings documented for interactive messaging
- **THEN** tool implementations **SHALL NOT** call **`POST /v1/embed`** for messages sent or read solely through Slack tools

### Requirement: [DALC-REQ-SLACK-TOOLS-002] Slack tools credentials are distinct from Slack scraper credentials

Slack tools **SHALL** load bot tokens and related secrets **only** from configuration keys and environment variables **documented as distinct** from the Slack scraper / **`scrapers`** CronJob configuration.

#### Scenario: Scraper and tools both enabled

- **WHEN** a Slack scraper job and Slack tools are enabled
- **THEN** each **SHALL** read Slack authorization material from **non-overlapping** documented settings (no single undocumented shared secret field required for both)

### Requirement: [DALC-REQ-SLACK-TOOLS-003] Agent can acknowledge and respond via reactions, posts, and updates

Slack tools **SHALL** include allowlisted operations so the agent can **add or remove reactions**, **post messages** (including **threaded replies** when channel id and thread timestamp are supplied), and **update** messages the bot previously posted.

#### Scenario: Reaction added

- **WHEN** the agent invokes the documented reaction tool with valid channel id, message timestamp, and reaction name
- **THEN** the system **SHALL** call the Slack Web API to add that reaction and **SHALL** return a structured success or error result without logging secrets

#### Scenario: Thread reply posted

- **WHEN** the agent invokes the documented post tool with valid channel id, text, and thread timestamp
- **THEN** the system **SHALL** call the Slack Web API to post in that thread and **SHALL** return structured identifiers (for example channel and message timestamp) on success

#### Scenario: Message updated

- **WHEN** the agent invokes the documented update tool with valid channel id, message timestamp, and new text
- **THEN** the system **SHALL** call the Slack Web API to update that message and **SHALL** return structured metadata including the updated timestamp when Slack provides it

### Requirement: [DALC-REQ-SLACK-TOOLS-004] Agent can fetch bounded channel or thread history

Slack tools **SHALL** provide a documented read tool (or tools) that returns **recent messages** for a **channel** or **thread**, bounded by documented limits (maximum message count and/or time window).

#### Scenario: Thread history fetched

- **WHEN** the agent requests thread history for a valid channel and thread root timestamp within documented limits
- **THEN** the system **SHALL** return normalized message records including timestamps and user identifiers as available from Slack, and the response **SHALL NOT** include raw bearer tokens

### Requirement: [DALC-REQ-SLACK-TOOLS-005] Slack Web API access uses slack_sdk consistent with other Slack integrations

Slack tools **SHALL** perform Slack Web API calls using **`slack_sdk`** consistent with repository dependency policy, and **SHALL NOT** rely on undocumented private Slack HTTP endpoints.

#### Scenario: Dependency present

- **WHEN** the runtime image is built for a release that includes Slack tools
- **THEN** package metadata **SHALL** declare **`slack_sdk`** with version constraints consistent with repository policy

### Requirement: [DALC-REQ-SLACK-TOOLS-006] Secrets are never written to logs or metrics labels on the tools path

Slack tools **SHALL NOT** print bot tokens or user tokens to stdout/stderr, and **SHALL NOT** attach those values to Prometheus metric labels.

#### Scenario: Slack API error

- **WHEN** a Slack Web API call fails with an authorization or permission error
- **THEN** logs **SHALL** redact or omit secret material while still recording a safe correlation identifier such as **request id** or **Slack request id** when available
