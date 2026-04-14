## ADDED Requirements

### Requirement: [CFHA-REQ-SLACK-TRIGGER-001] App mention events start a hosted agent trigger run

The Slack trigger integration **SHALL** accept Slack **`app_mention`** events for the installed bot and **SHALL** forward each such event into the hosted agent **trigger pipeline** with the same functional outcome as an operator-initiated **`POST /api/v1/trigger`** for a text message (including **channel id**, **thread root or message timestamp**, and **plain text** suitable for **`TriggerBody.message`**), so a supervisor or reply graph can run.

#### Scenario: Mention in channel

- **WHEN** Slack delivers an **`app_mention`** payload for a channel where the bot is present
- **THEN** the system **SHALL** invoke the trigger pipeline **once** per delivered event (subject to documented retry/idempotency policy) with the documented Slack context fields available to downstream code

### Requirement: [CFHA-REQ-SLACK-TRIGGER-002] Trigger path does not ingest Slack mention traffic into managed RAG

The Slack trigger integration **SHALL NOT** call **`POST /v1/embed`** or otherwise persist mention payload text into the managed RAG index **as part of** the trigger forwarding step.

#### Scenario: Trigger-only configuration

- **WHEN** only the Slack trigger integration is enabled and no separate RAG ingestion feature is enabled for those payloads
- **THEN** the trigger handler **SHALL NOT** submit mention content to **`/v1/embed`**

### Requirement: [CFHA-REQ-SLACK-TRIGGER-003] HTTP Events requests are verified when that topology is used

When the operator configures **HTTP Events API** delivery to the runtime, the Slack trigger integration **SHALL** verify incoming requests using the **Slack signing secret** (or successor documented mechanism) before invoking the trigger pipeline, and **SHALL** respond correctly to Slack **URL verification** challenges when applicable.

#### Scenario: Invalid signature

- **WHEN** a POST to the Slack events endpoint carries a signature that fails verification
- **THEN** the system **SHALL** reject the request without invoking **`run_trigger_graph`**

#### Scenario: URL verification challenge

- **WHEN** Slack sends the documented URL verification handshake to the events endpoint
- **THEN** the system **SHALL** return the required challenge response without invoking **`run_trigger_graph`**

### Requirement: [CFHA-REQ-SLACK-TRIGGER-004] Trigger configuration keys are distinct from Slack scraper configuration

Slack trigger settings (for example signing secret, Socket Mode app token, or listener enablement) **SHALL** be loaded from configuration paths **documented as distinct** from **Slack scraper** / **`scrapers`** CronJob settings so operators can provision trigger delivery separately from scheduled ingestion.

#### Scenario: Scraper and trigger both enabled

- **WHEN** a Slack scraper job and the Slack trigger integration are configured
- **THEN** the scraper **SHALL NOT** require the trigger’s signing secret or Socket Mode token fields, and the trigger **SHALL NOT** require scraper-only secret fields

### Requirement: [CFHA-REQ-SLACK-TRIGGER-005] Secrets are never written to logs or metrics labels on the trigger path

The Slack trigger integration **SHALL NOT** print signing secrets, app tokens, or bot tokens to stdout/stderr while handling inbound Slack delivery, and **SHALL NOT** attach those values to Prometheus metric labels.

#### Scenario: Malformed event body

- **WHEN** inbound JSON cannot be parsed or fails structural validation
- **THEN** error handling **SHALL** avoid echoing header values that contain secrets
