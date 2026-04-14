# Step 16: agent-maker-system

`````
# Downstream LLM implementation brief: `agent-maker-system`

## 0. Context (read first)

- **Linear checklist:** Step **16** in `docs/openspec-implementation-order.md` — **later / meta:** **bot + prefix convention** slices; land **after** the platform is stable enough for **templates** (upstream **steps 1–15**: dedupe/naming/tests/examples/o11y/token dashboard/postgres/scrapers+cursors/Baseten/HITL/Slack path/Jira path).
- **DAG:** **`subagent-reference-system`** and **`ci-delta-flagging`** have **dashed** edges **into** `agent-maker-system` in `docs/openspec-implementation-order.md` — they are **stubs / follow-ups**, not prerequisites; **do not** block v1 on them.
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) … [`15-jira-bot-spec.md`](15-jira-bot-spec.md) — agent-maker **consumes** existing **checkpoint / trace / W&B env** patterns (**steps 1, 6, 7, 12**) and **additive** Helm conventions; it **does not** redefine scraper vs trigger vs tools boundaries (**8–9**, **13–15**).
- **Authoritative change bundle:** `openspec/changes/agent-maker-system/` — `proposal.md`, `design.md`, `tasks.md`, `.openspec.yaml`, and delta specs under `specs/*/spec.md`.
- **In-scope capabilities (implement):** **`agent-prefix-convention`** (operator-facing policy), **`agent-maker-bot`** (constrained NL → validated **GitHub PR**).
- **Deferred / reference-only (do not implement as part of step 16):**
  - `openspec/changes/agent-maker-system/specs/subagent-reference-system/spec.md` — owned by **`openspec/changes/subagent-reference-system`** when that change is activated (**proposal.md** §3).
  - `openspec/changes/agent-maker-system/specs/code-committed-evals/spec.md` — eval suites, W&B sync, versioning: **consume** **`agent-checkpointing-wandb-feedback`** (and successors); **no parallel eval semantics** in agent-maker (**proposal.md** §4, **design.md** goals).
  - **`ci-delta-flagging`** — **`openspec/changes/ci-delta-flagging`** stub (**proposal.md** §5).
- **Scope reconciliation:** **`specs/agent-prefix-convention/spec.md`** currently states **CI SHALL** validate `#agent-` prefixes broadly and **linters SHALL** enforce. **`design.md` / `tasks.md` Slice 1** call for **operator documentation** first. **v1 SHALL** satisfy **tasks.md** (doc + cross-link). **Full-repo CI/linter prefix enforcement** is **out of v1** unless a maintainer explicitly expands scope—if you add checks, keep them **narrow** (e.g. documented paths or examples only) and avoid breaking unrelated trees.
- **Removed product scope:** **shadow** rollout / twin execution — **no** integration in agent-maker (**proposal.md**).
- **Traceability:** When promoting normative **SHALL** rows to `openspec/specs/*/spec.md`, assign stable **`[DALC-REQ-…]`** / **`[DALC-VER-…]`** per **`openspec/specs/dalc-requirement-verification/spec.md`**, **ADR 0003**, **AGENTS.md** (**DALC-VER-005**); update **`docs/spec-test-traceability.md`**; cite IDs in **pytest** docstrings and/or **helm unittest `#`** comments; **`python3 scripts/check_spec_traceability.py`** exit **0**.

## 1. Goal

