## ADDED Requirements

### Requirement: Declarative HITL configuration

The system SHALL represent human-in-the-loop behavior using **declarative configuration** (e.g. YAML/Helm values or equivalent runtime config), not only imperative Python authored per deployment. Configuration MUST identify **interrupt kinds** and **ordering** relative to named steps or tasks in the workflow template the runtime executes.

#### Scenario: Operator enables a simple feedback interrupt

- **WHEN** declarative config defines a **simple feedback** interrupt after a named automated step
- **THEN** the runtime SHALL materialize a LangGraph functional workflow that calls `interrupt()` at that point with a payload derived from config (e.g. prompt text including upstream step output)

#### Scenario: Operator enables tool-call review

- **WHEN** declarative config enables **tool-call review** for model-emitted tool calls
- **THEN** the runtime SHALL pause before execution with an interrupt payload that includes the tool call(s) to review and SHALL accept structured resume data mapping to continue, revised args, or feedback-as-tool-message per LangGraph’s documented pattern

### Requirement: Functional API and checkpointing

HITL workflows SHALL be implemented using LangGraph’s **functional API** (`@entrypoint`, `@task`, `interrupt`, `Command` for resume) as described in [Use the functional API — Human-in-the-loop](https://docs.langchain.com/oss/python/langgraph/use-functional-api#human-in-the-loop). Any HITL-enabled workflow SHALL be associated with a **checkpointer** so that completed tasks before an interrupt are not re-run on resume.

#### Scenario: Resume after interrupt does not repeat prior tasks

- **WHEN** a run pauses at an interrupt after task A completes and the human resumes with valid input
- **THEN** task A’s side effects MUST NOT execute again for that `thread_id`; only post-interrupt work proceeds

### Requirement: Thread identity and correlation

The system SHALL require a stable **`thread_id`** (or equivalent configurable key) for every HITL-capable invocation so pause and resume correlate to the same checkpointed run. The operator-facing API SHALL document how clients obtain and pass this identifier on initial invoke and on resume.

#### Scenario: Client resumes with same thread

- **WHEN** a client supplies the same `thread_id` on resume as on the initial invoke that produced the interrupt
- **THEN** the system SHALL apply the resume payload to that run and continue execution

### Requirement: JSON-friendly interrupt and resume contract

The externally exposed HTTP (or RPC) surface for hosted agents SHALL describe **interrupts** and **resume requests** using **JSON-serializable** fields. The runtime MAY map these to LangGraph `Command(resume=...)` internally without requiring callers to embed Python-only types.

#### Scenario: Resume maps to Command

- **WHEN** a client sends a valid resume JSON body for the active interrupt kind
- **THEN** the runtime SHALL translate it into the appropriate `Command(resume=...)` value for the functional entrypoint and continue execution

### Requirement: Discovery of paused state

When a run is paused at an interrupt, the system SHALL expose sufficient information for a client or operator to determine that execution is **waiting for human input**, including interrupt kind and a human-readable or structured payload suitable for presentation or automation.

#### Scenario: Stream or status reflects interrupt

- **WHEN** a client uses supported streaming or status mechanisms during a run that hits an interrupt
- **THEN** the client SHALL be able to observe that the run is interrupted and receive data needed to formulate a resume request (without re-invoking completed tasks)
