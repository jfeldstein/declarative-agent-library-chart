## Context

**`hosted_agents.tools_impl.slack_post`** is currently **simulated** (observability only). This change supplies **real** Slack Web API behavior for triggered runs.

## Goals / Non-Goals

**Goals:**

- **`slack_sdk.WebClient`** with timeouts and structured errors.
- Tools for **reactions**, **post** (including **thread_ts**), **chat.update**, **conversations.history** / replies with **documented limits**.
- Correlation / side-effect checkpoints for real calls where applicable.

**Non-Goals:**

- Slack **event subscription** or signing-secret HTTP handler (**`slack-trigger`**).
- Embedding tool traffic into RAG by default.

## Decisions

1. **Env prefix** for tools (illustrative): **`HOSTED_AGENT_SLACK_TOOLS_*`**, disjoint from trigger and scraper env names.
2. **Simulation**: When token absent, keep simulated **`slack.post_message`** (or equivalent) for CI; when present, call Slack.

## Risks / Trade-offs

- **Rate limits** on **`conversations.history`** → hard caps and clear API errors to the model.

## Migration Plan

1. Ship tools behind env; staging with real token.
2. Production; rollback clears token → simulation/off.

## Open Questions

- Split vs combined tool ids for post vs update (overload **`ts`** vs separate id).
