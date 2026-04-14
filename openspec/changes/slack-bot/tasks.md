## 1. Shared configuration (trigger + tools vs scraper)

- [ ] 1.1 Document and implement **non-overlapping** Helm/env keys for **Slack scraper** vs **`slack-trigger`** vs **`slack-tools`** (`[CFHA-REQ-SLACK-TRIGGER-004]`, `[CFHA-REQ-SLACK-TOOLS-002]`).
- [ ] 1.2 Extend **`values.schema.json`** / **`values.yaml`** with subsections (or equivalent) for trigger and tools, including scope notes for operators.

## 2. Slack Trigger (`slack-trigger`)

- [ ] 2.1 Implement **HTTP Events** route (if chosen): URL verification + **signing secret** verification (`[CFHA-REQ-SLACK-TRIGGER-003]`).
- [ ] 2.2 Implement **Socket Mode** listener (if chosen): connect using documented app-level token; dispatch **`app_mention`** to the same handler as HTTP (`[CFHA-REQ-SLACK-TRIGGER-001]`).
- [ ] 2.3 Map **`app_mention`** payload → **`TriggerBody`** / internal **`run_trigger_graph`** call; pass **channel**, **thread ts**, **text** (`[CFHA-REQ-SLACK-TRIGGER-001]`).
- [ ] 2.4 Ensure trigger handler **never** calls **`/v1/embed`** (`[CFHA-REQ-SLACK-TRIGGER-002]`).
- [ ] 2.5 Logging and metrics: **no** secrets in logs or labels (`[CFHA-REQ-SLACK-TRIGGER-005]`).
- [ ] 2.6 Unit tests: signature failure, URL challenge, happy-path mention → one trigger invocation; optional **`event_id`** dedupe (`[CFHA-REQ-SLACK-TRIGGER-003]`).

## 3. Slack Tools (`slack-tools`)

- [ ] 3.1 Add **`slack_sdk.WebClient`** factory for tools env prefix; timeouts and structured errors (`[CFHA-REQ-SLACK-TOOLS-005]`).
- [ ] 3.2 Implement tools: **post** (incl. thread), **reactions** add/remove, **chat.update**, **conversations.history** / replies with caps (`[CFHA-REQ-SLACK-TOOLS-003]`, `[CFHA-REQ-SLACK-TOOLS-004]`).
- [ ] 3.3 Register ids in **`hosted_agents.tools_impl.dispatch`**; update **`tools_impl/README.md`**; gate or replace **`slack.post_message`** simulation when token present (`[CFHA-REQ-SLACK-TOOLS-001]`).
- [ ] 3.4 Observability: correlation / side-effect checkpoints for real Slack calls (`[CFHA-REQ-SLACK-TOOLS-006]`).
- [ ] 3.5 Unit tests: argument validation, Slack error mapping, no token leakage in logs (`[CFHA-REQ-SLACK-TOOLS-006]`).

## 4. End-to-end verification

- [ ] 4.1 Helm unittest for env wiring for **trigger** and **tools** on the runtime Deployment (if applicable).
- [ ] 4.2 Smoke: **@mention** → trigger run starts; agent uses tools to **react** + **thread reply**; confirm **no** `/v1/embed` from tools (`[CFHA-REQ-SLACK-TRIGGER-002]`, `[CFHA-REQ-SLACK-TOOLS-001]`).
