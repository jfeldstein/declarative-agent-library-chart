## Why

Hosted agents need durable, inspectable runs so we can resume work, audit decisions, and turn production signals into training data. Today, tying human approval (for example Slack reactions on posted messages) to specific tool calls, exporting standardized trajectories (ATIF), and comparing prompt or model variants lacks a single, tagged observability story. Aligning persistence with [LangGraph’s functional API checkpoint model](https://docs.langchain.com/oss/python/langgraph/use-functional-api#manage-checkpoints) while making checkpointing automatic—and wiring feedback into Weights & Biases—closes that loop for SFT, RL-style fine-tuning, and safe shadow rollouts.

## What Changes

- Adopt **automatic checkpointing** for agent runs (functional API–style entrypoints/tasks or equivalent), so every step is persisted without requiring authors to manually save state; expose **thread state** and **checkpoint history** consistent with LangGraph’s `get_state` / `get_state_history` semantics where applicable.
- Introduce a **feedback channel abstraction** (first implementation: **Slack reactions** such as 👍/👎) that binds **±1 (or scalar) feedback** to **tool calls** and to **external artifacts** (e.g. a Slack message posted by `slack_post_message`).
- Ensure structured logs and checkpoints can be **exported to ATIF** trajectories for downstream tooling; support filtering **positive-feedback** subsequences for **SFT / RLFT** dataset construction.
- Add **shadow rollouts**: run **candidate** skills, models, or system prompts alongside (or immediately after) the primary path, with runs **tagged** so comparisons are possible in W&B and in exports.
- Integrate **Weights & Biases**: all runs and traces carry **consistent tags** (agent id, environment, skill version, model id, prompt hash, rollout arm); **human feedback** is **pushed onto the relevant W&B trace/span** (not only unstructured logs).
- Define a **feedback and signals model**: a **single global, versioned label registry** for all human-judgment labels, and a deliberate split between **explicit human feedback** (training-eligible judgments) and **operational run signals** (e.g. message deleted, prompt rewritten, human takeover) so implicit behavior does not silently become “feedback.”

## Capabilities

### New Capabilities

- `runtime-langgraph-checkpoints`: Automatic persistence and inspection of agent runs (checkpoint after tasks/steps), thread identifiers, optional checkpoint listing/history API aligned with LangGraph functional API patterns.
- `agent-feedback-model`: **Global-only**, versioned taxonomy for human-judgment labels; explicit separation of **human feedback events** from **operational run signals** for analytics and training hygiene.
- `tool-feedback-slack`: Map Slack message reactions to tool-call identifiers (and optional checkpoint step metadata); pluggable enough for other channels later.
- `wandb-agent-traces`: W&B run/span model for agents; required tags; logging of tool calls, checkpoints references, and human feedback on spans.
- `atif-trajectory-export`: Conversion from internal trajectory format to ATIF; rules for which steps and feedback fields are included; export hooks for training pipelines.
- `shadow-rollout-evaluation`: Configuration and execution of shadow variants (skill/model/prompt) with mandatory tagging and non-destructive comparison to primary.

### Modified Capabilities

- _(none — no existing `openspec/specs/` capability covers agent checkpointing or W&B feedback today.)_

## Impact

- **Supersedes** removed change `agent-feedback-wandb-integration`: unique requirements were merged into this tree (2026-04-11).
- **Runtime / agent host** (e.g. config-first hosted agents): checkpoint store selection, LangGraph or compatible checkpointer wiring, correlation IDs on tool invocations.
- **Integrations**: Slack Events API (or Bolt) for reactions; `wandb` SDK for traces and feedback enrichment.
- **Data / ML**: ATIF exporters, dataset builders for SFT/RLFT; single global label registry and version bumps; possible new dependencies (`langgraph`, `wandb`, Slack client).
- **Ops**: secrets for Slack and W&B; retention and PII policies for exported trajectories.
