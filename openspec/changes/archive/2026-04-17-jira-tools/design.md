## Context

Jira-tools defines LLM-time Jira REST capabilities for active runs. It should stay separate from trigger ingress (`jira-trigger`) and scheduled ingestion (`scrapers.jira`).

## Goals / Non-Goals

**Goals:**

- Provide bounded Jira search/read and scoped mutation tools.
- Register allowlisted tool ids via existing dispatch patterns.
- Keep tool credentials/config disjoint from trigger verification and scraper keys.
- Reuse observability/correlation patterns for side effects.

**Non-goals:**

- Building webhook ingress or verification.
- Default embedding of tool request/response content into managed RAG.

## Decisions

1. Jira REST access uses `httpx` or thin wrapper with explicit timeout + error mapping.
2. Tool operations are scope-gated and configuration-driven.
3. Real-call path can be gated similarly to existing simulated-vs-real tool patterns.

## Risks / Trade-offs

- Over-scoped credentials: mitigate with explicit allowlist and scope docs.
- Jira API rate/permission errors: normalize and redact responses.
- Drift from trigger expectations: coordinate smoke coverage with `jira-trigger`.

## Migration Plan

1. Land tools with mocks and tests first.
2. Enable real credentials in staging and validate comment/transition flows.
3. Pair with `jira-trigger` smoke path for end-to-end Jira mention/update workflows.