1. **`#agent-` prefix policy (Slice 1):** Publish **operator-facing** documentation: which channels run bots, why a **visible machine boundary** matters, examples using **`#agent-`** (or documented successor) for **bot-parsed** spans; cross-link from **`docs/development-log.md`** or a runbook (**`tasks.md`**).
2. **Agent-maker bot MVP (Slice 2):** **Listener** on agreed transport (**design.md** default sketch: **Telegram** **`#agent-maker`**); **pattern matcher** for constrained phrasing (e.g. **“I want an agent that…”** or documented successor); **validate** → **render templates** → **create GitHub PR** with Helm/runtime/doc stubs matching repo conventions; **human PR review** remains mandatory (**proposal.md**); **no auto-deploy** in v1.
3. **Chart / runtime alignment (Slice 3):** **Optional additive** values keys and/or doc snippets so **generated** assets align with **`declarative-agent-library-chart`**; generated configs **opt into** existing **W&B / checkpoint** env patterns **without** defining new eval semantics (**proposal.md**, **design.md**).
4. **Safety / quality:** Pre-PR **validation** of generated artifacts (naming, obvious security footguns, resource hints per **`specs/agent-maker-bot/spec.md`** validation scenarios—tighten to match code); **clear errors** to channel on malformed requests (**bot spec** scenarios).
5. **Observability / UX:** Post **PR URL** (or failure detail) back to the channel (**bot spec** PR status scenarios); **no secrets** in logs or returned messages (**GitHub tokens**, **Telegram bot token**, etc.).

## 2. Entities and interfaces (signatures only; no bodies)

### 2.1 Parsed request model

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ParsedAgentIntent:
    """Outcome of constrained NL parse — fields are illustrative; align with template variables."""
    raw_text: str
    capability_phrases: tuple[str, ...]  # ordered, deduped stable list
    template_id: str  # selected validated template bundle
```

```python
def parse_agent_maker_message(text: str) -> ParsedAgentIntent: ...
"""SHALL raise ParseError (or return rejected result type) when pattern / markers fail ([agent-maker-bot] invalid format scenario)."""

def message_includes_agent_boundary_marker(text: str) -> bool: ...
"""True only when agreed marker present (e.g. #agent- segment policy — exact rule in operator doc + tests)."""
```

### 2.2 Validation → render → PR pipeline

```python
from pathlib import Path
from typing import Protocol

class GeneratedTree(Protocol):
    def paths(self) -> frozenset[Path]: ...
    def read_text(self, path: Path) -> str: ...

def validate_generated_tree(tree: GeneratedTree) -> None: ...
"""SHALL raise on naming/security/resource violations ([agent-maker-bot] validation scenarios)."""

def render_templates(intent: ParsedAgentIntent, *, chart_version_band: str) -> GeneratedTree: ...
"""Deterministic render — no network."""

class GitHubPullRequestClient(Protocol):
    def create_pull_request(
        self,
        *,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        files: dict[str, str],  # path -> utf-8 content
    ) -> str: ...
    """Returns HTML URL of PR — implement with github REST or gh CLI wrapper; inject token only via env/secret."""
```

```python
def handle_inbound_channel_message(
    *,
    channel_id: str,
    sender_id: str,
    text: str,
    gh: GitHubPullRequestClient,
) -> ChannelReply: ...
"""Orchestrate parse → validate → PR; never log raw tokens."""

@dataclass(frozen=True)
class ChannelReply:
    ok: bool
    user_visible_markdown: str  # PR link or actionable error — no secrets
```

### 2.3 Transport adapter (Telegram default)

```python
class TelegramUpdateHandler(Protocol):
    async def on_text_message(self, *, chat_id: str, text: str, message_id: str) -> None: ...
"""Wire to handle_inbound_channel_message; ignore chats not allowlisted to #agent-maker equivalent."""
```

**Contract:** **Default CI** runs **without** live Telegram or GitHub — tests use **fakes** / **Recorded transports** / **env-disabled** short circuit (**`tasks.md`**: no live network in default CI).

### 2.4 Helm / values (additive illustration — exact keys in implementing PR)

```yaml
# Illustrative only — extend values.schema.json + values.yaml without breaking existing installs.

agentMaker:
  enabled: bool
  # Optional: GitHub repo/org defaults, branch naming prefix, template pack version pin
  github:
    tokenSecretRef: { name: str, key: str }
  telegram:
    botTokenSecretRef: { name: str, key: str }
    allowedChatIds: [str]
