## 1. Chart values and schema

- [x] 1.1 Add **`presence`** to **`helm/chart/values.yaml`** with **`slack.botUserId`** and **`jira.botAccountId`** objects defaulting to empty **`secretName`** / **`secretKey`** (or omit inner keys per chart conventions).
- [x] 1.2 Extend **`helm/chart/values.schema.json`** with the **`presence`** object and Secret-reference shape for both platforms per **[DALC-REQ-CHART-PRESENCE-001]**.
- [x] 1.3 Update **`helm/chart/templates/_manifest_deployment.tpl`** to inject **`env`** entries via **`secretKeyRef`** when **`secretName`** and **`secretKey`** are non-empty for Slack and Jira per **[DALC-REQ-CHART-PRESENCE-002]**; document final env var names in **`README`** or inline chart comments.

## 2. Tests and documentation

- [x] 2.1 Add or extend **`helm/tests/`** unittest cases asserting presence **`env`** entries when values are set and absence when unset per **[DALC-REQ-CHART-PRESENCE-002]** (cite **`[DALC-REQ-CHART-PRESENCE-…]`** in suite/`it:` comments).
- [x] 2.2 Update root **`README.md`** example **`values.yaml`** to show **`presence.slack`** and **`presence.jira`** together per **[DALC-REQ-CHART-PRESENCE-003]**; remove or replace the outdated **`slackBotId`-only** snippet.
- [x] 2.3 Resolve **Open Questions** in **`design.md`**: either wire ids into **`helm/src`** **`RuntimeConfig`** (if tools need them) or explicitly defer and keep chart-only wiring.

## 3. Spec promotion and traceability (on merge / archive)

- [x] 3.1 Promote **`openspec/changes/presence-slack-jira-ootb/specs/dalc-chart-presence/spec.md`** to **`openspec/specs/dalc-chart-presence/spec.md`** when the change is accepted.
- [x] 3.2 Add rows for **`[DALC-REQ-CHART-PRESENCE-001]`** … **`003`** to **`docs/spec-test-traceability.md`** with evidence paths and CI tier.
- [x] 3.3 Run **`python3 scripts/check_spec_traceability.py`** and fix any drift before merge.
