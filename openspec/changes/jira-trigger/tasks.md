## 1. Configuration

- [ ] 1.1 Add Jira-trigger-specific env/Helm keys disjoint from `scrapers.jira` and `jira-tools` (`[DALC-REQ-JIRA-TRIGGER-004]`; coordinate with `openspec/changes/jira-tools/`).
- [ ] 1.2 Document operator setup for Jira webhooks and required verification material.

## 2. Inbound path

- [ ] 2.1 Implement webhook route: parse JSON, apply documented verification (`[DALC-REQ-JIRA-TRIGGER-003]`).
- [ ] 2.2 Map accepted payload -> `TriggerBody` / `run_trigger_graph` with issue/project/event/text context (`[DALC-REQ-JIRA-TRIGGER-001]`).
- [ ] 2.3 Ensure trigger handler never calls `/v1/embed` (`[DALC-REQ-JIRA-TRIGGER-002]`).
- [ ] 2.4 Logging/metrics: no secrets in logs or labels (`[DALC-REQ-JIRA-TRIGGER-005]`).
- [ ] 2.5 Unit tests: verification failure, happy-path webhook -> one trigger invocation; optional dedupe tests.

## 3. Verification

- [ ] 3.1 Helm unittest for trigger env wiring on runtime Deployment (if applicable).
- [ ] 3.2 Smoke with `jira-tools`: webhook -> trigger run starts -> run can call Jira tools; trigger path itself never embeds.
