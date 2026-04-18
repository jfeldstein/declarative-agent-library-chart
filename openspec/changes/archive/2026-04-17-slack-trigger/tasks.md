## 1. Configuration

- [x] 1.1 Add **Slack-trigger-specific** env/Helm keys **disjoint** from **`scrapers`** and from **Slack tools** keys (`[DALC-REQ-SLACK-TRIGGER-004]`; coordinate with **`openspec/changes/slack-tools/`**).
- [x] 1.2 Document operator Slack app setup: **Event Subscriptions** / Socket Mode, **`app_mention`** bot scope.

## 2. Inbound path

- [x] 2.1 HTTP Events: URL verification + signing secret verification (`[DALC-REQ-SLACK-TRIGGER-003]`).
- [x] 2.2 Socket Mode: connect and dispatch **`app_mention`** to shared handler (`[DALC-REQ-SLACK-TRIGGER-001]`).
- [x] 2.3 Map payload → **`TriggerBody`** / **`run_trigger_graph`** with channel, thread ts, text (`[DALC-REQ-SLACK-TRIGGER-001]`).
- [x] 2.4 Confirm trigger path **never** calls **`/v1/embed`** (`[DALC-REQ-SLACK-TRIGGER-002]`).
- [x] 2.5 Logs/metrics: no secrets (`[DALC-REQ-SLACK-TRIGGER-005]`).

## 3. Verification

- [x] 3.1 Unit tests: bad signature, URL challenge, happy-path mention → one trigger (`[DALC-REQ-SLACK-TRIGGER-003]`).
- [x] 3.2 Optional: **`event_id`** dedupe tests.
