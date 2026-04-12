## ADDED Requirements

### Requirement: #agent- prefix convention for bot-readable content

The system SHALL use the #agent- prefix convention to denote content that is machine-readable by agent automation systems. All agent-related configuration, descriptions, evaluations, and metadata SHALL be prefixed with #agent- when intended for automated processing.

#### Scenario: Agent configuration uses #agent-config prefix

- **WHEN** creating agent configuration files
- **THEN** the content SHALL be prefixed with #agent-config to indicate machine-readable configuration

#### Scenario: Agent description uses #agent-description prefix

- **WHEN** writing agent descriptions or documentation
- **THEN** the content SHALL be prefixed with #agent-description to indicate machine-readable description

#### Scenario: Agent evaluation uses #agent-eval prefix

- **WHEN** creating evaluation suites or test cases
- **THEN** the content SHALL be prefixed with #agent-eval to indicate machine-readable evaluations

#### Scenario: Non-agent content does not use #agent- prefix

- **WHEN** creating content not intended for agent automation
- **THEN** the content SHALL NOT use #agent- prefix to avoid false positives

### Requirement: Prefix validation in CI pipeline

The CI pipeline SHALL validate that all agent-related content uses the proper #agent- prefix convention and SHALL reject content that violates this convention.

#### Scenario: CI validates #agent- prefix usage

- **WHEN** running CI checks on agent-related files
- **THEN** the pipeline SHALL validate proper #agent- prefix usage and fail on violations

#### Scenario: CI allows non-prefixed content in non-agent contexts

- **WHEN** running CI checks on non-agent files
- **THEN** the pipeline SHALL NOT require #agent- prefixes

### Requirement: Linter rules for prefix convention

The system SHALL include linter rules that enforce the #agent- prefix convention and provide clear error messages for violations.

#### Scenario: Linter detects missing #agent- prefix

- **WHEN** running linter on agent content without proper prefix
- **THEN** the linter SHALL detect the violation and provide clear error message

#### Scenario: Linter allows proper prefix usage

- **WHEN** running linter on agent content with proper prefix
- **THEN** the linter SHALL pass without errors