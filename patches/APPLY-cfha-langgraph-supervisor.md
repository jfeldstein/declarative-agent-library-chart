# Apply patch: LangChain supervisor + subagent tools (9b233c3)

This directory contains a **path-rewritten** git patch ported from the **agentic-pocs** worktree commit `9b233c3` (`feat(cfha): LangChain supervisor + subagent tools on trigger`).

Original paths used `projects/config-first-hosted-agents/`; the patch on disk is rewritten so paths are **relative to this repository root** (`runtime/`, `helm/chart/`, `README.md`, etc.).

## Files

| File | Purpose |
|------|---------|
| `cfha-langgraph-supervisor-9b233c3.patch` | Unified diff; use with `git apply` from repo root |

## Preconditions

- Repository root: directory that contains `runtime/pyproject.toml` and `helm/chart/`.
- No uncommitted changes you care about losing, or commit/stash first.

## Dry run

From the repository root:

```bash
cd "$(git rev-parse --show-toplevel)"
git apply --check patches/cfha-langgraph-supervisor-9b233c3.patch
```

If this reports **no output**, the patch should apply cleanly.

**Current repo note:** `git apply --check` may fail on `README.md` first because this chart repo’s README has diverged from agentic-pocs. Use the partial-apply flow below, or merge README by hand from the patch.

## Apply

```bash
git apply patches/cfha-langgraph-supervisor-9b233c3.patch
```

If **hunks fail** (often `README.md` if it has diverged), either:

1. Apply with rejects: `git apply --reject patches/cfha-langgraph-supervisor-9b233c3.patch` and merge `*.rej` manually, or  
2. **Exclude README**, apply everything else, then merge README manually:

   ```bash
   git apply --exclude=README.md patches/cfha-langgraph-supervisor-9b233c3.patch
   ```

   Open `README.md` and incorporate the README-related hunks from the patch file (search for `diff --git a/README.md`).

3. Apply in parts: `git apply` with path filters for subtrees (e.g. only `runtime/`), then port remaining files from the patch.

## After applying

1. **Sync Python env and lockfile** (patch may touch `runtime/uv.lock`):

   ```bash
   cd runtime
   uv sync --all-groups
   ```

2. **Lint and tests** (matches `ci.sh` Python stages):

   ```bash
   cd runtime
   uv run ruff check src tests
   uv run pytest tests/ -v --tb=short
   ```

3. **Helm** (optional but recommended if you have Helm + plugins): from repo root run `./ci.sh` for chart-testing and `helm unittest` on `examples/*`, or run those steps separately.

4. **Extra chart tests**: Consider extending `examples/*/tests/*_test.yaml` to assert `HOSTED_AGENT_CHAT_MODEL` when `chatModel` is set in values (pattern used in this repo’s example chart tests).

5. **Commit**:

   ```bash
   git add -A
   git commit -m "feat: LangChain supervisor + subagent tools on trigger"
   ```

## Regenerating the patch (maintainers)

If the upstream commit is available in an **agentic-pocs** worktree at `$WT` on commit `9b233c3`:

```bash
git -C "$WT" format-patch -1 9b233c3 --stdout \
  | sed 's|projects/config-first-hosted-agents/||g' \
  > patches/cfha-langgraph-supervisor-9b233c3.patch
```

Then re-run `git apply --check` from this repo’s root.

## What the patch changes (summary)

- **Trigger API:** `TriggerBody` uses `message` (no `subagent`); legacy `subagent` in JSON → **400** (handled in `app.py` before Pydantic).
- **Runtime:** Supervisor via LangChain `create_agent`, subagents as tools backed by LangGraph subgraphs; new modules `supervisor.py`, `subagent_exec.py`, `subagent_units.py`, `chat_model.py`, `trigger_steps.py`, `trigger_context.py`, `trigger_errors.py`; `trigger_graph.py` simplified to a single pipeline node.
- **Helm:** `HOSTED_AGENT_CHAT_MODEL` from values; `values.schema.json` updates (`description`, `exposeAsTool`, `chatModel`).
- **Docs / OpenSpec:** `README.md`, `docs/observability.md`, and `openspec/changes/cfha-langgraph-native-subagents/tasks.md` (checkboxes marked complete).
