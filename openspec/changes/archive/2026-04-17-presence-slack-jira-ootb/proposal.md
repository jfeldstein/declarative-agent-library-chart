## Why

The README’s getting-started example shows a **`presence`** block with **`slackBotId`** backed by a Kubernetes Secret, but the library chart’s **`values.yaml`** and templates do not implement that path today. Operators have no first-class, symmetric way to declare **who the agent is** on Slack and Jira (for mention filtering, attribution, or future tool behavior) using the same Secret-reference pattern for both platforms. Aligning docs, schema, and rendering closes that gap and makes Slack + Jira **out-of-the-box** from a values perspective.

## What Changes

- Introduce a documented **`presence`** subtree on chart values with **Slack** and **Jira** sections, each supporting identity fields via **`secretName` / `secretKey`** (and sensible defaults for keys where it reduces friction).
- Extend the Helm library chart (schema, default **`values.yaml`**, templates) so rendered workloads receive the right **environment variables or mounted config** for those identities—consistent with how other Secret-sourced settings work (e.g. scraper auth).
- Update the **README** example so it shows **both** Slack and Jira presence configuration without implying unsupported keys.
- Add **helm-unittest** (and/or schema) coverage proving presence is wired when set and omitted when unset.
- **BREAKING**: If the README’s current nested shape (`slackBotId` under `presence`) is replaced by a clearer **`presence.slack`** / **`presence.jira`** layout, existing copies of the old snippet will need a one-time values rename (call out explicitly in design/tasks).

## Capabilities

### New Capabilities

- `dalc-chart-presence`: Library chart SHALL expose **`presence.slack`** and **`presence.jira`** (or equivalent explicit keys) for operator-declared agent identity on each platform, with Secret references for sensitive ids, documentation in README, and tests proving render behavior.

### Modified Capabilities

- _(none)_ — requirement changes are scoped to the new capability unless promotion merges it into an existing promoted spec later.

## Impact

- **`helm/chart/`**: `values.yaml`, `values.schema.json`, templates (e.g. Deployment/ConfigMap env), helm unittest suites under **`helm/tests/`**.
- **`README.md`**: Example **`values.yaml`** block for presence.
- **`helm/src/`**: Only if runtime must read new env vars for presence (otherwise chart-only).
- **Spec promotion / traceability**: New **`[DALC-REQ-…]`** IDs in `openspec/specs/dalc-chart-presence/spec.md` when promoted; **`docs/spec-test-traceability.md`** and test docstrings/comments per **DALC-VER-005**.
