## Why

Composable agents need a **validated subagent reference** model (existence, loop depth, request correlation). That work is **orthogonal** to the agent-maker bot and should not block prefix conventions or PR automation.

## What Changes

- _(Stub)_ Define **`subagent-reference-system`** when this change is activated: validation rules, loop-depth limits, and request-id forwarding across the subagent call chain.
- **Additive-only** (intended **SHALL** once promoted): runtime and chart extensions introduced for subagent references **must not** remove or redefine existing agent configuration keys incompatibly; new behavior is opt-in via new fields or explicit flags.

## Capabilities

### New Capabilities

- `subagent-reference-system`: _(deferred — stub proposal only.)_

### Modified Capabilities

- _(none until spec work begins.)_

## Impact

- **`agent-maker-system`** may depend on this capability once specified; until then agent-maker work should not assume subagent validation semantics beyond documentation pointers.