```

**Contract:** New keys **extend** schema only (**design.md** decision 4); **no breaking removals** in templates the bot opens.

### 2.5 File placement (suggested — align with repo layout in PR)

```text
runtime/src/hosted_agents/agent_maker/   # or sibling package — match existing hosted_agents patterns
helm/chart/templates/…                   # only if Slice 3 requires rendered resources
docs/operator/agent-prefix-convention.md # or path chosen with maintainers
```

## 3. Normative specs (implement against)

### 3.1 Delta specs **in scope** for step 16

| Path | Notes |
|------|--------|
| `openspec/changes/agent-maker-system/specs/agent-maker-bot/spec.md` | Telegram listener, pattern parse, templates, validation, PR creation, status reporting, errors — **tighten v1** if prose exceeds **`proposal.md`** (e.g. RBAC **out**). |
| `openspec/changes/agent-maker-system/specs/agent-prefix-convention/spec.md` | **Policy + examples** for **`#agent-`** boundary — **v1** matches **documentation** deliverable; treat **full CI/linter enforcement** as **non-v1** unless scope explicitly expanded (see §0). |

### 3.2 Delta specs **deferred** (do not implement now; trace for conflicts)

| Path | Track in |
|------|----------|
| `openspec/changes/agent-maker-system/specs/subagent-reference-system/spec.md` | `openspec/changes/subagent-reference-system/` |
| `openspec/changes/agent-maker-system/specs/code-committed-evals/spec.md` | Checkpoint / W&B / eval OpenSpecs — agent-maker **templates only enable** flags/paths |

### 3.3 Scenario → acceptance mapping (pre-ID promotion)

Until **`[DALC-REQ-…]`** rows exist on promoted specs, use **test docstrings** that quote **`openspec/changes/agent-maker-system/specs/...`** paths + scenario titles.

| Source | Intent |
|--------|--------|
| **agent-maker-bot** — listener | Bot listens on configured channel; ignores non-allowlisted chats. |
| **agent-maker-bot** — valid NL | **“I want an agent that…”** (and documented variants) → parse initiates PR path. |
| **agent-maker-bot** — invalid | Malformed → **clear** guidance message; **no** PR. |
| **agent-maker-bot** — PR created | Valid → PR with generated files; reply includes **link**. |
| **agent-maker-bot** — validation | Bad generated tree → **no** PR; error surfaced. |
| **agent-maker-bot** — rate limits | GitHub API 403/429 → graceful message + bounded retry policy **without** leaking token. |
| **agent-prefix-convention** | Doc states when to use **`#agent-`**, examples, and **non-agent** content avoids false positives. |

## 4. Tests and assertions (TDD; all must end green)

**Rule:** Add **failing tests first** for each behavior row, then implementation. Test-writing is **not** a separate stage from code.

### 4.1 Pytest (`runtime/tests/` or `helm/src/tests/` — follow existing CI layout for new code)

| Intent | Assertion |
|--------|------------|
| **Parse: happy path** | Canonical phrase → **`ParsedAgentIntent`** with expected **`capability_phrases`** / **`template_id`**. |
| **Parse: invalid** | Non-matching text → rejection / exception path; **no** `create_pull_request` call (spy). |
| **Marker gating** | Messages **without** agreed **`#agent-`** (or configured) marker → **no** PR path when policy requires marker. |
| **Validation** | Injected bad tree (illegal name, path traversal attempt, oversize resource) → **`validate_generated_tree`** fails; **no** PR. |
| **Render determinism** | Same intent + version band → identical file bytes. |
| **GitHub client** | Mock **`GitHubPullRequestClient`**: correct branch name, file map keys stable, **title/body** include agent summary; **no** `Authorization` string in logs/captured replies. |
| **Telegram handler** | Mock transport: **one** pipeline invocation per message; dedupe **message_id** optional (**document** if skipped in v1). |

**Invocation (adjust path if code lives under `helm/src`):**

```bash
cd runtime && uv sync --all-groups && uv run pytest tests/ -v --tb=short
```

### 4.2 Helm unittest (`helm/tests/`)

