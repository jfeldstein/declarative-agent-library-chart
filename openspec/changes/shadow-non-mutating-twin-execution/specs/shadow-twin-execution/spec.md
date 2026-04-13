## ADDED Requirements

### Requirement: Shadow twin runner executes full agent path

The system SHALL execute a **shadow twin** for an eligible primary request that runs the same configured agent workflow (supervisor/graph entrypoint) as the primary, using the same normalized request inputs at the boundary, under an execution context marked `rollout_arm=shadow` and a configured `shadow_variant_id`.

#### Scenario: Twin runs after primary completes

- **WHEN** shadow twin mode is enabled and the request matches sampling and tenant bounds
- **THEN** the system SHALL invoke the shadow twin runner after the primary response is committed or SHALL invoke it asynchronously per configuration without blocking the primary past a configured deadline

#### Scenario: Twin uses variant configuration

- **WHEN** a shadow variant specifies skill version, model id, and/or prompt hash overrides
- **THEN** the shadow twin SHALL apply those overrides only inside the shadow execution context and SHALL NOT mutate primary deployment configuration

### Requirement: Request correlation and identity

The system SHALL assign and propagate a stable `request_correlation_id` for each primary request that has shadow enabled. The shadow twin SHALL inherit the same `request_correlation_id` and primary `thread_id` as read-only correlation fields while using a distinct **shadow persistence key** for checkpoints and internal state.

#### Scenario: Telemetry join key

- **WHEN** primary and shadow complete for the same request
- **THEN** both SHALL emit telemetry containing the same `request_correlation_id` and SHALL include `rollout_arm` (`primary` vs `shadow`) and `shadow_variant_id` on shadow records

### Requirement: Checkpoint and state isolation

The system SHALL ensure shadow twin execution does not read or write primary LangGraph checkpoints under the primary `thread_id` namespace. Shadow MAY persist checkpoints only under an isolated namespace or MAY run with shadow checkpointing disabled by default.

#### Scenario: No primary checkpoint overwrite

- **WHEN** shadow twin executes tool and graph steps
- **THEN** the system SHALL NOT update primary checkpoint history for the primary `thread_id` as a side effect of shadow execution

### Requirement: Tool classification for shadow safety

The system SHALL classify each tool id for shadow execution as **read-only**, **mutating external**, or **internal** via registry metadata (or explicit per-tool override). Tools without metadata SHALL be treated as **mutating external** for shadow safety.

#### Scenario: Unknown tool defaults to mutating

- **WHEN** shadow twin invokes a tool id that has no shadow classification metadata
- **THEN** the system SHALL treat the tool as mutating external and SHALL apply stubbing rules unless a deployment-wide dangerous override is enabled

### Requirement: Default non-mutating stubbing of external tools

For shadow twins, the system SHALL NOT perform mutating external side effects unless the tool is **allowlisted for shadow** or a **dangerous full-mirror** flag is enabled. The system SHALL record planned arguments (redacted per policy), stub result envelope, and timing for stubbed calls.

#### Scenario: Mutating tool stubbed

- **WHEN** shadow twin reaches a mutating external tool that is not allowlisted and full-mirror is disabled
- **THEN** the system SHALL not perform the real side effect and SHALL return a stub result that explicitly indicates shadow stubbing and the reason code

#### Scenario: Read-only tool executes

- **WHEN** shadow twin reaches a tool classified as read-only
- **THEN** the system MAY execute the real implementation subject to rate limits and redaction policy

### Requirement: Shadow allowlist and dangerous full mirror

The system SHALL support configuration that allowlists specific tool ids for real execution during shadow. The system SHALL support a separately named **dangerous** flag that permits full mirror of mutating tools, default **off**.

#### Scenario: Allowlisted mutating tool executes

- **WHEN** a mutating external tool id appears on the shadow tool allowlist and dangerous full mirror is disabled
- **THEN** the system SHALL execute the real tool implementation in shadow context

#### Scenario: Full mirror requires danger flag

- **WHEN** an operator attempts to run shadow without allowlist entries but expects real mutating execution
- **THEN** the system SHALL refuse or SHALL require the dangerous full-mirror flag to be explicitly enabled

### Requirement: Failure isolation for shadow twin

Shadow twin failures SHALL NOT cause the primary HTTP request to fail by default. The system SHALL record shadow failure as operational telemetry on the shadow arm.

#### Scenario: Shadow raises mid-run

- **WHEN** the shadow twin raises an unhandled exception or exceeds a budget
- **THEN** the primary response status and body SHALL remain as if shadow were disabled unless explicitly configured otherwise
- **AND** the system SHALL emit a shadow failure record tied to `request_correlation_id`

### Requirement: Comparable telemetry and budgets

The system SHALL emit comparable metrics for primary and shadow twins including, where available, total latency, token usage, tool call count/order, and outcome classification. The system SHALL enforce configurable **shadow budgets** (wall time, max tokens, max tool calls).

#### Scenario: Budget stops shadow

- **WHEN** shadow twin exceeds configured max tokens or wall time
- **THEN** the system SHALL terminate shadow execution and SHALL record budget exhaustion on the shadow telemetry stream

### Requirement: Trajectory and export provenance

Canonical trajectory and ATIF-oriented exports SHALL tag shadow twin steps with `rollout_arm=shadow` and `shadow_variant_id`. Export jobs SHALL default to excluding shadow steps unless explicitly requested, or SHALL emit shadow in a separate manifest per configuration.

#### Scenario: Export filter explicit feedback only

- **WHEN** an export requests primary-only training data
- **THEN** the output SHALL exclude shadow twin steps unless the request explicitly opts in to include shadow
