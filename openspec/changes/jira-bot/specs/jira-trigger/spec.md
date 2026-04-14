## ADDED Requirements

### Requirement: [CFHA-REQ-JIRA-TRIGGER-001] Jira webhook events start a hosted agent trigger run

The Jira trigger integration **SHALL** accept **documented Jira Cloud webhook** deliveries (or operator-configured equivalent) for enabled event types and **SHALL** forward each accepted delivery into the hosted agent **trigger pipeline** with the same functional outcome as an operator-initiated **`POST /api/v1/trigger`** for a text message (including **issue key**, **project key**, **webhook event type**, and **plain text** suitable for **`TriggerBody.message`** derived from fields such as summary, comment body, or changelog as available), so a supervisor or reply graph can run.

#### Scenario: Issue updated webhook

- **WHEN** Jira delivers a webhook payload for an **issue updated** event matching operator configuration
- **THEN** the system **SHALL** invoke the trigger pipeline **once** per accepted delivery (subject to documented retry/idempotency policy) with the documented Jira context fields available to downstream code

### Requirement: [CFHA-REQ-JIRA-TRIGGER-002] Trigger path does not ingest Jira webhook traffic into managed RAG

The Jira trigger integration **SHALL NOT** call **`POST /v1/embed`** or otherwise persist webhook payload text into the managed RAG index **as part of** the trigger forwarding step.

#### Scenario: Trigger-only configuration

- **WHEN** only the Jira trigger integration is enabled and no separate RAG ingestion feature is enabled for those payloads
- **THEN** the trigger handler **SHALL NOT** submit webhook content to **`/v1/embed`**

### Requirement: [CFHA-REQ-JIRA-TRIGGER-003] Webhook requests are verified when that topology is used

When the operator configures **Jira webhooks** (or documented successor) delivered to the runtime, the Jira trigger integration **SHALL** verify incoming requests using the **mechanism documented for that webhook type** (for example shared secret comparison, signature header, or Connect JWT rules when applicable) before invoking the trigger pipeline, and **SHALL** reject malformed or unverifiable requests without invoking **`run_trigger_graph`**.

#### Scenario: Invalid secret or signature

- **WHEN** a POST to the Jira webhook endpoint fails verification
- **THEN** the system **SHALL** reject the request without invoking **`run_trigger_graph`**

#### Scenario: Unsupported content type

- **WHEN** the request body cannot be parsed as the expected JSON webhook envelope
- **THEN** the system **SHALL** reject the request without invoking **`run_trigger_graph`**

### Requirement: [CFHA-REQ-JIRA-TRIGGER-004] Trigger configuration keys are distinct from Jira scraper configuration

Jira trigger settings (for example webhook signing secret, optional Connect app credentials used only for inbound verification) **SHALL** be loaded from configuration paths **documented as distinct** from **Jira scraper** / **`scrapers`** CronJob settings so operators can provision webhook delivery separately from scheduled ingestion.

#### Scenario: Scraper and trigger both enabled

- **WHEN** a Jira scraper job and the Jira trigger integration are configured
- **THEN** the scraper **SHALL NOT** require the trigger’s webhook secret-only fields, and the trigger **SHALL NOT** require scraper-only batching or watermark fields

### Requirement: [CFHA-REQ-JIRA-TRIGGER-005] Secrets are never written to logs or metrics labels on the trigger path

The Jira trigger integration **SHALL NOT** print webhook signing secrets, JWT material, or API tokens to stdout/stderr while handling inbound Jira delivery, and **SHALL NOT** attach those values to Prometheus metric labels.

#### Scenario: Malformed event body

- **WHEN** inbound JSON cannot be parsed or fails structural validation
- **THEN** error handling **SHALL** avoid echoing header values that contain secrets
