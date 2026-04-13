## Why

Manual agent creation (Helm values, runtime config, eval wiring) is slow and inconsistent. An **agent-maker** path that turns structured requests into **reviewed PRs** can speed iteration while reusing platform primitives defined elsewhere.

## What Changes (iterative, small slices)

1. **`#agent-` prefix (policy)** — Document that channels where bots parse traffic need a **machine-visible boundary**; recommend `#agent-` prefixes for bot-readable segments so humans and automation share one convention.
2. **Agent-maker bot (narrow v1)** — A listener (e.g. Telegram **#agent-maker** channel) parses a constrained pattern (“I want an agent that…”) and opens **GitHub PRs** from validated templates. RBAC and rich NLU stay **out of scope** for v1.
3. **Subagent composition** — **Not** specified here. Deferred to **`openspec/changes/subagent-reference-system`** (stub); **additive-only** rules for that surface live with that change when promoted.
4. **Code-committed evals** — **Not** duplicated here. Eval suites, W&B sync, and versioning are owned by existing or future eval changes (e.g. checkpoint / trace work under **`agent-checkpointing-wandb-feedback`** and related specs). Agent-maker **consumes** those mechanisms so generated agents opt into the same **core** eval flow **without extra one-off wiring**.
5. **CI regression / delta flagging** — **Not** specified here. Deferred to **`openspec/changes/ci-delta-flagging`** (stub).

**Removed from scope:** shadow rollout / twin execution (OpenSpec changes deleted; no shadow integration in agent-maker).

## Capabilities

### New Capabilities

- `agent-prefix-convention`: Operator-facing documentation for `#agent-` (or successor) bot-readable markers in channels that run automation.
- `agent-maker-bot`: Constrained NL → validated PR workflow for new agent assets.

### Modified Capabilities

- `declarative-agent-library-chart`: Values/templates may gain optional sections produced by agent-maker (additive).

### Deferred (separate changes)

- `subagent-reference-system` — see stub change folder.
- `ci-delta-flagging` — see stub change folder.
- Code-committed eval contracts — see **`agent-checkpointing-wandb-feedback`** / W&B specs rather than redefining here.

## Impact

- **Velocity**: Less manual copy-paste for new agents.
- **Safety**: Human PR review remains mandatory; no auto-deploy in v1.
- **Dependencies**: GitHub API, messaging transport credentials, alignment with eval/trace specs **already** on the platform roadmap.
