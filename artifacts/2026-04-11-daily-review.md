# Daily Review — 2026-04-11

## 1. What actually moved today
- **Shipped (git, same day):** Eight commits on `main`, from initial standalone import through LangGraph/LangChain trigger work, OpenSpec reshaping (checkpointing/W&B feedback change + archive of prior W&B integration), **LangChain supervisor + subagent tools** on the trigger path, **BaseTen inference provider** proposal, **scraper Prometheus metrics** (reference CronJob + Helm + `docs/observability.md`), **development log** + README link, evening **OpenSpec** additions (**agent-maker-system**, **traceability**), and **networking-research-pipeline** Cursor skill.
- **Decided:** Trigger API shape moves toward supervisor turns (`message` vs legacy `subagent` field returning 400); scraper observability exposed via optional metrics port and Prometheus annotations when enabled; OpenSpec work is split into focused changes (checkpointing/W&B vs traceability vs agent-maker-system).
- **Tested / verified:** Evidence + `docs/development-log.md` document unit coverage for scraper metrics (`test_reference_scraper.py`, registry assertions); broader runtime tests touched in supervisor/subagent commits (`test_subagent_roles.py`, `test_agent_extensions.py`, `test_o11y_metrics.py`, etc.). CI intent is `./ci.sh` per initial import; no failing CI signal in the evidence packet itself.
- **Learned:** Same calendar day can carry **repo bootstrap + multiple OpenSpec proposals + runtime + Helm + packaged chart tgz** updates—high coordination cost; deterministic evidence packet is the right anchor when transcripts span many projects.
- **Deferred / abandoned:** Nothing explicitly marked abandoned in git; **untracked** tree still holds `.agent-reflect-and-learn/`, `.cursor/hooks/`, `.vscode/`, and `artifacts/`—needs a deliberate commit vs gitignore policy.

## 2. Current state at close
- **Repo / branch state:** `/Users/jordan/Code/declarative-agent-library-chart`, branch **`main`**, working tree **not clean** (`??` as above).
- **Main artifact or deliverable state:** Runnable chart + Python runtime with supervisor/subagent path, scraper metrics story documented, several **active OpenSpec changes** (e.g. `agent-checkpointing-wandb-feedback`, `baseten-inference-provider`, `agent-maker-system`, `traceability`) plus **archived** same-day change folders.
- **Open loops:** Track or ignore `artifacts/` and local hook/config dirs; continue implementation vs archive decisions for active OpenSpec changes; optional integration paths (BaseTen, W&B/checkpointing) remain specification-heavy until implemented end-to-end.
- **Blocking unknowns:** None surfaced in git; session transcripts show transient **Claude Code auth (401)** resolved via `/login` (environment/session, not this repo).

## 3. Mistakes and friction
| Symptom | Root cause | Evidence | Recurrence risk | Smallest durable fix |
|---|---|---|---|---|
| Untracked agent-reflect + hooks + VS Code + artifacts | Local setup and review outputs not yet in version control or ignore rules | `git status` in evidence packet | medium | Add `.gitignore` rules for generated artifacts if desired; commit stable config under `.agent-reflect-and-learn/` |
| Claude Code “Unknown skill: add-plugin” / 401 on skill install | Harness skill name mismatch; expired or missing API credentials | Same-day Claude project jsonl in evidence | medium | Use documented install path; `/login` when 401; avoid ambiguous slash commands |
| No same-day `~/.claude/plans` or `history.jsonl` rows | Planning/history not captured in those stores this day | Evidence packet sections | low | Rely on git + OpenSpec + dev log as source of truth when plans empty |
| Very large evidence markdown | Many cross-project jsonl transcripts included by mtime | `2026-04-11-evidence.md` size | medium | Use `--extra` sparingly; accept truncation; focus review on git + repo-local files |

## 4. Improvement candidates
### Memory / rules updates
- Prefer **git + development log + OpenSpec tasks** as the canonical story when Claude plan/history is empty for a day.
- After adding **breaking API** behavior (e.g. trigger `subagent` → 400), keep **one** client-facing note in README or examples until callers migrate.

### New skill candidates
- None strongly justified today beyond existing OpenSpec and chart skills—today’s work is already covered by repo skills and proposals.

### Deterministic script candidates
- Optional small script or doc snippet: “refresh packaged example tgz” when chart version bumps—only if manual tgz drift becomes recurring.

### Workflow / naming / packaging fixes
- Decide policy for **`examples/*/charts/*.tgz`**: always regenerate in CI vs commit; align with release process.
- Normalize **worktree vs main repo path** in mental model (Cursor transcripts show both); use explicit `--repo` for collectors and hooks.

## 5. Debugging summary
- **Target symptom:** Not a single deep repo debugging thread in evidence; nearest friction is **Claude Code authentication** during skill-pack install.
- **Actual root cause:** Invalid or missing credentials (`401`), resolved after `/login`.
- **Misleading clues / false leads:** “Unknown skill: add-plugin” suggests wrong command name before auth failure.
- **Decisive observation:** Successful login immediately unblocked the same user intent retry.
- **Prevention step:** Check auth state before multi-step installs; use official plugin/skill install commands only.
- **Skill or playbook update needed:** Optional one-liner in personal Claude setup notes—not chart repo specific.

## 6. Tomorrow-start brief
- **Exact current state:** `main` with substantial shipped code; **untracked** local config/artifacts; active OpenSpec changes listed under `openspec/changes/`.
- **First file(s) to open:** `openspec/changes/agent-checkpointing-wandb-feedback/tasks.md` (if continuing W&B/checkpoint thread), `docs/development-log.md`, `.gitignore` (for artifacts policy).
- **First command(s) to run:** `PAGER="" git -C /Users/jordan/Code/declarative-agent-library-chart status -sb`; `./ci.sh` before any large merge or release.
- **First 1 to 3 actions:** (1) Commit or ignore `.agent-reflect-and-learn/` and `artifacts/` deliberately. (2) Pick **one** OpenSpec change to drive to “implemented + archived” or explicitly park. (3) If touching Helm/examples, regenerate or verify packaged tgz consistency.
- **Known traps:** Breaking trigger contract for clients still sending `subagent`; Prometheus scrape assumptions for short-lived CronJob pods (grace/metrics addr).
- **Decisions already made and not to reopen without new evidence:** Supervisor-style trigger with LangChain agent root; scraper metrics via optional bind + annotations pattern.

## 7. Optional publishable nuggets
### One-line insights
- Shipping a library chart **and** a LangGraph runtime **and** OpenSpec in one day needs a written dev log—your future self only trusts git if commits are as dense as today’s.
- Treat **packaged example tgz** like lockfiles: either automate regeneration or you will drift silently.

### Short LinkedIn-style post draft
Today was a full-stack product day in one repo: standalone Helm chart import, LangChain/LangGraph supervisor wiring with an explicit API break for cleaner turns, Prometheus metrics on reference scrapers, and multiple OpenSpec proposals so the roadmap stays traceable. The pattern that held it together was a running development log next to ADRs—commits tell *what* changed; the log tells *why operators should care*.

### Short X / thread hooks
- 8 commits, 1 repo: chart + runtime + observability + specs. Density without chaos needs a dev log.
- Breaking `POST /trigger` on purpose: sometimes API hygiene is a feature.

## 8. Action JSON mirror
See `/Users/jordan/Code/declarative-agent-library-chart/artifacts/2026-04-11-improvement-actions.json`.
