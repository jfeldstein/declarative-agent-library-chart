---
description: When adding or renaming ADRs under docs/adrs/, avoid duplicate NNNN prefixes in filenames.
---

# ADR numbers must not collide

Architecture Decision Records use `docs/adrs/NNNN-short-title.md` (four digits, hyphen, kebab-case slug).

## Rules

1. **One number, one file.** The same `NNNN` must not appear on two different `.md` files in `docs/adrs/`. CI enforces this via `scripts/check_adr_numbers.sh`.
2. **Pick the next free number.** Before creating a new ADR, inspect existing files matching `docs/adrs/[0-9][0-9][0-9][0-9]-*.md` and use an unused sequence value—usually **max existing + 1** (e.g. if the highest is `0002`, the next is `0003`).
3. **Do not reuse numbers** when superseding or renaming; keep the original file (or update it in place) and add **Supersedes** / **Superseded by** notes per `docs/adrs/README.md`.
4. **Boilerplate** for new content: start from `docs/adrs/0000-topic.md`.

If two branches each add `0003-*.md`, reconcile before merge so only one `0003` exists; renumber the newer draft if needed.
