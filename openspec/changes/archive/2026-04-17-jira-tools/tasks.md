## 1. Configuration

- [x] 1.1 Add Jira-tools-specific env/Helm keys disjoint from `scrapers.jira` and from `jira-trigger` keys (`[DALC-REQ-JIRA-TOOLS-002]`; coordinate with `openspec/changes/jira-trigger/`).
- [x] 1.2 Document OAuth/API-token scopes for read/search/comment/transition/create-update capabilities.

## 2. Implementation

- [x] 2.1 Add Jira REST client factory for tools env prefix; timeout and structured error mapping (`[DALC-REQ-JIRA-TOOLS-005]`).
- [x] 2.2 Implement allowlisted tools: bounded search/read, comment, transition, create/update within configured scope (`[DALC-REQ-JIRA-TOOLS-003]`, `[DALC-REQ-JIRA-TOOLS-004]`).
- [x] 2.3 Register ids in `hosted_agents.tools_impl.dispatch`; update `tools_impl/README.md`; gate real vs simulated behavior as documented (`[DALC-REQ-JIRA-TOOLS-001]`).
- [x] 2.4 Observability/correlation and side-effect checkpoints for real Jira calls (`[DALC-REQ-JIRA-TOOLS-006]`).

## 3. Verification

- [x] 3.1 Unit tests: argument validation, Jira error mapping, no token leakage (`[DALC-REQ-JIRA-TOOLS-006]`).
- [x] 3.2 Helm unittest for tools env wiring on runtime Deployment when applicable.
- [x] 3.3 Smoke with `jira-trigger`: webhook starts run and agent performs Jira tool action; tools path does not call `/v1/embed` by default (`[DALC-REQ-JIRA-TOOLS-001]`).
