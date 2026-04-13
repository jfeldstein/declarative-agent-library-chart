## Slice 1 — `#agent-` prefix policy

- [ ] Author operator doc: which channels run bots; why a visible prefix matters; examples using `#agent-` for bot-parsed segments.
- [ ] Cross-link from **`docs/development-log.md`** or runbook when the doc lands.

## Slice 2 — Agent-maker bot (MVP)

- [ ] Bot skeleton + channel listener for the agreed transport.
- [ ] Pattern matcher for the constrained “I want an agent that…” (or successor) template.
- [ ] GitHub PR creation using validated file templates (Helm fragment + docs stub).
- [ ] Unit tests for parsing + template selection (no live network in default CI).

## Slice 3 — Chart / runtime alignment (additive)

- [ ] Optional values keys or documentation snippets so generated charts match **`declarative-agent-library-chart`** conventions.
- [ ] Ensure generated configs opt into existing W&B / checkpoint env patterns **without** defining new eval semantics here.

## Deferred — tracked elsewhere

- **Subagent validation / loop limits / correlation** → **`subagent-reference-system`** stub (activate that change when ready).
- **CI delta / regression flagging** → **`ci-delta-flagging`** stub (activate that change when ready).
