## Why

Agent runs that post to Slack (and similar surfaces) currently lack a durable, queryable link between **human thumbs-up / thumbs-down** (or emoji reactions) and **specific tool calls** (e.g. “this message was produced by `slack_post_message`”). Without that association, teams cannot reliably turn production feedback into **training trajectories** (ATIF), **SFT/RLFT** datasets from positive sequences, or **experiment traces** in Weights & Biases. Adding checkpointing, consistent tagging, and W&B trace export closes the loop from live usage to model and prompt iteration—including **shadow rollouts** that compare variants without changing the default user-facing path.

## What Changes

- **Checkpointing & feedback binding**: Record explicit checkpoints around externally visible tool effects (e.g. Slack messages); ingest **+1 / -1** style signals (Slack reactions, or equivalent) and attach them to the correct tool-call span and checkpoint.
- **Trajectory export**: Convert structured run logs into **ATIF**-compatible trajectories; support extracting **positive (+1)** subsequences for **SFT/RLFT** pipelines.
- **Shadow rollouts**: Run alternate **skills / models / prompts** in parallel (shadow) with the same or mirrored inputs, log outcomes under distinct variant tags, without replacing the primary response unless configured.
- **Weights & Biases**: Integrate **wandb** for runs/traces; ensure **consistent tags** (environment, agent id, skill version, model, rollout type, checkpoint id); **push human +/- feedback** onto the corresponding W&B trace/span metadata or logged events.

## Capabilities

### New Capabilities

- `agent-tool-call-feedback`: Correlation of human **+1/-1** (and neutral/unlabeled) signals to **tool-call spans** and **checkpoints** (e.g. Slack message ts → run/tool id); idempotency and late-arriving reactions.
- `agent-atif-trajectory-export`: Definition of log → **ATIF** trajectory mapping, retention/redaction boundaries, and **positive-sequence** extraction for **SFT/RLFT**.
- `agent-wandb-traces`: **W&B** project/run/trace model for agent execution; **tagging conventions**; exporting **feedback events** and checkpoint linkage into traces.
- `agent-shadow-rollouts`: Configuration and logging for **shadow** execution of prompt/skill/model variants alongside primary; tagging and comparison hooks (metrics + traces).

### Modified Capabilities

- (none — no existing capability specs in `openspec/specs/` define prior requirements for this domain.)

## Impact

- **Agent runtime & tooling**: Instrumentation around tool calls that have user-visible side effects; optional Slack event subscription (or webhook) for reactions.
- **Data & compliance**: PII/redaction policy for trajectories and W&B payloads; retention and access control for training exports.
- **MLOps**: New dependency on **wandb** (API key, project configuration); possible batch jobs or pipelines for ATIF export and dataset builds.
- **Operations**: Shadow rollouts increase compute/latency cost where enabled; must be configurable per environment.
