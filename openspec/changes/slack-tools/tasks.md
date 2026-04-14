## 1. Configuration

- [ ] 1.1 Add **Slack-tools-specific** env/Helm keys **disjoint** from **`scrapers`** and from **Slack trigger** keys (`[DALC-REQ-SLACK-TOOLS-002]`; coordinate with **`openspec/changes/slack-trigger/`**).
- [ ] 1.2 Document OAuth scopes for **chat**, **reactions**, **history** as needed.

## 2. Implementation

- [ ] 2.1 **`slack_sdk.WebClient`** factory for tools (`[DALC-REQ-SLACK-TOOLS-005]`).
- [ ] 2.2 Tools: post (incl. thread), reactions add/remove, **`chat.update`**, history/replies with caps (`[DALC-REQ-SLACK-TOOLS-003]`, `[DALC-REQ-SLACK-TOOLS-004]`).
- [ ] 2.3 **`dispatch`** + **`tools_impl/README.md`**; gate real vs simulated post (`[DALC-REQ-SLACK-TOOLS-001]`).
- [ ] 2.4 Observability on real calls (`[DALC-REQ-SLACK-TOOLS-006]`).

## 3. Verification

- [ ] 3.1 Unit tests: validation, error mapping, no token leakage (`[DALC-REQ-SLACK-TOOLS-006]`).
- [ ] 3.2 Helm unittest for tools env on Deployment when applicable.
- [ ] 3.3 Smoke with **`slack-trigger`**: mention → run uses tools to react + thread reply; no **`/v1/embed`** from tools path (`[DALC-REQ-SLACK-TOOLS-001]`).
