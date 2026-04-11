## ADDED Requirements

### Requirement: BaseTen inference configuration

The system SHALL support declarative configuration that selects **BaseTen** as the LLM inference backend, including a **base URL** for the OpenAI-compatible API, a **model or deployment identifier** string, and **API credentials** supplied via Kubernetes **Secret** reference (not committed in plain values).

#### Scenario: Operator enables BaseTen with a Secret

- **WHEN** the operator sets inference provider to BaseTen, provides `baseUrl` and `model` (or equivalent identifier fields), and references an existing Secret key for the API token
- **THEN** the workload SHALL receive environment variables or mounted secret data sufficient for the runtime to authenticate to BaseTen without embedding the token in ConfigMaps or non-secret values

#### Scenario: Inference disabled by default

- **WHEN** inference provider is unset or set to a disabled/none value
- **THEN** the system SHALL NOT require BaseTen credentials and SHALL preserve prior non-remote inference behavior for existing code paths (e.g. deterministic replies where that is the current implementation)

### Requirement: OpenAI-compatible chat completion call

When BaseTen inference is enabled, the runtime SHALL invoke the configured model using an **OpenAI-compatible chat completions** request to the configured base URL (including authentication headers derived from the supplied Secret), and SHALL use the response text as the model output for the calling agent/subagent path.

#### Scenario: Successful completion

- **WHEN** BaseTen inference is enabled and the remote API returns a successful chat completion payload
- **THEN** the runtime SHALL extract the assistant message content and return it to the caller without logging the API key

#### Scenario: Remote error

- **WHEN** the remote API returns a non-success HTTP status or malformed payload
- **THEN** the runtime SHALL surface a controlled error to the API layer (appropriate HTTP status where applicable) and SHALL NOT include the raw API key in error responses or logs

### Requirement: Helm chart wiring

The Helm chart SHALL expose values (with JSON Schema descriptions) for BaseTen inference settings and SHALL wire API credentials using `secretKeyRef` (or equivalent) on the agent Deployment, consistent with Kubernetes best practices.

#### Scenario: Schema documents secret-backed credentials

- **WHEN** an operator reads `values.schema.json` for inference settings
- **THEN** API key material SHALL be described as coming from a Secret name and key, not as a plain string field intended for checked-in values

### Requirement: Automated tests without live BaseTen

The runtime test suite SHALL include tests that validate inference integration using **mocked HTTP** or stubbed clients, so that continuous integration does not require BaseTen network access or real credentials.

#### Scenario: Mocked successful call

- **WHEN** tests run with a mock server or patched HTTP client returning a fixed OpenAI-style completion JSON
- **THEN** the runtime code under test SHALL produce the expected assistant text and the test SHALL pass without external network calls
