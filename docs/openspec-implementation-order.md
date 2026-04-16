# OpenSpec implementation order (DAG + linear checklist)

This document captures **dependency ordering** for OpenSpec chart/runtime work: **rationale** for steps already **complete** in `openspec list`, plus a **linear checklist** for what remains, so implementers can reduce merge pain and double-breaking `values.yaml` / Grafana / `helm/tests/` churn.

**Sources:** proposal cross-references (`examples-distinct-values-readmes` → `consolidate-helm-tests`), shared artifact overlap (values schema, Grafana JSON, unittest paths), and product coupling (Slack trigger vs tools; scrapers vs cursor store). `.openspec.yaml` files do **not** declare edges; some links are **judgment calls**—see caveats.

**As of:** 2026-04-16 (`openspec list --json` + `main`).

---

## Legend

- **Solid edge** — explicit dependency in an OpenSpec proposal, or strong file-overlap if reordered.
- **Dashed edge** — soft coupling (parallelize with coordination).
- **✓ in DAG nodes** — change is **OpenSpec `status: complete`** as of the **As of** date above.
- **Checklist** — `- [x]` plus ~~strikethrough~~ means the change is **complete** in OpenSpec; unchecked lines are still **in-flight** or **stub** (no tasks).

---

## Mermaid DAG

Logical merge order (historical + remaining). Nodes marked **✓** are OpenSpec-complete; edges stay useful for **“what must land before what”** even when the upstream node is already done.

```mermaid
flowchart TB
  subgraph foundation["OpenSpec: complete (foundation)"]
    F1[checkpointing, trigger entrypoint, library chart, traceability, …]
  end

  DED["✓ dedupe-helm-values-observability"]
  HT["✓ consolidate-helm-tests"]
  EX["✓ examples-distinct-values-readmes"]
  O11Y["✓ observability-automatic-enabled-components"]
  NAM[consolidate-naming]
  PG[postgres-agent-persistence]
  CURS["✓ scraper-cursors-durable-store"]
  JSCR["jira-scraper 9/14"]
  SSCR["slack-scraper 8/14"]
  TOK[token-metrics-dashboard]
  HITL[declarative-langgraph-hitl]
  BASE[baseten-inference-provider]
  STR[slack-trigger]
  STO[slack-tools]
  JTL[jira-tools]
  JTR[jira-trigger]
  AMK[agent-maker-system]
  SUB[subagent-reference-system stub]
  CDF[ci-delta-flagging stub]

  DED --> NAM
  DED --> PG
  DED --> CURS
  NAM --> O11Y
  NAM --> TOK
  HT --> EX
  HT --> O11Y
  JSCR --> CURS
  SSCR --> CURS
  PG -.-> CURS
  STO -.-> STR
  JTL -.-> JTR
  SUB -.-> AMK
  CDF -.-> AMK
```

---

## ASCII (same graph)

`[done]` marks OpenSpec-complete steps as of the **As of** date above.

```
                    ┌──────────────────────────────────────┐
                    │  foundation (OpenSpec: complete)      │
                    │  LangGraph entry, checkpoints, etc.   │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
              ┌────────────────────────────────────────────┐
              │ [done] dedupe-helm-values-observability     │
              │  (values/schema/runtime key split)          │
              └─────────────┬──────────────┬─────────────────┘
                            │              │
              ┌─────────────▼───┐          │
              │ consolidate-   │          │
              │ naming         │          │
              └───────┬────────┘          │
                      │                   │
         ┌────────────┼───────────┐       │
         │            │           │       │
         ▼            ▼           │       ▼
    ┌─────────┐ ┌─────────┐     │  ┌─────────────────┐
    │ [done]  │ │ token-  │     │  │ postgres-agent- │
    │ o11y-   │ │ metrics │     │  │ persistence     │
    │ auto    │ │dashboard│     │  └────────┬────────┘
    │ enabled │ └─────────┘     │           │
    │ comps   │                   │           │ (optional / cleaner)
    └────┬────┘                   │           ▼
         │                        │  ┌─────────────────┐
         │                        └──│ [done] scraper- │
         │                           │ cursors durable │
         │                           └────────▲────────┘
         │                     ┌──────────────┴──────────────┐
         │                     │                           │
         │              ┌──────▼──────┐             ┌─────────▼─────┐
         │              │ jira-scraper│             │ slack-scraper│
         │              │ (finish)    │             │ (finish)     │
         │              └─────────────┘             └──────────────┘
         │
  ┌──────▼──────────────────────────┐
  │ [done] consolidate-helm-tests     │
  └──────┬──────────────────────────┘
         │
         ├──────────────────► [done] examples-distinct-values-readmes
         │
         └── (also feeds) ──► (o11y-auto row above)
```