| Intent | Pattern |
|--------|---------|
| **Slice 3** | When **`agentMaker.enabled`** true, Deployment/CronJob/Job (whichever carries the bot) references **`secretKeyRef`** for GitHub + Telegram tokens — **never** ConfigMap literals for secrets. |
| **Defaults** | With **`agentMaker.enabled`** false, **no** new required secrets; chart still renders prior examples. |

```bash
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
```

Follow **`docs/implementation-specs/03-consolidate-helm-tests-spec.md`** for suite location and **`values:`** paths.

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

### 4.4 Manual / staging smoke (**optional** `tasks.md` follow-through)

- Telegram test channel → one valid phrase → PR opened in **dry-run** or **test repo**; reviewer verifies **no** secrets in PR description or bot replies.

## 5. Staged execution (each stage ends with listed tests green)

1. **Slice 1 — docs only** — `agent-prefix-convention` markdown + cross-link; **no** production code required; CI unchanged unless maintainer adds narrow checks.
2. **Slice 2a — parse + validate + render** — pytest for parse/validate/render tables (**§4.1**); **no** GitHub.
3. **Slice 2b — GitHub PR client** — mock PR client tests; optional **`httpx`** / PyGithub adapter behind interface (**§2.2**).
4. **Slice 2c — Telegram wiring** — async handler tests with fake transport; feature flag / **`enabled`** gate.
5. **Slice 3 — Helm additive** — schema + templates + helm unittest (**§4.2**); templates reference **existing** W&B/checkpoint env keys from **step 1 / 7** docs.
6. **Promotion** — assign **`[DALC-REQ-…]`** on promotion; matrix + comments; **`check_spec_traceability.py`** **0**.

## 6. Acceptance checklist

- [ ] Operator doc for **`#agent-`** / bot-readable channels landed and linked (**Slice 1**).
- [ ] Constrained pattern → **validated** tree → **GitHub PR** path with **unit tests** and **no live network** in default CI (**Slice 2**).
- [ ] Channel feedback for **success** (PR link) and **failure** (actionable, **no secrets**) (**bot spec**).
- [ ] **Additive-only** chart/runtime changes (**Slice 3**); generated snippets **reuse** documented W&B/checkpoint env patterns **without** new eval semantics.
- [ ] **No** implementation of **subagent graph validation**, **code-committed eval suites**, or **CI delta flagging** inside this change—only **stubs / references** per **proposal.md**.
- [ ] **`python3 scripts/check_spec_traceability.py`** passes after any promoted SHALL / matrix updates.

## 7. Commands summary

```bash
cd runtime && uv run pytest tests/ -v --tb=short
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite>.yaml" .
python3 scripts/check_spec_traceability.py
```

## 8. Clarifying questions (human / planner)

1. **Transport for v1:** **Telegram only** first vs abstraction that also supports **Slack** internal tooling (**design.md** allows alternatives if contract unchanged)?
2. **Pattern language:** Exact English template(s) and whether **non-English** prompts are explicitly rejected in v1.
3. **Target repo for PRs:** Same monoreo (`declarative-agent-library-chart`) vs **examples** satellite repos — branch naming + CODEOWNERS implications.
4. **Allowlisting:** Until RBAC exists (**non-goal**), how are **`allowedChatIds`** / GitHub repo targets configured and rotated?
5. **Prefix CI:** Maintainer decision on whether **any** automated check ships with v1 beyond documentation (**§0** conflict resolution).

## 9. Downstream LLM note (plan-for-downstream-llm)

Human reviewer: resolve **§8** where possible, then paste this fenced brief to the implementing LLM. Implementer: if **§8** unanswered, choose the **smallest safe** default (**Telegram + mock clients**, **same-repo PRs to feature branches**, **docs-only prefix enforcement**, **strict allowlist** via values), document in PR, and keep **Helm keys additive**. Do **not** implement **deferred** folder specs (**subagent-reference-system**, **code-committed-evals**) in this step.
`````
