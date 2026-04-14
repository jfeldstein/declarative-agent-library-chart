## ADDED Requirements

### Requirement: [DALC-REQ-JIRA-TOOLS-001] Jira tools operate during agent invocation and do not ingest tool I/O into managed RAG by default

Jira tools **SHALL** be invocable **only** during an active agent run (for example via **`run_tool_json`** while handling a trigger), and **SHALL NOT** automatically submit tool payloads or returned Jira issue bodies to **`POST /v1/embed`** or the managed RAG index **unless** a separate capability explicitly enables that.

#### Scenario: Default configuration

- **WHEN** Jira tools are enabled with only the settings documented for interactive REST usage
- **THEN** tool implementations **SHALL NOT** call **`POST /v1/embed`** for issues read or updated solely through Jira tools

### Requirement: [DALC-REQ-JIRA-TOOLS-002] Jira tools credentials are distinct from Jira scraper credentials

Jira tools **SHALL** load API tokens, OAuth client secrets, or related authorization material **only** from configuration keys and environment variables **documented as distinct** from the Jira scraper / **`scrapers`** CronJob configuration.

#### Scenario: Scraper and tools both enabled

- **WHEN** a Jira scraper job and Jira tools are enabled
- **THEN** each **SHALL** read Jira authorization material from **non-overlapping** documented settings (no single undocumented shared secret field required for both)

### Requirement: [DALC-REQ-JIRA-TOOLS-003] Agent can read and mutate issues within configured scopes

Jira tools **SHALL** include allowlisted operations so the agent can **fetch issue details**, **add comments**, **transition** issues when the operator has enabled the corresponding scope, and **create or update** issues only where explicitly allowlisted, returning structured success or error results.

#### Scenario: Comment added

- **WHEN** the agent invokes the documented comment tool with valid issue key and comment body within configured limits
- **THEN** the system **SHALL** call Jira Cloud REST (or documented successor) to add the comment and **SHALL** return structured metadata (for example comment id) on success without logging secrets

#### Scenario: Transition applied

- **WHEN** the agent invokes the documented transition tool with valid issue key and transition id or name allowed by configuration
- **THEN** the system **SHALL** apply the transition via Jira REST and **SHALL** return structured workflow metadata on success

#### Scenario: Scoped create

- **WHEN** the operator has enabled **create** scope for a documented project list and the agent invokes the create tool with valid fields
- **THEN** the system **SHALL** create the issue only inside an allowlisted project and **SHALL** return the new issue key on success

### Requirement: [DALC-REQ-JIRA-TOOLS-004] Agent can run bounded JQL or issue search

Jira tools **SHALL** provide a documented read or search tool (or tools) that returns **issues or fields** matching a **bounded** query (maximum result count and/or documented JQL length and timeout caps).

#### Scenario: Search results capped

- **WHEN** the agent requests search with JQL within documented limits
- **THEN** the system **SHALL** return normalized issue records up to the configured cap and **SHALL NOT** include raw bearer tokens or Basic auth material in the response

### Requirement: [DALC-REQ-JIRA-TOOLS-005] Jira REST access uses httpx consistent with repository dependency policy

Jira tools **SHALL** perform Jira REST calls using **`httpx`** (or a thin documented wrapper) consistent with repository dependency policy, and **SHALL NOT** rely on undocumented private Atlassian HTTP endpoints.

#### Scenario: Dependency present

- **WHEN** the runtime image is built for a release that includes Jira tools
- **THEN** package metadata **SHALL** declare **`httpx`** with version constraints consistent with repository policy

### Requirement: [DALC-REQ-JIRA-TOOLS-006] Secrets are never written to logs or metrics labels on the tools path

Jira tools **SHALL NOT** print API tokens, OAuth secrets, or **`Authorization`** headers to stdout/stderr, and **SHALL NOT** attach those values to Prometheus metric labels.

#### Scenario: Jira API error

- **WHEN** a Jira REST call fails with an authorization or permission error
- **THEN** logs **SHALL** redact or omit secret material while still recording a safe correlation identifier such as **Atlassian trace id** or **issue key** when available