---

## Ordering tiers (why)

| Tier | Changes | OpenSpec | Rationale |
|------|---------|----------|-----------|
| **1** | `dedupe-helm-values-observability` | **complete** | Defines where **checkpoints**, **wandb**, and Kubernetes **observability** (ex-`o11y`) live; `postgres-agent-persistence` and `scraper-cursors-durable-store` prose assume chart DSN / values paths this change reshapes. |
| **2** | `consolidate-naming` | **in progress** (0/20) | BREAKING pass on chart `name`, **`agent:`** values key (alias), image repo, Grafana filename / product tags; cleaner **after** value *semantics* are deduped. |
| **3** | `consolidate-helm-tests` | **complete** | Moves helm-unittest suites to `helm/tests/`; **`examples-distinct-values-readmes` explicitly depends on this**; `observability-automatic-enabled-components` should target the post-move layout. |
| **4** | `examples-distinct-values-readmes`, `observability-automatic-enabled-components` | **complete** | Example values layout + component-neutral scrape / Grafana behavior; coordinate **Grafana filenames** with tier 2. |
| **5** | `postgres-agent-persistence` | **in progress** (0/19) | Durable checkpoints + first-party tables; chart env should match **tier 1** contract. |
| **6** | Finish `slack-scraper` / `jira-scraper` (remaining tasks) | **in progress** (`slack-scraper` 8/14, `jira-scraper` 9/14) | Current watermark / cursor behavior; **`scraper-cursors-durable-store`** generalizes those jobs. |
| **7** | `scraper-cursors-durable-store` | **complete** | DSN reuse + abstraction; after **dedupe** (paths), after **scrapers** code paths; smoother after **postgres** exists. |
| **Parallel / leaf** | `baseten-inference-provider`, `declarative-langgraph-hitl` | **not started** (0/n) | Mostly additive; still touches shared tree—rebase often or land after **tiers 1–2**. |
| **Slack path** | `slack-tools` → `slack-trigger` | **not started** | Tools first so trigger-launched runs can respond immediately; ingress and tools still need coordinated keys/tests. |
| **Jira path** | `jira-tools` → `jira-trigger` | **not started** | Same split/order as Slack: LLM-time REST tools first, then webhook ingress using disjoint trigger keys. |
| **Later / meta** | `agent-maker-system` | **not started** | Defers **`subagent-reference-system`**, **`ci-delta-flagging`**; consumes existing checkpoint / trace mechanisms. |
| **Stubs** | `subagent-reference-system`, `ci-delta-flagging` | **no tasks** | Not an implementation queue until tasks exist. |
| **Other in-flight** | `presence-slack-jira-ootb`, `ci-cyclomatic-complexity` | 0/9, 0/8 | Not sequenced in the linear checklist; coordinate with **tier 2** (values/README) and **Python CI** respectively. |

---

## Single linear checklist

Use this as **one valid topological sort**. Re-run `openspec list --json` after merges; refresh ~~strikes~~ and `[x]` when statuses move.

