## Context

The repository’s canonical Python package lives under **`helm/src`** (`hosted_agents`, `tests`). **CI** (`.github/workflows/ci.yml`) already runs **`uv run ruff check hosted_agents tests`** with dependencies from **`uv sync --all-groups`**, but **`pyproject.toml`** does not yet pin **McCabe (`C901`)** or run **complexipy**. [complexipy](https://github.com/rohaquinlop/complexipy) measures **cognitive** complexity (human readability); Ruff **`C901`** measures **cyclomatic** (control-flow/decision density). Together they reduce merge of unmaintainable code without duplicating the same signal if thresholds are chosen deliberately.

## Goals / Non-Goals

**Goals:**

- Enforce **cyclomatic complexity** via Ruff **`C901`** with an explicit **`max-complexity`** in **`helm/src/pyproject.toml`**, applied to the same paths CI already lints.
- Enforce **cognitive complexity** via **`complexipy`** in CI with **`max-complexity-allowed`** (and **`paths`** / **`exclude`** as needed) aligned with project layout, preferably via **`[tool.complexipy]`** in **`pyproject.toml`**.
- Keep **local parity**: contributors can run the same commands as CI using **`uv`** from **`helm/src`**.

**Non-Goals:**

- Rewriting existing code in the **proposal/design** phase (implementation may refactor or use **complexipy snapshot** baselines if the initial pass is too noisy—decide during implementation).
- Replacing Ruff with another linter or adding **Sonar**/commercial scanners.
- Enforcing complexity on **non-Python** artifacts (Helm templates, JS, etc.).

## Decisions

1. **Ruff: enable `C901` + `mccabe.max-complexity`**  
   - **Rationale**: **`C901`** is the standard **McCabe/cyclomatic** rule in Ruff; it must be **selected** (`extend-select` or `select`) or it will not run even if `max-complexity` is set.  
   - **Alternatives**: Pylint **`PLR0912`** (too many branches)—orthogonal to McCabe; optional later if we want branch-count caps too.

2. **complexipy: dev dependency in `helm/src` + CI step**  
   - **Rationale**: Matches Ruff (already a dev tool), **`uv run complexipy`** works locally and in CI without a separate install recipe. **GitHub Action** `rohaquinlop/complexipy-action` is an alternative if we want zero Python env coupling—trade-off: another pinned action vs. single **`uv`** workflow. Prefer **`uv`** for consistency with the existing job unless action maintenance wins (open to flip during implementation).

3. **Thresholds: start from defaults or conservative values, tune with one PR**  
   - Ruff McCabe default in config is often **10**; complexipy default threshold is **15** per upstream docs. **Implementation** SHALL pick concrete numbers that **pass on current `main`** or add a **complexipy snapshot** / targeted refactors—whichever is smaller churn.  
   - **Alternatives**: Strict low limits from day one (high churn); **`--snapshot-create`** baseline file committed (good for large legacy surfaces).

4. **Scope paths**  
   - Match CI: **`hosted_agents`** and **`tests`** (or `.` from `helm/src` with excludes for generated/venv if needed). **`coverage` `omit`** patterns are unrelated—do not use them to hide complexity violations.

## Risks / Trade-offs

- **[Risk] CI breakage on merge** if thresholds are too strict for existing code → **Mitigation**: Measure locally first; use **complexipy snapshot** or temporary **`# noqa: C901` / `# complexipy: ignore`** only where justified and documented.  
- **[Risk] Duplicate nagging** between **`C901`** and complexipy on the same hot spots → **Mitigation**: Treat Ruff as **structural** gate and complexipy as **readability** gate; slightly different thresholds; disable one on a path only with ADR-level rationale (avoid by default).  
- **[Risk] Contributor confusion** (two metrics) → **Mitigation**: Short comment block in **`pyproject.toml`** or **`docs/`** linking Ruff + complexipy docs.

## Migration Plan

1. Land **`pyproject.toml`** Ruff + complexipy configuration and optional baseline/snapshot.  
2. Add/update **CI** steps so **`ruff check`** and **`complexipy`** run on PRs.  
3. Fix violations or establish baselines in the same change series so **`main` stays green**.  
4. **Rollback**: revert workflow + config commits; no data migration.

## Open Questions

- Exact **numeric thresholds** for **`C901`** and **complexipy** after a trial run on current tree (may drive snapshot vs. refactor split).  
- Whether to use **`complexipy-action`** vs. **`uv run complexipy`** for speed/caching only—decide in implementation.  
- Whether to upload **SARIF** for PR annotations (nice-to-have; not required for the minimal gate).
