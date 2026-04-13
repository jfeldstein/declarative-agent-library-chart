## Context

Agent assets today are hand-authored. **Agent-maker** automates the boring parts (boilerplate PRs) while keeping humans in the loop for merge and deploy.

## Goals / Non-Goals

**Goals:**

- Document and adopt an **`#agent-` prefix policy** so operators know which channels have parsers and how to mark machine-readable spans.
- Ship a **thin bot** that turns a **narrow, documented phrase pattern** into a **GitHub PR** with chart/runtime stubs that match this repo’s conventions.
- **Reuse** eval + W&B + checkpoint contracts defined under **`agent-checkpointing-wandb-feedback`** (and successors)—agent-maker does **not** invent parallel eval semantics.

**Non-Goals:**

- RBAC for who may trigger the bot (v1).
- Open-ended natural language beyond the documented pattern.
- **Subagent graph validation** (moved to **`subagent-reference-system`**).
- **CI regression matrices** (moved to **`ci-delta-flagging`**).
- **Shadow** execution or rollout tagging (removed from product OpenSpec).

## Decisions

1. **Prefix policy** — Treat `#agent-` as a **social + technical** convention: humans learn which channels are bot-attended; parsers only scan messages that include the agreed marker, reducing false positives.

2. **Bot transport** — Default sketch: Telegram channel **`#agent-maker`**; alternatives are fine if the contract (pattern → PR) stays identical.

3. **Evals** — Generated agents **inherit** the same eval hooks as hand-authored agents once the **code-committed eval** specs and CI jobs exist elsewhere. Agent-maker templates merely **enable** the right flags/paths.

4. **Additive-only chart/runtime edits** — Any new keys **extend** values schema; no breaking removals in templates produced by the bot.

## Architecture (sketch)

```
Operator message (pattern + #agent- marker)
        → Parser / validator
        → Template render
        → GitHub PR (human review)
        → Existing CI (pytest, helm unittest, traceability checks)
```

## Risks / Trade-offs

- **Ambiguous prompts** → tight pattern + reviewer owns merge.
- **Template drift** → pin template versions to chart semver bands in docs.

## Migration

1. Land prefix documentation (no code risk).
2. Land bot read-only / dry-run mode.
3. Enable PR creation behind a feature flag or allowlist.
