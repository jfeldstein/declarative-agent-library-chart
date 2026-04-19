# OpenSpec sync and spec drift — remediation checklist

Actionable follow-up from the spec–code audit (promotion vs archive, root `openspec/specs/` vs `openspec/changes/`). Use alongside **[`openspec/AGENTS.md`](../openspec/AGENTS.md)** and root **[`AGENTS.md`](../AGENTS.md)** for **test-to-spec traceability** when you touch promoted requirements.

**Global gate (any time a promoted `SHALL` or its ID changes):** update `docs/spec-test-traceability.md`, cite IDs in tests, run `python3 scripts/check_spec_traceability.py`.

---

## A. No action required (verify only, optional)

These **root** `openspec/specs/*/spec.md` files are **byte-identical** to at least one path under `openspec/changes/` (archive or active). Spot-check if you doubt; otherwise treat as already promoted.

- [x] `dalc-chart-presence` — e.g. `archive/2026-04-17-presence-slack-jira-ootb/…`
- [x] `dalc-example-values-files` — e.g. `archive/2026-04-16-examples-distinct-values-readmes/…`
- [x] `dalc-library-chart-packaging` — e.g. `archive/2026-04-16-consolidate-naming/…`
- [x] `dalc-python-complexity-ci` — e.g. `archive/2026-04-16-ci-cyclomatic-complexity/…`
- [x] `dalc-runtime-token-metrics` — e.g. `archive/2026-04-19-token-metrics-dashboard/specs/dalc-runtime-token-metrics/spec.md` (identical to root)
- [x] `dalc-jira-tools` — same bytes as `archive/2026-04-17-jira-tools/specs/jira-tools/spec.md` (folder name differs)
- [x] `dalc-jira-trigger` — same as `…/jira-trigger/spec.md`
- [x] `dalc-slack-tools` — same as `…/slack-tools/spec.md`
- [x] `dalc-slack-trigger` — same as `…/slack-trigger/spec.md`

---

## B. Root spec drift — resolve with a three-way merge (root is often ahead on IDs)

**No** change folder has a **byte-identical** copy of these **root** files. For each: compare root to the **newest relevant** delta (often `archive/2026-04-16-dalc-traceability-migration/` or topic-specific archives), merge intentionally—**prefer shipped behavior + stable `[DALC-REQ-*]` / `[DALC-VER-*]` lines**; do **not** blindly overwrite root from archive.

- [x] `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` — also compare `archive/2026-04-19-token-metrics-dashboard/specs/dalc-agent-o11y-logs-dashboards/spec.md` (aligned: archived delta matches root)
- [x] `openspec/specs/dalc-agent-o11y-scrape/spec.md`
- [x] `openspec/specs/dalc-chart-runtime-values/spec.md`
- [x] `openspec/specs/dalc-chart-testing-ct/spec.md`
- [x] `openspec/specs/dalc-helm-unittest/spec.md`
- [x] `openspec/specs/dalc-postgres-agent-persistence/spec.md`
- [x] `openspec/specs/dalc-rag-from-scrapers/spec.md`
- [x] `openspec/specs/dalc-requirement-verification/spec.md` — archive copies may be **older slices**; root likely includes extra `[DALC-VER-*]` content
- [x] `openspec/specs/dalc-scraper-cursor-store/spec.md`

---

## C. Completed active changes — finish promotion alignment

Normative text should live under **`openspec/specs/`** when behavior is shipped; reconcile folders that still exist under **`openspec/changes/`**.

- [x] **`token-metrics-dashboard`** — deltas under **`openspec/specs/`** (`dalc-runtime-token-metrics`, `dalc-agent-o11y-logs-dashboards`) matched root; change archived to **`openspec/changes/archive/2026-04-19-token-metrics-dashboard/`** per **`openspec/AGENTS.md`** §6.
- [x] **`cfha-helm-library`** — delta **`specs/`** replaced with promoted **`dalc-library-chart-packaging`** / **`dalc-example-values-files`** bytes; archived to **`openspec/changes/archive/2026-04-19-cfha-helm-library/`**.
- [x] **`config-first-hosted-agents`** — delta **`specs/`** folded to promoted **`dalc-example-values-files`** / **`dalc-library-chart-packaging`**; archived to **`openspec/changes/archive/2026-04-19-config-first-hosted-agents/`**.

---

## D. Capabilities only in change deltas — promote or explicitly fold

These appear under **`openspec/changes/**`** (some only under **`archive/`**) without a **same-named** directory under **`openspec/specs/`**. For each **shipped** behavior: either **add** `openspec/specs/<slug>/spec.md` or **merge** into an existing capability; document **deferrals** in proposal/design if not promoted.

**Runtime (`changes/agent-runtime-components/specs/`):**

- [x] `runtime-rag-http` — **deferral / fold** documented in **`openspec/changes/agent-runtime-components/design.md`** (*Checklist §D*); standalone **`openspec/specs/runtime-*`** promotion deferred.
- [x] `runtime-scrapers` — *(same)*
- [x] `runtime-skills` — *(same)*
- [x] `runtime-subagents` — *(same)*
- [x] `runtime-tools-mcp` — *(same)*

**Checkpointing / feedback (`changes/agent-checkpointing-wandb-feedback/specs/`):**

- [x] `agent-feedback-model` — **deferral** in **`openspec/changes/agent-checkpointing-wandb-feedback/proposal.md`** (*Promotion status*).
- [x] `runtime-langgraph-checkpoints` — *(same)*
- [x] `tool-feedback-slack` — *(same)*
- [x] `wandb-agent-traces` — *(same)*

**Other active or archived deltas (examples — scan `changes/**/specs/` for full set):**

- [x] `baseten-inference` (`changes/baseten-inference-provider/specs/`) — **deferral** in **`openspec/changes/baseten-inference-provider/proposal.md`**.
- [x] `declarative-langgraph-hitl` (`changes/declarative-langgraph-hitl/specs/`) — **deferral** in **`openspec/changes/declarative-langgraph-hitl/proposal.md`**.
- [x] `jira-scraper` (`changes/jira-scraper/specs/`) — **fold** note in **`openspec/changes/jira-scraper/proposal.md`** (behavior tied to **`dalc-rag-from-scrapers`** / **`scrapers.jira`**).
- [x] Archive-only examples (`slack-scraper`, `agent-tool-call-feedback`, `agent-wandb-traces`, `declarative-agent-library-chart`, …) — treated as **historical** under **`openspec/changes/archive/`**; promote only when a maintainer explicitly revives normative text into **`openspec/specs/`** (otherwise non-promotion is implicit from absence of root specs).

---

## E. Housekeeping after remediation

- [x] Re-run **`python3 scripts/check_spec_traceability.py`** (strict)
- [x] **`uv run pytest`** / **`helm unittest`** as needed for touched evidence paths
- [x] Move finished **`openspec/changes/<name>/`** to **`openspec/changes/archive/<YYYY-MM-DD>-<name>/`** only **after** promotion decisions are reflected in **`openspec/specs/`** (see **`openspec/AGENTS.md`** §6) — **`token-metrics-dashboard`**, **`cfha-helm-library`**, **`config-first-hosted-agents`** archived **2026-04-19**.

---

## F. Already addressed (audit context)

- **Helm negative path:** `helm/tests/hello_world_test.yaml` asserts **no** `batch/v1` `CronJob` when scrapers are off / parent disabled / sole job `enabled: false`; **`agent-runtime-components`** task **3.3** Helm slice marked done.
