# OpenSpec sync and spec drift — remediation checklist

Actionable follow-up from the spec–code audit (promotion vs archive, root `openspec/specs/` vs `openspec/changes/`). Use alongside **[`openspec/AGENTS.md`](../openspec/AGENTS.md)** and root **[`AGENTS.md`](../AGENTS.md)** for **test-to-spec traceability** when you touch promoted requirements.

**Global gate (any time a promoted `SHALL` or its ID changes):** update `docs/spec-test-traceability.md`, cite IDs in tests, run `python3 scripts/check_spec_traceability.py`.

---

## A. No action required (verify only, optional)

These **root** `openspec/specs/*/spec.md` files are **byte-identical** to at least one path under `openspec/changes/` (archive or active). Spot-check if you doubt; otherwise treat as already promoted.

- [ ] `dalc-chart-presence` — e.g. `archive/2026-04-17-presence-slack-jira-ootb/…`
- [ ] `dalc-example-values-files` — e.g. `archive/2026-04-16-examples-distinct-values-readmes/…`
- [ ] `dalc-library-chart-packaging` — e.g. `archive/2026-04-16-consolidate-naming/…`
- [ ] `dalc-python-complexity-ci` — e.g. `archive/2026-04-16-ci-cyclomatic-complexity/…`
- [ ] `dalc-runtime-token-metrics` — e.g. `changes/token-metrics-dashboard/specs/…` (identical to root)
- [ ] `dalc-jira-tools` — same bytes as `archive/2026-04-17-jira-tools/specs/jira-tools/spec.md` (folder name differs)
- [ ] `dalc-jira-trigger` — same as `…/jira-trigger/spec.md`
- [ ] `dalc-slack-tools` — same as `…/slack-tools/spec.md`
- [ ] `dalc-slack-trigger` — same as `…/slack-trigger/spec.md`

---

## B. Root spec drift — resolve with a three-way merge (root is often ahead on IDs)

**No** change folder has a **byte-identical** copy of these **root** files. For each: compare root to the **newest relevant** delta (often `archive/2026-04-16-dalc-traceability-migration/` or topic-specific archives), merge intentionally—**prefer shipped behavior + stable `[DALC-REQ-*]` / `[DALC-VER-*]` lines**; do **not** blindly overwrite root from archive.

- [ ] `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` — also compare `changes/token-metrics-dashboard/specs/dalc-agent-o11y-logs-dashboards/spec.md` (differs from root)
- [ ] `openspec/specs/dalc-agent-o11y-scrape/spec.md`
- [ ] `openspec/specs/dalc-chart-runtime-values/spec.md`
- [ ] `openspec/specs/dalc-chart-testing-ct/spec.md`
- [x] `openspec/specs/dalc-helm-unittest/spec.md`
- [ ] `openspec/specs/dalc-postgres-agent-persistence/spec.md`
- [ ] `openspec/specs/dalc-rag-from-scrapers/spec.md`
- [ ] `openspec/specs/dalc-requirement-verification/spec.md` — archive copies may be **older slices**; root likely includes extra `[DALC-VER-*]` content
- [ ] `openspec/specs/dalc-scraper-cursor-store/spec.md`

---

## C. Completed active changes — finish promotion alignment

Normative text should live under **`openspec/specs/`** when behavior is shipped; reconcile folders that still exist under **`openspec/changes/`**.

- [ ] **`token-metrics-dashboard`** — align **dashboards** spec: merge `changes/token-metrics-dashboard/specs/dalc-agent-o11y-logs-dashboards/spec.md` with root **§B first item**; then archive or retire duplicate delta text per **`openspec/AGENTS.md`**
- [ ] **`cfha-helm-library`** — `specs/dalc-helm-library/spec.md` and `specs/dalc-hello-world-example/spec.md` vs root **`dalc-library-chart-packaging`** / **`dalc-example-values-files`**: merge overlapping requirements, assign IDs, dedupe narrative
- [ ] **`config-first-hosted-agents`** — `specs/hello-world-example/spec.md`, `specs/hosted-agent-template/spec.md`: fold into appropriate **`openspec/specs/<capability>/`** or add new capability dirs with IDs + matrix rows

---

## D. Capabilities only in change deltas — promote or explicitly fold

These appear under **`openspec/changes/**`** (some only under **`archive/`**) without a **same-named** directory under **`openspec/specs/`**. For each **shipped** behavior: either **add** `openspec/specs/<slug>/spec.md` or **merge** into an existing capability; document **deferrals** in proposal/design if not promoted.

**Runtime (`changes/agent-runtime-components/specs/`):**

- [ ] `runtime-rag-http`
- [ ] `runtime-scrapers`
- [ ] `runtime-skills`
- [ ] `runtime-subagents`
- [ ] `runtime-tools-mcp`

**Checkpointing / feedback (`changes/agent-checkpointing-wandb-feedback/specs/`):**

- [ ] `agent-feedback-model`
- [ ] `runtime-langgraph-checkpoints`
- [ ] `tool-feedback-slack`
- [ ] `wandb-agent-traces`

**Other active or archived deltas (examples — scan `changes/**/specs/` for full set):**

- [ ] `baseten-inference` (`changes/baseten-inference-provider/specs/`)
- [ ] `declarative-langgraph-hitl` (`changes/declarative-langgraph-hitl/specs/`)
- [ ] `jira-scraper` (`changes/jira-scraper/specs/`)
- [ ] Archive-only examples: `slack-scraper`, `agent-tool-call-feedback`, `agent-wandb-traces`, `declarative-agent-library-chart`, etc. — promote if still normative for mainline; otherwise leave archived with explicit non-promotion note

---

## E. Housekeeping after remediation

- [ ] Re-run **`python3 scripts/check_spec_traceability.py`** (strict)
- [ ] **`uv run pytest`** / **`helm unittest`** as needed for touched evidence paths
- [ ] Move finished **`openspec/changes/<name>/`** to **`openspec/changes/archive/<YYYY-MM-DD>-<name>/`** only **after** promotion decisions are reflected in **`openspec/specs/`** (see **`openspec/AGENTS.md`** §6)

---

## F. Already addressed (audit context)

- **Helm negative path:** `helm/tests/hello_world_test.yaml` asserts **no** `batch/v1` `CronJob` when scrapers are off / parent disabled / sole job `enabled: false`; **`agent-runtime-components`** task **3.3** Helm slice marked done.
