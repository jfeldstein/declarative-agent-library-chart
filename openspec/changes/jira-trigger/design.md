## Context

Jira-trigger is an inbound integration layer only. It should verify inbound Jira webhook requests, map payloads into the existing trigger contract, and invoke `run_trigger_graph` with safe context fields. It should not perform user-visible Jira mutations directly.

## Goals / Non-Goals

**Goals:**

- Receive operator-enabled Jira webhook events.
- Verify inbound requests according to the chosen webhook topology.
- Normalize event payload into trigger-friendly message/context fields.
- Invoke hosted trigger path once per accepted event (subject to dedupe/retry policy).
- Keep trigger keys disjoint from `scrapers.jira` and from `jira-tools`.

**Non-goals:**

- Implement Jira REST read/write tools (belongs to `jira-tools`).
- Ingest trigger payload text into managed RAG by default.

## Decisions

1. Trigger handler calls internal trigger pipeline (`run_trigger_graph`) via normalized `TriggerBody`-equivalent payload.
2. Trigger layer SHALL NOT perform Jira REST mutations except verification-specific checks if required by transport.
3. Trigger config values are separate from both `scrapers.jira` and `jira-tools` keys.

## Risks / Trade-offs

- Duplicate webhook delivery: document idempotency policy and optional dedupe key strategy.
- Jira Cloud webhook variants: support the selected topology first; add others as follow-up.
- Bad payloads / invalid signatures: reject safely without leaking secrets.

## Migration Plan

1. Ship trigger route behind feature flag / disabled-by-default values.
2. Validate webhook verification and mapping in tests.
3. Enable in staging with `jira-tools` available for end-to-end workflows.

Rollback: disable trigger route via values/env or remove webhook subscription in Jira.
