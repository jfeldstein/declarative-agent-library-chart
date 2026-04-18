## ADDED Requirements

### Requirement: [DALC-REQ-CHART-PRESENCE-001] Presence values for Slack and Jira

The Helm library chart SHALL expose a top-level **`presence`** object with at least:

- **`slack`**, containing **`botUserId`** as an optional object with **`secretName`** and **`secretKey`** (strings), referencing the Slack **bot user id** (for example `U…`) used to identify the agent in Slack.
- **`jira`**, containing **`botAccountId`** as an optional object with **`secretName`** and **`secretKey`** (strings), referencing the Jira Cloud **accountId** for the automation user that represents the agent.

The chart’s **`values.schema.json`** SHALL describe this shape, and the default **`values.yaml`** SHALL include the keys with empty or null-safe defaults consistent with other optional Secret-backed settings.

#### Scenario: Schema documents both platforms

- **WHEN** a maintainer inspects **`values.schema.json`**
- **THEN** **`presence.slack.botUserId`** and **`presence.jira.botAccountId`** SHALL be defined as Secret-reference objects suitable for **`secretKeyRef`**

#### Scenario: Defaults do not require secrets

- **WHEN** an operator uses chart defaults without setting **`presence`**
- **THEN** rendering SHALL NOT require **`presence`**-related Secrets to exist

### Requirement: [DALC-REQ-CHART-PRESENCE-002] Agent workload receives presence from Secrets

When **`presence.slack.botUserId.secretName`** and **`presence.slack.botUserId.secretKey`** are both non-empty (after trimming whitespace), the agent **`Deployment`** (or equivalent workload template) SHALL expose the Slack bot user id to the container via an environment variable (implementation: **`HOSTED_AGENT_SLACK_BOT_USER_ID`**) sourced with **`valueFrom.secretKeyRef`** using those strings.

When **`presence.jira.botAccountId.secretName`** and **`presence.jira.botAccountId.secretKey`** are both non-empty, the same SHALL apply for the Jira account id (implementation: **`HOSTED_AGENT_JIRA_BOT_ACCOUNT_ID`**).

When a given presence field is unset, **`secretName`** is empty, **`secretKey`** is empty, or only one of **`secretName`** / **`secretKey`** is set, the chart SHALL NOT inject the corresponding environment variable.

#### Scenario: Slack presence wired

- **WHEN** **`presence.slack.botUserId`** specifies a non-empty **`secretName`** and **`secretKey`**
- **THEN** rendered manifests SHALL include the Slack presence **`env`** entry with **`secretKeyRef`** pointing at that Secret

#### Scenario: Jira presence wired

- **WHEN** **`presence.jira.botAccountId`** specifies a non-empty **`secretName`** and **`secretKey`**
- **THEN** rendered manifests SHALL include the Jira presence **`env`** entry with **`secretKeyRef`** pointing at that Secret

#### Scenario: Incomplete Secret reference omits env

- **WHEN** **`presence.slack.botUserId.secretName`** is non-empty but **`secretKey`** is empty (or the reverse)
- **THEN** rendered agent manifests SHALL NOT include **`HOSTED_AGENT_SLACK_BOT_USER_ID`**

#### Scenario: Omitted presence omits env

- **WHEN** **`presence`** is absent or both **`secretName`** fields are empty
- **THEN** rendered agent manifests SHALL NOT include **`HOSTED_AGENT_SLACK_BOT_USER_ID`** or **`HOSTED_AGENT_JIRA_BOT_ACCOUNT_ID`** (or whatever final names are documented for this requirement)

### Requirement: [DALC-REQ-CHART-PRESENCE-003] README documents OOTB Slack and Jira presence

The repository’s primary **README** SHALL include an example **`values.yaml`** fragment under the library chart key showing **`presence.slack`** and **`presence.jira`** together (each with **`secretName`** / **`secretKey`**), so operators can configure both platforms without inventing ad hoc keys.

#### Scenario: Example shows both platforms

- **WHEN** a reader follows the README “Example” **`values.yaml`**
- **THEN** they SHALL see **`presence`** blocks for **both** Slack and Jira using the same Secret-reference pattern
