## 1. Shared configuration (trigger + tools vs scraper)

- [ ] 1.1 Document and implement **non-overlapping** Helm/env keys for **Jira scraper** vs **`jira-trigger`** vs **`jira-tools`** (`[CFHA-REQ-JIRA-TRIGGER-004]`, `[CFHA-REQ-JIRA-TOOLS-002]`).
- [ ] 1.2 Extend **`values.schema.json`** / **`values.yaml`** with subsections (or equivalent) for trigger and tools, including scope notes for operators; reconcile with draft **`tools.jira`** when ready.

## 2. Jira Trigger (`jira-trigger`)

- [ ] 2.1 Implement **webhook** HTTP route: parse JSON body, apply **documented verification** (`[CFHA-REQ-JIRA-TRIGGER-003]`).
- [ ] 2.2 Map **accepted webhook payload** → **`TriggerBody`** / internal **`run_trigger_graph`** call; pass **issue key**, **project**, **event**, **text** suitable for **`TriggerBody.message`** (`[CFHA-REQ-JIRA-TRIGGER-001]`).
- [ ] 2.3 Ensure trigger handler **never** calls **`/v1/embed`** (`[CFHA-REQ-JIRA-TRIGGER-002]`).
- [ ] 2.4 Logging and metrics: **no** secrets in logs or labels (`[CFHA-REQ-JIRA-TRIGGER-005]`).
- [ ] 2.5 Unit tests: verification failure, happy-path webhook → one trigger invocation; optional **dedupe** (`[CFHA-REQ-JIRA-TRIGGER-003]`).

## 3. Jira Tools (`jira-tools`)

- [ ] 3.1 Add **Jira REST** client factory for tools env prefix; timeouts and structured errors (`[CFHA-REQ-JIRA-TOOLS-005]`).
- [ ] 3.2 Implement tools within **documented scopes**: bounded search/read, comment, transition, create/update as allowlisted (`[CFHA-REQ-JIRA-TOOLS-003]`, `[CFHA-REQ-JIRA-TOOLS-004]`).
- [ ] 3.3 Register ids in **`hosted_agents.tools_impl.dispatch`**; update **`tools_impl/README.md`**; gate simulation when credentials present (`[CFHA-REQ-JIRA-TOOLS-001]`).
- [ ] 3.4 Observability: correlation / side-effect checkpoints for real Jira calls (`[CFHA-REQ-JIRA-TOOLS-006]`).
- [ ] 3.5 Unit tests: argument validation, Jira error mapping, no token leakage in logs (`[CFHA-REQ-JIRA-TOOLS-006]`).

## 4. End-to-end verification

- [ ] 4.1 Helm unittest for env wiring for **trigger** and **tools** on the runtime Deployment (if applicable).
- [ ] 4.2 Smoke: **webhook** → trigger run starts; agent uses tools to **comment** or **transition**; confirm **no** `/v1/embed` from tools (`[CFHA-REQ-JIRA-TRIGGER-002]`, `[CFHA-REQ-JIRA-TOOLS-001]`).
