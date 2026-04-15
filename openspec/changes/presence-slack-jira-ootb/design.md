## Context

The root **README** shows **`presence.slackBotId`** with **`secretName` / `secretKey`**, but **`helm/chart/values.yaml`** has no **`presence`** key and **`deployment.yaml`** does not mount those secrets. **`values.schema.json`** still describes **`tools`** (draft) with plain-string **`slackBotId`**, which does not match the README or the Secret-first pattern used under **`scrapers.*.auth`**. Jira has no parallel “agent identity” knob in values today.

## Goals / Non-Goals

**Goals:**

- Define a single, documented **`presence`** subtree with **Slack** and **Jira** children, each using the same **Kubernetes Secret reference** pattern (`secretName`, `secretKey`) as other chart secrets.
- Render **optional** `env` entries on the agent **`Deployment`** so the process can read stable env vars (exact names fixed in implementation; design default: **`HOSTED_AGENT_SLACK_BOT_USER_ID`** and **`HOSTED_AGENT_JIRA_BOT_ACCOUNT_ID`**) when the corresponding presence block is set.
- Update **README** example values to show **both** platforms OOTB.
- Lock the contract in **JSON Schema** and **helm-unittest** (present/absent cases).

**Non-Goals:**

- Implementing full Jira/Slack MCP tool suites or mention-routing logic—only **chart values, docs, and wiring** unless the runtime already has a clear consumer (if not, env vars may be unused until tools read them; call out in tasks whether Python **`RuntimeConfig`** must be extended).
- Backward compatibility for the README-only shape **`presence.slackBotId`** unless tasks explicitly choose to support it as an alias; prefer one canonical nested shape (**`presence.slack`**, **`presence.jira`**) to avoid duplicate paths.

## Decisions

1. **Canonical values shape** — Use **`presence.slack.botUserId`** and **`presence.jira.botAccountId`** (or **`serviceAccountId`**) each as an object **`{ secretName, secretKey }`**.  
   - *Rationale:* Matches **`scrapers.jira.auth`** / **`scrapers.slack.auth`** style; “bot user id” (Slack) and “account id” (Jira Cloud) are the usual stable identifiers for “this agent” on each platform.  
   - *Alternative considered:* Flat **`presence.slackBotId`** only — rejected because it does not extend to Jira symmetrically and confuses “id” with Secret metadata.

2. **Injection mechanism** — **`secretKeyRef`** on the agent container **`env`** entries, gated on non-empty **`secretName`** (and optionally **`secretKey`**).  
   - *Rationale:* Same pattern as other credentials; no new CRDs.  
   - *Alternative:* Init container / projected volume — heavier than needed for single string ids.

3. **Default empty** — **`presence`** defaults: both platform blocks empty or disabled-by-omission so existing installs see **no** new env vars.  
   - *Rationale:* Safe upgrade path; tests assert absence when unset.

4. **Naming alignment with README** — Replace the current README snippet with the canonical nested keys and a short comment that Jira **`botAccountId`** is the Jira Cloud **accountId** for the automation user.  
   - *Rationale:* Removes doc drift from schema.

## Risks / Trade-offs

- **[Risk]** Operators copied the old **`slackBotId`** nesting from README → **Mitigation:** Document one-time migration in proposal/tasks; optionally support both shapes briefly (adds Helm complexity—prefer breaking doc-only if no chart ever implemented the old key).
- **[Risk]** Runtime does not yet read the new env vars → **Mitigation:** Tasks include verifying consumer or explicitly scoping “chart-only” with follow-up; unittest still proves Secret wiring.
- **[Risk]** Jira Server/DC uses different identity concepts → **Mitigation:** Document Jira Cloud as the reference; key name **`botAccountId`** stays generic enough for a string id from Secret.

## Migration Plan

1. Ship chart changes with **defaults off** (no presence secrets required).
2. Operators add **`presence.slack`** / **`presence.jira`** and create Secrets with ids.
3. Rollback: remove **`presence`** keys and redeploy; env entries disappear.

## Open Questions

- Exact **env var names** (if product already standardizes on different names, align in implementation).
- Whether **Python** should load these into **`RuntimeConfig`** immediately or defer to a later tools change.