- [x] ~~**1.** `dedupe-helm-values-observability` — split `o11y` vs product integrations; move checkpoints / wandb / Slack feedback keys per proposal.~~
- [ ] **2.** `consolidate-naming` — chart `name`, `agent:` alias, image repo, Grafana rename (`dalc-overview` etc.).
- [x] ~~**3.** `consolidate-helm-tests` — centralize suites under `helm/tests/`; CI `helm unittest -f …`; traceability path updates.~~
- [x] ~~**4.** `examples-distinct-values-readmes` — one values file per demonstrated setup; README index; unittest `values:` per file (**after** step 3).~~
- [x] ~~**5.** `observability-automatic-enabled-components` — component-neutral `ServiceMonitor` / Grafana story; tests under post-move `helm/tests/`.~~
- [ ] **6.** `token-metrics-dashboard` — Prometheus token / cost metrics + Grafana; keep aligned with **step 2** dashboard paths and **step 5** o11y specs.
- [ ] **7.** `postgres-agent-persistence` — Postgres checkpointer + relational stores; values/env match **step 1** (dedupe contract on `main`).
- [ ] **8.** `jira-scraper` — complete remaining tasks (OpenSpec **9/14** at last refresh).
- [ ] **9.** `slack-scraper` — complete remaining tasks (OpenSpec **8/14** at last refresh).
- [x] ~~**10.** `scraper-cursors-durable-store` — durable watermark/cursor backends; reuse DSN story from **step 1**; builds on **8–9** code paths.~~
- [ ] **11.** `baseten-inference-provider` — inference provider subtree + runtime client (additive).
- [ ] **12.** `declarative-langgraph-hitl` — declarative interrupt/resume model (additive; checkpointing already complete).
- [ ] **13.** `slack-tools` — LLM-time Slack Web API tools.
- [ ] **14.** `slack-trigger` — inbound Slack → trigger pipeline (coordinate with **13** for mention → run → reply).
- [ ] **15.** `jira-tools` — LLM-time Jira REST tools (search/read/comment/transition/create-update).
- [ ] **16.** `jira-trigger` — Jira webhook ingress → hosted trigger pipeline (coordinate with **15**).
- [ ] **17.** `agent-maker-system` — bot + prefix convention slices; after platform stable enough for templates.
- [ ] **18.** Stub follow-ups — `subagent-reference-system`, `ci-delta-flagging` (no tasks until those changes grow a `tasks.md` queue).

**Also in-flight** (not in the numbered list): `presence-slack-jira-ootb`, `ci-cyclomatic-complexity` — see **Ordering tiers**.

---

## Caveats

1. **Pull requests** — reconcile this checklist with **`gh pr list --state open`** before each sprint. Older PRs may still be useful context even when **closed** (e.g. [postgres #15](https://github.com/jfeldstein/declarative-agent-library-chart/pull/15), [checkpointing plan #14](https://github.com/jfeldstein/declarative-agent-library-chart/pull/14); both **closed without merge** as of 2026-04-16).
2. **Tiers 1 vs 2** (`dedupe` vs `naming`) — both touch many of the same files; **dedupe → naming** minimizes re-breaking the same keys twice; reversing is possible with one coordinated merge.
3. **Steps 5–6** can swap if Grafana ownership is serialized differently; both share the “Grafana + o11y specs” lane—avoid parallel PRs without coordination.
4. **Steps 11–12** (and parts of **15**) are **independent** of scrapers; the linear list places them after persistence/scrapers for a “platform then features” narrative—valid parallel tracks exist after **step 2** or **3** with careful rebasing.

---

## Maintenance

When a change reaches **complete** in `openspec list` and is archived, ~~strike~~ it here and set `[x]`, or remove it from the checklist and simplify the DAG. Optionally link this doc from `ARCHITECTURE.md` or `AGENTS.md` if maintainers want it discoverable.

**Authoring source of truth:** normative requirements live under **`openspec/changes/<name>/`** (deltas while a change is active) and **`openspec/specs/*/spec.md`** once promoted. The former **`docs/implementation-specs/`** per-step handoffs were removed: that queue is implemented in-tree, and duplicating plans there was redundant with OpenSpec + this checklist.
